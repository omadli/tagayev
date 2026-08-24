"""Tests for apps.siteconfig."""
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.siteconfig.models import SiteConfig, SocialLink, TelegramRecipient

User = get_user_model()

_STATIC_STORAGE = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}


class SiteConfigModelTests(TestCase):
    """SiteConfig model behaviour."""

    def _get_config(self, **kwargs):
        """Fetch or create the singleton, update fields, save."""
        config = SiteConfig.get_solo()
        for k, v in kwargs.items():
            setattr(config, k, v)
        config.save()
        return config

    def test_str(self):
        config = SiteConfig.get_solo()
        self.assertEqual(str(config), "Sayt sozlamalari")

    def test_phone_normalization_spaced(self):
        config = self._get_config(phone_primary="+998 90 123 45 67")
        self.assertEqual(config.phone_primary, "+998901234567")

    def test_phone_normalization_9digit(self):
        config = self._get_config(phone_primary="901234567")
        self.assertEqual(config.phone_primary, "+998901234567")

    def test_phone_secondary_normalization(self):
        config = self._get_config(phone_secondary="+998 71 200 00 00")
        self.assertEqual(config.phone_secondary, "+998712000000")

    def test_blank_phone_stays_blank(self):
        config = self._get_config(phone_primary="", phone_secondary="")
        self.assertEqual(config.phone_primary, "")
        self.assertEqual(config.phone_secondary, "")

    def test_has_geo_false_when_empty(self):
        config = self._get_config(latitude="", longitude="")
        self.assertFalse(config.has_geo)

    def test_has_geo_true_when_set(self):
        config = self._get_config(latitude="41.299496", longitude="69.240073")
        self.assertTrue(config.has_geo)


@override_settings(STORAGES=_STATIC_STORAGE)
class SiteConfigAdminTests(TestCase):
    """Admin siteconfig pages return 200."""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin_siteconfig",
            password="adminpass123",
            email="admin_siteconfig@test.com",
        )
        self.client.force_login(self.superuser)

    def _get(self, url):
        return self.client.get(url, follow=True)

    def test_siteconfig_changelist(self):
        """Singleton admin changelist redirects to change page — follow=True → 200."""
        url = reverse("admin:siteconfig_siteconfig_changelist")
        self.assertEqual(self._get(url).status_code, 200)

    def test_siteconfig_change(self):
        """Singleton change page (pk=1 after get_solo())."""
        SiteConfig.get_solo()  # ensure the singleton exists
        url = reverse("admin:siteconfig_siteconfig_change", args=[1])
        self.assertEqual(self._get(url).status_code, 200)


# ---------------------------------------------------------------------------
# Phase F — repeatable SocialLink
# ---------------------------------------------------------------------------
class SocialLinkModelTests(TestCase):
    def test_str_uses_platform_when_no_label(self):
        s = SocialLink(platform="instagram", url="https://instagram.com/x")
        self.assertEqual(str(s), "Instagram")

    def test_str_uses_custom_label(self):
        s = SocialLink(platform="instagram", label="Bizning IG", url="https://instagram.com/x")
        self.assertEqual(str(s), "Bizning IG")

    def test_telegram_group_shares_telegram_icon(self):
        s = SocialLink(platform="telegram_group", url="https://t.me/g")
        self.assertEqual(s.icon_key, "telegram")

    def test_icon_key_default(self):
        s = SocialLink(platform="youtube", url="https://youtube.com/x")
        self.assertEqual(s.icon_key, "youtube")


@override_settings(STORAGES=_STATIC_STORAGE)
class SocialLinkRenderTests(TestCase):
    def test_link_renders_in_footer_and_jsonld(self):
        SocialLink.objects.create(
            platform="telegram", url="https://t.me/tagayev_demo", is_active=True)
        body = self.client.get("/uz/", follow=True).content.decode("utf-8", "replace")
        self.assertIn("https://t.me/tagayev_demo", body)      # footer icon link
        self.assertIn('"sameAs"', body)                     # JSON-LD block present

    def test_inactive_link_not_rendered(self):
        SocialLink.objects.create(
            platform="tiktok", url="https://tiktok.com/@hidden", is_active=False)
        body = self.client.get("/uz/", follow=True).content.decode("utf-8", "replace")
        self.assertNotIn("tiktok.com/@hidden", body)


@override_settings(STORAGES=_STATIC_STORAGE)
class SocialLinkAdminTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin_social", password="adminpass123", email="s@test.com")
        self.client.force_login(self.superuser)

    def test_changelist(self):
        url = reverse("admin:siteconfig_sociallink_changelist")
        self.assertEqual(self.client.get(url, follow=True).status_code, 200)

    def test_add(self):
        url = reverse("admin:siteconfig_sociallink_add")
        self.assertEqual(self.client.get(url, follow=True).status_code, 200)


# ---------------------------------------------------------------------------
# TelegramRecipient — multiple admins receive ariza notifications
# ---------------------------------------------------------------------------
class TelegramRecipientModelTests(TestCase):
    def test_str_prefers_name(self):
        r = TelegramRecipient(name="Direktor", chat_id="123456789")
        self.assertEqual(str(r), "Direktor")

    def test_str_falls_back_to_chat_id(self):
        r = TelegramRecipient(chat_id="123456789")
        self.assertEqual(str(r), "123456789")

    def test_numeric_chat_id_is_valid(self):
        r = TelegramRecipient(name="A", chat_id="123456789")
        r.full_clean()  # should not raise

    def test_negative_group_chat_id_is_valid(self):
        r = TelegramRecipient(name="Guruh", chat_id="-1001234567890")
        r.full_clean()

    def test_username_chat_id_is_valid(self):
        r = TelegramRecipient(name="Kanal", chat_id="@tagayev_admin")
        r.full_clean()

    def test_invalid_chat_id_rejected(self):
        r = TelegramRecipient(name="Bad", chat_id="not a chat id")
        with self.assertRaises(ValidationError):
            r.full_clean()


@override_settings(STORAGES=_STATIC_STORAGE)
class TelegramRecipientAdminTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin_tg", password="adminpass123", email="tg@test.com")
        self.client.force_login(self.superuser)

    def test_changelist(self):
        TelegramRecipient.objects.create(name="A", chat_id="111")
        url = reverse("admin:siteconfig_telegramrecipient_changelist")
        self.assertEqual(self.client.get(url, follow=True).status_code, 200)

    def test_add(self):
        url = reverse("admin:siteconfig_telegramrecipient_add")
        self.assertEqual(self.client.get(url, follow=True).status_code, 200)


# ---------------------------------------------------------------------------
# Telegram bot token — write-only / one-time entry (never readable back)
# ---------------------------------------------------------------------------
class TelegramBotTokenWriteOnlyTests(TestCase):
    """The stored bot token is a secret: it is never rendered back, an empty
    submit keeps it unchanged, a new value overwrites it, and the clear box
    drops it. See apps/siteconfig/admin.py:SiteConfigForm."""

    def _form(self, **extra):
        from apps.siteconfig.admin import SiteConfigForm
        data = {"site_name": "Tagayev Methods", "telegram_notifications_enabled": "on"}
        data.update(extra)
        return SiteConfigForm(data=data, instance=self.config)

    def setUp(self):
        self.config = SiteConfig.get_solo()
        self.config.telegram_bot_token = "SECRET-EXISTING-TOKEN"
        self.config.save()

    def test_empty_submit_keeps_existing_token(self):
        form = self._form()
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["telegram_bot_token"], "SECRET-EXISTING-TOKEN")

    def test_new_token_overwrites(self):
        form = self._form(telegram_bot_token="NEW-TOKEN-999")
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["telegram_bot_token"], "NEW-TOKEN-999")

    def test_clear_checkbox_empties_token(self):
        form = self._form(clear_telegram_bot_token="on")
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["telegram_bot_token"], "")

    def test_widget_never_renders_stored_token(self):
        from apps.siteconfig.admin import SiteConfigForm
        html = str(SiteConfigForm(instance=self.config)["telegram_bot_token"])
        self.assertNotIn("SECRET-EXISTING-TOKEN", html)
        self.assertIn('type="password"', html)


@override_settings(STORAGES=_STATIC_STORAGE)
class TelegramBotTokenAdminLeakTests(TestCase):
    """The rendered admin change page must not leak the saved token."""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin_token", password="adminpass123", email="t@test.com")
        self.client.force_login(self.superuser)
        self.config = SiteConfig.get_solo()
        self.config.telegram_bot_token = "SECRET-TOKEN-IN-PAGE"
        self.config.save()

    def test_change_page_does_not_leak_token(self):
        url = reverse("admin:siteconfig_siteconfig_change", args=[self.config.pk])
        body = self.client.get(url, follow=True).content.decode("utf-8", "replace")
        self.assertNotIn("SECRET-TOKEN-IN-PAGE", body)


# ---------------------------------------------------------------------------
# Analytics IDs are echoed into inline <script> — validate their format (XSS)
# ---------------------------------------------------------------------------
class AnalyticsIdValidationTests(TestCase):
    def _full_clean(self, **kwargs):
        config = SiteConfig.get_solo()
        for k, v in kwargs.items():
            setattr(config, k, v)
        config.full_clean()

    def test_valid_ga4_id_passes(self):
        self._full_clean(ga4_measurement_id="G-ABC1234567")

    def test_valid_metrica_id_passes(self):
        self._full_clean(yandex_metrica_id="12345678")

    def test_script_payload_in_ga4_is_rejected(self):
        with self.assertRaises(ValidationError):
            self._full_clean(ga4_measurement_id="1);alert(1);//")

    def test_script_payload_in_metrica_is_rejected(self):
        with self.assertRaises(ValidationError):
            self._full_clean(yandex_metrica_id="1);alert(document.cookie);//")


# ---------------------------------------------------------------------------
# Map-embed sanitizer — strips scripts, keeps only allowlisted-host iframes
# ---------------------------------------------------------------------------
class MapEmbedSanitizeTests(TestCase):
    def test_script_is_stripped(self):
        from apps.siteconfig.models import sanitize_map_embed
        out = sanitize_map_embed('<iframe src="https://www.google.com/maps?x=1"></iframe>'
                                 '<script>alert(1)</script>')
        self.assertNotIn("<script", out)
        self.assertIn("<iframe", out)

    def test_non_allowlisted_host_is_dropped(self):
        from apps.siteconfig.models import sanitize_map_embed
        self.assertEqual(sanitize_map_embed('<iframe src="https://evil.example/x"></iframe>'), "")

    def test_javascript_scheme_is_dropped(self):
        from apps.siteconfig.models import sanitize_map_embed
        out = sanitize_map_embed('<iframe src="javascript:alert(1)"></iframe>')
        self.assertNotIn("javascript:", out)

    def test_blank_returns_empty(self):
        from apps.siteconfig.models import sanitize_map_embed
        self.assertEqual(sanitize_map_embed(""), "")

    def test_safe_property_uses_sanitizer(self):
        config = SiteConfig.get_solo()
        config.google_maps_embed = '<iframe src="https://www.google.com/maps?q=1"></iframe><script>x</script>'
        self.assertIn("<iframe", config.safe_google_maps_embed)
        self.assertNotIn("<script", config.safe_google_maps_embed)


@override_settings(STORAGES=_STATIC_STORAGE)
class BrandColorTests(TestCase):
    """Admin-set brand colours reach <html> as custom properties; source.css
    derives every shade from them, so no Tailwind rebuild is involved."""

    def _home(self):
        return self.client.get("/uz/", follow=True).content.decode("utf-8", "replace")

    def test_no_attribute_when_unset(self):
        body = self._home()
        self.assertNotIn("data-brand-p", body)
        self.assertNotIn("--brand-p", body)

    def test_primary_only_sets_its_own_hook(self):
        config = SiteConfig.get_solo()
        config.brand_primary = "#0f766e"
        config.save()
        body = self._home()
        self.assertIn("data-brand-p", body)
        self.assertIn("--brand-p:#0f766e;", body)
        self.assertNotIn("data-brand-a", body)   # accent keeps the default palette

    def test_both_colors_render(self):
        config = SiteConfig.get_solo()
        config.brand_primary = "#0f766e"
        config.brand_accent = "#b45309"
        config.save()
        body = self._home()
        self.assertIn("data-brand-p", body)
        self.assertIn("data-brand-a", body)
        self.assertIn("--brand-a:#b45309;", body)

    def test_non_hex_is_rejected(self):
        # The value lands inside an inline style attribute, so anything that is
        # not a literal #RRGGBB must fail validation, not get escaped later.
        for bad in ("red", "#fff", "#7a45e0;}", "url(javascript:alert(1))"):
            config = SiteConfig(site_name="x", brand_primary=bad)
            with self.assertRaises(ValidationError, msg=bad):
                config.full_clean()


@override_settings(STORAGES=_STATIC_STORAGE)
class AdminBrandPaletteTests(TestCase):
    """The admin chrome follows the same palette as the public site."""

    def setUp(self):
        User = get_user_model()
        self.client.force_login(User.objects.create_superuser(
            username="admin_brand", password="x", email="b@t.uz"))

    def test_shade_ladder_endpoints(self):
        from apps.siteconfig.models import shade
        self.assertEqual(shade("#7a45e0", 100), "122 69 224")   # 500 = the colour itself
        self.assertEqual(shade("#000000", 8), "235 235 235")    # 8% of black into white
        self.assertEqual(shade("#ffffff", -50), "128 128 128")  # 50% of white into black

    def test_palette_empty_until_a_colour_is_set(self):
        self.assertEqual(SiteConfig.get_solo().brand_palette, {})

    def test_admin_emits_override_only_when_set(self):
        url = reverse("admin:siteconfig_siteconfig_changelist")
        # Unfold always prints its own :root palette, so the marker for OUR
        # override is the html:root selector, not the variable name.
        self.assertNotIn("html:root", self.client.get(url, follow=True)
                         .content.decode("utf-8", "replace"))
        config = SiteConfig.get_solo()
        config.brand_primary = "#0f766e"
        config.save()
        body = self.client.get(url, follow=True).content.decode("utf-8", "replace")
        # html:root, not :root — Unfold prints its own :root block later in the
        # document, so the override has to win on specificity.
        self.assertIn("html:root", body)
        self.assertIn("--color-primary-500: 15 118 110;", body)
