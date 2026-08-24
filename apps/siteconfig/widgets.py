from django import forms
from django.templatetags.static import static
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


class LeafletLocationWidget(forms.TextInput):
    """Renders an interactive Leaflet map + address search above the latitude
    input. Clicking/dragging the marker (or searching) fills #id_latitude and
    #id_longitude automatically. No API key required (OpenStreetMap).

    Leaflet is self-hosted under static/vendor/leaflet/ (no third-party CDN in
    the authenticated admin, and no SRI to maintain); the marker image URLs are
    resolved with static() so they stay correct under manifest hashing."""

    class Media:
        css = {"all": (
            "vendor/leaflet/leaflet.css",
            "css/admin_map_picker.css",
        )}
        js = (
            "vendor/leaflet/leaflet.js",
            "js/admin_map_picker.js",
        )

    def render(self, name, value, attrs=None, renderer=None):
        input_html = super().render(name, value, attrs, renderer)
        search_ph = _("Manzilni qidiring (masalan: Chilonzor, Toshkent)…")
        find_label = _("Qidirish")
        hint = _("Xaritani bosing yoki belgini suring — koordinatalar avtomatik to‘ladi.")
        icon = static("vendor/leaflet/images/marker-icon.png")
        icon_2x = static("vendor/leaflet/images/marker-icon-2x.png")
        shadow = static("vendor/leaflet/images/marker-shadow.png")
        map_html = f"""
        <div class="hs-map-picker">
          <div class="hs-map-search">
            <input type="text" id="hs-map-search-input" placeholder="{search_ph}" autocomplete="off">
            <button type="button" id="hs-map-search-btn">{find_label}</button>
          </div>
          <div id="hs-map" data-icon="{icon}" data-icon-2x="{icon_2x}" data-shadow="{shadow}"></div>
          <p class="hs-map-hint">{hint}</p>
        </div>
        """
        return mark_safe(map_html + input_html)


class BrandColorWidget(forms.TextInput):
    """Hex text input paired with a native <input type="color"> swatch and a
    "Standart" button.

    The stored value must stay *blank* to mean "use the built-in palette", and a
    colour input can never post an empty value — so the text box remains the
    real field and the swatch is a sidecar that only writes into it."""

    class Media:
        css = {"all": ("css/admin_color_picker.css",)}
        js = ("js/admin_color_picker.js",)

    # Ready-made pairs, rendered once (by whichever field passes presets=True)
    # as a click-to-apply row. Each fills BOTH inputs, so a palette is one click.
    PRESETS = (
        (_("Binafsha + tilla"), "#7a45e0", "#c9a961"),
        (_("Zumrad + mis"), "#0f766e", "#b45309"),
        (_("Siyoh + latun"), "#1e3a8a", "#b08d57"),
        (_("Bordo + tilla"), "#8c1d3f", "#c9a961"),
        (_("Oʻrmon + qahrabo"), "#14532d", "#b8912f"),
        (_("Grafit + moviy"), "#334155", "#38bdf8"),
    )

    def __init__(self, fallback="#7a45e0", presets=False, attrs=None):
        self.fallback = fallback
        self.presets = presets
        super().__init__(attrs={"placeholder": fallback, **(attrs or {})})

    def _preset_row(self):
        if not self.presets:
            return ""
        chips = "".join(
            f'<button type="button" class="hs-preset" data-p="{p}" data-a="{a}" title="{label}">'
            f'<span style="background:{p}"></span><span style="background:{a}"></span>'
            f"<em>{label}</em></button>"
            for label, p, a in self.PRESETS
        )
        return f'<div class="hs-presets">{chips}</div>'

    def render(self, name, value, attrs=None, renderer=None):
        text = super().render(name, value, attrs, renderer)
        swatch = value or self.fallback
        return mark_safe(
            f"{self._preset_row()}"
            f'<div class="hs-color" data-fallback="{self.fallback}">'
            f'<input type="color" class="hs-color-swatch" value="{swatch}" '
            f'aria-label="{_("Rang tanlash")}" tabindex="-1">'
            f"{text}"
            f'<button type="button" class="hs-color-reset">{_("Standart")}</button>'
            f"</div>"
            f'<div class="hs-shades" aria-hidden="true"></div>'
        )
