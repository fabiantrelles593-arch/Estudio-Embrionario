"""Procedencia de una corrida: commit y si el CÓDIGO tenía cambios sin commitear.

Un cambio en ``docs/`` o un archivo de resultados nuevo no altera lo que se
ejecutó, así que no marcan la corrida como «sucia» (error de v0.1: el criterio
incluía ``docs``). Solo cuentan los archivos versionados de código.

Sin git (copia descargada, sin ``.git``), el commit es desconocido. Para que la
corrida no quede sin respaldo, se guarda además la **huella del código**: el
identificador de blob de git (SHA-1 de ``"blob <n>\\0" + contenido``, con finales de
línea normalizados a LF, como se guardan en la rama) de cada archivo de código.
Esas huellas se pueden comparar después con el árbol de cualquier commit publicado
(``compare_fingerprint``). Ocurrió en H11 (`docs/h11/RESULTADOS_H11.md` §1).
"""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

CODE_PATHS = ("src", "scripts", "pyproject.toml")
CODE_SUFFIXES = (".py", ".json", ".toml")
FINGERPRINT_ALGORITHM = "git-blob-sha1, finales de línea LF"


def _run(repo: Path, *args: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    except FileNotFoundError:  # git no está instalado: procedencia desconocida, no un fallo
        return subprocess.CompletedProcess(["git", *args], 127, "", "git no encontrado")


def git_blob_sha(data: bytes) -> str:
    """Identificador de blob de git del contenido, con CRLF normalizado a LF."""
    data = data.replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def code_fingerprint(repo: str | Path = ".", code_paths: tuple[str, ...] = CODE_PATHS) -> dict:
    """Huella de cada archivo de código bajo ``code_paths`` (rutas relativas con ``/``) y un resumen.

    Se ignoran ``__pycache__`` y los archivos que no son de código (``CODE_SUFFIXES``). ``digest`` es el
    SHA-256 de las líneas «ruta huella» ordenadas: cambia si cambia, se añade o se quita cualquier archivo.
    """
    repo = Path(repo)
    files: dict[str, str] = {}
    for p in code_paths:
        base = repo / p
        cands = [base] if base.is_file() else sorted(base.rglob("*")) if base.is_dir() else []
        for f in cands:
            if f.is_file() and f.suffix in CODE_SUFFIXES and "__pycache__" not in f.parts:
                files[f.relative_to(repo).as_posix()] = git_blob_sha(f.read_bytes())
    lines = "".join(f"{k} {v}\n" for k, v in sorted(files.items()))
    return {"algorithm": FINGERPRINT_ALGORITHM, "n_files": len(files), "files": files,
            "digest": hashlib.sha256(lines.encode("utf-8")).hexdigest()}


def compare_fingerprint(fingerprint: dict, tree: dict[str, str]) -> dict:
    """Compara una huella con el árbol de un commit (``{ruta: sha del blob}``, p. ej. de la API de GitHub).

    Devuelve las rutas que coinciden, las que difieren y las que faltan en el árbol. Las rutas del árbol que
    no están en la huella no cuentan: la huella solo cubre el código.
    """
    files = fingerprint["files"]
    return {"match": sorted(p for p, s in files.items() if tree.get(p) == s),
            "differ": sorted(p for p, s in files.items() if p in tree and tree[p] != s),
            "missing": sorted(p for p in files if p not in tree)}


def git_state(repo: str | Path = ".", code_paths: tuple[str, ...] = CODE_PATHS) -> dict:
    repo = Path(repo)
    head = _run(repo, "rev-parse", "HEAD")
    if head.returncode != 0:
        return {"commit": "unknown", "dirty_code": None, "code_fingerprint": code_fingerprint(repo, code_paths)}
    existing = [p for p in code_paths if (repo / p).exists()]
    status = _run(repo, "status", "--porcelain", "--untracked-files=no", "--", *existing)
    return {"commit": head.stdout.strip(), "dirty_code": bool(status.stdout.strip())}
