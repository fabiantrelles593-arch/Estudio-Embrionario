// Prueba en vivo: objetos al azar, semáforo SIN mirar la verdad, comparación al final.
// Núcleo sin DOM: se puede ejecutar en Node para comprobarlo.
const GVTrial = (() => {
  const G = (typeof GV !== "undefined") ? GV : require("./core.js");
  let NSUB = 3; const TS = [1.5, 2, 3, 4, 6, 8], ANISO = [1, 2, 3], TOL = 0.05;
  function design(seed, n, shapes) {
    const rng = G.mulberry32(seed >>> 0), keys = shapes || Object.keys(G.SHAPES), out = [];
    for (let i = 0; i < n; i++) {
      out.push({ shape: keys[Math.floor(rng() * keys.length)], t: TS[Math.floor(rng() * TS.length)],
        aniso: ANISO[Math.floor(rng() * ANISO.length)], seed: Math.floor(rng() * 1e9) + 1 });
    }
    return out;
  }
  function runOne(s) {
    const r = G.render(s.shape, s.t, s.aniso, s.seed, NSUB);
    const m = G.measure(G.threshold(r.cov), r.n, r.sp, "ideal", true);   // el semáforo solo ve la máscara y el vóxel
    const err = m.volume / r.trueVolume - 1;
    return { ...s, light: m.light, p: m.p, err, ok: Math.abs(err) <= TOL };
  }
  function summary(rows) {
    const o = { n: rows.length };
    for (const L of ["verde", "amarillo", "rojo"]) {
      const g = rows.filter(r => r.light === L), ok = g.filter(r => r.ok).length;
      o[L] = { n: g.length, ok, pctOk: g.length ? ok / g.length : NaN };
    }
    o.falseGreen = o.verde.n ? 1 - o.verde.pctOk : NaN;
    return o;
  }
  return { design, runOne, summary, TS, ANISO, TOL };
})();
if (typeof module !== "undefined") module.exports = GVTrial;
