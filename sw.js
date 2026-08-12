// KK Lite service worker — v2
// HTML: network-first (deploy baru langsung terlihat, fallback cache offline)
// Aset lain: cache-first. API (origin lain): selalu jaringan.
const C = 'kk-lite-v2';
self.addEventListener('install', e => {
  e.waitUntil(caches.open(C).then(c => c.addAll(['./manifest.json'])));
  self.skipWaiting();
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== C).map(k => caches.delete(k)))));
  self.clients.claim();
});
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const u = new URL(e.request.url);
  if (u.origin !== location.origin) return; // API origin lain: selalu jaringan
  if (u.pathname.startsWith('/api/')) return; // serverless (login, moodle-cal): selalu jaringan
  if (u.pathname.startsWith('/hebat-links') && u.pathname.endsWith('.json')) return; // data link tugas (termasuk per-user): selalu segar
  if (u.pathname.endsWith('generator-hebat.js')) return; // kode generator: selalu segar
  const isNav = e.request.mode === 'navigate';
  if (isNav) {
    e.respondWith(fetch(e.request).then(r => {
      const cp = r.clone();
      caches.open(C).then(c => c.put('./', cp));
      return r;
    }).catch(() => caches.match('./')));
    return;
  }
  e.respondWith(caches.match(e.request).then(m => m || fetch(e.request)));
});
