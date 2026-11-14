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

import pandas as pd

from geovida import h11
from geovida.certificate import load_frozen
from geovida.provenance import git_state


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    warnings.filterwarnings("ignore")
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--root", default=".")
    ap.add_argument("--frozen", default=None, help="modelos congelados de H12 (por defecto: los de v0.4)")
    ap.add_argument("--profile", default="realistic")
    ap.add_argument("--tag", default="v04", help="sufijo de los archivos de salida (p. ej. v04 o h12)")
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
    df = h11.run_cases(manifest, root=a.root, profile=a.profile, frozen=frozen)
    verdicts = h11.evaluate_h11(df)

    out = Path("results/summary")
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / f"h11_{a.tag}_cases.csv", index=False)
    meta = {"generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "git_commit": state["commit"],
            "code_dirty": state["dirty_code"], "manifest": man_path.name, "manifest_sha256": _sha256(man_path),
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
