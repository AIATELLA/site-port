/**
 * Blog filter: handles category filter buttons on /blog.
 * Categories: all, paper, press-release, blog, abstract, article
 */
(function () {
  "use strict";

  const CATEGORY_MAP = {
    All: "all",
    Paper: "paper",
    "Press Release": "press-release",
    Blog: "blog",
    Abstract: "abstract",
    Article: "article",
  };

  function initFilters() {
    // Find all filter button groups (one per responsive variant)
    const filterGroups = document.querySelectorAll(".blog__filter-all");

    filterGroups.forEach(function (group) {
      const buttons = group.querySelectorAll("a.blog__scope");
      // Find the sibling card container (next .framer-o35a9e)
      const section = group.closest(
        '[class*="blog__latest-news"], [class*="framer-"]'
      );
      const cardContainer = section
        ? section.querySelector(".framer-o35a9e")
        : null;

      if (!cardContainer) return;

      buttons.forEach(function (btn) {
        btn.style.cursor = "pointer";
        btn.addEventListener("click", function (e) {
          e.preventDefault();

          // Get category from button text
          var textEl = btn.querySelector(".framer-text");
          var text = textEl ? textEl.textContent.trim() : "";
          var category = CATEGORY_MAP[text] || "all";

          // Update active state
          buttons.forEach(function (b) {
            var isActive = b === btn;
            // Active: red bg, white text
            if (isActive) {
              b.style.backgroundColor =
                "var(--aiatella-color-brand-red, rgb(209, 0, 0))";
              b.style.borderColor =
                "var(--aiatella-color-brand-red, rgb(209, 0, 0))";
              var label = b.querySelector(".blog__primary-btn");
              if (label) {
                label.querySelectorAll(".framer-text").forEach(function (t) {
                  t.style.setProperty(
                    "--framer-text-color",
                    "var(--aiatella-color-surface, rgb(255, 255, 255))"
                  );
                });
              }
            } else {
              b.style.backgroundColor =
                "var(--aiatella-color-surface-subtle, rgb(247, 247, 247))";
              b.style.borderColor =
                "var(--aiatella-color-border, rgb(219, 219, 219))";
              var label = b.querySelector(".blog__primary-btn");
              if (label) {
                label.querySelectorAll(".framer-text").forEach(function (t) {
                  t.style.setProperty(
                    "--framer-text-color",
                    "var(--aiatella-color-ink, rgb(0, 0, 0))"
                  );
                });
              }
            }
          });

          // Filter cards
          var cards = cardContainer.querySelectorAll("a.framer-1dmiu0e");
          cards.forEach(function (card) {
            if (category === "all") {
              card.style.display = "";
            } else {
              var cardCat = card.getAttribute("data-category") || "";
              card.style.display = cardCat === category ? "" : "none";
            }
          });
        });
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initFilters);
  } else {
    initFilters();
  }
})();
