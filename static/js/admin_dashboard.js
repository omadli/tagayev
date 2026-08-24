// Admin dashboard: Chart.js line charts, the time-range picker, the segmented
// switches (Locations map/list, Browsers/Devices/OS) and the world choropleth.
// Chart.js is bundled by Unfold and available as the global `Chart`; the map
// path data comes from static/js/world_map.js (loaded only on this page).
//
// Motion: every animation here is skipped when the OS asks for reduced motion
// (`reduced()`), and none of them gate correctness — the dashboard is fully
// readable the instant the HTML lands.
(function () {
  "use strict";

  var SVG_NS = "http://www.w3.org/2000/svg";
  var LIVE_REFRESH_MS = 30000;
  var EASE = function (t) { return 1 - Math.pow(1 - t, 3); };  // easeOutCubic

  var motionQuery = window.matchMedia
    ? window.matchMedia("(prefers-reduced-motion: reduce)") : null;
  function reduced() { return !!(motionQuery && motionQuery.matches); }

  /** rAF tween from 0..1; `step(t)` gets the eased progress.
   *  Snaps straight to the end when motion is off or the tab is in the
   *  background — a throttled rAF would otherwise leave a half-counted number
   *  or a half-panned map on screen when the user comes back. */
  function tween(duration, step, done) {
    if (reduced() || document.hidden) { step(1); if (done) done(); return; }
    var start = null;
    function frame(now) {
      if (start === null) start = now;
      var t = Math.min(1, (now - start) / duration);
      step(EASE(t));
      if (t < 1) requestAnimationFrame(frame);
      else if (done) done();
    }
    requestAnimationFrame(frame);
  }

  function hexToRgb(hex) {
    var h = hex.replace("#", "");
    if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16),
            parseInt(h.slice(4, 6), 16)];
  }

  function rgba(hex, alpha) {
    var c = hexToRgb(hex);
    return "rgba(" + c[0] + "," + c[1] + "," + c[2] + "," + alpha + ")";
  }

  // "2026-08-01" -> "01.08.2026", matching the server-rendered custom label.
  function dmy(iso) {
    var p = String(iso).split("-");
    return p.length === 3 ? p[2] + "." + p[1] + "." + p[0] : iso;
  }

  function cssVar(name, fallback) {
    var v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  }

  // --- Country names / flags -------------------------------------------------
  // Intl.DisplayNames localizes ~250 country names with no data of our own —
  // but Chrome's ICU has no uz territory data and silently answers in English,
  // so for uz we use the CLDR table shipped in world_map.js instead.
  var pageLang = (document.documentElement.lang || "uz").slice(0, 2);
  var regionNames = null;
  if (pageLang !== "uz") {
    try {
      regionNames = new Intl.DisplayNames([pageLang], { type: "region" });
    } catch (e) { /* older browser: the server-rendered English name stays */ }
  }

  function countryName(code, fallback) {
    if (!code) return fallback || "";
    if (pageLang === "uz" && window.COUNTRY_NAMES_UZ) {
      var uz = window.COUNTRY_NAMES_UZ[code];
      if (uz) return uz;
    }
    try {
      var name = regionNames && regionNames.of(code);
      if (name && name !== code) return name;
    } catch (e) { /* not a valid region code */ }
    return fallback || code;
  }

  // Flag emoji render as blank/letters on Windows, so flags come from a sprite
  // sheet (static/img/flags.png). The stylesheet holds the image; here we only
  // pick the row.
  function paintFlag(el) {
    var sprite = window.FLAG_SPRITE;
    var row = sprite && sprite.index[el.getAttribute("data-flag")];
    // Hide, never remove: this can run before world_map.js has executed (the
    // theme observer below fires during Alpine's init, ahead of the deferred
    // scripts), and the DOMContentLoaded pass must still find the node.
    el.style.display = row === undefined ? "none" : "";
    if (row !== undefined) {
      el.style.backgroundPosition = "0 -" + (row * 15) + "px";
    }
  }

  function localizeCountries(root) {
    root.querySelectorAll("[data-country]").forEach(function (el) {
      var code = el.getAttribute("data-country");
      // "" (unresolved) and ZZ (local network) are our own labels, already
      // translated server-side — never hand them to a region-name lookup.
      if (!code || code === "ZZ") return;
      el.textContent = countryName(code, el.textContent.trim());
    });
    root.querySelectorAll("[data-flag]").forEach(paintFlag);
  }

  // --- Charts ----------------------------------------------------------------
  window.__dashCharts = window.__dashCharts || {};

  function destroyCharts() {
    Object.keys(window.__dashCharts).forEach(function (k) {
      try { window.__dashCharts[k].destroy(); } catch (e) {}
    });
    window.__dashCharts = {};
  }

  // Vertical guide under the hovered point — the thing that makes a line chart
  // readable when two series overlap.
  var crosshair = {
    id: "dashCrosshair",
    afterDatasetsDraw: function (chart) {
      var active = chart.tooltip && chart.tooltip.getActiveElements
        ? chart.tooltip.getActiveElements() : null;
      if (!active || !active.length || !chart.chartArea) return;
      var ctx = chart.ctx;
      var x = active[0].element.x;
      ctx.save();
      ctx.beginPath();
      ctx.setLineDash([4, 4]);
      ctx.lineWidth = 1;
      ctx.strokeStyle = chart.$guide || "rgba(100,116,139,.45)";
      ctx.moveTo(x, chart.chartArea.top);
      ctx.lineTo(x, chart.chartArea.bottom);
      ctx.stroke();
      ctx.restore();
    },
  };

  /** Vertical fade under the line, rebuilt whenever the chart area changes. */
  function areaFill(color) {
    return function (ctx) {
      var area = ctx.chart.chartArea;
      if (!area) return rgba(color, 0.18);
      var gradient = ctx.chart.ctx.createLinearGradient(0, area.top, 0, area.bottom);
      gradient.addColorStop(0, rgba(color, 0.34));
      gradient.addColorStop(1, rgba(color, 0.01));
      return gradient;
    };
  }

  function buildChart(canvas, cfg) {
    if (typeof Chart === "undefined") return null;
    var tick = cssVar("--dash-muted", "#6b7280");
    var ink = cssVar("--dash-ink", "#111827");
    var card = cssVar("--dash-card", "#ffffff");
    var slow = reduced() ? 0 : 900;
    var chart = new Chart(canvas.getContext("2d"), {
      type: "line",
      data: {
        labels: cfg.labels || [],
        datasets: (cfg.datasets || []).map(function (ds) {
          return {
            label: ds.label || "",
            data: ds.data || [],
            borderColor: ds.color,
            backgroundColor: areaFill(ds.color),
            pointBackgroundColor: ds.color,
            pointBorderColor: card,
            pointBorderWidth: 2,
            fill: true, tension: 0.35, borderWidth: 2,
            pointRadius: 0, pointHoverRadius: 5, pointHitRadius: 12,
          };
        }),
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        // The line sweeps in left-to-right; the delay is capped so a 400-bucket
        // range does not take ten seconds to draw.
        animation: {
          duration: slow,
          easing: "easeOutQuart",
          delay: function (ctx) {
            if (!slow || ctx.type !== "data" || ctx.mode !== "default") return 0;
            return Math.min(ctx.dataIndex, 40) * 12;
          },
        },
        animations: { colors: false },
        transitions: {
          active: { animation: { duration: reduced() ? 0 : 160 } },
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: ink, titleColor: card, bodyColor: card,
            padding: 10, cornerRadius: 8, boxPadding: 4,
            displayColors: true, usePointStyle: true,
            animation: { duration: reduced() ? 0 : 140 },
          },
        },
        scales: {
          y: {
            beginAtZero: true, border: { display: false },
            grid: { color: "rgba(100,116,139,.18)" },
            ticks: { color: tick, precision: 0, maxTicksLimit: 6 },
          },
          x: {
            grid: { display: false }, border: { display: false },
            ticks: { color: tick, maxRotation: 0, autoSkipPadding: 24 },
          },
        },
      },
      plugins: [crosshair],
    });
    chart.$guide = rgba(tick.charAt(0) === "#" ? tick : "#6b7280", 0.5);
    chart.$keys = (cfg.datasets || []).map(function (ds) { return ds.key; });
    return chart;
  }

  function initCharts(root) {
    destroyCharts();
    (root || document).querySelectorAll("[data-dash-chart]").forEach(function (canvas) {
      var cfg;
      try { cfg = JSON.parse(canvas.getAttribute("data-chart")); } catch (e) { return; }
      var chart = buildChart(canvas, cfg);
      if (chart) window.__dashCharts[canvas.getAttribute("data-dash-chart")] = chart;
    });
  }

  // Stat tiles double as the chart legend: clicking one hides/shows its series.
  function bindSeriesToggles(root) {
    root.querySelectorAll("[data-series-toggle]").forEach(function (tile) {
      tile.addEventListener("click", function () {
        var chart = window.__dashCharts.visits;
        if (!chart) return;
        var index = (chart.$keys || []).indexOf(tile.getAttribute("data-series-toggle"));
        if (index < 0) return;
        var visible = chart.isDatasetVisible(index);
        chart.setDatasetVisibility(index, !visible);
        chart.update();
        tile.setAttribute("aria-pressed", String(!visible));
      });
    });
  }

  // --- Entrance motion -------------------------------------------------------
  /** Roll the headline numbers up to their rendered value. */
  function animateCounters(root) {
    if (reduced()) return;
    root.querySelectorAll(".dash-tile-value").forEach(function (el) {
      var text = el.textContent.trim();
      // Only plain counts and percentages; "4m 41s" is left alone.
      var match = /^(\d+)(%?)$/.exec(text.replace(/\s+/g, ""));
      if (!match) return;
      var target = parseInt(match[1], 10);
      if (!target) return;
      tween(700, function (t) {
        el.textContent = Math.round(target * t) + match[2];
      }, function () { el.textContent = text; });
    });
  }

  /** Grow the row bars from zero, staggered down the list. */
  function animateBars(root) {
    if (reduced()) return;
    var bars = [];
    root.querySelectorAll(".dash-row-bar").forEach(function (bar) {
      if (bar.dataset.grown === "1" || !bar.offsetParent) return;   // skip hidden panes
      bars.push([bar, bar.style.width]);
      bar.dataset.grown = "1";
      bar.style.transition = "none";
      bar.style.width = "0%";
    });
    if (!bars.length) return;
    void root.offsetWidth;                       // one reflow for the whole batch
    bars.forEach(function (pair, i) {
      pair[0].style.transition = "";
      pair[0].style.transitionDelay = Math.min(i, 20) * 25 + "ms";
      pair[0].style.width = pair[1];
    });
  }

  /** Fade+lift the cards in, one after another, after a range swap. */
  function animateCards(root) {
    if (reduced()) return;
    Array.prototype.forEach.call(root.children, function (el, i) {
      el.style.animationDelay = Math.min(i, 8) * 45 + "ms";
      el.classList.remove("dash-enter");
      void el.offsetWidth;
      el.classList.add("dash-enter");
    });
  }

  // --- Segmented panes (Locations map/list, Browsers/Devices/OS) -------------
  function bindPanes(root) {
    root.querySelectorAll("[data-pane-group]").forEach(function (group) {
      group.querySelectorAll("[data-pane-btn]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          var name = btn.getAttribute("data-pane-btn");
          group.querySelectorAll("[data-pane-btn]").forEach(function (other) {
            other.setAttribute("aria-selected",
              String(other.getAttribute("data-pane-btn") === name));
          });
          group.querySelectorAll("[data-pane]").forEach(function (pane) {
            pane.hidden = pane.getAttribute("data-pane") !== name;
          });
          // Bars in a pane that was hidden never got their entrance; give it now.
          var shown = group.querySelector('[data-pane="' + name + '"]');
          if (shown) animateBars(shown);
        });
      });
    });
  }

  // --- World map choropleth --------------------------------------------------
  function renderMaps(root) {
    root.querySelectorAll("[data-world-map]").forEach(function (box) {
      if (!window.WORLD_MAP) return;
      var rows = [];
      try { rows = JSON.parse(box.getAttribute("data-countries")) || []; } catch (e) {}
      var byCode = {}, max = 0;
      rows.forEach(function (r) {
        byCode[r.code] = r;
        if (r.users > max) max = r.users;
      });

      var blue = cssVar("--dash-blue", "#7a45e0");
      var map = window.WORLD_MAP;
      var svg = document.createElementNS(SVG_NS, "svg");
      svg.setAttribute("viewBox", "0 0 " + map.w + " " + map.h);
      svg.setAttribute("class", "dash-map");
      svg.setAttribute("role", "img");

      var filled = [];
      Object.keys(map.paths).forEach(function (code) {
        var path = document.createElementNS(SVG_NS, "path");
        path.setAttribute("d", map.paths[code]);
        path.setAttribute("data-code", code);
        var row = byCode[code];
        if (row) {
          // sqrt scale so a single visit is still clearly tinted.
          var t = max ? Math.sqrt(row.users / max) : 0;
          // Inline style, not a fill attribute: presentation attributes lose
          // to the stylesheet's `fill: var(--dash-map-empty)`.
          path.$fill = rgba(blue, 0.18 + 0.82 * t);
          path.setAttribute("data-users", row.users);
          var title = document.createElementNS(SVG_NS, "title");
          title.textContent = countryName(code, row.name) + " — " + row.users;
          path.appendChild(title);
          filled.push(path);
        }
        svg.appendChild(path);
      });

      var tip = document.createElement("div");
      tip.className = "dash-tip";
      box.textContent = "";
      box.appendChild(svg);
      box.appendChild(tip);

      // Ink the countries in on the next frame, brightest first — the map
      // "develops" instead of appearing fully painted.
      if (reduced()) {
        filled.forEach(function (p) { p.style.fill = p.$fill; });
      } else {
        filled.sort(function (a, b) {
          return b.getAttribute("data-users") - a.getAttribute("data-users");
        });
        requestAnimationFrame(function () {
          filled.forEach(function (p, i) {
            p.style.transitionDelay = Math.min(i, 24) * 22 + "ms";
            p.style.fill = p.$fill;
          });
        });
      }

      function show(target, event) {
        var code = target.getAttribute("data-code");
        var row = byCode[code];
        if (!row) return hide();
        var rect = box.getBoundingClientRect();
        tip.innerHTML = "";
        var name = document.createElement("b");
        name.textContent = countryName(code, row.name);
        tip.appendChild(name);
        tip.appendChild(document.createTextNode(" — " + row.users));
        tip.classList.add("is-on");
        tip.style.left = (event.clientX - rect.left) + "px";
        tip.style.top = (event.clientY - rect.top) + "px";
        svg.querySelectorAll(".is-active").forEach(function (p) {
          p.classList.remove("is-active");
        });
        target.classList.add("is-active");
      }

      function hide() {
        tip.classList.remove("is-on");
        svg.querySelectorAll(".is-active").forEach(function (p) {
          p.classList.remove("is-active");
        });
      }

      // --- zoom / pan --------------------------------------------------
      // The viewBox is the whole camera: zooming shrinks it around a point,
      // panning slides it. Everything stays crisp because it is still SVG.
      var view = { x: 0, y: 0, w: map.w, h: map.h };
      var MIN_W = map.w / 20;               // 20x is as close as it gets
      var drag = null;
      // Token for the running fly-to tween. Bumping it cancels that tween
      // instead of latching a boolean — a rAF throttled by a background tab
      // must never leave the map permanently "busy".
      var flight = 0;

      function applyView() {
        svg.setAttribute("viewBox",
          view.x + " " + view.y + " " + view.w + " " + view.h);
      }

      function clamped(v) {
        var w = Math.min(map.w, Math.max(MIN_W, v.w));
        var h = w * map.h / map.w;
        return {
          w: w, h: h,
          x: Math.min(map.w - w, Math.max(0, v.x)),
          y: Math.min(map.h - h, Math.max(0, v.y)),
        };
      }

      // Target view for a zoom around a point given in 0..1 of the current view,
      // so whatever sits under the cursor stays under the cursor.
      function zoomTarget(factor, fx, fy) {
        var anchorX = view.x + view.w * fx;
        var anchorY = view.y + view.h * fy;
        var w = Math.min(map.w, Math.max(MIN_W, view.w / factor));
        return clamped({ x: anchorX - w * fx, y: anchorY - (w * map.h / map.w) * fy, w: w });
      }

      function flyTo(target) {
        var from = { x: view.x, y: view.y, w: view.w, h: view.h };
        var token = ++flight;
        hide();
        tween(280, function (t) {
          if (token !== flight) return;          // superseded or cancelled
          view = {
            x: from.x + (target.x - from.x) * t,
            y: from.y + (target.y - from.y) * t,
            w: from.w + (target.w - from.w) * t,
            h: from.h + (target.h - from.h) * t,
          };
          applyView();
        });
      }

      // The wheel stays instant — a tween would lag behind a fast scroll.
      svg.addEventListener("wheel", function (event) {
        event.preventDefault();
        flight++;                                // the wheel takes over any tween
        var rect = svg.getBoundingClientRect();
        view = zoomTarget(event.deltaY < 0 ? 1.2 : 1 / 1.2,
                          (event.clientX - rect.left) / rect.width,
                          (event.clientY - rect.top) / rect.height);
        applyView();
      }, { passive: false });

      // Double-click zooms in on the spot, the usual map gesture.
      svg.addEventListener("dblclick", function (event) {
        var rect = svg.getBoundingClientRect();
        flyTo(zoomTarget(2, (event.clientX - rect.left) / rect.width,
                            (event.clientY - rect.top) / rect.height));
      });

      // Drag-to-pan with a mouse only: on touch, a finger drag must still
      // scroll the page (the +/- buttons cover zooming there).
      svg.addEventListener("pointerdown", function (event) {
        if (event.pointerType !== "mouse" || event.button !== 0) return;
        flight++;                                // dragging takes over any tween
        drag = { x: event.clientX, y: event.clientY };
        svg.setPointerCapture(event.pointerId);
        svg.classList.add("is-panning");
      });

      function endDrag(event) {
        if (!drag) return;
        try { svg.releasePointerCapture(event.pointerId); } catch (e) {}
        svg.classList.remove("is-panning");
        drag = null;
      }
      svg.addEventListener("pointerup", endDrag);
      svg.addEventListener("pointercancel", endDrag);

      // pointer* covers mouse hover and a tap on touch devices in one path.
      svg.addEventListener("pointermove", function (event) {
        if (drag) {
          var rect = svg.getBoundingClientRect();
          view = clamped({
            x: view.x - (event.clientX - drag.x) * view.w / rect.width,
            y: view.y - (event.clientY - drag.y) * view.h / rect.height,
            w: view.w,
          });
          drag.x = event.clientX;
          drag.y = event.clientY;
          applyView();
          hide();
          return;
        }
        var target = event.target.closest("path[data-users]");
        if (target) show(target, event); else hide();
      });

      svg.addEventListener("pointerleave", hide);

      // The toolbar lives outside the redrawn box, so it is bound once and
      // always talks to the CURRENT svg through this handle (a theme switch
      // rebuilds the map, which would otherwise leave the buttons on a dead one).
      var outer = box.closest("[data-map-outer]");
      if (!outer) return;
      outer.__map = {
        zoom: function (factor) { flyTo(zoomTarget(factor, 0.5, 0.5)); },
        reset: function () { flyTo({ x: 0, y: 0, w: map.w, h: map.h }); },
      };
      if (outer.dataset.mapBound === "1") return;
      outer.dataset.mapBound = "1";
      outer.querySelectorAll("[data-map-zoom]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          outer.__map.zoom(parseFloat(btn.getAttribute("data-map-zoom")));
        });
      });
      outer.querySelector("[data-map-reset]").addEventListener("click", function () {
        outer.__map.reset();
      });
      outer.querySelector("[data-map-full]").addEventListener("click", function () {
        if (document.fullscreenElement) document.exitFullscreen();
        else if (outer.requestFullscreen) outer.requestFullscreen();
      });
    });
  }

  // Module scope on purpose: an AJAX range swap replaces [data-map-outer], so a
  // listener registered per map would pile up one dead closure per switch.
  document.addEventListener("fullscreenchange", function () {
    document.querySelectorAll("[data-map-full] .material-symbols-outlined")
      .forEach(function (icon) {
        icon.textContent = document.fullscreenElement ? "fullscreen_exit" : "fullscreen";
      });
  });

  // --- CRM "copy link" buttons ----------------------------------------------
  function bindCopy(root) {
    root.querySelectorAll("[data-copy-link]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var link = btn.getAttribute("data-copy-link");
        var label = btn.querySelector("[data-copy-label]");
        function flash() {
          if (!label) return;
          var prev = label.textContent;
          label.textContent = "✓";
          btn.classList.add("is-copied");
          setTimeout(function () {
            label.textContent = prev;
            btn.classList.remove("is-copied");
          }, 1500);
        }
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(link).then(flash).catch(function () {});
        } else {
          var ta = document.createElement("textarea");
          ta.value = link; document.body.appendChild(ta); ta.select();
          try { document.execCommand("copy"); } catch (e) {}
          document.body.removeChild(ta); flash();
        }
      });
    });
  }

  function bindContent(root, fresh) {
    initCharts(root);
    bindSeriesToggles(root);
    bindPanes(root);
    renderMaps(root);
    localizeCountries(root);
    bindCopy(root);
    animateCounters(root);
    animateBars(root);
    if (fresh) animateCards(root);
  }

  // --- Boot ------------------------------------------------------------------
  document.addEventListener("DOMContentLoaded", function () {
    var box = document.querySelector("[data-dash-range]");
    var content = document.getElementById("dashboard-content");
    if (!content) return;
    bindContent(content, false);
    if (!box) return;

    var url = box.getAttribute("data-dash-url");
    var menu = box.querySelector("[data-range-menu]");
    var opener = box.querySelector("[data-range-open]");
    var labelEl = box.querySelector("[data-range-label]");
    var fromInput = box.querySelector("[data-range-from]");
    var toInput = box.querySelector("[data-range-to]");
    var progress = document.querySelector("[data-dash-progress]");
    var errorBar = document.querySelector("[data-dash-error]");
    var liveTimer = null;
    var inflight = null;
    var lastRequest = null;

    // --- menu open/close + keyboard navigation ---
    function items() {
      return Array.prototype.slice.call(menu.querySelectorAll("[data-range-pick]"));
    }

    function openMenu() {
      menu.hidden = false;
      opener.setAttribute("aria-expanded", "true");
    }

    function closeMenu(refocus) {
      if (menu.hidden) return;
      menu.hidden = true;
      opener.setAttribute("aria-expanded", "false");
      if (refocus) opener.focus();
    }

    opener.addEventListener("click", function (event) {
      event.stopPropagation();
      if (menu.hidden) openMenu(); else closeMenu();
    });
    menu.addEventListener("click", function (event) { event.stopPropagation(); });
    document.addEventListener("click", function () { closeMenu(); });

    box.addEventListener("keydown", function (event) {
      if (event.key === "Escape") { closeMenu(true); return; }
      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        if (menu.hidden) openMenu();
        var list = items();
        var at = list.indexOf(document.activeElement);
        var next = event.key === "ArrowDown"
          ? (at + 1) % list.length
          : (at <= 0 ? list.length - 1 : at - 1);
        list[next].focus();
        event.preventDefault();
      } else if (event.key === "Home" || event.key === "End") {
        if (menu.hidden) return;
        var all = items();
        all[event.key === "Home" ? 0 : all.length - 1].focus();
        event.preventDefault();
      }
    });

    function markActive(period) {
      items().forEach(function (item) {
        var on = item.getAttribute("data-range-pick") === period;
        item.querySelector(".dash-check").textContent = on ? "check" : "";
        item.setAttribute("aria-current", String(on));
      });
    }

    function busy(on) {
      content.classList.toggle("is-loading", on);
      if (progress) progress.hidden = !on;
    }

    function showError(retry) {
      if (!errorBar) return;
      errorBar.hidden = false;
      errorBar.querySelector("[data-dash-retry]").onclick = function () {
        errorBar.hidden = true;
        retry();
      };
    }

    function load(period, from, to) {
      lastRequest = [period, from, to];
      box.setAttribute("data-period", period);
      box.setAttribute("data-from", from || "");
      box.setAttribute("data-to", to || "");
      markActive(period);
      if (errorBar) errorBar.hidden = true;
      busy(true);

      var query = "?period=" + encodeURIComponent(period);
      if (period === "custom") {
        query += "&from=" + encodeURIComponent(from || "") +
                 "&to=" + encodeURIComponent(to || "");
      }
      // A quick second pick must not lose the race with the first one.
      if (inflight) inflight.abort();
      inflight = typeof AbortController !== "undefined" ? new AbortController() : null;

      fetch(url + query, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
        signal: inflight ? inflight.signal : undefined,
      })
        .then(function (r) {
          if (r.redirected || !r.ok) {
            // Session gone / server error: a full reload lands on the login page.
            window.location.reload();
            return Promise.reject(new Error("reload"));
          }
          return r.text();
        })
        .then(function (html) {
          inflight = null;
          content.innerHTML = html;
          bindContent(content, true);
          var picked = menu.querySelector('[data-range-pick="' + period + '"] span:nth-child(2)');
          if (labelEl) {
            labelEl.textContent = picked
              ? picked.textContent
              : (from && to ? dmy(from) + " — " + dmy(to) : labelEl.textContent);
          }
          try {
            sessionStorage.setItem("dash_range",
              JSON.stringify({ period: period, from: from || "", to: to || "" }));
          } catch (e) {}
          history.replaceState(null, "", query);
          scheduleLive(period);
          busy(false);
        })
        .catch(function (err) {
          if (err && err.name === "AbortError") return;   // superseded, not a failure
          inflight = null;
          busy(false);
          showError(function () { load.apply(null, lastRequest); });
        });
    }

    // "Live" keeps itself fresh; every other range is a static window.
    function scheduleLive(period) {
      if (liveTimer) { clearInterval(liveTimer); liveTimer = null; }
      var dot = box.querySelector("[data-live-dot]");
      if (dot) dot.hidden = period !== "live";
      if (period !== "live") return;
      liveTimer = setInterval(function () {
        if (!document.hidden) load("live");
      }, LIVE_REFRESH_MS);
    }

    // Coming back to a backgrounded tab should show fresh numbers at once,
    // not whatever was on screen up to 30 seconds ago.
    document.addEventListener("visibilitychange", function () {
      if (!document.hidden && box.getAttribute("data-period") === "live") load("live");
    });

    items().forEach(function (item) {
      item.addEventListener("click", function () {
        closeMenu(true);
        load(item.getAttribute("data-range-pick"));
      });
    });

    box.querySelector("[data-range-apply]").addEventListener("click", function () {
      if (!fromInput.value || !toInput.value) return;
      if (fromInput.value > toInput.value) {         // ISO dates sort as strings
        var swap = fromInput.value;
        fromInput.value = toInput.value;
        toInput.value = swap;
      }
      closeMenu(true);
      load("custom", fromInput.value, toInput.value);
    });

    // Enter inside either date field applies the custom range.
    [fromInput, toInput].forEach(function (input) {
      input.addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
          event.preventDefault();
          box.querySelector("[data-range-apply]").click();
        }
      });
    });

    // The page is server-rendered for its range already; only switch if a
    // different one was chosen earlier this session.
    var initial = box.getAttribute("data-period") || "30d";
    scheduleLive(initial);
    var saved = null;
    try { saved = JSON.parse(sessionStorage.getItem("dash_range") || "null"); } catch (e) {}
    if (saved && saved.period && saved.period !== initial) {
      load(saved.period, saved.from, saved.to);
    }
  });

  // Unfold's theme toggle only flips the `dark` class on <html>; rebuild the
  // charts so axis/grid/tooltip colours follow. Other class changes are ignored.
  var wasDark = document.documentElement.classList.contains("dark");
  new MutationObserver(function () {
    var isDark = document.documentElement.classList.contains("dark");
    if (isDark === wasDark) return;
    wasDark = isDark;
    var content = document.getElementById("dashboard-content");
    if (content) { initCharts(content); renderMaps(content); localizeCountries(content); }
  }).observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
})();
