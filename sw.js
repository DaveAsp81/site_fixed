/* BattleTech HQ service worker.
 *
 * Purpose: the trackers get used at a table on club wifi, so the tool pages
 * and their data need to open when the network does not cooperate.
 *
 * Strategy:
 *   navigations  -> network first, fall back to cache, then to /offline.html
 *   static assets -> stale-while-revalidate (instant, refreshed in background)
 *
 * Bump CACHE_VERSION whenever the precache list or the shell changes; the old
 * cache is deleted on activate so a stale shell can never stick around.
 */
var CACHE_VERSION = 'bthq-v1';
var SHELL = CACHE_VERSION + '-shell';
var RUNTIME = CACHE_VERSION + '-runtime';

// The shell only. Precaching the five tool pages as well would have pulled
// roughly 600 KB in the background on every first visit, including for
// someone who only came to read one lore article. The tool pages and
// mechs.json land in the runtime cache the first time they are actually
// opened, which is what makes them work offline afterwards.
var PRECACHE = [
    '/',
    '/offline.html',
    '/assets/css/style.css',
    '/assets/js/site.js'
];

self.addEventListener('install', function (event) {
    event.waitUntil(
        caches.open(SHELL).then(function (cache) {
            // addAll fails the whole install if any single item 404s, so add
            // them independently and let the rest through.
            return Promise.all(PRECACHE.map(function (url) {
                return cache.add(new Request(url, { cache: 'reload' })).catch(function () {});
            }));
        }).then(function () { return self.skipWaiting(); })
    );
});

self.addEventListener('activate', function (event) {
    event.waitUntil(
        caches.keys().then(function (keys) {
            return Promise.all(keys.map(function (k) {
                if (k !== SHELL && k !== RUNTIME) { return caches.delete(k); }
            }));
        }).then(function () { return self.clients.claim(); })
    );
});

function isStatic(url) {
    return /\.(css|js|woff2?|webp|jpg|jpeg|png|svg|ico|json)$/i.test(url.pathname);
}

self.addEventListener('fetch', function (event) {
    var req = event.request;
    if (req.method !== 'GET') { return; }

    var url = new URL(req.url);
    // Never touch analytics, Mailchimp or anything cross-origin.
    if (url.origin !== self.location.origin) { return; }

    if (req.mode === 'navigate') {
        event.respondWith(
            fetch(req).then(function (res) {
                var copy = res.clone();
                caches.open(RUNTIME).then(function (c) { c.put(req, copy); });
                return res;
            }).catch(function () {
                return caches.match(req).then(function (hit) {
                    return hit || caches.match('/offline.html');
                });
            })
        );
        return;
    }

    if (!isStatic(url)) { return; }

    event.respondWith(
        caches.match(req).then(function (hit) {
            var network = fetch(req).then(function (res) {
                if (res && res.status === 200) {
                    var copy = res.clone();
                    caches.open(RUNTIME).then(function (c) { c.put(req, copy); });
                }
                return res;
            }).catch(function () { return hit; });
            return hit || network;
        })
    );
});
