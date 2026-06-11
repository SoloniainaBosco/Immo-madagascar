# =============================================================
# src/app.py — VERSION CORRIGÉE
# Bugs corrigés :
#   1. requests sync → httpx async (performance)
#   2. setEx() supprimait les chiffres
#   3. Index markers/cards désynchronisés après filtre
#   4. activeIndex non réinitialisé entre recherches
#   5. entites : champs inutiles masqués
#   6. reload=True retiré
# =============================================================

import os
import sys
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config.settings import ES_HOST, ES_INDEX, ES_TIMEOUT
from nlp_parser import parser_phrase, construire_query

app = FastAPI(title="Immo Madagascar API", version="3.1.0")


class RequeteRecherche(BaseModel):
    phrase: str


PAGE_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <title>Immo Madagascar | Recherche immobilière intelligente</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400;14..32,500;14..32,600;14..32,700;14..32,800;14..32,900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }

    :root {
      --primary:          #0b6e4f;
      --primary-dark:     #064e3b;
      --primary-light:    #e6f7f1;
      --primary-gradient: linear-gradient(135deg, #0b6e4f 0%, #064e3b 100%);
      --accent:           #f97316;
      --gray-50:  #f9fafb;
      --gray-100: #f3f4f6;
      --gray-200: #e5e7eb;
      --gray-300: #d1d5db;
      --gray-600: #4b5563;
      --gray-700: #374151;
      --gray-800: #1f2937;
      --shadow-xs: 0 1px 2px rgba(0,0,0,.05);
      --shadow-sm: 0 1px 3px rgba(0,0,0,.10);
      --shadow-md: 0 4px 6px  rgba(0,0,0,.10);
      --shadow-lg: 0 10px 15px rgba(0,0,0,.10);
      --shadow-xl: 0 20px 25px rgba(0,0,0,.10);
      --shadow-2xl:0 25px 50px rgba(0,0,0,.25);
      --radius-lg: 1rem;
      --radius-xl: 1.5rem;
    }

    body {
      font-family: 'Inter', system-ui, sans-serif;
      background: linear-gradient(145deg, var(--gray-50) 0%, #fff 100%);
      color: var(--gray-800);
      padding-top: 88px;
      min-height: 100vh;
    }

    /* ── HEADER ─────────────────────────────── */
    .site-header {
      position: fixed; top:0; left:0; right:0;
      background: rgba(255,255,255,.98);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid rgba(0,0,0,.05);
      box-shadow: var(--shadow-sm);
      z-index: 1000;
      padding: .3rem 2rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      transition: all .3s;
    }
    .site-header.scrolled { padding: .75rem 2rem; box-shadow: var(--shadow-md); }

    .logo-area {
      position: absolute; left: 70%;
      transform: translateX(-50%);
      text-align: center;
      pointer-events: none;
    }
    .logo-area h1 {
      font-size: 2rem; font-weight:700;
      color: #064e3b; letter-spacing:1px;
      display: inline-block; position: relative;
    }
    .logo-area h1::after {
      content:'';
      position:absolute; bottom:-5px; left:0; right:0;
      height:3px;
      background: linear-gradient(90deg,#0b6e4f,#f97316,#0b6e4f);
      border-radius:3px;
    }
    .logo-area p { font-size:.7rem; color:var(--gray-600); margin-top:.2rem; }

    /* ── SEARCH ──────────────────────────────── */
    .search-section { flex: 0 1 500px; min-width:280px; z-index:2; }

    .search-container {
      background: white;
      border-radius: 60px;
      border: 1px solid var(--gray-200);
      box-shadow: var(--shadow-xs);
      transition: all .3s;
    }
    .search-container:focus-within {
      border-color: var(--primary);
      box-shadow: 0 0 0 4px rgba(11,110,79,.1);
      transform: translateY(-1px);
    }
    .search-row {
      display:flex; align-items:center;
      background:white; border-radius:60px;
      padding: .15rem .15rem .15rem 1.2rem;
    }
    .search-row input {
      flex:1; border:none;
      padding:.75rem 0; font-size:.95rem;
      font-weight:500; outline:none;
      background:transparent; color:var(--gray-800);
    }
    .search-row input::placeholder { color:#9ca3af; font-weight:400; }

    .search-row button {
      background: var(--primary-gradient);
      border:none; color:white;
      font-weight:600; padding:.55rem 1.3rem;
      border-radius:40px; cursor:pointer;
      transition:all .2s; font-size:.9rem;
      display:inline-flex; align-items:center; gap:6px;
    }
    .search-row button:hover { transform:translateY(-2px); box-shadow:var(--shadow-md); }

    .clear-btn {
      background:transparent !important;
      color:var(--gray-600) !important;
      padding:.5rem .8rem !important;
      font-size:1.1rem !important;
    }
    .clear-btn:hover {
      background:var(--gray-100) !important;
      transform:none !important;
      box-shadow:none !important;
    }

    /* ── LAYOUT ──────────────────────────────── */
    .layout {
      max-width:1440px; margin:.25rem auto .5rem;
      padding:0 1rem; display:flex;
      gap:1rem; align-items:flex-start;
    }
    .results-panel { flex:1.2; min-width:0; }
    .map-panel {
      flex:1.8; position:sticky;
      top:100px; align-self:flex-start;
    }
    #map {
      height:550px; width:100%;
      border-radius:var(--radius-xl);
      box-shadow:var(--shadow-xl);
      border:2px solid white;
      transition:box-shadow .3s;
    }
    #map:hover { box-shadow:var(--shadow-2xl); }

    /* ── WELCOME ─────────────────────────────── */
    .welcome-section {
      background:white; border-radius:var(--radius-xl);
      padding:2rem; box-shadow:var(--shadow-lg);
      border:1px solid var(--gray-200);
      animation: fadeInUp .6s ease;
    }
    @keyframes fadeInUp {
      from { opacity:0; transform:translateY(20px); }
      to   { opacity:1; transform:translateY(0); }
    }
    .welcome-section h2 { font-size:1.6rem; font-weight:800; color:var(--primary-dark); margin-bottom:.5rem; }

    .welcome-cards { display:flex; flex-wrap:wrap; gap:1rem; margin:1.5rem 0; }
    .demo-card {
      background:linear-gradient(135deg,white 0%,var(--gray-50) 100%);
      border-radius:var(--radius-lg); padding:1.2rem;
      flex:1; min-width:160px; cursor:pointer;
      transition:all .3s; border:1px solid var(--gray-200);
    }
    .demo-card:hover {
      transform:translateY(-4px); box-shadow:var(--shadow-xl);
      border-color:var(--primary-light); background:white;
    }
    .demo-card .price { font-weight:800; color:var(--accent); font-size:1.2rem; margin-bottom:.3rem; }

    .guide-list { background:var(--primary-light); padding:1.2rem; border-radius:var(--radius-lg); margin-top:1.5rem; }
    .stats-badge {
      display:inline-block; background:var(--primary); color:white;
      padding:.4rem 1.2rem; border-radius:30px;
      font-size:.8rem; font-weight:600;
      margin-right:.6rem; margin-bottom:.6rem;
    }

    /* ── RÉSULTATS ───────────────────────────── */
    .stats-bar {
      background:var(--primary-light); padding:1rem 1.2rem;
      border-radius:var(--radius-lg); margin-bottom:1.2rem;
      display:flex; justify-content:space-between;
      align-items:center; flex-wrap:wrap; gap:.8rem;
      font-weight:600; border-left:4px solid var(--primary);
    }
    .sort-btn {
      background:white; border:1px solid var(--gray-300);
      border-radius:30px; padding:.4rem 1rem;
      font-size:.75rem; font-weight:600;
      cursor:pointer; transition:all .2s;
    }
    .sort-btn:hover { border-color:var(--primary); background:var(--primary-light); }

    .filter-chips { display:flex; flex-wrap:wrap; gap:.6rem; margin-bottom:1.5rem; }
    .chip {
      background:white; border:1px solid var(--gray-200);
      border-radius:40px; padding:.4rem 1.2rem;
      font-size:.8rem; font-weight:600; cursor:pointer;
      transition:all .2s; display:inline-flex;
      align-items:center; gap:6px;
    }
    .chip:hover { border-color:var(--primary); background:var(--primary-light); transform:translateY(-1px); }
    .chip.active { background:var(--primary-gradient); border-color:var(--primary); color:white; }

    .property-card {
      background:white; border-radius:var(--radius-lg);
      padding:1.2rem; margin-bottom:1rem;
      box-shadow:var(--shadow-sm); border:1px solid var(--gray-200);
      cursor:pointer; transition:all .3s;
    }
    .property-card:hover { transform:translateY(-3px); box-shadow:var(--shadow-xl); border-color:var(--primary-light); }
    .property-card.active {
      border-left:4px solid var(--accent);
      background:linear-gradient(135deg,white 0%,#fff7ed 100%);
    }

    .price { font-size:1.3rem; font-weight:800; color:var(--accent); margin:.4rem 0; }
    .type-tag { font-size:.7rem; font-weight:700; padding:.3rem 1rem; border-radius:30px; display:inline-block; }
    .type-maison      { background:#ffedd5; color:#c2410c; }
    .type-villa       { background:#fee2e2; color:#b91c1c; }
    .type-appartement { background:#e0f2fe; color:#075985; }
    .type-duplex      { background:#f3e8ff; color:#6b21a5; }
    .type-terrain     { background:#fef3c7; color:#854d0e; }
    .type-studio      { background:#dcfce7; color:#166534; }

    .entity-badge {
      background:var(--gray-100); padding:.2rem .8rem;
      border-radius:20px; font-size:.7rem;
      font-weight:500; display:inline-block; margin:.2rem;
    }

    .loading-spinner {
      display:none; justify-content:center;
      align-items:center; gap:1rem; padding:2rem;
      background:white; border-radius:var(--radius-lg);
    }
    .spinner {
      width:32px; height:32px;
      border:3px solid var(--gray-200);
      border-top-color:var(--primary);
      border-radius:50%;
      animation:spin .7s linear infinite;
    }
    @keyframes spin { to { transform:rotate(360deg); } }

    /* ── RESPONSIVE ──────────────────────────── */
    @media (max-width:968px) {
      body { padding-top:120px; }
      .site-header { flex-direction:column; align-items:stretch; gap:1rem; padding:1rem; }
      .logo-area { position:static; transform:none; margin-bottom:.5rem; }
      .logo-area h1 { font-size:1.8rem; }
      .layout { flex-direction:column; padding:0 1rem; }
      .map-panel { position:static; width:100%; }
      #map { height:400px; }
      .search-section { max-width:100%; }
    }
    @media (max-width:640px) {
      .logo-area h1 { font-size:1.5rem; }
      .welcome-cards { flex-direction:column; }
      .stats-bar { flex-direction:column; align-items:flex-start; }
    }

    /* ── SCROLLBAR ───────────────────────────── */
    ::-webkit-scrollbar { width:8px; height:8px; }
    ::-webkit-scrollbar-track { background:var(--gray-100); border-radius:10px; }
    ::-webkit-scrollbar-thumb { background:var(--primary); border-radius:10px; }
    ::-webkit-scrollbar-thumb:hover { background:var(--primary-dark); }
  </style>
</head>
<body>

<header class="site-header" id="siteHeader">
  <div class="search-section">
    <div class="search-container">
      <div class="search-row">
        <input type="text" id="searchInput"
          placeholder="ex: villa avec piscine à Nosy Be, budget 400 millions"
          autocomplete="off"
          onkeydown="if(event.key==='Enter') rechercher()">
        <button class="clear-btn" onclick="effacerRecherche()">
          <i class="fas fa-times"></i>
        </button>
        <button onclick="rechercher()">
          <i class="fas fa-search"></i> Rechercher
        </button>
      </div>
    </div>
  </div>

  <div class="logo-area">
    <h1>Immo Madagascar</h1>
    <p>Recherche immobilière intelligente</p>
  </div>
  <div style="width:80px;"></div>
</header>

<div class="layout">
  <div class="results-panel">
    <div id="loading" class="loading-spinner">
      <div class="spinner"></div>
      <span>Recherche en cours...</span>
    </div>
    <div id="results"></div>
    <div id="welcome" class="welcome-section">
      <h2><i class="fas fa-search"></i> Trouvez votre bien en langage naturel</h2>
      <p>Recherchez comme vous parlez :
        <strong>"maison avec jardin à Ivandry moins de 300 millions"</strong>
      </p>
      <div class="welcome-cards">
        <div class="demo-card"
          onclick="setExText('maison familiale Antananarivo 4 chambres 250 millions')">
          <div class="price"><i class="fas fa-home"></i> Maison familiale</div>
          <div>Tana · 4 chambres · jardin</div>
          <small><i class="fas fa-mouse-pointer"></i> Cliquez pour tester</small>
        </div>
        <div class="demo-card"
          onclick="setExText('duplex moderne à Mahajanga 3 chambres climatisation')">
          <div class="price"><i class="fas fa-building"></i> Duplex moderne</div>
          <div>Mahajanga · 3 chambres · clim</div>
          <small><i class="fas fa-mouse-pointer"></i> Cliquez pour tester</small>
        </div>
        <div class="demo-card"
          onclick="setExText('terrain constructible Toamasina 150 millions')">
          <div class="price"><i class="fas fa-mountain"></i> Terrain</div>
          <div>Toamasina · 600 m²</div>
          <small><i class="fas fa-mouse-pointer"></i> Cliquez pour tester</small>
        </div>
        <div class="demo-card"
          onclick="setExText('villa de luxe avec piscine Nosy Be')">
          <div class="price"><i class="fas fa-crown"></i> Villa de luxe</div>
          <div>Nosy Be · piscine · vue mer</div>
          <small><i class="fas fa-mouse-pointer"></i> Cliquez pour tester</small>
        </div>
      </div>
      <div class="guide-list">
        <span class="stats-badge"><i class="fas fa-database"></i> 20 000+ biens</span>
        <span class="stats-badge"><i class="fas fa-map-marker-alt"></i> 8 villes malgaches</span>
        <span class="stats-badge"><i class="fas fa-microchip"></i> NLP intégré</span>
        <span class="stats-badge"><i class="fas fa-tachometer-alt"></i> Recherche instantanée</span>
        <p style="margin-top:1rem;">
          <strong><i class="fas fa-lightbulb"></i> Comment ça marche ?</strong>
          Notre moteur analyse votre phrase, extrait le type de bien, la ville,
          le prix, les équipements et affiche les résultats sur la carte.
        </p>
      </div>
    </div>
  </div>

  <div class="map-panel">
    <div id="map"></div>
  </div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
// ── HEADER SCROLL ─────────────────────────────────────────────
window.addEventListener('scroll', () => {
  document.getElementById('siteHeader')
    .classList.toggle('scrolled', window.scrollY > 10);
});

// ── CARTE LEAFLET ─────────────────────────────────────────────
const TYPE_COLORS = {
  maison:'#e67e22', villa:'#c2410c', appartement:'#2563eb',
  studio:'#16a34a', terrain:'#a16207', duplex:'#7c3aed'
};
const getColor = t => TYPE_COLORS[t] || '#9ca3af';

const TYPE_ICONS = {
  maison:'fa-home', villa:'fa-crown', appartement:'fa-building',
  duplex:'fa-building', terrain:'fa-mountain', studio:'fa-city'
};
const getIcon = t => TYPE_ICONS[t] || 'fa-home';

const map = L.map('map').setView([-18.9, 47.5], 6);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '© OpenStreetMap', maxZoom: 19
}).addTo(map);

// ── ÉTAT GLOBAL ───────────────────────────────────────────────
let markers        = [];
let activeIndex    = null;   // FIX: réinitialisé à chaque recherche
let currentBiens   = [];     // FIX: liste synchronisée avec markers[]
let currentSort    = 'none';
let currentFilter  = 'all';
let lastDataRaw    = null;

// ── MARKERS ───────────────────────────────────────────────────
function buildIcon(type, isActive) {
  const s = isActive ? 18 : 12;
  return L.divIcon({
    html: `<div style="width:${s}px;height:${s}px;background:${getColor(type)};border:3px solid white;border-radius:50%;box-shadow:0 2px 8px rgba(0,0,0,.25);transition:all .2s;"></div>`,
    iconSize: [s, s], iconAnchor: [s/2, s/2]
  });
}

function clearMarkers() {
  markers.forEach(m => map.removeLayer(m));
  markers = [];
  activeIndex = null;  // FIX BUG 5 : réinitialiser à chaque effacement
}

// FIX BUG 3 & 4 : displayMarkers reçoit la liste déjà filtrée/triée
// markers[i] correspond exactement à currentBiens[i]
function displayMarkers(biens) {
  clearMarkers();
  const bounds = [];
  biens.forEach((b, idx) => {
    if (!b.localisation?.lat) return;
    const { lat, lon } = b.localisation;
    const marker = L.marker([lat, lon], { icon: buildIcon(b.type_bien, false) });
    marker.bindPopup(`
      <div style="font-family:Inter;min-width:180px;">
        <strong style="font-size:.9rem;">${escapeHtml(b.titre)}</strong><br>
        <span style="color:#f97316;font-size:1.1rem;font-weight:800;">${(b.prix_ariary/1e6).toFixed(1)} MAr</span><br>
        <span style="font-size:.75rem;color:#4b5563;">${b.quartier}, ${b.ville}</span><br>
        <span style="font-size:.7rem;">${b.surface} m² | ${b.nb_pieces} pièces</span>
      </div>`, { maxWidth: 220 });

    marker.on('click', () => {
      // Désactiver l'ancien marker
      if (activeIndex !== null && markers[activeIndex]) {
        markers[activeIndex].setIcon(buildIcon(currentBiens[activeIndex].type_bien, false));
      }
      marker.setIcon(buildIcon(b.type_bien, true));
      activeIndex = idx;
      highlightCard(idx);
    });

    marker.addTo(map);
    markers.push(marker);
    bounds.push([lat, lon]);
  });
  if (bounds.length) map.fitBounds(bounds, { padding: [40,40] });
}

function highlightCard(index) {
  document.querySelectorAll('.property-card').forEach(c => c.classList.remove('active'));
  const card = document.getElementById(`card-${index}`);
  if (card) {
    card.classList.add('active');
    card.scrollIntoView({ behavior:'smooth', block:'nearest' });
  }
}

// FIX BUG 3 & 4 : flyToCard utilise currentBiens qui est synchronisé avec markers
window.flyToCard = function(idx, lat, lon) {
  map.flyTo([lat, lon], 15, { duration: 0.8 });
  setTimeout(() => {
    if (activeIndex !== null && markers[activeIndex]) {
      markers[activeIndex].setIcon(buildIcon(currentBiens[activeIndex].type_bien, false));
    }
    if (markers[idx]) {
      markers[idx].setIcon(buildIcon(currentBiens[idx].type_bien, true));
      markers[idx].openPopup();
    }
    activeIndex = idx;
    highlightCard(idx);
  }, 850); // après la fin du flyTo
};

// ── RENDU RÉSULTATS ───────────────────────────────────────────
function renderResults(data) {
  document.getElementById('welcome').style.display = 'none';
  const container = document.getElementById('results');

  if (data.detail) {
    container.innerHTML = `<div style="padding:2rem;text-align:center;background:white;border-radius:1rem;">
      <i class="fas fa-exclamation-triangle"></i> ${escapeHtml(data.detail)}
    </div>`;
    return;
  }

  // ── BARRE STATS + TRI ──
  let html = `<div class="stats-bar">
    <span><i class="fas fa-home"></i> <strong>${data.total}</strong> bien(s) pour « ${escapeHtml(data.phrase)} »</span>
    <div>
      <button class="sort-btn" onclick="setSort('asc')"><i class="fas fa-arrow-up"></i> Prix ↑</button>
      <button class="sort-btn" onclick="setSort('desc')"><i class="fas fa-arrow-down"></i> Prix ↓</button>
    </div>
  </div>`;

  // ── FILTRES PAR TYPE ──
  const allTypes = [...new Set(data.biens.map(b => b.type_bien))];
  html += `<div class="filter-chips">
    <span class="chip ${currentFilter==='all'?'active':''}" onclick="setTypeFilter('all')">
      <i class="fas fa-list"></i> Tous
    </span>
    ${allTypes.map(t => `
      <span class="chip ${currentFilter===t?'active':''}" onclick="setTypeFilter('${t}')">
        <i class="fas ${getIcon(t)}"></i> ${t.charAt(0).toUpperCase()+t.slice(1)}
      </span>`).join('')}
  </div>`;

  // FIX BUG 6 : masquer les champs techniques dans les entités
  const CHAMPS_EXCLUS = new Set(['phrase_originale','coords','rayon_km']);
  const entitesFiltrees = Object.entries(data.entites || {})
    .filter(([k,v]) => v && !CHAMPS_EXCLUS.has(k));
  if (entitesFiltrees.length) {
    html += `<div style="background:white;border-radius:1rem;padding:.8rem;margin-bottom:1rem;border:1px solid #e5e7eb;">
      <i class="fas fa-microchip"></i> <strong>Critères détectés :</strong><br>
      ${entitesFiltrees.map(([k,v]) => `<span class="entity-badge">${k}: ${Array.isArray(v)?v.join(', '):v}</span>`).join(' ')}
    </div>`;
  }

  // ── FILTRE + TRI ──
  let biensAffiches = [...data.biens];
  if (currentFilter !== 'all') biensAffiches = biensAffiches.filter(b => b.type_bien === currentFilter);
  if (currentSort === 'asc')  biensAffiches.sort((a,b) => a.prix_ariary - b.prix_ariary);
  if (currentSort === 'desc') biensAffiches.sort((a,b) => b.prix_ariary - a.prix_ariary);

  if (!biensAffiches.length) {
    container.innerHTML = html + `<div style="padding:2rem;text-align:center;">
      <i class="fas fa-filter"></i> Aucun bien avec ce filtre.
    </div>`;
    return;
  }

  // ── CARTES ──
  biensAffiches.forEach((b, idx) => {
    const equipHtml = (b.equipements||[]).map(e =>
      `<span style="background:#f3f4f6;padding:.2rem .7rem;border-radius:12px;font-size:.7rem;margin:.2rem;">
        <i class="fas fa-check-circle"></i> ${escapeHtml(e)}
      </span>`
    ).join('');
    const lat = b.localisation?.lat ?? 0;
    const lon = b.localisation?.lon ?? 0;
    html += `
    <div class="property-card" id="card-${idx}"
      onclick="flyToCard(${idx},${lat},${lon})">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <strong>
          <i class="fas ${getIcon(b.type_bien)}"></i>
          ${escapeHtml(b.titre)}
        </strong>
        <span class="type-tag type-${b.type_bien}">${b.type_bien}</span>
      </div>
      <div class="price">
        ${(b.prix_ariary/1e6).toFixed(1)} MAr
        <small>· ${Math.round(b.prix_m2_ariary/1000)}k Ar/m²</small>
      </div>
      <div>
        <i class="fas fa-map-marker-alt"></i> ${escapeHtml(b.quartier)}, ${escapeHtml(b.ville)}
        &nbsp;·&nbsp;
        <i class="fas fa-arrows-alt"></i> ${b.surface} m²
        &nbsp;·&nbsp;
        <i class="fas fa-bed"></i> ${b.nb_pieces} pièces
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:.3rem;margin-top:.6rem;">${equipHtml}</div>
    </div>`;
  });

  container.innerHTML = html;

  // FIX BUG 3 : synchroniser currentBiens avec markers APRÈS rendu
  currentBiens = biensAffiches;
  displayMarkers(currentBiens);
}

// ── RECHERCHE ─────────────────────────────────────────────────
async function rechercher() {
  const phrase = document.getElementById('searchInput').value.trim();
  if (!phrase) return;

  document.getElementById('loading').style.display = 'flex';
  document.getElementById('results').innerHTML = '';
  clearMarkers();

  try {
    const resp = await fetch('/api/recherche', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phrase })
    });
    const data = await resp.json();
    lastDataRaw    = data;
    currentSort    = 'none';
    currentFilter  = 'all';
    renderResults(data);
  } catch {
    document.getElementById('results').innerHTML = `
      <div style="text-align:center;padding:2rem;background:white;border-radius:1rem;">
        <i class="fas fa-wifi"></i>  Erreur réseau
      </div>`;
  } finally {
    document.getElementById('loading').style.display = 'none';
  }
}

function effacerRecherche() {
  document.getElementById('searchInput').value = '';
  document.getElementById('results').innerHTML = '';
  document.getElementById('welcome').style.display = 'block';
  clearMarkers();
  currentBiens  = [];
  lastDataRaw   = null;
  map.setView([-18.9, 47.5], 6);
}

// FIX BUG 2 : setExText conserve les chiffres (pas de remplacement regex)
function setExText(text) {
  document.getElementById('searchInput').value = text;
  rechercher();
}

function setSort(order) {
  currentSort = order;
  if (lastDataRaw) renderResults(lastDataRaw);
}

function setTypeFilter(type) {
  currentFilter = type;
  if (lastDataRaw) renderResults(lastDataRaw);
}

function escapeHtml(str) {
  return (str || '').replace(/[&<>"]/g, m =>
    ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[m]);
}
</script>
</body>
</html>"""


# ── ROUTES FASTAPI ─────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    return PAGE_HTML


# FIX BUG 1 : httpx.AsyncClient au lieu de requests (non bloquant)
@app.post("/api/recherche")
async def recherche(body: RequeteRecherche):
    phrase = body.phrase.strip()
    if not phrase:
        raise HTTPException(status_code=400, detail="Phrase vide.")

    entites  = parser_phrase(phrase)
    query_es = construire_query(entites)

    try:
        async with httpx.AsyncClient(timeout=ES_TIMEOUT) as client:
            reponse = await client.post(
                f"{ES_HOST}/{ES_INDEX}/_search",
                json=query_es,
                headers={"Content-Type": "application/json"}
            )
            reponse.raise_for_status()
            hits = reponse.json()["hits"]
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Elasticsearch inaccessible.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "phrase":  phrase,
        "entites": entites,
        "total":   hits["total"]["value"],
        "biens":   [h["_source"] for h in hits["hits"]],
    }


@app.get("/api/stats")
async def stats():
    try:
        async with httpx.AsyncClient(timeout=ES_TIMEOUT) as client:
            r = await client.get(f"{ES_HOST}/{ES_INDEX}/_count")
            total = r.json().get("count", 0)
        return {"index": ES_INDEX, "total": total, "status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "Immo Madagascar API"}


# ── LANCEMENT ──────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
 
    print("  IMMO MADAGASCAR — Version corrigée")
    print("  Interface : http://localhost:5000")
    print("  API docs  : http://localhost:5000/docs")
   
    
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=False)