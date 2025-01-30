if ('serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations().then(function(registrations) {
    registrations.forEach(function(registration) {
      registration.unregister().then(function(success) {
        if (success) {
          console.log('Service worker unregistered successfully.');
        } else {
          console.log('Failed to unregister service worker.');
        }
      });
    });
  }).catch(function(error) {
    console.error('Error while fetching service workers:', error);
  });
}
if ('caches' in window) {
  caches.keys().then(function(cacheNames) {
    cacheNames.forEach(function(cacheName) {
      caches.delete(cacheName).then(function(success) {
        if (success) {
          console.log('Cache deleted:', cacheName);
        }
      });
    });
  });
}
