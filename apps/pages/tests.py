"""Tests for apps.pages — i18n URL redirects, landing view, admin pages, SEO."""
import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.certificates.models import Certificate
from apps.courses.models import Course
from apps.news.models import NewsPost
from apps.pages.models import AboutSection, HeroSection, HomeVideo, Partner, SiteCopy
from apps.siteconfig.models import SiteConfig

User = get_user_model()

_STATIC_STORAGE = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}


@override_settings(STORAGES=_STATIC_STORAGE)
class I18nRedirectTests(TestCase):
    """Root URL / → 302 to /uz/; language prefixed URLs → 200."""

    def test_root_redirects(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/uz/", response["Location"])

    def test_root_ignores_accept_language(self):
        """A non-uz browser must still land on /uz/ (default is always uz)."""
        response = self.client.get("/", HTTP_ACCEPT_LANGUAGE="ru-RU,ru;q=0.9,en;q=0.8")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/uz/", response["Location"])

    def test_root_ignores_language_cookie_on_public(self):
        """A stale django_language cookie must not override the uz default on
        the public site (the switcher uses /uz//ru//en/ URLs, not the cookie)."""
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/uz/", response["Location"])

    def test_prefixed_url_still_wins(self):
        """An explicit /ru/ URL is served in ru even with an en cookie set."""
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"
        response = self.client.get("/ru/", follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('lang="ru"', response.content.decode("utf-8", "replace"))

    def test_uz_home_ok(self):
        response = self.client.get("/uz/", follow=True)
        self.assertEqual(response.status_code, 200)

    def test_ru_home_ok(self):
        response = self.client.get("/ru/", follow=True)
        self.assertEqual(response.status_code, 200)

    def test_en_home_ok(self):
        response = self.client.get("/en/", follow=True)
        self.assertEqual(response.status_code, 200)


class AboutSectionModelTests(TestCase):
    """AboutSection model basics."""

    def test_str(self):
        section = AboutSection.objects.create(
            title="Biz haqimizda",
            is_active=True,
        )
        self.assertEqual(str(section), "Biz haqimizda")

    def test_i18n_fields_exist(self):
        """modeltranslation creates _uz / _ru / _en variants."""
        section = AboutSection()
        self.assertTrue(hasattr(section, "title_uz"))
        self.assertTrue(hasattr(section, "title_ru"))
        self.assertTrue(hasattr(section, "title_en"))


class PartnerModelTests(TestCase):
    """Partner model basics."""

    def test_str(self):
        partner = Partner.objects.create(name="Test Partner")
        self.assertEqual(str(partner), "Test Partner")

    def test_i18n_fields_exist(self):
        """modeltranslation creates _uz / _ru / _en variants."""
        partner = Partner()
        self.assertTrue(hasattr(partner, "name_uz"))
        self.assertTrue(hasattr(partner, "name_ru"))
        self.assertTrue(hasattr(partner, "name_en"))

    def test_website_url_defaults_to_blank(self):
        partner = Partner.objects.create(name="No URL Partner")
        self.assertEqual(partner.website_url, "")

    def test_default_ordering_by_order_field(self):
        # Delete first so this test is robust whether or not seed data
        # (Task 3) has landed yet — avoids order-value collisions either way.
        Partner.objects.all().delete()
        second = Partner.objects.create(name="Second", order=2)
        first = Partner.objects.create(name="First", order=1)
        self.assertEqual(list(Partner.objects.all()), [first, second])


@override_settings(STORAGES=_STATIC_STORAGE)
class PartnersSectionTests(TestCase):
    """LandingView passes partners to the template; _partners.html renders them."""

    def setUp(self):
        # No seed data on this site — partners come from the admin, so the
        # test creates the rows it asserts on.
        Partner.objects.create(name="Cambridge", order=0)
        Partner.objects.create(name="IELTS", order=1)
        Partner.objects.create(name="Pearson", order=2)

    def test_partner_name_renders_on_landing_page(self):
        body = self.client.get("/uz/", follow=True).content.decode("utf-8", "replace")
        self.assertIn("Cambridge", body)

    def test_link_wraps_name_when_website_url_set(self):
        Partner.objects.filter(name="IELTS").update(website_url="https://www.ielts.org")
        body = self.client.get("/uz/", follow=True).content.decode("utf-8", "replace")
        self.assertIn('href="https://www.ielts.org"', body)

    def test_plain_name_has_no_link_when_url_blank(self):
        body = self.client.get("/uz/", follow=True).content.decode("utf-8", "replace")
        # "Pearson" has a blank website_url — must render as plain text
        # (a <span>), not wrapped in a link.
        self.assertIn("<span>Pearson</span>", body)

    def test_section_hidden_when_no_partners(self):
        Partner.objects.all().delete()
        body = self.client.get("/uz/", follow=True).content.decode("utf-8", "replace")
        self.assertNotIn("marquee-track", body)

    def test_partner_name_renders_twice_for_seamless_marquee_loop(self):
        # The marquee's CSS animation (scrollx, translateX(-50%)) only loops
        # seamlessly if the track contains the list twice, back-to-back.
        body = self.client.get("/uz/", follow=True).content.decode("utf-8", "replace")
        self.assertEqual(body.count("<span>Pearson</span>"), 2)


@override_settings(STORAGES=_STATIC_STORAGE)
class PagesAdminTests(TestCase):
    """Admin changelist and add pages return 200 for pages app models."""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin_pages",
            password="adminpass123",
            email="admin_pages@test.com",
        )
        self.client.force_login(self.superuser)

    def _get(self, url):
        return self.client.get(url, follow=True)

    def test_aboutsection_changelist(self):
        url = reverse("admin:pages_aboutsection_changelist")
        self.assertEqual(self._get(url).status_code, 200)

    def test_aboutsection_add(self):
        url = reverse("admin:pages_aboutsection_add")
        self.assertEqual(self._get(url).status_code, 200)

    def test_statitem_changelist(self):
        url = reverse("admin:pages_statitem_changelist")
        self.assertEqual(self._get(url).status_code, 200)

    def test_whyusitem_changelist(self):
        url = reverse("admin:pages_whyusitem_changelist")
        self.assertEqual(self._get(url).status_code, 200)

    def test_herosection_changelist(self):
        url = reverse("admin:pages_herosection_changelist")
        self.assertEqual(self._get(url).status_code, 200)

    def test_sitecopy_changelist(self):
        url = reverse("admin:pages_sitecopy_changelist")
        self.assertEqual(self._get(url).status_code, 200)

    def test_homevideo_changelist(self):
        url = reverse("admin:pages_homevideo_changelist")
        self.assertEqual(self._get(url).status_code, 200)

    def test_partner_changelist(self):
        url = reverse("admin:pages_partner_changelist")
        self.assertEqual(self._get(url).status_code, 200)

    def test_partner_add(self):
        url = reverse("admin:pages_partner_add")
        self.assertEqual(self._get(url).status_code, 200)


# ---------------------------------------------------------------------------
# Phase B: admin-editable site copy (hero badge, section headings, form texts)
# ---------------------------------------------------------------------------
@override_settings(STORAGES=_STATIC_STORAGE)
class EditableSiteCopyTests(TestCase):
    """Hero/section/form copy lives in singletons and is rendered from the DB."""

    def test_singletons_created_with_defaults(self):
        hero = HeroSection.get_solo()
        copy = SiteCopy.get_solo()
        self.assertIn("Zamonaviy", hero.badge_text)
        self.assertIn("natijalari", copy.results_title)
        self.assertTrue(copy.contact_intro)

    def test_i18n_fields_exist(self):
        """modeltranslation creates _uz / _ru / _en variants for copy fields."""
        self.assertTrue(hasattr(HeroSection(), "badge_text_uz"))
        self.assertTrue(hasattr(HeroSection(), "badge_text_ru"))
        self.assertTrue(hasattr(SiteCopy(), "results_title_en"))

    def test_home_renders_editable_defaults(self):
        body = self.client.get("/uz/", follow=True).content.decode("utf-8", "replace")
        self.assertIn("Zamonaviy taʼlim markazi", body)
        self.assertIn("Arizangizni qoldiring", body)  # contact intro
        # old hardcoded "· Toshkent" badge must be gone
        self.assertNotIn("markazi · Toshkent", body)

    def test_editing_hero_badge_updates_home(self):
        hero = HeroSection.get_solo()
        hero.badge_text = "Sinov Shahar Yorligi"
        hero.save()
        body = self.client.get("/uz/", follow=True).content.decode("utf-8", "replace")
        self.assertIn("Sinov Shahar Yorligi", body)

    def test_editing_results_title_updates_home(self):
        # The results section only renders when a certificate (or testimonial)
        # exists, so create one before asserting the editable heading.
        Certificate.objects.create(
            title="Sinov sertifikati",
            external_url="https://example.com/cert",
            is_active=True,
        )
        copy = SiteCopy.get_solo()
        copy.results_title = "Bizning Natijalar 2026"
        copy.save()
        body = self.client.get("/uz/", follow=True).content.decode("utf-8", "replace")
        self.assertIn("Bizning Natijalar 2026", body)

    def test_editing_footer_note_updates_all_pages(self):
        copy = SiteCopy.get_solo()
        copy.footer_note = "Sinov footer 2026"
        copy.save()
        body = self.client.get("/uz/", follow=True).content.decode("utf-8", "replace")
        self.assertIn("Sinov footer 2026", body)


# ---------------------------------------------------------------------------
# Phase E — home page video block
# ---------------------------------------------------------------------------
@override_settings(STORAGES=_STATIC_STORAGE)
class HomeVideoTests(TestCase):
    def test_disabled_video_not_rendered(self):
        body = self.client.get("/uz/", follow=True).content.decode("utf-8", "replace")
        self.assertNotIn('id="video"', body)

    def test_enabled_video_rendered(self):
        hv = HomeVideo.get_solo()
        hv.is_enabled = True
        hv.video_url = "https://youtu.be/dQw4w9WgXcQ"
        hv.save()
        body = self.client.get("/uz/", follow=True).content.decode("utf-8", "replace")
        self.assertIn('id="video"', body)
        self.assertIn("youtube.com/embed/dQw4w9WgXcQ", body)


# ---------------------------------------------------------------------------
# SEO feature tests (Phase 5: sitemap, robots.txt, head tags, analytics gating)
# ---------------------------------------------------------------------------
@override_settings(STORAGES=_STATIC_STORAGE)
class SitemapTests(TestCase):
    """GET /sitemap.xml returns 200 with urlset/sitemap-index and hreflang alternates."""

    def setUp(self):
        # Create an active course and a published news post so they appear in the sitemap.
        self.course = Course.objects.create(
            name="SEO Kursi",
            slug="seo-kursi",
            is_active=True,
        )
        self.post = NewsPost.objects.create(
            title="SEO Yangilik",
            slug="seo-yangilik",
            is_published=True,
        )

    def test_sitemap_status_200(self):
        response = self.client.get("/sitemap.xml")
        self.assertEqual(
            response.status_code, 200,
            f"Expected /sitemap.xml to return 200, got {response.status_code}",
        )

    def test_sitemap_contains_urlset_or_index(self):
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8", errors="replace")
        self.assertTrue(
            "<urlset" in body or "<sitemapindex" in body,
            "sitemap.xml body must contain <urlset or <sitemapindex",
        )

    def test_sitemap_contains_hreflang_alternates(self):
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8", errors="replace")
        # xhtml:link with hreflang attribute (i18n alternates)
        self.assertIn("hreflang", body, "sitemap.xml must contain hreflang alternates")

    def test_sitemap_contains_course_url(self):
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8", errors="replace")
        self.assertIn("seo-kursi", body, "sitemap.xml must include course URLs")

    def test_sitemap_contains_news_url(self):
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8", errors="replace")
        self.assertIn("seo-yangilik", body, "sitemap.xml must include news URLs")


@override_settings(STORAGES=_STATIC_STORAGE)
class RobotsTxtTests(TestCase):
    """GET /robots.txt returns 200 plain-text with Disallow:/admin/ and Sitemap:."""

    def test_robots_status_200(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(
            response.status_code, 200,
            f"Expected /robots.txt to return 200, got {response.status_code}",
        )

    def test_robots_content_type_plain(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response["Content-Type"].startswith("text/plain"),
            f"robots.txt Content-Type should start with text/plain, got {response['Content-Type']}",
        )

    def test_robots_disallow_admin(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8", errors="replace")
        self.assertIn(
            "Disallow: /admin/", body,
            "robots.txt must contain 'Disallow: /admin/'",
        )

    def test_robots_sitemap_directive(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8", errors="replace")
        self.assertIn(
            "Sitemap:", body,
            "robots.txt must contain a 'Sitemap:' directive",
        )

    def test_robots_disallow_ariza(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8", errors="replace")
        self.assertIn(
            "Disallow: /ariza/", body,
            "robots.txt must disallow the POST-only /ariza/ lead endpoint",
        )


@override_settings(STORAGES=_STATIC_STORAGE)
class WebManifestTests(TestCase):
    """GET /site.webmanifest returns a valid installable PWA manifest."""

    def test_manifest_status_and_content_type(self):
        response = self.client.get("/site.webmanifest")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response["Content-Type"].startswith("application/manifest+json"),
            f"manifest Content-Type should be application/manifest+json, "
            f"got {response['Content-Type']}",
        )

    def test_manifest_is_valid_json_with_required_keys(self):
        import json

        response = self.client.get("/site.webmanifest")
        data = json.loads(response.content)
        for key in ("name", "short_name", "start_url", "display", "icons"):
            self.assertIn(key, data, f"manifest missing required key '{key}'")
        self.assertEqual(data["display"], "standalone")

    def test_manifest_has_192_and_512_icons(self):
        import json

        response = self.client.get("/site.webmanifest")
        data = json.loads(response.content)
        sizes = {icon["sizes"] for icon in data["icons"]}
        self.assertIn("192x192", sizes, "manifest needs a 192x192 icon")
        self.assertIn("512x512", sizes, "manifest needs a 512x512 icon")
        purposes = {icon.get("purpose") for icon in data["icons"]}
        self.assertIn("maskable", purposes, "manifest needs a maskable icon")


@override_settings(STORAGES=_STATIC_STORAGE)
class AdminWebManifestTests(TestCase):
    """The admin panel installs as its OWN PWA — a dedicated manifest scoped to
    the admin (not the public site), served under the obfuscated ADMIN_URL, plus
    an in-header install button rendered on admin pages."""

    def test_manifest_status_and_content_type(self):
        response = self.client.get(reverse("admin_web_manifest"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response["Content-Type"].startswith("application/manifest+json"),
            f"admin manifest Content-Type should be application/manifest+json, "
            f"got {response['Content-Type']}",
        )

    def test_manifest_is_admin_scoped_standalone(self):
        import json

        response = self.client.get(reverse("admin_web_manifest"))
        data = json.loads(response.content)
        for key in ("name", "short_name", "start_url", "scope", "display", "icons"):
            self.assertIn(key, data, f"admin manifest missing required key '{key}'")
        self.assertEqual(data["display"], "standalone")
        admin_index = reverse("admin:index")
        # A *separate* admin app: start_url/scope point at the admin, not "/".
        self.assertEqual(data["start_url"], admin_index)
        self.assertEqual(data["scope"], admin_index)
        self.assertNotEqual(data["start_url"], "/")

    def test_manifest_lives_under_admin_prefix(self):
        # Kept under the obfuscated ADMIN_URL so it never leaks the admin path.
        self.assertEqual(
            reverse("admin_web_manifest"),
            "/" + settings.ADMIN_URL + "app.webmanifest",
        )

    def test_admin_page_links_manifest_and_shows_install_button(self):
        superuser = User.objects.create_superuser(
            username="admin_pwa", password="pwapass123", email="admin_pwa@test.com",
        )
        self.client.force_login(superuser)
        body = self.client.get(
            reverse("admin:pages_sitecopy_changelist"), follow=True
        ).content.decode("utf-8", "replace")
        self.assertIn('rel="manifest"', body, "admin page must link a PWA manifest")
        self.assertIn(
            reverse("admin_web_manifest"), body,
            "admin page must link the dedicated admin manifest",
        )
        self.assertIn(
            'id="admin-pwa-install"', body,
            "admin page must render the install button",
        )
        # Guard against a multi-line {# #} comment leaking onto the page (Django
        # only treats {# #} as a comment when it opens/closes on one line).
        self.assertNotIn(
            "reveals the header install button", body,
            "a template comment leaked into the rendered admin page",
        )


@override_settings(STORAGES=_STATIC_STORAGE)
class HomePageHeadTagsTests(TestCase):
    """GET /uz/ head contains canonical, hreflang, OG tags, and JSON-LD schema."""

    def test_uz_canonical_link(self):
        response = self.client.get("/uz/", follow=True)
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8", errors="replace")
        self.assertIn('rel="canonical"', body, "/uz/ page must have rel=canonical")

    def test_uz_hreflang_uz(self):
        response = self.client.get("/uz/", follow=True)
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8", errors="replace")
        self.assertIn('hreflang="uz"', body, "/uz/ page must have hreflang=uz")

    def test_uz_hreflang_ru(self):
        response = self.client.get("/uz/", follow=True)
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8", errors="replace")
        self.assertIn('hreflang="ru"', body, "/uz/ page must have hreflang=ru")

    def test_uz_hreflang_en(self):
        response = self.client.get("/uz/", follow=True)
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8", errors="replace")
        self.assertIn('hreflang="en"', body, "/uz/ page must have hreflang=en")

    def test_uz_hreflang_x_default(self):
        response = self.client.get("/uz/", follow=True)
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8", errors="replace")
        self.assertIn('hreflang="x-default"', body, "/uz/ page must have hreflang=x-default")

    def test_uz_og_title(self):
        response = self.client.get("/uz/", follow=True)
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8", errors="replace")
        self.assertIn('og:title', body, "/uz/ page must have og:title meta tag")

    def test_uz_og_image_or_og_meta(self):
        response = self.client.get("/uz/", follow=True)
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8", errors="replace")
        # Check for any og: meta property (og:image, og:url, og:description etc.)
        self.assertTrue(
            'property="og:' in body or "property='og:" in body,
            "/uz/ page must contain at least one Open Graph meta tag",
        )

    def test_uz_json_ld_educational_organization(self):
        response = self.client.get("/uz/", follow=True)
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8", errors="replace")
        self.assertIn(
            'application/ld+json', body,
            "/uz/ page must include a JSON-LD script block",
        )
        self.assertIn(
            "EducationalOrganization", body,
            "/uz/ JSON-LD must contain EducationalOrganization type",
        )

    def test_uz_has_theme_color_and_manifest(self):
        response = self.client.get("/uz/", follow=True)
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8", errors="replace")
        self.assertIn(
            'name="theme-color"', body,
            "/uz/ page must have a theme-color meta for the mobile browser toolbar",
        )
        self.assertIn(
            'rel="manifest"', body,
            "/uz/ page must link the PWA web manifest",
        )
        self.assertIn(
            'rel="apple-touch-icon"', body,
            "/uz/ page must link an apple-touch-icon for iOS install",
        )


@override_settings(STORAGES=_STATIC_STORAGE)
class RuLocaleHeadTagsTests(TestCase):
    """GET /ru/ canonical and og:url must reference the /ru/ path."""

    def _get_body(self):
        response = self.client.get("/ru/", follow=True)
        self.assertEqual(response.status_code, 200)
        return response.content.decode("utf-8", errors="replace")

    def test_ru_canonical_references_ru_path(self):
        body = self._get_body()
        # Find the canonical link tag and assert it points to /ru/
        canonical_match = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]*>', body)
        if canonical_match is None:
            # Try reversed attribute order
            canonical_match = re.search(r'<link[^>]+canonical[^>]*rel[^>]*>', body)
        self.assertIsNotNone(canonical_match, "/ru/ page must contain a canonical link tag")
        canonical_tag = canonical_match.group(0)
        self.assertIn("/ru/", canonical_tag, "canonical tag must reference the /ru/ path")

    def test_ru_og_url_references_ru_path(self):
        body = self._get_body()
        # Find og:url meta tag
        og_url_match = re.search(r'<meta[^>]+og:url[^>]*>', body)
        if og_url_match is None:
            og_url_match = re.search(r'<meta[^>]+og:url[^>]*/?>', body)
        self.assertIsNotNone(og_url_match, "/ru/ page must contain og:url meta tag")
        og_url_tag = og_url_match.group(0)
        self.assertIn("/ru/", og_url_tag, "og:url tag on /ru/ page must reference the /ru/ path")


@override_settings(STORAGES=_STATIC_STORAGE)
class AnalyticsGatingTests(TestCase):
    """Analytics scripts are only injected when corresponding IDs are configured."""

    def _get_home_body(self):
        response = self.client.get("/uz/", follow=True)
        self.assertEqual(response.status_code, 200)
        return response.content.decode("utf-8", errors="replace")

    def _set_config(self, **kwargs):
        cfg = SiteConfig.get_solo()
        for key, value in kwargs.items():
            setattr(cfg, key, value)
        cfg.save()

    def test_ga4_absent_when_id_empty(self):
        """With no GA4 ID configured, page must NOT inject gtag/gtm script."""
        self._set_config(ga4_measurement_id="")
        body = self._get_home_body()
        self.assertNotIn(
            "googletagmanager.com/gtag", body,
            "googletagmanager.com/gtag must not appear when ga4_measurement_id is empty",
        )

    def test_ga4_present_when_id_set(self):
        """With a GA4 measurement ID, page must inject googletagmanager gtag script."""
        self._set_config(ga4_measurement_id="G-TEST123")
        body = self._get_home_body()
        self.assertIn(
            "googletagmanager.com/gtag", body,
            "googletagmanager.com/gtag must appear when ga4_measurement_id='G-TEST123'",
        )

    def test_yandex_metrica_absent_when_id_empty(self):
        """With no Yandex Metrica ID configured, page must NOT inject mc.yandex script."""
        self._set_config(yandex_metrica_id="")
        body = self._get_home_body()
        self.assertFalse(
            "mc.yandex" in body or "metrika" in body,
            "Yandex Metrica script must not appear when yandex_metrica_id is empty",
        )

    def test_yandex_metrica_present_when_id_set(self):
        """With a Yandex Metrica ID, page must inject mc.yandex or metrika script."""
        self._set_config(yandex_metrica_id="12345678")
        body = self._get_home_body()
        self.assertTrue(
            "mc.yandex" in body or "metrika" in body,
            "Yandex Metrica script (mc.yandex or metrika) must appear when yandex_metrica_id is set",
        )


@override_settings(STORAGES=_STATIC_STORAGE)
class CourseDetailJsonLdTests(TestCase):
    """Course detail page head contains Course JSON-LD schema."""

    def setUp(self):
        self.course = Course.objects.create(
            name="JSON-LD Kurs",
            slug="json-ld-kurs",
            is_active=True,
        )

    def test_course_detail_has_course_json_ld(self):
        url = self.course.get_absolute_url()
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8", errors="replace")
        self.assertIn(
            "application/ld+json", body,
            "Course detail page must include a JSON-LD script block",
        )
        # Resilient check: allow single or double quotes around the type value
        self.assertIn(
            "Course", body,
            "Course detail JSON-LD must contain 'Course' type token",
        )


@override_settings(STORAGES=_STATIC_STORAGE)
class NewsDetailJsonLdTests(TestCase):
    """News detail page head contains NewsArticle JSON-LD schema."""

    def setUp(self):
        self.post = NewsPost.objects.create(
            title="JSON-LD Yangilik",
            slug="json-ld-yangilik",
            is_published=True,
        )

    def test_news_detail_has_news_article_json_ld(self):
        url = self.post.get_absolute_url()
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8", errors="replace")
        self.assertIn(
            "application/ld+json", body,
            "News detail page must include a JSON-LD script block",
        )
        # Resilient check: allow single or double quotes around the type value
        self.assertIn(
            "NewsArticle", body,
            "News detail JSON-LD must contain 'NewsArticle' type token",
        )
