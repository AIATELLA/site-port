/**
 * Scroll-linked redline animations, replacing Framer hydration.
 *
 * The redline elements ship with an inline `translateX(<n>px)` that parks them
 * off-screen to the right (1050px desktop / 800px tablet / 360px phone). Framer
 * drove them with an overdamped spring fired by a hidden trigger section; here
 * the offset is linked directly to scroll position instead, so it slides left as
 * you scroll down, slides back right as you scroll up, and is smoothed with a
 * per-frame ease so wheel steps don't read as jumps.
 */
(function() {
  "use strict";

  /* Multiplier on the inline offset, i.e. how much further right than Framer's
     own resting value the line is parked before it starts sliding in. */
  var START_SCALE = 1.5;
  /* Fraction of the element's viewport traversal spent sliding home. At 0.9 the
     line only lands flush left once it is nearly off the top of the screen. */
  var TRAVEL = 0.9;
  /* Per-frame catch-up toward the scroll-derived offset, normalised to 60fps. */
  var SMOOTHING = 0.18;
  var SETTLED = 0.0004;

  function clamp01(v) {
    return v < 0 ? 0 : v > 1 ? 1 : v;
  }

  function viewportHeight() {
    return window.innerHeight || document.documentElement.clientHeight;
  }

  function initScrollAnimations() {
    var targets = [];

    document.querySelectorAll("[style*='translateX']").forEach(function(el) {
      var match = (el.getAttribute("style") || "").match(/translateX\((\d+(?:\.\d+)?)px\)/);
      if (!match) return;
      var initialX = parseFloat(match[1]) * START_SCALE;
      if (!(initialX > 0)) return;
      /* offset: 1 = parked off to the right, 0 = home. */
      targets.push({ el: el, initialX: initialX, offset: 1, goal: 1 });
    });

    if (targets.length === 0) return;

    var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

    function render(t) {
      var shift = (t.offset * t.initialX).toFixed(2) + "px";
      t.el.style.transform = "perspective(1200px) translateX(" + shift + ")";
      /* Lets a mask on the element cancel the translation, so any fade painted
         via --redline-shift stays pinned to the container as the line moves. */
      t.el.style.setProperty("--redline-shift", shift);
    }

    function goalFor(el) {
      var rect = el.getBoundingClientRect();
      var vh = viewportHeight();
      /* Parked when the element sits at the bottom edge, home once it has risen
         TRAVEL * vh — i.e. just shy of leaving through the top of the screen. */
      return 1 - clamp01((vh - rect.top) / (vh * TRAVEL));
    }

    var running = false;
    var lastTime = 0;

    function frame(now) {
      var dt = lastTime ? Math.min(now - lastTime, 100) : 16.667;
      lastTime = now;

      var instant = reduceMotion.matches;
      var ease = instant ? 1 : 1 - Math.pow(1 - SMOOTHING, dt / 16.667);
      var busy = false;

      targets.forEach(function(t) {
        /* Hidden breakpoint variants have no box to measure — leave them parked. */
        if (t.el.offsetParent === null) return;

        t.goal = goalFor(t.el);
        var delta = t.goal - t.offset;

        if (Math.abs(delta) < SETTLED) {
          if (t.offset !== t.goal) {
            t.offset = t.goal;
            render(t);
          }
          return;
        }

        t.offset += delta * ease;
        render(t);
        busy = true;
      });

      if (busy) {
        requestAnimationFrame(frame);
      } else {
        running = false;
        lastTime = 0;
      }
    }

    function schedule() {
      if (running) return;
      running = true;
      lastTime = 0;
      requestAnimationFrame(frame);
    }

    /* Snap to the current scroll position on load: a mid-page reload should not
       replay the slide-in, and a fresh load at the top leaves them parked. */
    targets.forEach(function(t) {
      if (t.el.offsetParent === null) return;
      t.offset = t.goal = goalFor(t.el);
      render(t);
    });

    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    if (reduceMotion.addEventListener) {
      reduceMotion.addEventListener("change", schedule);
    }
  }

  function initScrollOverlays() {
    /* Framer's invisible scroll-trigger sections. Unused now, and they sit on top
       of real content with a z-index, so keep them out of the way entirely. */
    document.querySelectorAll(".scroll__redline, .scroll__aorta").forEach(function(overlay) {
      overlay.style.display = "none";
    });
  }

  function init() {
    initScrollOverlays();
    initScrollAnimations();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
