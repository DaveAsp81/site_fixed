/* BattleTech HQ - shared behaviour for every page.
 *
 * This replaces the inline nav-toggle snippet that was copy-pasted into 40
 * pages. Everything here degrades to nothing if JavaScript is off: the nav
 * is a plain list, tables still scroll, and the tools still work.
 */
(function () {
    'use strict';

    /* -- Mobile nav ---------------------------------------------------
       The old snippet toggled a class and never told assistive tech
       whether the menu was open. */
    function initNav() {
        var toggle = document.querySelector('.nav-toggle');
        var nav = document.getElementById('site-nav');
        if (!toggle || !nav) { return; }
        var list = nav.querySelector('ul');
        if (!list) { return; }

        function setOpen(open) {
            list.classList.toggle('open', open);
            toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
        }
        setOpen(false);

        toggle.addEventListener('click', function () {
            setOpen(toggle.getAttribute('aria-expanded') !== 'true');
        });
        // Escape closes it and returns focus to the button.
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
                setOpen(false);
                toggle.focus();
            }
        });
        // A tap outside the menu closes it.
        document.addEventListener('click', function (e) {
            if (toggle.getAttribute('aria-expanded') !== 'true') { return; }
            if (!nav.contains(e.target) && !toggle.contains(e.target)) {
                setOpen(false);
            }
        });
    }

    /* -- Wide tables --------------------------------------------------
       The variant tables are 900px inside a 375px viewport. Most were
       already in an overflow:auto wrapper, but nothing said so and a
       keyboard could not scroll them. */
    function initTables() {
        var tables = document.querySelectorAll('table');
        Array.prototype.forEach.call(tables, function (table) {
            var wrap = table.parentElement;
            if (!wrap || !wrap.classList.contains('table-wrap')) {
                wrap = document.createElement('div');
                wrap.className = 'table-wrap';
                table.parentNode.insertBefore(wrap, table);
                wrap.appendChild(table);
            }
            function sync() {
                var over = wrap.scrollWidth > wrap.clientWidth + 1;
                wrap.classList.toggle('is-scrollable', over);
                if (over) {
                    // focusable, so it can be scrolled from the keyboard
                    wrap.setAttribute('tabindex', '0');
                    wrap.setAttribute('role', 'region');
                    var cap = table.querySelector('caption');
                    wrap.setAttribute('aria-label',
                        (cap ? cap.textContent.trim() : 'Table') + ' (scrolls sideways)');
                } else {
                    wrap.removeAttribute('tabindex');
                    wrap.removeAttribute('role');
                    wrap.removeAttribute('aria-label');
                }
                wrap.classList.toggle('at-end',
                    wrap.scrollLeft + wrap.clientWidth >= wrap.scrollWidth - 2);
            }
            sync();
            wrap.addEventListener('scroll', sync, { passive: true });
            window.addEventListener('resize', sync);
        });
    }

    /* Headings carry decorative emoji; a contents link should not. */
    function cleanHeading(text) {
        var out = text;
        try {
            out = out.replace(/[\p{Extended_Pictographic}\p{So}]/gu, '');
        } catch (e) {
            // very old engine with no Unicode property escapes
            out = out.replace(/[^\w\s':,.&()-]/g, '');
        }
        return out.replace(/\s+/g, ' ').trim();
    }

    /* -- Contents list for long guides --------------------------------
       A 3,500-word guide with 12 headings and no way to jump. Built
       from the headings already on the page, so it cannot go stale.
       Opt in with <nav class="guide-toc" data-toc hidden></nav>. */
    function initToc() {
        var host = document.querySelector('[data-toc]');
        if (!host) { return; }
        var scopeSel = host.getAttribute('data-toc-scope') || 'main';
        var scope = document.querySelector(scopeSel) || document;
        var heads = Array.prototype.filter.call(scope.querySelectorAll('h2'), function (h) {
            // Skip our own heading and the related-guides block's, which both
            // sit inside the article but are not sections of it.
            return h.textContent.trim()
                && !h.closest('.guide-toc')
                && !h.closest('.related-guides');
        });
        if (heads.length < 4) { host.remove(); return; }

        var list = document.createElement('ol');
        heads.forEach(function (h, i) {
            var clean = cleanHeading(h.textContent);
            if (!h.id) {
                h.id = 'section-' + (i + 1) + '-' + clean.toLowerCase()
                    .replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 40);
            }
            var li = document.createElement('li');
            var a = document.createElement('a');
            a.href = '#' + h.id;
            a.textContent = clean;
            li.appendChild(a);
            list.appendChild(li);
        });
        var title = document.createElement('h2');
        title.className = 'guide-toc-title';
        title.id = 'toc-title';
        title.textContent = 'On this page';
        host.appendChild(title);
        host.appendChild(list);
        host.hidden = false;
    }

    /* -- Back to top --------------------------------------------------
       Only on pages long enough to need it. */
    function initBackToTop() {
        if (document.documentElement.scrollHeight < window.innerHeight * 4) { return; }
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'to-top';
        btn.setAttribute('aria-label', 'Back to top');
        btn.innerHTML = '<span aria-hidden="true">&uarr;</span>';
        btn.addEventListener('click', function () {
            window.scrollTo({ top: 0, behavior: 'smooth' });
            var first = document.querySelector('.skip-link');
            if (first) { first.focus(); }
        });
        document.body.appendChild(btn);
        function sync() {
            btn.classList.toggle('is-visible', window.scrollY > window.innerHeight * 1.5);
        }
        sync();
        window.addEventListener('scroll', sync, { passive: true });
    }

    /* -- Screen wake lock ---------------------------------------------
       The trackers get used on a phone propped next to the table for a
       couple of hours. Without this the screen sleeps mid-turn.
       Opt in with <body data-wake-lock>. */
    function initWakeLock() {
        if (!document.body.hasAttribute('data-wake-lock')) { return; }
        if (!('wakeLock' in navigator)) { return; }

        var sentinel = null;
        var wanted = true;
        try { wanted = localStorage.getItem('bthq-wake-lock') !== 'off'; } catch (e) {}

        var chip = document.createElement('button');
        chip.type = 'button';
        chip.className = 'wake-chip';
        document.body.appendChild(chip);

        function paint() {
            chip.classList.toggle('is-on', wanted);
            chip.setAttribute('aria-pressed', wanted ? 'true' : 'false');
            chip.textContent = wanted ? 'Screen stays on' : 'Screen may sleep';
        }

        function acquire() {
            if (!wanted || sentinel || document.visibilityState !== 'visible') { return; }
            navigator.wakeLock.request('screen').then(function (s) {
                sentinel = s;
                s.addEventListener('release', function () { sentinel = null; });
            }).catch(function () { /* denied or unsupported; nothing to do */ });
        }
        function release() {
            if (sentinel) { sentinel.release(); sentinel = null; }
        }

        chip.addEventListener('click', function () {
            wanted = !wanted;
            try { localStorage.setItem('bthq-wake-lock', wanted ? 'on' : 'off'); } catch (e) {}
            if (wanted) { acquire(); } else { release(); }
            paint();
        });
        // The lock is dropped whenever the tab is hidden, so re-take it.
        document.addEventListener('visibilitychange', function () {
            if (document.visibilityState === 'visible') { acquire(); }
        });
        paint();
        acquire();
    }

    /* -- Newsletter, without leaving the page -------------------------
       The form used to post to Mailchimp with target="_blank", which
       threw the reader into a new tab. Mailchimp's JSONP endpoint lets
       us keep them here. */
    function initNewsletter() {
        var forms = document.querySelectorAll('form[data-mc-ajax]');
        Array.prototype.forEach.call(forms, function (form) {
            var status = form.parentNode.querySelector('.form-status');
            if (!status) {
                status = document.createElement('p');
                status.className = 'form-status';
                status.setAttribute('role', 'status');
                form.parentNode.insertBefore(status, form.nextSibling);
            }
            form.addEventListener('submit', function (e) {
                e.preventDefault();
                var url = form.action.replace('/post?', '/post-json?');
                var data = new URLSearchParams(new FormData(form)).toString();
                var cb = 'mc_cb_' + Date.now();
                var script = document.createElement('script');

                status.className = 'form-status is-pending';
                status.textContent = 'Signing you up...';

                window[cb] = function (res) {
                    var ok = res && res.result === 'success';
                    status.className = 'form-status ' + (ok ? 'is-ok' : 'is-error');
                    status.textContent = ok
                        ? 'You are on the list. Check your inbox to confirm.'
                        : (res && res.msg ? String(res.msg).replace(/<[^>]*>/g, '')
                                          : 'That did not go through. Try again in a moment.');
                    if (ok) { form.reset(); }
                    delete window[cb];
                    script.remove();
                };
                script.src = url + '&' + data + '&c=' + cb;
                script.onerror = function () {
                    status.className = 'form-status is-error';
                    status.textContent = 'That did not go through. Try again in a moment.';
                    script.remove();
                };
                document.body.appendChild(script);
            });
        });
    }

    /* -- Offline support ----------------------------------------------
       So the tools still open at a club with bad wifi. */
    function initServiceWorker() {
        if (!('serviceWorker' in navigator)) { return; }
        if (location.protocol === 'file:') { return; }
        window.addEventListener('load', function () {
            navigator.serviceWorker.register('/sw.js').catch(function () {});
        });
    }

    function boot() {
        initNav();
        initTables();
        initToc();
        initBackToTop();
        initWakeLock();
        initNewsletter();
        initServiceWorker();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})();
