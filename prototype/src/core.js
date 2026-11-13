/* CORE:BEGIN */
/* Núcleo matemático de Calibre Geovida. Sin DOM, sin red, sin almacenamiento: se prueba con Node contra el código Python.
   Fórmulas de edad: INTERGROWTH-21st (Papageorghiou et al. 2014, Ultrasound Obstet Gynecol), igual que geovida.dating y geovida.trajectory.
   Solo investigación y educación. */
const Core = (() => {
  'use strict';

  const RANGE_MM = [15, 95];            // rango de la fórmula de edad por CRL
  const GA_RANGE = [58, 105];           // rango (días) de la ecuación de tamaño de referencia
  const GREEN = 0.90, RED = 0.50;
  const HORIZONS = [7, 14, 21, 28];
  const MIN_SIDE = 32, WINDOW = 7, MIN_FLAT_PX = 200, MIN_MEAN = 0.02, MIN_SD = 1e-4;   // iguales a geovida.chainguard

  // Cajas de soporte congeladas de H16 (results/summary/h16_chain_frozen.json, modelo de CRL): lo que la guardia vio en simulación.
  const SUPPORT_BODY = {
    chain: { lnCv: [-2.020073397278121, -0.9553965256666371], skew: [0.3164463343596403, 1.3634433173550824] },
    clean: { lnCv: [0.03264821899984906, 0.9043419798682549], skew: [2.060048442669502, 2.8210492525818642] },
  };

  // --- funciones especiales ---------------------------------------------------------------------------------------
  function erfcCF(x) {                                 // fracción continua, x >= 2.5
    let f = x;
    for (let k = 60; k >= 1; k--) f = x + (k / 2) / f;
    return Math.exp(-x * x) / (Math.sqrt(Math.PI) * f);
  }
  function erf(x) {
    if (Number.isNaN(x)) return NaN;
    const ax = Math.abs(x);
    let r;
    if (ax < 2.5) {                                    // serie de Taylor
      let term = ax, sum = ax;
      const x2 = ax * ax;
      for (let n = 1; n < 200; n++) {
        term *= -x2 / n;
        const add = term / (2 * n + 1);
        sum += add;
        if (Math.abs(add) < 1e-17 * Math.abs(sum)) break;
      }
      r = 2 / Math.sqrt(Math.PI) * sum;
    } else {
      r = 1 - erfcCF(ax);
    }
    return x < 0 ? -r : r;
  }
  const phi = (x) => 0.5 * (1 + erf(x / Math.SQRT2));

  // --- datación por CRL (geovida.dating) --------------------------------------------------------------------------
  function checkCrl(c) {
    if (!(c > 0) || Number.isNaN(c)) throw new Error('la longitud cráneo-rabadilla debe ser un número > 0 (mm)');
    return c;
  }
  const inFormulaRange = (c) => c >= RANGE_MM[0] && c <= RANGE_MM[1];
  const gaDays = (c) => { checkCrl(c); return 40.9041 + 3.21585 * Math.sqrt(c) + 0.348956 * c; };
  const sdGaDays = (c) => { checkCrl(c); return 2.39102 + 0.0193474 * c; };
  const dgaDcrl = (c) => { checkCrl(c); return 3.21585 / (2 * Math.sqrt(c)) + 0.348956; };
  function weeksDays(days) {
    const total = Math.round(days);
    return [Math.floor(total / 7), total - 7 * Math.floor(total / 7)];
  }
  function probWithin(bias, sd, tol) {                 // P(|e| <= tol), e ~ N(bias, sd^2)
    if (sd <= 0) return Math.abs(bias) <= tol ? 1 : 0;
    return phi((tol - bias) / sd) - phi((-tol - bias) / sd);
  }
  function certifyDating(crl, biasMm, sdMm, tol = 1) {
    const ga = gaDays(crl), slope = dgaDcrl(crl), sdForm = sdGaDays(crl);
    const bDays = slope * biasMm, sDays = Math.abs(slope) * sdMm;
    const p = probWithin(bDays, sDays, tol);
    const inRange = inFormulaRange(crl);
    let lightRaw = p >= GREEN ? 'verde' : (p < RED ? 'rojo' : 'amarillo');
    if (!inRange && lightRaw === 'verde') lightRaw = 'amarillo';
    const share = (sDays ** 2) / (sDays ** 2 + sdForm ** 2);
    const greenBlocked = lightRaw === 'verde';
    // Tope del proyecto: sobre una imagen sin validar no se emite verde (geovida.real2d).
    const light = greenBlocked ? 'amarillo' : lightRaw;
    return {
      crlMm: crl, gaDays: ga, gaWeeksDays: weeksDays(ga), sdFormulaDays: sdForm, sdMeasurementDays: sDays,
      biasMeasurementDays: bDays, sdTotalDays: Math.sqrt(sdForm ** 2 + sDays ** 2), measurementShare: share,
      toleranceDays: tol, pWithinTolerance: p, inRange, lightRaw, light, greenBlocked, refused: !inRange,
    };
  }

  // --- presupuesto de incertidumbre del calibre manual -------------------------------------------------------------
  const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
  /* Longitud = (píxeles entre los extremos) × (mm por píxel de la escala). Cada punto marcado tiene una incertidumbre de
     puntería de sigmaPx píxeles a lo largo de la línea. Las dos longitudes en píxeles (objeto y escala) llevan errores
     independientes: var_rel = 2σ²/L² + 2σ²/R². El sesgo relativo declarado no mueve la lectura: solo entra al certificado. */
  function measure({ cal, calMm, crl, sigmaPx, biasRel }) {
    const issues = [], warnings = [];
    const empty = { mmPerPx: null, lengthMm: null, lengthPx: null, refPx: null, relSd: null, sdMm: null, biasMm: null, issues, warnings };
    if (!cal || !cal[0] || !cal[1]) issues.push('Marca los dos puntos de la escala.');
    if (!(calMm > 0)) issues.push('La distancia real entre los dos puntos de la escala debe ser mayor que 0 mm.');
    if (!crl || !crl[0] || !crl[1]) issues.push('Marca los dos extremos de la longitud cráneo-rabadilla.');
    if (issues.length) return empty;
    const refPx = dist(cal[0], cal[1]), lPx = dist(crl[0], crl[1]);
    if (!(refPx > 0)) issues.push('Los dos puntos de la escala coinciden.');
    if (!(lPx > 0)) issues.push('Los dos extremos de la longitud coinciden.');
    if (issues.length) return empty;
    const sigma = Math.max(0, Number(sigmaPx) || 0);
    const s = calMm / refPx;
    const lengthMm = lPx * s;
    const relSd = Math.sqrt(2 * sigma ** 2 / lPx ** 2 + 2 * sigma ** 2 / refPx ** 2);
    if (lPx < 40) warnings.push(`El objeto mide solo ${lPx.toFixed(0)} píxeles: la incertidumbre relativa de la puntería es grande.`);
    if (refPx < 60) warnings.push(`La referencia de escala mide solo ${refPx.toFixed(0)} píxeles: separa más los dos puntos de la regla.`);
    if (s > 0.5) warnings.push(`Cada píxel mide ${s.toFixed(2)} mm: la imagen es demasiado gruesa para medir con precisión.`);
    return { mmPerPx: s, lengthMm, lengthPx: lPx, refPx, relSd, sdMm: lengthMm * relSd, biasMm: (Number(biasRel) || 0) * lengthMm, issues, warnings };
  }

  // --- tamaño de referencia (geovida.trajectory) ---------------------------------------------------------------
  function checkGa(ga) {
    if (Number.isNaN(ga) || !(ga >= GA_RANGE[0] && ga <= GA_RANGE[1])) {
      throw new Error(`la edad ${ga} d está fuera del rango publicado de la ecuación (${GA_RANGE[0]}–${GA_RANGE[1]} días)`);
    }
    return ga;
  }
  const clipGa = (g) => Math.min(Math.max(g, GA_RANGE[0]), GA_RANGE[1]);
  const meanAt = (g) => -50.6562 + 0.815118 * g + 0.00535302 * g * g;
  const sdAt = (g) => -2.21626 + 0.0984894 * g;
  const crlMeanMm = (ga) => meanAt(checkGa(ga));
  const crlSdMm = (ga) => sdAt(checkGa(ga));

  function mulberry32(seed) {
    let a = seed >>> 0;
    return () => {
      a = (a + 0x6D2B79F5) >>> 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function makeNormal(rng) {
    let spare = null;
    return () => {
      if (spare !== null) { const v = spare; spare = null; return v; }
      let u = 0;
      while (u === 0) u = rng();
      const v = rng(), r = Math.sqrt(-2 * Math.log(u));
      spare = r * Math.sin(2 * Math.PI * v);
      return r * Math.cos(2 * Math.PI * v);
    };
  }
  function quantileSorted(s, q) {                      // interpolación lineal, como numpy
    const pos = (s.length - 1) * q, i = Math.floor(pos), f = pos - i;
    return i + 1 < s.length ? s[i] * (1 - f) + s[i + 1] * f : s[i];
  }
  function quantiles(arr, coverage) {
    const s = Float64Array.from(arr).sort();
    const a = (1 - coverage) / 2;
    return { lo: quantileSorted(s, a), median: quantileSorted(s, 0.5), hi: quantileSorted(s, 1 - a) };
  }

  /* Franja de referencia a varios días de la medida, con el error de la CRL y la incertidumbre de la edad propagados por Monte Carlo.
     No predice el crecimiento ni el aspecto de ningún feto. Dos escenarios extremos: 'persistence' (conserva su puntuación z) y
     'regression' (la pierde por completo). La correlación real entre visitas no se conoce. */
  function projection(crl, opts = {}) {
    const { crlRelSd = 0, crlRelBias = 0, gaKnownDays = null, horizons = HORIZONS, nDraws = 20000, seed = 20261218, coverage = 0.90 } = opts;
    if (!(crl > 0) || Number.isNaN(crl)) throw new Error('la longitud debe ser un número > 0 (mm)');
    if (crlRelSd < 0 || !(coverage >= 0 && coverage < 1) || nDraws < 100) throw new Error('parámetros fuera de rango');
    const rng = mulberry32(seed), z = makeNormal(rng);
    const n = Math.floor(nDraws);
    const meas = new Float64Array(n), gaTrue = new Float64Array(n);
    for (let i = 0; i < n; i++) meas[i] = crl / Math.max(1 + crlRelBias + crlRelSd * z(), 0.05);
    let source;
    if (gaKnownDays === null || gaKnownDays === undefined) {
      if (!inFormulaRange(crl)) {
        throw new Error(`la CRL ${crl} mm está fuera del rango de la fórmula de edad (${RANGE_MM[0]}–${RANGE_MM[1]} mm); da la edad con gaKnownDays`);
      }
      for (let i = 0; i < n; i++) gaTrue[i] = gaDays(meas[i]) + sdGaDays(meas[i]) * z();
      source = 'estimada con esta misma CRL';
    } else {
      gaTrue.fill(checkGa(gaKnownDays));
      source = 'dada por otra vía';
    }
    const z0 = new Float64Array(n), eps = new Float64Array(n);
    for (let i = 0; i < n; i++) {
      const g = clipGa(gaTrue[i]);
      z0[i] = (meas[i] - meanAt(g)) / sdAt(g);
    }
    for (let i = 0; i < n; i++) eps[i] = z();
    const gaMed = quantiles(gaTrue, coverage).median;
    const qNow = quantiles(gaTrue, coverage);
    const gaNow = { source, medianDays: gaMed, weeksDays: weeksDays(gaMed), loDays: qNow.lo, hiDays: qNow.hi };
    const rows = [];
    const bufP = new Float64Array(n), bufR = new Float64Array(n);
    for (const h0 of horizons) {
      const h = Number(h0), gaCentral = gaMed + h;
      const inRange = gaCentral >= GA_RANGE[0] && gaCentral <= GA_RANGE[1];
      const row = { daysAhead: h, gaDays: gaCentral, gaWeeksDays: weeksDays(gaCentral), inSourceRange: inRange,
                    populationMeanMm: null, populationSdMm: null, persistence: null, regression: null, envelope: null };
      if (inRange) {
        for (let i = 0; i < n; i++) {
          const g = clipGa(gaTrue[i] + h), m = meanAt(g), s = sdAt(g);
          bufP[i] = m + z0[i] * s;
          bufR[i] = m + eps[i] * s;
        }
        const pers = quantiles(bufP, coverage), regr = quantiles(bufR, coverage);
        row.populationMeanMm = meanAt(gaCentral);
        row.populationSdMm = sdAt(gaCentral);
        row.persistence = pers;
        row.regression = regr;
        row.envelope = { lo: Math.min(pers.lo, regr.lo), hi: Math.max(pers.hi, regr.hi) };
      }
      rows.push(row);
    }
    return { crlMmMeasured: crl, crlRelSd, crlRelBias, coverage, nDraws: n, seed, gaNow, rows };
  }

  // --- huella de la imagen (geovida.chainguard.image_indices) ---------------------------------------------------
  function percentile(values, q) {                     // q en [0, 100], interpolación lineal como numpy
    const s = Float64Array.from(values).sort();
    return quantileSorted(s, q / 100);
  }
  function kernelUniform(size) { return new Float64Array(size).fill(1 / size); }
  function kernelGauss(sigma, truncate = 4.0) {        // igual que scipy.ndimage.gaussian_filter1d, orden 0
    const lw = Math.floor(truncate * sigma + 0.5);
    const k = new Float64Array(2 * lw + 1);
    let sum = 0;
    for (let i = -lw; i <= lw; i++) { const v = Math.exp(-0.5 / (sigma * sigma) * i * i); k[i + lw] = v; sum += v; }
    for (let i = 0; i < k.length; i++) k[i] /= sum;
    return k;
  }
  function convSeparable(src, w, h, kernel) {          // modo 'reflect' de scipy: (d c b a | a b c d | d c b a)
    const r = (kernel.length - 1) >> 1;
    const tmp = new Float64Array(w * h), out = new Float64Array(w * h);
    const refl = (i, n) => (i < 0 ? -i - 1 : (i >= n ? 2 * n - i - 1 : i));
    for (let y = 0; y < h; y++) {
      const row = y * w;
      for (let x = 0; x < w; x++) {
        let acc = 0;
        for (let k = -r; k <= r; k++) acc += kernel[k + r] * src[row + refl(x + k, w)];
        tmp[row + x] = acc;
      }
    }
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        let acc = 0;
        for (let k = -r; k <= r; k++) acc += kernel[k + r] * tmp[refl(y + k, h) * w + x];
        out[y * w + x] = acc;
      }
    }
    return out;
  }
  function medianOf(arr) {
    const s = Float64Array.from(arr).sort(), n = s.length;
    return n % 2 ? s[(n - 1) / 2] : 0.5 * (s[n / 2 - 1] + s[n / 2]);
  }
  /* ln_cv: logaritmo de la variación local mediana en zonas sin bordes (baja cuando una compresión tonal aplana el grano).
     skew: asimetría de las intensidades. Solo usa la imagen. null si no hay base para medirlos. */
  function imageIndices(flat, w, h) {
    const NONE = { lnCv: null, skew: null };
    if (!(w >= MIN_SIDE && h >= MIN_SIDE) || flat.length !== w * h) return NONE;
    const a = Float64Array.from(flat);
    for (let i = 0; i < a.length; i++) if (!Number.isFinite(a[i])) return NONE;
    const scale = percentile(a, 99.5);
    if (!(scale > 0)) return NONE;
    const n = a.length, x = new Float64Array(n);
    let mean = 0;
    for (let i = 0; i < n; i++) { x[i] = a[i] / scale; mean += x[i]; }
    mean /= n;
    let v2 = 0, v3 = 0;
    for (let i = 0; i < n; i++) { const d = x[i] - mean; v2 += d * d; v3 += d * d * d; }
    const sdImg = Math.sqrt(v2 / n);
    const skew = sdImg > 1e-12 ? (v3 / n) / (sdImg ** 3) : null;
    const xx = new Float64Array(n);
    for (let i = 0; i < n; i++) xx[i] = x[i] * x[i];
    const ku = kernelUniform(WINDOW);
    const m = convSeparable(x, w, h, ku), m2 = convSeparable(xx, w, h, ku);
    const sd = new Float64Array(n);
    for (let i = 0; i < n; i++) sd[i] = Math.sqrt(Math.max(m2[i] - m[i] * m[i], 0));
    const gs = convSeparable(x, w, h, kernelGauss(1.5));
    const g = new Float64Array(n);
    for (let yy = 0; yy < h; yy++) {
      for (let xxp = 0; xxp < w; xxp++) {
        const i = yy * w + xxp;
        const gy = yy === 0 ? gs[i + w] - gs[i] : (yy === h - 1 ? gs[i] - gs[i - w] : (gs[i + w] - gs[i - w]) / 2);
        const gx = xxp === 0 ? gs[i + 1] - gs[i] : (xxp === w - 1 ? gs[i] - gs[i - 1] : (gs[i + 1] - gs[i - 1]) / 2);
        g[i] = Math.hypot(gx, gy);
      }
    }
    const thr = percentile(g, 50);
    const cvs = [];
    for (let i = 0; i < n; i++) if (g[i] < thr && m[i] > MIN_MEAN && sd[i] > MIN_SD) cvs.push(sd[i] / m[i]);
    if (cvs.length < MIN_FLAT_PX) return { lnCv: null, skew };
    const cv = medianOf(cvs);
    return { lnCv: cv > 0 ? Math.log(cv) : null, skew };
  }
  const supportBody = () => SUPPORT_BODY;
  /* 'clean' (imagen cruda simulada), 'chain' (cadena pantalla-impresión-foto simulada) o null si cae fuera de todas las cajas. */
  function locateRegime(idx) {
    if (!idx || idx.lnCv === null || idx.skew === null || !Number.isFinite(idx.lnCv) || !Number.isFinite(idx.skew)) return null;
    const eps = 1e-12;
    for (const name of ['chain', 'clean']) {
      const b = SUPPORT_BODY[name];
      if (idx.lnCv >= b.lnCv[0] - eps && idx.lnCv <= b.lnCv[1] + eps && idx.skew >= b.skew[0] - eps && idx.skew <= b.skew[1] + eps) return name;
    }
    return null;
  }

  return {
    RANGE_MM, GA_RANGE, GREEN, RED, HORIZONS, MIN_SIDE,
    erf, phi, inFormulaRange, gaDays, sdGaDays, dgaDcrl, weeksDays, probWithin, certifyDating,
    measure, crlMeanMm, crlSdMm, projection, imageIndices, supportBody, locateRegime, mulberry32,
  };
})();
/* CORE:END */
