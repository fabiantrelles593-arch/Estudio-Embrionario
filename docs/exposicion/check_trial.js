// Comprobación de la prueba en vivo de la exposición, sin navegador:
//   node docs/exposicion/check_trial.js
// Exige que, con el mismo diseño que usa el navegador (9 formas, t en {1.5..8}, vóxel x1/x2/x3),
// las luces verdes fallen menos del 10 % (criterio de H6d) y que haya luces verdes suficientes.
// Referencia: en Python, «global · ideal» dio 2.3 % de verdes falsos en 3 771 luces verdes.
// Esta comprobación existe porque el laboratorio usaba n_sub = 2 por encima de 6 vóxeles y daba
// ~17 % (ERRATA E21): ninguna prueba lo habría visto sin comparar la tasa con Python.
const T = require("./trial.js");
const N = Number(process.argv[2] || 1000), seed = Number(process.argv[3] || 5);
const rows = T.design(seed, N).map(T.runOne), s = T.summary(rows);
console.log(`n=${N} semilla=${seed}: ${s.verde.n} verdes, verde falso ${(100 * s.falseGreen).toFixed(1)} %`);
if (s.verde.n < 100) { console.error("FALLO: muy pocas luces verdes para juzgar"); process.exit(1); }
if (s.falseGreen > 0.10) { console.error("FALLO: más de 10 % de luces verdes falsas"); process.exit(1); }
console.log("OK");
