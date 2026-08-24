"""
Django settings for Tagayev Methods.
"""
import sys
from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# True while the Django test runner is active (``manage.py test``).
TESTING = "test" in sys.argv

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
# Defaults are the SAFE (production) values: a missing/mistyped DEBUG in the
# server .env must fail closed, not silently ship the site with DEBUG=True.
# Development opts IN to debug via .env (DEBUG=True) — see .env.example.
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    SECRET_KEY=(str, "django-insecure-dev-key-change-me"),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# Admin panel URL prefix. Default "admin/". Set a hard-to-guess value in .env
# (e.g. ADMIN_URL=boshqaruv-7x3k) to keep the login page off the obvious path.
# Normalised to "<prefix>/" (no leading slash, single trailing slash) so the
# value works in config/urls.py regardless of how it is written in .env.
ADMIN_URL = env("ADMIN_URL", default="admin/").strip().strip("/") + "/"

# Number of trusted reverse proxies in front of the app (nginx = 1; add 1 if a
# CDN/WAF such as Cloudflare also proxies). The real client IP is read this many
# hops from the END of X-Forwarded-For — client-supplied prefixes are untrusted,
# so the lead-form rate-limit (apps/leads/views.py) cannot be bypassed by sending
# a forged X-Forwarded-For header.
TRUSTED_PROXY_COUNT = env.int("TRUSTED_PROXY_COUNT", default=1)

# Telegram (lead notifications) — filled in later phases
TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", default="")
TELEGRAM_ADMIN_CHAT_ID = env("TELEGRAM_ADMIN_CHAT_ID", default="")

# ---------------------------------------------------------------------------
# Security — production hardening (active only when DEBUG=False)
# ---------------------------------------------------------------------------
# These browser-facing protections require HTTPS, so they are gated on DEBUG:
# local development over plain http keeps working, while production (DEBUG=False
# behind nginx + Certbot) switches them all on. `manage.py check --deploy`
# reports zero issues with this block active (see apps/common/test_deploy.py).
if not DEBUG:
    # Fail fast rather than silently shipping the insecure development defaults.
    if SECRET_KEY.startswith("django-insecure-") or SECRET_KEY in ("", "change-me"):
        raise ImproperlyConfigured(
            "SECRET_KEY production uchun yaroqsiz (dev qiymati ishlatilyapti). "
            "Kuchli kalit yarating va .env ga yozing:\n"
            '  python -c "from django.core.management.utils import '
            'get_random_secret_key; print(get_random_secret_key())"'
        )
    if "*" in ALLOWED_HOSTS:
        raise ImproperlyConfigured(
            "ALLOWED_HOSTS production-da '*' boʻlishi mumkin emas — aniq "
            "domenlarni koʻrsating, masalan: tagayev.uz,www.tagayev.uz"
        )

    # nginx/Certbot terminates TLS and forwards the original scheme.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True
    SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)

    # HTTP Strict Transport Security. Env-tunable because it is hard to undo
    # once browsers cache it — drop SECURE_HSTS_SECONDS to a small value (e.g.
    # 3600) on the very first HTTPS deploy, then raise to a year once stable.
    SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)  # 1 yil
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True)
    SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=True)

    # Cookies travel only over HTTPS.
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # Defence in depth.
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
    SESSION_COOKIE_HTTPONLY = True
    X_FRAME_OPTIONS = "DENY"
    # Django defaults to "Lax" already; explicit so it's not silently relying
    # on a default an upgrade could change.
    SESSION_COOKIE_SAMESITE = "Lax"
    CSRF_COOKIE_SAMESITE = "Lax"

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    # Unfold admin theme — MUST precede django.contrib.admin
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",

    # i18n — MUST precede django.contrib.admin
    "modeltranslation",

    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    # Custom staticfiles config: excludes the Tailwind source (source.css) from
    # collectstatic so WhiteNoise's manifest storage never chokes on its
    # `@import "tailwindcss";`. App label stays "staticfiles". See apps/common/apps.py.
    "apps.common.apps.CustomStaticFilesConfig",
    "django.contrib.sitemaps",

    # Third-party
    "solo",
    "django_tailwind_cli",
    "django_ckeditor_5",
    "easy_thumbnails",
    # Admin-login brute-force protection (rate-limit + lockout + attempt log).
    "axes",

    # Local apps
    "apps.common",
    "apps.siteconfig",
    "apps.pages",
    "apps.courses",
    "apps.teachers",
    "apps.gallery",
    "apps.testimonials",
    "apps.news",
    "apps.certificates",
    "apps.leads",
    "apps.analytics",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "apps.common.middleware.DefaultUzLocaleMiddleware",  # after Session, before Common
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.analytics.middleware.VisitLogMiddleware",  # log public page visits
    # django-axes: MUST be the last middleware — wraps the login flow to enforce
    # lockouts after too many failed admin-login attempts.
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "apps.common.context_processors.site_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Database (SQLite + WAL for safer concurrent analytics writes)
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "OPTIONS": {
            "init_command": (
                "PRAGMA journal_mode=WAL;"
                "PRAGMA synchronous=NORMAL;"
                "PRAGMA foreign_keys=ON;"
                "PRAGMA busy_timeout=5000;"
            ),
            "transaction_mode": "IMMEDIATE",
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Auth is admin-only; keep redirects on the admin instead of Django's /accounts/* defaults.
LOGIN_URL = "admin:login"
LOGIN_REDIRECT_URL = "admin:index"

# ---------------------------------------------------------------------------
# django-axes — admin-login brute-force protection
# ---------------------------------------------------------------------------
# AxesStandaloneBackend MUST come first so a locked-out (ip, username) pair is
# rejected before Django's ModelBackend ever checks the password. It has no
# get_user(), so the test client's force_login() skips it and uses ModelBackend.
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# App-level protection (defence-in-depth on top of the nginx rate-limit): the
# admin login is the only auth surface. Lock a specific (client IP + username)
# pair after 5 failed attempts for 1 hour; a successful login resets its counter.
# Every attempt (success and failure) is recorded to the DB and is visible under
# admin → "Access attempts", giving an audit trail of brute-force activity and
# the source IPs to block.
AXES_ENABLED = env.bool("AXES_ENABLED", default=True)
AXES_FAILURE_LIMIT = env.int("AXES_FAILURE_LIMIT", default=5)
AXES_COOLOFF_TIME = env.int("AXES_COOLOFF_HOURS", default=1)  # hours
# Lock the IP+username *combination* (not the bare IP) so a shared/NAT IP does
# not lock out unrelated staff, while still stopping a targeted password guess.
AXES_LOCKOUT_PARAMETERS = [["ip_address", "username"]]
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_CALLABLE = None  # default 429 response on lockout
# Read the real client IP behind nginx (same trust model as the lead-form limiter):
# count TRUSTED_PROXY_COUNT proxy hops so a forged X-Forwarded-For cannot spoof it.
AXES_IPWARE_PROXY_COUNT = TRUSTED_PROXY_COUNT
AXES_IPWARE_META_PRECEDENCE_ORDER = ("HTTP_X_FORWARDED_FOR", "REMOTE_ADDR")
# Only guard the admin login path (the sole login surface); never interfere with
# public views if an auth check ever runs there.
AXES_ONLY_ADMIN_SITE = True

# ---------------------------------------------------------------------------
# Cache — DatabaseCache: shared across gunicorn workers (no Redis needed)
# ---------------------------------------------------------------------------
# The lead-form rate-limit (apps/leads/views.py) counts submissions per IP in
# the cache. With the default per-process LocMemCache each gunicorn worker keeps
# its own counter, so the effective limit becomes (workers × RATE_LIMIT_MAX) and
# resets on every restart. A shared backend makes the limit accurate. DatabaseCache
# needs no extra service — create its table once at deploy:
#   python manage.py createcachetable
# (Django's test runner creates it automatically during tests.)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "tagayev_cache",
        "TIMEOUT": 300,
        "OPTIONS": {"MAX_ENTRIES": 5000},
    },
    # Template-fragment cache for the landing sections (see templates/pages/
    # landing.html). Shared DatabaseCache so all workers serve the same cached
    # HTML; reuses the default cache table (fragment keys are namespaced).
    "fragments": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "tagayev_cache",
        "TIMEOUT": 300,
    },
    # Per-process in-memory cache for the read-mostly singletons (SiteConfig,
    # HeroSection, SiteCopy). django-solo hits the DB on every get_solo() unless
    # SOLO_CACHE is set; a LocMemCache serves them from RAM with no DB round-trip
    # (a shared DatabaseCache would just swap 3 model SELECTs for 3 cache SELECTs).
    "solo": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "tagayev-solo",
    },
}

# django-solo: cache the singletons in the "solo" LocMemCache. Solo invalidates
# its own key on save; the short timeout bounds cross-worker staleness (another
# gunicorn worker keeps a stale copy for at most this long after an admin edit).
SOLO_CACHE = "solo"
SOLO_CACHE_TIMEOUT = 300  # seconds
SOLO_CACHE_PREFIX = "solo"

# The solo LocMemCache is process-global and is NOT rolled back between tests
# (unlike the DB), so a cached singleton would leak across test methods. Disable
# solo caching under the test runner to keep tests isolated; production keeps it.
if TESTING:
    SOLO_CACHE = None
    # Landing fragment cache is not rolled back between tests and keys only on
    # language, so cached HTML would leak across tests that render "/". Make it a
    # no-op under the test runner (the shared "default" cache stays real so the
    # lead rate-limit tests still exercise a genuine cross-worker backend).
    CACHES["fragments"] = {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}

# ---------------------------------------------------------------------------
# Internationalization (uz default, ru, en)
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "uz"
LANGUAGES = [
    ("uz", "Oʻzbekcha"),
    ("ru", "Русский"),
    ("en", "English"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
USE_I18N = True
USE_TZ = True
TIME_ZONE = "Asia/Tashkent"

MODELTRANSLATION_DEFAULT_LANGUAGE = "uz"
MODELTRANSLATION_LANGUAGES = ("uz", "ru", "en")
MODELTRANSLATION_FALLBACK_LANGUAGES = ("uz", "ru", "en")
MODELTRANSLATION_CUSTOM_FIELDS = ("CKEditor5Field",)

# ---------------------------------------------------------------------------
# Static & media
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "assets", BASE_DIR / "static"]

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------------------------------------------------------------
# easy-thumbnails — responsive WebP delivery (Core Web Vitals)
# ---------------------------------------------------------------------------
# Default quality for generated thumbnails. 82 is a good quality/size
# sweet spot for photographic content. THUMBNAIL_QUALITY backs the
# thumbnailer's per-instance default; DEFAULT_OPTIONS covers the tag path.
THUMBNAIL_DEFAULT_OPTIONS = {"quality": 82}
THUMBNAIL_QUALITY = 82
# Keep the original extension for the <img> fallback (JPG stays JPG, PNG stays
# PNG, etc.). The WebP <source> variants force a .webp extension explicitly in
# apps/common/templatetags/media_tags.py (PRESERVE_EXTENSIONS alone keeps the
# source extension even for format="WEBP", which would mislabel the file).
THUMBNAIL_PRESERVE_EXTENSIONS = ("jpg", "jpeg", "png", "gif", "webp")
# Silent in production: a missing/unreadable source yields an empty URL
# (the template keeps its gradient placeholder) instead of raising.
THUMBNAIL_DEBUG = False
# Persist each thumbnail's width/height in the DB. Without this, every
# {% responsive_img %} re-opens and PIL-decodes each variant on EVERY render
# just to read its dimensions (~230 decodes per landing render). With it on,
# dimensions come back inside the existing lookup — decode happens once.
THUMBNAIL_CACHE_DIMENSIONS = True

# Upload limits (security)
DATA_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024   # 12 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 2000

# CKEditor 5
CKEDITOR_5_FILE_UPLOAD_PERMISSION = "staff"
CKEDITOR_5_UPLOAD_FILE_TYPES = ["jpg", "jpeg", "png", "webp", "gif"]
CKEDITOR_5_MAX_FILE_SIZE = 5  # MB
CKEDITOR_5_CONFIGS = {
    "default": {
        "toolbar": [
            "heading", "|",
            "bold", "italic", "underline", "strikethrough", "code", "|",
            "fontSize", "fontColor", "highlight", "|",
            "alignment", "|",
            "bulletedList", "numberedList", "todoList", "outdent", "indent", "|",
            "link", "blockQuote", "insertImage", "mediaEmbed", "insertTable",
            "horizontalLine", "|",
            "removeFormat", "|",
            "undo", "redo",
        ],
        "height": "420px",
        "image": {
            "toolbar": ["imageTextAlternative", "|", "resizeImage"],
        },
        "table": {
            "contentToolbar": ["tableColumn", "tableRow", "mergeTableCells"],
        },
        # Save the real <iframe> into the field HTML so embeds render on the site.
        "mediaEmbed": {"previewsInData": True},
        "heading": {
            "options": [
                {"model": "paragraph", "title": "Paragraph", "class": "ck-heading_paragraph"},
                {"model": "heading2", "view": "h2", "title": "Sarlavha 2", "class": "ck-heading_heading2"},
                {"model": "heading3", "view": "h3", "title": "Sarlavha 3", "class": "ck-heading_heading3"},
                {"model": "heading4", "view": "h4", "title": "Sarlavha 4", "class": "ck-heading_heading4"},
            ],
        },
    },
}

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if not DEBUG
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        )
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Logging — stream to stderr so systemd/journald (or gunicorn) captures it.
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} [{levelname}] {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": env("DJANGO_LOG_LEVEL", default="INFO"),
            "propagate": False,
        },
        # Suspicious-operation / disallowed-host attempts, etc.
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        # Lead-notification failures (Telegram) bubble up here.
        "apps": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# ---------------------------------------------------------------------------
# Tailwind CSS (standalone CLI, Tailwind v4 — no Node)
# ---------------------------------------------------------------------------
TAILWIND_CLI_VERSION = "4.1.3"
TAILWIND_CLI_SRC_CSS = "assets/css/source.css"
TAILWIND_CLI_DIST_CSS = "css/tailwind.css"
TAILWIND_CLI_AUTOMATIC_DOWNLOAD = True

# ---------------------------------------------------------------------------
# Unfold admin (expanded with dashboard/sidebar in later phases)
# ---------------------------------------------------------------------------
from django.templatetags.static import static  # noqa: E402
from django.urls import reverse_lazy  # noqa: E402
from django.utils.translation import gettext_lazy as _  # noqa: E402

def _admin_favicon_href(request):
    """Admin browser-tab icon href: the uploaded site favicon if one is set,
    otherwise the bundled brand logo. Mirrors the public <link rel="icon">
    (see templates/base.html). Defensive so a missing table (e.g. during an
    early migration) degrades to the static logo instead of erroring."""
    try:
        from apps.siteconfig.models import SiteConfig
        favicon = SiteConfig.get_solo().favicon
        if favicon:
            return favicon.url
    except Exception:  # pragma: no cover - defensive
        pass
    return static("img/logo.png")


UNFOLD = {
    "SITE_TITLE": "Tagayev Methods",
    "SITE_HEADER": "Tagayev Methods",
    "SITE_SUBHEADER": _("Boshqaruv paneli"),
    "DASHBOARD_CALLBACK": "apps.analytics.dashboard.dashboard_callback",
    "SITE_SYMBOL": "school",
    # Admin browser-tab favicon (Unfold renders these in the admin <head>).
    "SITE_FAVICONS": [
        {"rel": "icon", "type": "image/png", "href": _admin_favicon_href},
    ],
    "SITE_URL": "/",  # "Saytni koʻrish" tugmasi
    # Qo'shimcha admin CSS (CKEditor tungi rejim tuzatmasi + UI tweaks)
    "STYLES": [
        lambda request: static("css/admin_extra.css"),
        lambda request: static("css/admin_dashboard.css"),
    ],
    "SCRIPTS": [
        lambda request: static("js/admin_sidebar.js"),
        lambda request: static("js/admin_dashboard.js"),
    ],
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "SHOW_BACK_BUTTON": True,
    "COLORS": {
        "primary": {
            "50": "246 243 255",
            "100": "235 227 255",
            "200": "214 197 254",
            "300": "183 153 249",
            "400": "150 106 240",
            "500": "122 69 224",
            "600": "101 51 189",
            "700": "81 40 152",
            "800": "63 32 119",
            "900": "44 22 85",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "navigation": [
            {
                "title": _("Boshqaruv"),
                "items": [
                    {"title": _("Bosh sahifa"), "icon": "dashboard", "link": reverse_lazy("admin:index")},
                    {"title": _("Saytni koʻrish"), "icon": "language", "link": "/"},
                ],
            },
            {
                "title": _("Murojaatlar"),
                "items": [
                    {
                        "title": _("Arizalar"),
                        "icon": "inbox",
                        "link": reverse_lazy("admin:leads_lead_changelist"),
                        "badge": "apps.leads.badges.new_leads_count",
                    },
                ],
            },
            {
                "title": _("CRM"),
                "items": [
                    {"title": _("Manbalar"), "icon": "hub",
                     "link": reverse_lazy("admin:leads_leadsource_changelist")},
                ],
            },
            {
                "title": _("Sayt kontenti"),
                "collapsible": True,
                "items": [
                    {"title": _("Kurslar"), "icon": "menu_book", "link": reverse_lazy("admin:courses_course_changelist")},
                    {"title": _("Oʻqituvchilar"), "icon": "groups", "link": reverse_lazy("admin:teachers_teacher_changelist")},
                    {"title": _("Yangiliklar"), "icon": "campaign", "link": reverse_lazy("admin:news_newspost_changelist")},
                    {"title": _("Galereya"), "icon": "photo_library", "link": reverse_lazy("admin:gallery_galleryalbum_changelist")},
                    {"title": _("Galereya videolari"), "icon": "smart_display", "link": reverse_lazy("admin:gallery_galleryvideo_changelist")},
                    {"title": _("Sertifikatlar"), "icon": "workspace_premium", "link": reverse_lazy("admin:certificates_certificate_changelist")},
                    {"title": _("Fikrlar"), "icon": "reviews", "link": reverse_lazy("admin:testimonials_testimonial_changelist")},
                ],
            },
            {
                "title": _("Bosh sahifa bloklari"),
                "collapsible": True,
                "items": [
                    {"title": _("Hero bo'limi"), "icon": "wallpaper", "link": reverse_lazy("admin:pages_herosection_changelist")},
                    {"title": _("Bosh sahifa videosi"), "icon": "smart_display", "link": reverse_lazy("admin:pages_homevideo_changelist")},
                    {"title": _("Biz haqimizda"), "icon": "article", "link": reverse_lazy("admin:pages_aboutsection_changelist")},
                    {"title": _("Statistika"), "icon": "bar_chart", "link": reverse_lazy("admin:pages_statitem_changelist")},
                    {"title": _("Nega biz"), "icon": "verified", "link": reverse_lazy("admin:pages_whyusitem_changelist")},
                    {"title": _("Sayt matnlari"), "icon": "edit_note", "link": reverse_lazy("admin:pages_sitecopy_changelist")},
                ],
            },
            {
                "title": _("Analitika"),
                "items": [
                    {"title": _("Tashriflar"), "icon": "analytics", "link": reverse_lazy("admin:analytics_visitlog_changelist")},
                ],
            },
            {
                "title": _("Sozlamalar"),
                "collapsible": True,
                "items": [
                    {"title": _("Sayt sozlamalari"), "icon": "settings", "link": reverse_lazy("admin:siteconfig_siteconfig_changelist")},
                    {"title": _("Ijtimoiy tarmoqlar"), "icon": "share", "link": reverse_lazy("admin:siteconfig_sociallink_changelist")},
                    {"title": _("Telegram qabul qiluvchilar"), "icon": "notifications", "link": reverse_lazy("admin:siteconfig_telegramrecipient_changelist")},
                    {"title": _("Foydalanuvchilar"), "icon": "person", "link": reverse_lazy("admin:auth_user_changelist")},
                ],
            },
        ],
    },
}
