const CACHE_NAME = "nmu-smart-bus-v1";
const OFFLINE_URLS = [
	"/",
	"/wallet",
	"/capacity",
	"/admin",
	"/manifest.webmanifest",
];

self.addEventListener("install", (event) => {
	event.waitUntil(
		caches.open(CACHE_NAME).then((cache) => {
			return cache.addAll(OFFLINE_URLS);
		}),
	);
	self.skipWaiting();
});

self.addEventListener("activate", (event) => {
	event.waitUntil(
		caches.keys().then((cacheNames) =>
			Promise.all(
				cacheNames.map((name) => {
					if (name !== CACHE_NAME) {
						return caches.delete(name);
					}
					return Promise.resolve();
				}),
			),
		),
	);
	self.clients.claim();
});

self.addEventListener("fetch", (event) => {
	const { request } = event;

	if (request.method !== "GET") {
		return;
	}

	event.respondWith(
		caches.match(request).then((cachedResponse) => {
			if (cachedResponse) {
				return cachedResponse;
			}

			return fetch(request)
				.then((networkResponse) => {
					if (
						!networkResponse ||
						networkResponse.status !== 200 ||
						networkResponse.type !== "basic"
					) {
						return networkResponse;
					}

					const responseClone = networkResponse.clone();
					caches
						.open(CACHE_NAME)
						.then((cache) => cache.put(request, responseClone));
					return networkResponse;
				})
				.catch(() => caches.match("/"));
		}),
	);
});
