/* Brand palette field: native swatch + hex box + presets + a live shade strip.

   The text box is the actual form field — blank means "use the built-in
   palette", which is why the swatch can never be the field itself.
   The shade ladder mirrors assets/css/source.css (same percentages) so what the
   strip previews is what the site renders. */
(function () {
  "use strict";
  var HEX = /^#[0-9a-fA-F]{6}$/;
  // + = share of the brand colour mixed into white, - = into black
  var LADDER = [8, 16, 30, 50, 72, 100, -84, -68, -54, -39];

  function mix(hex, pct) {
    var n = parseInt(hex.slice(1), 16);
    var ratio = Math.abs(pct) / 100;
    var target = pct > 0 ? 255 : 0;
    var out = [16, 8, 0].map(function (shift) {
      var c = (n >> shift) & 255;
      return Math.round(c * ratio + target * (1 - ratio));
    });
    return "#" + out.map(function (c) { return ("0" + c.toString(16)).slice(-2); }).join("");
  }

  function paintStrip(strip, hex) {
    strip.textContent = "";
    if (!HEX.test(hex)) return;
    LADDER.forEach(function (pct) {
      var cell = document.createElement("span");
      cell.style.background = mix(hex, pct);
      strip.appendChild(cell);
    });
  }

  function fieldOf(box) {
    return box.querySelector('input[type="text"]');
  }

  function wire(box) {
    var swatch = box.querySelector(".hs-color-swatch");
    var text = fieldOf(box);
    var reset = box.querySelector(".hs-color-reset");
    var strip = box.parentNode.querySelector(".hs-shades");
    if (!swatch || !text) return;

    function sync(hex, writeField) {
      if (writeField) text.value = hex;
      if (HEX.test(hex)) swatch.value = hex;
      if (strip) paintStrip(strip, HEX.test(hex) ? hex : box.dataset.fallback);
    }

    swatch.addEventListener("input", function () { sync(swatch.value, true); });
    text.addEventListener("input", function () { sync(text.value.trim(), false); });
    if (reset) {
      reset.addEventListener("click", function () {
        text.value = "";
        sync(box.dataset.fallback, false);
      });
    }
    // expose for the preset row
    box.$apply = function (hex) { sync(hex, true); };
    sync(text.value.trim() || box.dataset.fallback, false);
  }

  document.addEventListener("DOMContentLoaded", function () {
    var boxes = Array.prototype.slice.call(document.querySelectorAll(".hs-color"));
    boxes.forEach(wire);
    // A preset fills both fields at once — the pair IS the palette.
    document.querySelectorAll(".hs-preset").forEach(function (chip) {
      chip.addEventListener("click", function () {
        var pair = [chip.dataset.p, chip.dataset.a];
        boxes.forEach(function (box, i) {
          if (box.$apply && pair[i]) box.$apply(pair[i]);
        });
      });
    });
  });
})();
