#!/usr/bin/env python3
"""
Builds mechs.html (the chassis guide index) and patches index.html so the
guides are reachable from the home page.

Adding a new chassis guide means adding one entry to GUIDES below and
re-running this. Nothing else on the site needs touching.

Usage: python3 build_mech_index.py
Outputs to /mnt/user-data/outputs/for-site/
"""

import html
import json
import re
from pathlib import Path

import site_links

# Build from the pristine homepage every time, never from the deployed copy.
# Every change this script makes is a patch it applies itself, so starting
# clean is deterministic: patching an already-patched file is how the page
# ended up with six copies of the same CSS block.
#
# IMPORTANT: this file is the source of truth for the home page. Hand edits
# made to the deployed index.html will be lost on the next build.
SRC_INDEX = Path('/mnt/user-data/uploads/index.html')
OUT_DIR = Path('/mnt/user-data/outputs/for-site')
GA_ID = 'G-T2794K8B9W'

# ---------------------------------------------------------------- the guides
# One entry per published chassis page. Order here is display order.

FEATURE_TPL = (Path(__file__).with_name('_home_feature.html')
               .read_text(encoding='utf-8'))

GUIDES = [
    {
        'chassis': 'Marauder',
        'href': 'marauder.html',
        'tons': 75,
        'tech': 'Inner Sphere',
        'variants': 36,
        'image': 'assets/images/marauder-schematic.png',
        'image_webp': 'assets/images/marauder-schematic.webp',
        'blurb': ('The most recognisable heavy in the game, and the one most '
                  'people play wrong. Every variant ranked, the heat maths '
                  'behind the 3R, and how to kill one.'),
        'hook': 'Why the 3R cannot fire its own main guns two turns running',
    },
    {
        'chassis': 'Warhammer',
        'href': 'warhammer.html',
        'tons': 70,
        'tech': 'Inner Sphere',
        'variants': 31,
        'image': 'assets/images/warhammer-card.webp',
        'image_webp': 'assets/images/warhammer-card.webp',
        'blurb': ('Designed in 2515 and still in service in the ilClan era. '
                  'Every variant ranked, the heat maths, and why nobody ever '
                  'managed to replace the original.'),
        'hook': 'Why the 2515 original outlasted every improvement',
    },
    {
        'chassis': 'Atlas',
        'href': 'atlas.html',
        'tons': 100,
        'tech': 'Inner Sphere',
        'variants': 28,
        'image': 'assets/images/atlas-schematic.webp',
        'image_webp': 'assets/images/atlas-schematic.webp',
        'blurb': ('Every Atlas carries the same armour. What changes is what '
                  'sits underneath, and half the modern fits give away the '
                  'one quality the design exists for.'),
        'hook': 'Why the engine matters more than the guns',
    },
    {
        'chassis': 'Locust',
        'href': 'locust.html',
        'tons': 20,
        'tech': 'Inner Sphere',
        'variants': 24,
        'image': 'assets/images/locust-schematic.webp',
        'image_webp': 'assets/images/locust-schematic.webp',
        'blurb': ('Nobody wanted to pilot one and everybody fielded one '
                  'anyway. Every variant ranked, and why the cheapest mech '
                  'in the game outlasted almost everything.'),
        'hook': 'Why economics kept it alive for six centuries',
    },
    {
        'chassis': 'Highlander',
        'href': 'highlander.html',
        'tons': 90,
        'tech': 'Inner Sphere',
        'variants': 13,
        'image': 'assets/images/highlander-schematic.webp',
        'image_webp': 'assets/images/highlander-schematic.webp',
        'blurb': ('Pilots invented death from above during the trial runs, '
                  'and the designers went back and reinforced the legs so '
                  'they could keep doing it. Every variant ranked.'),
        'hook': 'How a misuse became a factory feature',
    },
    {
        'chassis': 'BattleMaster',
        'href': 'battlemaster.html',
        'tons': 85,
        'tech': 'Inner Sphere',
        'variants': 32,
        'image': 'assets/images/battlemaster-schematic.webp',
        'image_webp': 'assets/images/battlemaster-schematic.webp',
        'blurb': ('It holds its PPC like a rifle and can throw it away. '
                  'Every variant ranked, plus the ComStar filing error that '
                  'armed the Draconis Combine by accident.'),
        'hook': 'The command mech with weak head armour',
    },
    {
        'chassis': 'Bushwacker',
        'href': 'bushwacker.html',
        'tons': 55,
        'tech': 'Inner Sphere',
        'variants': 6,
        'image': 'assets/images/bushwacker-schematic.webp',
        'image_webp': 'assets/images/bushwacker-schematic.webp',
        'blurb': ('A failed design, saved by schematics stolen from Clan '
                  'Jade Falcon. Every variant ranked, and why the low '
                  'profile nearly killed it.'),
        'hook': 'The mech the Clans accidentally rescued',
    },
    {
        'chassis': 'Axman',
        'href': 'axman.html',
        'tons': 65,
        'tech': 'Inner Sphere',
        'variants': 8,
        'image': 'assets/images/axman-schematic.webp',
        'image_webp': 'assets/images/axman-schematic.webp',
        'blurb': ('Built as a symbol of Federated Commonwealth unity, and '
                  'the variant list records that union coming apart. Plus '
                  'five tonnes of hatchet.'),
        'hook': 'A symbol of unity, and what happened to it',
    },
    {
        'chassis': 'Timber Wolf (Mad Cat)',
        'href': 'timber-wolf.html',
        'tons': 75,
        'tech': 'Clan OmniMech',
        'variants': 20,
        'image': 'assets/images/timber-wolf-schematic.webp',
        'image_webp': 'assets/images/timber-wolf-schematic.webp',
        'blurb': ('Named after a targeting computer that could not decide '
                  'between a Marauder and a Catapult. Every configuration '
                  'ranked, and what an OmniMech actually changes.'),
        'hook': 'The machine that broke Inner Sphere planning',
    },
    {
        'chassis': 'Ostroc',
        'href': 'ostroc.html',
        'tons': 60,
        'tech': 'Inner Sphere',
        'variants': 15,
        'image': 'assets/images/ostroc-schematic.webp',
        'image_webp': 'assets/images/ostroc-schematic.webp',
        'blurb': ('Rare because the factory was small, rarer once it was '
                  'destroyed, then passed over for upgrades because it was '
                  'rare. Every variant ranked.'),
        'hook': 'The mech that got skipped, and why',
    },
    {
        'chassis': 'Thunderbolt',
        'href': 'thunderbolt.html',
        'tons': 65,
        'tech': 'Mixed',
        'variants': 30,
        'image': 'assets/images/thunderbolt-schematic.webp',
        'image_webp': 'assets/images/thunderbolt-schematic.webp',
        'blurb': ('The oldest mech on the site, built by a nation with no '
                  'BattleMech experience, and famous for one very specific '
                  'piece of advice: park it in a lake.'),
        'hook': 'The design old enough to duel its own replacement',
    },
    {
        'chassis': 'Enforcer',
        'href': 'enforcer.html',
        'tons': 50,
        'tech': 'Inner Sphere',
        'variants': 5,
        'image': 'assets/images/enforcer-schematic.webp',
        'image_webp': 'assets/images/enforcer-schematic.webp',
        'blurb': ('A flaw its own engineers tried to fix and gave up on, '
                  'left broken on purpose. Every variant ranked, and the '
                  'unbuilt Star League design it was built from.'),
        'hook': 'The fix that was worse than the flaw',
    },
]

# Chassis with a page planned but not published yet. Shown greyed out so the
# index does not look like a one-item shelf. Delete an entry once it ships.
COMING = ['Awesome', 'Catapult', 'Rifleman']

# A published guide left behind in COMING is exactly how Thunderbolt ended up
# listed as "coming soon" directly beneath its own real card: caught by eye
# once, then silently reintroduced because nothing checked it automatically.
# A single-line grep for "^COMING" also missed the bug the first time round,
# since the list wraps onto a second line -- check the parsed value instead.
_published = {g['chassis'].split(' (')[0] for g in GUIDES}
_stale = sorted(_published & set(COMING))
if _stale:
    raise RuntimeError(
        f'COMING lists {_stale}, which already has a published guide in '
        f'GUIDES. Remove it from COMING before building.')


def e(x):
    return html.escape(str(x), quote=True)


# ----------------------------------------------------------- shared fragments

HEADER = site_links.header_html()


def guide_card(g, linked=True):
    """A card in the home page articles-grid style, so it looks native."""
    img = (f'<div class="article-card-image mech-card-image" '
           f'style="background-image: url(\'{e(g["image"])}\');"></div>')
    if linked:
        cta = f'<a href="{e(g["href"])}" class="read-more">Read More &rarr;</a>'
    else:
        cta = '<span class="read-more" style="color:#666;">Coming soon</span>'
    return f'''            <div class="article-card">
                {img}
                <div class="article-card-content">
                    <h3>{e(g["chassis"])}</h3>
                    <p class="mech-card-meta">{e(g["tons"])} tons &middot; {e(g["tech"])} &middot; {e(g["variants"])} variants</p>
                    <p>{e(g["blurb"])}</p>
                    {cta}
                </div>
            </div>'''


# ------------------------------------------------------------- mechs.html

def build_index_page():
    cards = '\n'.join(guide_card(g) for g in GUIDES)
    coming = '\n'.join(
        f'                <li>{e(c)}</li>' for c in COMING
    )
    n = len(GUIDES)
    return f'''<!DOCTYPE html>
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
    <meta name="description" content="In-depth BattleTech chassis guides. Every variant ranked with Battle Value, Alpha Strike stats and per-era faction availability, plus how each mech actually plays on the table.">
    <meta name="keywords" content="BattleTech mech guide, best variant, BattleMech chassis guide, Battle Value, Alpha Strike stats">
    <title>Mech Guides: Every Variant Ranked | BattleTech HQ</title>
    <link rel="canonical" href="https://battletechhq.com/mechs.html">
    <link rel="stylesheet" href="assets/css/style.css">
{site_links.FAVICON}
    <style>
        .site-search {{
            display: flex;
            gap: 10px;
            max-width: 620px;
            margin: 0 0 30px;
        }}
        .site-search input {{
            flex: 1;
            background: #141414;
            border: 1px solid #2a2a2a;
            border-left: 3px solid #ff8c00;
            border-radius: 8px;
            color: #e8e8e8;
            font-family: 'Rajdhani', sans-serif;
            font-size: 1rem;
            padding: 11px 14px;
            outline: none;
        }}
        .site-search input:focus {{ border-color: #ff8c00; }}
        .site-search input::placeholder {{ color: #666; }}
        .site-search button {{
            background: rgba(255,140,0,0.12);
            border: 1px solid rgba(255,140,0,0.45);
            color: #ff8c00;
            border-radius: 8px;
            padding: 0 20px;
            font-family: 'Rajdhani', sans-serif;
            font-weight: 600;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            font-size: 0.82rem;
            cursor: pointer;
        }}
        .site-search button:hover {{ background: rgba(255,140,0,0.2); }}
        .mech-card-image {{
            background-color: #0d0d0d;
            background-size: contain;
            background-repeat: no-repeat;
            background-position: center;
        }}
        .mech-card-meta {{
            font-family: 'Rajdhani', sans-serif;
            font-size: 0.75rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: #ff8c00;
            margin-bottom: 10px !important;
        }}
        .mech-intro {{ color: #c8c8c8; line-height: 1.8; max-width: 820px; margin-bottom: 8px; }}
        .coming-soon {{
            background: rgba(20,20,20,0.98);
            border: 1px solid #2a2a2a;
            border-radius: 8px;
            padding: 24px 28px;
            margin: 40px 0;
        }}
        .coming-soon h3 {{ color: #ff8c00; margin: 0 0 12px; font-size: 1.05rem; }}
        .coming-soon ul {{
            list-style: none;
            padding: 0;
            margin: 0;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .coming-soon li {{
            background: rgba(255,140,0,0.08);
            border: 1px solid rgba(255,140,0,0.25);
            color: #aa8855;
            padding: 5px 14px;
            border-radius: 20px;
            font-family: 'Rajdhani', sans-serif;
            font-size: 0.82rem;
            font-weight: 600;
            letter-spacing: 0.04em;
        }}
        .coming-soon p {{ color: #888; font-size: 0.88rem; margin: 14px 0 0; line-height: 1.6; }}
    </style>
</head>
<body>

{HEADER}
    <section class="hero">
        <h1>Mech Guides</h1>
        <p>Every variant ranked, with the numbers behind each call.<br>
        Not just what a mech is, but how it actually plays.</p>
    </section>

    <div class="container">

        <p class="mech-intro">Stat blocks are easy to find. What is harder to find is someone telling you which variant is worth the Battle Value, which one is a trap, and what happens when the thing you are piloting runs out of heat sinks halfway through turn three.</p>
        <p class="mech-intro">That is what these are. Every guide covers the full variant list with Battle Value and Alpha Strike figures, per-era faction availability off the Master Unit List, how to pilot the chassis, how to kill one, and how our <a href="opfor-command.html" style="color:#ff8c00;">AI opponent</a> handles it in a solo game.</p>
        <p class="mech-intro">Every variant gets a verdict. If you want to know exactly what those verdicts mean and how the Trap rating is calculated, <a href="rating-scale.html" style="color:#ff8c00;">the rating scale is written down here</a>.</p>

        <form class="site-search" action="search.html" method="get" role="search">
            <input type="search" name="q" placeholder="Search the whole site" aria-label="Search the site" autocomplete="off">
            <button type="submit">Search</button>
        </form>

        <div class="articles-grid" style="margin-top:36px;">
{cards}
        </div>

        <div class="coming-soon">
            <h3>Next up</h3>
            <ul>
{coming}
            </ul>
            <p>New chassis guides go up regularly. If there is one you want moved to the front of the queue, <a href="mailto:DaveAsp81@gmail.com" style="color:#ff8c00;">let me know</a>.</p>
        </div>

    </div>

    <footer>
        <div class="footer-content">
            <div class="footer-section">
                <h4>About BattleTech HQ</h4>
                <p>Home of the <a href="https://www.youtube.com/@DaveAsp81" target="_blank" style="color:#ff8c00;">BattleTech Down Under</a> YouTube channel. Guides, tools, and opinions for the modern MechWarrior.</p>
            </div>
            <div class="footer-section">
                <h4>Quick Links</h4>
                <ul>
                    <li><a href="lance-builder.html">Lance Builder</a></li>
                    <li><a href="mechs.html">Mech Guides</a></li>
                    <li><a href="guides.html">All Guides &amp; Articles</a></li>
                    <li><a href="search.html">Search</a></li>
                    <li><a href="rating-scale.html">Rating Scale</a></li>
                    <li><a href="game-tracker.html">Game Tracker</a></li>
                    <li><a href="opfor-command.html">OpFor Command</a></li>
                    <li><a href="campaign.html">Campaign Tracker</a></li>
                    <li><a href="paint-tool.html">Paint Tool</a></li>
                    <li><a href="articles/battletech-beginner-guide.html">Beginner Guide</a></li>
                    <li><a href="privacy.html">Privacy Policy</a></li>
                    <li><a href="affiliate-disclosure.html">Affiliate Disclosure</a></li>
                    <li><a href="image-credits.html">Image Credits</a></li>
                </ul>
            </div>
            <div class="footer-section">
                <h4>Resources</h4>
                <ul>
                    <li><a href="https://www.sarna.net" target="_blank">Sarna.net &mdash; BattleTech Wiki</a></li>
                    <li><a href="https://store.catalystgamelabs.com" target="_blank">Catalyst Game Labs</a></li>
                    <li><a href="https://battletech.com" target="_blank">Official BattleTech</a></li>
                    <li><a href="https://megamek.games" target="_blank">MegaMek &mdash; Free Digital BT</a></li>
                </ul>
            </div>
        </div>
        <div class="footer-bottom">
            <p style="margin-bottom:16px;"><a class="bmc-button" href="https://buymeacoffee.com/daveasp" target="_blank" rel="noopener">&#9749; Buy me a coffee</a></p>
            <p>&copy; 2026 BattleTech HQ. Unofficial fansite. BattleTech is a registered trademark of Topps Company, Inc.</p>
            <p class="affiliate-note">As an Amazon Associate I earn from qualifying purchases.</p>
        </div>
    </footer>

<script>
/* Which guide cards actually get clicked, so the index earns its place. */
(function () {{
    document.addEventListener('click', function (ev) {{
        var el = ev.target;
        if (!el || typeof el.closest !== 'function') return;
        var card = el.closest('.article-card');
        if (!card) return;
        var a = card.querySelector('a[href]');
        if (!a) return;
        var h3 = card.querySelector('h3');
        if (typeof gtag !== 'function') return;
        try {{
            gtag('event', 'guide_click', {{
                chassis: (h3 ? h3.textContent : 'unknown').toLowerCase(),
                source: 'mech-index'
            }});
        }} catch (err) {{ /* never block */ }}
    }}, true);
}})();
</script>

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


# --------------------------------------------------------- index.html patch

def patch_home(src):
    """Three surgical edits. Each is checked so a silent miss is impossible."""
    applied = []

    # 1. Replace the home page nav wholesale with the shared six-item one.
    #    Adding a Mech Guides item to the existing ten made it wrap harder;
    #    the fix is fewer items, not one more.
    nav_block = re.search(r'<nav>\s*<ul>.*?</ul>\s*</nav>', src, re.S)
    if not nav_block:
        raise RuntimeError('nav block not found in index.html')
    shared = '<nav>\n                <ul>\n' + site_links.nav_html(20) + '\n                </ul>\n            </nav>'
    src = src.replace(nav_block.group(0), shared, 1)
    applied.append(f'nav: replaced {nav_block.group(0).count("<li>")} items with '
                   f'{len(site_links.NAV)}')

    # 2. New home page section, placed ahead of Gameplay & Strategy.
    #    One large featured card that shuffles client-side on each load, so
    #    the homepage stays fresh as the series outgrows a card grid. The
    #    first guide is rendered server-side: that is what search engines
    #    index and what shows with JavaScript off. Every guide also keeps a
    #    link in the row underneath, so the shuffle costs none of them an
    #    internal link.
    gameplay = '        <div class="section-divider" id="gameplay">'
    if gameplay not in src:
        raise RuntimeError('gameplay section-divider not found in index.html')

    first = GUIDES[0]
    payload = json.dumps([{
        'href': g['href'], 'chassis': g['chassis'], 'tons': g['tons'],
        'tech': g['tech'], 'variants': g['variants'],
        'image': g['image'], 'blurb': g['blurb'],
    } for g in GUIDES], separators=(',', ':'))

    others = ' &middot; '.join(
        '<a href="{}">{}</a>'.format(e(g['href']), e(g['chassis']))
        for g in GUIDES)

    section = FEATURE_TPL
    for key, val in (
        ('__HREF__', e(first['href'])),
        ('__IMAGE__', e(first['image'])),
        ('__CHASSIS__', e(first['chassis'])),
        ('__META__', '{} tons &middot; {} &middot; {} variants'.format(
            e(first['tons']), e(first['tech']), e(first['variants']))),
        ('__BLURB__', e(first['blurb'])),
        ('__OTHERS__', others),
        ('__DATA__', payload),
    ):
        section = section.replace(key, val)

    if 'id="mechs"' in src:
        # Already present from a previous run: replace it rather than adding
        # a second copy.
        i = src.index('<div class="section-divider" id="mechs">')
        j = src.index(gameplay, i)
        src = src[:i] + section + src[j:]
        applied.append(f'home: featured card refreshed, {len(GUIDES)} in rotation')
    else:
        src = src.replace(gameplay, section + gameplay, 1)
        applied.append(f'home: featured card added, {len(GUIDES)} in rotation')

    # 3. Footer quick links, inserted after whatever is already there so a
    #    second run does not duplicate them.
    for link, label in (('mechs.html', 'Mech Guides'),
                        ('guides.html', 'All Guides &amp; Articles'),
                        ('search.html', 'Search')):
        entry = f'                    <li><a href="{link}">{label}</a></li>\n'
        if f'"{link}"' in src.split('<footer')[-1]:
            continue
        anchor = '                    <li><a href="game-tracker.html">Game Tracker</a></li>\n'
        if anchor in src:
            src = src.replace(anchor, entry + anchor, 1)
            applied.append(f'footer: added {label}')
        else:
            applied.append(f'footer: anchor missing, {label} SKIPPED')

    # 4. Styles for the new cards, appended to the existing page <style> block.
    style_close = '    </style>'
    extra = '''
        .section-more {
            margin: 4px 0 50px;
            font-family: 'Rajdhani', sans-serif;
            letter-spacing: 0.03em;
        }
        .section-more a {
            color: #ff8c00;
            text-decoration: none;
            font-weight: 600;
        }
        .section-more a:hover { text-decoration: underline; }

        /* Featured mech guide card, shuffled on load */
        .mech-feature {
            display: flex;
            gap: 0;
            background: rgba(20,20,20,0.98);
            border: 1px solid #2a2a2a;
            border-left: 3px solid #ff8c00;
            border-radius: 10px;
            overflow: hidden;
            text-decoration: none;
            margin-bottom: 18px;
            transition: border-color 0.2s, background 0.2s;
        }
        .mech-feature:hover {
            border-color: #ff8c00;
            background: rgba(255,140,0,0.05);
        }
        .mech-feature-img {
            flex: 0 0 230px;
            background-color: #0d0d0d;
            background-size: contain;
            background-repeat: no-repeat;
            background-position: center;
            min-height: 250px;
        }
        .mech-feature-body { padding: 26px 30px; flex: 1; }
        .mech-feature-tag {
            font-family: 'Rajdhani', sans-serif;
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #ff8c00;
            border: 1px solid rgba(255,140,0,0.45);
            border-radius: 20px;
            padding: 3px 12px;
        }
        .mech-feature-body h3 {
            color: #fff;
            font-size: 1.7rem;
            margin: 14px 0 6px;
        }
        .mech-feature-meta {
            font-family: 'Courier New', monospace;
            font-size: 0.8rem;
            color: #8a8a8a;
            margin: 0 0 14px !important;
        }
        .mech-feature-body p { color: #c8c8c8; line-height: 1.7; }
        .mech-feature-all {
            color: #888;
            font-size: 0.92rem;
            margin: 0 0 50px;
        }
        .mech-feature-all a { color: #ff8c00; text-decoration: none; }
        .mech-feature-all a:hover { text-decoration: underline; }
        @media (max-width: 700px) {
            .mech-feature { flex-direction: column; }
            .mech-feature-img { flex: 0 0 200px; min-height: 200px; }
            .mech-feature-body { padding: 22px; }
        }

        /* Mech guide cards */
        .mech-card-image {
            background-color: #0d0d0d;
            background-size: contain;
            background-repeat: no-repeat;
            background-position: center;
        }
        .mech-card-meta {
            font-family: 'Rajdhani', sans-serif;
            font-size: 0.75rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: #ff8c00;
            margin-bottom: 10px !important;
        }
'''
    if '/* Featured mech guide card' in src:
        applied.append('home: card styles already present, skipped')
    elif style_close in src:
        src = src.replace(style_close, extra + style_close, 1)
        applied.append('home: added card styles')
    else:
        applied.append('home: style block not found, SKIPPED')

    # 5. Claims that will not survive contact with someone who knows the
    #    hobby. MegaMekLab and the MUL force builder both exist.
    sup = 'only dedicated BattleTech lance builder on the web'
    if sup in src:
        src = src.replace(sup, 'lance builder built for the table, not the wiki', 1)
        applied.append('home: softened the lance builder superlative')

    # 6. Dead link: the official site moved off bg.battletech.com.
    if 'https://bg.battletech.com' in src:
        src = src.replace('https://bg.battletech.com', 'https://battletech.com')
        applied.append('home: fixed the official BattleTech link')

    # 7. Brand: the domain is battletechhq.com and OpFor's own title already
    #    says HQ. One name, and it is the one that matches the URL.
    n_brand = src.count('BattleTech Hub')
    if n_brand:
        src = src.replace('BattleTech Hub', site_links.SITE_NAME)
        applied.append(f'home: renamed {n_brand} brand strings to '
                       f'{site_links.SITE_NAME}')

    # 8. Favicon. It 404s at the moment, which is free brand thrown away.
    if 'rel="icon"' not in src:
        anchor = '    <link rel="stylesheet"'
        if anchor in src:
            src = src.replace(anchor, site_links.FAVICON + '\n' + anchor, 1)
            applied.append('home: added favicon markup')
        else:
            applied.append('home: stylesheet anchor not found, favicon SKIPPED')

    # 9. The wordmark emoji wraps onto a second line on narrow screens.
    src = src.replace('class="logo">\u2694\ufe0f ', 'class="logo">')

    # 10. Slim the topic sections and point them at the articles index.
    #     All 25 articles used to live only on this page.
    import build_guides_index as guides
    src, guide_changes = guides.slim_home(src)
    applied.extend(guide_changes)

    # 11. Remove the emoji from the remaining section headings.
    before_emoji = len(re.findall(r'<h2>[^\x00-\x7F]', src))
    src = re.sub(r'(<h2>)[^\x00-\x7F\s]+\s*', r'\1', src)
    if before_emoji:
        applied.append(f'home: removed emoji from {before_emoji} headings')

    return src, applied


# ------------------------------------------------------------------- run

OUT_DIR.mkdir(parents=True, exist_ok=True)

index_page = site_links.clean_links(build_index_page())
(OUT_DIR / 'mechs.html').write_text(index_page, encoding='utf-8')

home_src = SRC_INDEX.read_text(encoding='utf-8')
patched, applied = patch_home(home_src)
(OUT_DIR / 'index.html').write_text(patched, encoding='utf-8')

print(f'Wrote {OUT_DIR / "mechs.html"} ({len(index_page):,} bytes)')
print(f'Wrote {OUT_DIR / "index.html"} ({len(patched):,} bytes, '
      f'was {len(home_src):,})')
print()
for a in applied:
    print('  ', a)

# ------------------------------------------------------------- self-test
problems = []

for g in GUIDES:
    if g['href'] not in patched:
        problems.append(f'home page does not link {g["href"]}')
    clean = site_links.clean_links(f'href="{g["href"]}"')
    if clean not in index_page:
        problems.append(f'mechs.html does not link {g["href"]} (as {clean})')

if 'mechs.html' not in patched:
    problems.append('home page does not link mechs.html')

if '<a href="/mechs">Mech Guides</a>' not in patched:
    problems.append('nav item missing from patched index.html')

# The nav uses the clean form, the section and footer still use .html on this
# page because the rest of index.html does. Count both.
mech_links = patched.count('"mechs.html"') + patched.count('"/mechs"')
if mech_links < 3:
    problems.append(f'expected nav, section and footer links to the guides '
                    f'index, found {mech_links}')

# Tag balance on the patched home page, so a bad splice is caught here.
for tag in ('div', 'p', 'ul', 'li'):
    o = len(re.findall(r'<' + tag + r'[ >]', patched))
    c = len(re.findall(r'</' + tag + '>', patched))
    if o != c:
        problems.append(f'index.html tag imbalance: {tag} {o} open, {c} close')

for tag in ('div', 'p', 'ul', 'li'):
    o = len(re.findall(r'<' + tag + r'[ >]', index_page))
    c = len(re.findall(r'</' + tag + '>', index_page))
    if o != c:
        problems.append(f'mechs.html tag imbalance: {tag} {o} open, {c} close')

leftovers = site_links.audit(index_page)
if leftovers:
    problems.append(f'internal .html links in mechs.html: {leftovers}')

if '\u2014' in index_page:
    problems.append('literal em dash in mechs.html')

print()
if problems:
    print('PROBLEMS:')
    for p in problems:
        print('  -', p)
else:
    print('All checks passed.')

# ------------------------------------------------------- sitemap completeness

def sync_sitemap(sitemap_path='/mnt/user-data/outputs/for-site/sitemap.xml'):
    """Every published guide gets a sitemap entry, checked against the full
    GUIDES list rather than trusted from a running tally of "entries added so
    far". The latter is exactly how Atlas and Locust went missing: both
    shipped before per-chassis sitemap patching became a habit, and nothing
    ever re-checked the old entries against the current guide list.

    Safe to call every build: existing entries are left untouched, only
    genuinely missing slugs get appended.
    """
    import datetime
    import re
    import xml.etree.ElementTree as ET
    from pathlib import Path

    path = Path(sitemap_path)
    if not path.exists():
        return []
    s = path.read_text(encoding='utf-8')
    expected = {g['href'].replace('.html', '') for g in GUIDES}
    present = set(re.findall(r'battletechhq\.com/([a-z-]+)<', s))
    missing = sorted(expected - present)
    if not missing:
        return []
    today = datetime.date.today().isoformat()
    for slug in missing:
        entry = (f'  <url>\n    <loc>https://battletechhq.com/{slug}</loc>\n'
                f'    <lastmod>{today}</lastmod>\n    <changefreq>monthly</changefreq>\n'
                f'    <priority>0.8</priority>\n  </url>\n')
        s = s.replace('</urlset>', entry + '</urlset>')
    ET.fromstring(s)  # fail loudly on malformed XML rather than write it
    path.write_text(s, encoding='utf-8')
    return missing

_sitemap_gaps = sync_sitemap()
if _sitemap_gaps:
    print(f'sitemap: backfilled missing entries for {", ".join(_sitemap_gaps)}')
