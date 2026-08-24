"""Machine-translation backend (admin-triggered, human-reviewed).

The whole feature is gated behind a human review step ("admin tekshirib
saqlaydi"), so the backend is deliberately swappable and low-stakes: change
the two ``_engine_translate`` calls below to move from the free
``deep-translator`` (Google, no API key) to an LLM/paid API later — nothing
else needs to change.

Design constraints (see Phase C):
  * Translation is ALWAYS triggered explicitly from the admin, never at render
    time. Public pages read whatever modeltranslation stores.
  * ``fill_translations`` is generic over every modeltranslation-registered
    field, so models added in later phases are auto-covered.
  * HTML (CKEditor) fields are translated node-by-node so tags survive.
"""
from __future__ import annotations

import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

from django.conf import settings

logger = logging.getLogger(__name__)

# GoogleTranslator rejects payloads above 5000 chars; stay safely under.
_MAX_CHUNK = 4500

# Bulk auto-translate fans the per-(row, field, language) requests out across a
# small thread pool (the work is network-I/O bound, not CPU) and dedupes
# identical source strings via a shared in-run cache. Together these are why
# selecting many rows no longer blocks the admin request for a minute.
_MAX_WORKERS = 8
_cache_lock = threading.Lock()
_run_cache: dict | None = None   # (source, target, text) -> result, while active
_run_locks: dict = {}            # (source, target, text) -> Lock, to translate once


@contextmanager
def translation_cache():
    """Enable a thread-shared translation cache for the duration of the block.

    Re-entrant: nested calls reuse the outermost cache. Outside this context the
    engine never caches, so unit tests that count engine calls are unaffected.
    """
    global _run_cache
    outer = _run_cache
    if outer is None:
        _run_cache = {}
        _run_locks.clear()
    try:
        yield
    finally:
        if outer is None:
            _run_cache = None
            _run_locks.clear()


# Brand/program names the MT engine must pass through unchanged. Google
# Translate parses these as ordinary words rather than proper nouns (e.g.
# "Tagayev Methods" -> "Методы Тагаева"), which is wrong
# every single time. Swapped for a placeholder before translation and
# restored after. Digit-only tokens, verified empirically: punctuation/
# brackets get mangled, and even plain uppercase-letter tokens get silently
# transliterated into Cyrillic under some sentence contexts (e.g. inside
# quotes) — pure digit sequences are the one form the engine never touches.
# Add every program/group name the admin publishes here (value = a free
# digit-only token) so the MT engine leaves it alone.
_PROTECTED_TERMS = {
    "Tagayev Methods": "700200301",
}


def _protect_terms(text: str) -> str:
    for term, token in _PROTECTED_TERMS.items():
        text = text.replace(term, token)
    return text


def _restore_terms(text: str) -> str:
    for term, token in _PROTECTED_TERMS.items():
        text = text.replace(token, term)
    return text


def _engine_translate(text: str, target: str, source: str) -> str:
    """Single point of contact with the MT engine. Swap this to change backends.

    Returns "" on any failure (offline, rate-limit, unsupported language) so the
    caller never overwrites a real value with garbage.
    """
    try:
        from deep_translator import GoogleTranslator

        result = GoogleTranslator(source=source, target=target).translate(_protect_terms(text))
        return _restore_terms(result) if result else ""
    except Exception as exc:  # pragma: no cover - network/engine errors
        logger.warning("MT failed (%s->%s): %s", source, target, exc)
        return ""


def _cached_translate(text: str, target: str, source: str) -> str:
    """Cache layer over :func:`_engine_translate`, active only inside a
    :func:`translation_cache` block. Identical (source, target, text) triples are
    translated exactly once, even across worker threads (per-key locking), so the
    free Google endpoint isn't hammered with duplicate requests when many rows
    share the same short value (badges, "soʻm/oy", "Doimiy qabul", …).
    """
    cache = _run_cache
    if cache is None:
        return _engine_translate(text, target, source)
    key = (source, target, text)
    with _cache_lock:
        if key in cache:
            return cache[key]
        lock = _run_locks.setdefault(key, threading.Lock())
    with lock:
        # Another thread may have produced it while we waited on the key lock.
        with _cache_lock:
            if key in cache:
                return cache[key]
        result = _engine_translate(text, target, source)
        with _cache_lock:
            cache[key] = result
        return result


def _chunks(text: str, size: int = _MAX_CHUNK):
    """Yield <=size character chunks, splitting on paragraph/space boundaries."""
    remaining = text
    while len(remaining) > size:
        cut = remaining.rfind("\n", 0, size)
        if cut <= 0:
            cut = remaining.rfind(" ", 0, size)
        if cut <= 0:
            cut = size
        yield remaining[:cut]
        remaining = remaining[cut:]
    if remaining:
        yield remaining


def translate_text(text: str, target: str, source: str = "uz") -> str:
    """Translate a plain-text string. Returns "" for empty input or failure."""
    text = (text or "").strip()
    if not text or target == source:
        return ""
    if len(text) <= _MAX_CHUNK:
        return _cached_translate(text, target, source)
    return " ".join(
        part for part in (_cached_translate(c, target, source) for c in _chunks(text)) if part
    ).strip()


def _translate_segments(texts: list, target: str, source: str) -> list:
    """Translate many short strings with FEW requests by joining on newlines.

    An HTML article has dozens of text nodes; translating each with its own HTTP
    round-trip would blow past the request timeout. Instead we newline-join them
    (a boundary the engine preserves) and translate in <=_MAX_CHUNK blocks. If
    the line counts ever fail to line up, we fall back to per-item translation so
    correctness is never sacrificed for speed. Returns a list aligned to `texts`.
    """
    if not texts:
        return []
    flat = [t.replace("\n", " ").strip() for t in texts]

    chunks, cur, cur_len = [], [], 0
    for line in flat:
        add = len(line) + 1
        if cur and cur_len + add > _MAX_CHUNK:
            chunks.append(cur)
            cur, cur_len = [], 0
        cur.append(line)
        cur_len += add
    if cur:
        chunks.append(cur)

    result = []
    for chunk in chunks:
        translated = _cached_translate("\n".join(chunk), target, source)
        lines = translated.split("\n")
        if len(lines) == len(chunk):
            result.extend(lines)
        else:
            # Alignment broke for this block — translate its items individually.
            result.extend(_cached_translate(item, target, source) for item in chunk)
    return result


def translate_html(html: str, target: str, source: str = "uz") -> str:
    """Translate the text nodes of an HTML fragment, preserving all markup.

    Used for CKEditor fields: translating the raw HTML string directly would
    corrupt tags/attributes, so we walk the DOM and translate only visible text
    (batched — see _translate_segments).
    """
    html = (html or "").strip()
    if not html or target == source:
        return ""
    try:
        from bs4 import BeautifulSoup, NavigableString
    except Exception:  # pragma: no cover
        # bs4 missing — fall back to a plain-text translation (better than nothing).
        return translate_text(html, target, source)

    soup = BeautifulSoup(html, "html.parser")
    skip_parents = {"script", "style"}
    nodes, raws = [], []
    for node in soup.descendants:
        if not isinstance(node, NavigableString):
            continue
        if node.parent and node.parent.name in skip_parents:
            continue
        if not str(node).strip():
            continue
        nodes.append(node)
        raws.append(str(node))

    translated = _translate_segments([r.strip() for r in raws], target, source)
    for node, raw, tr in zip(nodes, raws, translated):
        if not tr:
            continue
        # Preserve leading/trailing whitespace around the text node.
        lead = raw[: len(raw) - len(raw.lstrip())]
        trail = raw[len(raw.rstrip()):]
        node.replace_with(f"{lead}{tr}{trail}")
    return str(soup)


def target_languages(source: str | None = None) -> list[str]:
    """Languages to translate INTO (all configured langs except the source)."""
    source = source or getattr(settings, "MODELTRANSLATION_DEFAULT_LANGUAGE", "uz")
    langs = getattr(settings, "MODELTRANSLATION_LANGUAGES", ("uz", "ru", "en"))
    return [code for code in langs if code != source]


def fill_translations(obj, *, overwrite: bool = False) -> int:
    """Fill empty RU/EN (etc.) fields of ``obj`` by translating its UZ values.

    Generic over modeltranslation: discovers translatable fields by
    introspection, so every registered model is covered automatically. HTML
    (CKEditor) fields are translated tag-safely. Does NOT save — the caller
    decides when to persist (so the admin can review first).

    Returns the number of fields populated.
    """
    from django_ckeditor_5.fields import CKEditor5Field
    from modeltranslation.translator import NotRegistered, translator
    from modeltranslation.utils import build_localized_fieldname

    source = getattr(settings, "MODELTRANSLATION_DEFAULT_LANGUAGE", "uz")
    try:
        opts = translator.get_options_for_model(type(obj))
    except NotRegistered:
        return 0

    targets = target_languages(source)
    filled = 0
    for field_name in opts.fields:
        src_value = getattr(obj, build_localized_fieldname(field_name, source), None)
        if not src_value or not str(src_value).strip():
            continue
        is_html = isinstance(obj._meta.get_field(field_name), CKEditor5Field)
        translate = translate_html if is_html else translate_text
        for lang in targets:
            attr = build_localized_fieldname(field_name, lang)
            current = getattr(obj, attr, None)
            if current and str(current).strip() and not overwrite:
                continue
            translated = translate(str(src_value), lang, source)
            if translated:
                setattr(obj, attr, translated)
                filled += 1
    return filled


def _pending_units(obj, *, overwrite, source, targets):
    """Yield (field_name, attr, src_text, is_html, lang) for each empty target.

    Pure read of already-loaded attributes + model metadata (no DB query), so it
    is safe to call before fanning the actual translation out to threads.
    """
    from django_ckeditor_5.fields import CKEditor5Field
    from modeltranslation.translator import NotRegistered, translator
    from modeltranslation.utils import build_localized_fieldname

    try:
        opts = translator.get_options_for_model(type(obj))
    except NotRegistered:
        return
    for field_name in opts.fields:
        src_value = getattr(obj, build_localized_fieldname(field_name, source), None)
        if not src_value or not str(src_value).strip():
            continue
        is_html = isinstance(obj._meta.get_field(field_name), CKEditor5Field)
        for lang in targets:
            attr = build_localized_fieldname(field_name, lang)
            current = getattr(obj, attr, None)
            if current and str(current).strip() and not overwrite:
                continue
            yield field_name, attr, str(src_value), is_html, lang


def fill_translations_bulk(objects, *, overwrite=False, max_workers=_MAX_WORKERS):
    """Parallel, deduped equivalent of calling :func:`fill_translations` per object.

    Flattens every (object, field, target-language) that still needs filling into
    one work list and translates them concurrently (the cost is network latency,
    not CPU) under a shared :func:`translation_cache`, so identical strings cost a
    single request. Attributes are set on the main thread; objects are NOT saved
    (the caller decides when to persist, so the admin can review first).

    Returns ``[(obj, filled_count), ...]`` aligned to ``objects``.
    """
    source = getattr(settings, "MODELTRANSLATION_DEFAULT_LANGUAGE", "uz")
    targets = target_languages(source)

    jobs = []  # (obj, attr, src_text, is_html, lang)
    for obj in objects:
        for _field, attr, src, is_html, lang in _pending_units(
            obj, overwrite=overwrite, source=source, targets=targets
        ):
            jobs.append((obj, attr, src, is_html, lang))

    counts: dict[int, int] = {id(obj): 0 for obj in objects}
    if not jobs:
        return [(obj, 0) for obj in objects]

    def _run(job):
        _obj, _attr, src, is_html, lang = job
        try:
            fn = translate_html if is_html else translate_text
            return job, fn(src, lang, source)
        except Exception:  # pragma: no cover - defensive; engine already swallows
            logger.warning("translate unit failed", exc_info=True)
            return job, ""

    workers = max(1, min(max_workers, len(jobs)))
    with translation_cache():
        with ThreadPoolExecutor(max_workers=workers) as pool:
            # Threads only translate; setattr happens here on the main thread.
            for (obj, attr, _src, _h, _l), translated in pool.map(_run, jobs):
                if translated:
                    setattr(obj, attr, translated)
                    counts[id(obj)] += 1
    return [(obj, counts[id(obj)]) for obj in objects]


def missing_translation_fields(obj) -> list[str]:
    """Return human field names whose UZ is set but a target language is empty.

    Backs the "translations must not be left half-done" completeness warning.
    """
    from modeltranslation.translator import NotRegistered, translator
    from modeltranslation.utils import build_localized_fieldname

    source = getattr(settings, "MODELTRANSLATION_DEFAULT_LANGUAGE", "uz")
    try:
        opts = translator.get_options_for_model(type(obj))
    except NotRegistered:
        return []

    targets = target_languages(source)
    missing = []
    for field_name in opts.fields:
        src_value = getattr(obj, build_localized_fieldname(field_name, source), None)
        if not src_value or not str(src_value).strip():
            continue
        for lang in targets:
            value = getattr(obj, build_localized_fieldname(field_name, lang), None)
            if not value or not str(value).strip():
                label = str(obj._meta.get_field(field_name).verbose_name)
                missing.append(f"{label} ({lang})")
    return missing
