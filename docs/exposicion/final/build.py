"""Construye ``docs/exposicion/geovida-presentacion-final.html`` (un solo archivo, funciona sin internet).

Sustituye en ``final/deck.html``:

* ``{{IMG:nombre}}``  -> PNG de ``docs/exposicion/img/nombre.png`` en base64;
* ``{{JSON:nombre}}`` -> contenido de ``docs/exposicion/img/nombre.json`` (mallas 3D reales);
* ``{{THREE}}``       -> three.js r128 (MIT), tomado del bloque incrustado en ``exposicion-geovida.html``.

Uso: ``python docs/exposicion/final/build.py``
"""
from __future__ import annotations

import base64
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPO = HERE.parent
IMG = EXPO / "img"
OUT = EXPO / "geovida-presentacion-final.html"


def _three() -> str:
    """Extrae three.js del laboratorio interactivo (ya incrustado allí, licencia MIT)."""
    html = (EXPO / "exposicion-geovida.html").read_text(encoding="utf-8")
    for block in re.findall(r"<script[^>]*>(.*?)</script>", html, flags=re.S):
        if "Three.js Authors" in block[:500] and "WebGLRenderer" in block:
            return block
    raise SystemExit("No se encontró three.js en exposicion-geovida.html")


def build() -> Path:
    src = (HERE / "deck.html").read_text(encoding="utf-8")

    def img(m: re.Match) -> str:
        data = (IMG / f"{m.group(1)}.png").read_bytes()
        return "data:image/png;base64," + base64.b64encode(data).decode("ascii")

    def js(m: re.Match) -> str:
        return (IMG / f"{m.group(1)}.json").read_text(encoding="utf-8")

    out = re.sub(r"\{\{IMG:([\w-]+)\}\}", img, src)
    out = re.sub(r"\{\{JSON:([\w-]+)\}\}", js, out)
    three = _three().replace("</script", "<\\/script")
    out = out.replace("{{THREE}}", three)
    missing = re.findall(r"\{\{[A-Z]+:?[\w-]*\}\}", out)
    if missing:
        raise SystemExit(f"Marcadores sin sustituir: {missing}")
    OUT.write_text(out, encoding="utf-8", newline="\n")
    return OUT


if __name__ == "__main__":
    p = build()
    print(f"{p} · {p.stat().st_size / 1e6:.2f} MB")
