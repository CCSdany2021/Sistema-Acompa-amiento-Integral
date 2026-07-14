const CACHE = 'sai-v2';
const SHELL = [
  '/',
  '/students/',
  '/reports/',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  // Solo GETs de navegación — excluir APIs, admin, y rutas SAI sensibles
  if (e.request.method !== 'GET') return;
  const url = new URL(e.request.url);
  if (
    url.pathname.startsWith('/admin/') ||
    url.pathname.startsWith('/api/') ||
    url.pathname.startsWith('/reports/admin-sai/') ||
    url.pathname.startsWith('/auth/')
  ) return;

  e.respondWith(
    fetch(e.request)
      .then(res => {
        if (res.ok && res.type !== 'opaqueredirect') {
          const clone = res.clone();
          caches.open(CACHE).then(c => c.put(e.request, clone));
        }
        return res;
      })
      .catch(() =>
        caches.match(e.request).then(cached =>
          cached || new Response('Sin conexión — SAI', {
            status: 503,
            headers: { 'Content-Type': 'text/plain; charset=utf-8' },
          })
        )
      )
  );
});
