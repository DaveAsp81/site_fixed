#!/usr/bin/env python3
"""
The chassis guide engine.

Everything that is the same for every mech page lives here: loading the
variant data, computing the rating rubric, rendering the variant table and
verdict cards, the page skeleton, click tracking, link cleaning and the
self-tests.

Everything that is specific to one mech, the prose and the judgement calls,
lives in a chassis module (chassis_marauder.py, chassis_warhammer.py, ...).

VOICE
-----
Inner Sphere chassis are written by a MechTech who has had the machine in
the bay: first person, opinionated, plain. "I have sharpened one of these."

Clan chassis are written from the technician caste's perspective. Precise,
unhedged, no contractions, the Inner Sphere referred to as "they". Clan
terms only where they carry meaning (caste, Trial, touman); heavier jargon
reads as pastiche. chassis_timber_wolf.py is the reference implementation.

The two registers sit close enough together that writing one right after
the other is exactly when the voice bleeds. It happened on chassis_ostroc.py:
written after chassis_timber_wolf.py, it came out clipped and unhedged, a
Clan technician's rhythm on an Inner Sphere page, with none of the
MechTech's usual first-person asides. The build guard below catches the
obvious version of this in both directions; it does not replace reading
the lead paragraph back before shipping, especially when a Clan and an
Inner Sphere page are written in the same sitting.

The engine decides which note to show from the data, not from the module:
technology == 'Clan' gets the voice note automatically. "Mixed" chassis are
Inner Sphere designs with Clan-tech variants and keep the MechTech voice.
A module can override with 'clan_voice': True/False.

Build a page with:  python3 build_mech_page.py marauder
"""

import difflib
import html
import json
import re
from pathlib import Path

import site_links

# The corrected data with the restored Clan aliases, falling back to the
# original upload if it has not been built yet.
SRC = Path('/mnt/user-data/outputs/for-site/mechs.json')
if not SRC.exists():
    SRC = Path('/mnt/user-data/uploads/mechs.json')
OUT_DIR = Path('/mnt/user-data/outputs/for-site')
GA_ID = 'G-T2794K8B9W'
SITE = 'https://battletechhq.com'

# A variant is a Trap if another variant of the same chassis, in the same era,
# at no more than this above its Battle Value, matches or beats it on every
# damage band, on armour, on structure, carries every ability it has and does
# not lose jump. Restated in build_rating_scale.py, which checks it matches.
BV_TOLERANCE = 0.03

ERA_ORDER = [
    'Age of War',
    'Star League',
    'Early Succession War',
    'Late Succession War - LosTech',
    'Late Succession War - Renaissance',
    'Clan Invasion',
    'Civil War',
    'Jihad',
    'Early Republic',
    'Late Republic',
    'Dark Age',
    'ilClan',
]

TIER_LABEL = {
    'pick': 'Worth it',
    'solid': 'Solid',
    'situational': 'Situational',
    'trap': 'Trap',
}

# Tiers a chassis module is allowed to assign. 'trap' is computed, never given.
ASSIGNABLE_TIERS = ('pick', 'solid', 'situational')


def e(x):
    return html.escape(str(x), quote=True)


# 15 variants across 14 chassis carry no introduction date: the Master Unit
# List has null for them, so there is no year to use. We do not invent one.
# They sort to the end of their era block and the table prints what the data
# says, which is "Unknown".
UNDATED = 10 ** 6


def year(var):
    """Introduction year. Undated variants sort last, never first."""
    try:
        return int(var['date_introduced'])
    except (ValueError, TypeError, KeyError):
        return UNDATED


def dated(variants):
    """Only the variants that actually carry a year."""
    return [v for v in variants if year(v) != UNDATED]


# --------------------------------------------------------------- the context

class Chassis:
    """Data access and rubric for one chassis. Handed to the content module."""

    def __init__(self, name, data=None):
        raw = data if data is not None else json.loads(SRC.read_text(encoding='utf-8'))
        self.all = {c['chassis']: c for c in raw}
        if name not in self.all:
            raise KeyError(f'chassis not in mechs.json: {name}')
        self.name = name
        self.rec = self.all[name]
        self.variants = {v['name']: v for v in self.rec['variants']}
        self.dominated = self._compute_dominated()

    # -- data access --------------------------------------------------------

    def v(self, variant, field, default=''):
        rec = self.variants.get(variant)
        if rec is None:
            raise KeyError(f'{self.name} has no variant {variant}')
        val = rec.get(field, default)
        return default if val is None else val

    def other(self, chassis, variant, field):
        if chassis not in self.all:
            raise KeyError(f'chassis not in mechs.json: {chassis}')
        for var in self.all[chassis]['variants']:
            if var['name'] == variant:
                return var.get(field)
        raise KeyError(f'{chassis} has no variant {variant}')

    def dmg(self, variant):
        b = self.variants[variant].get('bf_damage') or {}
        return (b.get('short', 0), b.get('medium', 0), b.get('long', 0))

    def dmg_str(self, variant):
        return '{}/{}/{}'.format(*self.dmg(variant))

    def hs_prose(self, variant):
        """'16 Single' reads badly mid-sentence. Render it as prose."""
        raw = str(self.v(variant, 'heatsinks', '')).strip()
        if not raw:
            return 'an unrecorded number of heat sinks'
        parts = raw.split()
        kind = ' '.join(parts[1:]).lower().replace('is ', '').replace('clan ', '')
        return f'{parts[0]} {kind} heat sinks'.replace('  ', ' ')

    def hs_count(self, variant):
        return int(str(self.v(variant, 'heatsinks', '0')).split()[0])

    def hs_prose_other(self, chassis, variant):
        raw = str(self.other(chassis, variant, 'heatsinks') or '').strip()
        parts = raw.split()
        kind = ' '.join(parts[1:]).lower().replace('is ', '').replace('clan ', '')
        return f'{parts[0]} {kind} heat sinks'.replace('  ', ' ')

    @property
    def n_variants(self):
        return len(self.rec['variants'])

    @property
    def tons(self):
        return self.rec['tons']

    def by_date(self):
        return sorted(self.rec['variants'], key=year)

    def production_span(self):
        d = dated(self.by_date())
        return year(d[-1]) - year(d[0])

    def first_year(self):
        return dated(self.by_date())[0]['date_introduced']

    def last_year(self):
        return dated(self.by_date())[-1]['date_introduced']

    def undated(self):
        """Variants the MUL gives no introduction date for."""
        return [v['name'] for v in self.rec['variants'] if year(v) == UNDATED]

    # -- the rubric ---------------------------------------------------------

    @staticmethod
    def _abil(var):
        raw = (var.get('bf_abilities') or '').strip()
        return set(x.split('/')[0].strip() for x in raw.split(',') if x.strip())

    @staticmethod
    def _jumps(var):
        mv = var.get('movement') or ''
        return 'Jump' in mv and 'Jump 0' not in mv

    @staticmethod
    def _dmg(var):
        b = var.get('bf_damage') or {}
        return (b.get('short', 0), b.get('medium', 0), b.get('long', 0))

    def _compute_dominated(self):
        eras = {}
        for var in self.rec['variants']:
            eras.setdefault(var['era'], []).append(var)

        out = {}
        for peers in eras.values():
            for a in peers:
                da, aa, sa, ja = self._dmg(a), a.get('bf_armor', 0), self._abil(a), self._jumps(a)
                sta = a.get('bf_structure', 0)
                beaten = []
                for b in peers:
                    if b is a:
                        continue
                    db, ab, sb, jb = self._dmg(b), b.get('bf_armor', 0), self._abil(b), self._jumps(b)
                    stb = b.get('bf_structure', 0)
                    better = (any(y > x for x, y in zip(da, db))
                              or ab > aa or b['bv'] < a['bv'])
                    if (b['bv'] <= a['bv'] * (1 + BV_TOLERANCE)
                            and all(y >= x for x, y in zip(da, db))
                            and ab >= aa and stb >= sta
                            and sa.issubset(sb)
                            and (jb or not ja)
                            and better):
                        beaten.append(b['name'])
                if beaten:
                    beaten.sort(key=lambda n: next(
                        x['bv'] for x in peers if x['name'] == n))
                    out[a['name']] = beaten
        return out

    def best_dominator(self, variant):
        """The cheapest variant that beats this one and is not itself beaten."""
        winners = self.dominated[variant]
        clean = [w for w in winners if w not in self.dominated]
        return clean[0] if clean else winners[0]

    def verdict_for(self, variant, verdicts):
        """Resolved tier and note. A computed domination overrides the call."""
        tier, note = verdicts[variant]
        if variant in self.dominated:
            # Prefer a dominator that is not itself a trap: telling someone
            # to take a machine that is also beaten is useless advice, and it
            # happens whenever domination chains (A beaten by B beaten by C).
            winner = self.best_dominator(variant)
            saving = self.variants[variant]['bv'] - self.variants[winner]['bv']
            if saving > 0:
                cost = f'costs {saving} less BV and'
            elif saving == 0:
                cost = 'costs the same and'
            else:
                cost = f'costs {abs(saving)} more BV but'
            note = (f'{note} Beaten outright by the {winner}, which {cost} '
                    f'gives up nothing it carries.')
            tier = 'trap'
        return tier, note


# ------------------------------------------------------------- page fragments

def variant_table(ch, verdicts):
    groups = {}
    for var in ch.rec['variants']:
        groups.setdefault(var['era'], []).append(var)

    rows = []
    for era in ERA_ORDER:
        if era not in groups:
            continue
        rows.append(f'<tr class="era-row"><th colspan="8">{e(era)}</th></tr>')
        for var in sorted(groups[era], key=year):
            tier, _ = ch.verdict_for(var['name'], verdicts)
            badge = f'<span class="tier tier-{tier}">{TIER_LABEL[tier]}</span>'
            if var['name'] in ch.dominated:
                badge += (f'<span class="beaten">beaten by '
                          f'{e(ch.best_dominator(var["name"]))}</span>')
            b = var.get('bf_damage') or {}
            rows.append(
                '<tr>'
                f'<td class="vname">{e(var["name"])}</td>'
                f'<td>{e(var["date_introduced"])}</td>'
                f'<td>{e(var["bv"])}</td>'
                f'<td>{e(var["pv"])}</td>'
                f'<td>{e(var["role"])}</td>'
                f'<td class="wpn">{e(", ".join(var.get("weapons", [])))}</td>'
                f'<td class="num">{b.get("short", 0)}/{b.get("medium", 0)}/{b.get("long", 0)}</td>'
                f'<td>{badge}</td>'
                '</tr>')
    return '\n'.join(rows)


def verdict_card(ch, variant, heading, verdicts):
    tier, note = ch.verdict_for(variant, verdicts)
    rec = ch.variants[variant]
    return f'''<div class="vcard">
  <div class="vcard-head">
    <h3>{e(heading)}</h3>
    <span class="tier tier-{tier}">{TIER_LABEL[tier]}</span>
  </div>
  <p class="vstats">{e(rec["tons"])} tons &middot; BV {e(rec["bv"])} &middot; PV {e(rec["pv"])} &middot; {e(rec["role"])} &middot; {e(rec["date_introduced"])}<br>
  {e(rec.get("movement", ""))} &middot; {e(rec.get("heatsinks", ""))} &middot; {e(rec.get("engine", ""))}<br>
  {e(", ".join(rec.get("weapons", [])))}</p>
  <p>{e(note)}</p>
</div>'''


def availability_table(ch, variant):
    av = ch.variants[variant].get('availability_mul', {})
    rows = '\n'.join(
        f'<tr><td class="vname">{e(era)}</td><td>{e(", ".join(f))}</td></tr>'
        for era, f in av.items())
    return f'''<div class="table-wrap">
                <table class="vtable" style="min-width:600px;">
                    <thead><tr><th>Era</th><th>Available to</th></tr></thead>
                    <tbody>
{rows}
                    </tbody>
                </table>
            </div>'''


def family_grid(ch, entries):
    cards = []
    for chassis_name, blurb in entries:
        if chassis_name not in ch.all:
            raise KeyError(
                f'family card for "{chassis_name}" but there is no such '
                f'chassis in mechs.json. Mention it in prose instead, or '
                f'check the spelling.')
        rec = ch.all[chassis_name]
        bvs = [x['bv'] for x in rec['variants'] if x.get('bv')]
        cards.append(f'''<div class="fam">
  <h3>{e(rec["chassis"])}</h3>
  <p class="vstats">{e(rec["tons"])} tons &middot; {e(rec["technology"])} &middot; {len(rec["variants"])} variants &middot; BV {min(bvs)} to {max(bvs)}</p>
  <p>{e(blurb)}</p>
</div>''')
    return '<div class="fam-grid">\n' + '\n'.join(cards) + '\n</div>'


def rubric_box(ch, display=None):
    return f'''<div class="rubric">
                <div class="rubric-row">
                    <span class="tier tier-pick">Worth it</span>
                    <p>Nothing in its era does the chassis's job better for the money.</p>
                </div>
                <div class="rubric-row">
                    <span class="tier tier-solid">Solid</span>
                    <p>Does the job competently. Another variant does it better or cheaper, but there is no reason to avoid this one.</p>
                </div>
                <div class="rubric-row">
                    <span class="tier tier-situational">Situational</span>
                    <p>Only earns its Battle Value if you specifically need what it carries. C3, stealth, a command console, flak, jump jets.</p>
                </div>
                <div class="rubric-row">
                    <span class="tier tier-trap">Trap</span>
                    <p>Another variant in the same era, at no more than {int(BV_TOLERANCE * 100)} percent above its Battle Value, matches or beats it on every Alpha Strike damage band, on armour, on structure, and carries every special ability it has. Nothing gained, something lost, no dearer.</p>
                </div>
            </div>
            <p class="rubric-note">Only the Trap tier is calculated. It is worked out from the variant data rather than decided by me, which means it is falsifiable: to argue with it you only have to name something the cheaper machine gives up. The other three are my opinion and you should treat them that way. {len(ch.dominated)} of the {ch.n_variants} {display or ch.name} variants fail the Trap test. <a href="rating-scale.html" style="color:#ff8c00;">The full rating scale is here</a>, including what it deliberately does not measure.</p>'''


def voice_note(ch, c):
    """Clan pages are written from the technician caste's perspective, not
    the Inner Sphere MechTech who narrates everything else. Without a note
    the shift reads as an inconsistent author rather than a deliberate one.

    Decided from the data: technology == 'Clan'. "Mixed" chassis are Inner
    Sphere designs with some Clan-tech variants and stay in the usual voice.
    A chassis module can force it either way with 'clan_voice'.
    """
    clan = c.get('clan_voice', ch.rec.get('technology') == 'Clan')
    if not clan:
        return ''
    return ('<p class="voice-note"><strong>A note on this one.</strong> '
            'Clan machines on this site are written from the perspective of '
            'a Clan technician rather than the Inner Sphere MechTech who '
            'narrates the rest. Same research, same data, different chair.</p>')


def tool_cta(ch, display=None):
    return f'''<div class="tool-cta">
                <a href="lance-builder.html">
                    <strong>&#9881; Build a lance around it</strong>
                    <span>Filter by faction and era, track BV and tonnage live, and print the roster.</span>
                </a>
                <a href="opfor-command.html">
                    <strong>&#9876; Fight one solo</strong>
                    <span>Put a {e(display or ch.name)} in the opposing force and let the AI drive it.</span>
                </a>
            </div>'''


def faq_block(entries):
    parts = []
    for q, a in entries:
        parts.append(f'                <h3>{e(q)}</h3>\n                <p>{a}</p>')
    return '<div class="faq">\n' + '\n\n'.join(parts) + '\n            </div>'


def faq_schema(entries):
    items = ',\n'.join(
        '    {\n'
        '      "@type": "Question",\n'
        f'      "name": {json.dumps(q)},\n'
        '      "acceptedAnswer": {"@type": "Answer", "text": '
        f'{json.dumps(re.sub(r"<[^>]+>", "", a))}' '}\n'
        '    }' for q, a in entries)
    return ('<script type="application/ld+json">\n{\n'
            '  "@context": "https://schema.org",\n'
            '  "@type": "FAQPage",\n'
            '  "mainEntity": [\n' + items + '\n  ]\n}\n</script>')


# ------------------------------------------------------------------ assembly

CSS = Path(__file__).with_name('_page_css.html')
TRACKING = Path(__file__).with_name('_page_tracking.html')
FOOTER = Path(__file__).with_name('_page_footer.html')


def _part(p):
    return p.read_text(encoding='utf-8')


NL = '\n\n            '


def render(ch, c):
    """Assemble the page. `c` is the dict returned by a chassis module."""
    # A chassis may be shown under a different name to the one the data is
    # keyed on. Clan designs are keyed by their Inner Sphere reporting name.
    display = c.get('display_name', ch.name)
    body = []
    for item in c['body']:
        kind = item[0]
        if kind == 'prose':
            _, heading, inner = item
            body.append((f'            <h2>{e(heading)}</h2>\n' if heading else '') + inner)
        elif kind == 'rubric':
            body.append(rubric_box(ch, display))
        elif kind == 'featured':
            body.append('\n'.join(
                verdict_card(ch, name, head, c['verdicts']) for name, head in item[1]))
        elif kind == 'table':
            body.append(f'''<div class="table-wrap">
                <table class="vtable">
                    <thead>
                        <tr><th>Variant</th><th>Intro</th><th>BV</th><th>PV</th><th>Role</th><th>Weapons</th><th>S/M/L</th><th>Verdict</th></tr>
                    </thead>
                    <tbody>
{variant_table(ch, c['verdicts'])}
                    </tbody>
                </table>
            </div>''')
        elif kind == 'availability':
            body.append(availability_table(ch, item[1]))
        elif kind == 'family':
            body.append(family_grid(ch, item[1]))
        elif kind == 'cta':
            body.append(tool_cta(ch, display))
        elif kind == 'faq':
            body.append(faq_block(item[1]))
        elif kind == 'plate':
            pl = item[1]
            body.append(f'''<figure class="mech-plate">
                <picture>
                    <source srcset="{pl['webp']}" type="image/webp">
                    <img src="{pl['png']}" alt="{e(pl['alt'])}"
                         width="{pl['width']}" height="{pl['height']}"
                         loading="lazy" decoding="async">
                </picture>
                <figcaption>{pl['caption']}</figcaption>
            </figure>''')
        elif kind == 'raw':
            body.append(item[1])
        else:
            raise ValueError(f'unknown body item: {kind}')

    schem = c.get('schematic')
    if schem:
        figure = f'''            <figure class="mech-schematic">
                <picture>
                    <source srcset="{schem['webp']}" type="image/webp">
                    <img src="{schem['png']}"
                         alt="{e(schem['alt'])}"
                         width="{schem['width']}" height="{schem['height']}" loading="eager" decoding="async">
                </picture>
                <figcaption>{e(schem['caption'])}</figcaption>
            </figure>
'''
    else:
        figure = ''

    lead = '\n'.join(f'                <p>{p}</p>' for p in c['lead'])

    page = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{GA_ID}');
    </script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{e(c['meta_description'])}">
    <meta name="keywords" content="{e(c['keywords'])}">
    <title>{e(c['title'])} | {site_links.SITE_NAME}</title>
    <link rel="canonical" href="{SITE}/{c['slug']}.html">
    <meta property="og:title" content="{e(c['title'])}">
    <meta property="og:description" content="{e(c['og_description'])}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{SITE}/{c['slug']}.html">
    <link rel="stylesheet" href="assets/css/style.css">
{site_links.FAVICON}
{_part(CSS)}
</head>
<body>

{site_links.header_html()}
    <div class="container">

        <p class="breadcrumb"><a href="index.html">Home</a> &rsaquo; <a href="mechs.html">Mechs</a> &rsaquo; {e(display)}</p>

        <div class="mech-hero">
            <h1>{e(display)}</h1>
            <p class="sub">{c['hero_sub']}</p>
            <div class="mech-hero-grid">
{figure}            <div class="verdict-box">
{lead}
            </div>
            </div>
        </div>

        {voice_note(ch, c)}

        <div class="mech-body">

            {NL.join(body)}

            <p class="srcnote">Stats on this page are generated directly from our variant database, which is reconciled against the Master Unit List for Battle Value, introduction dates and per-era faction availability. Alpha Strike damage values are the standard card figures. If you spot something wrong, <a href="mailto:DaveAsp81@gmail.com" style="color:#ff8c00;">tell me</a> and I will fix it.</p>

        </div>
    </div>

{_part(FOOTER)}

{faq_schema(c['faq_schema']) if c.get('faq_schema') else ''}

{_part(TRACKING).replace('__CHASSIS__', c['slug'])}

<script>
document.addEventListener('DOMContentLoaded', function() {{
    var toggle = document.querySelector('.nav-toggle');
    var navUl = document.querySelector('nav ul');
    if (toggle && navUl) {{
        toggle.addEventListener('click', function() {{
            navUl.classList.toggle('open');
        }});
    }}
}});
</script>
</body>
</html>
'''
    return site_links.clean_links(page)


# -------------------------------------------------------------- social output

TCO_LEN = 23
_URL_RE = re.compile(r'https?://\S+')


def billed_len(text):
    """Character count as X meters it: every link bills at a flat 23."""
    return len(_URL_RE.sub('x' * TCO_LEN, text))


def social_link(slug, source, content, campaign=None):
    campaign = campaign or f'mech-{slug}'
    return (f'{SITE}/{slug}?utm_source={source}&utm_medium=social'
            f'&utm_campaign={campaign}&utm_content={content}')


def split_for_x(text):
    """Split an X post into the main post and a first reply carrying the link.

    Posts with an external link in the body are reported to lose meaningful
    reach; putting the link in the first reply is the usual workaround. The
    posts end with a call to action and the URL on the last two lines, so
    both move to the reply and the main post goes out clean.

    Returns (post, reply). If no trailing URL is found the text is returned
    unchanged with no reply, so this can never mangle a post it does not
    understand.
    """
    lines = text.rstrip().split('\n')
    if not lines or not _URL_RE.fullmatch(lines[-1].strip()):
        return text, None
    url = lines[-1].strip()
    body = lines[:-1]
    # Take the call-to-action line with it when there is one, so the reply
    # reads as a sentence rather than a bare link.
    cta = ''
    while body and not body[-1].strip():
        body.pop()
    if body and body[-1].rstrip().endswith(':'):
        cta = body.pop().strip()
    while body and not body[-1].strip():
        body.pop()
    reply = f'{cta}\n{url}' if cta else url
    return '\n'.join(body).rstrip(), reply


def write_social(slug, social, limits):
    blocks = []
    for platform, text in social.items():
        is_x = platform.upper().startswith('X')
        post, reply = split_for_x(text) if is_x else (text, None)
        n = billed_len(post)
        limit = limits.get(platform)
        flag = f' [{n}/{limit}]' + (' OVER LIMIT' if n > limit else '') if limit else ''
        block = f'===== {platform}{flag} =====\n\n{post}\n'
        if reply:
            block += (f'\n  --- first reply (post this immediately after, '
                      f'{billed_len(reply)} chars) ---\n\n{reply}\n')
        blocks.append(block)
    path = OUT_DIR / f'{slug}-social.txt'
    path.write_text('\n'.join(blocks), encoding='utf-8')
    return path


# ------------------------------------------------------------------ self-test

def check(ch, c, page):
    p = []
    verdicts = c['verdicts']

    missing = [x['name'] for x in ch.rec['variants'] if x['name'] not in verdicts]
    if missing:
        p.append(f'variants with no verdict: {missing}')

    stale = [k for k in verdicts if k not in ch.variants]
    if stale:
        p.append(f'verdict keys not in data: {stale}')

    bad_tier = [k for k, (t, _) in verdicts.items() if t not in ASSIGNABLE_TIERS]
    if bad_tier:
        p.append(f'tier must be one of {ASSIGNABLE_TIERS} (trap is computed): {bad_tier}')

    rendered = {n for n in ch.variants if ch.verdict_for(n, verdicts)[0] == 'trap'}
    if rendered != set(ch.dominated):
        p.append(f'trap set mismatch: {sorted(rendered)} vs {sorted(ch.dominated)}')

    for n in ch.dominated:
        if f'beaten by {html.escape(ch.best_dominator(n), quote=True)}' not in page:
            p.append(f'trap {n} dominator not shown on the page')

    for var in ch.rec['variants']:
        if f'>{html.escape(var["name"], quote=True)}</td>' not in page:
            p.append(f'variant missing from table: {var["name"]}')

    eras = {x['era'] for x in ch.rec['variants']}
    uncovered = eras - set(ERA_ORDER)
    if uncovered:
        p.append(f'eras not in ERA_ORDER: {uncovered}')

    if '\u2014' in page:
        p.append('literal em dash in page')

    leftovers = site_links.audit(page)
    if leftovers:
        p.append(f'internal .html links survived cleaning: {leftovers}')

    if 'href="/mechs"' not in page:
        p.append('no link to the mech guides index')

    if 'tool_handoff' not in page:
        p.append('click tracking script missing')

    # Voice drift, in either direction. Writing a Clan page and an Inner
    # Sphere one back to back is exactly when this happens: the two
    # registers are close enough that a rewrite of one bleeds into the
    # other. Caught this happening on the Ostroc page once already.
    try:
        art_body = page[page.index('<div class="mech-hero">'):page.index('class="srcnote"')]
    except ValueError:
        art_body = page
    body_txt = re.sub(r'<[^>]+>', ' ', art_body)

    # Vocabulary that only belongs to the Clan technician: caste, touman,
    # Trial-speak, "Aff" for yes. Specific enough that it will not collide
    # with ordinary Inner Sphere prose, which mentions "the Clans" and
    # "Clan technology" constantly without ever using these.
    CLAN_TELLS = ('touman', 'the technician caste', 'Clan technician',
                  ' Aff,', ' Aff.')
    # The MechTech's hedges and asides: first person, opinionated, warm.
    # Every Inner Sphere/Mixed page written so far hits at least one of
    # these somewhere in the article body.
    MECHTECH_TELLS = ('I think', 'I would', 'I have', 'I like', 'I enjoy',
                       'I find', 'I actually', 'I recall', 'I swear',
                       'I still', 'I reckon', 'gets me', 'in the bay')

    if ch.rec.get('technology') == 'Clan':
        if 'voice-note' not in page:
            p.append('Clan chassis with no voice note')
        for tell in ('in the bay', 'in my bay', 'signed one out'):
            if tell in body_txt:
                p.append(f'Clan page uses Inner Sphere MechTech phrasing: "{tell}"')
    else:
        # Inner Sphere and Mixed chassis keep the MechTech. Flag Clan
        # vocabulary bleeding in, and flag the MechTech's voice going
        # missing entirely, which is what happened when the Ostroc got
        # written right after a Clan page and came out half-technician.
        for tell in CLAN_TELLS:
            if tell in body_txt:
                p.append(f'Inner Sphere page uses Clan-voice phrasing: "{tell.strip()}"')
        if not any(t in body_txt for t in MECHTECH_TELLS):
            p.append('Inner Sphere page has none of the MechTech\'s usual '
                     'first-person asides — check it has not drifted '
                     'into the Clan register')

    # Unrendered placeholders. A doubled brace in a chassis module's prose
    # renders a literal {name} instead of the value, and the page still looks
    # plausible enough to ship. This caught 13 of them across three pages.
    # Only the article body is checked: CSS and JS legitimately use braces.
    try:
        body = page[page.index('<div class="mech-hero">'):page.index('<p class="srcnote">')]
    except ValueError:
        body = page
    stray = re.findall(r'\{[A-Za-z_][A-Za-z0-9_]*(?:\s*[*+-]\s*\d+)?\}'
                       r'|\{ctx\.[^}]*\}', body)
    if stray:
        p.append(f'unrendered placeholders in the page body: {sorted(set(stray))}')

    for tag in ('div', 'p', 'table', 'tr', 'td', 'span', 'figure'):
        o = len(re.findall('<' + tag + '[ >]', page))
        cl = len(re.findall('</' + tag + '>', page))
        if o != cl:
            p.append(f'tag imbalance {tag}: {o} open, {cl} close')

    for platform, text in c.get('social', {}).items():
        limit = c.get('social_limits', {}).get(platform)
        measured = (split_for_x(text)[0] if platform.upper().startswith('X')
                    else text)
        if limit and billed_len(measured) > limit:
            p.append(f'{platform} post is {billed_len(measured)} billed chars, '
                     f'limit {limit}')
        if '\u2014' in text:
            p.append(f'em dash in {platform} post')
        post, reply = (split_for_x(text) if platform.upper().startswith('X')
                       else (text, None))
        whole = post + (reply or '')
        if f'{SITE}/{c["slug"]}' not in whole:
            p.append(f'no link in {platform} post')
        if 'utm_source=' not in whole:
            p.append(f'untagged link in {platform} post')
        if platform.upper().startswith('X') and reply is None:
            p.append(f'{platform}: no trailing link found to move to a reply')
        if platform.upper().startswith('X') and 'http' in post:
            p.append(f'{platform}: a link is still in the main post body')

    return p


def divergences(page, social):
    """Near-identical sentences in the page and the social copy that differ.

    The two duplicate a lot of claims on purpose, because they should read
    differently. The risk is fixing a fact in one and not the other, which
    has happened three times. Reported, never fatal.
    """
    def sents(t):
        t = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', t))
        return [x.strip() for x in re.split(r'(?<=[.!?]) ', t)
                if 40 < len(x.strip()) < 300]
    try:
        body = page[page.index('<div class="mech-hero">'):page.index('class="srcnote"')]
    except ValueError:
        body = page
    ps = sents(body)
    out = []
    for a in sents('\n'.join(social.values())):
        m = difflib.get_close_matches(a, ps, n=1, cutoff=0.80)
        if m and m[0] != a:
            r = difflib.SequenceMatcher(None, a, m[0]).ratio()
            if r < 0.99:
                out.append((round(r, 2), a, m[0]))
    return sorted(out, reverse=True)
