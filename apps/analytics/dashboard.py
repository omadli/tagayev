"""Unfold dashboard callback for the admin index page.

Wired via UNFOLD["DASHBOARD_CALLBACK"]. Unfold calls this as
``context = dashboard_callback(request, context)`` (sites.py), so it MUST
return the context. The whole body is defensive: if the analytics table does
not yet exist (e.g. during a migration window) it degrades to zeros instead of
500-ing the admin index.

Time windows are rolling ranges ("last 24 hours", "last 30 days", …) chosen
from the header dropdown, plus a custom from/to range. Every widget on the page
reads the same window, and every headline reconciles with the chart.
"""
import json
from datetime import datetime, time, timedelta
from urllib.parse import urlsplit

from django.db.models import Count, Min
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.translation import get_language, gettext_lazy as _

from apps.common.tech_icons import browser_slug, host_slug, os_slug

from .middleware import LOCAL_CODE
from .models import VisitLog

_DEVICE_LABELS = dict(VisitLog.DeviceType.choices)

# Material Symbols icon per device type.
_DEVICE_ICONS = {
    "mobile": "smartphone",
    "tablet": "tablet",
    "desktop": "computer",
    "bot": "smart_toy",
    "other": "devices_other",
}

# --- Time ranges -----------------------------------------------------------
# Rolling windows, in seconds. "all" and "custom" are handled separately.
RANGE_SECONDS = {
    "live": 30 * 60,
    "1h": 60 * 60,
    "24h": 24 * 3600,
    "7d": 7 * 86400,
    "30d": 30 * 86400,
    "3mo": 90 * 86400,
    "6mo": 180 * 86400,
    "12mo": 365 * 86400,
}
PERIODS = tuple(RANGE_SECONDS) + ("all", "custom")
DEFAULT_PERIOD = "30d"
# Old calendar-period keys kept working (bookmarks, sessionStorage, ?period=).
_ALIASES = {"today": "24h", "week": "7d", "month": "30d", "year": "12mo"}

# A visit more than this far after the previous one starts a new session —
# the usual web-analytics convention, and what bounce rate / duration count.
SESSION_GAP = 30 * 60

# Chart colours as literal brand hexes (blue + violet). NOT Unfold var keys:
# Unfold's base-* vars are oklch(), which the canvas renders black.
_BLUE = "#7a45e0"
_VIOLET = "#c08bff"
_RED = "#dcae3c"

_TOP_N = 7


def range_options():
    """[(key, label)] for the header range dropdown, in menu order."""
    return [
        ("live", _("Jonli")),
        ("1h", _("Soʻnggi 1 soat")),
        ("24h", _("Soʻnggi 24 soat")),
        ("7d", _("Soʻnggi 7 kun")),
        ("30d", _("Soʻnggi 30 kun")),
        ("3mo", _("Soʻnggi 3 oy")),
        ("6mo", _("Soʻnggi 6 oy")),
        ("12mo", _("Soʻnggi 1 yil")),
        ("all", _("Butun davr")),
    ]


def range_label(period):
    for key, label in range_options():
        if key == period:
            return label
    return _("Tanlangan davr")


def clean_period(value):
    """Whitelist a requested range key, defaulting to the last 30 days."""
    value = _ALIASES.get(value, value)
    return value if value in PERIODS else DEFAULT_PERIOD


def resolve_window(period, start=None, end=None):
    """(period, start_dt|None, end_dt) — start None means "since the beginning"."""
    now = timezone.now()
    if period == "custom":
        try:
            first, last = parse_date(start or ""), parse_date(end or "")
        except ValueError:
            first = last = None
        if first and last and first <= last:
            tz = timezone.get_current_timezone()
            return (
                period,
                timezone.make_aware(datetime.combine(first, time.min), tz),
                timezone.make_aware(
                    datetime.combine(last + timedelta(days=1), time.min), tz
                ),
            )
        period = DEFAULT_PERIOD
    seconds = RANGE_SECONDS.get(period)
    if seconds is None:  # "all"
        return period, None, now
    return period, now - timedelta(seconds=seconds), now


def _bucket_plan(start, end):
    """(step_seconds|None, keys, labels) — step None means calendar months.

    Granularity follows the span: 5-minute buckets up to 2 hours, hourly up to
    ~2 days, daily up to ~3 months, monthly beyond. TIME_ZONE has no DST, so
    fixed-second day steps stay aligned to local midnight.
    """
    tz = timezone.get_current_timezone()
    span = (end - start).total_seconds()
    if span <= 2 * 3600:
        step, fmt = 300, "%H:%M"
    elif span <= 50 * 3600:
        step, fmt = 3600, "%H:%M"
    elif span <= 95 * 86400:
        step, fmt = 86400, "%d.%m"
    else:
        step, fmt = None, ""

    if step is None:
        first, last = timezone.localtime(start, tz), timezone.localtime(end, tz)
        keys, year, month = [], first.year, first.month
        while (year, month) <= (last.year, last.month) and len(keys) < 240:
            keys.append((year, month))
            year, month = (year + 1, 1) if month == 12 else (year, month + 1)
        return None, keys, [f"{m:02d}.{y % 100:02d}" for y, m in keys]

    local = timezone.localtime(start, tz)
    if step >= 86400:
        anchor = local.replace(hour=0, minute=0, second=0, microsecond=0)
    elif step >= 3600:
        anchor = local.replace(minute=0, second=0, microsecond=0)
    else:
        anchor = local.replace(
            minute=local.minute - local.minute % 5, second=0, microsecond=0
        )
    count = max(1, min(int((end - anchor).total_seconds() // step) + 1, 400))
    keys = [anchor + timedelta(seconds=step * i) for i in range(count)]
    return step, keys, [timezone.localtime(k, tz).strftime(fmt) for k in keys]


def _source_label(referrer, self_hosts):
    """Referrer host without scheme/www; "" for direct and internal links."""
    if not referrer:
        return ""
    try:
        host = urlsplit(referrer).netloc.lower()
    except ValueError:
        return ""
    host = host.split("@")[-1].split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    return "" if not host or host in self_hosts else host


_ROW_FIELDS = (
    "visitor_id", "created_at", "path", "referrer", "country",
    "country_code", "browser", "os", "device_type",
)


def _aggregate(qs, plan, self_hosts):
    """One streaming pass producing every number the dashboard shows.

    ponytail: a single ordered query plus Python aggregation, instead of ~8
    GROUP BY queries — distinct-visitor counts per bucket and per row are not
    expressible in the ORM anyway, and sessions need row order. Streams with
    .iterator(), so memory is bounded by the number of distinct visitors /
    paths / countries rather than by the row count. If a window ever holds
    millions of rows, pre-aggregate into a daily rollup table.
    """
    step, keys, _labels = plan
    slots = len(keys)
    month_index = {k: i for i, k in enumerate(keys)} if step is None else None
    anchor = keys[0] if step else None
    tz = timezone.get_current_timezone()

    view_buckets = [0] * slots
    user_buckets = [set() for _ in range(slots)]
    users, views = set(), 0
    pages, sources, countries = {}, {}, {}
    browsers, systems, devices = {}, {}, {}
    country_names = {}
    sessions = bounced = 0
    duration = 0.0
    current = session_start = session_last = None
    session_views = 0

    def add(store, key, visitor):
        slot = store.get(key)
        if slot is None:
            slot = store[key] = [0, set()]
        slot[0] += 1
        slot[1].add(visitor)

    rows = qs.order_by("visitor_id", "created_at").values_list(*_ROW_FIELDS)
    for (visitor, at, path, referrer, country, code,
         browser, system, device) in rows.iterator(chunk_size=2000):
        views += 1
        users.add(visitor)

        if step is None:
            local = timezone.localtime(at, tz)
            index = month_index.get((local.year, local.month), -1)
        else:
            index = int((at - anchor).total_seconds() // step)
        if 0 <= index < slots:
            view_buckets[index] += 1
            user_buckets[index].add(visitor)

        if visitor != current:
            if current is not None:
                sessions += 1
                bounced += session_views == 1
                duration += (session_last - session_start).total_seconds()
            current, session_start, session_views = visitor, at, 0
        elif (at - session_last).total_seconds() > SESSION_GAP:
            sessions += 1
            bounced += session_views == 1
            duration += (session_last - session_start).total_seconds()
            session_start, session_views = at, 0
        session_last = at
        session_views += 1

        add(pages, path, visitor)
        add(sources, _source_label(referrer, self_hosts), visitor)
        key = (code or "").upper()
        if key and key not in country_names:
            country_names[key] = country
        add(countries, key, visitor)
        add(browsers, browser, visitor)
        add(systems, system, visitor)
        add(devices, device, visitor)

    if current is not None:
        sessions += 1
        bounced += session_views == 1
        duration += (session_last - session_start).total_seconds()

    return {
        "users": len(users),
        "views": views,
        "bounce": round(bounced * 100 / sessions) if sessions else 0,
        "duration": duration / sessions if sessions else 0.0,
        "user_series": [len(s) for s in user_buckets],
        "view_series": view_buckets,
        "pages": pages,
        "sources": sources,
        "countries": countries,
        "country_names": country_names,
        "browsers": browsers,
        "systems": systems,
        "devices": devices,
    }


def _top(store, label_fn=None, icon_fn=None, brand_fn=None, limit=_TOP_N):
    """Top rows sorted by users, with a bar width relative to the leader.

    ``icon_fn`` picks a Material Symbols name, ``brand_fn`` a slug for the
    {% tech_icon %} brand mark — a row uses whichever its table provides.
    """
    items = sorted(store.items(), key=lambda kv: (-len(kv[1][1]), -kv[1][0]))[:limit]
    leader = max((len(value[1]) for _key, value in items), default=0) or 1
    return [{
        "key": key,
        "label": str(label_fn(key)) if label_fn else (key or ""),
        "users": len(value[1]),
        "views": value[0],
        "percent": round(len(value[1]) * 100 / leader),
        "icon": icon_fn(key) if icon_fn else "",
        "brand": brand_fn(key) if brand_fn else "",
    } for key, value in items]


def _fmt_duration(seconds):
    seconds = int(round(seconds))
    if seconds >= 3600:
        return f"{seconds // 3600}h {seconds % 3600 // 60}m"
    if seconds >= 60:
        return f"{seconds // 60}m {seconds % 60}s"
    return f"{seconds}s"


def _trend(now_value, was_value, higher_is_better=True):
    """{'pct', 'up', 'good'} versus the previous window, or None if flat/new."""
    if not was_value:
        return None
    change = round((now_value - was_value) * 100 / was_value)
    if change == 0:
        return None
    return {"pct": abs(change), "up": change > 0,
            "good": (change > 0) == higher_is_better}


def _country_label(code):
    if code == LOCAL_CODE:
        return _("Mahalliy tarmoq")
    if not code:
        return _("Aniqlanmagan")
    return code  # localized client-side from the ISO code (Intl.DisplayNames)


def _unknown(value):
    return value or str(_("Nomaʼlum"))


def _tech_panes(browsers, devices, systems):
    """Panes of the Technology card — the segmented switch flips between them."""
    return [
        ("browsers", browsers, _("Brauzer")),
        ("devices", devices, _("Qurilma")),
        ("os", systems, _("Operatsion tizim")),
    ]


def _content_inventory():
    """Static (non-time) content totals — not affected by the range filter."""
    from apps.certificates.models import Certificate
    from apps.courses.models import Course
    from apps.gallery.models import GalleryImage
    from apps.news.models import NewsPost
    from apps.teachers.models import Teacher
    from apps.testimonials.models import Testimonial

    inventory = [
        (_("Kurslar"), Course.objects, {"is_active": True}),
        (_("Oʻqituvchilar"), Teacher.objects, {"is_active": True}),
        (_("Yangiliklar"), NewsPost.objects, {"is_published": True}),
        (_("Sertifikatlar"), Certificate.objects, {"is_active": True}),
        (_("Fikrlar"), Testimonial.objects, {"is_active": True}),
        (_("Galereya rasmlari"), GalleryImage.objects, {"is_active": True}),
    ]
    return {
        "headers": [str(_("Boʻlim")), str(_("Jami")), str(_("Faol / chop etilgan"))],
        "rows": [[str(label), mgr.count(), mgr.filter(**flt).count()]
                 for label, mgr, flt in inventory],
    }


def dashboard_callback(request, context):
    """Unfold index callback — renders the default (or ?period=) range."""
    context.update(build_dashboard_data(
        request,
        request.GET.get("period"),
        request.GET.get("from"),
        request.GET.get("to"),
    ))
    try:
        context["content_inventory"] = _content_inventory()
    except Exception:  # pragma: no cover - defensive
        context.setdefault("content_inventory", {"headers": [], "rows": []})
    context["range_options"] = range_options()
    return context


def _empty(period, start, end):
    labels = _bucket_plan(start or end - timedelta(days=30), end)[2]
    return {
        "dash_period": period,
        "dash_from": "",
        "dash_to": "",
        "dash_range_label": range_label(period),
        "stats": [],
        "visits_chart": json.dumps({"labels": labels, "datasets": []}),
        "leads_chart": json.dumps({"labels": labels, "datasets": []}),
        "top_pages": [], "top_sources": [], "top_countries": [],
        "top_browsers": [], "top_os": [], "top_devices": [],
        "tech_panes": _tech_panes([], [], []),
        "map_countries": "[]",
        "leads_by_status": {"headers": [], "rows": []},
        "source_cards": [],
    }


def build_dashboard_data(request, period, start=None, end=None):
    """Every range-dependent widget. Defensive: zeroed widgets on DB trouble."""
    period, window_start, window_end = resolve_window(clean_period(period), start, end)
    data = _empty(period, window_start, window_end)
    data["dash_from"] = start or ""
    data["dash_to"] = end or ""
    if period == "custom":
        tz = timezone.get_current_timezone()
        data["dash_range_label"] = "{} — {}".format(
            timezone.localtime(window_start, tz).strftime("%d.%m.%Y"),
            (timezone.localtime(window_end, tz) - timedelta(days=1)).strftime("%d.%m.%Y"),
        )
    try:
        from apps.leads.models import Lead, LeadSource
        from apps.siteconfig.models import SiteConfig

        visits = VisitLog.objects.all()
        if window_start is None:
            first = visits.aggregate(m=Min("created_at"))["m"]
            window_start = first or window_end - timedelta(days=30)
        span = window_end - window_start
        plan = _bucket_plan(window_start, window_end)
        labels = plan[2]

        try:
            domain = SiteConfig.get_solo().site_domain or ""
        except Exception:  # pragma: no cover - defensive
            domain = ""
        self_hosts = {h.lower().split(":")[0].removeprefix("www.")
                      for h in (domain, request.get_host()) if h}

        in_window = visits.filter(created_at__gte=window_start,
                                  created_at__lt=window_end)
        now = _aggregate(in_window, plan, self_hosts)
        # Same-length window immediately before this one, for the trend arrows.
        before = _aggregate(
            visits.filter(created_at__gte=window_start - span,
                          created_at__lt=window_start),
            _bucket_plan(window_start - span, window_start), self_hosts,
        )

        data["stats"] = [
            {"key": "users", "title": _("Foydalanuvchilar"), "icon": "person",
             "value": now["users"], "color": _BLUE, "series": True,
             "trend": _trend(now["users"], before["users"])},
            {"key": "views", "title": _("Sahifa koʻrishlari"), "icon": "visibility",
             "value": now["views"], "color": _VIOLET, "series": True,
             "trend": _trend(now["views"], before["views"])},
            {"key": "bounce", "title": _("Chiqib ketish darajasi"), "icon": "call_missed_outgoing",
             "value": f"{now['bounce']}%", "color": "", "series": False,
             "trend": _trend(now["bounce"], before["bounce"], higher_is_better=False)},
            {"key": "duration", "title": _("Oʻrtacha davomiylik"), "icon": "schedule",
             "value": _fmt_duration(now["duration"]), "color": "", "series": False,
             "trend": _trend(now["duration"], before["duration"])},
        ]

        data["visits_chart"] = json.dumps({
            "labels": labels,
            "datasets": [
                {"key": "users", "label": str(_("Foydalanuvchilar")),
                 "data": now["user_series"], "color": _BLUE},
                {"key": "views", "label": str(_("Sahifa koʻrishlari")),
                 "data": now["view_series"], "color": _VIOLET},
            ],
        })

        names = now["country_names"]
        data["top_pages"] = _top(now["pages"], label_fn=lambda p: p or "/")
        data["top_sources"] = _top(
            now["sources"], label_fn=lambda h: h or _("Toʻgʻridan-toʻgʻri"),
            brand_fn=lambda h: host_slug(h) if h else "")
        data["top_countries"] = _top(now["countries"], label_fn=_country_label)
        for row in data["top_countries"]:
            # Fallback name for browsers without Intl.DisplayNames data.
            row["fallback"] = names.get(row["key"], "") or row["label"]
        data["top_browsers"] = _top(now["browsers"], label_fn=_unknown,
                                    brand_fn=browser_slug)
        data["top_os"] = _top(now["systems"], label_fn=_unknown, brand_fn=os_slug)
        data["top_devices"] = _top(
            now["devices"],
            label_fn=lambda d: _DEVICE_LABELS.get(d, d or _("Nomaʼlum")),
            icon_fn=lambda d: _DEVICE_ICONS.get(d, "devices_other"))
        data["tech_panes"] = _tech_panes(
            data["top_browsers"], data["top_devices"], data["top_os"])

        # Choropleth payload: real ISO-2 countries only (ZZ/unknown have no
        # place on the map, but stay in the list above).
        data["map_countries"] = json.dumps([
            {"code": code, "users": len(value[1]), "views": value[0],
             "name": names.get(code, "")}
            for code, value in now["countries"].items()
            if code and code != LOCAL_CODE
        ])

        # --- Leads (CRM) — same window, same buckets ---
        leads = Lead.objects.filter(created_at__gte=window_start,
                                    created_at__lt=window_end)
        data["leads_chart"] = json.dumps({
            "labels": labels,
            "datasets": [{"key": "leads", "label": str(_("Arizalar")),
                          "data": _count_series(leads, plan), "color": _RED}],
        })
        status_labels = dict(Lead.Status.choices)
        data["leads_by_status"] = {
            "headers": [str(_("Holat")), str(_("Soni"))],
            "rows": [[str(status_labels.get(r["status"], r["status"])), r["total"]]
                     for r in leads.values("status").annotate(total=Count("id"))
                                   .order_by("-total")],
        }

        counts = {r["source"]: r["total"]
                  for r in leads.values("source").annotate(total=Count("id"))}
        active = list(LeadSource.objects.filter(is_active=True))
        total_src = sum(counts.get(s.id, 0) for s in active) or 1
        lang = get_language() or "uz"
        data["source_cards"] = [{
            "name": s.name, "count": counts.get(s.id, 0),
            "percent": round(counts.get(s.id, 0) * 100 / total_src),
            "link": s.build_link(domain or request.get_host(), lang),
            "image": s.image.url if s.image else "",
            "brand": s.brand_key, "icon": s.icon or "hub", "color": s.color or "",
        } for s in active]
    except Exception:  # pragma: no cover - defensive (unmigrated tables)
        pass
    return data


def _count_series(qs, plan):
    """Plain per-bucket row counts (no visitor logic) — used for leads."""
    step, keys, _labels = plan
    slots = len(keys)
    buckets = [0] * slots
    tz = timezone.get_current_timezone()
    month_index = {k: i for i, k in enumerate(keys)} if step is None else None
    anchor = keys[0] if step else None
    for at in qs.values_list("created_at", flat=True).iterator(chunk_size=2000):
        if step is None:
            local = timezone.localtime(at, tz)
            index = month_index.get((local.year, local.month), -1)
        else:
            index = int((at - anchor).total_seconds() // step)
        if 0 <= index < slots:
            buckets[index] += 1
    return buckets
