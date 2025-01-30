import * as Turbo from "@hotwired/turbo"
import 'iframe-resizer/js/iframeResizer.contentWindow.min.js';
import { Application } from "@hotwired/stimulus"

import SearchController from "../js/controllers/assistant/search"
import BlinkController from "../js/controllers/assistant/blink"
import AnalyticsController from "../js/controllers/assistant/analytics"
import CopyController from "../js/copy_controller"

window.stimulus = Application.start()
stimulus.debug = document.body.dataset.stimulusDebug
stimulus.register("search", SearchController)
stimulus.register("blink", BlinkController)
stimulus.register("copy", CopyController)
stimulus.register("analytics", AnalyticsController)

document.addEventListener("DOMContentLoaded", () => {

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
})



Turbo.session.drive = false;
