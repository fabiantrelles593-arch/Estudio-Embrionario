const GV = require("./core.js"), fx = require("./fixtures.json");
let bad = 0;
for (const f of fx) {
  const mask = Uint8Array.from(f.mask), m = GV.measure(mask, f.n, f.sp, "ideal");
  const ok = Math.abs(m.volume - f.volume) < 1e-9 && JSON.stringify(m.betti) === JSON.stringify(f.betti)
    && Math.abs(m.dMean - f.d_mean) < 1e-6 && Math.abs(m.p - f.p) < 1e-9 && m.light === f.light;
  if (!ok) bad++;
  console.log(f.shape, ok ? "OK" : "DIFERENTE", "| V", m.volume, f.volume, "| Betti", m.betti, f.betti, "| d", m.dMean.toFixed(6), f.d_mean.toFixed(6), "| p", m.p.toFixed(6), f.p.toFixed(6), m.light);
}
// Fantomas JS frente a los volúmenes verdaderos de Python y render propio
for (const [name, t] of [["ball", 8], ["torus", 6], ["dumbbell", 4], ["cup", 6], ["shell", 4], ["capsule", 8], ["tube", 4], ["ellipsoid", 8], ["torus_tight", 8]]) {
  const r = GV.render(name, t, 1, 7), mask = GV.threshold(r.cov), m = GV.measure(mask, r.n, r.sp);
  let cv = 0; for (const c of r.cov) cv += c;
  console.log(name, "cobertura/verdad", (cv / r.trueVolume).toFixed(4), "V/verdad", (m.volume / r.trueVolume).toFixed(4), "Betti", m.betti, "verdad", r.trueBetti, "p", m.p.toFixed(3), m.light, "vóxeles", r.n);
}
const pyTrue = Object.fromEntries(fx.map(f => [f.shape, f.true_volume / f.t ** 3]));
for (const k in pyTrue) console.log("volumen unitario", k, GV.SHAPES[k].vol.toFixed(6), pyTrue[k].toFixed(6));
process.exit(bad ? 1 : 0);
