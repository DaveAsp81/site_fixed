/* BattleTech HQ — paint scheme reference.
 *
 * Replaces an interactive colour wheel with reference cards. The wheel let you
 * pick any colour on a screen, which is not a thing a painter needs; what they
 * need is "this unit, these three pots, in this order".
 *
 * Matching is nearest-neighbour in CIELAB. The previous version bucketed HSL
 * ranges and returned the first bucket that matched, which had three visible
 * consequences: mid grey #7a7a7a matched the metallic Leadbelcher, gold #ccaa00
 * matched the flat yellow Averland Sunset, and bone #e8e0cc matched nothing at
 * all. Lab distance has no buckets to fall between, and the pool is filtered by
 * finish so a matt panel can never be matched to a metallic.
 */
(function () {
    'use strict';

    var DATA = { paints: null, schemes: null };
    var state = { scheme: null, filter: 'all' };

    /* ---------- colour maths ---------- */

    function hexToRgb(hex) {
        var h = String(hex).trim().replace('#', '');
        if (h.length === 3) { h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2]; }
        return [parseInt(h.slice(0, 2), 16),
                parseInt(h.slice(2, 4), 16),
                parseInt(h.slice(4, 6), 16)];
    }

    function rgbToHex(rgb) {
        return '#' + rgb.map(function (v) {
            var n = Math.max(0, Math.min(255, Math.round(v)));
            return (n < 16 ? '0' : '') + n.toString(16);
        }).join('');
    }

    // sRGB -> linear -> XYZ (D65) -> CIELAB
    function rgbToLab(rgb) {
        var t = rgb.map(function (v) {
            v /= 255;
            return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
        });
        var x = (t[0] * 0.4124 + t[1] * 0.3576 + t[2] * 0.1805) / 0.95047;
        var y = (t[0] * 0.2126 + t[1] * 0.7152 + t[2] * 0.0722);
        var z = (t[0] * 0.0193 + t[1] * 0.1192 + t[2] * 0.9505) / 1.08883;
        var f = function (v) {
            return v > 0.008856 ? Math.cbrt(v) : (7.787 * v) + (16 / 116);
        };
        var fx = f(x), fy = f(y), fz = f(z);
        return [(116 * fy) - 16, 500 * (fx - fy), 200 * (fy - fz)];
    }

    function labToRgb(lab) {
        var fy = (lab[0] + 16) / 116;
        var fx = fy + lab[1] / 500;
        var fz = fy - lab[2] / 200;
        var inv = function (v) {
            var c = v * v * v;
            return c > 0.008856 ? c : (v - 16 / 116) / 7.787;
        };
        var x = inv(fx) * 0.95047, y = inv(fy), z = inv(fz) * 1.08883;
        var r = x * 3.2406 + y * -1.5372 + z * -0.4986;
        var g = x * -0.9689 + y * 1.8758 + z * 0.0415;
        var b = x * 0.0557 + y * -0.2040 + z * 1.0570;
        return [r, g, b].map(function (v) {
            v = v <= 0.0031308 ? 12.92 * v : 1.055 * Math.pow(Math.max(v, 0), 1 / 2.4) - 0.055;
            return Math.max(0, Math.min(255, v * 255));
        });
    }

    function deltaE(a, b) {
        var dl = a[0] - b[0], da = a[1] - b[1], db = a[2] - b[2];
        return Math.sqrt(dl * dl + da * da + db * db);
    }

    function labChroma(lab) { return Math.sqrt(lab[1] * lab[1] + lab[2] * lab[2]); }

    function labHue(lab) {
        var h = Math.atan2(lab[2], lab[1]) * 180 / Math.PI;
        return h < 0 ? h + 360 : h;
    }

    /* Which wash suits this colour. Worked out from Lab lightness, chroma and
       hue rather than a lookup per scheme, so a new scheme needs no extra data. */
    function shadeFamily(hex, finish) {
        if (finish === 'metallic') { return 'metal'; }
        var lab = rgbToLab(hexToRgb(hex));
        var c = labChroma(lab), h = labHue(lab), l = lab[0];
        if (c < 10) { return 'neutral'; }
        if (l > 72 && c < 32 && h >= 55 && h <= 105) { return 'bone'; }
        if (h >= 20 && h < 75 && l < 60) { return 'brown'; }
        if (h < 20 || h >= 345) { return 'red'; }
        if (h < 50) { return 'orange'; }
        if (h < 95) { return 'yellow'; }
        if (h < 165) { return 'green'; }
        if (h < 200) { return 'teal'; }
        if (h < 280) { return 'blue'; }
        if (h < 325) { return 'purple'; }
        return 'pink';
    }

    /* ---------- matching ---------- */

    /* `neutralOnly` restricts the pool to paints with almost no chroma.
       Without it, lightening #111111 matched Dryad Bark: a brown is genuinely
       closer in Lab to a lightened black than Eshin Grey is, because a 5-unit
       chroma error costs less than a 7-unit lightness error. Visually that is
       backwards - a grey that is slightly too light still reads as grey, a
       brown does not - so a neutral scheme gets a neutral pool. */
    function pool(rangeKey, finish, neutralOnly) {
        var want = finish === 'metallic' ? 'metallic' : 'matt';
        var list = DATA.paints.ranges[rangeKey].paints.filter(function (p) {
            return p.finish === want;
        });
        if (neutralOnly) {
            /* 4, not 8: at low lightness a chroma of 6 still reads plainly as
               brown, which is how Dryad Bark kept winning the layer slot on an
               all-black scheme. This leaves the true greys and whites. */
            var neutral = list.filter(function (p) {
                return labChroma(rgbToLab(hexToRgb(p.hex))) < 4;
            });
            // only if the range can actually supply a ramp from them
            if (neutral.length >= 3) { return neutral; }
        }
        return list;
    }

    function isNeutral(hex) {
        return labChroma(rgbToLab(hexToRgb(hex))) < 6;
    }

    /** Nearest paint in a range, optionally excluding names already used. */
    function nearest(rangeKey, hex, finish, exclude) {
        var target = rgbToLab(hexToRgb(hex));
        var best = null, bestD = Infinity;
        pool(rangeKey, finish, isNeutral(hex)).forEach(function (p) {
            if (exclude && exclude.indexOf(p.name) !== -1) { return; }
            var d = deltaE(target, rgbToLab(hexToRgb(p.hex)));
            if (d < bestD) { bestD = d; best = p; }
        });
        return best ? { name: best.name, hex: best.hex, delta: bestD } : null;
    }

    /** Shift a colour's lightness in Lab, keeping its hue. */
    function lighten(hex, dL) {
        var lab = rgbToLab(hexToRgb(hex));
        var chroma = labChroma(lab);
        lab[0] = Math.max(0, Math.min(100, lab[0] + dL));
        if (chroma < 6) {
            /* A near-neutral has to stay neutral. #111111 carries a faint warm
               cast, and lightening it while keeping that cast matched the layer
               to Dryad Bark - a brown - on an all-black scheme. */
            lab[1] = 0;
            lab[2] = 0;
        } else if (lab[0] > 80) {
            // Very light colours lose chroma in reality; mimic that a little so
            // a highlight is not a more saturated version of the base.
            var f = 1 - ((lab[0] - 80) / 40);
            lab[1] *= f; lab[2] *= f;
        }
        return rgbToHex(labToRgb(lab));
    }

    function lightnessOf(hex) { return rgbToLab(hexToRgb(hex))[0]; }

    /** Base -> layer -> edge highlight, as three distinct paints from one range.
     *
     * Each step has to be genuinely lighter than the one before it. Picking
     * purely by nearest-colour does not guarantee that: on a white scheme it
     * chose White Scar for the layer and then Corax White for the edge, which
     * is darker, so the highlight would have disappeared into the panel. */
    function ramp(rangeKey, hex, finish) {
        var used = [];
        var base = nearest(rangeKey, hex, finish, null);
        if (base) { used.push(base.name); }
        var neutral = isNeutral(hex);

        function stepUp(dL, floorL) {
            var target = rgbToLab(hexToRgb(lighten(hex, dL)));
            var best = null, bestD = Infinity;
            pool(rangeKey, finish, neutral).forEach(function (p) {
                if (used.indexOf(p.name) !== -1) { return; }
                var lab = rgbToLab(hexToRgb(p.hex));
                if (lab[0] <= floorL + 1.5) { return; }   // must actually be lighter
                var d = deltaE(target, lab);
                if (d < bestD) { bestD = d; best = p; }
            });
            return best
                ? { name: best.name, hex: best.hex, delta: bestD, L: lightnessOf(best.hex) }
                : null;
        }

        var baseL = base ? lightnessOf(base.hex) : lightnessOf(hex);
        var layer = stepUp(12, baseL);
        if (layer) { used.push(layer.name); }
        var edge = stepUp(26, layer ? layer.L : baseL);
        return { base: base, layer: layer, edge: edge };
    }

    function shadeFor(hex, finish) {
        var fam = shadeFamily(hex, finish);
        var match = DATA.paints.shades.filter(function (s) {
            return s.families.indexOf(fam) !== -1;
        });
        var pick = match[0] || DATA.paints.shades[0];
        var alts = DATA.paints.shade_alternatives[pick.name] || [];
        return { name: pick.name, brand: pick.brand, hex: pick.hex, family: fam, alts: alts };
    }

    /* ---------- rendering ---------- */

    function el(tag, cls, text) {
        var e = document.createElement(tag);
        if (cls) { e.className = cls; }
        if (text != null) { e.textContent = text; }
        return e;
    }

    function swatch(hex, size) {
        var s = el('span', 'ps-swatch');
        s.style.background = hex;
        if (size) { s.classList.add('ps-swatch--' + size); }
        return s;
    }

    function renderFilters() {
        var host = document.getElementById('ps-filters');
        if (!host) { return; }
        var factions = [];
        DATA.schemes.schemes.forEach(function (s) {
            if (factions.indexOf(s.faction) === -1) { factions.push(s.faction); }
        });
        host.innerHTML = '';
        var mk = function (value, label) {
            var b = el('button', 'ps-filter', label);
            b.type = 'button';
            b.setAttribute('aria-pressed', state.filter === value ? 'true' : 'false');
            b.addEventListener('click', function () {
                state.filter = value;
                renderFilters();
                renderCards();
            });
            return b;
        };
        host.appendChild(mk('all', 'All (' + DATA.schemes.schemes.length + ')'));
        factions.forEach(function (f) { host.appendChild(mk(f, f)); });
    }

    function visibleSchemes() {
        if (state.filter === 'all') { return DATA.schemes.schemes; }
        return DATA.schemes.schemes.filter(function (s) { return s.faction === state.filter; });
    }

    function renderCards() {
        var host = document.getElementById('ps-cards');
        if (!host) { return; }
        host.innerHTML = '';
        visibleSchemes().forEach(function (s) {
            var card = el('button', 'ps-card');
            card.type = 'button';
            card.setAttribute('aria-pressed', state.scheme === s.id ? 'true' : 'false');
            if (state.scheme === s.id) { card.classList.add('is-active'); }

            var bars = el('span', 'ps-card-bars');
            bars.setAttribute('aria-hidden', 'true');
            s.colours.forEach(function (c) {
                if (c.role === 'cockpit') { return; }
                var b = el('span', 'ps-card-bar');
                b.style.background = c.hex;
                bars.appendChild(b);
            });
            card.appendChild(bars);

            var body = el('span', 'ps-card-body');
            body.appendChild(el('span', 'ps-card-unit', s.unit));
            body.appendChild(el('span', 'ps-card-faction',
                s.faction + (s.kind ? ' · ' + s.kind : '')));
            card.appendChild(body);

            card.addEventListener('click', function () { select(s.id, true); });
            host.appendChild(card);
        });
        if (!host.children.length) {
            host.appendChild(el('p', 'ps-empty', 'No schemes for that filter.'));
        }
    }

    function colourBlock(c) {
        var wrap = el('div', 'ps-colour');

        var head = el('div', 'ps-colour-head');
        head.appendChild(swatch(c.hex, 'lg'));
        var titles = el('div', 'ps-colour-titles');
        titles.appendChild(el('span', 'ps-colour-role', c.role));
        titles.appendChild(el('span', 'ps-colour-label', c.label));
        var hx = el('span', 'ps-colour-hex', c.hex.toUpperCase()
            + (c.finish === 'metallic' ? ' · metallic' : ''));
        titles.appendChild(hx);
        head.appendChild(titles);
        wrap.appendChild(head);

        // one row per brand
        var table = el('div', 'ps-brands');
        Object.keys(DATA.paints.ranges).forEach(function (key) {
            var range = DATA.paints.ranges[key];
            var m = nearest(key, c.hex, c.finish, null);
            var row = el('div', 'ps-brand');
            row.appendChild(el('span', 'ps-brand-name', range.label));
            var val = el('span', 'ps-brand-match');
            if (m) {
                val.appendChild(swatch(m.hex));
                val.appendChild(el('span', 'ps-brand-paint', m.name));
                var q = m.delta < 6 ? 'close' : (m.delta < 14 ? 'near' : 'loose');
                var tag = el('span', 'ps-brand-fit ps-fit-' + q,
                    q === 'close' ? 'close match'
                        : (q === 'near' ? 'near match' : 'nearest available'));
                tag.title = 'Lab colour distance ' + m.delta.toFixed(1)
                    + '. Under 6 is hard to tell apart, over 14 is a visible difference.';
                val.appendChild(tag);
            } else {
                val.appendChild(el('span', 'ps-brand-paint', 'no match in range'));
            }
            row.appendChild(val);
            table.appendChild(row);
        });
        wrap.appendChild(table);

        if (c.role === 'cockpit') {
            /* Canopy colours are deliberately brighter than any matt paint can
               reach, so every one of them reports as a loose match. Say why,
               rather than leaving it looking like a gap in the data. */
            wrap.appendChild(el('p', 'ps-colour-note',
                'Canopy colours are brighter than any matt paint reaches. The match '
                + 'is the starting layer; the gloss coat in step 5 does the rest.'));
        }
        return wrap;
    }

    function stepRow(n, title, body, chips) {
        var li = el('li', 'ps-step');
        var num = el('span', 'ps-step-n', String(n));
        num.setAttribute('aria-hidden', 'true');
        li.appendChild(num);
        var main = el('div', 'ps-step-main');
        main.appendChild(el('h4', 'ps-step-title', title));
        main.appendChild(el('p', 'ps-step-body', body));
        if (chips && chips.length) {
            var row = el('div', 'ps-step-chips');
            chips.forEach(function (c) {
                if (!c || !c.name) { return; }
                var chip = el('span', 'ps-chip');
                chip.appendChild(swatch(c.hex));
                chip.appendChild(el('span', null, c.name));
                if (c.note) { chip.appendChild(el('em', 'ps-chip-note', c.note)); }
                row.appendChild(chip);
            });
            main.appendChild(row);
        }
        li.appendChild(main);
        return li;
    }

    function renderGuide(s) {
        var host = document.getElementById('ps-guide');
        host.innerHTML = '';

        var primary = s.colours.filter(function (c) { return c.role === 'primary'; })[0];
        var cockpit = s.colours.filter(function (c) { return c.role === 'cockpit'; })[0];
        if (!primary) { return; }

        var brand = document.getElementById('ps-brand-select').value;
        var r = ramp(brand, primary.hex, primary.finish);
        var sh = shadeFor(primary.hex, primary.finish);

        var intro = el('p', 'ps-guide-intro',
            'Five steps on the primary armour, with the ' + DATA.paints.ranges[brand].label
            + ' pots worked out from the scheme colour. The same ramp applies to the '
            + 'secondary and accent — swap the base and the rest follows.');
        host.appendChild(intro);

        var ol = el('ol', 'ps-steps');

        ol.appendChild(stepRow(1, 'Basecoat',
            'Two thin coats over primer rather than one thick one. Thick paint fills the '
            + 'panel lines you are about to shade, which is the single most common way a '
            + "'Mech ends up looking soft.",
            [{ hex: r.base ? r.base.hex : primary.hex,
               name: r.base ? r.base.name : primary.hex, note: 'base' }]));

        ol.appendChild(stepRow(2, 'Recess shade',
            'A wash over the whole panel, then pull it off the flats with a damp brush, or '
            + 'apply it only into the recesses if you want the panels clean. '
            + (sh.family === 'neutral' || sh.family === 'metal'
                ? 'A black wash suits this colour.'
                : 'A coloured wash keeps the hue; black would grey it down.'),
            [{ hex: sh.hex, name: sh.brand + ' ' + sh.name, note: 'wash' }].concat(
                sh.alts.map(function (a) { return { hex: sh.hex, name: a, note: 'or' }; }))));

        /* A range can simply run out of lighter paint: nothing in any of the
           three sits above White Scar, so a white scheme has no lighter pot to
           highlight with. Say what to do instead of inventing a chip. */
        var layerBody = 'Back over the raised panels with the base colour lightened, leaving '
            + 'the shade showing in the recesses and along the panel joins. Keep it off the '
            + 'edges — that is the next step.';
        if (!r.layer) {
            layerBody += ' There is nothing lighter than ' + (r.base ? r.base.name : 'the base')
                + ' in this range, so lighten it yourself: a drop of white into the base, '
                + 'thinned, is the layer.';
        }
        ol.appendChild(stepRow(3, 'Layer', layerBody,
            r.layer ? [{ hex: r.layer.hex, name: r.layer.name, note: 'layer' }] : []));

        var edgeBody = 'A fine line along the top edges and the chamfers only, where a light '
            + "above the 'Mech would catch. On a BattleMech that means shoulder tops, the "
            + 'cockpit brow, knee and hip plates, and the leading edge of each arm.';
        if (!r.edge) {
            edgeBody += ' This colour is already at the top of the range, so there is no '
                + 'lighter pot to edge with. Get the same effect the other way round: shade '
                + 'down the panel around the edge so the edge is what stays light.';
        }
        ol.appendChild(stepRow(4, 'Edge highlight', edgeBody,
            r.edge ? [{ hex: r.edge.hex, name: r.edge.name, note: 'edge' }] : []));

        if (cockpit) {
            var cr = ramp(brand, cockpit.hex, cockpit.finish);
            ol.appendChild(stepRow(5, 'Cockpit glass',
                'Gemming, the same technique used on power crystals. Black in the recess '
                + 'first, then the canopy colour across the lower two thirds, then a lighter '
                + 'layer in the bottom third only — light enters the top and pools at the '
                + 'bottom, so the gradient runs opposite to the armour. Finish with a single '
                + 'white dot in the upper corner and a coat of gloss varnish; the gloss is '
                + 'what actually sells it as glass.',
                [{ hex: '#0b0b0b', name: 'Black', note: 'recess' },
                 { hex: cr.base ? cr.base.hex : cockpit.hex,
                   name: cr.base ? cr.base.name : cockpit.hex, note: 'lower 2/3' }]
                .concat(cr.layer
                    ? [{ hex: cr.layer.hex, name: cr.layer.name, note: 'lower 1/3' }]
                    : [])
                .concat([{ hex: '#f2f3ef', name: 'White', note: 'dot' },
                         { hex: '#cfd6dd', name: 'Gloss varnish', note: 'last' }])));
        }

        host.appendChild(ol);
    }

    function renderDetail(s) {
        var host = document.getElementById('ps-detail');
        host.hidden = false;

        document.getElementById('ps-detail-unit').textContent = s.unit;
        document.getElementById('ps-detail-meta').textContent =
            [s.faction, s.era, s.kind + ' scheme'].filter(Boolean).join(' · ');
        document.getElementById('ps-detail-notes').textContent = s.notes || '';

        var src = document.getElementById('ps-detail-source');
        src.textContent = s.source;
        src.className = 'ps-source ' + (s.sourced ? 'is-sourced' : 'is-unsourced');

        var cols = document.getElementById('ps-colours');
        cols.innerHTML = '';
        s.colours.forEach(function (c) { cols.appendChild(colourBlock(c)); });

        renderGuide(s);
    }

    function select(id, push) {
        var s = DATA.schemes.schemes.filter(function (x) { return x.id === id; })[0];
        if (!s) { return; }
        state.scheme = id;
        renderCards();
        renderDetail(s);
        if (push) {
            try {
                history.replaceState(null, '', '?scheme=' + encodeURIComponent(id));
            } catch (e) { /* file:// or blocked */ }
            document.getElementById('ps-detail')
                .scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    /* ---------- boot ---------- */

    function fail(msg) {
        var host = document.getElementById('ps-cards');
        if (host) {
            host.innerHTML = '';
            host.appendChild(el('p', 'ps-empty', msg));
        }
    }

    function boot() {
        Promise.all([
            fetch('assets/data/paints.json').then(function (r) {
                if (!r.ok) { throw new Error('paints.json ' + r.status); }
                return r.json();
            }),
            fetch('assets/data/paint-schemes.json').then(function (r) {
                if (!r.ok) { throw new Error('paint-schemes.json ' + r.status); }
                return r.json();
            })
        ]).then(function (res) {
            DATA.paints = res[0];
            DATA.schemes = res[1];

            var sel = document.getElementById('ps-brand-select');
            sel.innerHTML = '';
            Object.keys(DATA.paints.ranges).forEach(function (k) {
                var o = document.createElement('option');
                o.value = k;
                o.textContent = DATA.paints.ranges[k].label;
                sel.appendChild(o);
            });
            sel.addEventListener('change', function () {
                if (state.scheme) {
                    var s = DATA.schemes.schemes.filter(function (x) {
                        return x.id === state.scheme;
                    })[0];
                    if (s) { renderGuide(s); }
                }
            });

            renderFilters();
            renderCards();

            var wanted = null;
            try {
                wanted = new URLSearchParams(location.search).get('scheme');
            } catch (e) { /* ignore */ }
            var first = DATA.schemes.schemes[0];
            select(wanted && DATA.schemes.schemes.some(function (x) { return x.id === wanted; })
                ? wanted : first.id, false);
        }).catch(function (err) {
            console.error(err);
            fail('Could not load the scheme data. Reload the page, and if it keeps '
                 + 'happening the paint data files may not have deployed.');
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})();
