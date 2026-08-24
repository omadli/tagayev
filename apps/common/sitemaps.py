"""Sitemaps for Tagayev Methods (i18n alternates + x-default, https protocol).

The Sites framework is not installed; Django's Sitemap falls back to the
request host for the domain, so generated URLs match the live host.
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.courses.models import Course
from apps.news.models import NewsPost
from apps.teachers.models import Teacher


class StaticViewSitemap(Sitemap):
    """Home + key landing/list pages."""

    i18n = True
    alternates = True
    x_default = True
    protocol = "https"
    changefreq = "weekly"

    def items(self):
        return ["home", "news:list", "gallery:list", "certificates:list"]

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return 1.0 if item == "home" else 0.7


class ModelSitemap(Sitemap):
    """Shared config for per-object sitemaps (URL from get_absolute_url)."""

    i18n = True
    alternates = True
    x_default = True
    protocol = "https"

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


class CourseSitemap(ModelSitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Course.objects.filter(is_active=True)


class TeacherSitemap(ModelSitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return Teacher.objects.filter(is_active=True)


class NewsSitemap(ModelSitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return NewsPost.objects.filter(is_published=True)


sitemaps = {
    "static": StaticViewSitemap,
    "courses": CourseSitemap,
    "teachers": TeacherSitemap,
    "news": NewsSitemap,
}
