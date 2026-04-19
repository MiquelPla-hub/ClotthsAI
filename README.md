# ClothsAI

A localhost wardrobe manager that recommends daily outfits based on color theory and style compatibility rules.

## Features

- Upload clothing items with photos
- Browse your wardrobe by category
- Daily outfit recommendations ranked by color + style compatibility
- Filter suggestions by style (casual, smart-casual, formal, sporty)
- Dark-themed web UI, no installation beyond Python

## Setup

**Requirements:** Python 3.10+

```bash
git clone https://github.com/mpla11/ClothsAI.git
cd ClothsAI
pip install -r requirements.txt
```

### Load demo wardrobe

```bash
python seed_data/seed.py
```

### Run

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

## Adding your own clothes

1. Open http://localhost:5000
2. Click **Add Item**
3. Upload a photo and fill in the category, color, and style
4. Switch to **Outfits** to see updated recommendations

## How recommendations work

Each outfit combination (top + bottom + shoes) is scored 0–100%:

- **Color compatibility (60%)** — based on color groups (neutral, cool, warm, earth). Neutrals pair with everything. Complementary groups score high. Clashing warm+warm scores low.
- **Style compatibility (40%)** — based on a style matrix. Same styles score 100%. Formal + sporty scores 10%.

## Running tests

```bash
pytest tests/ -v
```

## Tech stack

- Python 3 + Flask + SQLAlchemy
- SQLite (local `wardrobe.db`)
- Vanilla JS — no build step, no Node.js required
