/* Cache-first service worker: after the first visit the game runs with no network at all. */
const CACHE = "imposter-v2";
const ASSETS = [
  ".",
  "index.html",
  "manifest.webmanifest",
  "icons/icon-192.png",
  "icons/icon-512.png"
];

/* The built-in GIF pack (~3 MB). Cached one by one rather than through
   addAll, so a single failed request can't fail the whole install and
   leave the app without an offline copy of everything else. */
function cacheGifs(cache) {
  return fetch("gifs/index.json")
    .then(r => r.json())
    .then(list => Promise.allSettled(list.map(g => cache.add("gifs/" + g.file))))
    .catch(() => {});
}

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(ASSETS).then(() => cacheGifs(c)))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  e.respondWith(
    caches.match(e.request, { ignoreSearch: true }).then(hit =>
      hit || fetch(e.request).then(res => {
        if (res.ok && new URL(e.request.url).origin === location.origin) {
          const copy = res.clone();
          caches.open(CACHE).then(c => c.put(e.request, copy));
        }
        return res;
      }).catch(() => caches.match("index.html"))
    )
  );
});
