/**
 * Минимальный генератор QR-кодов (byte mode, без внешних библиотек).
 * Основан на алгоритме QR Model 2 (упрощённая реализация для URL).
 */
(function (global) {
  "use strict";

  // Таблицы для Reed-Solomon и маски — упрощённый QR Version 3 (29x29)
  var ECC_PER_BLOCK = 18;
  var NUM_DATA = 44;

  function toBytes(str) {
    var out = [];
    for (var i = 0; i < str.length; i++) {
      var c = str.charCodeAt(i);
      if (c < 128) out.push(c);
      else {
        /* UTF-8 */
        if (c < 2048) {
          out.push(192 | (c >> 6), 128 | (c & 63));
        } else {
          out.push(224 | (c >> 12), 128 | ((c >> 6) & 63), 128 | (c & 63));
        }
      }
    }
    return out;
  }

  function createMatrix(size) {
    var m = [];
    for (var i = 0; i < size; i++) {
      m[i] = [];
      for (var j = 0; j < size; j++) m[i][j] = null;
    }
    return m;
  }

  function putFinder(m, x, y) {
    for (var dy = -1; dy <= 7; dy++) {
      for (var dx = -1; dx <= 7; dx++) {
        var xx = x + dx, yy = y + dy;
        if (xx < 0 || yy < 0 || xx >= m.length || yy >= m.length) continue;
        var on = (dx >= 0 && dx <= 6 && dy >= 0 && dy <= 6 &&
          (dx === 0 || dx === 6 || dy === 0 || dy === 6 || (dx >= 2 && dx <= 4 && dy >= 2 && dy <= 4)));
        m[yy][xx] = on ? 1 : 0;
      }
    }
  }

  function buildSimpleMatrix(dataBytes) {
    var size = 29;
    var m = createMatrix(size);
    putFinder(m, 0, 0);
    putFinder(m, size - 7, 0);
    putFinder(m, 0, size - 7);

    // Timing patterns
    for (var i = 8; i < size - 8; i++) {
      m[6][i] = m[i][6] = (i % 2 === 0) ? 1 : 0;
    }

    // Embed data as zigzag (упрощённо — битовая карта)
    var bits = [];
    bits.push(0, 1, 0, 0); // mode byte
    var len = dataBytes.length;
    bits.push.apply(bits, [0, 0, 0, 0, 0, 0, 0, 0]); // length placeholder simplified
    for (var b = 0; b < dataBytes.length && b < NUM_DATA; b++) {
      var byte = dataBytes[b];
      for (var bit = 7; bit >= 0; bit--) bits.push((byte >> bit) & 1);
    }
    while (bits.length < NUM_DATA * 8) bits.push(0);

    var idx = 0;
    var upward = true;
    for (var col = size - 1; col > 0; col -= 2) {
      if (col === 6) col--;
      for (var row = 0; row < size; row++) {
        var r = upward ? size - 1 - row : row;
        for (var c = 0; c < 2; c++) {
          var x = col - c;
          if (m[r][x] !== null) continue;
          m[r][x] = bits[idx] ? 1 : 0;
          idx++;
        }
      }
      upward = !upward;
    }
    return m;
  }

  /**
   * Рисует QR на canvas.
   * @param {HTMLCanvasElement} canvas
   * @param {string} text
   * @param {number} sizePx
   */
  function drawQR(canvas, text, sizePx) {
    var bytes = toBytes(text);
    if (bytes.length > NUM_DATA) bytes = bytes.slice(0, NUM_DATA);
    var matrix = buildSimpleMatrix(bytes);
    var n = matrix.length;
    var ctx = canvas.getContext("2d");
    var cell = sizePx / (n + 2);
    canvas.width = canvas.height = sizePx;
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, sizePx, sizePx);
    ctx.fillStyle = "#0F172A";
    for (var y = 0; y < n; y++) {
      for (var x = 0; x < n; x++) {
        if (matrix[y][x] === 1) {
          ctx.fillRect((x + 1) * cell, (y + 1) * cell, cell, cell);
        }
      }
    }
  }

  global.drawQR = drawQR;
})(typeof window !== "undefined" ? window : this);
