# ClothsAI — Mobile Redesign Spec
**Date:** 2026-04-20
**Status:** Approved

## Overview

Full frontend redesign targeting Android mobile browsers. Primary use case: wake up, browse wardrobe photos, tap a piece, swipe through pre-generated outfit combinations. White background, fashion-app aesthetic, touch-first interactions.

## Architecture

**Navigation model: Screen-stack (no tabs)**

3 screens managed in vanilla JS. Bottom nav always visible with 2 items: Wardrobe (home) + Add Item.

```
Screen 1 — Wardrobe Grid    (default)
Screen 2 — Outfit Carousel  (pushed when item tapped)
Screen 3 — Add Item         (pushed when + tapped)
```

Screens are `<section>` elements toggled with `data-screen` classes. No routing library. Back navigation via in-header back arrow.

## Screens

### Screen 1 — Wardrobe Grid

- 2-column photo grid, full-width images, minimal padding
- Each card shows clothing photo + item name + outfit count badge (e.g. `3 outfits`)
- Badge hidden when count is 0
- Tap card → navigate to Screen 2 (Outfit Carousel) for that item
- Long-press (500ms) → haptic feedback (`navigator.vibrate(50)`) + confirm dialog → delete item
- Bottom nav visible

### Screen 2 — Outfit Carousel

- Header: back arrow + tapped item name + position indicator (e.g. `4 / 9`)
- Horizontal swipeable cards using CSS `scroll-snap-type: x mandatory` — zero JS for swipe
- Each card occupies full viewport width, centered
- Card content (top to bottom):
  - Photos of each outfit piece (top, bottom, shoes) stacked vertically with names
  - Color-coded score bar (green >75%, amber 50–75%, red <50%) + percentage label
  - Occasion label (Casual / Smart-casual / Formal / Sporty)
- Outfits sorted by score descending
- Fetched from `GET /api/outfits?item_id=X`
- Empty state: "No outfits yet — add more clothes!"

### Screen 3 — Add Item

- Header: back arrow + "Add Item"
- Large tap area (photo picker) at top — tap opens OS file chooser (camera + gallery via `<input type="file" accept="image/*">`)
- Photo preview shown immediately after selection (FileReader API)
- Form fields below: Name, Category, Color (primary), Style, Season
- Submit button — disabled until photo + required fields filled
- On submit: POST to `/api/clothes`, backend auto-regenerates outfits, navigate back to wardrobe
- Loading state on submit button ("Adding...")

## Backend Changes

### Auto-regeneration

New internal function `regenerate_outfits(app)`:
1. Clear all rows from `Outfit` table
2. Call `generate_suggestions(items, style_filter='all', limit=9999)`
3. Save each suggestion as an `Outfit` row

Triggered after:
- `POST /api/clothes` — after item is saved
- `DELETE /api/clothes/<id>` — after item is deleted

### API changes

**`GET /api/outfits?item_id=X`** (new query param)
- Filter outfits where `item_ids` JSON array contains `X`
- Returns outfits with full item objects (not just IDs) in `items` field
- Sorted by score descending

**`GET /api/clothes` response**
- Each item gains `outfit_count` field: count of saved outfits containing that item's ID
- Computed with a Python list comprehension over `Outfit.query.all()`

**`GET /api/suggest`**
- Now reads from DB (`Outfit.query`) instead of calling `generate_suggestions` live
- Keeps existing query params (style, limit) for backward compatibility

## Visual Design

### Color palette
```css
--bg: #ffffff
--surface: #f8f8f8
--border: #ebebeb
--text: #111111
--text-muted: #888888
--accent: #111111        /* buttons, active nav */
--score-high: #22c55e    /* >75% */
--score-mid:  #f59e0b    /* 50–75% */
--score-low:  #ef4444    /* <50% */
--radius: 12px
```

### Touch guidelines
- All tap targets: minimum 48×48px
- Bottom nav height: 64px
- Card padding: 16px
- Grid gap: 8px

### Typography
- `font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`
- Body: 15px / 1.5 line-height
- Labels: 12px, color `--text-muted`

### Carousel implementation
```css
.carousel-track {
  display: flex;
  overflow-x: scroll;
  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}
.carousel-card {
  flex: 0 0 100%;
  scroll-snap-align: center;
}
```
No JavaScript needed for swipe. Position indicator (`4 / 9`) updated via `scroll` event listener.

### Score bar
```html
<div class="score-bar">
  <div class="score-fill" style="width: 87%; background: var(--score-high)"></div>
</div>
```

### Outfit count badge
```html
<span class="outfit-badge">3 outfits</span>
```
Black pill, 11px, hidden when count is 0.

### Photo preview on Add
```js
photoInput.addEventListener('change', e => {
  const reader = new FileReader();
  reader.onload = ev => { preview.src = ev.target.result; preview.hidden = false; };
  reader.readAsDataURL(e.target.files[0]);
});
```

### Haptic on delete
```js
navigator.vibrate?.(50);
```

## Files Changed

| File | Change |
|------|--------|
| `static/index.html` | Full rewrite — 3 screen sections, bottom nav, no tabs |
| `static/style.css` | Full rewrite — white theme, mobile-first, carousel CSS |
| `static/app.js` | Full rewrite — screen navigation, carousel position, add form |
| `app.py` | Add `regenerate_outfits()`, update POST/DELETE routes, update `/api/outfits` and `/api/suggest`, add `outfit_count` to clothes response |

## Out of Scope
- Push notifications for daily outfit reminder
- Weather-based filtering
- Outfit history / "don't repeat" logic
- PWA / offline mode
