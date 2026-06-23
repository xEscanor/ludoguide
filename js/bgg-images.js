(function() {
  'use strict';
  const CACHE_PREFIX = 'ludoref_bgg_img_';
  const CACHE_TTL = 30 * 24 * 60 * 60 * 1000;
  const BGG_API = 'https://boardgamegeek.com/xmlapi2/thing?id=';

  function getSlug() {
    const m = window.location.pathname.match(/\/jeux\/([^\/]+)\.html/);
    return m ? m[1] : null;
  }

  function getCache(slug) {
    try {
      const raw = localStorage.getItem(CACHE_PREFIX + slug);
      if (!raw) return null;
      const d = JSON.parse(raw);
      if (Date.now() - d.ts > CACHE_TTL) { localStorage.removeItem(CACHE_PREFIX + slug); return null; }
      return d.img;
    } catch(e) { return null; }
  }

  function setCache(slug, url) {
    try { localStorage.setItem(CACHE_PREFIX + slug, JSON.stringify({img: url, ts: Date.now()})); } catch(e) {}
  }

  function parseImg(xml) {
    try {
      const doc = new DOMParser().parseFromString(xml, 'text/xml');
      const el = doc.querySelector('image');
      if (!el || !el.textContent) return null;
      let u = el.textContent.trim();
      if (u.startsWith('//')) u = 'https:' + u;
      return u;
    } catch(e) { return null; }
  }

  function showImg(container, url) {
    const img = document.createElement('img');
    img.src = url;
    img.alt = document.title.replace(' \u2014 LudoRef', '');
    img.style.cssText = 'width:100%;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,.3);display:block;';
    img.loading = 'lazy';
    img.onerror = () => showPlaceholder(container);
    container.innerHTML = '';
    container.appendChild(img);
  }

  function showPlaceholder(container) {
    container.innerHTML = '<div style="width:100%;aspect-ratio:1;background:var(--surface-2,#1a1a2e);border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:3rem">\uD83C\uDFB2</div>';
  }

  async function loadImg(slug, bggId, container, attempt) {
    attempt = attempt || 1;
    if (attempt > 3) { showPlaceholder(container); return; }
    try {
      const r = await fetch(BGG_API + bggId, {signal: AbortSignal.timeout(8000)});
      if (r.status === 202) { setTimeout(() => loadImg(slug, bggId, container, attempt + 1), 3000); return; }
      if (!r.ok) { showPlaceholder(container); return; }
      const url = parseImg(await r.text());
      if (url) { setCache(slug, url); showImg(container, url); }
      else showPlaceholder(container);
    } catch(e) { showPlaceholder(container); }
  }

  async function init() {
    const slug = getSlug();
    const container = document.getElementById('bgg-image-container');
    if (!slug || !container) return;

    const cached = getCache(slug);
    if (cached) { showImg(container, cached); return; }

    showPlaceholder(container);

    try {
      const r = await fetch('/bgg_ids.json');
      const ids = await r.json();
      const bggId = ids[slug];
      if (bggId) loadImg(slug, bggId, container, 1);
    } catch(e) {}
  }

  document.readyState === 'loading'
    ? document.addEventListener('DOMContentLoaded', init)
    : init();
})();
