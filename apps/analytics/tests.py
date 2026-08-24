"""Tests for apps.analytics — visit logging, staff exclusion, geo-IP, dashboard."""
from io import StringIO
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from apps.analytics import geoip
from apps.analytics.dashboard import dashboard_callback
from apps.analytics.models import VisitLog

User = get_user_model()

_STATIC_STORAGE = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


class VisitLogModelTests(TestCase):
    def test_country_fields_exist(self):
        v = VisitLog()
        self.assertTrue(hasattr(v, "country"))
        self.assertTrue(hasattr(v, "country_code"))


@override_settings(STORAGES=_STATIC_STORAGE)
class StaffExclusionTests(TestCase):
    """Logged-in staff browsing the live site must NOT be counted; anons are."""

    def test_anonymous_visit_is_logged(self):
        self.assertEqual(VisitLog.objects.count(), 0)
        # A real, routable client IP — the middleware drops loopback/private IPs.
        self.client.get("/uz/", follow=True, REMOTE_ADDR="8.8.8.8")
        self.assertEqual(VisitLog.objects.filter(path="/uz/").count(), 1)

    def test_staff_visit_is_not_logged(self):
        staff = User.objects.create_user(
            username="staffer", password="pw12345678", is_staff=True)
        self.client.force_login(staff)
        self.client.get("/uz/", follow=True, REMOTE_ADDR="8.8.8.8")
        self.assertEqual(VisitLog.objects.filter(path="/uz/").count(), 0)

    def test_loopback_visit_is_logged_as_local(self):
        # Local/LAN traffic is real traffic — it is kept and tagged "Local"
        # instead of dropped, and never handed to the geo resolver.
        self.client.get("/uz/", follow=True, REMOTE_ADDR="127.0.0.1")
        visit = VisitLog.objects.get(path="/uz/")
        self.assertEqual(visit.country, "Local")
        self.assertEqual(visit.country_code, "ZZ")

    def test_private_lan_visit_is_logged_as_local(self):
        self.client.get("/uz/", follow=True, REMOTE_ADDR="192.168.1.5")
        self.assertEqual(VisitLog.objects.get(path="/uz/").country_code, "ZZ")

    def test_public_visit_is_not_marked_local(self):
        self.client.get("/uz/", follow=True, REMOTE_ADDR="8.8.8.8")
        visit = VisitLog.objects.get(path="/uz/")
        self.assertEqual(visit.country, "")
        self.assertEqual(visit.country_code, "")

    def test_visit_gets_a_visitor_id(self):
        self.client.get("/uz/", follow=True, REMOTE_ADDR="8.8.8.8")
        self.assertEqual(len(VisitLog.objects.get(path="/uz/").visitor_id), 32)

    def test_same_client_shares_one_visitor_id(self):
        for _ in range(2):
            self.client.get("/uz/", follow=True, REMOTE_ADDR="8.8.8.8",
                            HTTP_USER_AGENT="Mozilla/5.0")
        ids = set(VisitLog.objects.values_list("visitor_id", flat=True))
        self.assertEqual(len(ids), 1)

    def test_different_clients_get_different_visitor_ids(self):
        self.client.get("/uz/", follow=True, REMOTE_ADDR="8.8.8.8",
                        HTTP_USER_AGENT="Mozilla/5.0")
        self.client.get("/uz/", follow=True, REMOTE_ADDR="9.9.9.9",
                        HTTP_USER_AGENT="Mozilla/5.0")
        ids = set(VisitLog.objects.values_list("visitor_id", flat=True))
        self.assertEqual(len(ids), 2)


@override_settings(STORAGES=_STATIC_STORAGE)
class AdminUrlExclusionTests(TestCase):
    """The (configurable) admin URL must never be counted as a public visit.

    The admin prefix is derived from settings.ADMIN_URL per request, so a custom
    ADMIN_URL is excluded too. Tested at the middleware level because the URLconf
    binds ADMIN_URL at import time — override_settings can't re-route the admin,
    but the middleware reads settings.ADMIN_URL live.
    """

    def _visit(self, path):
        from django.contrib.auth.models import AnonymousUser
        from django.http import HttpResponse

        from apps.analytics.middleware import VisitLogMiddleware
        # A public client IP — loopback/private IPs are dropped by the middleware.
        request = RequestFactory().get(path, REMOTE_ADDR="8.8.8.8")
        request.user = AnonymousUser()
        VisitLogMiddleware(lambda r: HttpResponse(status=200))(request)

    @override_settings(ADMIN_URL="kirma-bu-yerga/")
    def test_custom_admin_url_not_logged(self):
        self._visit("/kirma-bu-yerga/login/")
        self.assertEqual(VisitLog.objects.count(), 0)

    @override_settings(ADMIN_URL="admin/")
    def test_default_admin_url_not_logged(self):
        self._visit("/admin/login/")
        self.assertEqual(VisitLog.objects.count(), 0)

    @override_settings(ADMIN_URL="kirma-bu-yerga/")
    def test_public_path_still_logged(self):
        self._visit("/uz/")
        self.assertEqual(VisitLog.objects.filter(path="/uz/").count(), 1)


class GeoIpResolverTests(TestCase):
    def test_is_public_ip(self):
        self.assertTrue(geoip.is_public_ip("8.8.8.8"))
        self.assertFalse(geoip.is_public_ip("127.0.0.1"))
        self.assertFalse(geoip.is_public_ip("192.168.1.5"))
        self.assertFalse(geoip.is_public_ip("10.0.0.1"))
        self.assertFalse(geoip.is_public_ip("not-an-ip"))

    @patch("apps.analytics.geoip.requests.post")
    def test_resolve_ips_parses_batch(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: [
                {"status": "success", "query": "8.8.8.8",
                 "country": "United States", "countryCode": "US"},
                {"status": "fail", "query": "1.2.3.4"},
            ],
            raise_for_status=lambda: None,
        )
        result = geoip.resolve_ips(["8.8.8.8", "1.2.3.4", "127.0.0.1"])
        self.assertEqual(result, {"8.8.8.8": ("United States", "US")})
        # Private/loopback IPs are filtered out before the request payload.
        sent = mock_post.call_args.kwargs["json"]
        self.assertEqual([e["query"] for e in sent], ["8.8.8.8", "1.2.3.4"])

    @patch("apps.analytics.geoip.requests.post", side_effect=Exception("net down"))
    def test_resolve_ips_network_failure_is_empty(self, _mock):
        self.assertEqual(geoip.resolve_ips(["8.8.8.8"]), {})


class ResolveGeoipCommandTests(TestCase):
    @patch("apps.analytics.management.commands.resolve_geoip.resolve_ips")
    def test_command_backfills_country(self, mock_resolve):
        mock_resolve.return_value = {"8.8.8.8": ("Uzbekistan", "UZ")}
        VisitLog.objects.create(path="/uz/", method="GET", ip_address="8.8.8.8")
        VisitLog.objects.create(path="/ru/", method="GET", ip_address="8.8.8.8")
        call_command("resolve_geoip", stdout=StringIO())
        rows = VisitLog.objects.filter(ip_address="8.8.8.8")
        self.assertTrue(all(r.country == "Uzbekistan" and r.country_code == "UZ" for r in rows))

    @patch("apps.analytics.management.commands.resolve_geoip.resolve_ips")
    def test_command_noop_when_all_resolved(self, mock_resolve):
        VisitLog.objects.create(path="/uz/", method="GET",
                                ip_address="8.8.8.8", country="Uzbekistan")
        call_command("resolve_geoip", stdout=StringIO())
        mock_resolve.assert_not_called()


class DashboardCallbackTests(TestCase):
    def test_callback_returns_new_keys(self):
        ctx = dashboard_callback(RequestFactory().get("/admin/"), {})
        for key in ("stats", "visits_chart", "leads_chart", "map_countries",
                    "leads_by_status", "top_countries", "top_pages",
                    "top_sources", "tech_panes", "content_inventory"):
            self.assertIn(key, ctx)

    def test_content_inventory_has_all_sections(self):
        ctx = dashboard_callback(RequestFactory().get("/admin/"), {})
        rows = ctx["content_inventory"]["rows"]
        self.assertEqual(len(rows), 6)  # courses, teachers, news, certs, testimonials, gallery
        for row in rows:
            self.assertEqual(len(row), 3)  # label, total, active

    def test_top_countries_reflects_resolved_visits(self):
        VisitLog.objects.create(path="/uz/", method="GET", ip_address="8.8.8.8",
                                country="Uzbekistan", country_code="UZ",
                                visitor_id="v1")
        ctx = dashboard_callback(RequestFactory().get("/admin/"), {})
        self.assertEqual([row["key"] for row in ctx["top_countries"]], ["UZ"])
        self.assertIn("UZ", ctx["map_countries"])

    def test_local_visits_stay_off_the_map(self):
        VisitLog.objects.create(path="/uz/", method="GET", ip_address="127.0.0.1",
                                country="Local", country_code="ZZ", visitor_id="v1")
        ctx = dashboard_callback(RequestFactory().get("/admin/"), {})
        self.assertEqual([row["key"] for row in ctx["top_countries"]], ["ZZ"])
        self.assertEqual(ctx["map_countries"], "[]")


class DashboardSourceCardsTests(TestCase):
    """Per-source cards are now driven entirely by the global period filter
    (``build_dashboard_data``) — no more independent CRM tabs/``source_period``/
    ``counts_json``/``percents_json`` (removed with the global filter; see
    ``DashboardIndexRenderTests`` for the filter-bar rendering)."""

    def _data(self, period="all"):
        from apps.analytics.dashboard import build_dashboard_data
        return build_dashboard_data(RequestFactory().get("/admin/"), period)

    def _card(self, data, name):
        return next(c for c in data["source_cards"] if c["name"] == name)

    def test_periods_respect_time_windows(self):
        from datetime import timedelta

        from django.utils import timezone

        from apps.leads.models import Lead, LeadSource
        tg = LeadSource.objects.get(slug="telegram")
        Lead.objects.create(full_name="Now", phone="+998901234567", source=tg)
        old = Lead.objects.create(full_name="Old", phone="+998901234568", source=tg)
        # 8 days ago: outside today+week, inside month(30d)+all. .update()
        # bypasses auto_now_add so we can backdate created_at.
        Lead.objects.filter(pk=old.pk).update(
            created_at=timezone.now() - timedelta(days=8)
        )
        self.assertEqual(self._card(self._data("today"), "Telegram")["count"], 1)
        self.assertEqual(self._card(self._data("week"), "Telegram")["count"], 1)
        self.assertEqual(self._card(self._data("month"), "Telegram")["count"], 2)
        self.assertEqual(self._card(self._data("all"), "Telegram")["count"], 2)

    def test_inactive_source_excluded_and_percent_rebased(self):
        from apps.leads.models import Lead, LeadSource
        tg = LeadSource.objects.get(slug="telegram")
        ig = LeadSource.objects.get(slug="instagram")
        # instagram gets a lead, then is deactivated -> it has no card
        Lead.objects.create(full_name="I", phone="+998901234500", source=ig)
        ig.is_active = False
        ig.save()
        Lead.objects.create(full_name="A", phone="+998901234567", source=tg)
        Lead.objects.create(full_name="B", phone="+998901234568", source=tg)
        data = self._data("all")
        names = [c["name"] for c in data["source_cards"]]
        self.assertNotIn("Instagram", names)  # inactive -> no card
        # 2 telegram of 2 active-source leads = 100%, NOT 2/3 = 67%
        self.assertEqual(self._card(data, "Telegram")["percent"], 100)


class DashboardDataTests(TestCase):
    """build_dashboard_data + _series bucketing across periods."""

    def _visit(self, when=None, **kw):
        from apps.analytics.models import VisitLog
        kw.setdefault("visitor_id", "v%d" % (VisitLog.objects.count() + 1))
        v = VisitLog.objects.create(path="/", device_type="mobile", **kw)
        if when is not None:
            VisitLog.objects.filter(pk=v.pk).update(created_at=when)  # bypass auto_now_add
        return v

    def _data(self, period):
        from apps.analytics.dashboard import build_dashboard_data
        return build_dashboard_data(RequestFactory().get("/admin/"), period)

    def test_clean_period_defaults_and_aliases(self):
        from apps.analytics.dashboard import clean_period
        self.assertEqual(clean_period("bogus"), "30d")
        self.assertEqual(clean_period(None), "30d")
        self.assertEqual(clean_period("7d"), "7d")
        # Old calendar keys keep working (bookmarks, saved sessions).
        self.assertEqual(clean_period("year"), "12mo")
        self.assertEqual(clean_period("today"), "24h")

    def test_24h_series_is_hourly(self):
        import json
        from django.utils import timezone
        now = timezone.now()
        self._visit(when=now)
        cfg = json.loads(self._data("24h")["visits_chart"])
        self.assertEqual(len(cfg["labels"]), 25)  # 24 rolling hours + current
        self.assertEqual([d["key"] for d in cfg["datasets"]], ["users", "views"])
        self.assertEqual(sum(cfg["datasets"][1]["data"]), 1)

    def test_7d_series_is_daily(self):
        import json
        cfg = json.loads(self._data("7d")["visits_chart"])
        self.assertEqual(len(cfg["labels"]), 8)  # 7 rolling days + today

    def test_12mo_series_is_monthly(self):
        import json
        cfg = json.loads(self._data("12mo")["visits_chart"])
        self.assertEqual(len(cfg["labels"]), 13)

    def test_month_window_excludes_older_visits(self):
        from django.utils import timezone
        from datetime import timedelta
        now = timezone.now()
        self._visit(when=now)                       # in window
        self._visit(when=now - timedelta(days=40))  # outside 30 days
        stats = {s["key"]: s["value"] for s in self._data("30d")["stats"]}
        self.assertEqual(stats["views"], 1)

    def test_week_series_excludes_out_of_window_visits(self):
        import json
        from django.utils import timezone
        from datetime import timedelta
        now = timezone.now()
        self._visit(when=now)                        # in window
        self._visit(when=now - timedelta(days=20))   # older than 7 days
        cfg = json.loads(self._data("7d")["visits_chart"])
        self.assertEqual(sum(cfg["datasets"][1]["data"]), 1)  # only the in-window visit

    def test_kpi_reconciles_with_chart_sum_for_week(self):
        import json
        from datetime import timedelta

        from django.utils import timezone
        now = timezone.now()
        self._visit(when=now)                       # today (in window)
        self._visit(when=now - timedelta(days=3))   # in week window
        self._visit(when=now - timedelta(days=10))  # outside week window
        data = self._data("7d")
        views = {s["key"]: s["value"] for s in data["stats"]}["views"]
        chart_sum = sum(json.loads(data["visits_chart"])["datasets"][1]["data"])
        self.assertEqual(views, 2)          # only the two in-window visits
        self.assertEqual(views, chart_sum)  # headline == sum of the line

    def test_source_cards_period_and_default(self):
        from apps.leads.models import Lead, LeadSource
        tg = LeadSource.objects.get(slug="telegram")
        Lead.objects.create(full_name="A", phone="+998901234567", source=tg)
        data = self._data("all")
        self.assertEqual(data["dash_period"], "all")
        tg_card = next(c for c in data["source_cards"] if c["name"] == "Telegram")
        self.assertEqual(tg_card["count"], 1)
        self.assertEqual(tg_card["percent"], 100)
        self.assertIn("source=telegram", tg_card["link"])


class SessionMetricsTests(TestCase):
    """users / bounce rate / visit duration are derived from visitor_id runs."""

    def _visit(self, visitor, minutes_ago, **kw):
        from datetime import timedelta

        from django.utils import timezone
        row = VisitLog.objects.create(
            path=kw.pop("path", "/uz/"), method="GET", visitor_id=visitor, **kw)
        VisitLog.objects.filter(pk=row.pk).update(
            created_at=timezone.now() - timedelta(minutes=minutes_ago))
        return row

    def _stats(self, period="30d"):
        from apps.analytics.dashboard import build_dashboard_data
        data = build_dashboard_data(RequestFactory().get("/admin/"), period)
        return {s["key"]: s["value"] for s in data["stats"]}

    def test_users_counts_distinct_visitors_not_rows(self):
        self._visit("a", 10)
        self._visit("a", 9)
        self._visit("b", 8)
        stats = self._stats()
        self.assertEqual(stats["users"], 2)
        self.assertEqual(stats["views"], 3)

    def test_single_page_visit_is_a_bounce(self):
        self._visit("a", 10)                      # 1 page -> bounce
        self._visit("b", 10)
        self._visit("b", 8)                       # 2 pages -> not a bounce
        self.assertEqual(self._stats()["bounce"], "50%")

    def test_visit_duration_is_first_to_last_hit(self):
        self._visit("a", 10)
        self._visit("a", 6)                       # 4 minutes later
        self.assertEqual(self._stats()["duration"], "4m 0s")

    def test_gap_over_30_minutes_starts_a_new_session(self):
        # One visitor, two hits 2 hours apart: two sessions, both bounces,
        # zero duration each — not a single 2-hour visit.
        self._visit("a", 150)
        self._visit("a", 20)
        stats = self._stats()
        self.assertEqual(stats["users"], 1)
        self.assertEqual(stats["bounce"], "100%")
        self.assertEqual(stats["duration"], "0s")


class SourceLabelTests(TestCase):
    """Referrers collapse to a host; own domain and empty both mean "direct"."""

    def test_labels(self):
        from apps.analytics.dashboard import _source_label
        hosts = {"tagayev.uz"}
        self.assertEqual(_source_label("", hosts), "")
        self.assertEqual(_source_label("https://tagayev.uz/uz/", hosts), "")
        self.assertEqual(_source_label("https://www.google.com/search?q=x", hosts),
                         "google.com")
        self.assertEqual(_source_label("https://t.me/chan", hosts), "t.me")

    def test_internal_referrers_are_not_a_source(self):
        VisitLog.objects.create(path="/uz/", method="GET", visitor_id="a",
                                referrer="http://testserver/uz/kurslar/")
        from apps.analytics.dashboard import build_dashboard_data
        data = build_dashboard_data(RequestFactory().get("/admin/"), "30d")
        # testserver is our own host -> counted as direct, not as a referrer.
        self.assertEqual([r["key"] for r in data["top_sources"]], [""])


class TechIconTests(TestCase):
    """Every browser/OS row gets a mark — unmatched ones fall back to a globe."""

    def test_slugs(self):
        from apps.common.tech_icons import TECH_ICONS, browser_slug, os_slug
        self.assertEqual(browser_slug("Chrome Mobile WebView"), "googlechrome")
        self.assertEqual(browser_slug("Mobile Safari"), "safari")
        self.assertEqual(browser_slug("Yandex Browser"), "globe")
        self.assertEqual(os_slug("Mac OS X"), "apple")
        self.assertEqual(os_slug("Windows"), "windows")
        self.assertEqual(os_slug(""), "globe")
        for slug in ("googlechrome", "safari", "apple", "windows", "globe"):
            self.assertIn(slug, TECH_ICONS)

    def test_tag_renders_svg(self):
        from apps.common.templatetags.ui import tech_icon
        self.assertIn("<svg", tech_icon("googlechrome"))
        # Unknown slug still renders (the globe), never an empty string.
        self.assertIn("<svg", tech_icon("no-such-brand"))


@override_settings(STORAGES=_STATIC_STORAGE)
class DashboardIndexRenderTests(TestCase):
    """The admin index renders the new filter bar + content for a period."""

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="dash_admin", password="pass12345", email="d@test.com")
        self.client.force_login(self.admin)

    def test_index_has_filter_and_content(self):
        resp = self.client.get(reverse("admin:index") + "?period=7d", follow=True)
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn("data-dash-range", html)          # range picker present
        self.assertIn('id="dashboard-content"', html)   # swappable wrapper
        self.assertIn("data-dash-chart", html)          # our own chart canvas
        self.assertIn("data-world-map", html)           # locations choropleth
        self.assertIn('data-period="7d"', html)


@override_settings(STORAGES=_STATIC_STORAGE)
class DashboardDataViewTests(TestCase):
    """The AJAX endpoint is staff-only and returns the content partial."""

    def _url(self):
        return reverse("admin_dashboard_data")

    def test_anonymous_is_redirected(self):
        resp = self.client.get(self._url())
        self.assertIn(resp.status_code, (302, 403))

    def test_staff_gets_partial_html(self):
        admin = User.objects.create_superuser(
            username="ajax_admin", password="pass12345", email="a@test.com")
        self.client.force_login(admin)
        resp = self.client.get(self._url() + "?period=week")
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn("data-dash-chart", html)
        self.assertNotIn("data-dash-range", html)  # partial only, no range picker

    def test_invalid_period_defaults_to_30d(self):
        admin = User.objects.create_superuser(
            username="ajax_admin2", password="pass12345", email="a2@test.com")
        self.client.force_login(admin)
        resp = self.client.get(self._url() + "?period=bogus")
        self.assertEqual(resp.status_code, 200)
