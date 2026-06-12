/**
 * Страница сокращения: форма, API, копирование, QR.
 */
(function () {
  const form = document.getElementById("shortenForm");
  const paramsToggle = document.getElementById("paramsToggle");
  const paramsPanel = document.getElementById("paramsPanel");
  const resultPanel = document.getElementById("resultPanel");
  const formError = document.getElementById("formError");
  const shortUrlLink = document.getElementById("shortUrlLink");
  const copyBtn = document.getElementById("copyBtn");
  const qrBtn = document.getElementById("qrBtn");
  const qrWrap = document.getElementById("qrWrap");
  const qrCanvas = document.getElementById("qrCanvas");
  const toast = document.getElementById("toast");
  const rateRemaining = document.getElementById("rateRemaining");

  let lastShortUrl = "";

  if (paramsToggle && paramsPanel) {
    paramsToggle.addEventListener("click", function () {
      const open = paramsPanel.hidden;
      paramsPanel.hidden = !open;
      paramsToggle.setAttribute("aria-expanded", String(open));
      paramsToggle.textContent = open ? "− Скрыть параметры" : "+ Добавить параметры";
    });
  }

  if (form) {
    form.addEventListener("submit", async function (e) {
      e.preventDefault();
      formError.hidden = true;
      const fd = new FormData(form);
      const body = Object.fromEntries(fd.entries());

      try {
        const res = await fetch("/api/shorten", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        const data = await res.json();
        if (!res.ok) {
          formError.textContent = data.error || "Ошибка";
          formError.hidden = false;
          return;
        }
        lastShortUrl = data.short_url;
        shortUrlLink.href = lastShortUrl;
        shortUrlLink.textContent = lastShortUrl;
        resultPanel.hidden = false;
        qrWrap.hidden = true;
        if (rateRemaining && data.remaining_today !== undefined) {
          rateRemaining.textContent = String(data.remaining_today);
        }
      } catch (err) {
        formError.textContent = "Сеть недоступна";
        formError.hidden = false;
      }
    });
  }

  if (copyBtn) {
    copyBtn.addEventListener("click", async function () {
      if (!lastShortUrl) return;
      try {
        await navigator.clipboard.writeText(lastShortUrl);
        toast.hidden = false;
        setTimeout(function () { toast.hidden = true; }, 2000);
      } catch (_) {
        /* fallback */
        prompt("Скопируйте:", lastShortUrl);
      }
    });
  }

  if (qrBtn && qrCanvas && typeof drawQR === "function") {
    qrBtn.addEventListener("click", function () {
      if (!lastShortUrl) return;
      qrWrap.hidden = false;
      drawQR(qrCanvas, lastShortUrl, 200);
    });
  }
})();
