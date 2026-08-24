from django import forms
from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TabbedTranslationAdmin
from solo.admin import SingletonModelAdmin
from unfold.admin import ModelAdmin

from apps.common.admin import AutoTranslateAdminMixin

from .models import SiteConfig, SocialLink, TelegramRecipient
from .widgets import BrandColorWidget, LeafletLocationWidget


@admin.register(SocialLink)
class SocialLinkAdmin(ModelAdmin):
    list_display = ("__str__", "platform", "url", "is_active", "order")
    list_editable = ("is_active", "order")
    list_filter = ("platform", "is_active")


@admin.register(TelegramRecipient)
class TelegramRecipientAdmin(ModelAdmin):
    list_display = ("__str__", "chat_id", "is_active")
    list_editable = ("is_active",)
    list_filter = ("is_active",)
    search_fields = ("name", "chat_id")


class SiteConfigForm(forms.ModelForm):
    # --- Telegram bot token: write-only / one-time entry ---------------------
    # The stored token is a secret: once saved it must never be shown back to an
    # operator (even a different admin). So the field renders as an *empty*
    # password box on every load (`render_value=False`), and submitting it empty
    # keeps the existing value untouched — an admin can rotate the token but can
    # never read the current one. To deliberately drop the panel token (and fall
    # back to the .env value) the operator ticks `clear_telegram_bot_token`.
    telegram_bot_token = forms.CharField(
        label=_("Telegram bot tokeni"),
        required=False,
        widget=forms.PasswordInput(
            render_value=False,
            attrs={"autocomplete": "new-password", "placeholder": "••••••••••"},
        ),
        help_text=_(
            "Xavfsizlik uchun saqlangan token qayta koʻrsatilmaydi. "
            "Boʻsh qoldirilsa — oʻzgarmaydi; yangi token kiritilsa — ustiga yoziladi."
        ),
    )
    clear_telegram_bot_token = forms.BooleanField(
        label=_("Saqlangan tokenni oʻchirish"),
        required=False,
        help_text=_("Belgilansa, paneldagi token oʻchiriladi va .env qiymati ishlatiladi."),
    )

    class Meta:
        model = SiteConfig
        fields = "__all__"
        widgets = {
            "latitude": LeafletLocationWidget(),
            "brand_primary": BrandColorWidget(fallback="#7a45e0", presets=True),
            "brand_accent": BrandColorWidget(fallback="#c9a961"),
        }

    def clean(self):
        cleaned = super().clean()
        submitted = (cleaned.get("telegram_bot_token") or "").strip()
        if cleaned.get("clear_telegram_bot_token"):
            cleaned["telegram_bot_token"] = ""
        elif submitted:
            cleaned["telegram_bot_token"] = submitted
        else:
            # Empty and not clearing → preserve the stored token (write-only).
            cleaned["telegram_bot_token"] = self.instance.telegram_bot_token
        return cleaned


@admin.register(SiteConfig)
class SiteConfigAdmin(AutoTranslateAdminMixin, ModelAdmin, TabbedTranslationAdmin, SingletonModelAdmin):
    form = SiteConfigForm
    readonly_fields = ("telegram_bot_token_status",)

    @admin.display(description=_("Token holati"))
    def telegram_bot_token_status(self, obj):
        """Read-only indicator so an admin knows a token is set without seeing it."""
        if obj and obj.telegram_bot_token:
            return format_html('<b style="color:#16a34a">{}</b>', _("✓ Oʻrnatilgan (panel)"))
        if getattr(settings, "TELEGRAM_BOT_TOKEN", ""):
            return format_html('<span style="color:#64748b">{}</span>', _("• .env qiymati ishlatiladi"))
        return format_html('<b style="color:#dc2626">{}</b>', _("✗ Oʻrnatilmagan"))

    fieldsets = (
        (_("Brending"), {
            "fields": ("site_name", "tagline", "logo", "favicon", "site_domain"),
        }),
        (_("Brend ranglari"), {
            "fields": ("brand_primary", "brand_accent"),
        }),
        (_("Kontaktlar"), {
            "fields": ("phone_primary", "phone_secondary", "email", "address", "working_hours"),
        }),
        (_("Joylashuv (xaritadan tanlang)"), {
            "fields": ("latitude", "longitude"),
            "description": _("Xaritani bosib yoki qidirib joylashuvni tanlang. "
                             "Google va Yandex xaritalari shu koordinatalardan avtomatik chiqadi."),
        }),
        (_("Google xarita — qo‘lda override (ixtiyoriy)"), {
            "fields": ("google_maps_embed",),
            "classes": ("collapse",),
            "description": _("Faqat maxsus Google embed kerak bo‘lsa to‘ldiring. Bo‘sh "
                             "qoldirilsa, yuqoridagi koordinatalardan foydalaniladi."),
        }),
        (_("SEO"), {
            "fields": ("seo_title", "seo_description", "og_image",
                       "google_site_verification", "yandex_verification", "bing_msvalidate"),
            "classes": ("collapse",),
        }),
        (_("Analitika"), {
            "fields": ("ga4_measurement_id", "yandex_metrica_id"),
            "classes": ("collapse",),
        }),
        (_("Telegram"), {
            "fields": (
                "telegram_notifications_enabled",
                "telegram_bot_token_status",
                "telegram_bot_token",
                "clear_telegram_bot_token",
            ),
            "classes": ("collapse",),
            "description": _("Bot tokenini kiriting, soʻng «Telegram qabul qiluvchilar» boʻlimida arizalarni qabul qiladigan adminlarni qoʻshing — bir nechta admin qoʻshish mumkin. Xavfsizlik uchun token bir marta yoziladi va qaytadan koʻrsatilmaydi."),
        }),
    )
