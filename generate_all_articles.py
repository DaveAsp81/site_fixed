#!/usr/bin/env python3
"""
Generate all remaining BattleTech articles with SEO-optimized content
"""
import os

def write_article(filename, data):
    """Write a complete article HTML file"""
    sections_html = ""
    for section_title, content in data['sections']:
        # Process markdown-style formatting
        formatted = content.replace('\n\n', '</p>\n<p>')
        formatted = formatted.replace('**', '<strong>', 1)
        while '**' in formatted:
            formatted = formatted.replace('**', '</strong>', 1)
            formatted = formatted.replace('**', '<strong>', 1)
        
        sections_html += f"""
                    <h2>{section_title}</h2>
                    <p>{formatted}</p>
"""
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{data['meta']}">
    <meta name="keywords" content="{data['keywords']}">
    <title>{data['title']} | BattleTech Hub</title>
    <link rel="stylesheet" href="../assets/css/style.css">
</head>
<body>
    <header>
        <div class="header-content">
            <a href="../index.html" class="logo">⚔️ BattleTech Hub</a>
            <nav>
                <ul>
                    <li><a href="../index.html#getting-started">Getting Started</a></li>
                    <li><a href="../index.html#painting">Painting</a></li>
                    <li><a href="../index.html#gameplay">Gameplay</a></li>
                    <li><a href="../index.html#lore">Lore</a></li>
                </ul>
            </nav>
        </div>
    </header>
    <div class="container">
        <div class="content-wrapper">
            <main class="main-content">
                <article>
                    <h1>{data['h1']}</h1>
                    <p>{data['intro']}</p>
                    <div class="ad-space">[Header Ad - 728x90]</div>
                    {sections_html}
                    <div class="product-recommendation">
                        <h4>🛒 Recommended Products</h4>
                        <p>{data.get('product_rec', 'Check out these products to enhance your BattleTech experience:')}</p>
                        <a href="https://www.amazon.com/s?k=battletech" class="buy-button" target="_blank">Shop on Amazon →</a>
                    </div>
                    <div class="ad-space">[Footer Ad - 728x90]</div>
                </article>
            </main>
            <aside class="sidebar">
                <div class="sidebar-widget newsletter-box">
                    <h3>📬 Newsletter</h3>
                    <p>Weekly BattleTech tips & deals!</p>
                    <input type="email" placeholder="Your email">
                    <button>Subscribe Free</button>
                </div>
                <div class="sidebar-widget ad-space">[Sidebar Ad 300x250]</div>
            </aside>
        </div>
    </div>
    <footer>
        <div class="footer-bottom">
            <p>&copy; 2026 BattleTech Hub.</p>
        </div>
    </footer>
</body>
</html>"""
    
    with open(f"articles/{filename}", "w", encoding='utf-8') as f:
        f.write(html)
    print(f"✓ Created: {filename}")

# Define all remaining articles
remaining_articles = {
    "battletech-painting-tutorial.html": {
        "title": "BattleTech Painting Tutorial for Beginners",
        "meta": "Learn to paint BattleTech miniatures with this step-by-step guide. From priming to details, get tabletop-ready mechs fast.",
        "keywords": "battletech painting, how to paint mechs, miniature painting tutorial",
        "h1": "BattleTech Painting Tutorial: Beginner-Friendly Guide",
        "intro": "Painting your BattleMechs transforms them from grey plastic into battle-worn war machines. This tutorial walks you through every step from preparation to final details.",
        "sections": [
            ("What You'll Need to Start", "Essential supplies: primer spray (grey or black), 3-5 basic acrylic paints, brushes (sizes 0, 1, 2), wash (brown or black), water cup, palette. Budget: $30-50 to start. Quality matters but you don't need expensive brands initially."),
            ("Step 1: Cleaning and Priming", "Remove mold lines with hobby knife. Wash in warm soapy water, dry completely. Prime in thin coats from 12 inches away. Grey primer is most forgiving for beginners. Let dry 24 hours before painting."),
            ("Step 2: Base Coating", "Apply 2-3 thin coats of your main color. Thin paints with water (milk consistency). Popular schemes: Olive drab for military, grey for urban camo, tan for desert. Each coat should be translucent alone but opaque combined."),
            ("Step 3: Washing for Depth", "Apply diluted dark wash (Nuln Oil, Agrax Earthshade, or thinned black paint). Let it flow into recesses naturally. This creates instant depth and shadows. Wait to fully dry - rushing causes problems."),
            ("Step 4: Drybrushing Highlights", "Load brush with highlight color, wipe most off on paper towel. Lightly brush raised areas. This picks out details effortlessly. Use color lighter than base - add white to your base color for perfect match."),
            ("Step 5: Details and Finishing", "Paint cockpit windows (black, then highlight with white or blue), weapon barrels (metallic), heat vents (red/orange). Add decals or freehand unit insignia. Seal with matte varnish spray to protect your work."),
        ],
        "product_rec": "The Army Painter Mega Paint Set has everything you need to start painting BattleTech miniatures."
    },
    
    "best-battletech-paints.html": {
        "title": "Best Paints for BattleTech Miniatures - Tested & Reviewed",
        "meta": "Comprehensive review of the best paints for BattleTech minis. Compare Citadel, Vallejo, Army Painter, and more.",
        "keywords": "best battletech paints, miniature paints, acrylic paints review",
        "h1": "Best Paints for BattleTech Miniatures (Tested & Reviewed 2026)",
        "intro": "Choosing the right paints for your BattleTechs can be overwhelming. This comprehensive review compares all major brands with specific recommendations for BattleTech painting.",
        "sections": [
            ("Citadel Color (Games Workshop) - Premium Choice", "Pros: Excellent coverage, huge color range, perfect consistency. Cons: Expensive ($4-5 per pot), pots dry out. Best for: Detailed work, established painters with budget. Recommended starter: Citadel Base Paint Set ($40-50). Perfect military colors: Castellan Green, Mechanicus Standard Grey, Zandri Dust."),
            ("Vallejo Model Color - Best Value", "Pros: Dropper bottles prevent drying, excellent coverage, paint-to-paint consistency, affordable ($3-3.50). Cons: Some colors need thinning. Best for: Batch painting multiple mechs. Recommended: Vallejo Basic Colors Set ($35). Ideal BattleTech colors: German Cam Medium Brown, US Olive Drab, Medium Grey."),
            ("Army Painter - Best for Beginners", "Pros: Affordable, excellent washes, beginner-friendly sets. Cons: Consistency varies between colors. Best for: New painters, speed painting. Recommended: Army Painter Mega Paint Set ($80-100) includes everything. Their Quickshade washes are industry-best for instant depth."),
            ("Reaper MSP - Hidden Gem", "Pros: Dropper bottles, excellent coverage, vast color selection, affordable. Cons: Less available in stores. Best for: Online shoppers wanting quality + value. Learn Set ($40) perfect starter. Their triads (shadow/base/highlight) make color matching easy."),
        ],
        "product_rec": "For BattleTech specifically, we recommend Vallejo Model Color for your main painting, supplemented with Army Painter washes."
    },
    
    "speed-painting-battletech.html": {
        "title": "Speed Painting BattleTech: Paint a Lance in One Weekend",
        "meta": "Paint 4 BattleMechs in one weekend with these speed painting techniques. Get tabletop quality fast.",
        "keywords": "speed painting battletech, quick mech painting, tabletop standard",
        "h1": "Speed Painting BattleTech: Paint a Lance in One Weekend",
        "intro": "Don't let unpainted miniatures delay your games. These speed painting techniques deliver great tabletop results in hours, not days.",
        "sections": [
            ("The Speed Painting Philosophy", "Tabletop standard doesn't mean sloppy - it means efficient. Focus on techniques that create maximum visual impact with minimum time. Three key principles: batch painting, strategic color placement, washes do the work."),
            ("Friday Night: Prep and Prime (1 hour)", "Clean all four mechs simultaneously. Prime all together in single session. Use grey primer for speed - works with any color scheme. Assembly-line approach saves setup time. Prime Friday evening, dry overnight."),
            ("Saturday Morning: Basecoats (2-3 hours)", "Paint all four mechs the same color before switching. Do all legs, then all torsos, then all arms. 2-3 thin coats each color. Main color first, then secondary details. Don't worry about perfection - wash will fix it."),
            ("Saturday Afternoon: The Magic Wash (1 hour)", "Diluted dark wash over everything. This single step adds depth, shading, and definition. Let dry completely (3-4 hours or overnight). This transforms basic paint into professional-looking work."),
            ("Sunday: Drybrushing and Details (3-4 hours)", "Heavy drybrush with lighter shade of base color. Hits all raised details instantly. Paint cockpits (black+grey), weapons (metallic). Add simple base texture. Done! Four tabletop-ready mechs in one weekend."),
        ],
        "product_rec": "Army Painter Speedpaint system is specifically designed for this approach and works perfectly with BattleTech miniatures."
    },
    
    "battletech-terrain-building.html": {
        "title": "BattleTech Terrain Building: DIY Beginner's Guide",
        "meta": "Build stunning 3D terrain for BattleTech on a budget. Complete DIY guide with materials and techniques.",
        "keywords": "battletech terrain, diy mech terrain, hex terrain",
        "h1": "BattleTech Terrain Building for Beginners: Complete DIY Guide",
        "intro": "3D terrain transforms BattleTech games from functional to immersive. This guide shows you how to create professional-looking terrain using affordable household materials.",
        "sections": [
            ("Materials and Tools (Under $30)", "Essential: XPS foam ($10), craft paint ($10), PVA glue ($3), sand/rocks (free), craft knife. Optional: hot glue gun, texture rollers, flock/static grass. Total investment under $30 creates full table of terrain."),
            ("Making Hills and Elevated Terrain", "Stack and glue XPS foam layers. Carve edges for rocky look. Each layer = 1 level (approx 1 inch). Paint brown base, drybrush grey/tan. Add flock and rocks. Cost per hill: $1-2. Make 6-8 varied sizes for full table."),
            ("Creating Buildings (Hex-Compatible)", "Cardboard boxes or foam blocks for structure. Size to fit hex grid - most should be 1-2 hexes wide. Paint urban grey or industrial brown. Weather with washes. Add details with card stock. Modular design means endless configurations."),
            ("Woods and Forests", "Foam core bases cut to hex sizes. Glue aquarium plants or craft trees. Flock base. Create both light woods (1-2 trees per base) and heavy woods (dense placement). Make 8-12 pieces for variety."),
            ("Roads and Water Features", "Roads: Cardboard strips painted grey, add painted lane lines. Water: Blue-painted foam with gloss varnish. Both should fit hex grid. Strategic placement creates interesting battlefields."),
        ],
        "product_rec": "XPS foam insulation boards from hardware stores are the perfect terrain building material - cheap, easy to work with, and durable."
    },
    
    "faction-color-schemes.html": {
        "title": "Painting Clan vs Inner Sphere: BattleTech Color Guide",
        "meta": "Learn official color schemes for all BattleTech factions. Painting guides for Great Houses and Clans.",
        "keywords": "battletech color schemes, faction paint schemes, clan colors",
        "h1": "Painting Clan vs Inner Sphere Mechs: Complete Color Scheme Guide",
        "intro": "Each BattleTech faction has signature color schemes that identify their forces. This guide covers official colors and painting techniques for all major factions.",
        "sections": [
            ("House Steiner (Lyran Commonwealth)", "Signature colors: Blue and white. Classic scheme: Deep blue primary, white accents, gold/yellow highlights. Alternative: Urban grey with blue trim. Represents wealth and formality. Paint recipe: Ultramarine Blue + White + Auric Gold accents."),
            ("House Davion (Federated Suns)", "Signature colors: Red and gold. Classic scheme: Deep red primary, gold/brass details. Alternative: Tan/desert camo with red highlights. Represents nobility and honor. Paint recipe: Mephiston Red + Retributor Gold details."),
            ("House Liao (Capellan Confederation)", "Signature colors: Green. Classic scheme: Dark green primary, minimal accents. Alternative: Green and black urban camo. Represents stealth and cunning. Paint recipe: Castellan Green + Black wash."),
            ("House Marik (Free Worlds League)", "Signature colors: Purple and white. Classic scheme: Royal purple with white details. Alternative: Grey with purple accents. Paint recipe: Phoenician Purple + White + Silver."),
            ("House Kurita (Draconis Combine)", "Signature colors: Red and black. Classic scheme: Deep red with black details, gold dragon symbols. Alternative: Black primary with red accents. Paint recipe: Khorne Red + Abaddon Black + Gold details."),
            ("Clan Wolf", "Signature colors: Grey and red. Classic scheme: Wolf grey primary, red trim. Paint recipe: Mechanicus Grey + Mephiston Red accents."),
            ("Clan Jade Falcon", "Signature colors: Green and yellow. Bright jade green primary, yellow/gold accents. Paint recipe: Warpstone Glow + Flash Gitz Yellow."),
        ],
        "product_rec": "Citadel Contrast paints work excellently for faction schemes - one coat over grey primer creates perfect military looks."
    },
    
    "lance-building-guide.html": {
        "title": "BattleTech Lance Building Guide: Roles, Synergy & Tactics",
        "meta": "Master BattleTech lance building. Learn roles, synergy, and tactical compositions for winning gameplay.",
        "keywords": "battletech lance building, mech tactics, lance composition",
        "h1": "BattleTech Lance Building Guide: Create Winning Formations",
        "intro": "A well-built lance is greater than the sum of its parts. This guide teaches you how to create synergistic lances that dominate the battlefield.",
        "sections": [
            ("Understanding Lance Roles", "Every lance needs four key roles: Scout (light mech, speed 7+), Striker (medium/heavy, balanced offense), Brawler (heavy/assault, close combat), Fire Support (any weight, long-range). Not every mech fills exactly one role, but coverage of all four creates versatile forces."),
            ("Battle Value Basics", "BV is the fairest balancing method. Typical lance BVs: Light lance ~3000 BV, Medium ~4000 BV, Heavy ~5000 BV, Assault ~6000 BV. Build to these targets for balanced play. Pilot skills modify BV - lower skill increases BV cost."),
            ("Synergistic Weapon Selection", "Lances should complement, not duplicate. Example: If one mech carries LRM40, others need TAG or direct fire to support. Stability damage + direct damage work together - LRMs knock down, AC/20 cores the downed target. Heat management - if one mech runs hot, others should be heat-efficient to maintain pressure."),
            ("Sample Winning Lances", "Classic 3025 Lance (4500 BV): Locust 1V (scout, 431 BV), Wolverine 6R (striker, 1063 BV), Thunderbolt 5S (brawler, 1335 BV), Catapult C1 (fire support, 1460 BV). Total: 4289 BV with room for pilot upgrades. Balances all roles with synergistic weapons."),
            ("Advanced: C3 Networks", "C3 allows lance to share targeting data. Requires C3 Master + 3 Slaves. Effectively removes range penalties for networked mechs. Expensive in BV but devastating. Best with long-range lances - everyone hits at optimal range."),
        ],
        "product_rec": "Catalyst Game Labs Force Packs are pre-designed for synergistic lance composition - great starting points."
    },
}

# Generate all articles
os.makedirs("articles", exist_ok=True)
for filename, data in remaining_articles.items():
    write_article(filename, data)

print(f"\n✓ Generated {len(remaining_articles)} additional articles")
print("Total articles now available: 20+")
