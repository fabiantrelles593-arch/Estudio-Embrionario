(() => {
  const $ = id => document.getElementById(id);
  const css = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const state = { shape: "torus", t: 4, aniso: 1, seed: 11, scale: 0 };
  const LIGHT_TEXT = { verde: "Verde: se puede fiar del volumen", amarillo: "Amarillo: dudoso", rojo: "Rojo: no fiarse del volumen" };
  const LIGHT_VAR = { verde: "--go", amarillo: "--wait", rojo: "--stop" };
  const SCORE = [
    ["H1 · v0.1", "¿Basta contar vóxeles a través del rasgo más fino para predecir el error?", "refutada en parte", "mid", "La topología sí depende del rasgo más estrecho. El volumen no: una bola necesita unos 8 vóxeles y una cáscara unos 2."],
    ["H2 · v0.1", "¿Cuánto distorsiona una trayectoria 4D el error al asignar la etapa?", "medido", "ok", "Sesgo de hasta 4.3 %. Corregirlo cuesta más varianza de la que quita. Con 3 especímenes por etapa el intervalo cubre un 70 %, no un 95 %."],
    ["H3 · v0.2", "¿Predice mejor el cociente volumen/área que el grosor?", "apoyada", "ok", "Confirmado con formas y semillas nuevas. Usa el volumen y el área verdaderos: no sirve aún en imágenes reales."],
    ["H4 · v0.2", "¿Mejora el área un estimador por distancia con signo?", "apoyada", "ok", "A 4 vóxeles el sesgo baja de entre −17 y −34 % a entre −3 y −11 %. No sirve por debajo de 3 vóxeles."],
    ["H5 · v0.2", "¿Aguanta el instrumento una imagen tipo ecografía, con moteado?", "3 de 5", "mid", "El área es fiable desde 4 píxeles. La topología de un anillo no se recupera ni con 20 píxeles sin limpiar."],
    ["H6 · v0.3", "¿Puede el instrumento saber, sin conocer la verdad, si su volumen es fiable?", "5 de 5", "ok", "Semáforo por profundidad media. En verde se equivoca entre 0.4 y 2.6 % de las veces. Es el que usa esta página."],
    ["H7 · v0.3", "¿Arregla la topología 2D una limpieza que escala con el objeto?", "1 de 3", "bad", "Ayuda (hasta +82 puntos) pero cierra el margen solo en 8 de 18 casos. Con imagen ideal borra huecos reales pequeños."],
    ["H8 · v0.3", "¿Mejora la tasa de crecimiento si se descartan las etapas en rojo?", "3 de 3", "ok", "El error mediano baja de entre 3 y 64 % a entre 1 y 2 %. Con el segmentador suavizado, 70–89 % de las series se quedan sin tasa."],
    ["H9 · v0.4", "¿Puede saber si la topología medida es correcta?", "en curso", "mid", "Semáforo topológico por margen de persistencia. Preregistrado; la confirmación está corriendo."],
    ["H10 · v0.4", "¿Se da cuenta de que una imagen está fuera de su calibración?", "en curso", "mid", "En el piloto, el semáforo de H6 dio hasta 97 % de luces verdes falsas con el doble de ruido. La guardia de dominio se está probando."],
  ];

  // ---------- controles ----------
  const sel = $("shape");
  for (const [key, s] of Object.entries(GV.SHAPES)) { const o = document.createElement("option"); o.value = key; o.textContent = s.label; sel.appendChild(o); }
  sel.value = state.shape;
  $("scoreRows").innerHTML = SCORE.map(r => `<tr><td class="num">${r[0]}</td><td>${r[1]}</td><td><span class="chip ${r[3]}">${r[2]}</span></td><td>${r[4]}</td></tr>`).join("");
  const seg = (id, key, parse) => $(id).addEventListener("click", e => {
    const b = e.target.closest("button"); if (!b) return;
    for (const x of $(id).children) x.setAttribute("aria-pressed", x === b ? "true" : "false");
    state[key] = parse(b.dataset.v); schedule();
  });
  seg("aniso", "aniso", Number); seg("scale", "scale", Number);
  sel.addEventListener("change", () => { state.shape = sel.value; schedule(); });
  $("res").addEventListener("input", () => { state.t = Number($("res").value); $("resOut").textContent = state.t.toFixed(1); schedule(); });
  $("reroll").addEventListener("click", () => { state.seed = (state.seed * 7 + 13) % 100003; schedule(); });

  // ---------- vista 3D ----------
  let T = null;
  function initThree() {
    if (!window.THREE) { const h = document.querySelector(".stage .hint"); h.textContent = "La vista 3D no pudo cargarse; las medidas de la derecha siguen funcionando."; return; }
    const canvas = $("view"), renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    const scene = new THREE.Scene(), camera = new THREE.PerspectiveCamera(35, 4 / 3, 0.1, 5000), group = new THREE.Group();
    scene.add(group); scene.add(new THREE.AmbientLight(0xffffff, 0.62));
    const sun = new THREE.DirectionalLight(0xffffff, 0.75); sun.position.set(0.6, 1, 0.8); scene.add(sun);
    T = { renderer, scene, camera, group, mesh: null, dist: 60, rx: 0.5, ry: 0.6, auto: !matchMedia("(prefers-reduced-motion: reduce)").matches, raf: 0 };
    const size = () => { const r = canvas.parentElement.getBoundingClientRect(); renderer.setSize(r.width, r.height, false); camera.aspect = r.width / Math.max(r.height, 1); camera.updateProjectionMatrix(); draw3d(); };
    new ResizeObserver(size).observe(canvas.parentElement); size();
    let drag = null;
    canvas.addEventListener("pointerdown", e => { drag = [e.clientX, e.clientY]; T.auto = false; canvas.setPointerCapture(e.pointerId); });
    canvas.addEventListener("pointermove", e => { if (!drag) return; T.ry += (e.clientX - drag[0]) * 0.01; T.rx = Math.max(-1.5, Math.min(1.5, T.rx + (e.clientY - drag[1]) * 0.01)); drag = [e.clientX, e.clientY]; draw3d(); });
    const end = () => { drag = null; }; canvas.addEventListener("pointerup", end); canvas.addEventListener("pointercancel", end);
    canvas.addEventListener("wheel", e => { e.preventDefault(); T.zoom = Math.max(0.4, Math.min(3, (T.zoom || 1) * Math.exp(e.deltaY * 0.001))); T.auto = false; draw3d(); }, { passive: false });
    const spin = () => { if (T.auto) { T.ry += 0.004; draw3d(); T.raf = requestAnimationFrame(spin); } };
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
      if (at(i - 1, j, k) && at(i + 1, j, k) && at(i, j - 1, k) && at(i, j + 1, k) && at(i, j, k - 1) && at(i, j, k + 1)) continue;  // interior: no se ve
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

  // ---------- medida ----------
  const pct = v => (v >= 0 ? "+" : "−") + Math.abs(100 * v).toFixed(1) + " %";
  const bettiText = b => `(${b[0]}, ${b[1]}, ${b[2]})`;
  let current = null;
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
    const r = GV.render(state.shape, state.t, state.aniso, state.seed, state.t <= 6 ? 3 : 2);
    const levels = levelsFrom(r), lv = levels[state.scale] || levels[0], m = lv.m;
    current = { r, levels };
    const err = m.volume / r.trueVolume - 1, okV = Math.abs(err) <= 0.05;
    const okT = bettiText(m.betti) === bettiText(r.trueBetti);
    $("lamp").dataset.light = m.light; $("lightText").textContent = LIGHT_TEXT[m.light];
    $("lightSub").textContent = m.nVoxels ? `Probabilidad estimada de que el error de volumen sea ≤ 5 %: ${m.p.toFixed(2)}` : "La máscara está vacía: el objeto no se ve a esta resolución.";
    $("rVol").innerHTML = `${m.volume.toFixed(0)} / ${r.trueVolume.toFixed(0)} <span class="${okV ? "ok" : "bad"}">(${pct(err)})</span>`;
    $("rTop").innerHTML = `${bettiText(m.betti)} <span class="${okT ? "ok" : "bad"}">${okT ? "correcta" : "incorrecta"}</span>`;
    $("rTopTrue").textContent = bettiText(r.trueBetti);
    $("rDepth").textContent = m.nVoxels ? m.feature.toFixed(2) : "—";
    $("rVox").textContent = m.nVoxels.toLocaleString("es");
    $("scaleRows").innerHTML = levels.map((L, k) => {
      const name = ["nativa", "×2", "×4"][k];
      if (!L) return `<tr><td>${name}</td><td colspan="4">la rejilla ya no alcanza</td></tr>`;
      const e = L.m.volume / r.trueVolume - 1, same = bettiText(L.m.betti) === bettiText(levels[0].m.betti);
      return `<tr><td>${name}</td><td class="num">${L.sp.map(s => s.toFixed(0)).join(" × ")}</td><td class="num"><span class="${Math.abs(e) <= 0.05 ? "ok" : "bad"}">${pct(e)}</span></td><td class="num">${bettiText(L.m.betti)}</td><td>${k === 0 ? "—" : `<span class="${same ? "ok" : "bad"}">${same ? "sí" : "no"}</span>`}</td></tr>`;
    }).join("");
    setMesh(lv.mask, lv.n, lv.sp);
  }

  // ---------- serie de crecimiento ----------
  let growthToken = 0, growth = [];
  const SIZES = Array.from({ length: 8 }, (_, k) => 2 * 1.35 ** k);
  function startGrowth() {
    const token = ++growthToken; growth = [];
    const step = k => {
      if (token !== growthToken) return;
      if (k === SIZES.length) { finishGrowth(); return; }
      const r = GV.render(state.shape, SIZES[k], state.aniso, state.seed * 31 + k + 1, SIZES[k] <= 6 ? 3 : 2);
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
      const st = growth.map((_, i) => i), fit = keep => {
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

  // ---------- orquestación ----------
  let timer = 0;
  function schedule() {
    clearTimeout(timer); $("busy").hidden = false;
    timer = setTimeout(() => { compute(); $("busy").hidden = true; startGrowth(); }, 60);
  }
  const retheme = () => { if (T && T.mesh) { T.mesh.material.color.set(css("--voxel")); draw3d(); } drawGrowth(growth.length === 8); };
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", retheme);
  new MutationObserver(retheme).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  window.addEventListener("resize", () => drawGrowth(growth.length === 8));
  initThree(); schedule();
})();
