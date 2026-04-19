let allClothes = [];
let currentStyle = 'all';
let currentCategory = 'all';

const $ = id => document.getElementById(id);

// Tab switching
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
    if (btn.dataset.tab === 'outfits') loadOutfits();
    if (btn.dataset.tab === 'wardrobe') loadWardrobe();
  });
});

// Style filter buttons
document.querySelectorAll('.style-filter .filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.style-filter .filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentStyle = btn.dataset.style;
    loadOutfits();
  });
});

// Category filter buttons
document.querySelectorAll('.category-filter .filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.category-filter .filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentCategory = btn.dataset.category;
    renderWardrobe();
  });
});

// ---- Outfits ----

async function loadOutfits() {
  const outfits = await fetch(`/api/suggest?style=${currentStyle}&limit=20`).then(r => r.json());
  renderOutfits(outfits);
}

function renderOutfits(outfits) {
  const hero = $('hero-outfit');
  const grid = $('outfit-grid');
  const noOutfits = $('no-outfits');

  hero.innerHTML = '';
  grid.innerHTML = '';

  if (!outfits.length) {
    noOutfits.hidden = false;
    return;
  }
  noOutfits.hidden = true;

  const top = outfits[0];
  hero.innerHTML = `
    <div class="hero-card">
      <span class="hero-badge">★ Top Pick Today</span>
      <div class="hero-items">
        ${top.items.map(item => `
          <div>
            <img class="hero-item-img" src="/uploads/${item.photo_path}" alt="${item.name}">
            <div class="hero-item-label">${item.name}</div>
          </div>`).join('')}
      </div>
      <div class="hero-name">${top.items.map(i => i.name).join(' + ')}</div>
      <div class="hero-meta">
        ${capitalize(top.occasion)}
        <span class="score-badge">${Math.round(top.score * 100)}% match</span>
      </div>
    </div>`;

  outfits.slice(1).forEach(outfit => {
    const card = document.createElement('div');
    card.className = 'outfit-card';
    card.innerHTML = `
      <div class="outfit-card-imgs">
        ${outfit.items.map(i => `
          <img class="outfit-card-img" src="/uploads/${i.photo_path}" alt="${i.name}">`).join('')}
      </div>
      <div class="outfit-card-name">${outfit.items.map(i => i.name).join(' + ')}</div>
      <div class="outfit-card-score">${Math.round(outfit.score * 100)}% match</div>
      <div class="outfit-card-style">${capitalize(outfit.occasion)}</div>`;
    grid.appendChild(card);
  });
}

// ---- Wardrobe ----

async function loadWardrobe() {
  allClothes = await fetch('/api/clothes').then(r => r.json());
  renderWardrobe();
}

function renderWardrobe() {
  const grid = $('wardrobe-grid');
  const noClothes = $('no-clothes');
  grid.innerHTML = '';

  const filtered = currentCategory === 'all'
    ? allClothes
    : allClothes.filter(c => c.category === currentCategory);

  if (!filtered.length) {
    noClothes.hidden = false;
    return;
  }
  noClothes.hidden = true;

  filtered.forEach(item => {
    const card = document.createElement('div');
    card.className = 'wardrobe-card';
    card.innerHTML = `
      <img src="/uploads/${item.photo_path}" alt="${item.name}">
      <button class="delete-btn" data-id="${item.id}" title="Remove">✕</button>
      <div class="wardrobe-card-info">
        <div class="wardrobe-card-name">${item.name}</div>
        <div class="wardrobe-card-meta">${capitalize(item.category)} · ${item.style_tags.join(', ')}</div>
      </div>`;
    card.querySelector('.delete-btn').addEventListener('click', () => deleteItem(item.id));
    grid.appendChild(card);
  });
}

async function deleteItem(id) {
  if (!confirm('Remove this item from your wardrobe?')) return;
  await fetch(`/api/clothes/${id}`, { method: 'DELETE' });
  loadWardrobe();
}

// ---- Add Item form ----

$('add-form').addEventListener('submit', async e => {
  e.preventDefault();
  const resp = await fetch('/api/clothes', { method: 'POST', body: new FormData(e.target) });
  if (resp.ok) {
    e.target.reset();
    const msg = $('add-success');
    msg.hidden = false;
    setTimeout(() => { msg.hidden = true; }, 3000);
  }
});

// ---- Util ----

function capitalize(str) {
  return str ? str.charAt(0).toUpperCase() + str.slice(1) : '';
}

// Init
loadOutfits();
