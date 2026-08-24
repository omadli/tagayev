import re

import nh3
from django.core.validators import RegexValidator
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from solo.models import SingletonModel

from apps.common.models import OrderedActiveModel, TimeStampedModel
from apps.common.utils import normalize_phone
from apps.common.validators import image_validators

# A Telegram chat id is numeric (negative for groups/channels) or an @username.
telegram_chat_id_validator = RegexValidator(
    regex=r"^(-?\d+|@[A-Za-z0-9_]{4,})$",
    message=_("Chat ID raqam (masalan: 123456789 yoki -1001234567890) yoki @username koʻrinishida boʻlishi kerak."),
)

# Analytics IDs are echoed verbatim into inline <script> blocks, so their format
# is validated strictly to shut the door on script/JS-context injection (stored
# XSS) — only the real vendor shapes are accepted.
ga4_measurement_id_validator = RegexValidator(
    regex=r"^(G-[A-Z0-9]{4,20}|UA-\d{4,10}-\d{1,4})$",
    message=_("Google Analytics ID G-XXXXXXX (yoki UA-XXXX-Y) koʻrinishida boʻlishi kerak."),
)
# Brand colours are echoed into an inline style="" on <html>. Same reasoning as
# the analytics IDs above: accept only a literal 6-digit hex so nothing can break
# out of the attribute or the CSS value.
hex_color_validator = RegexValidator(
    regex=r"^#[0-9a-fA-F]{6}$",
    message=_("Rang #RRGGBB koʻrinishida boʻlishi kerak (masalan: #7a45e0)."),
)

yandex_metrica_id_validator = RegexValidator(
    regex=r"^\d{4,12}$",
    message=_("Yandex Metrica ID faqat raqamlardan iborat boʻlishi kerak (masalan: 12345678)."),
)

# Manual map-embed fields hold operator-supplied HTML rendered with |safe. Run
# it through nh3 first: only an <iframe> with https-scheme src (from an allowed
# maps host) and a few layout attributes survive — <script>, event handlers and
# javascript:/data: URLs are stripped, closing the stored-XSS hole.
_EMBED_TAGS = {"iframe"}
_EMBED_ATTRS = {
    "iframe": {
        "src", "width", "height", "style", "title",
        "allow", "allowfullscreen", "loading", "referrerpolicy", "frameborder",
    }
}
_EMBED_ALLOWED_HOSTS = (
    "google.com", "maps.google.com", "www.google.com",
    "yandex.com", "yandex.ru", "maps.yandex.com", "maps.yandex.ru",
    "yandex.uz", "maps.yandex.uz",
)


def sanitize_map_embed(raw):
    """Return a safe, mark_safe'd <iframe> embed (or '') from operator HTML."""
    if not raw or not raw.strip():
        return ""
    from urllib.parse import urlparse

    cleaned = nh3.clean(
        raw,
        tags=_EMBED_TAGS,
        attributes=_EMBED_ATTRS,
        url_schemes={"https"},
    )
    # Host allowlist: keep the iframe only if its src points at a known maps host
    # (nh3 already dropped scripts / non-https URLs; this blocks arbitrary sites).
    src_match = re.search(r'src="([^"]+)"', cleaned)
    if not src_match:
        return ""
    host = (urlparse(src_match.group(1)).hostname or "").lower()
    if not any(host == h or host.endswith("." + h) for h in _EMBED_ALLOWED_HOSTS):
        return ""
    return mark_safe(cleaned)


class SiteConfig(SingletonModel):
    """Global, admin-managed site configuration (single row)."""

    # --- Branding ---
    site_name = models.CharField(_("Sayt nomi"), max_length=120, default="Tagayev Methods")
    tagline = models.CharField(_("Shior"), max_length=200, blank=True)
    logo = models.ImageField(_("Logo"), upload_to="branding/", blank=True,
                             validators=image_validators,
                             help_text=_("Bo'sh qoldirilsa, standart logo ishlatiladi."))
    favicon = models.ImageField(_("Favicon"), upload_to="branding/", blank=True,
                                validators=image_validators)

    # --- Brand colours ---
    # Blank = the stylesheet's built-in palette. When set, base.html hangs the
    # value off <html> and source.css derives every shade/gradient from it via
    # color-mix() — no Tailwind rebuild, no per-shade fields to fill in.
    brand_primary = models.CharField(
        _("Asosiy rang"), max_length=7, blank=True, validators=[hex_color_validator],
        help_text=_("#RRGGBB. Havolalar, sarlavhalar, gradientlar. Boʻsh = standart binafsha."),
    )
    brand_accent = models.CharField(
        _("Aksent rang"), max_length=7, blank=True, validators=[hex_color_validator],
        help_text=_("#RRGGBB. Tugmalar va belgilar. Boʻsh = standart tilla."),
    )

    # --- Canonical domain (SEO uchun yagona manba) ---
    site_domain = models.CharField(
        _("Domen"), max_length=120, blank=True,
        help_text=_("Masalan: tagayev.uz (protokolsiz). Sitemap/canonical uchun."),
    )

    # --- Contacts ---
    phone_primary = models.CharField(_("Asosiy telefon"), max_length=30, blank=True)
    phone_secondary = models.CharField(_("Qo'shimcha telefon"), max_length=30, blank=True)
    email = models.EmailField(_("Email"), blank=True)
    address = models.CharField(_("Manzil"), max_length=255, blank=True)
    working_hours = models.CharField(_("Ish vaqti"), max_length=120, blank=True)
    latitude = models.CharField(_("Kenglik (lat)"), max_length=32, blank=True)
    longitude = models.CharField(_("Uzunlik (lng)"), max_length=32, blank=True)

    # --- Maps: coordinates drive the iframes; this optional field overrides the
    # Google map with a hand-pasted embed (sanitized by safe_google_maps_embed). ---
    google_maps_embed = models.TextField(_("Google Maps embed"), blank=True)

    # --- Social links are now managed via the repeatable SocialLink model ---

    # --- SEO defaults ---
    seo_title = models.CharField(_("SEO sarlavha"), max_length=200, blank=True)
    seo_description = models.TextField(_("SEO tavsif"), blank=True)
    og_image = models.ImageField(_("OG rasm (ulashish)"), upload_to="seo/", blank=True,
                                 validators=image_validators)

    # --- Webmaster verification ---
    google_site_verification = models.CharField(_("Google verification"), max_length=255, blank=True)
    yandex_verification = models.CharField(_("Yandex verification"), max_length=255, blank=True)
    bing_msvalidate = models.CharField(_("Bing verification"), max_length=255, blank=True)

    # --- Analytics IDs ---
    ga4_measurement_id = models.CharField(_("Google Analytics 4 ID"), max_length=40, blank=True,
                                          validators=[ga4_measurement_id_validator],
                                          help_text="G-XXXXXXX")
    yandex_metrica_id = models.CharField(_("Yandex Metrica ID"), max_length=40, blank=True,
                                         validators=[yandex_metrica_id_validator])

    # --- Telegram ---
    telegram_notifications_enabled = models.BooleanField(
        _("Telegram bildirishnomalari yoniq"), default=True,
    )
    telegram_bot_token = models.CharField(
        _("Telegram bot tokeni"), max_length=128, blank=True,
        help_text=_("@BotFather bergan token. Boʻsh qoldirilsa, serverdagi .env qiymati ishlatiladi."),
    )

    class Meta:
        verbose_name = _("Sayt sozlamalari")
        verbose_name_plural = _("Sayt sozlamalari")

    def __str__(self):
        return "Sayt sozlamalari"

    def save(self, *args, **kwargs):
        self.phone_primary = normalize_phone(self.phone_primary)
        self.phone_secondary = normalize_phone(self.phone_secondary)
        super().save(*args, **kwargs)

    # --- Safe manual Google Maps embed (sanitized; rendered with |safe) ---
    @property
    def safe_google_maps_embed(self):
        return sanitize_map_embed(self.google_maps_embed)

    @property
    def has_geo(self):
        """True when coordinates are set (drives JSON-LD geo + the map iframes,
        whose src URLs are built by the ui.py google_map_src/yandex_map_src tags)."""
        return bool(self.latitude and self.longitude)


class SocialLink(OrderedActiveModel):
    """A site-wide social network link. Repeatable so links can be added/removed
    freely; the platform drives the brand icon (see social_icon template tag)."""

    class Platform(models.TextChoices):
        INSTAGRAM = "instagram", "Instagram"
        TELEGRAM = "telegram", "Telegram"
        TELEGRAM_GROUP = "telegram_group", _("Telegram guruh")
        YOUTUBE = "youtube", "YouTube"
        FACEBOOK = "facebook", "Facebook"
        TIKTOK = "tiktok", "TikTok"
        TWITTER = "twitter", "X (Twitter)"
        LINKEDIN = "linkedin", "LinkedIn"
        WHATSAPP = "whatsapp", "WhatsApp"
        WEBSITE = "website", _("Veb-sayt")

    platform = models.CharField(_("Platforma"), max_length=20, choices=Platform.choices)
    label = models.CharField(
        _("Nomi (ixtiyoriy)"), max_length=60, blank=True,
        help_text=_("Boʻsh qoldirilsa, platforma nomi ishlatiladi."),
    )
    url = models.URLField(_("Havola"))

    class Meta(OrderedActiveModel.Meta):
        verbose_name = _("Ijtimoiy tarmoq")
        verbose_name_plural = _("Ijtimoiy tarmoqlar")

    def __str__(self):
        return self.label or self.get_platform_display()

    @property
    def display_label(self):
        return self.label or self.get_platform_display()

    @property
    def icon_key(self):
        # telegram_group shares the telegram brand icon
        return "telegram" if self.platform == self.Platform.TELEGRAM_GROUP else self.platform


class TelegramRecipient(TimeStampedModel):
    """A Telegram chat that receives new-application (ariza) notifications.

    Repeatable so several admins can be notified at once; toggle ``is_active``
    to stop notifying someone without deleting their entry. The bot token lives
    on ``SiteConfig`` — here we only keep *who* receives the messages."""

    name = models.CharField(
        _("Nomi"), max_length=120, blank=True,
        help_text=_("Kimligini eslatuvchi nom (masalan: Direktor). Ixtiyoriy."),
    )
    chat_id = models.CharField(
        _("Chat ID"), max_length=64, validators=[telegram_chat_id_validator],
        help_text=_("Raqamli chat ID (masalan: 123456789). Foydalanuvchi botga /start yozgach, @userinfobot orqali bilib olish mumkin."),
    )
    is_active = models.BooleanField(
        _("Faol"), default=True, db_index=True,
        help_text=_("Belgilanmasa, bu adminga arizalar yuborilmaydi."),
    )

    class Meta:
        ordering = ["name", "chat_id"]
        verbose_name = _("Telegram qabul qiluvchi")
        verbose_name_plural = _("Telegram qabul qiluvchilar")

    def __str__(self):
        return self.name or self.chat_id
