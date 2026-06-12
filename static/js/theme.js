/**
 * Переключение темы: системная по умолчанию + ручной toggle (localStorage).
 */
(function () {
  const STORAGE_KEY = "sl-theme";
  const toggle = document.getElementById("themeToggle");

  function applyTheme(theme) {
    if (theme === "light" || theme === "dark") {
      document.documentElement.setAttribute("data-theme", theme);
    } else {
      document.documentElement.removeAttribute("data-theme");
    }
  }

  function init() {
    const saved = localStorage.getItem(STORAGE_KEY);
    applyTheme(saved);
  }

  function cycleTheme() {
    const current = localStorage.getItem(STORAGE_KEY);
    let next;
    if (!current) next = "dark";
    else if (current === "dark") next = "light";
    else next = null; // системная
    if (next) localStorage.setItem(STORAGE_KEY, next);
    else localStorage.removeItem(STORAGE_KEY);
    applyTheme(next);
  }

  init();
  if (toggle) toggle.addEventListener("click", cycleTheme);
})();
