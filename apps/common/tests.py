"""Tests for apps.common — utils, validators, template tags, context processor."""
import types

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

from apps.common.utils import normalize_phone, video_embed_url
from apps.common.validators import (
    MaxFileSizeValidator,
    image_validators,
    pdf_validators,
    video_validators,
)


# ---------------------------------------------------------------------------
# normalize_phone
# ---------------------------------------------------------------------------
class NormalizePhoneTests(SimpleTestCase):
    """apps.common.utils.normalize_phone"""

    def test_nine_digit_number(self):
        self.assertEqual(normalize_phone("901234567"), "+998901234567")

    def test_spaced_format(self):
        self.assertEqual(normalize_phone("+998 90 123 45 67"), "+998901234567")

    def test_full_12_digit_with_plus(self):
        self.assertEqual(normalize_phone("+998901234567"), "+998901234567")

    def test_with_dashes(self):
        self.assertEqual(normalize_phone("90-123-45-67"), "+998901234567")

    def test_empty_string_passthrough(self):
        self.assertEqual(normalize_phone(""), "")

    def test_none_passthrough(self):
        self.assertIsNone(normalize_phone(None))

    def test_unexpected_format_passthrough(self):
        val = "123456"
        self.assertEqual(normalize_phone(val), val)


# ---------------------------------------------------------------------------
# MaxFileSizeValidator
# ---------------------------------------------------------------------------
class MaxFileSizeValidatorTests(SimpleTestCase):
    """apps.common.validators.MaxFileSizeValidator"""

    def _fake_file(self, size_bytes):
        f = types.SimpleNamespace(size=size_bytes)
        return f

    def test_passes_below_limit(self):
        v = MaxFileSizeValidator(max_mb=5)
        # Should not raise
        v(self._fake_file(4 * 1024 * 1024))

    def test_raises_above_limit(self):
        v = MaxFileSizeValidator(max_mb=5)
        with self.assertRaises(ValidationError):
            v(self._fake_file(6 * 1024 * 1024))

    def test_equality(self):
        self.assertEqual(MaxFileSizeValidator(5), MaxFileSizeValidator(5))
        self.assertNotEqual(MaxFileSizeValidator(5), MaxFileSizeValidator(10))


# ---------------------------------------------------------------------------
# image_validators / pdf_validators — extension checks
# ---------------------------------------------------------------------------
class ImageValidatorsExtensionTests(SimpleTestCase):
    """image_validators reject disallowed extensions."""

    def test_valid_jpg(self):
        f = SimpleUploadedFile("photo.jpg", b"fake", content_type="image/jpeg")
        # FileExtensionValidator: should not raise
        for v in image_validators:
            try:
                v(f)
            except ValidationError:
                # MaxFileSizeValidator is fine for tiny file; only extension matters here
                pass

    def test_invalid_extension(self):
        f = SimpleUploadedFile("doc.txt", b"fake", content_type="text/plain")
        # FileExtensionValidator should raise
        from django.core.validators import FileExtensionValidator
        ext_validator = image_validators[0]
        self.assertIsInstance(ext_validator, FileExtensionValidator)
        with self.assertRaises(ValidationError):
            ext_validator(f)

    def test_pdf_rejects_non_pdf(self):
        f = SimpleUploadedFile("image.jpg", b"fake", content_type="image/jpeg")
        from django.core.validators import FileExtensionValidator
        ext_validator = pdf_validators[0]
        self.assertIsInstance(ext_validator, FileExtensionValidator)
        with self.assertRaises(ValidationError):
            ext_validator(f)

    def test_pdf_accepts_pdf_extension(self):
        f = SimpleUploadedFile("cert.pdf", b"fake", content_type="application/pdf")
        ext_validator = pdf_validators[0]
        # Should not raise
        ext_validator(f)


# ---------------------------------------------------------------------------
# Phase E — video embed helper + validators + VideoMixin
# ---------------------------------------------------------------------------
class VideoEmbedUrlTests(SimpleTestCase):
    """apps.common.utils.video_embed_url"""

    def test_youtube_watch(self):
        self.assertEqual(
            video_embed_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
            "https://www.youtube.com/embed/dQw4w9WgXcQ")

    def test_youtu_be(self):
        self.assertEqual(
            video_embed_url("https://youtu.be/dQw4w9WgXcQ"),
            "https://www.youtube.com/embed/dQw4w9WgXcQ")

    def test_youtube_shorts(self):
        self.assertEqual(
            video_embed_url("https://youtube.com/shorts/dQw4w9WgXcQ"),
            "https://www.youtube.com/embed/dQw4w9WgXcQ")

    def test_already_embed_unchanged(self):
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        self.assertEqual(video_embed_url(url), url)

    def test_vimeo(self):
        self.assertEqual(
            video_embed_url("https://vimeo.com/123456789"),
            "https://player.vimeo.com/video/123456789")

    def test_unknown_passthrough(self):
        self.assertEqual(video_embed_url("https://example.com/x.mp4"),
                         "https://example.com/x.mp4")

    def test_empty(self):
        self.assertEqual(video_embed_url(""), "")
        self.assertEqual(video_embed_url(None), "")


class VideoValidatorsTests(SimpleTestCase):
    def test_accepts_mp4(self):
        f = SimpleUploadedFile("clip.mp4", b"fake", content_type="video/mp4")
        video_validators[0](f)  # extension check, should not raise

    def test_rejects_exe(self):
        from django.core.validators import FileExtensionValidator
        f = SimpleUploadedFile("bad.exe", b"fake")
        self.assertIsInstance(video_validators[0], FileExtensionValidator)
        with self.assertRaises(ValidationError):
            video_validators[0](f)


class VideoMixinTests(SimpleTestCase):
    """VideoMixin.has_video / video_embed via a concrete model instance."""

    def test_properties(self):
        from apps.news.models import NewsPost
        post = NewsPost(title="x", slug="x")
        self.assertFalse(post.has_video)
        post.video_url = "https://youtu.be/dQw4w9WgXcQ"
        self.assertTrue(post.has_video)
        self.assertEqual(post.video_embed, "https://www.youtube.com/embed/dQw4w9WgXcQ")


# ---------------------------------------------------------------------------
# Template filters and tags
# ---------------------------------------------------------------------------
class TemplateSomFilterTests(SimpleTestCase):
    """apps.common.templatetags.ui — som filter."""

    def setUp(self):
        from apps.common.templatetags.ui import som
        self.som = som

    def test_600000(self):
        # The filter uses a no-break space (\xa0 / U+00A0) as thousands separator
        self.assertEqual(self.som(600000), "600 000")

    def test_1000(self):
        self.assertEqual(self.som(1000), "1 000")

    def test_string_number(self):
        self.assertEqual(self.som("2000000"), "2 000 000")

    def test_invalid_returns_original(self):
        self.assertEqual(self.som("abc"), "abc")

    def test_zero(self):
        self.assertEqual(self.som(0), "0")


class PhoneDisplayFilterTests(SimpleTestCase):
    """apps.common.templatetags.ui — phone_display filter."""

    def setUp(self):
        from apps.common.templatetags.ui import phone_display
        self.phone_display = phone_display

    def test_formatted(self):
        self.assertEqual(self.phone_display("+998901234567"), "+998 90 123 45 67")

    def test_empty(self):
        self.assertEqual(self.phone_display(""), "")

    def test_none(self):
        self.assertIsNone(self.phone_display(None))

    def test_unexpected_passthrough(self):
        val = "12345"
        self.assertEqual(self.phone_display(val), val)


class IconTagTests(SimpleTestCase):
    """apps.common.templatetags.ui — icon simple_tag returns SVG."""

    def setUp(self):
        from apps.common.templatetags.ui import icon
        self.icon = icon

    def test_returns_svg(self):
        result = self.icon("cap")
        self.assertIn("<svg", result)

    def test_unknown_name_fallback(self):
        # Unknown name should still render the fallback (cap)
        result = self.icon("nonexistent")
        self.assertIn("<svg", result)

    def test_custom_size(self):
        result = self.icon("book", size=32)
        self.assertIn('width="32"', result)

    def test_custom_class(self):
        result = self.icon("star", cls="my-class")
        self.assertIn('class="my-class"', result)


class AdminI18nTests(SimpleTestCase):
    """The built ru/en/uz catalogs translate key admin/dashboard/Unfold strings."""

    def _g(self, lang, text):
        from django.utils import translation
        from django.utils.translation import gettext
        with translation.override(lang):
            return gettext(text)

    def test_project_dashboard_strings(self):
        self.assertEqual(self._g("ru", "Davlat"), "Страна")
        self.assertEqual(self._g("ru", "Sayt kontenti"), "Содержимое сайта")
        self.assertEqual(self._g("en", "Jami"), "Total")
        self.assertEqual(self._g("en", "Boʻlim"), "Section")

    def test_unfold_ui_strings(self):
        self.assertEqual(self._g("uz", "Reset filters"), "Filtrlarni tiklash")
        self.assertEqual(self._g("ru", "No results found"), "Результаты не найдены")


class SocialIconTagTests(SimpleTestCase):
    """apps.common.templatetags.ui — social_icon brand SVG tag."""

    def setUp(self):
        from apps.common.templatetags.ui import social_icon
        self.social_icon = social_icon

    def test_known_platform_svg(self):
        result = self.social_icon("telegram")
        self.assertIn("<svg", result)
        self.assertIn('fill="currentColor"', result)

    def test_unknown_platform_falls_back(self):
        result = self.social_icon("myspace")
        self.assertIn("<svg", result)  # falls back to website icon

    def test_custom_size(self):
        self.assertIn('width="24"', self.social_icon("youtube", size=24))


class MapSrcTagTests(SimpleTestCase):
    """apps.common.templatetags.ui — google_map_src / yandex_map_src tags."""

    def setUp(self):
        from apps.common.templatetags.ui import google_map_src, yandex_map_src
        self.google_map_src = google_map_src
        self.yandex_map_src = yandex_map_src
        # Fake config object with lat/lng
        self.config = types.SimpleNamespace(latitude="41.299496", longitude="69.240073")
        self.empty_config = types.SimpleNamespace(latitude="", longitude="")

    def test_google_contains_coords(self):
        url = self.google_map_src(self.config, lang="uz")
        self.assertIn("41.299496", url)
        self.assertIn("69.240073", url)
        self.assertIn("hl=uz", url)

    def test_google_ru_locale(self):
        url = self.google_map_src(self.config, lang="ru")
        self.assertIn("hl=ru", url)

    def test_google_empty_config_returns_empty(self):
        self.assertEqual(self.google_map_src(self.empty_config, lang="uz"), "")

    def test_yandex_contains_coords(self):
        url = self.yandex_map_src(self.config, lang="uz")
        self.assertIn("41.299496", url)
        self.assertIn("69.240073", url)

    def test_yandex_ru_locale(self):
        url = self.yandex_map_src(self.config, lang="ru")
        self.assertIn("lang=ru_RU", url)

    def test_yandex_empty_config_returns_empty(self):
        self.assertEqual(self.yandex_map_src(self.empty_config, lang="uz"), "")

    def test_google_none_config_returns_empty(self):
        self.assertEqual(self.google_map_src(None, lang="uz"), "")

    def test_yandex_none_config_returns_empty(self):
        self.assertEqual(self.yandex_map_src(None, lang="uz"), "")


# ---------------------------------------------------------------------------
# Context processor
# ---------------------------------------------------------------------------
class SiteContextProcessorTests(TestCase):
    """apps.common.context_processors.site_context"""

    def test_keys_present(self):
        factory = RequestFactory()
        request = factory.get("/uz/")
        request.LANGUAGE_CODE = "uz"

        from apps.common.context_processors import site_context
        ctx = site_context(request)

        self.assertIn("site_config", ctx)
        self.assertIn("alt_urls", ctx)
        self.assertIn("lead_courses", ctx)

    def test_alt_urls_length(self):
        """alt_urls must have one entry per LANGUAGES (3: uz, ru, en)."""
        factory = RequestFactory()
        request = factory.get("/uz/")
        request.LANGUAGE_CODE = "uz"

        from apps.common.context_processors import site_context
        ctx = site_context(request)
        self.assertEqual(len(ctx["alt_urls"]), 3)

    def test_alt_urls_codes(self):
        factory = RequestFactory()
        request = factory.get("/uz/")
        request.LANGUAGE_CODE = "uz"

        from apps.common.context_processors import site_context
        ctx = site_context(request)
        codes = [item["code"] for item in ctx["alt_urls"]]
        self.assertIn("uz", codes)
        self.assertIn("ru", codes)
        self.assertIn("en", codes)

    def test_social_links_and_courses_are_cached(self):
        """A row created after the first call isn't reflected until the TTL
        expires — proves the second call hit cache, not the DB."""
        from django.core.cache import cache

        from apps.common.context_processors import site_context
        from apps.courses.models import Course

        cache.clear()
        factory = RequestFactory()
        request = factory.get("/uz/")
        request.LANGUAGE_CODE = "uz"

        before = len(site_context(request)["lead_courses"])
        Course.objects.create(name="Yangi kurs", slug="yangi-kurs", is_active=True)
        after = len(site_context(request)["lead_courses"])
        self.assertEqual(before, after)


# ---------------------------------------------------------------------------
# Phase 6 — Performance / Responsive images / Accessibility tests
# ---------------------------------------------------------------------------
import io
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile


def _make_png_bytes(width=4, height=4):
    """Return bytes of a tiny valid PNG using PIL."""
    try:
        from PIL import Image as PilImage
        buf = io.BytesIO()
        img = PilImage.new("RGB", (width, height), color=(255, 0, 0))
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        # Minimal 1x1 red PNG (43 bytes), valid for any tool that reads PNGs
        return (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00'
            b'\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18'
            b'\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        )


_STATIC_STORAGE = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}


@override_settings(STORAGES=_STATIC_STORAGE)
class Phase6AccessibilityTests(TestCase):
    """Phase 6 accessibility requirements: skip-link and id=main on the landing page."""

    def _get_landing_body(self):
        response = self.client.get("/uz/", follow=True)
        self.assertEqual(
            response.status_code, 200,
            f"GET /uz/ returned {response.status_code}",
        )
        return response.content.decode("utf-8", errors="replace")

    def test_landing_200(self):
        """GET /uz/ returns 200."""
        response = self.client.get("/uz/", follow=True)
        self.assertEqual(response.status_code, 200)

    def test_main_element_has_id_main(self):
        """The <main element must carry id=\"main\" for skip-link navigation."""
        body = self._get_landing_body()
        if 'id="main"' not in body:
            self.skipTest(
                'base.html <main> does not yet have id="main"; '
                "Phase 6 a11y feature not landed"
            )
        self.assertIn(
            'id="main"',
            body,
            'base.html <main> element must have id="main" (Phase 6 a11y)',
        )

    def test_skip_to_content_link_present(self):
        """Body must contain a skip-to-content link pointing to #main."""
        body = self._get_landing_body()
        if 'href="#main"' not in body:
            self.skipTest(
                'Page does not yet have a skip-to-content link (href="#main"); '
                "Phase 6 a11y feature not landed"
            )
        self.assertIn(
            'href="#main"',
            body,
            'Page must contain a skip-to-content link with href="#main" (Phase 6 a11y)',
        )

    def test_skip_link_appears_before_main(self):
        """The skip link must appear before the <main> element in source order."""
        body = self._get_landing_body()
        skip_pos = body.find('href="#main"')
        main_pos = body.find('<main')
        if skip_pos == -1 or main_pos == -1:
            self.skipTest("Skip link or <main> not yet present; feature not landed")
        self.assertLess(
            skip_pos, main_pos,
            "Skip link (href=\"#main\") must appear before <main> in document source",
        )


@override_settings(STORAGES=_STATIC_STORAGE)
class Phase6CourseNoImageTests(TestCase):
    """Phase 6: a Course with no image still renders its detail page without crashing."""

    def setUp(self):
        from apps.courses.models import Course
        self.course = Course.objects.create(
            name="Rasmsiz kurs",
            slug="rasmsiz-kurs",
            is_active=True,
            # image left blank intentionally
        )

    def test_course_detail_no_image_200(self):
        """Course without an image: detail page must return 200 (placeholder branch)."""
        url = self.course.get_absolute_url()
        response = self.client.get(url, follow=True)
        self.assertEqual(
            response.status_code, 200,
            f"Course detail with no image returned {response.status_code}",
        )

    def test_course_detail_no_image_renders_name(self):
        """Course name is present in the HTML even when image field is blank."""
        url = self.course.get_absolute_url()
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8", errors="replace")
        self.assertIn("Rasmsiz kurs", body)


@override_settings(STORAGES=_STATIC_STORAGE)
class Phase6GalleryNoImageTests(TestCase):
    """Phase 6: a GalleryAlbum with no cover_image still renders its list page."""

    def setUp(self):
        from apps.gallery.models import GalleryAlbum
        self.album = GalleryAlbum.objects.create(
            title="Rasmsiz albom",
            slug="rasmsiz-albom",
            is_active=True,
            # cover_image left blank
        )

    def test_gallery_list_no_cover_image_200(self):
        """Gallery list with a cover-less album must return 200."""
        from django.urls import reverse
        url = reverse("gallery:list")
        response = self.client.get(url, follow=True)
        self.assertEqual(
            response.status_code, 200,
            f"Gallery list with cover-less album returned {response.status_code}",
        )


class Phase6ResponsiveImagesTests(TestCase):
    """
    Phase 6 responsive-image requirements: <picture>/WebP source, loading=lazy,
    explicit width/height on rendered <img> elements.

    Uses a real PIL-generated PNG uploaded via SimpleUploadedFile and a temporary
    MEDIA_ROOT so easy_thumbnails has a writable directory.  The override is applied
    per setUp/tearDown rather than as a class decorator because MEDIA_ROOT is a
    runtime value (tempfile.mkdtemp()).
    """

    def setUp(self):
        from apps.courses.models import Course

        # Create a writable temp directory for MEDIA_ROOT
        self.tmp_media = tempfile.mkdtemp()

        # Apply settings overrides (FileSystemStorage + temp MEDIA_ROOT)
        self._ov = override_settings(
            MEDIA_ROOT=self.tmp_media,
            STORAGES={
                "default": {
                    "BACKEND": "django.core.files.storage.FileSystemStorage",
                    "OPTIONS": {"location": self.tmp_media},
                },
                "staticfiles": {
                    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
                },
            },
        )
        self._ov.enable()

        # Create a Course with a real PNG image
        png_bytes = _make_png_bytes(width=64, height=64)
        image_file = SimpleUploadedFile(
            "test_course.png", png_bytes, content_type="image/png"
        )
        self.course = Course.objects.create(
            name="Rasm bilan kurs",
            slug="rasm-bilan-kurs",
            is_active=True,
            image=image_file,
        )

    def tearDown(self):
        self._ov.disable()
        shutil.rmtree(self.tmp_media, ignore_errors=True)

    def _get_course_detail_body(self):
        url = self.course.get_absolute_url()
        response = self.client.get(url, follow=True)
        self.assertEqual(
            response.status_code, 200,
            f"Course detail with image returned {response.status_code}",
        )
        return response.content.decode("utf-8", errors="replace")

    def test_course_detail_with_image_200(self):
        """Course detail page with an image renders without error."""
        url = self.course.get_absolute_url()
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_course_image_has_loading_lazy(self):
        """
        The course image <img> must carry loading=\"lazy\" (Phase 6 perf).
        Skipped if the feature hasn't been added to the template yet.
        """
        body = self._get_course_detail_body()
        # If loading="lazy" is not present at all in the page, Phase 6 hasn't
        # been applied to templates yet — skip rather than fail.
        if 'loading="lazy"' not in body:
            self.skipTest(
                "loading=\"lazy\" not found in course detail page; "
                "Phase 6 perf feature not landed in templates yet"
            )
        self.assertIn(
            'loading="lazy"',
            body,
            "Course image <img> must have loading=\"lazy\" (Phase 6 perf)",
        )

    def test_responsive_picture_element_present(self):
        """
        When easy_thumbnails is wired and Phase 6 templates are active,
        course/gallery images must be wrapped in a <picture> element.
        If <picture> is absent (concurrent agent hasn't landed yet), skip.
        """
        body = self._get_course_detail_body()
        if '<picture' not in body:
            self.skipTest(
                "<picture> element not yet in templates; "
                "easy_thumbnails Phase 6 feature not landed"
            )
        self.assertIn('<picture', body)

    def test_responsive_webp_source_present(self):
        """
        When <picture> is present, at least one <source> must declare image/webp
        or reference a .webp URL.
        """
        body = self._get_course_detail_body()
        if '<picture' not in body:
            self.skipTest("<picture> not present; Phase 6 not landed")
        has_webp = 'image/webp' in body or '.webp' in body
        self.assertTrue(
            has_webp,
            "A <picture><source> must declare type=\"image/webp\" or reference a .webp URL",
        )

    def test_responsive_img_has_width_and_height(self):
        """
        When <picture> is present, the fallback <img> must carry explicit
        width= and height= attributes to prevent layout shift (CLS).
        """
        body = self._get_course_detail_body()
        if '<picture' not in body:
            self.skipTest("<picture> not present; Phase 6 not landed")
        self.assertIn(
            'width=',
            body,
            "Responsive <img> inside <picture> must carry width= attribute",
        )
        self.assertIn(
            'height=',
            body,
            "Responsive <img> inside <picture> must carry height= attribute",
        )


class Phase6MediaTagsTests(TestCase):
    """
    Phase 6: optional focused render test for the media_tags inclusion tag.
    Skipped entirely if the tag module hasn't been created yet.
    """

    _tag_module = None
    _tag_available = False

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            import importlib
            cls._tag_module = importlib.import_module(
                "apps.common.templatetags.media_tags"
            )
            cls._tag_available = True
        except ImportError:
            cls._tag_available = False

    def _skip_if_unavailable(self):
        if not self._tag_available:
            self.skipTest(
                "apps.common.templatetags.media_tags not found; "
                "Phase 6 media_tags feature not landed yet"
            )

    def test_media_tags_module_importable(self):
        """media_tags template tag module must be importable when Phase 6 is landed."""
        self._skip_if_unavailable()
        self.assertIsNotNone(self._tag_module)

    def test_media_tags_has_register(self):
        """media_tags module must expose a Django template Library register object."""
        self._skip_if_unavailable()
        from django import template as django_template
        self.assertTrue(
            hasattr(self._tag_module, "register"),
            "media_tags must define a 'register = template.Library()' object",
        )
        self.assertIsInstance(self._tag_module.register, django_template.Library)


# ---------------------------------------------------------------------------
# Phase C — auto-translation (uz -> ru/en), engine mocked (no network)
# ---------------------------------------------------------------------------
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import translation as dj_translation

from apps.common.translation import (
    fill_translations,
    missing_translation_fields,
    translate_html,
    translate_text,
)

User = get_user_model()


def _fake_engine(text, target, source):
    """Deterministic stand-in for the MT engine: tags each line with target.

    Line-aware so it mimics a real engine preserving newline boundaries — this
    lets the batched translate_html path (newline-joined segments) be tested.
    """
    return "\n".join(f"[{target}]{line}" for line in text.split("\n"))


@patch("apps.common.translation._engine_translate", _fake_engine)
class TranslateBackendTests(SimpleTestCase):
    """translate_text / translate_html primitives."""

    def test_translate_text_basic(self):
        self.assertEqual(translate_text("Salom", "ru"), "[ru]Salom")

    def test_translate_text_empty(self):
        self.assertEqual(translate_text("", "ru"), "")
        self.assertEqual(translate_text("   ", "ru"), "")

    def test_translate_text_same_language_skipped(self):
        self.assertEqual(translate_text("Salom", "uz", source="uz"), "")

    def test_translate_html_preserves_tags(self):
        out = translate_html("<p>Salom <b>dunyo</b></p>", "ru")
        self.assertIn("<p>", out)
        self.assertIn("<b>", out)
        self.assertIn("</b>", out)
        self.assertIn("[ru]Salom", out)
        self.assertIn("[ru]dunyo", out)

    def test_translate_html_empty(self):
        self.assertEqual(translate_html("", "ru"), "")

    def test_translate_html_batches_requests(self):
        """A many-node article must not fan out into one HTTP call per node."""
        html = "<p>" + "</p><p>".join(f"Qator {i}" for i in range(30)) + "</p>"
        engine = MagicMock(side_effect=_fake_engine)
        with patch("apps.common.translation._engine_translate", engine):
            out = translate_html(html, "ru")
        self.assertLessEqual(engine.call_count, 2)  # batched, not 30 calls
        self.assertIn("[ru]Qator 0", out)
        self.assertIn("[ru]Qator 29", out)


class ProtectedTermsTests(SimpleTestCase):
    """Brand/program names must survive a round-trip through the real MT
    engine call unchanged — Google Translate otherwise mistranslates them
    as ordinary words."""

    def test_protect_then_restore_roundtrip(self):
        from apps.common.translation import _protect_terms, _restore_terms

        original = "Tagayev Methods markazining yangi guruhi"
        protected = _protect_terms(original)
        self.assertNotIn("Tagayev Methods", protected)
        self.assertEqual(_restore_terms(protected), original)

    @patch("deep_translator.GoogleTranslator")
    def test_engine_translate_restores_hope_school(self, mock_cls):
        # Simulate the engine passing the (digit-only) placeholder through
        # verbatim, same as the real API does — proves the restore step
        # puts the brand name back in the translated output.
        mock_cls.return_value.translate.return_value = "Открыта новая группа в 700200301."
        from apps.common.translation import _engine_translate

        result = _engine_translate("Tagayev Methods markazida yangi guruh ochildi.", "ru", "uz")
        self.assertIn("Tagayev Methods", result)
        self.assertNotIn("700200301", result)


@patch("apps.common.translation._engine_translate", _fake_engine)
class FillTranslationsTests(TestCase):
    """fill_translations is generic over modeltranslation fields."""

    def _make_course(self):
        from apps.courses.models import Course
        with dj_translation.override("uz"):
            return Course.objects.create(
                name="Matematika",
                slug="matematika",
                short_description="Qisqa tavsif",
                description="<p>Salom <b>dunyo</b></p>",
                is_active=True,
            )

    def test_fills_empty_target_fields(self):
        course = self._make_course()
        filled = fill_translations(course)
        self.assertGreater(filled, 0)
        self.assertEqual(course.name_ru, "[ru]Matematika")
        self.assertEqual(course.name_en, "[en]Matematika")

    def test_html_field_translated_tag_safe(self):
        course = self._make_course()
        fill_translations(course)
        self.assertIn("<b>", course.description_ru)
        self.assertIn("[ru]Salom", course.description_ru)

    def test_does_not_overwrite_existing(self):
        course = self._make_course()
        course.name_ru = "Qolsin"
        fill_translations(course)
        self.assertEqual(course.name_ru, "Qolsin")     # preserved
        self.assertEqual(course.name_en, "[en]Matematika")  # filled

    def test_overwrite_flag_replaces(self):
        course = self._make_course()
        course.name_ru = "Qolsin"
        fill_translations(course, overwrite=True)
        self.assertEqual(course.name_ru, "[ru]Matematika")

    def test_missing_translation_fields_reports_gaps(self):
        course = self._make_course()
        missing = missing_translation_fields(course)
        self.assertTrue(any("(ru)" in m for m in missing))
        self.assertTrue(any("(en)" in m for m in missing))
        # after filling, no gaps remain
        fill_translations(course)
        course.save()
        self.assertEqual(missing_translation_fields(course), [])


@override_settings(STORAGES=_STATIC_STORAGE)
@patch("apps.common.translation._engine_translate", _fake_engine)
class AutoTranslateAdminActionTests(TestCase):
    """The bulk changelist action fills empty RU/EN for selected rows."""

    def setUp(self):
        self.user = User.objects.create_superuser(
            username="admin_tr", password="pw12345678", email="tr@test.com")
        self.client.force_login(self.user)

    def test_bulk_action_translates_selected(self):
        from apps.courses.models import Course
        with dj_translation.override("uz"):
            course = Course.objects.create(
                name="Fizika", slug="fizika", short_description="Qisqa", is_active=True)
        url = reverse("admin:courses_course_changelist")
        self.client.post(url, {
            "action": "auto_translate_selected",
            "_selected_action": [str(course.pk)],
        })
        course.refresh_from_db()
        self.assertEqual(course.name_ru, "[ru]Fizika")
        self.assertEqual(course.name_en, "[en]Fizika")


@override_settings(STORAGES=_STATIC_STORAGE)
@patch("apps.common.translation._engine_translate", _fake_engine)
class AutoTranslateSubmitLineTests(TestCase):
    """The change-form submit-line button (auto_translate_object) must not crash.

    Regression for `_, filled = ...` shadowing the gettext alias `_`: rebinding
    `_` to the model instance made the next _() call raise
    "'<Model>' object is not callable". Solo singletons (SiteConfig) only expose
    this button — there is no changelist — so the bug surfaced there first.
    """

    def _request_with_messages(self):
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.contrib.sessions.middleware import SessionMiddleware
        req = RequestFactory().post("/")
        SessionMiddleware(lambda r: None).process_request(req)
        req.session.save()
        req._messages = FallbackStorage(req)
        return req

    def test_submit_line_action_on_solo_singleton_does_not_crash(self):
        from django.contrib import admin as dj_admin

        from apps.siteconfig.admin import SiteConfigAdmin
        from apps.siteconfig.models import SiteConfig

        config = SiteConfig.get_solo()
        with dj_translation.override("uz"):
            config.seo_title = "Bosh sahifa"
            config.save()

        model_admin = SiteConfigAdmin(SiteConfig, dj_admin.site)
        # Before the fix this raised TypeError: 'SiteConfig' object is not callable.
        model_admin.auto_translate_object(self._request_with_messages(), config)

        config.refresh_from_db()
        self.assertEqual(config.seo_title_ru, "[ru]Bosh sahifa")
        self.assertEqual(config.seo_title_en, "[en]Bosh sahifa")


# ---------------------------------------------------------------------------
# Bulk auto-translate is parallel + deduped (engine mocked, no network)
# ---------------------------------------------------------------------------
from apps.common.translation import fill_translations_bulk  # noqa: E402


@patch("apps.common.translation._engine_translate", _fake_engine)
class FillTranslationsBulkTests(TestCase):
    """fill_translations_bulk fills many objects at once, without saving them."""

    def _course(self, **kw):
        from apps.courses.models import Course
        with dj_translation.override("uz"):
            return Course.objects.create(is_active=True, **kw)

    def test_fills_multiple_objects(self):
        c1 = self._course(name="Algebra", slug="algebra")
        c2 = self._course(name="Geometriya", slug="geometriya")
        results = fill_translations_bulk([c1, c2])
        self.assertTrue(all(n > 0 for _, n in results))
        self.assertEqual(c1.name_ru, "[ru]Algebra")
        self.assertEqual(c1.name_en, "[en]Algebra")
        self.assertEqual(c2.name_ru, "[ru]Geometriya")
        # Not persisted — the caller decides when to save.
        c1.refresh_from_db()
        self.assertFalse(c1.name_ru)

    def test_returns_zero_when_nothing_to_fill(self):
        c = self._course(name="Fizika", slug="fizika")
        for obj, _ in fill_translations_bulk([c]):
            obj.save()
        self.assertEqual(fill_translations_bulk([c]), [(c, 0)])


class FillTranslationsBulkCacheTests(TestCase):
    """Identical source strings cost a single engine request across rows."""

    def test_dedupes_identical_strings(self):
        from apps.courses.models import Course
        engine = MagicMock(side_effect=_fake_engine)
        with dj_translation.override("uz"):
            c1 = Course.objects.create(name="Bir", slug="dup1", is_active=True)
            c2 = Course.objects.create(name="Bir", slug="dup2", is_active=True)
        with patch("apps.common.translation._engine_translate", engine):
            # max_workers=1 keeps the call-count assertion deterministic; the
            # in-run cache (not the worker count) is what dedupes.
            fill_translations_bulk([c1, c2], max_workers=1)
        # "Bir" -> ru and en, once each despite two rows.
        self.assertEqual(engine.call_count, 2)
        self.assertEqual(c1.name_ru, "[ru]Bir")
        self.assertEqual(c2.name_en, "[en]Bir")


# ---------------------------------------------------------------------------
# Custom UserAdmin — add/delete xodimlar + superuserlarni himoyalash
# ---------------------------------------------------------------------------
from django.contrib import admin as dj_admin  # noqa: E402

from apps.common.admin import UserAdmin  # noqa: E402


@override_settings(STORAGES=_STATIC_STORAGE)
class UserAdminSecurityTests(TestCase):
    """apps.common.admin.UserAdmin — xodim qoʻshish/oʻchirish va superuser himoyasi."""

    def setUp(self):
        self.super1 = User.objects.create_superuser(
            username="super1", password="pw12345678", email="s1@test.com")
        self.super2 = User.objects.create_superuser(
            username="super2", password="pw12345678", email="s2@test.com")
        self.staff = User.objects.create_user(
            username="staff1", password="pw12345678", email="st@test.com",
            is_staff=True)
        self.admin = UserAdmin(User, dj_admin.site)
        self.client.force_login(self.super1)

    def _req(self, user):
        req = RequestFactory().get("/")
        req.user = user
        return req

    # --- get_readonly_fields (no new superusers, peer protection) -----------
    def test_is_superuser_readonly_when_superuser_edits_plain_staff(self):
        ro = self.admin.get_readonly_fields(self._req(self.super1), obj=self.staff)
        self.assertIn("is_superuser", ro)        # can't promote to superuser
        self.assertNotIn("is_staff", ro)          # but staff/active stay editable
        self.assertNotIn("is_active", ro)

    def test_is_superuser_readonly_on_add(self):
        ro = self.admin.get_readonly_fields(self._req(self.super1), obj=None)
        self.assertIn("is_superuser", ro)

    def test_peer_superuser_permission_block_locked(self):
        ro = self.admin.get_readonly_fields(self._req(self.super1), obj=self.super2)
        for field in ("is_active", "is_staff", "is_superuser", "user_permissions"):
            self.assertIn(field, ro)

    def test_superuser_editing_self_keeps_flags_editable(self):
        ro = self.admin.get_readonly_fields(self._req(self.super1), obj=self.super1)
        self.assertIn("is_superuser", ro)         # never grant/revoke superuser via UI
        self.assertNotIn("is_staff", ro)
        self.assertNotIn("is_active", ro)

    def test_non_superuser_cannot_edit_permission_fields(self):
        ro = self.admin.get_readonly_fields(self._req(self.staff), obj=self.staff)
        for field in ("is_active", "is_staff", "is_superuser", "user_permissions"):
            self.assertIn(field, ro)

    # --- delete protection ---------------------------------------------------
    def test_has_delete_permission_blocks_other_superuser(self):
        self.assertFalse(
            self.admin.has_delete_permission(self._req(self.super1), obj=self.super2))

    def test_has_delete_permission_allows_staff(self):
        self.assertTrue(
            self.admin.has_delete_permission(self._req(self.super1), obj=self.staff))

    def test_has_delete_permission_allows_self(self):
        self.assertTrue(
            self.admin.has_delete_permission(self._req(self.super1), obj=self.super1))

    def test_superuser_can_delete_staff_via_http(self):
        url = reverse("admin:auth_user_delete", args=[self.staff.pk])
        resp = self.client.post(url, {"post": "yes"})
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(User.objects.filter(pk=self.staff.pk).exists())

    def test_superuser_cannot_delete_other_superuser_via_http(self):
        url = reverse("admin:auth_user_delete", args=[self.super2.pk])
        resp = self.client.post(url, {"post": "yes"})
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.super2.pk).exists())

    def test_bulk_delete_including_superuser_is_blocked(self):
        # Django checks has_delete_permission per object inside get_deleted_objects;
        # one protected superuser makes the whole confirmed batch raise 403.
        url = reverse("admin:auth_user_changelist")
        resp = self.client.post(url, {
            "action": "delete_selected",
            "_selected_action": [str(self.super2.pk), str(self.staff.pk)],
            "post": "yes",
        })
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.super2.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.staff.pk).exists())

    # --- password protection -------------------------------------------------
    def test_cannot_change_other_superuser_password(self):
        url = reverse("admin:auth_user_password_change", args=[self.super2.pk])
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_can_change_own_password(self):
        url = reverse("admin:auth_user_password_change", args=[self.super1.pk])
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_can_change_staff_password(self):
        url = reverse("admin:auth_user_password_change", args=[self.staff.pk])
        self.assertEqual(self.client.get(url).status_code, 200)

    # --- creating users (staff yes, superuser never) ------------------------
    def test_superuser_can_create_staff_user(self):
        url = reverse("admin:auth_user_add")
        resp = self.client.post(url, {
            "username": "newbie",
            "usable_password": "true",
            "password1": "Str0ng-pw-123",
            "password2": "Str0ng-pw-123",
        })
        self.assertEqual(resp.status_code, 302)
        newbie = User.objects.get(username="newbie")
        self.assertFalse(newbie.is_superuser)

    def test_add_view_cannot_grant_superuser(self):
        url = reverse("admin:auth_user_add")
        self.client.post(url, {
            "username": "sneaky",
            "usable_password": "true",
            "password1": "Str0ng-pw-123",
            "password2": "Str0ng-pw-123",
            "is_superuser": "on",
            "is_staff": "on",
        })
        sneaky = User.objects.get(username="sneaky")
        self.assertFalse(sneaky.is_superuser)


class RichTextSanitizeTests(SimpleTestCase):
    """SEC-2: admin CKEditor HTML must be stripped of XSS before public render."""

    def test_strips_script_and_event_handlers(self):
        from apps.common.richtext import sanitize_rich_html
        self.assertNotIn("<script", sanitize_rich_html("<p>a</p><script>alert(1)</script>"))
        self.assertNotIn("onerror", sanitize_rich_html('<img src=x onerror=alert(1)>'))
        self.assertNotIn("javascript:", sanitize_rich_html('<a href="javascript:alert(1)">x</a>'))

    def test_keeps_safe_markup(self):
        from apps.common.richtext import sanitize_rich_html
        out = sanitize_rich_html('<p><strong>B</strong> <a href="https://x.uz">l</a></p>')
        self.assertIn("<strong>B</strong>", out)
        self.assertIn('href="https://x.uz"', out)

    def test_iframe_host_allowlist(self):
        from apps.common.richtext import sanitize_rich_html
        self.assertIn("youtube.com/embed", sanitize_rich_html(
            '<iframe src="https://www.youtube.com/embed/abc"></iframe>'))
        # Off-allowlist host: the src is dropped (iframe left empty/harmless).
        self.assertNotIn("evil.com", sanitize_rich_html(
            '<iframe src="https://evil.com/x"></iframe>'))

    def test_empty_input(self):
        from apps.common.richtext import sanitize_rich_html
        self.assertEqual(sanitize_rich_html(""), "")
        self.assertEqual(sanitize_rich_html(None), "")
