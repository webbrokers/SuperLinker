/**
 * Админка: тестовые данные.
 */
(function () {
  const genBtn = document.getElementById("genTestBtn");
  const clearBtn = document.getElementById("clearTestBtn");
  const toolMsg = document.getElementById("toolMsg");

  function showMsg(text, isError) {
    if (!toolMsg) return;
    toolMsg.textContent = text;
    toolMsg.style.color = isError ? "var(--error)" : "var(--success)";
    toolMsg.hidden = false;
  }

  if (genBtn) {
    genBtn.addEventListener("click", async function () {
      genBtn.disabled = true;
      try {
        const res = await fetch("/api/admin/generate-test-data", { method: "POST" });
        const data = await res.json();
        if (res.ok) {
          showMsg("Создано тестовых кликов: " + data.clicks_created + ". Обновите страницу.");
        } else {
          showMsg(data.error || "Ошибка", true);
        }
      } catch (_) {
        showMsg("Сеть недоступна", true);
      }
      genBtn.disabled = false;
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener("click", async function () {
      if (!confirm("Удалить все тестовые данные (is_test)? Реальная статистика сохранится.")) return;
      clearBtn.disabled = true;
      try {
        const res = await fetch("/api/admin/clear-test-data", { method: "POST" });
        const data = await res.json();
        if (res.ok) {
          var msg = "Удалено записей: " + data.deleted;
          if (data.backup) msg += ". Бэкап: " + data.backup;
          showMsg(msg);
        } else {
          showMsg(data.error || "Ошибка", true);
        }
      } catch (_) {
        showMsg("Сеть недоступна", true);
      }
      clearBtn.disabled = false;
    });
  }
})();
