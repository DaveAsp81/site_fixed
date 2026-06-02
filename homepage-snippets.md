# Homepage fixes for index.html

Four articles exist but aren't linked from the homepage. Below are ready-to-paste
`article-card` blocks matching your existing markup, plus where each one goes.

The image filenames are real files that already exist in `assets/images/articles/`.
Swap any you'd prefer — note the two currently-unused images: `atlas.jpg` and
`alpha-strike.jpg`.

---

## 1 + 2 — Add to the "🎯 Getting Started" grid

Paste these two cards just before the closing `</div>` of the Getting Started
`articles-grid` (right after the "Building a Force on a Budget" card, before the
`<!-- ── GAMEPLAY ──` comment).

```html
            <div class="article-card">
                <div class="article-card-image" style="background-image: url('assets/images/articles/starter-set.jpg');"></div>
                <div class="article-card-content">
                    <h3>Best Starter Sets, Ranked</h3>
                    <p>Beginner Box, A Game of Armored Combat, or an Alpha Strike box? A side-by-side breakdown to find the right entry point for how you want to play.</p>
                    <a href="articles/best-starter-sets.html" class="read-more">Read More →</a>
                </div>
            </div>
            <div class="article-card">
                <div class="article-card-image" style="background-image: url('assets/images/articles/atlas.jpg');"></div>
                <div class="article-card-content">
                    <h3>Where to Buy BattleTech</h3>
                    <p>The best online retailers, local game stores, and second-hand options — and how to actually find good prices on miniatures and books.</p>
                    <a href="articles/where-to-buy-battletech.html" class="read-more">Read More →</a>
                </div>
            </div>
```

---

## 3 + 4 — Add to the "⚔️ Gameplay & Strategy" grid

Paste these two cards just before the closing `</div>` of the Gameplay & Strategy
`articles-grid` (before the `<!-- ── LORE ──` / "📚 Lore & Universe" section).

```html
            <div class="article-card">
                <div class="article-card-image" style="background-image: url('assets/images/articles/alpha-strike.jpg');"></div>
                <div class="article-card-content">
                    <h3>MegaMek: Play BattleTech Free Online</h3>
                    <p>Play Classic BattleTech and Alpha Strike online or solo against the AI, completely free. How to download it and get your first game going.</p>
                    <a href="articles/megamek-guide.html" class="read-more">Read More →</a>
                </div>
            </div>
            <div class="article-card">
                <div class="article-card-image" style="background-image: url('assets/images/articles/list-builder.jpg');"></div>
                <div class="article-card-content">
                    <h3>Lance Builder: What's New</h3>
                    <p>620 chassis, rewritten fluff, faction and era filters, and Alpha Strike PV tracking — everything that's changed in the tool.</p>
                    <a href="articles/lance-builder-update.html" class="read-more">Read More →</a>
                </div>
            </div>
```

---

## Bonus fix A — Broken 'Mech image (case sensitivity)

`index.html` line 312 references a lowercase filename, but the actual file is
capitalised, so the image is broken on Netlify (case-sensitive hosting).

- Reference in HTML: `assets/images/articles/locust.jpg`
- Actual file on disk: `assets/images/articles/Locust.jpg`

Fix either way (pick one):
- **Edit the HTML:** change `locust.jpg` → `Locust.jpg` on line 312, **or**
- **Rename the file:** `git mv assets/images/articles/Locust.jpg assets/images/articles/locust.jpg`

Renaming the file to lowercase is the more future-proof option (keeps all asset
names consistently lowercase).

---

## Bonus fix B — Dead "Image Credits" link

Your footer "Quick Links" list (and the old sitemap) point to `image-credits.html`,
but that file doesn't exist — it's a 404. Two options:

- **Remove the link:** delete the `<li><a href="image-credits.html">Image Credits</a></li>`
  line from the footer in `index.html`, **or**
- **Create the page:** add an `image-credits.html` crediting MegaMek, the Master Unit
  List, and ImgBB (your README already lists these sources). If you go this route, also
  add it back into the sitemap.

The corrected `sitemap.xml` I generated currently **omits** `image-credits.html` since
the page doesn't exist yet — add it back only if you create the file.
