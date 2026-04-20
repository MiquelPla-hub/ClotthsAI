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

let _carouselScrollHandler = null;

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
  if (_carouselScrollHandler) track.removeEventListener('scroll', _carouselScrollHandler);
  _carouselScrollHandler = () => {
    const idx = Math.round(track.scrollLeft / track.clientWidth);
    document.getElementById('carousel-pos').textContent = `${idx + 1} / ${total}`;
  };
  track.addEventListener('scroll', _carouselScrollHandler, { passive: true });
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
