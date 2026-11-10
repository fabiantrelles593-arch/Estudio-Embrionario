(() => {
  const $ = id => document.getElementById(id);
  const css = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const NSUB = 3;   // el mismo supermuestreo que Python (con 2 el volumen sale sesgado a partir de ~7 vóxeles)
  const state = { shape: "torus_tight", t: 2, aniso: 1, seed: 2, scale: 0, panels: "measure" };
  const LIGHT_TEXT = { verde: "Verde: se puede fiar del volumen", amarillo: "Amarillo: dudoso", rojo: "Rojo: no fiarse del volumen" };
  const LIGHT_VAR = { verde: "--go", amarillo: "--wait", rojo: "--stop" };
  const pct = v => (v >= 0 ? "+" : "−") + Math.abs(100 * v).toFixed(1) + " %";
  const bettiText = b => `(${b[0]}, ${b[1]}, ${b[2]})`;
  const fmtPct = (x, d = 0) => (100 * x).toFixed(d).replace(".", ",") + " %";

  // ================= resultados (tabla de la lámina 12) =================
  const H9 = window.GEOVIDA_H9 || null;   // se rellena cuando termina la confirmación
  const SCORE = [
    ["H1 · v0.1", "¿Basta contar vóxeles a través del rasgo más fino para predecir el error?", "refutada en parte", "mid", "La topología sí depende del rasgo más estrecho. El volumen no: una bola necesita unos 8 vóxeles y una cáscara unos 2."],
    ["H2 · v0.1", "¿Cuánto distorsiona una trayectoria 4D el error al asignar la etapa?", "medido", "ok", "Sesgo de hasta 4,3 %. Corregirlo cuesta más varianza de la que quita."],
    ["H3 · v0.2", "¿Predice mejor el cociente volumen/área que el grosor?", "apoyada", "ok", "Confirmado con formas y semillas nuevas. Usa volumen y área verdaderos: aún no sirve en imágenes reales."],
    ["H4 · v0.2", "¿Mejora el área un estimador por distancia con signo?", "apoyada", "ok", "A 4 vóxeles el sesgo baja de entre −17 y −34 % a entre −3 y −11 %. No sirve por debajo de 3 vóxeles."],
    ["H5 · v0.2", "¿Aguanta el instrumento una imagen tipo ecografía, con moteado?", "3 de 5", "mid", "El área es fiable desde 4 píxeles. La topología de un anillo no se recupera sin limpiar."],
    ["H6 · v0.3", "¿Puede saber, sin conocer la verdad, si su volumen es fiable?", "5 de 5", "ok", "El semáforo de volumen. En verde se equivoca entre 0,4 y 2,6 % de las veces (50 400 imágenes)."],
    ["H7 · v0.3", "¿Arregla la topología 2D una limpieza que escala con el objeto?", "1 de 3", "bad", "Ayuda, pero cierra el margen solo en 8 de 18 casos. Con imagen ideal borra huecos reales pequeños."],
    ["H8 · v0.3", "¿Mejora la tasa de crecimiento 4D si se descartan las etapas en rojo?", "3 de 3", "ok", "El error mediano baja de entre 3 y 64 % a entre 1 y 2 %. Con el segmentador suavizado, 70–89 % de las series se quedan sin tasa."],
    ["H9 · v0.4", "¿Puede saber si la topología medida es correcta?", H9 ? H9.h9 : "en confirmación", H9 ? H9.h9cls : "mid", H9 ? H9.h9txt : "Modelo ya congelado antes de la confirmación. Resultado pendiente: se publica tal como salga."],
    ["H10 · v0.4", "¿Se da cuenta de que una imagen está fuera de su calibración?", H9 ? H9.h10 : "en confirmación", H9 ? H9.h10cls : "mid", H9 ? H9.h10txt : "En el piloto, el semáforo de volumen dio hasta 97 % de verdes falsos con el doble de ruido. La guardia de dominio se está confirmando."],
  ];
  $("scoreRows").innerHTML = SCORE.map(r => `<tr><td class="num">${r[0]}</td><td>${r[1]}</td><td><span class="chip ${r[3]}">${r[2]}</span></td><td>${r[4]}</td></tr>`).join("");

  // ================= laboratorio (una sola instancia que cambia de lámina) =================
  const sel = $("shape");
  for (const [key, s] of Object.entries(GV.SHAPES)) { const o = document.createElement("option"); o.value = key; o.textContent = s.label; sel.appendChild(o); }
  const segs = ["aniso", "scale"];
  function syncUI() {
    sel.value = state.shape; $("res").value = state.t; $("resOut").textContent = Number(state.t).toFixed(1);
    for (const id of segs) for (const b of $(id).children) b.setAttribute("aria-pressed", Number(b.dataset.v) === state[id] ? "true" : "false");
  }
  for (const [id, key] of [["aniso", "aniso"], ["scale", "scale"]]) $(id).addEventListener("click", e => {
    const b = e.target.closest("button"); if (!b) return; state[key] = Number(b.dataset.v); syncUI(); schedule();
  });
  sel.addEventListener("change", () => { state.shape = sel.value; schedule(); });
  $("res").addEventListener("input", () => { state.t = Number($("res").value); syncUI(); schedule(); });
  $("reroll").addEventListener("click", () => { state.seed = (state.seed * 7 + 13) % 100003; schedule(); });

  let T = null;
  function initThree() {
    if (!window.THREE) { document.querySelector(".stage .hint").textContent = "La vista 3D no pudo cargarse; las medidas siguen funcionando."; return; }
    const canvas = $("view"), renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    const scene = new THREE.Scene(), camera = new THREE.PerspectiveCamera(35, 4 / 3, 0.1, 5000), group = new THREE.Group();
    scene.add(group); scene.add(new THREE.AmbientLight(0xffffff, 0.62));
    const sun = new THREE.DirectionalLight(0xffffff, 0.75); sun.position.set(0.6, 1, 0.8); scene.add(sun);
    T = { renderer, scene, camera, group, mesh: null, dist: 60, rx: 0.5, ry: 0.6, auto: !matchMedia("(prefers-reduced-motion: reduce)").matches, raf: 0 };
    const size = () => { const r = canvas.parentElement.getBoundingClientRect(); if (!r.width) return; renderer.setSize(r.width, r.height, false); camera.aspect = r.width / Math.max(r.height, 1); camera.updateProjectionMatrix(); draw3d(); };
    new ResizeObserver(size).observe(canvas.parentElement); size();
    let drag = null;
    canvas.addEventListener("pointerdown", e => { drag = [e.clientX, e.clientY]; T.auto = false; canvas.setPointerCapture(e.pointerId); });
    canvas.addEventListener("pointermove", e => { if (!drag) return; T.ry += (e.clientX - drag[0]) * 0.01; T.rx = Math.max(-1.5, Math.min(1.5, T.rx + (e.clientY - drag[1]) * 0.01)); drag = [e.clientX, e.clientY]; draw3d(); });
    const end = () => { drag = null; }; canvas.addEventListener("pointerup", end); canvas.addEventListener("pointercancel", end);
    canvas.addEventListener("wheel", e => { e.preventDefault(); T.zoom = Math.max(0.4, Math.min(3, (T.zoom || 1) * Math.exp(e.deltaY * 0.001))); T.auto = false; draw3d(); }, { passive: false });
    const spin = () => { if (!T.auto) return; if (!$("labRoot").hidden) { T.ry += 0.004; draw3d(); } T.raf = requestAnimationFrame(spin); };
    if (T.auto) T.raf = requestAnimationFrame(spin);
  }
  function draw3d() {
    if (!T) return;
    T.group.rotation.set(T.rx, T.ry, 0);
    T.camera.position.set(0, 0, T.dist * (T.zoom || 1)); T.camera.lookAt(0, 0, 0);
    T.renderer.render(T.scene, T.camera);
  }
  function setMesh(mask, n, sp) {
    if (!T) return;
    if (T.mesh) { T.group.remove(T.mesh); T.mesh.geometry.dispose(); T.mesh.material.dispose(); T.mesh = null; }
    const [nx, ny, nz] = n, pos = [];
    const at = (i, j, k) => (i < 0 || j < 0 || k < 0 || i >= nx || j >= ny || k >= nz) ? 0 : mask[(i * ny + j) * nz + k];
    for (let i = 0; i < nx; i++) for (let j = 0; j < ny; j++) for (let k = 0; k < nz; k++) {
      if (!at(i, j, k)) continue;
      if (at(i - 1, j, k) && at(i + 1, j, k) && at(i, j - 1, k) && at(i, j + 1, k) && at(i, j, k - 1) && at(i, j, k + 1)) continue;
      pos.push((i - (nx - 1) / 2) * sp[0], (j - (ny - 1) / 2) * sp[1], (k - (nz - 1) / 2) * sp[2]);
    }
    const radius = 0.5 * Math.hypot(nx * sp[0], ny * sp[1], nz * sp[2]);
    T.dist = radius / Math.sin(35 * Math.PI / 360) * 0.56;
    T.camera.near = T.dist / 50; T.camera.far = T.dist * 8; T.camera.updateProjectionMatrix();
    if (pos.length) {
      const geo = new THREE.BoxGeometry(sp[0] * 0.9, sp[1] * 0.9, sp[2] * 0.9);
      const mat = new THREE.MeshLambertMaterial({ color: new THREE.Color(css("--voxel")) });
      const mesh = new THREE.InstancedMesh(geo, mat, pos.length / 3), m4 = new THREE.Matrix4();
      for (let q = 0; q < pos.length; q += 3) { m4.makeTranslation(pos[q], pos[q + 1], pos[q + 2]); mesh.setMatrixAt(q / 3, m4); }
      mesh.instanceMatrix.needsUpdate = true; T.mesh = mesh; T.group.add(mesh);
    }
    draw3d();
  }

  function levelsFrom(r) {
    const out = []; let cov = r.cov, n = r.n, sp = r.sp.slice();
    for (let k = 0; k <= 2; k++) {
      if (k > 0) { if (Math.min(...n) < 2) { out.push(null); continue; } const b = GV.blockMean(cov, n); cov = b.cov; n = b.n; sp = sp.map(s => s * 2); }
      const mask = GV.threshold(cov), m = GV.measure(mask, n, sp, "ideal");
      out.push({ mask, n, sp: sp.slice(), m });
    }
    return out;
  }
  function compute() {
    const r = GV.render(state.shape, state.t, state.aniso, state.seed, NSUB);
    const levels = levelsFrom(r), lv = levels[state.scale] || levels[0], m = lv.m;
    const err = m.volume / r.trueVolume - 1, okV = Math.abs(err) <= 0.05, okT = bettiText(m.betti) === bettiText(r.trueBetti);
    $("lamp").dataset.light = m.light; $("lightText").textContent = LIGHT_TEXT[m.light];
    $("lightSub").textContent = m.nVoxels ? `Probabilidad estimada de que el error de volumen sea ≤ 5 %: ${m.p.toFixed(2)}` : "La máscara está vacía: el objeto no se ve a esta resolución.";
    $("rVol").innerHTML = `${m.volume.toFixed(0)} / ${r.trueVolume.toFixed(0)} <span class="${okV ? "ok" : "bad"}">(${pct(err)})</span>`;
    $("rTop").innerHTML = `${bettiText(m.betti)} <span class="${okT ? "ok" : "bad"}">${okT ? "correcta" : "incorrecta"}</span>`;
    $("rTopTrue").textContent = bettiText(r.trueBetti);
    $("rVox").textContent = m.nVoxels.toLocaleString("es");
    $("scaleRows").innerHTML = levels.map((L, k) => {
      const name = ["original", "degradada ×2", "degradada ×4"][k];
      if (!L) return `<tr><td>${name}</td><td colspan="3">la rejilla ya no alcanza</td></tr>`;
      const e = L.m.volume / r.trueVolume - 1, same = bettiText(L.m.betti) === bettiText(levels[0].m.betti), okTopo = bettiText(L.m.betti) === bettiText(r.trueBetti);
      return `<tr><td>${name}</td><td class="num"><span class="${Math.abs(e) <= 0.05 ? "ok" : "bad"}">${pct(e)}</span></td><td class="num"><span class="${okTopo ? "ok" : "bad"}">${bettiText(L.m.betti)}</span></td><td>${k === 0 ? "—" : `<span class="${same ? "ok" : "bad"}">${same ? "sí" : "no: cambia"}</span>`}</td></tr>`;
    }).join("");
    setMesh(lv.mask, lv.n, lv.sp);
  }

  // ---- serie de crecimiento (4D) ----
  let growthToken = 0, growth = [];
  const SIZES = Array.from({ length: 8 }, (_, k) => 2 * 1.35 ** k);
  function startGrowth() {
    const token = ++growthToken; growth = [];
    const step = k => {
      if (token !== growthToken) return;
      if (k === SIZES.length) { finishGrowth(); return; }
      const r = GV.render(state.shape, SIZES[k], state.aniso, state.seed * 31 + k + 1, NSUB);
      const m = GV.measure(GV.threshold(r.cov), r.n, r.sp, "ideal", true);
      growth.push({ v: m.volume, vt: r.trueVolume, light: m.light });
      drawGrowth(); setTimeout(() => step(k + 1), 0);
    };
    $("rateAll").textContent = "…"; $("rateNoRed").textContent = "…";
    setTimeout(() => step(0), 30);
  }
  function rates() {
    const st = growth.map((_, i) => i), vol = growth.map(g => g.v);
    return { all: GV.fitRate(st, vol, growth.map(() => true)), noRed: GV.fitRate(st, vol, growth.map(g => g.light !== "rojo")) };
  }
  function finishGrowth() {
    const r = rates(), TRUE = 3 * Math.log(1.35), show = (id, sub, v, base) => {
      if (Number.isFinite(v)) { $(id).textContent = v.toFixed(3); $(sub).textContent = `${base} · error ${(100 * Math.abs(v / TRUE - 1)).toFixed(1)} %`; }
      else { $(id).textContent = "sin tasa"; $(sub).textContent = `${base}: quedan menos de 3 etapas`; }
    };
    show("rateAll", "rateAllSub", r.all, "con todas las etapas"); show("rateNoRed", "rateNoRedSub", r.noRed, "sin las etapas en rojo");
    drawGrowth(true);
  }
  function drawGrowth(done) {
    const c = $("growth"), dpr = Math.min(window.devicePixelRatio || 1, 2), w = c.clientWidth, h = c.clientHeight;
    if (!w) return;
    c.width = w * dpr; c.height = h * dpr;
    const g = c.getContext("2d"); g.scale(dpr, dpr); g.clearRect(0, 0, w, h);
    const L = 46, R = 14, Tp = 12, B = 40, X = k => L + (w - L - R) * k / 7;
    const ys = []; SIZES.forEach((s, k) => { ys.push(Math.log(GV.SHAPES[state.shape].vol * s ** 3)); if (growth[k] && growth[k].v > 0) ys.push(Math.log(growth[k].v)); });
    const lo = Math.min(...ys) - 0.4, hi = Math.max(...ys) + 0.4, Y = v => Tp + (h - Tp - B) * (1 - (v - lo) / (hi - lo));
    g.font = "11px " + (css("--mono") || "monospace"); g.fillStyle = css("--muted"); g.strokeStyle = css("--line"); g.lineWidth = 1;
    for (let v = Math.ceil(lo); v <= hi; v += Math.max(1, Math.round((hi - lo) / 6))) { g.beginPath(); g.moveTo(L, Y(v)); g.lineTo(w - R, Y(v)); g.stroke(); g.textAlign = "right"; g.fillText(v.toFixed(0), L - 6, Y(v) + 4); }
    g.textAlign = "center"; SIZES.forEach((s, k) => g.fillText(s.toFixed(1), X(k), h - B + 16));
    g.fillText("grosor del objeto en cada etapa (vóxeles)", L + (w - L - R) / 2, h - 6);
    g.save(); g.translate(12, Tp + (h - Tp - B) / 2); g.rotate(-Math.PI / 2); g.fillText("ln V", 0, 0); g.restore();
    const line = (f, color, dash) => { g.beginPath(); g.setLineDash(dash || []); g.strokeStyle = color; g.lineWidth = 2; g.moveTo(X(0), Y(f(0))); g.lineTo(X(7), Y(f(7))); g.stroke(); g.setLineDash([]); };
    const v0 = Math.log(GV.SHAPES[state.shape].vol * 8), TRUE = 3 * Math.log(1.35);
    line(k => v0 + TRUE * k, css("--muted"), [5, 4]);
    if (done) {
      const fit = keep => {
        const xs = [], yv = []; growth.forEach((p, i) => { if (keep(p) && p.v > 0) { xs.push(i); yv.push(Math.log(p.v)); } });
        if (xs.length < 3) return null;
        const mx = xs.reduce((a, b) => a + b) / xs.length, my = yv.reduce((a, b) => a + b) / yv.length;
        let sxy = 0, sxx = 0; xs.forEach((x, i) => { sxy += (x - mx) * (yv[i] - my); sxx += (x - mx) ** 2; });
        const b = sxy / sxx; return k => my + b * (k - mx);
      };
      const fa = fit(() => true), fn = fit(p => p.light !== "rojo");
      if (fa) line(fa, css("--stop")); if (fn) line(fn, css("--accent"));
    }
    growth.forEach((p, k) => {
      const y = p.v > 0 ? Y(Math.log(p.v)) : h - B - 4;
      g.beginPath(); g.arc(X(k), y, 5.5, 0, 2 * Math.PI); g.fillStyle = css(LIGHT_VAR[p.light]); g.fill();
      g.lineWidth = 1.5; g.strokeStyle = css("--surface"); g.stroke();
      if (!(p.v > 0)) { g.fillStyle = css("--muted"); g.fillText("no se ve", X(k), y - 10); }
    });
  }

  let timer = 0;
  function schedule() {
    clearTimeout(timer); $("busy").hidden = false;
    timer = setTimeout(() => { compute(); $("busy").hidden = true; if (state.panels === "growth") startGrowth(); else growthToken++; }, 40);
  }

  // ---- colocar el laboratorio en una lámina ----
  const ALL_CTL = ["shape", "res", "aniso", "scale"], CTL_ID = { shape: "ctlShape", res: "fRes", aniso: "fAniso", scale: "fScale" };
  function applyDemo(cfg) {
    Object.assign(state, { shape: cfg.shape, t: cfg.t, aniso: cfg.aniso || 1, scale: cfg.scale || 0, seed: cfg.seed || 11, panels: cfg.panels || "measure" });
    const ctl = cfg.controls === true ? ALL_CTL : (cfg.controls || []);
    for (const k of ALL_CTL) $(CTL_ID[k]).hidden = !ctl.includes(k);
    $("rowAS").hidden = !(ctl.includes("aniso") || ctl.includes("scale"));
    $("labGrid").classList.toggle("nostage", state.panels === "growth");
    $("readList").hidden = state.panels === "scale";
    $("pMeasure").hidden = state.panels === "growth";
    $("pScale").hidden = state.panels !== "scale";
    $("pGrowth").hidden = state.panels !== "growth";
    const pr = $("presets"); pr.innerHTML = "";
    for (const [label, patch] of (cfg.presets || [])) {
      const b = document.createElement("button"); b.type = "button"; b.className = "btn"; b.textContent = label;
      b.addEventListener("click", () => { Object.assign(state, patch); syncUI(); schedule(); });
      pr.appendChild(b);
    }
    pr.hidden = !(cfg.presets || []).length;
    syncUI(); schedule();
  }

  // ================= prueba en vivo =================
  let trialBusy = false;
  function runTrial() {
    if (trialBusy) return; trialBusy = true;
    const N = 200, seed = ((Date.now() ^ Math.floor(Math.random() * 2 ** 31)) >>> 0), design = GVTrial.design(seed, N), rows = [];
    $("runTrial").disabled = true; $("trialVerdict").hidden = true; $("failBox").hidden = true;
    $("trialStatus").textContent = "Creando y midiendo objetos…"; $("trialBar").style.width = "0%";
    let i = 0;
    const paint = () => {
      const s = GVTrial.summary(rows);
      $("tG").textContent = s.verde.n; $("tY").textContent = s.amarillo.n; $("tR").textContent = s.rojo.n;
      const sub = (o, big) => o.n ? `${o.ok} de ${o.n} correctas (${fmtPct(o.pctOk)})` : "ninguna";
      $("tGs").textContent = sub(s.verde); $("tYs").textContent = sub(s.amarillo); $("tRs").textContent = sub(s.rojo);
      return s;
    };
    const batch = () => {
      const t0 = performance.now();
      while (i < N && performance.now() - t0 < 40) rows.push(GVTrial.runOne(design[i++]));
      $("trialBar").style.width = (100 * i / N) + "%"; $("trialStatus").textContent = `${i} de ${N} objetos medidos`;
      paint();
      if (i < N) { setTimeout(batch, 0); return; }
      const s = paint(), fails = rows.filter(r => r.light === "verde" && !r.ok), fg = s.falseGreen;
      const v = $("trialVerdict"); v.hidden = false;
      const ok = Number.isFinite(fg) && fg <= 0.10;
      v.className = "callout " + (ok ? "good" : "bad");
      v.innerHTML = Number.isFinite(fg)
        ? `<b>${s.verde.n} luces verdes, ${fails.length} falsas (${fmtPct(fg, 1)}).</b> ${ok ? "Dentro del criterio fijado de antemano (menos de 10 %)." : "Fuera del criterio fijado de antemano (menos de 10 %)."} Con tan pocas luces verdes el porcentaje cambia de una corrida a otra. Semilla de esta corrida: ${seed}.`
        : "No hubo luces verdes en esta corrida.";
      if (fails.length) {
        $("failBox").hidden = false; $("failSum").textContent = `Las ${fails.length} luces verdes que fallaron`;
        const L = GV.SHAPES; $("failList").textContent = fails.map(r => `${L[r.shape].label}, ${r.t} vóxeles, vóxel ×${r.aniso}: error ${pct(r.err)}`).join(" · ");
      }
      $("trialStatus").textContent = `Terminado: ${N} objetos.`; $("runTrial").disabled = false; $("runTrial").textContent = "Ejecutar otra vez"; trialBusy = false;
    };
    setTimeout(batch, 20);
  }
  $("runTrial").addEventListener("click", runTrial);

  // ================= cuestionario =================
  const QUIZ = [
    ["¿Qué es un vóxel?", ["Un píxel en 3D: el cubito mínimo de una imagen tridimensional", "El volumen real de un embrión", "Un programa que separa objeto y fondo", "Una unidad de tiempo en las series 4D"], 0, "Una imagen 3D está hecha de vóxeles, como una foto 2D lo está de píxeles. Si son grandes frente al objeto, la medida se degrada."],
    ["¿Por qué se prueba con objetos matemáticos y no con embriones reales?", ["Porque son más bonitos de dibujar", "Porque su volumen y su topología se conocen exactamente, y así se puede medir el error", "Porque los embriones reales están prohibidos", "Porque así el programa siempre acierta"], 1, "Para medir un error hay que conocer la respuesta correcta. En un embrión real no se conoce; en una bola o un anillo, sí."],
    ["Si el semáforo da luz verde para el volumen, ¿qué significa?", ["Que el error es cero", "Que el embrión es sano", "Que, según su calibración, la probabilidad de un error de volumen de 5 % o menos es al menos 0,90", "Que la imagen tiene mucho contraste"], 2, "Es una probabilidad estimada, no una garantía. Y solo vale para imágenes parecidas a las de su calibración."],
    ["¿Qué es un preregistro?", ["Un permiso ético para usar imágenes", "Un resumen que se escribe al final del proyecto", "Escribir criterios y predicciones antes de ejecutar el experimento", "Un registro de las pruebas que salieron bien"], 2, "Fijar de antemano qué contará como éxito evita acomodar el criterio al resultado. Por eso este proyecto publica también lo que salió mal."],
    ["En este proyecto, ¿qué significa «4D»?", ["Cuatro cámaras a la vez", "Las tres dimensiones del espacio más etapas de crecimiento (pseudo-tiempo)", "Cuatro canales de color", "Un embrión seguido en el tiempo con total precisión"], 1, "Cada etapa es un espécimen distinto medido una vez, no el mismo seguido en el tiempo: por eso es pseudo-tiempo."],
    ["¿Se puede usar este programa para diagnosticar un embrión?", ["Sí, con luz verde el diagnóstico es seguro", "Sí, pero solo en el segundo trimestre", "No: es solo para investigación y educación, y no tiene validación clínica", "Sí, si el embrión es de ratón"], 2, "Se probó solo con imágenes sintéticas. Un software con finalidad médica requiere validación clínica y regulación que este proyecto no tiene."],
  ];
  let quizRight = 0, quizDone = 0;
  $("quiz").innerHTML = QUIZ.map((q, i) => `<div class="q" data-i="${i}"><h3>${i + 1}. ${q[0]}</h3><div class="opts">${q[1].map((o, j) => `<button type="button" data-j="${j}">${o}</button>`).join("")}</div><p class="why" hidden></p></div>`).join("");
  $("quiz").addEventListener("click", e => {
    const b = e.target.closest(".opts button"); if (!b) return;
    const box = b.closest(".q"), i = Number(box.dataset.i), j = Number(b.dataset.j), q = QUIZ[i];
    if (box.dataset.done) return; box.dataset.done = "1"; quizDone++;
    [...box.querySelectorAll(".opts button")].forEach((x, k) => { x.disabled = true; if (k === q[2]) x.dataset.state = "right"; else if (k === j) x.dataset.state = "wrong"; });
    if (j === q[2]) quizRight++;
    const w = box.querySelector(".why"); w.hidden = false; w.textContent = (j === q[2] ? "Correcto. " : "No exactamente. ") + q[3];
    $("quizScore").textContent = quizDone === QUIZ.length ? `Resultado: ${quizRight} de ${QUIZ.length}.` : `${quizRight} de ${quizDone} correctas hasta ahora.`;
  });

  // ================= mazo =================
  const slides = [...document.querySelectorAll(".slide")];
  let idx = 0, notesOn = false;
  function go(i, fromHash) {
    idx = Math.max(0, Math.min(slides.length - 1, i));
    slides.forEach((s, k) => s.classList.toggle("on", k === idx));
    const s = slides[idx], demo = s.dataset.demo;
    if (demo) { s.querySelector(".demo-slot").appendChild($("labRoot")); $("labRoot").hidden = false; applyDemo(JSON.parse(demo)); }
    else { $("labRoot").hidden = true; growthToken++; }
    $("where").textContent = `${idx + 1} / ${slides.length}`; $("navTitle").textContent = s.dataset.title || "";
    $("progress").style.width = (100 * (idx + 1) / slides.length) + "%";
    $("notesText").textContent = s.dataset.notes || "";
    $("prev").disabled = idx === 0; $("next").disabled = idx === slides.length - 1;
    $("slides").scrollTop = 0;
    document.title = `Exposición Geovida · ${s.dataset.title || idx + 1}`;
    if (!fromHash) { try { history.replaceState(null, "", "#" + (idx + 1)); } catch (e) { /* sin historial en un iframe aislado */ } }
  }
  function setNotes(on) { notesOn = on; $("notes").hidden = !on; $("toggleNotes").setAttribute("aria-pressed", on ? "true" : "false"); window.dispatchEvent(new Event("resize")); }
  $("prev").addEventListener("click", () => go(idx - 1)); $("next").addEventListener("click", () => go(idx + 1));
  $("toggleNotes").addEventListener("click", () => setNotes(!notesOn));
  document.addEventListener("keydown", e => {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    const tag = (e.target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "select" || tag === "textarea") return;
    if (e.key === "ArrowRight" || e.key === "PageDown") { e.preventDefault(); go(idx + 1); }
    else if (e.key === "ArrowLeft" || e.key === "PageUp") { e.preventDefault(); go(idx - 1); }
    else if (e.key === "Home") { go(0); } else if (e.key === "End") { go(slides.length - 1); }
    else if (e.key === "g" || e.key === "G") { setNotes(!notesOn); }
    else if (e.key === " " && tag === "body") { e.preventDefault(); go(idx + (e.shiftKey ? -1 : 1)); }
  });
  let sx = null;
  $("slides").addEventListener("touchstart", e => { sx = (e.target.closest("canvas, input, select, .scroll")) ? null : [e.touches[0].clientX, e.touches[0].clientY]; }, { passive: true });
  $("slides").addEventListener("touchend", e => { if (!sx) return; const dx = e.changedTouches[0].clientX - sx[0], dy = e.changedTouches[0].clientY - sx[1]; sx = null; if (Math.abs(dx) > 70 && Math.abs(dy) < 45) go(idx + (dx < 0 ? 1 : -1)); }, { passive: true });

  const retheme = () => { if (T && T.mesh) { T.mesh.material.color.set(css("--voxel")); draw3d(); } drawGrowth(growth.length === 8); };
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", retheme);
  new MutationObserver(retheme).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  window.addEventListener("resize", () => drawGrowth(growth.length === 8));
  initThree();
  const fromHash = parseInt((location.hash || "").slice(1), 10);
  go(Number.isFinite(fromHash) ? fromHash - 1 : 0, true);
})();
