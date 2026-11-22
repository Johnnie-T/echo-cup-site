/* ============================================================
   回声杯 · 示例站 —— 交互脚本
   只做三件事：深浅色切换、作品筛选、按篇幅排序
   全部在浏览器里跑，不需要服务器
   ============================================================ */
(() => {
  "use strict";

  const root = document.documentElement;
  const STORAGE_KEY = "echo-cup-theme";

  /* ---------- 深浅色 ---------- */
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "dark" || saved === "light") root.dataset.theme = saved;
  } catch (_) {
    /* 某些浏览器（如 file:// 下）会禁用 localStorage，忽略即可 */
  }

  const toggle = document.getElementById("theme-toggle");
  if (toggle) {
    const prefersDark = () => window.matchMedia("(prefers-color-scheme: dark)").matches;
    const isDark = () =>
      root.dataset.theme === "dark" || (!root.dataset.theme && prefersDark());

    const sync = () => {
      const dark = isDark();
      toggle.textContent = dark ? "浅色" : "深色";
      toggle.setAttribute("aria-pressed", String(dark));
      toggle.setAttribute("aria-label", dark ? "切换到浅色模式" : "切换到深色模式");
    };

    sync();
    toggle.addEventListener("click", () => {
      root.dataset.theme = isDark() ? "light" : "dark";
      try {
        localStorage.setItem(STORAGE_KEY, root.dataset.theme);
      } catch (_) {
        /* 存不了就算了，不影响切换 */
      }
      sync();
    });
  }

  /* ---------- 作品筛选与排序 ---------- */
  const grid = document.getElementById("works-grid");
  if (!grid) return;

  const cards = Array.from(grid.querySelectorAll("[data-card]"));
  const chips = Array.from(document.querySelectorAll("[data-filter]"));
  const sortSelect = document.getElementById("sort");
  const note = document.getElementById("result-note");
  const empty = document.getElementById("empty-state");
  const originalOrder = cards.slice();
  const total = cards.length;

  let activeFilter = "all";

  const matches = (card, filter) => {
    switch (filter) {
      case "both":
        return card.dataset.both === "1";
      case "human":
        return card.dataset.human === "1" && card.dataset.ai !== "1";
      case "ai":
        return card.dataset.ai === "1" && card.dataset.human !== "1";
      case "rod":
        return card.dataset.rod === "1";
      default:
        return true;
    }
  };

  const applyFilter = () => {
    let shown = 0;
    for (const card of cards) {
      const ok = matches(card, activeFilter);
      card.hidden = !ok;
      if (ok) shown += 1;
    }
    if (empty) empty.hidden = shown !== 0;
    if (note) {
      note.textContent =
        shown === total ? `共 ${total} 部作品` : `筛出 ${shown} 部，共 ${total} 部`;
    }
  };

  const applySort = () => {
    const mode = sortSelect ? sortSelect.value : "default";
    const ordered = cards.slice();
    if (mode === "words-asc") {
      ordered.sort((a, b) => Number(a.dataset.words) - Number(b.dataset.words));
    } else if (mode === "words-desc") {
      ordered.sort((a, b) => Number(b.dataset.words) - Number(a.dataset.words));
    } else {
      ordered.sort(
        (a, b) => originalOrder.indexOf(a) - originalOrder.indexOf(b)
      );
    }
    for (const card of ordered) grid.appendChild(card);
  };

  for (const chip of chips) {
    chip.addEventListener("click", () => {
      activeFilter = chip.dataset.filter || "all";
      for (const other of chips) {
        other.setAttribute("aria-pressed", String(other === chip));
      }
      applyFilter();
    });
  }

  if (sortSelect) {
    sortSelect.addEventListener("change", () => {
      applySort();
      applyFilter();
    });
  }

  applyFilter();
})();
