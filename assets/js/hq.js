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

  var logoSvg =
    '<svg class="logo-mark" viewBox="0 0 32 32" aria-hidden="true">' +
    '<rect width="32" height="32" rx="2" fill="#0a0a0b"/>' +
    '<path d="M7 7h5v1.6H8.6V12H7V7zm13 0h5v5h-1.6V8.6H20V7zM7 20h1.6v3.4H12V25H7v-5zm16.4 0H25v5h-5v-1.6h3.4V20z" fill="#ff8c00"/>' +
    '<rect x="14.2" y="14.2" width="3.6" height="3.6" fill="#ff8c00"/>' +
    "</svg>";

  function buildHeader() {
    var header = document.querySelector("header");
    if (!header) return;

    var toolItems = tools
      .map(function (t) {
        return (
          '<a href="' +
          prefix +
          t.href +
          '"><span>' +
          t.title +
          "</span><small>" +
          t.kicker +
          "</small></a>"
        );
      })
      .join("");

    var navLinks = links
      .map(function (l) {
        return '<li><a href="' + prefix + l.href + '">' + l.label + "</a></li>";
      })
      .join("");

    header.classList.add("hq-built");
    header.innerHTML =
      '<div class="header-content">' +
      '<a href="' +
      prefix +
      'index.html" class="logo" aria-label="BattleTech HQ home">' +
      logoSvg +
      '<span class="logo-stack"><small>BATTLETECH</small><strong>HQ</strong></span>' +
      "</a>" +
      '<button class="nav-toggle" type="button" aria-label="Open menu" aria-expanded="false">MENU</button>' +
      '<nav class="hq-nav" aria-label="Primary">' +
      "<ul>" +
      '<li class="hq-drop">' +
      '<a href="' +
      prefix +
      'lance-builder.html">Tools</a>' +
      '<div class="hq-drop-panel"><div class="hq-drop-inner">' +
      toolItems +
      "</div></div>" +
      "</li>" +
      navLinks +
      "</ul>" +
      "</nav>" +
      '<a class="hq-cta" href="' +
      prefix +
      'lance-builder.html">Lance Builder</a>' +
      "</div>";

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

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", buildHeader);
  } else {
    buildHeader();
  }
})();
