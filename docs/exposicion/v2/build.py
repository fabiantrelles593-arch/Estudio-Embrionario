"""Ensambla la presentación v2 en un único HTML autónomo (imágenes incrustadas, sin internet).

    python docs/exposicion/v2/build.py

Entrada: ``docs/exposicion/v2/deck.html`` con marcadores ``{{IMG:nombre}}`` y las figuras de
``docs/exposicion/img/`` (las genera ``scripts/figure_atlas.py``). Salida:
``docs/exposicion/geovida-presentacion.html``.
"""
import base64
import re
from pathlib import Path

here = Path(__file__).resolve().parent
src = (here / "deck.html").read_text(encoding="utf-8")
img = here.parent / "img"


def data_uri(m):
    p = img / f"{m.group(1)}.png"
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode("ascii")


out = re.sub(r"\{\{IMG:([a-z0-9_]+)\}\}", data_uri, src)
assert "{{IMG:" not in out
dst = here.parent / "geovida-presentacion.html"
dst.write_text(out, encoding="utf-8", newline="\n")
print(dst, len(out.encode("utf-8")), "bytes")
