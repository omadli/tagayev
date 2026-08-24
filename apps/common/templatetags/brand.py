"""Brand palette for the admin chrome.

The site_context processor deliberately skips admin requests, so admin
templates have no `site_config`. This tag fetches the singleton itself —
django-solo serves it from the LocMem cache, so it costs no query.
"""
from django import template

from apps.siteconfig.models import SiteConfig

register = template.Library()


@register.inclusion_tag("admin/_brand_style.html")
def admin_brand_style():
    config = SiteConfig.get_solo()
    return {"palette": config.brand_palette, "primary": config.brand_primary}
