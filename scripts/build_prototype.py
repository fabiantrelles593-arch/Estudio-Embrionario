"""Ensambla el prototipo del navegador (prototype/src/*) en dos archivos.

* ``prototype/calibre_geovida.html``: fragmento para publicar como artefacto (sin doctype ni etiquetas html/head/body: la plataforma los añade).
* ``prototype/calibre_geovida.standalone.html``: archivo completo que se abre con doble clic, sin servidor y sin conexión
  (solo las tipografías se piden a Google Fonts; si no hay red usa las del sistema).

``python scripts/build_prototype.py`` escribe los dos; ``--check`` falla si alguno no coincide con las fuentes.
Solo investigación y educación.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "prototype" / "src"
OUT_FRAGMENT = ROOT / "prototype" / "calibre_geovida.html"
OUT_STANDALONE = ROOT / "prototype" / "calibre_geovida.standalone.html"

TITLE = "Calibre Geovida"
FONTS = ("https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&"
         "family=IBM+Plex+Sans:wght@400;500;600&display=swap")
STANDALONE_RESET = ("html{color-scheme:light}body{margin:0}[hidden]{display:none!important}img{max-width:100%}")


def _read(name: str) -> str:
    return (SRC / name).read_text(encoding="utf-8").strip("\n")


def build() -> dict[str, str]:
    css, body, core, ui = _read("style.css"), _read("body.html"), _read("core.js"), _read("ui.js")
    head = (f"<title>{TITLE}</title>\n"
            '<meta name="claude:viewport-fit-sides" content="cover">\n'
            f'<link rel="stylesheet" href="{FONTS}">\n'
            f"<style>\n{css}\n</style>")
    script = f"<script>\n{core}\n\n{ui}\n</script>"
    fragment = f"{head}\n{body}\n{script}\n"
    standalone = ("<!doctype html>\n<html lang=\"es\">\n<head>\n<meta charset=\"utf-8\">\n"
                  "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
                  f"<style>{STANDALONE_RESET}</style>\n{head}\n</head>\n<body>\n{body}\n{script}\n</body>\n</html>\n")
    return {str(OUT_FRAGMENT): fragment, str(OUT_STANDALONE): standalone}


def main(argv: list[str]) -> int:
    built = build()
    if "--check" in argv:
        stale = [p for p, text in built.items() if not Path(p).exists() or Path(p).read_text(encoding="utf-8") != text]
        if stale:
            print("desactualizados:", *stale, sep="\n  ")
            return 1
        print("al día")
        return 0
    for p, text in built.items():
        Path(p).write_text(text, encoding="utf-8")
        print(f"escrito {Path(p).relative_to(ROOT)} ({len(text) / 1024:.1f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
