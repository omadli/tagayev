# -*- coding: utf-8 -*-
"""
Build a Uzbek override catalog for Django/Unfold CORE admin strings.

Django ships an `uz` admin catalog that is only ~40% translated, and Unfold
ships no `uz` catalog at all, so large parts of the admin UI appear in English
under the Uzbek interface (reported as "admin uz tarjimalari to'liqmas").

This script reads Django's bundled `uz` admin catalog purely to obtain the
*exact* msgid bytes (they use U+2019 apostrophes / U+201C-D quotes that must
match byte-for-byte), then writes our own
``locale/uz/LC_MESSAGES/django.po`` (+ .mo) containing Uzbek translations for
the untranslated, user-visible strings. Because the project's LOCALE_PATHS is
loaded last, these entries take precedence over Django's bundled catalog.

Only NON-empty translations are emitted, so anything we don't cover keeps
falling back to Django's own (already translated) strings instead of being
shadowed by a blank.

Run (gettext binaries not required — uses polib):
    set PYTHONIOENCODING=utf-8
    venv\\Scripts\\python.exe locale\\_build_uz_admin.py
"""
import os
import re

import polib
import unfold

from _extra_translations import UNFOLD_UZ

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DJANGO_UZ = os.path.join(
    BASE, "venv", "Lib", "site-packages", "django", "contrib", "admin",
    "locale", "uz", "LC_MESSAGES", "django.po",
)
UNFOLD_TPL = os.path.join(os.path.dirname(unfold.__file__), "templates")
_TRANS_RE = re.compile(r"{%\s*trans(?:late)?\s+(\"[^\"]*\"|'[^']*')\s*%}")

# Normalize curly quotes/apostrophes so our ASCII map keys match Django msgids.
_NORM = {"’": "'", "‘": "'", "“": '"', "”": '"', "—": "—"}


def unfold_msgids():
    """Exact {% trans %} msgids used across Unfold's templates (Unfold ships no
    catalog, so we translate its UI strings ourselves)."""
    ids = set()
    for dirpath, _dirs, files in os.walk(UNFOLD_TPL):
        for fn in files:
            if fn.endswith(".html"):
                with open(os.path.join(dirpath, fn), encoding="utf-8") as fh:
                    for m in _TRANS_RE.finditer(fh.read()):
                        ids.add(m.group(1)[1:-1])
    return ids


def norm(s: str) -> str:
    for k, v in _NORM.items():
        s = s.replace(k, v)
    return s


# English (normalized) msgid -> Uzbek. Placeholders ({name}, %(x)s, <strong>)
# are preserved verbatim. Apostrophes use ASCII ' for the admin UI.
UZ = {
    # --- Global chrome / navigation ---
    "Home": "Bosh sahifa",
    "Log in": "Kirish",
    "History": "Tarix",
    "Site administration": "Sayt boshqaruvi",
    "Django administration": "Boshqaruv paneli",
    "Django site admin": "Boshqaruv paneli",
    "%(app)s administration": "%(app)s boshqaruvi",
    "Breadcrumbs": "Yo'l ko'rsatkich",
    "Sidebar": "Yon panel",
    "Models in the %(name)s application": "%(name)s ilovasidagi modellar",
    "Start typing to filter…": "Filtrlash uchun yozing…",
    "Filter navigation items": "Navigatsiya elementlarini filtrlash",
    "Skip to main content": "Asosiy kontentga o'tish",
    "Forgotten your password or username?": "Parol yoki foydalanuvchi nomini unutdingizmi?",
    "Thanks for spending some quality time with the web site today.":
        "Bugun saytda vaqt ajratganingiz uchun rahmat.",
    # --- Theme / sorting / counts ---
    "Toggle theme (current theme: auto)": "Mavzuni almashtirish (joriy mavzu: avto)",
    "Toggle theme (current theme: light)": "Mavzuni almashtirish (joriy mavzu: yorug')",
    "Toggle theme (current theme: dark)": "Mavzuni almashtirish (joriy mavzu: tungi)",
    "Toggle sorting": "Saralashni almashtirish",
    "Sorting priority: %(priority_number)s": "Saralash ustuvorligi: %(priority_number)s",
    "Hide counts": "Sonlarni yashirish",
    "Show counts": "Sonlarni ko'rsatish",
    "Clear all filters": "Barcha filtrlarni tozalash",
    " By %(filter_title)s ": " %(filter_title)s bo'yicha ",
    "None available": "Mavjud emas",
    # --- Save / form buttons ---
    "Save as new": "Yangi sifatida saqlash",
    "Save and add another": "Saqlash va yana qo'shish",
    "Save and continue editing": "Saqlash va tahrirni davom ettirish",
    "Save and view": "Saqlash va ko'rish",
    "Close": "Yopish",
    "Go": "O'tish",
    "Show all": "Barchasini ko'rsatish",
    "%(full_result_count)s total": "Jami %(full_result_count)s ta",
    "Popup closing…": "Oyna yopilmoqda…",
    # --- Object/row action labels ---
    "Change selected %(model)s": "Tanlangan %(model)s ni o'zgartirish",
    "Add another %(model)s": "Yana %(model)s qo'shish",
    "Delete selected %(model)s": "Tanlangan %(model)s ni o'chirish",
    "View selected %(model)s": "Tanlangan %(model)s ni ko'rish",
    # --- Selection / actions ---
    "0 of %(cnt)s selected": "%(cnt)s tadan 0 tasi tanlandi",
    "Click here to select the objects across all pages":
        "Barcha sahifalardagi obyektlarni tanlash uchun shu yerni bosing",
    "Select all %(total_count)s %(module_name)s":
        "Barcha %(total_count)s ta %(module_name)s ni tanlash",
    "Clear selection": "Tanlovni tozalash",
    "Select this object for an action - {}": "Bu obyektni amal uchun tanlang - {}",
    "Items must be selected in order to perform actions on them. "
    "No items have been changed.":
        "Amal bajarish uchun elementlar tanlanishi kerak. Hech narsa o'zgartirilmadi.",
    "No action selected.": "Hech qanday amal tanlanmadi.",
    "Hold down \"Control\", or \"Command\" on a Mac, to select more than one.":
        "Bir nechtasini tanlash uchun \"Control\" (yoki Mac'da \"Command\") tugmasini bosib turing.",
    # --- LogEntry / change messages ---
    "LogEntry Object": "Jurnal yozuvi",
    "Added {name} \"{object}\".": "{name} \"{object}\" qo'shildi.",
    "Added.": "Qo'shildi.",
    "Changed {fields} for {name} \"{object}\".": "{name} \"{object}\" uchun {fields} o'zgartirildi.",
    "Changed {fields}.": "{fields} o'zgartirildi.",
    "Deleted {name} \"{object}\".": "{name} \"{object}\" o'chirildi.",
    "No fields changed.": "Hech qanday maydon o'zgartirilmadi.",
    "Change history: %s": "O'zgarishlar tarixi: %s",
    "This object doesn't have a change history. It probably wasn't added via this admin site.":
        "Bu obyektda o'zgarishlar tarixi yo'q. Ehtimol, u shu admin sayti orqali qo'shilmagan.",
    "Date/time": "Sana/vaqt",
    "User": "Foydalanuvchi",
    "Action": "Amal",
    # --- Add/change success messages ---
    "The {name} \"{obj}\" was added successfully.":
        "{name} \"{obj}\" muvaffaqiyatli qo'shildi.",
    "You may edit it again below.": "Uni quyida qayta tahrirlashingiz mumkin.",
    "The {name} \"{obj}\" was added successfully. You may add another {name} below.":
        "{name} \"{obj}\" muvaffaqiyatli qo'shildi. Quyida yana {name} qo'shishingiz mumkin.",
    "The {name} \"{obj}\" was changed successfully. You may edit it again below.":
        "{name} \"{obj}\" muvaffaqiyatli o'zgartirildi. Uni quyida qayta tahrirlashingiz mumkin.",
    "The {name} \"{obj}\" was added successfully. You may edit it again below.":
        "{name} \"{obj}\" muvaffaqiyatli qo'shildi. Uni quyida qayta tahrirlashingiz mumkin.",
    "The {name} \"{obj}\" was changed successfully. You may add another {name} below.":
        "{name} \"{obj}\" muvaffaqiyatli o'zgartirildi. Quyida yana {name} qo'shishingiz mumkin.",
    # --- Errors / permissions / not found ---
    "Page not found": "Sahifa topilmadi",
    "We're sorry, but the requested page could not be found.":
        "Kechirasiz, so'ralgan sahifa topilmadi.",
    "%(name)s with ID \"%(key)s\" doesn't exist. Perhaps it was deleted?":
        "ID \"%(key)s\" ga ega %(name)s mavjud emas. Ehtimol, u o'chirilgan?",
    "You don't have permission to view or edit anything.":
        "Sizda hech narsani ko'rish yoki tahrirlash huquqi yo'q.",
    "First, enter a username and password. Then, you'll be able to edit more user options.":
        "Avval foydalanuvchi nomi va parolni kiriting. So'ng boshqa sozlamalarni tahrirlashingiz mumkin.",
    "Enter a new password for the user <strong>%(username)s</strong>.":
        "<strong>%(username)s</strong> foydalanuvchisi uchun yangi parol kiriting.",
    "You are authenticated as %(username)s, but are not authorized to access this page. "
    "Would you like to login to a different account?":
        "Siz %(username)s sifatida tizimga kirgansiz, lekin bu sahifaga ruxsatingiz yo'q. "
        "Boshqa hisob bilan kirishni xohlaysizmi?",
    # --- Delete confirmations ---
    "Objects": "Obyektlar",
    "Yes, I'm sure": "Ha, ishonchim komil",
    "No, take me back": "Yo'q, ortga qaytar",
    "Delete multiple objects": "Bir nechta obyektni o'chirish",
    "Are you sure you want to delete the %(object_name)s \"%(escaped_object)s\"? "
    "All of the following related items will be deleted:":
        "\"%(escaped_object)s\" nomli %(object_name)s ni o'chirmoqchimisiz? "
        "Quyidagi bog'liq elementlarning barchasi o'chiriladi:",
    "Are you sure you want to delete the selected %(objects_name)s? "
    "All of the following objects and their related items will be deleted:":
        "Tanlangan %(objects_name)s ni o'chirmoqchimisiz? "
        "Quyidagi obyektlar va ularga bog'liq elementlarning barchasi o'chiriladi:",
    "Added:": "Qo'shildi:",
    "Changed:": "O'zgartirildi:",
    "Deleted:": "O'chirildi:",
    "Unknown content": "Noma'lum kontent",
}

# Strings from django.contrib.auth's own uz catalog (separate from
# contrib.admin's, which `src` below is read from) that Django's official
# translation still leaves blank — e.g. the login form's "username" field
# label (AbstractUser.username verbose_name; "password" is already covered).
DJANGO_AUTH_UZ = {
    "username": "foydalanuvchi nomi",
}

# Plural entries — Uzbek uses a single plural form (nplurals=1).
UZ_PLURAL = {
    "%(count)s %(name)s was changed successfully.":
        {0: "%(count)s ta %(name)s muvaffaqiyatli o'zgartirildi."},
    "%(total_count)s selected": {0: "%(total_count)s ta tanlandi"},
    "Please correct the error below.": {0: "Quyidagi xatolarni tuzating."},
    "entry": {0: "yozuv"},
    "%(counter)s result": {0: "%(counter)s ta natija"},
}

UZ = {norm(k): v for k, v in UZ.items()}
UZ_PLURAL = {norm(k): v for k, v in UZ_PLURAL.items()}


def main():
    src = polib.pofile(DJANGO_UZ)
    out = polib.POFile()
    out.metadata = {
        "Project-Id-Version": "tagayev-admin-uz 1.0",
        "Report-Msgid-Bugs-To": "",
        "POT-Creation-Date": "2026-06-08 00:00+0500",
        "PO-Revision-Date": "2026-06-08 00:00+0500",
        "Last-Translator": "tagayev",
        "Language-Team": "uz",
        "Language": "uz",
        "MIME-Version": "1.0",
        "Content-Type": "text/plain; charset=UTF-8",
        "Content-Transfer-Encoding": "8bit",
        "Plural-Forms": "nplurals=1; plural=0;",
    }

    used, used_plural, missing = set(), set(), []
    for entry in src:
        if entry.msgid_plural:
            forms = UZ_PLURAL.get(norm(entry.msgid))
            if forms:
                out.append(polib.POEntry(
                    msgid=entry.msgid, msgid_plural=entry.msgid_plural,
                    msgstr_plural=forms,
                ))
                used_plural.add(norm(entry.msgid))
            continue
        uz = UZ.get(norm(entry.msgid))
        if uz:
            out.append(polib.POEntry(msgid=entry.msgid, msgstr=uz))
            used.add(norm(entry.msgid))

    # ---- Unfold UI strings (Unfold ships no uz catalog) -------------------
    uf_map = {norm(k): v for k, v in UNFOLD_UZ.items()}
    seen = {e.msgid for e in out}
    unfold_count = 0
    for mid in sorted(unfold_msgids()):
        if mid in seen:
            continue
        val = uf_map.get(norm(mid))
        if val:
            out.append(polib.POEntry(msgid=mid, msgstr=val))
            seen.add(mid)
            unfold_count += 1

    # Curated Unfold strings that live in Python (_()) rather than templates —
    # e.g. "Select record" in unfold/admin.py — are not found by
    # unfold_msgids() (templates only). Emit them by their exact msgid key.
    for key, val in UNFOLD_UZ.items():
        if val and key not in seen:
            out.append(polib.POEntry(msgid=key, msgstr=val))
            seen.add(key)
            unfold_count += 1

    # ---- django.contrib.auth gaps (not sourced from contrib.admin's po) ---
    auth_count = 0
    for key, val in DJANGO_AUTH_UZ.items():
        if val and key not in seen:
            out.append(polib.POEntry(msgid=key, msgstr=val))
            seen.add(key)
            auth_count += 1

    lc_dir = os.path.join(BASE, "locale", "uz", "LC_MESSAGES")
    os.makedirs(lc_dir, exist_ok=True)
    po_path = os.path.join(lc_dir, "django.po")
    mo_path = os.path.join(lc_dir, "django.mo")
    out.save(po_path)
    out.save_as_mofile(mo_path)

    # Report any map entries that did not match a Django msgid (typo guard).
    for key in UZ:
        if key not in used:
            missing.append(key)
    for key in UZ_PLURAL:
        if key not in used_plural:
            missing.append(key + " (plural)")

    print("Wrote %d singular + %d plural Django + %d Unfold + %d auth uz overrides."
          % (len(used), len(used_plural), unfold_count, auth_count))
    print("  po=%s" % po_path)
    print("  mo=%s" % mo_path)
    if missing:
        print("  UNMATCHED map keys (check spelling vs Django msgid):")
        for m in missing:
            print("    - %r" % m)


if __name__ == "__main__":
    main()
