// Núcleo numérico del laboratorio (sin DOM): fantomas, voxelización, medidas y semáforo.
// Reproduce en el navegador lo que hace geovida en Python (perfil «ideal», umbral 0.5).
const GV = (() => {
  const PI = Math.PI;
  const SHAPES = {
    ball: { label: "Bola", betti: [1, 0, 0], half: [0.5, 0.5, 0.5], vol: 4 / 3 * PI * 0.125,
      inside: (x, y, z) => x * x + y * y + z * z <= 0.25 },
    ellipsoid: { label: "Elipsoide", betti: [1, 0, 0], half: [1.0, 0.75, 0.5], vol: 4 / 3 * PI * 1.0 * 0.75 * 0.5,
      inside: (x, y, z) => x * x + (y / 0.75) ** 2 + (z / 0.5) ** 2 <= 1 },
    capsule: { label: "Cápsula", betti: [1, 0, 0], half: [0.5, 0.5, 2.0], vol: PI * 0.25 * 3 + 4 / 3 * PI * 0.125,
      inside: (x, y, z) => { const r2 = x * x + y * y, az = Math.abs(z);
        return (r2 <= 0.25 && az <= 1.5) || (r2 + (az - 1.5) ** 2 <= 0.25); } },
    torus: { label: "Toro", betti: [1, 1, 0], half: [1.75, 1.75, 0.5], vol: 2 * PI * PI * 1.25 * 0.25,
      inside: (x, y, z) => (Math.hypot(x, y) - 1.25) ** 2 + z * z <= 0.25 },
    torus_tight: { label: "Toro de hueco estrecho", betti: [1, 1, 0], half: [1.25, 1.25, 0.5], vol: 2 * PI * PI * 0.75 * 0.25,
      inside: (x, y, z) => (Math.hypot(x, y) - 0.75) ** 2 + z * z <= 0.25 },
    shell: { label: "Cáscara hueca", betti: [1, 0, 1], half: [3, 3, 3], vol: 4 / 3 * PI * (27 - 8),
      inside: (x, y, z) => { const d = x * x + y * y + z * z; return d <= 9 && d >= 4; } },
    tube: { label: "Tubo", betti: [1, 1, 0], half: [2, 2, 2.5], vol: PI * (4 - 1) * 5,
      inside: (x, y, z) => { const r2 = x * x + y * y; return r2 <= 4 && r2 >= 1 && Math.abs(z) <= 2.5; } },
    dumbbell: (() => { const R = 2, r = 0.5, L = 1.5, root = Math.sqrt(R * R - r * r), d = root + L / 2;
      return { label: "Mancuerna", betti: [1, 0, 0], half: [R, R, d + R], vol: 2 * 4 / 3 * PI * R ** 3 + PI * r * r * L,
        inside: (x, y, z) => { const r2 = x * x + y * y;
          return r2 + (z - d) ** 2 <= R * R || r2 + (z + d) ** 2 <= R * R || (r2 <= r * r && Math.abs(z) <= d); } }; })(),
    cup: { label: "Copa", betti: [1, 0, 0], half: [2.5, 2.5, 2.5], vol: 2 / 3 * PI * (2.5 ** 3 - 1.5 ** 3),
      inside: (x, y, z) => { const d = x * x + y * y + z * z; return d <= 6.25 && d >= 2.25 && z >= 0; } },
  };

  // Semáforo de volumen congelado en H6 (results/summary/h6_frozen_models.json).
  const H6 = {
    "global|ideal": { a: 3.8711207594408537, b: 5.913882833618431 },
    "global|realistic": { a: 3.329914796589346, b: 6.301357579588664 },
  };
  const GREEN = 0.90, RED = 0.50;

  function mulberry32(seed) {
    let a = seed >>> 0;
    return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  }

  function randomRotation(rng) {           // cuaternión uniforme (Shoemake)
    const u1 = rng(), u2 = rng(), u3 = rng();
    const a = Math.sqrt(1 - u1), b = Math.sqrt(u1);
    const q = [a * Math.sin(2 * PI * u2), a * Math.cos(2 * PI * u2), b * Math.sin(2 * PI * u3), b * Math.cos(2 * PI * u3)];
    const [x, y, z, w] = q;
    return [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w),
            2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w),
            2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)];
  }

  // Imagen de cobertura (volumen parcial) del fantoma con grosor t = tOverH vóxeles (h_xy = 1).
  function render(shapeName, tOverH, anisotropy, seed, nSub = 3) {
    const S = SHAPES[shapeName], rng = mulberry32(seed);
    const R = randomRotation(rng);
    const sp = [1, 1, anisotropy];
    const off = [(rng() - 0.5) * sp[0], (rng() - 0.5) * sp[1], (rng() - 0.5) * sp[2]];
    const t = tOverH, n = [0, 0, 0];
    for (let i = 0; i < 3; i++) {
      const half = (Math.abs(R[3 * i]) * S.half[0] + Math.abs(R[3 * i + 1]) * S.half[1] + Math.abs(R[3 * i + 2]) * S.half[2]) * t + 2 * sp[i];
      n[i] = 2 * Math.ceil(half / sp[i]);
    }
    const [nx, ny, nz] = n, cov = new Float32Array(nx * ny * nz), w = 1 / (nSub ** 3);
    const sub = []; for (let s = 0; s < nSub; s++) sub.push((s + 0.5) / nSub - 0.5);
    let idx = 0;
    for (let i = 0; i < nx; i++) for (let j = 0; j < ny; j++) for (let k = 0; k < nz; k++, idx++) {
      const cx = (i - (nx - 1) / 2) * sp[0] + off[0], cy = (j - (ny - 1) / 2) * sp[1] + off[1], cz = (k - (nz - 1) / 2) * sp[2] + off[2];
      let acc = 0;
      for (const dx of sub) for (const dy of sub) for (const dz of sub) {
        const px = cx + dx * sp[0], py = cy + dy * sp[1], pz = cz + dz * sp[2];
        // del laboratorio al marco canónico: p · R (como `pts @ rot` en imaging.py)
        const qx = (px * R[0] + py * R[3] + pz * R[6]) / t, qy = (px * R[1] + py * R[4] + pz * R[7]) / t, qz = (px * R[2] + py * R[5] + pz * R[8]) / t;
        if (S.inside(qx, qy, qz)) acc++;
      }
      cov[idx] = acc * w;
    }
    return { cov, n, sp, trueVolume: S.vol * t ** 3, trueBetti: S.betti };
  }

  function threshold(cov, thr = 0.5) {
    const m = new Uint8Array(cov.length);
    for (let i = 0; i < cov.length; i++) m[i] = cov[i] >= thr ? 1 : 0;
    return m;
  }

  // Transformada de distancia euclídea exacta (Felzenszwalb y Huttenlocher), al cuadrado, anisótropa.
  function edtSquared(mask, n, sp) {
    const [nx, ny, nz] = n, INF = 1e20, f = new Float64Array(mask.length);
    for (let i = 0; i < mask.length; i++) f[i] = mask[i] ? INF : 0;
    const maxn = Math.max(nx, ny, nz), d = new Float64Array(maxn), g = new Float64Array(maxn), v = new Int32Array(maxn), z = new Float64Array(maxn + 1);
    const pass = (len, stride, start, s) => {
      const s2 = s * s;
      for (let q = 0; q < len; q++) g[q] = f[start + q * stride];
      let k = 0; v[0] = 0; z[0] = -INF; z[1] = INF;
      for (let q = 1; q < len; q++) {
        let sx;
        while (true) {
          const p = v[k];
          sx = ((g[q] + q * q * s2) - (g[p] + p * p * s2)) / (2 * s2 * (q - p));
          if (sx <= z[k] && k > 0) k--; else break;
        }
        k++; v[k] = q; z[k] = sx; z[k + 1] = INF;
      }
      k = 0;
      for (let q = 0; q < len; q++) { while (z[k + 1] < q) k++; const p = v[k]; d[q] = (q - p) * (q - p) * s2 + g[p]; }
      for (let q = 0; q < len; q++) f[start + q * stride] = d[q];
    };
    for (let i = 0; i < nx; i++) for (let j = 0; j < ny; j++) pass(nz, 1, (i * ny + j) * nz, sp[2]);
    for (let i = 0; i < nx; i++) for (let k = 0; k < nz; k++) pass(ny, nz, i * ny * nz + k, sp[1]);
    for (let j = 0; j < ny; j++) for (let k = 0; k < nz; k++) pass(nx, ny * nz, j * nz + k, sp[0]);
    return f;
  }

  function label(mask, n, fullConn) {       // nº de componentes; fullConn = 26-conexo, si no 6-conexo
    const [nx, ny, nz] = n, seen = new Uint8Array(mask.length), stack = new Int32Array(mask.length);
    let count = 0, touchesBorder = [];
    const nb = [];
    for (let a = -1; a <= 1; a++) for (let b = -1; b <= 1; b++) for (let c = -1; c <= 1; c++) {
      if (!a && !b && !c) continue;
      if (!fullConn && Math.abs(a) + Math.abs(b) + Math.abs(c) !== 1) continue;
      nb.push([a, b, c]);
    }
    for (let s = 0; s < mask.length; s++) {
      if (!mask[s] || seen[s]) continue;
      count++; let top = 0, border = false; stack[top++] = s; seen[s] = 1;
      while (top) {
        const p = stack[--top], k = p % nz, j = ((p - k) / nz) % ny, i = (p - k - j * nz) / (ny * nz);
        if (i === 0 || j === 0 || k === 0 || i === nx - 1 || j === ny - 1 || k === nz - 1) border = true;
        for (const [a, b, c] of nb) {
          const ii = i + a, jj = j + b, kk = k + c;
          if (ii < 0 || jj < 0 || kk < 0 || ii >= nx || jj >= ny || kk >= nz) continue;
          const q = (ii * ny + jj) * nz + kk;
          if (mask[q] && !seen[q]) { seen[q] = 1; stack[top++] = q; }
        }
      }
      touchesBorder.push(border);
    }
    return { count, touchesBorder };
  }

  // Números de Betti con el par de adyacencias (26, 6), como en topology.py.
  function betti(mask, n) {
    const [nx, ny, nz] = n;
    let any = false; for (let i = 0; i < mask.length && !any; i++) any = mask[i] === 1;
    if (!any) return [0, 0, 0];
    const b0 = label(mask, n, true).count;
    const bg = new Uint8Array(mask.length); for (let i = 0; i < mask.length; i++) bg[i] = mask[i] ? 0 : 1;
    const lb = label(bg, n, false);
    const b2 = lb.touchesBorder.filter(t => !t).length;   // la rejilla tiene margen: el exterior toca el borde
    // Característica de Euler del complejo cúbico (unión de vóxeles cerrados): V - E + F - C.
    const at = (i, j, k) => (i < 0 || j < 0 || k < 0 || i >= nx || j >= ny || k >= nz) ? 0 : mask[(i * ny + j) * nz + k];
    let V = 0, E = 0, F = 0, C = 0;
    for (let i = 0; i <= nx; i++) for (let j = 0; j <= ny; j++) for (let k = 0; k <= nz; k++) {
      const c = at(i, j, k);
      if (c) C++;
      if (c || at(i - 1, j, k)) F++;                       // cara perpendicular a x
      if (c || at(i, j - 1, k)) F++;
      if (c || at(i, j, k - 1)) F++;
      if (c || at(i, j - 1, k) || at(i, j, k - 1) || at(i, j - 1, k - 1)) E++;   // arista a lo largo de x
      if (c || at(i - 1, j, k) || at(i, j, k - 1) || at(i - 1, j, k - 1)) E++;
      if (c || at(i - 1, j, k) || at(i, j - 1, k) || at(i - 1, j - 1, k)) E++;
      if (c || at(i - 1, j, k) || at(i, j - 1, k) || at(i, j, k - 1) || at(i - 1, j - 1, k) || at(i - 1, j, k - 1) || at(i, j - 1, k - 1) || at(i - 1, j - 1, k - 1)) V++;
    }
    const chi = V - E + F - C;
    return [b0, b0 + b2 - chi, b2];
  }

  function measure(mask, n, sp, profile = "ideal", skipBetti = false) {
    let count = 0; for (let i = 0; i < mask.length; i++) count += mask[i];
    const voxel = sp[0] * sp[1] * sp[2], hGeo = Math.cbrt(voxel), hMin = Math.min(sp[0], sp[1], sp[2]);
    const out = { nVoxels: count, volume: count * voxel, betti: skipBetti ? null : betti(mask, n), dMean: 0, feature: NaN, p: 0, light: "rojo" };
    if (!count) return out;
    const d2 = edtSquared(mask, n, sp);
    let acc = 0; for (let i = 0; i < mask.length; i++) if (mask[i]) acc += Math.sqrt(d2[i]) - 0.5 * hMin;
    out.dMean = acc / count; out.feature = out.dMean / hGeo;
    if (out.feature > 0) { const m = H6["global|" + profile]; out.p = 1 / (1 + Math.exp(-(m.a + m.b * Math.log(out.feature)))); }
    out.light = out.p >= GREEN ? "verde" : (out.p >= RED ? "amarillo" : "rojo");
    out.depth = d2;
    return out;
  }

  function blockMean(cov, n) {
    const [nx, ny, nz] = n, mx = nx >> 1, my = ny >> 1, mz = nz >> 1, out = new Float32Array(mx * my * mz);
    for (let i = 0; i < mx; i++) for (let j = 0; j < my; j++) for (let k = 0; k < mz; k++) {
      let s = 0;
      for (let a = 0; a < 2; a++) for (let b = 0; b < 2; b++) for (let c = 0; c < 2; c++) s += cov[((2 * i + a) * ny + 2 * j + b) * nz + 2 * k + c];
      out[(i * my + j) * mz + k] = s / 8;
    }
    return { cov: out, n: [mx, my, mz] };
  }

  function fitRate(stages, volumes, keep) {     // pendiente de ln V frente a la etapa; NaN con < 3 etapas
    const xs = [], ys = [];
    for (let i = 0; i < stages.length; i++) if (keep[i] && volumes[i] > 0) { xs.push(stages[i]); ys.push(Math.log(volumes[i])); }
    if (xs.length < 3) return NaN;
    const mx = xs.reduce((a, b) => a + b) / xs.length, my = ys.reduce((a, b) => a + b) / ys.length;
    let sxy = 0, sxx = 0; for (let i = 0; i < xs.length; i++) { sxy += (xs[i] - mx) * (ys[i] - my); sxx += (xs[i] - mx) ** 2; }
    return sxy / sxx;
  }

  return { SHAPES, H6, GREEN, RED, render, threshold, measure, betti, edtSquared, blockMean, fitRate, mulberry32 };
})();
if (typeof module !== "undefined") module.exports = GV;
