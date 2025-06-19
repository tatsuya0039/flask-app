self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open('app-cache-v1').then(function (cache) {
      return cache.addAll([
        '/',
        '/static/style.css',
        '/static/icons/icon-192.png',
        '/static/icons/icon-512.png'
      ]);
    })
  );
});

self.addEventListener('fetch', function (event) {
  event.respondWith(
    caches.match(event.request).then(function (response) {
      return response || fetch(event.request);
    })
  );
});
