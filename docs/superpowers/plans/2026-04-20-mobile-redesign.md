# ClothsAI Mobile Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the ClothsAI frontend as a mobile-first Android app (white theme, 3-screen navigation, horizontal swipe carousel) and update the backend to pre-generate and persist outfit combinations.

**Architecture:** Screen-stack navigation in vanilla JS — 3 `<section>` elements toggled by class. Outfit generation happens automatically on every POST/DELETE to `/api/clothes` and results are stored in the `Outfit` table. The carousel uses CSS `scroll-snap` for zero-JS swipe.

**Tech Stack:** Python 3 / Flask / SQLAlchemy / SQLite / Vanilla JS / CSS scroll-snap

---

## File Map

| File | Change |
|------|--------|
| `app.py` | Add `regenerate_outfits()`, update POST/DELETE to call it, add `outfit_count` to GET /api/clothes, update GET /api/outfits with item_id filter + full items, update GET /api/suggest to read from DB |
| `tests/test_api.py` | Add tests: auto-regen after POST, auto-regen after DELETE, outfit_count field, item_id filter on /api/outfits |
| `static/index.html` | Full rewrite — 3 screen sections, bottom nav, no tabs |
| `static/style.css` | Full rewrite — white theme, mobile-first, carousel CSS |
| `static/app.js` | Full rewrite — screen navigation, wardrobe grid, carousel, add form |

---

### Task 1: Add regenerate_outfits() and wire to POST and DELETE

**Files:**
- Modify: `app.py`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_api.py`:

```python
def test_add_clothes_regenerates_outfits(client):
    post_item(client, 'White Shirt', 'top', 'white', 'casual')
    post_item(client, 'Navy Chinos', 'bottom', 'navy', 'casual')
    post_item(client, 'White Sneakers', 'shoes', 'white', 'casual')
    resp = client.get('/api/outfits')
    assert resp.status_code == 200
    assert len(resp.json) == 1


def test_delete_regenerates_outfits(client):
    post_item(client, 'White Shirt', 'top', 'white', 'casual')
    post_item(client, 'Navy Chinos', 'bottom', 'navy', 'casual')
    add_resp = post_item(client, 'White Sneakers', 'shoes', 'white', 'casual')
    shoes_id = add_resp.json['id']
    client.delete(f'/api/clothes/{shoes_id}')
    resp = client.get('/api/outfits')
    assert resp.json == []
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_api.py::test_add_clothes_regenerates_outfits tests/test_api.py::test_delete_regenerates_outfits -v
```

Expected: both FAIL — outfit table stays empty because regen is not yet wired.

- [ ] **Step 3: Add regenerate_outfits() and wire to POST and DELETE in app.py**

Inside `create_app()`, add this helper before the route definitions:

```python
def regenerate_outfits():
    Outfit.query.delete()
    items = ClothingItem.query.all()
    suggestions = generate_suggestions(items, style_filter='all', limit=9999)
    for s in suggestions:
        db.session.add(Outfit(
            item_ids=json.dumps([i['id'] for i in s['items']]),
            score=s['score'],
            occasion=s['occasion'],
        ))
    db.session.commit()
```

In `add_clothes`, add `regenerate_outfits()` after `db.session.commit()` and before the return:

```python
db.session.add(item)
db.session.commit()
regenerate_outfits()
return jsonify(item.to_dict()), 201
```

In `delete_clothes`, add `regenerate_outfits()` after `db.session.commit()`:

```python
db.session.delete(item)
db.session.commit()
regenerate_outfits()
return jsonify({'deleted': item_id})
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_api.py::test_add_clothes_regenerates_outfits tests/test_api.py::test_delete_regenerates_outfits -v
```

Expected: both PASS.

- [ ] **Step 5: Run full test suite**

```
pytest tests/ -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add app.py tests/test_api.py
git commit -m "feat: auto-regenerate outfits on add/delete"
```

---

### Task 2: Add outfit_count field to GET /api/clothes

**Files:**
- Modify: `app.py`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_api.py`:

```python
def test_get_clothes_outfit_count(client):
    post_item(client, 'White Shirt', 'top', 'white', 'casual')
    post_item(client, 'Navy Chinos', 'bottom', 'navy', 'casual')
    post_item(client, 'White Sneakers', 'shoes', 'white', 'casual')
    resp = client.get('/api/clothes')
    assert resp.status_code == 200
    for item in resp.json:
        assert 'outfit_count' in item
        assert item['outfit_count'] == 1
```

- [ ] **Step 2: Run test to verify it fails**

```
pytest tests/test_api.py::test_get_clothes_outfit_count -v
```

Expected: FAIL — `outfit_count` key missing from item dict.

- [ ] **Step 3: Update get_clothes route in app.py**

Replace the `get_clothes` route with:

```python
@app.route('/api/clothes', methods=['GET'])
def get_clothes():
    q = ClothingItem.query
    if category := request.args.get('category'):
        q = q.filter_by(category=category)
    if season := request.args.get('season'):
        q = q.filter(ClothingItem.season.in_([season, 'all']))
    if style := request.args.get('style'):
        q = q.filter(ClothingItem.style_tags.contains(style))

    all_outfits = Outfit.query.all()
    outfit_id_sets = [set(json.loads(o.item_ids)) for o in all_outfits]

    result = []
    for item in q.all():
        d = item.to_dict()
        d['outfit_count'] = sum(1 for ids in outfit_id_sets if item.id in ids)
        result.append(d)
    return jsonify(result)
```

- [ ] **Step 4: Run test to verify it passes**

```
pytest tests/test_api.py::test_get_clothes_outfit_count -v
```

Expected: PASS.

- [ ] **Step 5: Run full suite**

```
pytest tests/ -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add app.py tests/test_api.py
git commit -m "feat: add outfit_count to GET /api/clothes response"
```

---

### Task 3: Update GET /api/outfits with item_id filter and full item objects

**Files:**
- Modify: `app.py`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_api.py`:

```python
def test_get_outfits_filter_by_item_id(client):
    r1 = post_item(client, 'White Shirt', 'top', 'white', 'casual')
    post_item(client, 'Navy Chinos', 'bottom', 'navy', 'casual')
    post_item(client, 'White Sneakers', 'shoes', 'white', 'casual')
    shirt_id = r1.json['id']
    resp = client.get(f'/api/outfits?item_id={shirt_id}')
    assert resp.status_code == 200
    assert len(resp.json) == 1
    item_ids_in_outfit = [i['id'] for i in resp.json[0]['items']]
    assert shirt_id in item_ids_in_outfit


def test_get_outfits_filter_by_item_id_no_match(client):
    post_item(client, 'White Shirt', 'top', 'white', 'casual')
    post_item(client, 'Navy Chinos', 'bottom', 'navy', 'casual')
    post_item(client, 'White Sneakers', 'shoes', 'white', 'casual')
    resp = client.get('/api/outfits?item_id=99999')
    assert resp.status_code == 200
    assert resp.json == []
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_api.py::test_get_outfits_filter_by_item_id tests/test_api.py::test_get_outfits_filter_by_item_id_no_match -v
```

Expected: FAIL — current endpoint returns `to_dict()` with `item_ids` as int list, no `items` key.

- [ ] **Step 3: Replace get_outfits route in app.py**

```python
@app.route('/api/outfits', methods=['GET'])
def get_outfits():
    item_id = request.args.get('item_id', type=int)
    all_outfits = Outfit.query.order_by(Outfit.score.desc()).all()
    result = []
    for o in all_outfits:
        ids = json.loads(o.item_ids)
        if item_id is not None and item_id not in ids:
            continue
        items = [db.session.get(ClothingItem, i) for i in ids]
        items = [i for i in items if i]
        result.append({
            'id': o.id,
            'score': o.score,
            'occasion': o.occasion,
            'items': [i.to_dict() for i in items],
        })
    return jsonify(result)
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_api.py::test_get_outfits_filter_by_item_id tests/test_api.py::test_get_outfits_filter_by_item_id_no_match -v
```

Expected: both PASS.

- [ ] **Step 5: Run full suite**

```
pytest tests/ -v
```

Expected: all pass. `test_get_outfits_empty` still passes because empty DB returns `[]`.

- [ ] **Step 6: Commit**

```bash
git add app.py tests/test_api.py
git commit -m "feat: GET /api/outfits supports item_id filter and returns full item objects"
```

---

### Task 4: Update GET /api/suggest to read from DB

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Verify existing suggest tests pass**

```
pytest tests/test_api.py::test_suggest_with_complete_wardrobe tests/test_api.py::test_suggest_style_filter tests/test_api.py::test_suggest_empty_wardrobe tests/test_api.py::test_suggest_invalid_limit_returns_400 -v
```

Expected: all PASS (outfits now live in DB after Task 1 regen).

- [ ] **Step 2: Replace suggest_outfits route in app.py**

```python
@app.route('/api/suggest', methods=['GET'])
def suggest_outfits():
    style = request.args.get('style', 'all')
    try:
        limit = max(1, int(request.args.get('limit', 20)))
    except (ValueError, TypeError):
        return jsonify({'error': 'limit must be a positive integer'}), 400

    all_outfits = Outfit.query.order_by(Outfit.score.desc()).all()
    result = []
    for o in all_outfits:
        if len(result) >= limit:
            break
        if style != 'all' and o.occasion != style:
            continue
        ids = json.loads(o.item_ids)
        items = [db.session.get(ClothingItem, i) for i in ids]
        items = [i for i in items if i]
        result.append({
            'id': o.id,
            'score': o.score,
            'occasion': o.occasion,
            'items': [i.to_dict() for i in items],
        })
    return jsonify(result)
```

- [ ] **Step 3: Run suggest tests**

```
pytest tests/test_api.py::test_suggest_with_complete_wardrobe tests/test_api.py::test_suggest_style_filter tests/test_api.py::test_suggest_empty_wardrobe tests/test_api.py::test_suggest_invalid_limit_returns_400 -v
```

Expected: all PASS.

- [ ] **Step 4: Run full suite**

```
pytest tests/ -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add app.py
git commit -m "refactor: GET /api/suggest reads pre-generated outfits from DB"
```

---

### Task 5: Rewrite static/index.html

**Files:**
- Modify: `static/index.html`

- [ ] **Step 1: Rewrite static/index.html**

Replace entire file with:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
  <title>ClothsAI</title>
  <link rel="stylesheet" href="/style.css">
</head>
<body>

  <!-- Screen: Wardrobe -->
  <div id="screen-wardrobe" class="screen active">
    <header class="app-header">
      <span class="logo">ClothsAI</span>
    </header>
    <div class="wardrobe-grid" id="wardrobe-grid"></div>
    <p id="no-clothes" class="empty-msg" hidden>Your wardrobe is empty.<br>Tap + to add clothes.</p>
  </div>

  <!-- Screen: Carousel -->
  <div id="screen-carousel" class="screen">
    <header class="app-header">
      <button class="back-btn" id="carousel-back">&#8592;</button>
      <span class="header-title" id="carousel-title"></span>
      <span class="header-pos" id="carousel-pos"></span>
    </header>
    <div class="carousel-track" id="carousel-track"></div>
    <p id="no-outfits" class="empty-msg" hidden>No outfits yet.<br>Add more clothes to get combinations!</p>
  </div>

  <!-- Screen: Add Item -->
  <div id="screen-add" class="screen">
    <header class="app-header">
      <button class="back-btn" id="add-back">&#8592;</button>
      <span class="header-title">Add Item</span>
    </header>
    <div class="add-content">
      <form id="add-form" enctype="multipart/form-data">
        <label class="photo-picker" id="photo-picker">
          <input type="file" name="photo" accept="image/*" id="photo-input" required>
          <img id="photo-preview" hidden alt="Preview">
          <span id="photo-placeholder">&#128247; Tap to add photo</span>
        </label>
        <div class="form-group">
          <label>Name</label>
          <input type="text" name="name" required placeholder="e.g. White Oxford Shirt">
        </div>
        <div class="form-group">
          <label>Category</label>
          <select name="category" required>
            <option value="">Select category</option>
            <option value="top">Top</option>
            <option value="bottom">Bottom</option>
            <option value="shoes">Shoes</option>
            <option value="outerwear">Outerwear</option>
            <option value="accessory">Accessory</option>
          </select>
        </div>
        <div class="form-group">
          <label>Primary Color</label>
          <select name="color_primary" required>
            <option value="">Select color</option>
            <option value="white">White</option>
            <option value="black">Black</option>
            <option value="grey">Grey</option>
            <option value="navy">Navy</option>
            <option value="beige">Beige</option>
            <option value="tan">Tan</option>
            <option value="blue">Blue</option>
            <option value="green">Green</option>
            <option value="red">Red</option>
            <option value="orange">Orange</option>
            <option value="yellow">Yellow</option>
            <option value="purple">Purple</option>
            <option value="pink">Pink</option>
            <option value="brown">Brown</option>
            <option value="olive">Olive</option>
            <option value="burgundy">Burgundy</option>
            <option value="teal">Teal</option>
          </select>
        </div>
        <div class="form-group">
          <label>Style</label>
          <select name="style_tags" required>
            <option value="">Select style</option>
            <option value="casual">Casual</option>
            <option value="smart-casual">Smart Casual</option>
            <option value="formal">Formal</option>
            <option value="sporty">Sporty</option>
          </select>
        </div>
        <div class="form-group">
          <label>Season</label>
          <select name="season">
            <option value="all">All seasons</option>
            <option value="summer">Summer</option>
            <option value="winter">Winter</option>
            <option value="spring-fall">Spring / Fall</option>
          </select>
        </div>
        <button type="submit" class="btn-primary" id="add-submit">Add to Wardrobe</button>
        <p id="add-error" class="error-msg" hidden></p>
      </form>
    </div>
  </div>

  <!-- Bottom Nav -->
  <nav class="bottom-nav">
    <button class="nav-btn active" data-screen="wardrobe">
      <span class="nav-icon">&#128248;</span>
      <span class="nav-label">Wardrobe</span>
    </button>
    <button class="nav-btn" data-screen="add">
      <span class="nav-icon">+</span>
      <span class="nav-label">Add Item</span>
    </button>
  </nav>

  <script src="/app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add static/index.html
git commit -m "feat: rewrite index.html for mobile screen-stack navigation"
```

---

### Task 6: Rewrite static/style.css

**Files:**
- Modify: `static/style.css`

- [ ] **Step 1: Rewrite static/style.css**

Replace entire file with:

```css
:root {
  --bg: #ffffff;
  --surface: #f8f8f8;
  --border: #ebebeb;
  --text: #111111;
  --text-muted: #888888;
  --accent: #111111;
  --score-high: #22c55e;
  --score-mid: #f59e0b;
  --score-low: #ef4444;
  --radius: 12px;
  --nav-height: 64px;
  --header-height: 56px;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  height: 100dvh;
  overflow: hidden;
}

/* Screens */
.screen {
  display: none;
  flex-direction: column;
  height: 100dvh;
  padding-bottom: var(--nav-height);
}
.screen.active { display: flex; }

/* Header */
.app-header {
  height: var(--header-height);
  display: flex;
  align-items: center;
  padding: 0 16px;
  border-bottom: 1px solid var(--border);
  gap: 12px;
  flex-shrink: 0;
  background: var(--bg);
}

.logo { font-size: 20px; font-weight: 700; letter-spacing: -0.02em; }

.back-btn {
  background: none;
  border: none;
  font-size: 22px;
  cursor: pointer;
  color: var(--text);
  padding: 8px;
  margin-left: -8px;
  min-width: 48px;
  min-height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-pos { font-size: 13px; color: var(--text-muted); white-space: nowrap; }

/* Bottom nav */
.bottom-nav {
  position: fixed;
  bottom: 0; left: 0; right: 0;
  height: var(--nav-height);
  background: var(--bg);
  border-top: 1px solid var(--border);
  display: flex;
  z-index: 100;
}

.nav-btn {
  flex: 1;
  background: none;
  border: none;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  color: var(--text-muted);
  transition: color 0.15s;
  -webkit-tap-highlight-color: transparent;
}
.nav-btn.active { color: var(--accent); }
.nav-icon { font-size: 22px; line-height: 1; }
.nav-label { font-size: 11px; font-weight: 500; }

/* Wardrobe grid */
.wardrobe-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2px;
  overflow-y: auto;
  flex: 1;
  -webkit-overflow-scrolling: touch;
}

.wardrobe-card {
  position: relative;
  aspect-ratio: 3 / 4;
  overflow: hidden;
  background: var(--surface);
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.wardrobe-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.wardrobe-card-label {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  background: linear-gradient(transparent, rgba(0,0,0,0.65));
  color: white;
  padding: 24px 10px 8px;
  font-size: 12px;
  font-weight: 500;
}

.outfit-badge {
  position: absolute;
  top: 8px; right: 8px;
  background: rgba(0,0,0,0.72);
  color: white;
  font-size: 10px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 20px;
}

/* Carousel */
.carousel-track {
  display: flex;
  overflow-x: scroll;
  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  flex: 1;
}
.carousel-track::-webkit-scrollbar { display: none; }

.carousel-card {
  flex: 0 0 100%;
  scroll-snap-align: center;
  overflow-y: auto;
  padding: 20px 16px;
  -webkit-overflow-scrolling: touch;
}

.outfit-items { display: flex; flex-direction: column; gap: 14px; margin-bottom: 24px; }

.outfit-item { display: flex; gap: 14px; align-items: center; }

.outfit-item-img {
  width: 80px; height: 100px;
  object-fit: cover;
  border-radius: 10px;
  flex-shrink: 0;
  background: var(--surface);
}

.outfit-item-name { font-size: 15px; font-weight: 500; line-height: 1.3; }
.outfit-item-cat { font-size: 12px; color: var(--text-muted); margin-top: 3px; }

.score-section { padding-top: 16px; border-top: 1px solid var(--border); }
.score-label { font-size: 22px; font-weight: 700; margin-bottom: 6px; }

.score-bar-wrap {
  height: 6px;
  background: var(--border);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 8px;
}
.score-bar-fill { height: 100%; border-radius: 3px; }
.occasion-label { font-size: 13px; color: var(--text-muted); }

/* Add form */
.add-content { overflow-y: auto; flex: 1; padding: 16px; -webkit-overflow-scrolling: touch; }

.photo-picker {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  aspect-ratio: 4 / 3;
  border: 2px dashed var(--border);
  border-radius: var(--radius);
  cursor: pointer;
  overflow: hidden;
  position: relative;
  margin-bottom: 20px;
  background: var(--surface);
}

.photo-picker input[type="file"] {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
  font-size: 0;
}

#photo-preview {
  width: 100%; height: 100%;
  object-fit: cover;
  position: absolute;
  inset: 0;
}

#photo-placeholder { font-size: 16px; color: var(--text-muted); text-align: center; pointer-events: none; }

.form-group { margin-bottom: 14px; }

.form-group label {
  display: block;
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 6px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.form-group input,
.form-group select {
  width: 100%;
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 14px 12px;
  border-radius: var(--radius);
  font-size: 15px;
  -webkit-appearance: none;
  appearance: none;
}

.form-group input:focus,
.form-group select:focus { outline: none; border-color: var(--accent); }

.btn-primary {
  background: var(--accent);
  color: white;
  border: none;
  padding: 16px;
  border-radius: var(--radius);
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  width: 100%;
  margin-top: 8px;
  -webkit-tap-highlight-color: transparent;
}
.btn-primary:disabled { opacity: 0.45; }

.empty-msg {
  color: var(--text-muted);
  text-align: center;
  padding: 60px 32px;
  font-size: 15px;
  line-height: 1.7;
}

.error-msg { color: #ef4444; text-align: center; margin-top: 12px; font-size: 14px; }
```

- [ ] **Step 2: Commit**

```bash
git add static/style.css
git commit -m "feat: rewrite style.css — white mobile-first theme with carousel CSS"
```

---

### Task 7: Rewrite static/app.js

**Files:**
- Modify: `static/app.js`

- [ ] **Step 1: Rewrite static/app.js**

Replace entire file with:

```javascript
// Screen navigation
const screens = {
  wardrobe: document.getElementById('screen-wardrobe'),
  carousel: document.getElementById('screen-carousel'),
  add: document.getElementById('screen-add'),
};

function showScreen(name) {
  Object.values(screens).forEach(s => s.classList.remove('active'));
  screens[name].classList.add('active');
  document.querySelectorAll('.nav-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.screen === name);
  });
}

document.querySelectorAll('.nav-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    if (btn.dataset.screen === 'wardrobe') loadWardrobe();
    showScreen(btn.dataset.screen);
  });
});

document.getElementById('carousel-back').addEventListener('click', () => showScreen('wardrobe'));
document.getElementById('add-back').addEventListener('click', () => showScreen('wardrobe'));

// Wardrobe

let longPressTimer = null;

async function loadWardrobe() {
  const items = await fetch('/api/clothes').then(r => r.json());
  const grid = document.getElementById('wardrobe-grid');
  const empty = document.getElementById('no-clothes');
  grid.innerHTML = '';

  if (!items.length) {
    empty.hidden = false;
    return;
  }
  empty.hidden = true;

  items.forEach(item => {
    const card = document.createElement('div');
    card.className = 'wardrobe-card';
    card.innerHTML = `
      <img src="/uploads/${item.photo_path}" alt="${item.name}" loading="lazy">
      <div class="wardrobe-card-label">${item.name}</div>
      ${item.outfit_count > 0
        ? `<span class="outfit-badge">${item.outfit_count} outfit${item.outfit_count !== 1 ? 's' : ''}</span>`
        : ''}
    `;

    card.addEventListener('click', () => loadCarousel(item));

    card.addEventListener('pointerdown', () => {
      longPressTimer = setTimeout(() => deleteItem(item.id), 600);
    });
    card.addEventListener('pointerup', () => clearTimeout(longPressTimer));
    card.addEventListener('pointermove', () => clearTimeout(longPressTimer));
    card.addEventListener('pointerleave', () => clearTimeout(longPressTimer));

    grid.appendChild(card);
  });
}

async function deleteItem(id) {
  navigator.vibrate?.(50);
  if (!confirm('Remove this item from your wardrobe?')) return;
  await fetch(`/api/clothes/${id}`, { method: 'DELETE' });
  loadWardrobe();
}

// Carousel

async function loadCarousel(item) {
  document.getElementById('carousel-title').textContent = item.name;
  document.getElementById('carousel-pos').textContent = '';
  showScreen('carousel');

  const outfits = await fetch(`/api/outfits?item_id=${item.id}`).then(r => r.json());
  const track = document.getElementById('carousel-track');
  const empty = document.getElementById('no-outfits');
  track.innerHTML = '';

  if (!outfits.length) {
    empty.hidden = false;
    return;
  }
  empty.hidden = true;

  const total = outfits.length;
  document.getElementById('carousel-pos').textContent = `1 / ${total}`;

  outfits.forEach(outfit => {
    const score = Math.round(outfit.score * 100);
    const scoreColor = score >= 75
      ? 'var(--score-high)'
      : score >= 50 ? 'var(--score-mid)' : 'var(--score-low)';

    const card = document.createElement('div');
    card.className = 'carousel-card';
    card.innerHTML = `
      <div class="outfit-items">
        ${outfit.items.map(i => `
          <div class="outfit-item">
            <img class="outfit-item-img" src="/uploads/${i.photo_path}" alt="${i.name}" loading="lazy">
            <div class="outfit-item-info">
              <div class="outfit-item-name">${i.name}</div>
              <div class="outfit-item-cat">${capitalize(i.category)}</div>
            </div>
          </div>`).join('')}
      </div>
      <div class="score-section">
        <div class="score-label">${score}% match</div>
        <div class="score-bar-wrap">
          <div class="score-bar-fill" style="width:${score}%; background:${scoreColor}"></div>
        </div>
        <div class="occasion-label">${capitalize(outfit.occasion)}</div>
      </div>
    `;
    track.appendChild(card);
  });

  track.scrollLeft = 0;
  track.addEventListener('scroll', () => {
    const idx = Math.round(track.scrollLeft / track.clientWidth);
    document.getElementById('carousel-pos').textContent = `${idx + 1} / ${total}`;
  }, { passive: true });
}

// Add Item

const photoInput = document.getElementById('photo-input');
const photoPreview = document.getElementById('photo-preview');
const photoPlaceholder = document.getElementById('photo-placeholder');

photoInput.addEventListener('change', e => {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = ev => {
    photoPreview.src = ev.target.result;
    photoPreview.hidden = false;
    photoPlaceholder.hidden = true;
  };
  reader.readAsDataURL(file);
});

document.getElementById('add-form').addEventListener('submit', async e => {
  e.preventDefault();
  const btn = document.getElementById('add-submit');
  const errEl = document.getElementById('add-error');
  errEl.hidden = true;
  btn.disabled = true;
  btn.textContent = 'Adding...';

  const resp = await fetch('/api/clothes', { method: 'POST', body: new FormData(e.target) });

  btn.disabled = false;
  btn.textContent = 'Add to Wardrobe';

  if (resp.ok) {
    e.target.reset();
    photoPreview.hidden = true;
    photoPlaceholder.hidden = false;
    await loadWardrobe();
    showScreen('wardrobe');
  } else {
    errEl.textContent = 'Failed to add item. Check all fields and try again.';
    errEl.hidden = false;
  }
});

// Util

function capitalize(str) {
  return str ? str.charAt(0).toUpperCase() + str.slice(1) : '';
}

// Init
loadWardrobe();
```

- [ ] **Step 2: Start server and manual smoke test**

```
python app.py
```

Open http://localhost:5000. Verify:
- Wardrobe grid shows clothing photos with outfit count badges
- Tapping a card navigates to carousel; header shows item name + `1 / N`
- Swiping left/right moves between outfit cards; position indicator updates
- Back arrow returns to wardrobe
- Bottom nav `+` opens Add Item screen
- Choosing a photo shows preview immediately
- Submitting form adds item, returns to wardrobe, badges update

- [ ] **Step 3: Run full test suite**

```
pytest tests/ -v
```

Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add static/app.js
git commit -m "feat: rewrite app.js — mobile screen navigation, wardrobe grid, swipe carousel, add form"
```

---

## Self-Review

| Spec requirement | Task |
|----------------|------|
| Auto-regenerate outfits on POST | 1 |
| Auto-regenerate outfits on DELETE | 1 |
| outfit_count on GET /api/clothes | 2 |
| GET /api/outfits?item_id=X filter | 3 |
| GET /api/outfits returns full item objects | 3 |
| GET /api/suggest reads from DB | 4 |
| 3-screen stack navigation | 5, 7 |
| White theme, mobile-first CSS | 6 |
| CSS scroll-snap carousel | 6, 7 |
| Position indicator (1 / N) | 7 |
| Outfit count badge on wardrobe cards | 6, 7 |
| Color-coded score bar | 6, 7 |
| Photo picker (camera + gallery) | 5 |
| Photo preview before submit | 7 |
| Long-press delete + haptic | 7 |
| Submit loading/disabled state | 7 |
| Bottom nav (Wardrobe + Add) | 5, 6 |

All requirements covered. No placeholders. Types consistent across tasks — `outfit.items` (list of item dicts with `id`, `photo_path`, `name`, `category`) used identically in Tasks 3, 4, and 7. `outfit_count` added in Task 2 and consumed in Task 7.
