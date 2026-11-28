/* Interfaz de Calibre Geovida: marcar puntos sobre una imagen, mostrar el certificado y la franja de referencia.
   Todo ocurre en el navegador: la imagen se dibuja en un lienzo, nunca se envía ni se guarda. Solo investigación y educación. */
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const fmt = (x, d = 1) => (x === null || x === undefined || !Number.isFinite(x) ? '—' : x.toFixed(d));
  const num = (id, fallback) => { const v = parseFloat($(id).value); return Number.isFinite(v) ? v : fallback; };
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const pct = (p) => (p >= 0.995 && p < 1 ? '> 99' : (p > 0 && p < 0.005 ? '< 1' : fmt(100 * p, 0)));
  const wd = (days) => { const [w, d] = Core.weeksDays(days); return `${w}+${d}`; };

  const MAX_SIDE = 3000;
  const S = {
    img: null,                 // { canvas, w, h, gray }
    example: false,
    note: '',
    view: { k: 1, ox: 0, oy: 0 },
    cal: [null, null],         // puntos de la escala, en píxeles de la imagen
    crl: [null, null],         // extremos de la longitud
    sel: null,                 // { set, i }: la marca seleccionada
    drag: null,
    hover: null,
    last: null,                // último cálculo
  };

  const stage = $('stage'), ctx = stage.getContext('2d');
  const loupe = $('loupe'), lctx = loupe.getContext('2d');
  let dpr = 1, cw = 0, ch = 0;

  // --- imagen de ejemplo, dibujada aquí (no es ninguna ecografía real) -----------------------------------------
  function makeExample() {
    const W = 720, H = 540, PXMM = 7.5;
    const rng = Core.mulberry32(20261222);
    const noiseW = W >> 1, noiseH = H >> 1;
    const nc = document.createElement('canvas'); nc.width = noiseW; nc.height = noiseH;
    const nctx = nc.getContext('2d'), nimg = nctx.createImageData(noiseW, noiseH);
    for (let i = 0; i < noiseW * noiseH; i++) {
      const u = Math.max(rng(), 1e-9), r = Math.sqrt(-2 * Math.log(u)) * 0.55;       // Rayleigh: moteado
      const v = Math.min(255, r * 128);
      nimg.data[4 * i] = nimg.data[4 * i + 1] = nimg.data[4 * i + 2] = v; nimg.data[4 * i + 3] = 255;
    }
    nctx.putImageData(nimg, 0, 0);
    const up = document.createElement('canvas'); up.width = W; up.height = H;
    const uctx = up.getContext('2d'); uctx.imageSmoothingEnabled = true; uctx.drawImage(nc, 0, 0, W, H);
    const speckle = uctx.getImageData(0, 0, W, H).data;

    const ax = 360, ay = -60, R = 700, half = 48 * Math.PI / 180;
    const th = -14 * Math.PI / 180, cth = Math.cos(th), sth = Math.sin(th);
    const P0 = [250, 330], lenPx = 42 * PXMM;
    const out = document.createElement('canvas'); out.width = W; out.height = H;
    const octx = out.getContext('2d'), oimg = octx.createImageData(W, H);
    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        const dx = x - ax, dy = y - ay, rad = Math.hypot(dx, dy), ang = Math.atan2(dx, dy);
        let v = 0;
        if (rad < R && Math.abs(ang) < half) {
          const depth = rad / R;
          let t = 0.30 * Math.exp(-1.4 * depth) + 0.05;                                  // tejido con atenuación
          // saco gestacional: elipse oscura con borde brillante
          const sx = x - 400, sy = y - 295;
          const u = (sx * cth + sy * sth) / 250, w = (-sx * sth + sy * cth) / 120;
          const e = u * u + w * w;
          if (e < 1) t = 0.035; else if (e < 1.12) t = 0.62;
          // embrión: cápsula brillante a lo largo del eje de medida
          const qx = x - P0[0], qy = y - P0[1];
          const along = qx * cth + qy * sth, across = -qx * sth + qy * cth;
          const cl = Math.max(0, Math.min(lenPx, along));
          const dd = Math.hypot(along - cl, across);
          if (dd < 24) t = Math.max(t, 0.70 - 0.012 * dd + 0.08 * Math.sin(along / 11));
          v = t * (0.45 + 0.75 * speckle[4 * (y * W + x)] / 255 * 2);
        }
        const g = Math.max(0, Math.min(255, Math.pow(Math.min(v, 1), 0.8) * 255));
        const i = 4 * (y * W + x);
        oimg.data[i] = oimg.data[i + 1] = oimg.data[i + 2] = g; oimg.data[i + 3] = 255;
      }
    }
    octx.putImageData(oimg, 0, 0);
    // regla en el borde derecho: marcas cada 5 mm, más largas cada 10 mm
    octx.strokeStyle = 'rgba(235,235,235,0.9)'; octx.lineWidth = 1.5;
    const rx = W - 40;
    octx.beginPath(); octx.moveTo(rx, 50); octx.lineTo(rx, 420); octx.stroke();
    for (let k = 0; k <= 9; k++) {
      const y = 60 + k * 5 * PXMM, long = k % 2 === 0;
      octx.beginPath(); octx.moveTo(rx, y); octx.lineTo(rx - (long ? 14 : 8), y); octx.stroke();
    }
    octx.font = '600 15px sans-serif'; octx.fillStyle = 'rgba(242,184,75,0.85)';
    octx.fillText('EJEMPLO SINTÉTICO', 16, 28);
    return { canvas: out, w: W, h: H, gray: null,
             cal: [[rx, 60], [rx, 360]], calMm: 40,
             crl: [[P0[0] + 2.1, P0[1] + 1.2], [P0[0] + lenPx * cth + 1.9, P0[1] + lenPx * sth + 1.8]] };
  }

  // --- carga de imagen -------------------------------------------------------------------------------------------
  function installImage(canvas, example, note) {
    S.img = { canvas, w: canvas.width, h: canvas.height, gray: null };
    S.example = example; S.note = note || '';
    S.cal = [null, null]; S.crl = [null, null]; S.sel = null;
    fitView();
  }
  function useExample() {
    const ex = makeExample();
    installImage(ex.canvas, true, '');
    S.cal = ex.cal.map((p) => p.slice()); S.crl = ex.crl.map((p) => p.slice());
    $('cal-mm').value = ex.calMm;
    setMode('crl');
    update();
  }
  async function loadFile(file) {
    if (!file) return;
    try {
      let src, w, h;
      if (window.createImageBitmap) { src = await createImageBitmap(file); w = src.width; h = src.height; }
      else {
        src = await new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = rej; im.src = URL.createObjectURL(file); });
        w = src.naturalWidth; h = src.naturalHeight;
      }
      const k = Math.min(1, MAX_SIDE / Math.max(w, h));
      const c = document.createElement('canvas'); c.width = Math.round(w * k); c.height = Math.round(h * k);
      const cx = c.getContext('2d', { willReadFrequently: true }); cx.drawImage(src, 0, 0, c.width, c.height);
      if (src.close) src.close();
      installImage(c, false, k < 1 ? `La imagen se redujo de ${w}×${h} a ${c.width}×${c.height} px para trabajar.` : '');
      $('cal-mm').value = 10;
      setMode('scale');
      update();
    } catch (e) {
      S.note = 'No se pudo leer ese archivo como imagen. Prueba con PNG o JPEG.';
      update();
    }
  }
  function grayOf(img) {                                 // luminancia en [0, 255], solo para la huella; se calcula una vez
    if (img.gray) return img.gray;
    const d = img.canvas.getContext('2d', { willReadFrequently: true }).getImageData(0, 0, img.w, img.h).data;
    const g = new Float64Array(img.w * img.h);
    for (let i = 0; i < g.length; i++) g[i] = 0.2126 * d[4 * i] + 0.7152 * d[4 * i + 1] + 0.0722 * d[4 * i + 2];
    img.gray = g; return g;
  }

  // --- vista (zoom y desplazamiento) -----------------------------------------------------------------------------
  function resizeStage() {
    const r = stage.getBoundingClientRect();
    dpr = Math.max(1, window.devicePixelRatio || 1);
    cw = Math.max(1, Math.round(r.width)); ch = Math.max(1, Math.round(r.height));
    stage.width = Math.round(cw * dpr); stage.height = Math.round(ch * dpr);
  }
  function fitView() {
    if (!S.img) return;
    const k = Math.min(cw / S.img.w, ch / S.img.h) * 0.97;
    S.view = { k, ox: (cw - S.img.w * k) / 2, oy: (ch - S.img.h * k) / 2 };
  }
  const toScreen = (p) => [p[0] * S.view.k + S.view.ox, p[1] * S.view.k + S.view.oy];
  const toImage = (sx, sy) => [(sx - S.view.ox) / S.view.k, (sy - S.view.oy) / S.view.k];
  function zoomAt(f, sx, sy) {
    if (!S.img) return;
    const k0 = S.view.k, k1 = Math.min(Math.max(k0 * f, 0.1), 48);
    const p = toImage(sx, sy);
    S.view.k = k1; S.view.ox = sx - p[0] * k1; S.view.oy = sy - p[1] * k1;
    draw();
  }

  // --- dibujo ----------------------------------------------------------------------------------------------------
  function handle(p, color, label, selected) {
    const [x, y] = toScreen(p);
    ctx.save();
    ctx.lineWidth = 1.5; ctx.strokeStyle = color; ctx.fillStyle = color;
    ctx.beginPath(); ctx.arc(x, y, 8, 0, 2 * Math.PI); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(x - 14, y); ctx.lineTo(x - 4, y); ctx.moveTo(x + 4, y); ctx.lineTo(x + 14, y);
    ctx.moveTo(x, y - 14); ctx.lineTo(x, y - 4); ctx.moveTo(x, y + 4); ctx.lineTo(x, y + 14); ctx.stroke();
    ctx.beginPath(); ctx.arc(x, y, 1.2, 0, 2 * Math.PI); ctx.fill();
    if (selected) { ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 1; ctx.beginPath(); ctx.arc(x, y, 11.5, 0, 2 * Math.PI); ctx.stroke(); }
    ctx.font = '600 11px "IBM Plex Sans", system-ui, sans-serif';
    const lw = ctx.measureText(label).width, lx = x + 13 + lw > cw - 4 ? x - 13 - lw : x + 13;
    ctx.lineWidth = 3; ctx.strokeStyle = 'rgba(0,0,0,0.75)'; ctx.strokeText(label, lx, y - 11);
    ctx.fillStyle = color; ctx.fillText(label, lx, y - 11);
    ctx.restore();
  }
  function segment(a, b, color, text) {
    const A = toScreen(a), B = toScreen(b);
    ctx.save();
    ctx.strokeStyle = color; ctx.lineWidth = 1.25; ctx.setLineDash([6, 4]);
    ctx.beginPath(); ctx.moveTo(A[0], A[1]); ctx.lineTo(B[0], B[1]); ctx.stroke(); ctx.setLineDash([]);
    if (text) {
      const mx = (A[0] + B[0]) / 2, my = (A[1] + B[1]) / 2;
      ctx.font = '600 12px "IBM Plex Mono", ui-monospace, monospace';
      const tw = ctx.measureText(text).width, tx = mx + 8 + tw > cw - 4 ? mx - 8 - tw : mx + 8;
      ctx.lineWidth = 4; ctx.strokeStyle = 'rgba(0,0,0,0.8)'; ctx.strokeText(text, tx, my - 8);
      ctx.fillStyle = color; ctx.fillText(text, tx, my - 8);
    }
    ctx.restore();
  }
  function draw() {
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = '#0a0f12'; ctx.fillRect(0, 0, cw, ch);
    if (!S.img) {
      ctx.fillStyle = '#9fb2b8'; ctx.font = '500 15px "IBM Plex Sans", system-ui, sans-serif'; ctx.textAlign = 'center';
      ctx.fillText('Abre una imagen o carga el ejemplo sintético', cw / 2, ch / 2); ctx.textAlign = 'left';
      return;
    }
    ctx.imageSmoothingEnabled = S.view.k < 3;
    ctx.drawImage(S.img.canvas, S.view.ox, S.view.oy, S.img.w * S.view.k, S.img.h * S.view.k);
    const r = S.last && S.last.meas;
    if (S.cal[0] && S.cal[1]) segment(S.cal[0], S.cal[1], '#f2b84b', r && r.refPx ? `${fmt(num('cal-mm', 0), 1)} mm` : '');
    if (S.crl[0] && S.crl[1]) segment(S.crl[0], S.crl[1], '#4fd1de', r && r.lengthMm ? `${fmt(r.lengthMm, 1)} mm` : '');
    const names = { cal: ['Regla 1', 'Regla 2'], crl: ['Cráneo', 'Rabadilla'] };
    for (const set of ['cal', 'crl']) {
      for (let i = 0; i < 2; i++) {
        const p = S[set][i];
        if (p) handle(p, set === 'cal' ? '#f2b84b' : '#4fd1de', names[set][i], S.sel && S.sel.set === set && S.sel.i === i);
      }
    }
  }
  function drawLoupe(sx, sy) {
    if (!S.img) return;
    const p = toImage(sx, sy), size = 120, mag = 8, half = size / mag / 2;
    lctx.imageSmoothingEnabled = false;
    lctx.fillStyle = '#000'; lctx.fillRect(0, 0, size, size);
    lctx.drawImage(S.img.canvas, p[0] - half, p[1] - half, half * 2, half * 2, 0, 0, size, size);
    lctx.strokeStyle = 'rgba(79,209,222,0.95)'; lctx.lineWidth = 1;
    lctx.beginPath(); lctx.moveTo(size / 2, 0); lctx.lineTo(size / 2, size / 2 - 6); lctx.moveTo(size / 2, size / 2 + 6); lctx.lineTo(size / 2, size);
    lctx.moveTo(0, size / 2); lctx.lineTo(size / 2 - 6, size / 2); lctx.moveTo(size / 2 + 6, size / 2); lctx.lineTo(size, size / 2); lctx.stroke();
    loupe.style.left = sx < 150 && sy < 150 ? 'auto' : '10px';
    loupe.style.right = sx < 150 && sy < 150 ? '10px' : 'auto';
    loupe.hidden = false;
  }

  // --- interacción con los puntos ---------------------------------------------------------------------------------
  let mode = 'scale';
  function setMode(m) {
    mode = m;
    const el = $('mode-' + m); if (el) el.checked = true;
    stage.classList.toggle('pan', m === 'pan');
    hint();
  }
  function hint() {
    const el = $('stage-hint');
    if (!S.img) { el.textContent = ''; return; }
    if (mode === 'pan') el.textContent = 'Arrastra para mover; rueda del ratón o botones para el zoom.';
    else if (mode === 'scale') el.textContent = S.cal[0] && S.cal[1] ? 'Arrastra una marca ámbar para ajustarla.' : 'Marca dos marcas de la regla.';
    else el.textContent = S.crl[0] && S.crl[1] ? 'Arrastra una marca azul para ajustarla.' : 'Marca la cabeza y la rabadilla.';
  }
  function hit(sx, sy) {
    const R = (S.drag && S.drag.touch) ? 26 : 16;
    let best = null, bd = R;
    for (const set of ['cal', 'crl']) for (let i = 0; i < 2; i++) {
      const p = S[set][i]; if (!p) continue;
      const q = toScreen(p), d = Math.hypot(q[0] - sx, q[1] - sy);
      if (d < bd) { bd = d; best = { set, i }; }
    }
    return best;
  }
  const clampPt = (p) => [Math.min(Math.max(p[0], 0), S.img.w), Math.min(Math.max(p[1], 0), S.img.h)];
  function pos(e) { const r = stage.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; }

  stage.addEventListener('pointerdown', (e) => {
    if (!S.img) return;
    stage.focus({ preventScroll: true });
    const [sx, sy] = pos(e);
    const touch = e.pointerType === 'touch';
    stage.setPointerCapture(e.pointerId);
    S.drag = { touch, start: [sx, sy], ox: S.view.ox, oy: S.view.oy, target: null, pan: false };
    const h = mode === 'pan' ? null : hit(sx, sy);
    if (mode === 'pan') { S.drag.pan = true; stage.classList.add('panning'); return; }
    if (h) { S.drag.target = h; S.sel = h; }
    else {
      const set = mode === 'scale' ? 'cal' : 'crl';
      let i = S[set].findIndex((p) => !p);
      if (i < 0) {                                       // las dos puestas: mueve la más cercana
        const p = toImage(sx, sy);
        const d0 = Math.hypot(S[set][0][0] - p[0], S[set][0][1] - p[1]), d1 = Math.hypot(S[set][1][0] - p[0], S[set][1][1] - p[1]);
        i = d0 <= d1 ? 0 : 1;
      }
      S[set][i] = clampPt(toImage(sx, sy));
      S.drag.target = { set, i }; S.sel = { set, i };
    }
    drawLoupe(sx, sy); update(true);
  });
  stage.addEventListener('pointermove', (e) => {
    if (!S.img) return;
    const [sx, sy] = pos(e);
    if (S.drag && S.drag.pan) { S.view.ox = S.drag.ox + sx - S.drag.start[0]; S.view.oy = S.drag.oy + sy - S.drag.start[1]; draw(); return; }
    if (S.drag && S.drag.target) {
      const t = S.drag.target; S[t.set][t.i] = clampPt(toImage(sx, sy));
      drawLoupe(sx, sy); update(true);
    } else if (e.pointerType !== 'touch' && mode !== 'pan') { drawLoupe(sx, sy); }
    const p = toImage(sx, sy);
    $('stage-status').textContent = `x ${fmt(p[0], 1)} px · y ${fmt(p[1], 1)} px · zoom ${(S.view.k * 100).toFixed(0)} %`;
  });
  const endDrag = () => { S.drag = null; stage.classList.remove('panning'); loupe.hidden = true; update(); };
  stage.addEventListener('pointerup', endDrag);
  stage.addEventListener('pointercancel', endDrag);
  stage.addEventListener('pointerleave', () => { if (!S.drag) loupe.hidden = true; });
  stage.addEventListener('wheel', (e) => { if (!S.img) return; e.preventDefault(); const [sx, sy] = pos(e); zoomAt(e.deltaY < 0 ? 1.15 : 1 / 1.15, sx, sy); }, { passive: false });
  stage.addEventListener('keydown', (e) => {
    if (!S.img) return;
    if (e.key === '+' || e.key === '=') { zoomAt(1.25, cw / 2, ch / 2); e.preventDefault(); return; }
    if (e.key === '-') { zoomAt(1 / 1.25, cw / 2, ch / 2); e.preventDefault(); return; }
    if (!S.sel) return;
    const step = e.shiftKey ? 1 : 0.25, p = S[S.sel.set][S.sel.i];
    if (!p) return;
    if (e.key === 'Delete' || e.key === 'Backspace') { S[S.sel.set][S.sel.i] = null; S.sel = null; e.preventDefault(); update(); return; }
    const d = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] }[e.key];
    if (!d) return;
    e.preventDefault(); S[S.sel.set][S.sel.i] = clampPt([p[0] + d[0], p[1] + d[1]]); update();
  });
  stage.addEventListener('dragover', (e) => e.preventDefault());
  stage.addEventListener('drop', (e) => { e.preventDefault(); const f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]; if (f) loadFile(f); });

  // --- cálculo -------------------------------------------------------------------------------------------------------
  function regionOf(p1, p2) {                            // caja alrededor de la longitud, con 25 % de margen y al menos 48 px por lado
    const L = Math.hypot(p2[0] - p1[0], p2[1] - p1[1]), pad = Math.max(0.25 * L, 12);
    let x0 = Math.min(p1[0], p2[0]) - pad, x1 = Math.max(p1[0], p2[0]) + pad;
    let y0 = Math.min(p1[1], p2[1]) - pad, y1 = Math.max(p1[1], p2[1]) + pad;
    const grow = (a, b, lim) => { if (b - a < 48) { const c = (a + b) / 2; a = c - 24; b = c + 24; } return [Math.max(0, Math.floor(a)), Math.min(lim, Math.ceil(b))]; };
    [x0, x1] = grow(x0, x1, S.img.w); [y0, y1] = grow(y0, y1, S.img.h);
    return { x0, y0, w: x1 - x0, h: y1 - y0 };
  }
  function fingerprint(p1, p2) {
    const r = regionOf(p1, p2);
    if (r.w < Core.MIN_SIDE || r.h < Core.MIN_SIDE) return { r, idx: { lnCv: null, skew: null }, regime: null };
    const g = grayOf(S.img), out = new Float64Array(r.w * r.h);
    for (let y = 0; y < r.h; y++) for (let x = 0; x < r.w; x++) out[y * r.w + x] = g[(r.y0 + y) * S.img.w + (r.x0 + x)];
    const idx = Core.imageIndices(out, r.w, r.h);
    return { r, idx, regime: Core.locateRegime(idx) };
  }
  let projTimer = null;
  function compute(live) {
    const sigma = Math.max(0, num('sigma', 2)), biasRel = num('bias', 0) / 100, tol = Math.max(0.25, num('tol', 1));
    const gaKnownRaw = $('ga-known').value.trim(), gaKnown = gaKnownRaw === '' ? null : parseFloat(gaKnownRaw);
    const meas = S.img ? Core.measure({ cal: S.cal, calMm: num('cal-mm', 0), crl: S.crl, sigmaPx: sigma, biasRel }) : null;
    const res = { meas, sigma, biasRel, tol, gaKnown, cert: null, proj: null, projError: null, fp: null };
    if (meas && meas.lengthMm !== null) {
      res.cert = Core.certifyDating(meas.lengthMm, meas.biasMm, meas.sdMm, tol);
      if (!live) res.fp = fingerprint(S.crl[0], S.crl[1]);
    }
    return res;
  }
  function computeProjection(res) {
    if (!res.meas || res.meas.lengthMm === null) return;
    try {
      const relSd = Math.min(res.meas.relSd, 0.3);
      res.proj = Core.projection(res.meas.lengthMm, {
        crlRelSd: relSd, crlRelBias: res.biasRel,
        gaKnownDays: res.gaKnown !== null && Number.isFinite(res.gaKnown) ? res.gaKnown : null, nDraws: 20000,
      });
      res.projError = null;
    } catch (e) { res.proj = null; res.projError = e.message; }
  }

  // --- presentación --------------------------------------------------------------------------------------------------
  function lamps(state) {
    // state: 'rojo' | 'amarillo' | 'off'
    const mk = (cls, label, on, onCls, locked) =>
      `<span class="lamp ${cls}${on ? ' on ' + onCls : ''}${locked ? ' locked' : ''}"><i></i>${label}</span>`;
    $('lamps').innerHTML = mk('', 'Rojo', state === 'rojo', 'on-red') + mk('', 'Amarillo', state === 'amarillo', 'on-yellow') +
      mk('', 'Verde bloqueado', false, '', true) + (state === 'off' ? mk('', 'Se niega', true, 'on-off') : '');
    $('lamps').setAttribute('aria-label', state === 'off' ? 'Semáforo: se niega a certificar' : `Semáforo: ${state}`);
  }
  function renderResult(res) {
    const m = res.meas, c = res.cert;
    const metrics = [], reasons = [];
    $('btn-copy').disabled = !c;
    if (!S.img) {
      lamps('off');
      $('verdict').textContent = 'Abre una imagen o carga el ejemplo sintético para empezar.';
      $('metrics').innerHTML = ''; $('reasons').innerHTML = ''; $('fingerprint').innerHTML = ''; $('report').value = '';
      return;
    }
    if (S.note) reasons.push(`<li>${esc(S.note)}</li>`);
    if (!c) {
      lamps('off');
      $('verdict').textContent = 'Todavía no hay medida: faltan datos.';
      const issues = (m && m.issues) || [];
      for (const t of issues) reasons.push(`<li class="issue">${esc(t)}</li>`);
      $('metrics').innerHTML = ''; $('reasons').innerHTML = reasons.join(''); $('fingerprint').innerHTML = ''; $('report').value = '';
      return;
    }
    const p = c.pWithinTolerance, tolTxt = `${fmt(res.tol, res.tol % 1 ? 2 : 0)} ${res.tol === 1 ? 'día' : 'días'}`;
    metrics.push(`<div class="metric"><dt>Longitud cráneo-rabadilla</dt><dd>${fmt(m.lengthMm, 1)} mm<small>± ${fmt(m.sdMm, 2)} mm (1 sd) por la puntería</small></dd></div>`);
    if (c.refused) {
      lamps('off');
      $('verdict').textContent = `Se niega a dar una edad: ${fmt(m.lengthMm, 1)} mm está fuera del rango de la fórmula (15 a 95 mm).`;
      metrics.push(`<div class="metric is-off"><dt>Edad por esta longitud</dt><dd>sin edad<small>La fórmula no está publicada fuera de 15–95 mm.</small></dd></div>`);
      reasons.push('<li>Sin un certificado de datación no hay semáforo: la página prefiere callar antes que extrapolar.</li>');
    } else {
      lamps(c.light);
      if (c.light === 'rojo') $('verdict').textContent = `Rojo: con esta puntería, la probabilidad de que la medida, por sí sola, mueva la edad ${tolTxt} o menos es ${pct(p)} %.`;
      else if (c.greenBlocked) $('verdict').textContent = `Amarillo: la medida aportaría poco error (${pct(p)} % de probabilidad de quedar dentro de ${tolTxt}), pero esta página no emite verde sobre una imagen sin validar.`;
      else $('verdict').textContent = `Amarillo: la probabilidad de que el error de edad causado solo por la medida quede dentro de ${tolTxt} es ${pct(p)} %.`;
      metrics.push(`<div class="metric"><dt>Edad por CRL (INTERGROWTH-21st)</dt><dd>${wd(c.gaDays)}<small>${fmt(c.gaDays, 1)} días · semanas+días</small></dd></div>`);
      metrics.push(`<div class="metric"><dt>Dispersión de la edad</dt><dd>± ${fmt(c.sdTotalDays, 1)} d<small>fórmula ± ${fmt(c.sdFormulaDays, 1)} d · medida ± ${fmt(c.sdMeasurementDays, 1)} d</small></dd></div>`);
      metrics.push(`<div class="metric"><dt>P(error por la medida ≤ ${esc(tolTxt)})</dt><dd>${pct(p)} %<small>la medida pone el ${fmt(100 * c.measurementShare, 0)} % de la varianza del error de edad</small></dd></div>`);
      reasons.push(`<li>La edad sale de una ecuación poblacional con su propia dispersión biológica (± ${fmt(c.sdFormulaDays, 1)} d): una medida casi perfecta no hace correcta la edad de un feto concreto.</li>`);
    }
    reasons.push(`<li>Escala: ${fmt(m.mmPerPx, 4)} mm por píxel (referencia de ${fmt(m.refPx, 0)} px). La página supone que la regla marca la distancia que escribiste.</li>`);
    if (res.sigma === 0) reasons.push('<li>Con incertidumbre de puntería 0 el error de medida desaparece del cálculo; ningún lector humano marca sin error.</li>');
    for (const t of m.warnings) reasons.push(`<li class="issue">${esc(t)}</li>`);
    $('metrics').innerHTML = metrics.join('');
    $('reasons').innerHTML = reasons.join('');

    const fp = res.fp;
    if (fp) {
      const { idx, regime } = fp;
      const nums = idx.lnCv === null ? 'no se pudo calcular (región pequeña o sin zonas planas)' :
        `<span class="nums">ln_cv = ${fmt(idx.lnCv, 2)} · asimetría = ${fmt(idx.skew, 2)}</span>`;
      const where = regime === 'clean' ? 'imagen cruda simulada (sin cadena)' : regime === 'chain' ? 'foto de una impresión simulada (con cadena)' :
        'ninguna de las imágenes simuladas con las que se probó el certificado automático';
      const note = regime === null
        ? 'Esta imagen cae <b>fuera de lo conocido</b>: ningún certificado automático del proyecto (H16) la cubre. No invalida tu medida manual, pero impide apoyarla en esos certificados.'
        : 'Esto solo dice a qué se parece la imagen en simulación; no valida el calibre manual ni el equipo.';
      $('fingerprint').innerHTML = `<b>Huella de la imagen</b> (región alrededor de la longitud, ${fp.r.w}×${fp.r.h} px): ${nums}. Se parece a: <b>${where}</b>. ${note}`;
    } else {
      $('fingerprint').innerHTML = '<b>Huella de la imagen</b>: se calcula al soltar la marca.';
    }
    $('report').value = reportText(res);
  }

  function niceStep(span, target) {
    const raw = span / target, mag = Math.pow(10, Math.floor(Math.log10(raw))), f = raw / mag;
    return (f < 1.5 ? 1 : f < 3.5 ? 2 : f < 7.5 ? 5 : 10) * mag;
  }
  function renderEnvelope(res) {
    const chart = $('chart'), notes = [];
    const p = res.proj;
    if (!p) {
      chart.innerHTML = `<p class="chart-empty">${esc(res.projError || 'Sin medida todavía: marca la escala y la longitud para ver la franja.')}</p>`;
      $('env-table').innerHTML = ''; $('env-notes').innerHTML = ''; return;
    }
    const m = res.meas, z90 = 1.645, cov = Math.round(100 * p.coverage);
    const rows = p.rows.filter((r) => r.inSourceRange);
    const x0 = { x: 0, lo: m.lengthMm - z90 * m.sdMm, hi: m.lengthMm + z90 * m.sdMm };
    const pts = [x0, ...rows.map((r) => ({ x: r.daysAhead, lo: r.envelope.lo, hi: r.envelope.hi }))];
    const meanPts = rows.map((r) => ({ x: r.daysAhead, y: r.populationMeanMm }));
    try { meanPts.unshift({ x: 0, y: Core.crlMeanMm(p.gaNow.medianDays) }); } catch (e) { /* edad fuera del rango de la ecuación */ }
    let ymin = Math.min(...pts.map((q) => q.lo), ...meanPts.map((q) => q.y)), ymax = Math.max(...pts.map((q) => q.hi), ...meanPts.map((q) => q.y));
    const pad = 0.08 * (ymax - ymin || 1); ymin -= pad; ymax += pad;
    const step = niceStep(ymax - ymin, 5);
    ymin = Math.floor(ymin / step) * step; ymax = Math.ceil(ymax / step) * step;
    const cwid = Math.max(300, Math.min(880, Math.round(chart.clientWidth || 680))), wide = cwid >= 560;
    const W = cwid, H = wide ? 320 : 270, L = 44, R = wide ? 160 : 14, T = 22, B = 40;
    const X = (d) => L + (d / 28) * (W - L - R), Y = (v) => T + (1 - (v - ymin) / (ymax - ymin)) * (H - T - B);
    let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Franja de tamaño de referencia de 0 a 28 días después de la medida; la tabla de abajo trae los mismos valores">`;
    for (let v = ymin; v <= ymax + 1e-9; v += step) s += `<line class="grid" x1="${L}" x2="${W - R}" y1="${Y(v)}" y2="${Y(v)}"/><text x="${L - 8}" y="${Y(v) + 4}" text-anchor="end">${fmt(v, step < 1 ? 1 : 0)}</text>`;
    s += `<line class="axis" x1="${L}" x2="${W - R}" y1="${H - B}" y2="${H - B}"/>`;
    for (const d of [0, 7, 14, 21, 28]) s += `<text x="${X(d)}" y="${H - B + 18}" text-anchor="${d === 0 ? 'start' : d === 28 ? 'end' : 'middle'}">${d === 0 ? 'medida' : '+' + d + ' d'}</text>`;
    s += `<text x="${L - 8}" y="${T - 8}" text-anchor="end">mm</text>`;
    const top = pts.map((q) => `${X(q.x)},${Y(q.hi)}`), bot = pts.slice().reverse().map((q) => `${X(q.x)},${Y(q.lo)}`);
    s += `<polygon class="band" points="${top.concat(bot).join(' ')}"/>`;
    if (meanPts.length > 1) s += `<polyline class="mean" points="${meanPts.map((q) => `${X(q.x)},${Y(q.y)}`).join(' ')}"/>`;
    s += `<line class="whisk" x1="${X(0)}" x2="${X(0)}" y1="${Y(x0.lo)}" y2="${Y(x0.hi)}"/><circle class="dot" cx="${X(0)}" cy="${Y(m.lengthMm)}" r="5"/>`;
    s += `<text class="lbl" x="${X(0) + 10}" y="${Y(m.lengthMm) + 20}">tu medida: ${fmt(m.lengthMm, 1)} mm</text>`;
    if (wide) {
      const last = pts[pts.length - 1], mid = (last.lo + last.hi) / 2;
      s += `<text class="lbl" x="${X(last.x) + 10}" y="${Y(mid) + 4}">Franja de referencia</text><text class="lbl-soft" x="${X(last.x) + 10}" y="${Y(mid) + 19}">${cov} % de la población</text>`;
    }
    s += '</svg>';
    s += `<ul class="legend" aria-hidden="true"><li><i class="sw-band"></i>Franja de referencia (${cov} % de la población, con el error de tu medida)</li><li><i class="sw-mean"></i>Media poblacional</li><li><i class="sw-dot"></i>Tu medida y su intervalo del 90 %</li></ul>`;
    chart.innerHTML = s;

    let t = '<table><thead><tr><th class="num">Días después</th><th>Edad</th><th class="num">Media poblacional (mm)</th><th class="num">Persistencia (mm)</th><th class="num">Regresión (mm)</th><th class="num">Envolvente (mm)</th></tr></thead><tbody>';
    for (const r of p.rows) {
      if (!r.inSourceRange) { t += `<tr><td class="num">${r.daysAhead}</td><td>${wd(r.gaDays)}</td><td colspan="4">fuera del rango de la fuente (58–105 días): no se calcula</td></tr>`; continue; }
      const q = (o) => `${fmt(o.lo, 1)}–${fmt(o.hi, 1)}`;
      t += `<tr><td class="num">${r.daysAhead}</td><td>${wd(r.gaDays)}</td><td class="num">${fmt(r.populationMeanMm, 1)}</td><td class="num">${q(r.persistence)}</td><td class="num">${q(r.regression)}</td><td class="num">${q(r.envelope)}</td></tr>`;
    }
    $('env-table').innerHTML = t + '</tbody></table>';
    notes.push(`Edad ahora (${p.gaNow.source}): ${fmt(p.gaNow.medianDays, 0)} días (${wd(p.gaNow.medianDays)}); intervalo ${cov} %: ${fmt(p.gaNow.loDays, 0)}–${fmt(p.gaNow.hiDays, 0)} días.`);
    notes.push('<b>Persistencia</b>: el feto conserva su posición respecto de la referencia. <b>Regresión</b>: la pierde por completo. La realidad no es ninguno de los dos extremos y la correlación entre visitas no se conoce (sin validar; la prueba H17 pide datos seriados).');
    if (p.gaNow.source.startsWith('estimada')) notes.push('Como la edad se estimó con esta misma longitud, el tamaño no puede decir si el feto es grande o pequeño para su edad: por construcción cae en el centro de la referencia.');
    if (rows.length < p.rows.length) notes.push('La ecuación de referencia solo está publicada hasta 105 días: las semanas siguientes que pasan de ahí no se dibujan.');
    $('env-notes').innerHTML = notes.map((x) => `<li>${x}</li>`).join('');
  }

  function reportText(res) {
    const m = res.meas, c = res.cert, p = res.proj, fp = res.fp;
    const L = ['Calibre Geovida — informe (solo investigación y educación; no es un dispositivo médico)', ''];
    L.push(`Longitud cráneo-rabadilla: ${fmt(m.lengthMm, 2)} mm ± ${fmt(m.sdMm, 2)} mm (1 sd)`);
    L.push(`Escala: ${fmt(m.mmPerPx, 4)} mm/px (referencia de ${fmt(m.refPx, 0)} px = ${fmt(num('cal-mm', 0), 2)} mm). Objeto: ${fmt(m.lengthPx, 1)} px.`);
    L.push(`Supuestos declarados: incertidumbre por punto ${fmt(res.sigma, 2)} px; sesgo ${fmt(100 * res.biasRel, 1)} %; tolerancia ${fmt(res.tol, 2)} d.`);
    if (c.refused) L.push('Edad: se niega (fuera del rango 15–95 mm de la fórmula).');
    else {
      L.push(`Edad por CRL (INTERGROWTH-21st): ${fmt(c.gaDays, 1)} d (${wd(c.gaDays)}); dispersión total ± ${fmt(c.sdTotalDays, 1)} d (fórmula ± ${fmt(c.sdFormulaDays, 1)}, medida ± ${fmt(c.sdMeasurementDays, 1)}).`);
      L.push(`P(error por la medida ≤ ${fmt(res.tol, 2)} d) = ${pct(c.pWithinTolerance)} %. Semáforo: ${c.light}${c.greenBlocked ? ' (verde bloqueado: imagen sin validar)' : ''}.`);
    }
    if (fp) L.push(`Huella de la imagen: ln_cv ${fmt(fp.idx.lnCv, 2)}, asimetría ${fmt(fp.idx.skew, 2)}; ${fp.regime ? 'se parece a ' + fp.regime + ' (simulación)' : 'fuera de lo conocido por la guardia H16'}.`);
    if (p) {
      L.push('', `Tamaño de referencia (intervalo ${Math.round(100 * p.coverage)} %), edad ${p.gaNow.source}:`);
      for (const r of p.rows) L.push(r.inSourceRange ? `  +${r.daysAhead} d (${wd(r.gaDays)}): envolvente ${fmt(r.envelope.lo, 1)}–${fmt(r.envelope.hi, 1)} mm; media poblacional ${fmt(r.populationMeanMm, 1)} mm` : `  +${r.daysAhead} d: fuera del rango de la fuente (58–105 d)`);
    }
    L.push('', 'No predice el crecimiento ni el aspecto de ningún feto. Sin validar con imágenes reales. No contiene la imagen ni datos identificables.');
    return L.join('\n');
  }

  function update(live) {
    const res = compute(!!live);
    S.last = res;
    const m = res.meas;
    $('cal-readout').textContent = m && m.refPx ? `referencia ${fmt(m.refPx, 1)} px → ${fmt(m.mmPerPx, 4)} mm/px` :
      (S.cal[0] && S.cal[1] ? 'esperando la distancia real' : `${S.cal.filter(Boolean).length} de 2 marcas`);
    $('crl-readout').textContent = m && m.lengthMm !== null ? `${fmt(m.lengthPx, 1)} px → ${fmt(m.lengthMm, 2)} mm` : `${S.crl.filter(Boolean).length} de 2 marcas`;
    const b = $('stage-badge'); b.hidden = !S.example; b.textContent = S.example ? 'Ejemplo sintético, no es una ecografía real' : '';
    hint(); draw();
    if (live) {                                          // mientras se arrastra solo se recalcula lo barato
      renderResult(res);
      clearTimeout(projTimer); projTimer = setTimeout(() => { computeProjection(res); renderEnvelope(res); }, 120);
      return;
    }
    computeProjection(res); renderResult(res); renderEnvelope(res);
  }

  // --- eventos de la página ------------------------------------------------------------------------------------------
  $('file').addEventListener('change', (e) => { loadFile(e.target.files[0]); e.target.value = ''; });
  $('btn-example').addEventListener('click', useExample);
  for (const m of ['scale', 'crl', 'pan']) $('mode-' + m).addEventListener('change', () => setMode(m));
  $('zoom-in').addEventListener('click', () => zoomAt(1.25, cw / 2, ch / 2));
  $('zoom-out').addEventListener('click', () => zoomAt(1 / 1.25, cw / 2, ch / 2));
  $('zoom-fit').addEventListener('click', () => { fitView(); draw(); });
  for (const id of ['cal-mm', 'sigma', 'bias', 'tol', 'ga-known']) $(id).addEventListener('input', () => update());
  $('btn-copy').addEventListener('click', async () => {
    const text = $('report').value, st = $('copy-status');
    try { await navigator.clipboard.writeText(text); st.textContent = 'Copiado.'; }
    catch (e) { $('report-box').open = true; $('report').focus(); $('report').select(); st.textContent = 'Selecciona y copia el texto de abajo.'; }
    setTimeout(() => { st.textContent = ''; }, 4000);
  });
  let chartW = 0;
  const rerenderChart = () => { const w = $('chart').clientWidth; if (S.last && S.last.proj && Math.abs(w - chartW) > 8) { chartW = w; renderEnvelope(S.last); } };
  window.addEventListener('resize', () => { resizeStage(); fitView(); draw(); rerenderChart(); });
  if (window.ResizeObserver) new ResizeObserver(() => { const r = stage.getBoundingClientRect(); if (Math.round(r.width) !== cw || Math.round(r.height) !== ch) { resizeStage(); if (S.img && !S.drag) fitView(); draw(); } }).observe(stage);

  resizeStage();
  useExample();
})();
