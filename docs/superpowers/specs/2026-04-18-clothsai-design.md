# ClothsAI — Design Spec
**Date:** 2026-04-18  
**Status:** Approved

## Overview

A localhost web app that lets you catalog your wardrobe by photo and receive daily outfit recommendations based on color theory and style compatibility rules. Built with Python/Flask REST API + Vanilla JS frontend + SQLite.

## Architecture

**Option chosen: Flask API + Vanilla JS (Option B)**

- Flask serves a REST JSON API and static files from a single process
- Frontend is a single `index.html` + `app.js` — no build step, no Node.js required
- SQLite database via SQLAlchemy ORM
- Clothing photos stored on local filesystem under `uploads/`
- Recommendation logic lives in a pure Python module (`recommender.py`)

## Project Structure

```
ClothsAI/
  app.py              # Flask app entry point + API routes
  models.py           # SQLAlchemy models
  recommender.py      # Rule-based outfit scoring engine
  static/
    index.html        # Single page app
    app.js            # Frontend logic (fetch API calls, DOM manipulation)
    style.css         # Styling
  uploads/            # Clothing photos (gitignored)
  seed_data/          # Sample images for demo (Unsplash URLs or downloaded)
  wardrobe.db         # SQLite database (gitignored)
  requirements.txt
```

## Data Model

### ClothingItem
| Field | Type | Notes |
|---|---|---|
| id | int PK | auto |
| name | str | e.g. "White Oxford Shirt" |
| category | enum | top / bottom / shoes / outerwear / accessory |
| color_primary | str | hex color e.g. "#FFFFFF" |
| color_secondary | str | hex, optional |
| style_tags | str | comma-separated: casual / formal / sporty / smart-casual |
| season | str | all / summer / winter / spring-fall |
| photo_path | str | relative path under uploads/ |
| created_at | datetime | auto |

### Outfit (saved combinations)
| Field | Type | Notes |
|---|---|---|
| id | int PK | auto |
| name | str | optional user label |
| item_ids | str | JSON array of ClothingItem IDs |
| score | float | 0.0–1.0 |
| occasion | str | derived from style_tags of items |
| created_at | datetime | auto |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/clothes` | List all clothing items (filterable by category, season, style) |
| POST | `/api/clothes` | Upload new clothing item (multipart form) |
| DELETE | `/api/clothes/<id>` | Remove item |
| GET | `/api/outfits` | List saved outfits |
| GET | `/api/suggest` | Generate ranked outfit suggestions (query params: style, occasion, limit) |
| GET | `/uploads/<filename>` | Serve clothing photos |

## Recommendation Engine

### Outfit Validity
A valid outfit requires: **1 top + 1 bottom + 1 shoes** (minimum). Outerwear and accessories are optional add-ons.

### Scoring (0.0–1.0)

**Color compatibility — 60% of score**

Uses a color wheel / named-color approach:
- Neutral colors (black, white, grey, beige, navy, tan) pair with anything → 1.0
- Complementary colors (opposite on color wheel, e.g. blue + orange) → 0.9
- Analogous colors (adjacent, e.g. blue + green) → 0.7
- Monochromatic (same hue, different lightness) → 0.8
- Clashing (e.g. red + pink, red + orange) → 0.2

Color groups are defined as lookup tables in `recommender.py` mapped from named colors to their group (neutral / warm / cool / earth).

**Style compatibility — 40% of score**

Compatibility matrix:
| | casual | smart-casual | formal | sporty |
|---|---|---|---|---|
| casual | 1.0 | 0.7 | 0.2 | 0.6 |
| smart-casual | 0.7 | 1.0 | 0.8 | 0.3 |
| formal | 0.2 | 0.8 | 1.0 | 0.1 |
| sporty | 0.6 | 0.3 | 0.1 | 1.0 |

Final score = (color_score × 0.6) + (style_score × 0.4)

### Output
- All valid top+bottom+shoes combinations generated from wardrobe
- Ranked by score descending
- Top result shown as "hero" card
- Remaining shown in grid below
- Filterable by style tab (All / Casual / Formal / Sporty / Smart-casual)

## UI Layout

**Option B — Top Pick Hero + Grid**

```
┌─────────────────────────────────────────────┐
│  ClothsAI          [All][Casual][Formal]...  │
├─────────────────────────────────────────────┤
│  ★ TOP PICK TODAY                           │
│  [photo]  White Oxford + Navy Chinos +      │
│           White Sneakers                    │
│           Smart casual · 92% · Spring       │
├──────────────┬──────────────┬───────────────┤
│ [outfit 2]   │ [outfit 3]   │ [outfit 4]    │
│ Grey tee +   │ Blue hoodie  │ Black jacket  │
│ Black jeans  │ + Chinos     │ + White tee   │
│ 87%          │ 81%          │ 78%           │
└──────────────┴──────────────┴───────────────┘
```

Navigation tabs: **Outfits** (daily view) | **Wardrobe** (browse all items) | **Add Item** (upload form)

## Seed Data

~10 clothing items with real photos (downloaded Unsplash images or stable URLs), covering:
- 3 tops (white shirt, grey t-shirt, blue hoodie)
- 2 bottoms (navy chinos, black jeans)
- 2 shoes (white sneakers, black boots)
- 1 outerwear (black jacket)
- 2 accessories (optional)

## GitHub Repository

- Repo name: `ClothsAI`
- Public repository
- `.gitignore` excludes: `wardrobe.db`, `uploads/`, `__pycache__/`, `.env`, `.superpowers/`
- README with setup instructions and screenshot

## Future Enhancements (out of scope)
- AI vision model (Claude) for auto-tagging clothes from photo
- Weather API integration to filter by today's weather
- "Outfit history" to avoid repeating recent outfits
- Mobile-friendly PWA
