"""Procedencia de una corrida: commit y si el CÓDIGO tenía cambios sin commitear.

Un cambio en ``docs/`` o un archivo de resultados nuevo no altera lo que se
ejecutó, así que no marcan la corrida como «sucia» (error de v0.1: el criterio
incluía ``docs``). Solo cuentan los archivos versionados de código.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

CODE_PATHS = ("src", "scripts", "pyproject.toml")


def _run(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)


def git_state(repo: str | Path = ".", code_paths: tuple[str, ...] = CODE_PATHS) -> dict:
    repo = Path(repo)
    head = _run(repo, "rev-parse", "HEAD")
    if head.returncode != 0:
        return {"commit": "unknown", "dirty_code": None}
    existing = [p for p in code_paths if (repo / p).exists()]
    status = _run(repo, "status", "--porcelain", "--untracked-files=no", "--", *existing)
    return {"commit": head.stdout.strip(), "dirty_code": bool(status.stdout.strip())}
