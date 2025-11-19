const form = document.getElementById('form');
const submitBtn = document.getElementById('submit');
const statusEl = document.getElementById('status');
const resultEl = document.getElementById('result');
const imgEl = document.getElementById('img');
const downloadEl = document.getElementById('download');
const logEl = document.getElementById('log');

function readImageFile(file) {
  return new Promise((resolve, reject) => {
    const fr = new FileReader();
    fr.onerror = reject;
    fr.onload = () => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = reject;
      img.src = fr.result;
    };
    fr.readAsDataURL(file);
  });
}

function createTileCanvas(img, tile) {
  const c = document.createElement('canvas');
  c.width = tile;
  c.height = tile;
  const ctx = c.getContext('2d');
  ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(img, 0, 0, tile, tile);
  return c;
}

function generateRepeat(img, tile, outW, outH, scale) {
  const finalW = outW * scale;
  const finalH = outH * scale;
  const c = document.createElement('canvas');
  c.width = finalW;
  c.height = finalH;
  const ctx = c.getContext('2d');
  const tileCanvas = createTileCanvas(img, tile);
  const pattern = ctx.createPattern(tileCanvas, 'repeat');
  ctx.fillStyle = pattern;
  ctx.fillRect(0, 0, finalW, finalH);
  return c;
}

function generateMosaic(img, tile, outW, outH, scale, tint) {
  const finalW = outW * scale;
  const finalH = outH * scale;
  const cols = Math.ceil(finalW / tile);
  const rows = Math.ceil(finalH / tile);

  const c = document.createElement('canvas');
  c.width = finalW;
  c.height = finalH;
  const ctx = c.getContext('2d');
  ctx.imageSmoothingQuality = 'high';

  const tileCanvas = createTileCanvas(img, tile);

  const srcC = document.createElement('canvas');
  srcC.width = cols;
  srcC.height = rows;
  const srcCtx = srcC.getContext('2d');
  srcCtx.drawImage(img, 0, 0, cols, rows);
  const srcData = srcCtx.getImageData(0, 0, cols, rows).data;

  for (let r = 0; r < rows; r++) {
    for (let cIdx = 0; cIdx < cols; cIdx++) {
      const x = cIdx * tile;
      const y = r * tile;
      ctx.drawImage(tileCanvas, x, y, tile, tile);
      const i = (r * cols + cIdx) * 4;
      const rCol = srcData[i];
      const gCol = srcData[i + 1];
      const bCol = srcData[i + 2];
      if (tint > 0) {
        ctx.globalAlpha = tint;
        ctx.fillStyle = `rgb(${rCol},${gCol},${bCol})`;
        ctx.fillRect(x, y, tile, tile);
        ctx.globalAlpha = 1;
      }
    }
  }
  return c;
}

function canvasToBlobUrl(canvas, format, quality) {
  return new Promise((resolve) => {
    const type = format === 'jpg' ? 'image/jpeg' : 'image/png';
    const q = format === 'jpg' ? Math.max(0.1, Math.min(1, quality / 100)) : undefined;
    canvas.toBlob((blob) => {
      const url = URL.createObjectURL(blob);
      resolve(url);
    }, type, q);
  });
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  statusEl.textContent = '';
  resultEl.style.display = 'none';

  const fd = new FormData(form);
  const file = fd.get('image');
  if (!file || !file.size) {
    statusEl.textContent = 'Please choose an image';
    return;
  }

  const tile = parseInt(fd.get('tile'));
  const outW = parseInt(fd.get('out_w'));
  const outH = parseInt(fd.get('out_h'));
  const scale = parseInt(fd.get('scale'));
  const format = String(fd.get('format'));
  const jpgQuality = parseInt(fd.get('jpg_quality'));
  const preview = String(fd.get('preview')) === 'true';
  const mode = String(fd.get('mode'));
  const tint = parseFloat(fd.get('tint'));

  const finalW = outW * scale;
  const finalH = outH * scale;
  const maxPixels = 120_000_000;
  if (finalW * finalH > maxPixels) {
    statusEl.textContent = 'Output too large for browser memory. Reduce scale or dimensions.';
    return;
  }

  submitBtn.disabled = true;
  statusEl.textContent = 'Generating...';

  try {
    const img = await readImageFile(file);

    let canvas;
    if (mode === 'mosaic') {
      canvas = generateMosaic(img, tile, outW, outH, scale, tint);
    } else {
      canvas = generateRepeat(img, tile, outW, outH, scale);
    }

    let previewUrl;
    if (preview) {
      const pC = document.createElement('canvas');
      const pScale = 6;
      pC.width = Math.max(1, Math.floor(canvas.width / pScale));
      pC.height = Math.max(1, Math.floor(canvas.height / pScale));
      const pCtx = pC.getContext('2d');
      pCtx.imageSmoothingQuality = 'high';
      pCtx.drawImage(canvas, 0, 0, pC.width, pC.height);
      previewUrl = await canvasToBlobUrl(pC, format, jpgQuality);
    }

    const url = await canvasToBlobUrl(canvas, format, jpgQuality);
    imgEl.src = preview ? previewUrl : url;
    downloadEl.href = url;
    downloadEl.download = `secretwallpaper.${format}`;
    resultEl.style.display = 'block';
    statusEl.textContent = 'Done';
    logEl.textContent = `Final ${canvas.width}x${canvas.height}, tile ${tile}px, mode ${mode}`;
  } catch (err) {
    statusEl.textContent = `Error: ${err.message || err}`;
  } finally {
    submitBtn.disabled = false;
  }
});
