/**
 * Mobile nav hamburger, replacing Framer hydration.
 *
 * The static export shipped `.nav__hamburger` as an inert div: Framer's own
 * interactive-component runtime (the thing that would have wired it up) was
 * never captured by the export, so nothing listened for a click. This file
 * is new behaviour, not a repair of something that used to work.
 *
 * Markup contract (see partials/nav.html, mobile breakpoint):
 *   - `.nav__hamburger` is the toggle: `role="button" tabindex="0"`,
 *     `aria-expanded`, `aria-controls` pointing at the panel's id.
 *   - The panel is the next `.nav__mobile-menu` inside the same `.nav`,
 *     starting with the `hidden` attribute so it degrades safely with no JS.
 *
 * Runs on every page; pages without a hamburger (there are none today, but
 * nothing here assumes one exists) simply do nothing.
 */
(function () {
  "use strict";

  var OPEN_CLASS = "nav__mobile-menu--open";
  var TOP_TRANSFORM = "translateY(5px) rotate(45deg)";
  var BOT_TRANSFORM = "translateY(-5px) rotate(-45deg)";

  function wire(toggle) {
    var nav = toggle.closest(".nav");
    var panel = nav && nav.querySelector(".nav__mobile-menu");
    if (!panel) return;

    var top = toggle.querySelector(".nav__hamburger-top");
    var bot = toggle.querySelector(".nav__hamburger-bot");

    function isOpen() {
      return toggle.getAttribute("aria-expanded") === "true";
    }

    function setOpen(open) {
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      panel.hidden = !open;
      panel.classList.toggle(OPEN_CLASS, open);
      if (top) top.style.transform = open ? TOP_TRANSFORM : "";
      if (bot) bot.style.transform = open ? BOT_TRANSFORM : "";
    }

    function close(returnFocus) {
      if (!isOpen()) return;
      setOpen(false);
      if (returnFocus) toggle.focus();
    }

    toggle.addEventListener("click", function () {
      setOpen(!isOpen());
    });

    toggle.addEventListener("keydown", function (event) {
      if (event.key === "Enter" || event.key === " " || event.key === "Spacebar") {
        event.preventDefault();
        setOpen(!isOpen());
      } else if (event.key === "Escape") {
        close(true);
      }
    });

    panel.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        event.preventDefault();
        close(true);
      }
    });

    document.addEventListener("click", function (event) {
      if (!isOpen()) return;
      if (nav.contains(event.target)) return;
      close(false);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var toggles = document.querySelectorAll(".nav__hamburger");
    for (var i = 0; i < toggles.length; i++) wire(toggles[i]);
  });
})();
