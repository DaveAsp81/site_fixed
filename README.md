# BattleTech Hub

**battletechhq.com** — A BattleTech fan resource built by Dave (BloodAsp_NS), host of [BattleTech Down Under](https://www.youtube.com/@BattleTechDownUnder) on YouTube.

---

## What This Is

A BattleTech fan site covering lore, hobby guides, and tools for tabletop players. Built because the resource I wanted didn't exist — somewhere that explained the game clearly, covered the universe in proper depth, and had tools that actually worked.

---

## Site Structure

```
/
├── index.html                  # Homepage
├── lance-builder.html          # Lance Command Console (main tool)
├── paint-tool.html             # Paint Scheme Planner
├── about.html                  # About page
├── mechs.json                  # Mech database (620 chassis, 3700+ variants)
├── megamek_sync.py             # Database sync script (local use only)
│
├── articles/                   # All content articles
│   ├── battletech-beginner-guide.html
│   ├── battletech-lore-explained.html
│   ├── star-league.html
│   ├── succession-wars-deep-dive.html
│   ├── clan-invasion.html
│   ├── jihad-deep-dive.html
│   ├── great-houses-guide.html
│   ├── faction-color-schemes.html
│   ├── megamek-guide.html
│   ├── lance-builder-update.html
│   └── ... (19 articles total)
│
└── assets/
    ├── css/
    │   └── style.css
    └── images/
        ├── articles/           # Article hero images
        ├── mechs/              # Mech images (sourced from ImgBB via MUL API)
        │   └── paint/          # Miniature photos for paint tool
        └── factions/           # Faction logo assets
```

---

## The Lance Builder

The main tool. Built from:
- **MegaMek MTF files** — every published BattleMech chassis and variant
- **Master Unit List API** — faction availability, BV2, Point Values, era data
- **620 chassis / 3,700+ variants** with full fluff text (overview, capabilities, deployment notes)

Features:
- Faction and era filters
- Classic BV2 and Alpha Strike PV tracking (skill-adjusted)
- Clan Star support (5-unit formation, Clan terminology throughout)
- Pilot name generator (IS: full name + callsign, Clan: warrior name + Bloodname chance)
- MegaMek .mul export
- Quick-gen lance/star
- Save, print, CSV export

**Updating the database:** Run `megamek_sync.py` locally when MegaMek releases updates. The script checks the MegaMek GitHub for changes to MTF files, re-fetches BV/faction data from the MUL API, and merges into `mechs.json` while preserving manually written fluff text.

---

## The Paint Scheme Planner

Colour scheme planning tool at `paint-tool.html`:
- HSL colour wheel with brightness control
- 6 colour zones: primary armour, secondary armour, trim, weapons, cockpit, heat vents
- 12 faction presets (Great Houses + major Clans)
- Automatic Citadel and Vallejo paint name matching
- Share schemes via URL (zones encoded as query parameters)

The faction colour schemes article (`articles/faction-color-schemes.html`) links directly to the planner with each faction's colours pre-loaded.

---

## Content

### Lore Series
Full deep-dive articles on each era:
- **Star League** — Ian Cameron's empire, the Reunification War, Amaris coup, Kerensky's Exodus
- **Succession Wars** — Three centuries of self-destruction, LosTech, ComStar's rise
- **Clan Invasion** — Operation Revival, the five invading Clans, Tukayyid, destruction of Clan Smoke Jaguar
- **The Jihad** — Word of Blake holy war, Manei Domini, Devlin Stone, liberation of Terra

### Guides
Beginner guide, lance building, Alpha Strike vs Classic, BattleTech vs Warhammer, heat management, MegaMek, buying guides, painting tutorials, terrain building.

---

## Data Sources & Credits

- **'Mech data:** [MegaMek](https://megamek.games) MTF files (open source, GPL)
- **BV / faction availability:** [Master Unit List](https://masterunitlist.info) API
- **'Mech images:** ImgBB (sourced via MUL API)
- **Miniature photos:** Original photography by Dave / BattleTech Hub

BattleTech is a registered trademark of Topps Company Inc. This is an unofficial fan site.

---

## Deployment

Hosted on [Netlify](https://netlify.com). Deploys automatically on push to `main`.

Contact: DaveAsp81@gmail.com
