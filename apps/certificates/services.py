"""CEFR certificate ingestion.

Given a verification URL (the link encoded in the certificate's QR code), this
downloads the PDF, renders its first page to a JPEG for on-site display, and
parses the candidate's name + CEFR level from the embedded text.

Permissive dependencies only (client deliverable): pypdfium2 (Apache-2.0/BSD)
renders, pypdf (BSD) extracts text. No AGPL (PyMuPDF), no system poppler.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import re
import socket
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
from django.core.files.base import ContentFile

from apps.common.utils import is_public_ip

USER_AGENT = "Mozilla/5.0 (compatible; TagayevMethods-CertImporter/1.0)"
MAX_PDF_BYTES = 10 * 1024 * 1024
MAX_REDIRECTS = 4
RENDER_SCALE = 2.0          # ~144 dpi
JPEG_QUALITY = 82

# CEFR level token (A1..C2). Whole-word so it doesn't match inside other text.
CEFR_RE = re.compile(r"\b([ABC][12])\b")
# Certificate serial, e.g. 24BBA1263659AA (informational / dedup reference).
SERIAL_RE = re.compile(r"^\d{2}[A-Z]{2,5}\d{4,}[A-Z]{0,3}$")
# Issue/expiry dates: the PDF renders them as two DD.MM.YYYY tokens run
# together on one line with no separator, e.g. "29.05.202730.05.2025"
# (expiry then issue date). The earlier of the two is always the issue date.
DATE_RE = re.compile(r"\d{2}\.\d{2}\.\d{4}")
# Apostrophe variants seen in Uzbek text (oʻgʻli / o'g'li / o‘g‘li ...).
_APOS = "‘’ʻ'`ʼ"

# Subject names printed on the certificate → trilingual labels for the card.
SUBJECT_MAP = {
    "INGLIZ TILI": {"uz": "Ingliz tili", "ru": "Английский язык", "en": "English"},
    "RUS TILI": {"uz": "Rus tili", "ru": "Русский язык", "en": "Russian"},
    "NEMIS TILI": {"uz": "Nemis tili", "ru": "Немецкий язык", "en": "German"},
    "FRANSUZ TILI": {"uz": "Fransuz tili", "ru": "Французский язык", "en": "French"},
}


class CertificateImportError(Exception):
    """Raised for any recoverable failure during certificate import."""


# ---------------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------------
def _validate_public_url(url):
    """Reject anything that could turn an import into an SSRF probe.

    Only http/https is allowed, and every IP the host resolves to must be a
    routable public address — so an operator (or a crafted QR code) cannot make
    the server fetch ``http://169.254.169.254/…`` (cloud metadata), ``localhost``
    or any internal host.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise CertificateImportError("Faqat http/https havolalar qoʻllab-quvvatlanadi.")
    host = parsed.hostname
    if not host:
        raise CertificateImportError("Havola manzili notoʻgʻri.")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise CertificateImportError(f"Havola manzili aniqlanmadi: {host}") from exc
    validated = []
    for info in infos:
        ip = info[4][0]
        if not is_public_ip(ip):
            raise CertificateImportError(
                "Ichki/xususiy manzillarga soʻrov yuborib boʻlmaydi."
            )
        validated.append((info[0], ip))  # (family, ip)
    # Return one validated address so the caller can PIN the fetch to it (see
    # _pin_host): otherwise requests would resolve the host a second time, and a
    # DNS record that answered this check with a public IP could rebind to an
    # internal one for the actual request (TOCTOU / DNS rebinding).
    family, ip = validated[0]
    return host, family, ip


@contextlib.contextmanager
def _pin_host(host, family, ip):
    """Force `host` to resolve to the already-validated `ip` for one request,
    closing the DNS-rebinding window between validation and fetch.

    ponytail: monkeypatches the process-global socket.getaddrinfo — safe under
    gunicorn *sync* workers (single-threaded per request). If workers ever become
    threaded, swap this for a pinned urllib3 HTTPAdapter.
    """
    original = socket.getaddrinfo

    def pinned(h, p, *args, **kwargs):
        if h == host:
            sockaddr = (ip, p) if family == socket.AF_INET else (ip, p, 0, 0)
            return [(family, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", sockaddr)]
        return original(h, p, *args, **kwargs)

    socket.getaddrinfo = pinned
    try:
        yield
    finally:
        socket.getaddrinfo = original


def fetch_pdf_bytes(url, *, timeout=20):
    """Download `url` and return the PDF bytes, or raise CertificateImportError.

    SSRF-hardened: the target (and every manually-followed redirect hop) is
    validated to be a public http/https host, and the body is streamed with a
    hard byte cap so an oversized response cannot exhaust memory.
    """
    current = (url or "").strip()
    for _ in range(MAX_REDIRECTS + 1):
        host, family, ip = _validate_public_url(current)
        try:
            # Pin the connection to the IP we just validated (stream=True opens
            # the socket inside this call; the body is read from that same socket).
            with _pin_host(host, family, ip):
                resp = requests.get(
                    current, timeout=timeout, headers={"User-Agent": USER_AGENT},
                    allow_redirects=False, stream=True,
                )
        except requests.RequestException as exc:
            raise CertificateImportError(f"Yuklab boʻlmadi: {exc}") from exc

        try:
            # Follow redirects manually so each hop is re-validated (an allowed
            # host must not be able to bounce us to an internal one).
            if resp.is_redirect or resp.is_permanent_redirect:
                location = resp.headers.get("Location")
                if not location:
                    raise CertificateImportError("Yuklab boʻlmadi: redirect manzili yoʻq.")
                current = urljoin(current, location)
                continue

            try:
                resp.raise_for_status()
            except requests.RequestException as exc:
                raise CertificateImportError(f"Yuklab boʻlmadi: {exc}") from exc

            chunks, total = [], 0
            for chunk in resp.iter_content(chunk_size=64 * 1024):
                total += len(chunk)
                if total > MAX_PDF_BYTES:
                    raise CertificateImportError("PDF hajmi juda katta (10 MB dan oshdi).")
                chunks.append(chunk)
            data = b"".join(chunks)
            ctype = resp.headers.get("Content-Type", "").lower()
        finally:
            resp.close()

        if not (data[:5] == b"%PDF-" or "pdf" in ctype):
            raise CertificateImportError(
                "Havola PDF faylga olib bormadi (sertifikat PDF havolasini kiriting)."
            )
        return data

    raise CertificateImportError("Yuklab boʻlmadi: juda koʻp qayta yoʻnaltirish.")


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
def render_first_page_jpeg(pdf_bytes, *, scale=RENDER_SCALE):
    """Render page 1 of the PDF to JPEG bytes (for the certificate card)."""
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(pdf_bytes)
    try:
        if len(pdf) == 0:
            raise CertificateImportError("PDF boʻsh.")
        pil = pdf[0].render(scale=scale).to_pil().convert("RGB")
    finally:
        pdf.close()
    buf = io.BytesIO()
    pil.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Text parsing
# ---------------------------------------------------------------------------
def extract_text_lines(pdf_bytes):
    """Return the first page's non-empty text lines."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(pdf_bytes))
    if not reader.pages:
        return []
    text = reader.pages[0].extract_text() or ""
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def _strip_apostrophes(s):
    return "".join(c for c in s if c not in _APOS)


def _is_name_line(line):
    """A surname/name/patronymic line: ALL-CAPS letters, no digits, not subject."""
    return (
        line == line.upper()
        and any(ch.isalpha() for ch in line)
        and not any(ch.isdigit() for ch in line)
        and "TILI" not in line
        and "SERTIFIKAT" not in line
        and "CERTIFICATE" not in line
        and not CEFR_RE.fullmatch(line)
    )


def _format_name_part(part):
    """Title-case a name token; keep the o‘g‘li/qizi patronymic suffix lowercase."""
    out = []
    for word in part.split():
        low = word.lower()
        # Patronymic suffix stays lowercase, Latin or Cyrillic script.
        if _strip_apostrophes(low) in ("ogli", "qizi", "ўғли", "қизи"):
            out.append(low)
        else:
            out.append(word[:1].upper() + word[1:].lower())
    return " ".join(out)


def parse_cefr(lines):
    """Parse name / CEFR level / subject from the certificate's text lines.

    Robust to both pypdf and PyMuPDF line grouping: the name is always the run
    of ALL-CAPS lines immediately preceding the subject line ("… TILI"), which
    we anchor on and walk backwards from.
    """
    result = {"name": "", "level": "", "subject": "", "serial": "", "issued_on": None}

    result["serial"] = next((l for l in lines if SERIAL_RE.match(l)), "")

    dates = []
    for l in lines:
        for tok in DATE_RE.findall(l):
            try:
                dates.append(datetime.strptime(tok, "%d.%m.%Y").date())
            except ValueError:
                pass
    if dates:
        result["issued_on"] = min(dates)

    subj_idx = next((i for i, l in enumerate(lines) if "TILI" in l), None)
    if subj_idx is not None:
        subj_line = lines[subj_idx]
        result["subject"] = CEFR_RE.sub("", subj_line).strip()
        m = CEFR_RE.search(subj_line)
        result["level"] = m.group(1) if m else ""
        # Walk backwards collecting up to 3 name lines.
        name_parts = []
        for l in reversed(lines[:subj_idx]):
            if _is_name_line(l):
                name_parts.append(l)
                if len(name_parts) >= 3:
                    break
            else:
                break
        name_parts.reverse()
        result["name"] = " ".join(_format_name_part(p) for p in name_parts)

    if not result["level"]:
        m = next((CEFR_RE.search(l) for l in lines if CEFR_RE.search(l)), None)
        result["level"] = m.group(1) if m else ""

    return result


# ---------------------------------------------------------------------------
# Reordering
# ---------------------------------------------------------------------------
def _person_key(student_name):
    """Normalize a name for same-person grouping (casefold + apostrophe glyphs).

    Doesn't bridge Cyrillic/Latin spellings of the same name (that needs real
    transliteration) — a student whose two certificates were rendered in
    different scripts won't auto-group; nudge their `order` in admin.
    """
    return _strip_apostrophes((student_name or "").casefold()).split()


def _newest_first_key(cert):
    """Sort key giving newest `issued_on` first, undated certs last (ascending
    sort). Dates are negated via ordinal since date objects aren't negatable."""
    if cert.issued_on is None:
        return (1, 0, 0)
    return (0, -cert.issued_on.toordinal(), -cert.id)


def reorder_certificates():
    """Renumber every certificate's `order` so the NEWEST show first (order 0 =
    top), keeping a student's repeat certificates adjacent (grouped, newest
    within the group first). Certs without `issued_on` sort last, by id.
    Returns the number of rows changed.
    """
    from apps.certificates.models import Certificate

    certs = list(Certificate.objects.order_by("id"))
    groups = {}
    for cert in certs:
        groups.setdefault(tuple(_person_key(cert.student_name)), []).append(cert)

    for group in groups.values():
        group.sort(key=_newest_first_key)
    # After the within-group sort, group[0] is the group's newest certificate;
    # order groups by that so the most recent student appears at the top.
    ordered_groups = sorted(groups.values(), key=lambda g: _newest_first_key(g[0]))

    changed = 0
    order = 0
    for group in ordered_groups:
        for cert in group:
            if cert.order != order:
                Certificate.objects.filter(pk=cert.pk).update(order=order)
                changed += 1
            order += 1
    return changed


def _set_translated(obj, field, uz, ru, en):
    setattr(obj, field, uz)
    setattr(obj, f"{field}_uz", uz)
    setattr(obj, f"{field}_ru", ru)
    setattr(obj, f"{field}_en", en)


def populate_certificate(cert, *, fetcher=fetch_pdf_bytes, save=False):
    """Fill `cert` from its external_url: render image + parse name/level/subject.

    `fetcher` is injectable so tests can supply local PDF bytes without network.
    Returns the parsed data dict. Does not commit unless save=True.
    """
    url = (cert.external_url or "").strip()
    if not url:
        raise CertificateImportError("Tashqi havola (URL) kiritilmagan.")

    pdf_bytes = fetcher(url)
    jpeg = render_first_page_jpeg(pdf_bytes)
    data = parse_cefr(extract_text_lines(pdf_bytes))

    # Stable filename (hash() is per-process randomized → would orphan the old
    # image on every --force re-import for serial-less certs).
    ref = data.get("serial") or hashlib.md5(url.encode()).hexdigest()[:12]
    cert.image.save(f"cefr-{ref}.jpg", ContentFile(jpeg), save=False)

    if data.get("name"):
        cert.student_name = data["name"]

    if data.get("issued_on"):
        cert.issued_on = data["issued_on"]

    level = data.get("level") or ""
    subj_raw = (data.get("subject") or "").upper()
    subj = SUBJECT_MAP.get(subj_raw)
    if subj is None:
        cap = data.get("subject", "").capitalize()
        subj = {"uz": cap, "ru": cap, "en": cap}

    if level:
        cert.badge = level
        cert.badge_accent = level in ("C1", "C2")

    _set_translated(
        cert, "description",
        f"CEFR Multilevel · {subj['uz']}",
        f"CEFR Multilevel · {subj['ru']}",
        f"CEFR Multilevel · {subj['en']}",
    )

    name = cert.student_name or "CEFR sertifikati"
    title = f"CEFR {level} — {name}".strip(" —")
    _set_translated(cert, "title", title, title, title)

    if save:
        cert.save()
    return data
