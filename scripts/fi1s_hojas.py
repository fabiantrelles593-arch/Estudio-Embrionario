"""FI-1s: genera las 6 hojas sintéticas para imprimir y el archivo de valores diseñados (semilla 20261125).

    python scripts/fi1s_hojas.py            # data/fi1s/hojas_fi1s.pdf (6 páginas A4) y data/fi1s/valores_disenados.json

Imprimir el PDF al 100 %, sin «ajustar a página». **Quien marca no abre ``valores_disenados.json``** hasta terminar las
3 sesiones. ``data/fi1s/`` no se sube a git.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from geovida import fi1s

OUT = Path("data/fi1s")


def generate(out: Path = OUT, seed: int = fi1s.SEED) -> dict:
    from matplotlib.backends.backend_pdf import PdfPages
    import matplotlib.pyplot as plt

    out.mkdir(parents=True, exist_ok=True)
    design = fi1s.design_all(seed)
    rng = np.random.default_rng(seed + 1)                     # moteado, aparte de la geometría
    pdf_path = out / "hojas_fi1s.pdf"
    with PdfPages(pdf_path, metadata={"Title": "FI-1s hojas sinteticas", "CreationDate": None}) as pdf:
        for code, sheet in design["sheets"].items():
            fig = fi1s.render_sheet(code, sheet, rng)
            pdf.savefig(fig)
            plt.close(fig)
    design["pdf_sha256"] = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    (out / "valores_disenados.json").write_text(json.dumps(design, indent=1) + "\n", encoding="utf-8")
    return design


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    d = generate(Path(a.out))
    print(f"{len(d['sheets'])} hojas en {Path(a.out) / 'hojas_fi1s.pdf'} (SHA-256 {d['pdf_sha256'][:12]}…). "
          "No abras valores_disenados.json si vas a marcar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
