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

  function initMechRotate() {
    var root = document.getElementById("hq-mech");
    if (!root || !MECHS.length) return;
    var img = document.getElementById("hq-mech-img");
    var kicker = document.getElementById("hq-mech-kicker");
    var name = document.getElementById("hq-mech-name");
    var blurb = document.getElementById("hq-mech-blurb");
    var meta = document.getElementById("hq-mech-meta");
    var dots = document.getElementById("hq-mech-dots");
    var index = 0;
    var timer = null;
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    function show(i) {
      index = (i + MECHS.length) % MECHS.length;
      var m = MECHS[index];
      root.href = prefix + m.href;
      if (img) { img.src = prefix + m.img; img.alt = m.alt; }
      if (kicker) kicker.textContent = m.kicker;
      if (name) name.textContent = m.name;
      if (blurb) blurb.textContent = m.blurb;
      if (meta) meta.textContent = m.meta;
      if (dots) {
        var buttons = dots.querySelectorAll("button");
        for (var b = 0; b < buttons.length; b++) {
          buttons[b].setAttribute("aria-selected", b === index ? "true" : "false");
          buttons[b].classList.toggle("is-active", b === index);
        }
      }
    }
    function stop() { if (timer) { clearInterval(timer); timer = null; } }
    function start() {
      stop();
      if (reduce || MECHS.length < 2) return;
      timer = setInterval(function () { show(index + 1); }, 7000);
    }
    if (dots) {
      dots.innerHTML = MECHS.map(function (m, i) {
        return '<button type="button" role="tab" aria-selected="' + (i === 0 ? "true" : "false") + '" aria-label="' + m.name + '"></button>';
      }).join("");
      dots.addEventListener("click", function (ev) {
        var btn = ev.target.closest("button");
        if (!btn) return;
        var i = Array.prototype.indexOf.call(dots.querySelectorAll("button"), btn);
        if (i < 0) return;
        show(i);
        start();
      });
    }
    root.addEventListener("mouseenter", stop);
    root.addEventListener("mouseleave", start);
    root.addEventListener("focusin", stop);
    root.addEventListener("focusout", start);
    show(0);
    start();
  }

  function boot() { buildHeader(); initMechRotate(); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
