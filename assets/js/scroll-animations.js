/**
 * Vanilla scroll-linked animations replacing Framer hydration.
 * Uses IntersectionObserver to animate redline elements on scroll.
 */
(function() {
  "use strict";

  var DURATION = 1200;
  var EASING = "cubic-bezier(0.22, 1, 0.36, 1)";

  function initScrollAnimations() {
    var allElements = document.querySelectorAll("[style*='translateX']");
    var targets = [];

    allElements.forEach(function(el) {
      var style = el.getAttribute("style") || "";
      var match = style.match(/translateX\((\d+)px\)/);
      if (match && parseInt(match[1]) > 0) {
        targets.push({
          el: el,
          initialX: parseInt(match[1])
        });
      }
    });

    if (targets.length === 0) return;

    targets.forEach(function(t) {
      t.el.style.transition = "transform " + DURATION + "ms " + EASING;
    });

    var observer = new IntersectionObserver(
      function(entries) {
        entries.forEach(function(entry) {
          if (!entry.isIntersecting) return;
          var el = entry.target;
          targets.forEach(function(t) {
            if (t.el === el || el.contains(t.el)) {
              t.el.style.transform = "perspective(1200px) translateX(0px)";
            }
          });
          observer.unobserve(el);
        });
      },
      { threshold: 0.15, rootMargin: "0px 0px -50px 0px" }
    );

    var observed = new Set();
    targets.forEach(function(t) {
      var trigger = t.el.closest("section") || t.el.parentElement;
      if (trigger && !observed.has(trigger)) {
        observed.add(trigger);
        observer.observe(trigger);
      }
      if (!observed.has(t.el)) {
        observed.add(t.el);
        observer.observe(t.el);
      }
    });
  }

  function initScrollOverlays() {
    var overlays = document.querySelectorAll(".scroll__redline, .scroll__aorta");
    overlays.forEach(function(overlay) {
      overlay.style.display = "none";
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function() {
      initScrollAnimations();
      initScrollOverlays();
    });
  } else {
    initScrollAnimations();
    initScrollOverlays();
  }
})();
