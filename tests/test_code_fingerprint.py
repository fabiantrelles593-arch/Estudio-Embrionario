"""Huella del código cuando no hay git (``geovida.provenance``) y su uso en ``scripts/run_h11.py``.

Motivo: H11 quedó con ``git_commit: unknown`` y hubo que comprobar a mano, contra la rama, que el código era el
publicado (`docs/h11/RESULTADOS_H11.md` §1). Qué falla si la huella no coincide con la de git, si cuenta archivos
que no son código o si ``run_h11`` deja de guardarla.
"""
import hashlib
import importlib.util
import shutil
import subprocess
from pathlib import Path

import pytest

from geovida.provenance import code_fingerprint, compare_fingerprint, git_blob_sha, git_state

ROOT = Path(__file__).resolve().parents[1]


def _tree(tmp_path):
    (tmp_path / "src" / "pkg" / "__pycache__").mkdir(parents=True)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "src" / "pkg" / "a.py").write_bytes(b"x = 1\n")
    (tmp_path / "src" / "pkg" / "m.json").write_bytes(b'{"k": 1}\n')
    (tmp_path / "src" / "pkg" / "__pycache__" / "a.cpython-313.pyc").write_bytes(b"\x00\x01")
    (tmp_path / "src" / "pkg" / "notas.txt").write_bytes(b"no es codigo\n")
    (tmp_path / "scripts" / "run.py").write_bytes(b"print(1)\r\n")
    (tmp_path / "docs" / "d.md").write_bytes(b"doc\n")
    (tmp_path / "pyproject.toml").write_bytes(b"[project]\nname='t'\n")
    return tmp_path


def test_blob_sha_is_the_git_object_id():
    data = b"x = 1\n"
    assert git_blob_sha(data) == hashlib.sha1(b"blob 6\0x = 1\n").hexdigest()
    assert git_blob_sha(b"") == "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"  # blob vacío de git, valor conocido


def test_crlf_is_normalised_like_the_branch_stores_it():
    assert git_blob_sha(b"a\r\nb\r\n") == git_blob_sha(b"a\nb\n")


@pytest.mark.skipif(shutil.which("git") is None, reason="git no está instalado")
def test_matches_git_hash_object(tmp_path):
    f = tmp_path / "f.py"
    f.write_bytes(b"def g():\n    return 2\n")
    out = subprocess.run(["git", "hash-object", str(f)], capture_output=True, text=True, check=True)
    assert git_blob_sha(f.read_bytes()) == out.stdout.strip()


def test_fingerprint_covers_code_only(tmp_path):
    fp = code_fingerprint(_tree(tmp_path))
    assert sorted(fp["files"]) == ["pyproject.toml", "scripts/run.py", "src/pkg/a.py", "src/pkg/m.json"]
    assert fp["n_files"] == 4 and len(fp["digest"]) == 64
    assert fp["files"]["scripts/run.py"] == git_blob_sha(b"print(1)\n")


def test_digest_changes_when_code_changes_and_not_when_docs_change(tmp_path):
    repo = _tree(tmp_path)
    d0 = code_fingerprint(repo)["digest"]
    (repo / "docs" / "d.md").write_bytes(b"otra\n")
    (repo / "results.csv").write_bytes(b"a,b\n")
    assert code_fingerprint(repo)["digest"] == d0
    (repo / "src" / "pkg" / "a.py").write_bytes(b"x = 2\n")
    assert code_fingerprint(repo)["digest"] != d0


def test_compare_with_a_published_tree(tmp_path):
    fp = code_fingerprint(_tree(tmp_path))
    tree = dict(fp["files"])
    tree["src/pkg/a.py"] = "0" * 40           # difiere
    del tree["src/pkg/m.json"]                # falta en el árbol
    tree["docs/d.md"] = "f" * 40              # fuera de la huella: no cuenta
    r = compare_fingerprint(fp, tree)
    assert r["differ"] == ["src/pkg/a.py"] and r["missing"] == ["src/pkg/m.json"]
    assert r["match"] == ["pyproject.toml", "scripts/run.py"]


def test_outside_git_the_state_carries_the_fingerprint(tmp_path):
    s = git_state(_tree(tmp_path))
    assert s["commit"] == "unknown" and s["dirty_code"] is None
    assert s["code_fingerprint"]["n_files"] == 4


def _run_h11():
    spec = importlib.util.spec_from_file_location("run_h11", ROOT / "scripts" / "run_h11.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_run_h11_records_the_fingerprint_only_without_git():
    rh = _run_h11()
    fp = {"algorithm": "x", "n_files": 1, "files": {"a.py": "1" * 40}, "digest": "2" * 64}
    unknown = rh.code_provenance({"commit": "unknown", "dirty_code": None, "code_fingerprint": fp})
    assert unknown == {"git_commit": "unknown", "code_dirty": None, "code_fingerprint": fp}
    known = rh.code_provenance({"commit": "a" * 40, "dirty_code": False})
    assert known == {"git_commit": "a" * 40, "code_dirty": False}
