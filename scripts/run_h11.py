"""H11: aplica el certificado congelado a ecografía 3D real de embrión de ratón (docs/PREREGISTRO_H11.md).

Uso:
    python scripts/run_h11.py MANIFIESTO.csv --root CARPETA [--frozen h12_frozen.json] [--tag v04]

El manifiesto es un CSV con las columnas: embryo_id, structure (body|ventricle), image, label,
label_value (rutas relativas a --root). Se arma DESPUÉS de leer la ficha de `geovida datasheet` y de
anotar en «Desviaciones» del preregistro qué archivo es imagen y qué etiqueta es cada estructura.

No reajusta nada: usa los modelos congelados del paquete (v0.4) o los de --frozen (H12).
Escribe la tabla por caso, los veredictos y un manifiesto de procedencia en results/summary/.
"""
import argparse
import datetime as dt
import hashlib
import json
import platform
import warnings
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd

from geovida import h11
from geovida.certificate import load_frozen
from geovida.provenance import git_state


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def code_provenance(state: dict) -> dict:
    """Campos de procedencia del código para ``meta``: commit, si estaba sucio y, sin git, la huella del código.

    La huella se toma al empezar (``git_state()`` se llama antes de medir), así que describe el código que se
    ejecutó. Sin git, ``git_commit`` es ``unknown`` y la huella permite comprobarlo luego contra la rama
    (``geovida.provenance.compare_fingerprint``); es lo que en H11 hubo que hacer a mano.
    """
    out = {"git_commit": state["commit"], "code_dirty": state["dirty_code"]}
    if state.get("code_fingerprint") is not None:
        out["code_fingerprint"] = state["code_fingerprint"]
    return out


def _plain(v):
    """Valores de numpy a tipos de JSON (NaN se conserva: ``json`` de Python lo escribe y lo lee)."""
    if isinstance(v, np.generic):
        return v.item()
    if isinstance(v, np.ndarray):
        return v.tolist()
    return v


def _read_cache(cache: Path) -> tuple[str, list[dict]]:
    lines = cache.read_text(encoding="utf-8").splitlines()
    return json.loads(lines[0])["stamp"], [json.loads(x) for x in lines[1:] if x.strip()]


def _run_cached(manifest: pd.DataFrame, a, frozen, cache: Path) -> pd.DataFrame:
    """Igual que ``h11.run_cases`` sobre todo el manifiesto, pero caso a caso y guardando cada uno en ``cache``.

    ``cache`` es JSON por líneas (conserva tipos, listas y NaN). Es propia de una calibración y un perfil: la
    primera línea lo dice y se comprueba. Las filas se devuelven en el orden del manifiesto y solo las de sus
    casos (una caché con más casos sirve, p. ej. la del manifiesto de sensibilidad).
    """
    stamp = f"frozen={a.frozen or 'v04'} profile={a.profile}"
    if cache.exists():
        found, done = _read_cache(cache)
        if found != stamp:
            raise SystemExit(f"la caché {cache} es de otra calibración: {found!r} frente a {stamp!r}")
    else:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes((json.dumps({"stamp": stamp}) + "\n").encode("utf-8"))
        done = []
    have = {(r["image"], r["structure"]) for r in done}
    todo = manifest[[k not in have for k in zip(manifest["image"], manifest["structure"])]]
    for i, (_, case) in enumerate(todo.iterrows(), 1):
        rows = h11.run_cases(case.to_frame().T, root=a.root, profile=a.profile, frozen=frozen)
        with cache.open("ab") as f:
            for r in rows.to_dict("records"):
                rec = {"image": case["image"], **{k: _plain(v) for k, v in r.items()}}
                f.write((json.dumps(rec, ensure_ascii=False) + "\n").encode("utf-8"))
        print(f"[{i}/{len(todo)}] {case['structure']} {case['image']}", flush=True)
    _, done = _read_cache(cache)
    by_key: dict = {}
    for r in done:
        by_key.setdefault((r["image"], r["structure"]), []).append({k: v for k, v in r.items() if k != "image"})
    out = [r for k in zip(manifest["image"], manifest["structure"]) for r in by_key[k]]
    return pd.DataFrame(out)


def main():
    warnings.filterwarnings("ignore")
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--root", default=".")
    ap.add_argument("--frozen", default=None, help="modelos congelados de H12 (por defecto: los de v0.4)")
    ap.add_argument("--profile", default="realistic")
    ap.add_argument("--tag", default="v04", help="sufijo de los archivos de salida (p. ej. v04 o h12)")
    ap.add_argument("--cache", default=None,
                    help="JSONL donde se guarda cada caso al terminarlo; al relanzar, los ya hechos no se repiten")
    a = ap.parse_args()

    man_path = Path(a.manifest)
    manifest = pd.read_csv(man_path)
    if a.frozen:
        frozen_path = Path(a.frozen)
        frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
        calib = {"source": f"archivo: {frozen_path.name}", "sha256": _sha256(frozen_path)}
    else:
        frozen, calib = load_frozen(), {"source": "paquete: geovida/frozen/h9_frozen.json"}

    state = git_state()
    out = Path("results/summary")
    out.mkdir(parents=True, exist_ok=True)
    if a.cache:
        df = _run_cached(manifest, a, frozen, Path(a.cache))
    else:
        df = h11.run_cases(manifest, root=a.root, profile=a.profile, frozen=frozen)
    verdicts = h11.evaluate_h11(df)

    df.to_csv(out / f"h11_{a.tag}_cases.csv", index=False)
    meta = {"generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(), **code_provenance(state),
            "manifest": man_path.name, "manifest_sha256": _sha256(man_path),
            "calibration": calib, "profile": a.profile, "boot_seed": h11.BOOT_SEED, "n_boot": h11.N_BOOT,
            "roi_margin_ventricle": h11.ROI_MARGIN, "python": platform.python_version(),
            "packages": {p: version(p) for p in ("numpy", "scipy", "scikit-image", "pandas", "nibabel")}}
    (out / f"h11_{a.tag}_verdicts.json").write_text(
        json.dumps({"meta": meta, **verdicts}, indent=2, default=float), encoding="utf-8")
    for k in ("h11a", "h11b", "h11c", "h11e"):
        print(k, json.dumps(verdicts[k], default=float))
    print(f"{verdicts['n_cases']} filas, {verdicts['n_embryos']} embriones; salida en {out}/h11_{a.tag}_*")


if __name__ == "__main__":
    main()
