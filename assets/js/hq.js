(function () {
  var path = location.pathname || "";
  var prefix = /\/articles\//.test(path) ? "../" : "";

  var tools = [
    { href: "lance-builder.html", title: "Lance Builder", kicker: "Force planner" },
    { href: "game-tracker.html", title: "Game Tracker", kicker: "Your force" },
    { href: "opfor-command.html", title: "OpFor Command", kicker: "Their force" },
    { href: "campaign.html", title: "Campaign Tracker", kicker: "Alpha Strike" },
    { href: "paint-tool.html", title: "Paint Tool", kicker: "Hobby" }
  ];

  var links = [
    { href: "index.html#getting-started", label: "Guides" },
    { href: "index.html#lore", label: "Lore" },
    { href: "index.html#painting", label: "Hobby" },
    { href: "about.html", label: "About" }
  ];

  var MECHS = [
    {
      href: "marauder.html",
      name: "Marauder",
      img: "assets/images/marauder-schematic.png",
      alt: "Line schematic of a Marauder",
      kicker: "75 tons \u00b7 Inner Sphere",
      blurb: "The most recognisable heavy in the game, and the one most people play wrong. Every variant ranked, the heat maths behind the 3R, and how to kill one.",
      meta: "36 variants \u00b7 S-tier \u00b7 MAD-3R"
    },
    {
      href: "warhammer.html",
      name: "Warhammer",
      img: "assets/images/warhammer-schematic.png",
      alt: "Line schematic of a Warhammer",
      kicker: "70 tons \u00b7 Inner Sphere",
      blurb: "Designed in 2515 and still in service in the ilClan era. Every variant ranked, the heat maths, and why nobody ever managed to replace the original.",
      meta: "31 variants \u00b7 WHM-6R"
    }
  ];

  var logoSvg =
    '<svg class="logo-mark" viewBox="0 0 32 32" aria-hidden="true">' +
    '<rect width="32" height="32" rx="2" fill="#0a0a0b"/>' +
    '<path d="M7 7h5v1.6H8.6V12H7V7zm13 0h5v5h-1.6V8.6H20V7zM7 20h1.6v3.4H12V25H7v-5zm16.4 0H25v5h-5v-1.6h3.4V20z" fill="#ff8c00"/>' +
    '<rect x="14.2" y="14.2" width="3.6" height="3.6" fill="#ff8c00"/>' +
    "</svg>";

  function buildHeader() {
    var header = document.querySelector("header");
    if (!header) return;
    var toolItems = tools.map(function (t) {
      return '<a href="' + prefix + t.href + '"><span>' + t.title + "</span><small>" + t.kicker + "</small></a>";
    }).join("");
    var navLinks = links.map(function (l) {
      return '<li><a href="' + prefix + l.href + '">' + l.label + "</a></li>";
    }).join("");
    header.classList.add("hq-built");
    header.innerHTML =
      '<div class="header-content">' +
      '<a href="' + prefix + 'index.html" class="logo" aria-label="BattleTech HQ home">' +
      logoSvg +
      '<span class="logo-stack"><small>BATTLETECH</small><strong>HQ</strong></span></a>' +
      '<button class="nav-toggle" type="button" aria-label="Open menu" aria-expanded="false">MENU</button>' +
      '<nav class="hq-nav" aria-label="Primary"><ul>' +
      '<li class="hq-drop"><a href="' + prefix + 'lance-builder.html">Tools</a>' +
      '<div class="hq-drop-panel"><div class="hq-drop-inner">' + toolItems + "</div></div></li>" +
      navLinks +
      "</ul></nav>" +
      '<a class="hq-cta" href="' + prefix + 'lance-builder.html">Lance Builder</a></div>';
    var toggle = header.querySelector(".nav-toggle");
    var ul = header.querySelector("nav ul");
    if (toggle && ul) {
      toggle.addEventListener("click", function () {
        var open = ul.classList.toggle("open");
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
        toggle.textContent = open ? "CLOSE" : "MENU";
      });
    }
  }

  function norm(s) {
    return (s || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
  }

  function initMechRotate() {
    var root = document.getElementById("hq-mech");
    if (!root || !MECHS.length) return;
    var img = document.getElementById("hq-mech-img");
    var kicker = document.getElementById("hq-mech-kicker");
    var heading = document.getElementById("hq-mech-heading");
    var name = document.getElementById("hq-mech-name");
    var blurb = document.getElementById("hq-mech-blurb");
    var meta = document.getElementById("hq-mech-meta");
    var search = document.getElementById("hq-mech-search");
    var results = document.getElementById("hq-mech-results");
    var index = 0;
    var timer = null;
    var active = -1;
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var rotate = MECHS.length > 1 && MECHS.length <= 8;

    function show(i) {
      index = (i + MECHS.length) % MECHS.length;
      var m = MECHS[index];
      root.href = prefix + m.href;
      if (img) { img.src = prefix + m.img; img.alt = m.alt; }
      if (heading) heading.textContent = m.name;
      if (kicker) kicker.textContent = m.kicker;
      if (name) name.textContent = m.name;
      if (blurb) blurb.textContent = m.blurb;
      if (meta) meta.textContent = m.meta;
    }

    function stop() { if (timer) { clearInterval(timer); timer = null; } }
    function start() {
      stop();
      if (reduce || !rotate) return;
      timer = setInterval(function () { show(index + 1); }, 8000);
    }

    function go(m) {
      location.href = prefix + m.href;
    }

    function hideResults() {
      if (!results) return;
      results.hidden = true;
      results.innerHTML = "";
      active = -1;
    }

    function matches(q) {
      var n = norm(q);
      if (!n) return [];
      return MECHS.filter(function (m) {
        return norm(m.name).indexOf(n) !== -1;
      }).slice(0, 8);
    }

    function renderResults(list) {
      if (!results) return;
      if (!list.length) {
        results.innerHTML = '<li class="hq-mech-empty">No guide yet. Try All Guides.</li>';
        results.hidden = false;
        active = -1;
        return;
      }
      results.innerHTML = list.map(function (m, i) {
        return '<li><button type="button" data-i="' + MECHS.indexOf(m) + '" class="' + (i === 0 ? "is-active" : "") + '">' + m.name + "<small>" + m.kicker + "</small></button></li>";
      }).join("");
      results.hidden = false;
      active = 0;
    }

    if (search && results) {
      search.addEventListener("input", function () {
        var q = search.value;
        if (!q.trim()) { hideResults(); return; }
        renderResults(matches(q));
      });
      search.addEventListener("keydown", function (ev) {
        var buttons = results.querySelectorAll("button");
        if (ev.key === "Escape") { hideResults(); search.blur(); return; }
        if (ev.key === "ArrowDown" && buttons.length) {
          ev.preventDefault();
          active = Math.min(active + 1, buttons.length - 1);
          buttons.forEach(function (b, i) { b.classList.toggle("is-active", i === active); });
        }
        if (ev.key === "ArrowUp" && buttons.length) {
          ev.preventDefault();
          active = Math.max(active - 1, 0);
          buttons.forEach(function (b, i) { b.classList.toggle("is-active", i === active); });
        }
        if (ev.key === "Enter") {
          ev.preventDefault();
          var list = matches(search.value);
          if (!list.length) return;
          var pick = buttons.length && active >= 0 ? MECHS[parseInt(buttons[active].getAttribute("data-i"), 10)] : list[0];
          if (pick) go(pick);
        }
      });
      results.addEventListener("click", function (ev) {
        var btn = ev.target.closest("button");
        if (!btn) return;
        var i = parseInt(btn.getAttribute("data-i"), 10);
        if (!isNaN(i) && MECHS[i]) go(MECHS[i]);
      });
      document.addEventListener("click", function (ev) {
        if (!ev.target.closest(".hq-mech-find")) hideResults();
      });
    }

    root.addEventListener("mouseenter", stop);
    root.addEventListener("mouseleave", start);
    root.addEventListener("focusin", stop);
    root.addEventListener("focusout", start);

    if (MECHS.length > 8) show(Math.floor(Math.random() * MECHS.length));
    else show(0);
    start();
  }

  function initMechCatalog() {
    var grid = document.querySelector(".articles-grid");
    if (!grid) return;
    if (document.getElementById("hq-mech-catalog-search")) return;
    var wrap = document.createElement("div");
    wrap.className = "hq-mech-find hq-mech-catalog";
    wrap.innerHTML = '<label class="hq-kicker" for="hq-mech-catalog-search">Find a chassis</label><input id="hq-mech-catalog-search" type="search" placeholder="Atlas, Timber Wolf, Locust…" autocomplete="off">';
    grid.parentNode.insertBefore(wrap, grid);
    var input = wrap.querySelector("input");
    var cards = grid.querySelectorAll(".article-card");
    input.addEventListener("input", function () {
      var q = norm(input.value);
      var shown = 0;
      cards.forEach(function (card) {
        var h3 = card.querySelector("h3");
        var hit = !q || norm(h3 ? h3.textContent : "").indexOf(q) !== -1;
        card.style.display = hit ? "" : "none";
        if (hit) shown++;
      });
    });
  }

  function boot() {
    buildHeader();
    initMechRotate();
    initMechCatalog();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
