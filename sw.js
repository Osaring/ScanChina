// ScanChina : tout est servi depuis le cache (instantané, marche sans réseau).
// - L'app (page, scanner, icônes) ne change qu'avec une nouvelle version de ce fichier :
//   l'app affiche alors « Nouvelle version disponible » et se recharge quand on appuie.
//   ⚠️ À chaque modification de l'app, augmenter VERSION ci-dessous.
// - La base produits (data.json) se met à jour en arrière-plan dès qu'il y a du réseau,
//   et l'app propose aussi de rafraîchir.
const VERSION = "2";
const CACHE = "scanchina-v" + VERSION;
const DATA = "data.json";
const SHELL = ["./", "index.html", "manifest.webmanifest", DATA,
  "lib/zxing-reader.js", "lib/zxing_reader.wasm", "icons/icon-180.png", "icons/icon-192.png", "icons/icon-512.png"];

self.addEventListener("install", e => {
  // pas de skipWaiting automatique : on attend que l'utilisateur appuie sur « Rafraîchir »
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL.map(u => new Request(u, { cache: "reload" })))));
});

self.addEventListener("message", e => {
  if (e.data === "skip-waiting") self.skipWaiting();
  if (e.data === "version" && e.source) e.source.postMessage({ type: "version", version: VERSION });
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k.startsWith("scanchina-") && k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

async function notifyAll(msg) {
  for (const c of await self.clients.matchAll({ type: "window" })) c.postMessage(msg);
}

self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return; // Open Food Facts en direct : pas de cache ici
  const isData = url.pathname.endsWith("/" + DATA);
  e.respondWith(caches.open(CACHE).then(async cache => {
    const key = url.pathname.endsWith("/") ? "./" : (isData ? DATA : e.request);
    const cached = await cache.match(key, { ignoreSearch: true });
    if (cached && !isData) return cached;
    const update = fetch(isData ? new Request(DATA, { cache: "no-cache" }) : e.request).then(async r => {
      if (!r.ok) return null;
      if (isData && cached) {
        const oldTag = cached.headers.get("etag") || cached.headers.get("last-modified");
        const newTag = r.headers.get("etag") || r.headers.get("last-modified");
        if (oldTag && newTag && oldTag !== newTag) {
          await cache.put(key, r.clone());
          notifyAll({ type: "data-updated" });
          return r;
        }
        if (oldTag === newTag) return r;
      }
      await cache.put(key, r.clone());
      return r;
    }).catch(() => null);
    if (cached) { e.waitUntil(update); return cached; }
    return (await update) || new Response("Hors ligne", { status: 503 });
  }));
});
