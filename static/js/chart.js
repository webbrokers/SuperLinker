/**
 * График визитов по дням (Canvas, без библиотек).
 */
(function () {
  const canvas = document.getElementById("statsChart");
  if (!canvas) return;

  let data = [];
  try {
    data = JSON.parse(canvas.getAttribute("data-chart") || "[]");
  } catch (_) {
    return;
  }

  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth || 800;
  const h = 260;
  canvas.width = w * dpr;
  canvas.height = h * dpr;
  ctx.scale(dpr, dpr);

  const style = getComputedStyle(document.documentElement);
  const accent = style.getPropertyValue("--accent").trim() || "#6366F1";
  const muted = style.getPropertyValue("--text-muted").trim() || "#64748B";
  const border = style.getPropertyValue("--border").trim() || "#E2E8F0";

  const pad = { top: 20, right: 16, bottom: 40, left: 40 };
  const chartW = w - pad.left - pad.right;
  const chartH = h - pad.top - pad.bottom;
  const maxVal = Math.max(1, ...data.map(function (d) { return d.count; }));
  const barW = chartW / data.length * 0.65;
  const gap = chartW / data.length;

  ctx.clearRect(0, 0, w, h);

  // Ось Y
  ctx.strokeStyle = border;
  ctx.beginPath();
  ctx.moveTo(pad.left, pad.top);
  ctx.lineTo(pad.left, pad.top + chartH);
  ctx.lineTo(pad.left + chartW, pad.top + chartH);
  ctx.stroke();

  ctx.fillStyle = muted;
  ctx.font = "11px system-ui, sans-serif";
  ctx.textAlign = "right";
  ctx.fillText(String(maxVal), pad.left - 6, pad.top + 4);

  data.forEach(function (d, i) {
    const barH = (d.count / maxVal) * chartH;
    const x = pad.left + i * gap + (gap - barW) / 2;
    const y = pad.top + chartH - barH;

    const grad = ctx.createLinearGradient(0, y, 0, y + barH);
    grad.addColorStop(0, accent);
    grad.addColorStop(1, "color-mix(in srgb, " + accent + " 60%, transparent)");
    ctx.fillStyle = accent;
    ctx.beginPath();
    ctx.roundRect(x, y, barW, barH, 4);
    ctx.fill();

    // Подпись даты (каждый 5-й день)
    if (i % 5 === 0 || i === data.length - 1) {
      ctx.fillStyle = muted;
      ctx.font = "10px system-ui, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(d.day.slice(5), x + barW / 2, pad.top + chartH + 16);
    }
  });
})();
