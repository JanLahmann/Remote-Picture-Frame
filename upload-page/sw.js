/**
 * Service Worker for FamilyFrame Upload PWA.
 *
 * Handles:
 * 1. Share Target API — receives shared files from the OS share sheet
 * 2. Offline caching — cache the upload page shell for offline access
 */

const CACHE_NAME = 'familyframe-upload-v1';
const SHELL_FILES = [
  '/index.html',
  '/manifest.json',
];

// --- Install: pre-cache shell ---
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(SHELL_FILES))
      .then(() => self.skipWaiting())
  );
});

// --- Activate: clean old caches, claim clients ---
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

// --- Fetch: handle share target POST + cache-first for shell ---
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Handle Share Target API POST request
  if (event.request.method === 'POST' && url.searchParams.has('share')) {
    event.respondWith(handleShareTarget(event.request));
    return;
  }

  // Cache-first for shell, network-first for everything else
  if (SHELL_FILES.includes(url.pathname)) {
    event.respondWith(
      caches.match(event.request).then((cached) => cached || fetch(event.request))
    );
    return;
  }
});

/**
 * Handle incoming files from the OS Share sheet.
 *
 * The browser POSTs shared files as multipart/form-data.
 * We extract the files, store them temporarily, then redirect
 * the user to the upload page which picks them up.
 */
async function handleShareTarget(request) {
  const formData = await request.formData();
  const files = formData.getAll('photos');
  const caption = formData.get('caption') || formData.get('title') || '';
  const description = formData.get('description') || formData.get('text') || '';

  // Store shared files in a temporary cache for the page to pick up
  const shareCache = await caches.open('familyframe-share-temp');

  // Store metadata
  const meta = {
    caption: caption,
    description: description,
    fileCount: files.length,
    timestamp: Date.now(),
  };
  await shareCache.put(
    new Request('/_share_meta'),
    new Response(JSON.stringify(meta), { headers: { 'Content-Type': 'application/json' } })
  );

  // Store each file
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    await shareCache.put(
      new Request(`/_share_file_${i}`),
      new Response(file, {
        headers: {
          'Content-Type': file.type || 'image/jpeg',
          'X-Filename': file.name || `shared_${i}.jpg`,
        },
      })
    );
  }

  // Redirect to the upload page — it will detect and load the shared files
  return Response.redirect('/index.html?shared=true', 303);
}
