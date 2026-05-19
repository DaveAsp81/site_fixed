#!/usr/bin/env python3
"""
Update all BattleTech article pages with hero images and improved layout
"""

import os
import re

# Map articles to their hero images
ARTICLE_HERO_IMAGES = {
    'battletech-beginner-guide.html': 'articles/mecha-giant.jpg',
    'battletech-vs-warhammer.html': 'articles/dragon-miniature.jpg',
    'best-beginner-mechs.html': 'articles/giant-robot.jpg',
    'budget-battletech-army.html': 'articles/board-game-house.jpg',
    'battletech-painting-tutorial.html': 'heroes/tabletop-gaming.jpg',
    'best-battletech-paints.html': 'articles/boardgame-setup.jpg',
    'speed-painting-battletech.html': 'articles/tabletop-setup.jpg',
    'battletech-terrain-building.html': 'articles/game-table.jpg',
    'faction-color-schemes.html': 'articles/strategy-pieces.jpg',
    'lance-building-guide.html': 'articles/strategy-tokens.jpg',
    'alpha-strike-vs-classic.html': 'articles/dice-closeup.jpg',
    'best-light-mechs.html': 'articles/futuristic-robot.jpg',
    'best-heavy-mechs.html': 'articles/robot-water.jpg',
    'heat-management-guide.html': 'heroes/mech-robot.jpg',
    'battletech-lore-explained.html': 'articles/board-games.jpg',
    'great-houses-guide.html': 'heroes/strategy-game.jpg',
    'succession-wars-explained.html': 'articles/gaming-session.jpg',
    'where-to-buy-battletech.html': 'heroes/dice-boardgame.jpg',
    'best-starter-sets.html': 'articles/board-game-night.jpg',
}

def update_article_with_hero(filepath, hero_image):
    """Add hero image section to article page"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if article already has a hero image
    if 'article-hero' in content:
        print(f"  ✓ {os.path.basename(filepath)} already has hero image")
        return
    
    # Find the opening of the main content area (after header, before article)
    # Insert hero image right after the opening <main class="main-content"> tag
    # or after the opening <article> tag
    
    # Pattern: Find <article> tag and insert hero image right after it
    article_pattern = r'(<article>\s*<h1>)'
    
    if re.search(article_pattern, content):
        # Create hero image HTML
        hero_html = f'''<div class="article-hero" style="background-image: url('../assets/images/{hero_image}');"></div>
                    '''
        
        # Insert hero image before the h1
        content = re.sub(
            article_pattern,
            hero_html + r'\1',
            content,
            count=1
        )
        
        # Write updated content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  ✓ Updated {os.path.basename(filepath)} with hero image")
    else:
        print(f"  ✗ Could not find article tag in {os.path.basename(filepath)}")

def main():
    articles_dir = '/home/ubuntu/battletech-website/articles'
    
    print("Updating BattleTech article pages with hero images...")
    print("=" * 60)
    
    updated_count = 0
    
    for article_file, hero_image in ARTICLE_HERO_IMAGES.items():
        filepath = os.path.join(articles_dir, article_file)
        
        if os.path.exists(filepath):
            update_article_with_hero(filepath, hero_image)
            updated_count += 1
        else:
            print(f"  ✗ Article not found: {article_file}")
    
    print("=" * 60)
    print(f"Processed {updated_count} article pages")
    print("Done!")

if __name__ == '__main__':
    main()
