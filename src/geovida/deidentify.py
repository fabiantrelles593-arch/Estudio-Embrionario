"""Anonimización local de imágenes (fotos o capturas de ecografía) antes de cualquier análisis.

Qué hace
--------
* ``load_pixels``: lee la imagen, aplica la orientación EXIF y se queda solo con los píxeles (RGB). Los metadatos
  (EXIF, GPS, comentarios, perfiles) no pasan al arreglo.
* ``redact``: rellena de negro las cajas que indique una persona, en píxeles o en fracciones de la imagen.
* ``save_clean``: guarda un PNG construido solo a partir de los píxeles, y ``check_clean`` comprueba al releerlo que no
  lleva metadatos.
* ``preview``: copia reducida con las cajas dibujadas en rojo, para que una persona revise que no queda texto visible.
* ``anonymize``: todo lo anterior, con un registro sin el nombre del archivo original.

Qué NO hace
-----------
No detecta texto por sí misma: **una persona define las cajas y revisa la vista previa**. No es una garantía de
anonimato; es una ayuda para cumplir `docs/DATOS_REALES_Y_ETICA.md` §3. Solo escribe en ``data/private/``, que git
ignora; nunca en el repositorio. No sube nada a ningún sitio.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

PRIVATE_DIR = Path("data") / "private"
ALLOWED_INFO_KEYS = {"dpi"}          # Pillow puede añadir dpi al releer un PNG; no identifica a nadie


def _pil():
    try:
        from PIL import Image, ImageOps
    except ImportError as exc:  # pragma: no cover
        raise ImportError("hace falta Pillow (lo instala scikit-image)") from exc
    return Image, ImageOps


def load_pixels(path) -> np.ndarray:
    """Píxeles RGB (alto, ancho, 3) uint8, con la orientación EXIF aplicada y sin ningún metadato."""
    Image, ImageOps = _pil()
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im)
        return np.array(im.convert("RGB"), dtype=np.uint8)


def to_pixel_box(box, shape) -> tuple[int, int, int, int]:
    """Caja (x0, y0, x1, y1). Si todos los valores están en [0, 1] se leen como fracciones del ancho y el alto."""
    h, w = int(shape[0]), int(shape[1])
    b = [float(v) for v in box]
    if len(b) != 4:
        raise ValueError(f"una caja tiene 4 valores (x0, y0, x1, y1): {box}")
    if all(0.0 <= v <= 1.0 for v in b):
        b = [b[0] * w, b[1] * h, b[2] * w, b[3] * h]
    x0, x1 = sorted((int(np.floor(b[0])), int(np.ceil(b[2]))))
    y0, y1 = sorted((int(np.floor(b[1])), int(np.ceil(b[3]))))
    x0, x1 = max(0, x0), min(w, x1)
    y0, y1 = max(0, y0), min(h, y1)
    if x1 <= x0 or y1 <= y0:
        raise ValueError(f"caja vacía o fuera de la imagen: {box}")
    return x0, y0, x1, y1


def redact(pixels: np.ndarray, boxes) -> np.ndarray:
    """Copia con cada caja rellena de negro."""
    out = np.array(pixels, dtype=np.uint8, copy=True)
    for box in boxes:
        x0, y0, x1, y1 = to_pixel_box(box, out.shape)
        out[y0:y1, x0:x1] = 0
    return out


def _require_private(path: Path) -> Path:
    p = Path(path).resolve()
    root = PRIVATE_DIR.resolve()
    if root != p and root not in p.parents:
        raise ValueError(f"solo se escribe dentro de {PRIVATE_DIR}/ (ignorado por git): {path}")
    return p


def save_clean(pixels: np.ndarray, path) -> str:
    """PNG nuevo hecho solo con los píxeles (sin EXIF ni bloques de texto). Devuelve su SHA-256."""
    Image, _ = _pil()
    p = _require_private(Path(path))
    p.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.asarray(pixels, dtype=np.uint8)).save(p, format="PNG", optimize=True)
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check_clean(path) -> dict:
    """Relee el archivo: sin EXIF y sin claves de información más allá de las permitidas."""
    Image, _ = _pil()
    with Image.open(path) as im:
        exif = dict(im.getexif())
        extra = sorted(k for k in im.info if k not in ALLOWED_INFO_KEYS)
    return {"exif_tags": len(exif), "info_keys": extra, "clean": not exif and not extra}


def preview(pixels: np.ndarray, boxes, path, max_side: int = 1200) -> None:
    """Copia reducida de la imagen ORIGINAL con las cajas en rojo, para revisar a mano qué queda tapado."""
    Image, _ = _pil()
    from PIL import ImageDraw
    p = _require_private(Path(path))
    im = Image.fromarray(np.asarray(pixels, dtype=np.uint8))
    draw = ImageDraw.Draw(im)
    for box in boxes:
        draw.rectangle(to_pixel_box(box, pixels.shape), outline=(255, 0, 0), width=max(2, im.width // 300))
    im.thumbnail((max_side, max_side))
    p.parent.mkdir(parents=True, exist_ok=True)
    im.save(p, format="PNG")


def anonymize(src, boxes, out_dir, code: str) -> dict:
    """Tapa las cajas, guarda ``<code>.png`` limpio en ``out_dir`` (dentro de data/private/) y devuelve el registro.

    El registro no incluye el nombre ni la ruta del archivo original: solo el código, las cajas y los SHA-256."""
    if not code or any(c in code for c in "/\\ "):
        raise ValueError("el código debe ser corto, sin espacios ni barras (p. ej., CI-001-IMG01)")
    out_dir = _require_private(Path(out_dir))
    px = load_pixels(src)
    clean = redact(px, boxes)
    sha = save_clean(clean, out_dir / f"{code}.png")
    chk = check_clean(out_dir / f"{code}.png")
    if not chk["clean"]:
        raise RuntimeError(f"el archivo de salida conserva metadatos: {chk}")
    rec = {"code": code, "shape": list(clean.shape), "boxes_px": [list(to_pixel_box(b, px.shape)) for b in boxes],
           "sha256_source": hashlib.sha256(Path(src).read_bytes()).hexdigest(), "sha256_output": sha,
           "check": chk, "human_review": "pendiente"}
    (out_dir / f"{code}.json").write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
    return rec
