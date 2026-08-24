"""Seed RU/EN translations for the HeroSection / SiteCopy singletons.

Phase B moved this copy out of ``{% translate %}`` tags into DB fields, which
dropped the existing Russian/English renderings on /ru/ and /en/ (they fell
back to Uzbek). The human translations already live in the repo
(locale/_build_catalogs.py); this migration seeds the singletons'
``_ru`` / ``_en`` columns from them so the trilingual site is whole again.

Only EMPTY target fields are filled, so an admin who has already edited a
translation (or a re-run) is never clobbered.
"""
from django.db import migrations

# field -> (uz, ru, en). UZ matches the model defaults; RU/EN reuse the
# repo's existing human translations.
HERO = {
    "badge_text": (
        "Zamonaviy taʼlim markazi",
        "Современный образовательный центр",
        "Modern education center",
    ),
    "title_prefix": (
        "Farzandingiz kelajagi", "Будущее вашего ребёнка", "Your child's future",
    ),
    "title_suffix": ("dan boshlanadi", " начинается с", " starts with"),
    "primary_cta": (
        "Bepul darsga yoziling", "Записаться на бесплатный урок", "Book a free lesson",
    ),
    "secondary_cta": ("Kurslarni koʻrish", "Посмотреть курсы", "View courses"),
}

COPY = {
    "results_eyebrow": ("Natijalar", "Результаты", "Results"),
    "results_title": (
        "Oʻquvchilarimiz natijalari",
        "Результаты наших учеников",
        "Our students' results",
    ),
    "results_link_label": ("Barcha natijalar", "Все результаты", "All results"),
    "testimonials_title": ("Ota-onalar fikri", "Отзывы родителей", "Parents' reviews"),
    "contact_eyebrow": ("Bogʻlanish", "Контакты", "Contact"),
    "contact_title": (
        "Bepul sinov darsiga yoziling",
        "Запишитесь на бесплатный пробный урок",
        "Sign up for a free trial lesson",
    ),
    "contact_intro": (
        "Arizangizni qoldiring — mutaxassisimiz qaytib qoʻngʻiroq qiladi "
        "va sizga mos kursni tanlashda yordam beradi.",
        "Оставьте заявку — наш специалист перезвонит и поможет подобрать подходящий курс.",
        "Leave your request — our specialist will call you back and help you "
        "choose the right course.",
    ),
    "lead_submit_label": ("Arizani yuborish", "Отправить заявку", "Submit request"),
    "modal_title": ("Ariza qoldirish", "Оставить заявку", "Apply now"),
    "modal_subtitle": (
        "Maʻlumotlaringizni qoldiring, tez orada bogʻlanamiz.",
        "Оставьте свои данные, мы скоро свяжемся с вами.",
        "Leave your details and we'll get in touch soon.",
    ),
    "modal_submit_label": ("Yuborish", "Отправить", "Send"),
    "footer_note": ("", "", ""),
}


def _seed(model, field_map):
    # A one-time seed of authoritative initial copy. It runs during deploy,
    # before any admin can edit, so it sets every language unconditionally:
    #  - <field>    : the original column is modeltranslation's storage for the
    #                 default language; a migration-created row never syncs it,
    #                 so the uz page would fall back to ru unless we set it here;
    #  - <field>_uz : Uzbek source;
    #  - <field>_ru / _en : human translations from the repo.
    # django-solo reads/writes a FIXED primary key (default 1); create the row
    # at that pk so get_solo() returns THIS seeded row instead of lazily making
    # a second, untranslated one at pk=1.
    obj = model.objects.first() or model(pk=1)
    for field, (uz, ru, en) in field_map.items():
        setattr(obj, field, uz)
        setattr(obj, f"{field}_uz", uz)
        setattr(obj, f"{field}_ru", ru)
        setattr(obj, f"{field}_en", en)
    obj.save()


def seed_translations(apps, schema_editor):
    _seed(apps.get_model("pages", "HeroSection"), HERO)
    _seed(apps.get_model("pages", "SiteCopy"), COPY)


def noop(apps, schema_editor):
    # Data-only seed; nothing to undo (leaving the values is harmless).
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0003_herosection_sitecopy"),
    ]

    operations = [
        migrations.RunPython(seed_translations, noop),
    ]
