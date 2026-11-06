// ScanChina : tout est servi depuis le cache (instantané, marche sans réseau),
// puis mis à jour en arrière-plan quand il y a du réseau.
const CACHE = "scanchina-v1";
const SHELL = ["./", "index.html", "manifest.webmanifest", "data.json",
  "lib/zxing-reader.js", "lib/zxing_reader.wasm", "icons/icon-180.png", "icons/icon-192.png", "icons/icon-512.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return; // Open Food Facts en direct : pas de cache ici
  e.respondWith(caches.open(CACHE).then(async cache => {
    const key = url.pathname.endsWith("/") ? "./" : e.request;
    const cached = await cache.match(key, { ignoreSearch: true });
    const update = fetch(e.request).then(r => {
      if (r.ok) cache.put(key, r.clone());
      return r;
    }).catch(() => null);
    if (cached) { e.waitUntil(update); return cached; }
    return (await update) || new Response("Hors ligne", { status: 503 });
  }));
});
