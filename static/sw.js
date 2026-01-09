// MediCare Hospital - Service Worker
const CACHE_NAME = 'medicare-v1';
const STATIC_CACHE = 'medicare-static-v1';

// Assets to cache
const STATIC_ASSETS = [
    '/',
    '/static/manifest.json',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css',
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap'
];

// Install event
self.addEventListener('install', event => {
    console.log('[ServiceWorker] Installing...');
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => {
                console.log('[ServiceWorker] Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => self.skipWaiting())
    );
});

// Activate event
self.addEventListener('activate', event => {
    console.log('[ServiceWorker] Activating...');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames
                    .filter(name => name !== CACHE_NAME && name !== STATIC_CACHE)
                    .map(name => caches.delete(name))
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch event - Network first, fallback to cache
self.addEventListener('fetch', event => {
    // Skip non-GET requests
    if (event.request.method !== 'GET') return;

    // Skip cross-origin requests except for CDN
    const url = new URL(event.request.url);
    if (url.origin !== location.origin && !url.href.includes('cdn.jsdelivr.net')) {
        return;
    }

    event.respondWith(
        fetch(event.request)
            .then(response => {
                // Clone the response
                const responseClone = response.clone();

                // Cache successful responses
                if (response.status === 200) {
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(event.request, responseClone);
                    });
                }

                return response;
            })
            .catch(() => {
                // Return cached version if network fails
                return caches.match(event.request).then(response => {
                    if (response) {
                        return response;
                    }

                    // Return offline page for navigation requests
                    if (event.request.mode === 'navigate') {
                        return caches.match('/').then(cachedHome => {
                            if (cachedHome) return cachedHome;

                            // Return a simple offline message
                            return new Response(
                                '<!DOCTYPE html><html><head><title>Offline</title></head><body style="font-family:Inter,sans-serif;text-align:center;padding:50px;">' +
                                '<h1>📱 You are offline</h1>' +
                                '<p>Please check your internet connection and try again.</p>' +
                                '</body></html>',
                                { headers: { 'Content-Type': 'text/html' } }
                            );
                        });
                    }
                });
            })
    );
});

// Push notification event (for future use)
self.addEventListener('push', event => {
    const options = {
        body: event.data?.text() || 'New notification from MediCare Hospital',
        icon: '/static/icons/icon-192.png',
        badge: '/static/icons/icon-192.png',
        vibrate: [100, 50, 100],
        data: { url: '/' }
    };

    event.waitUntil(
        self.registration.showNotification('MediCare Hospital', options)
    );
});

// Notification click event
self.addEventListener('notificationclick', event => {
    event.notification.close();
    event.waitUntil(
        clients.openWindow(event.notification.data.url || '/')
    );
});
