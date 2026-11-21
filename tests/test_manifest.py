"""Pruebas del manifiesto de datos externos (ADR-005). Usan archivos inventados en una carpeta
temporal; no hay datos de terceros en el repositorio."""
import hashlib

import pytest

from geovida import manifest

META = {"source": "FaceBase", "record": "3-JZA6", "license": "CC BY 4.0", "downloaded": "2026-11-20"}


def _tree(root):
    (root / "e155").mkdir(parents=True)
    (root / "e155" / "a.mnc").write_bytes(b"volumen A")
    (root / "e155" / "b.mnc.gz").write_bytes(b"volumen B comprimido")
    (root / "e155" / "a_landmarks.tag").write_bytes(b"puntos")
    (root / "notas.txt").write_text("no es un dato", encoding="utf-8")
    return root


def test_build_uses_relative_paths_and_real_hashes(tmp_path):
    root = _tree(tmp_path / "datos")
    rows = manifest.build_manifest(root, **META)
    assert [r["file"] for r in rows] == ["e155/a.mnc", "e155/a_landmarks.tag", "e155/b.mnc.gz"]
    a = rows[0]
    assert a["sha256"] == hashlib.sha256(b"volumen A").hexdigest()
    assert a["bytes"] == len(b"volumen A")
    assert a["license"] == "CC BY 4.0" and a["record"] == "3-JZA6"
    assert all(str(tmp_path) not in r["file"] for r in rows)


@pytest.mark.parametrize("bad", [{"license": ""}, {"license": "   "}, {"downloaded": "20/11/2026"}])
def test_build_refuses_missing_license_or_bad_date(tmp_path, bad):
    root = _tree(tmp_path / "datos")
    with pytest.raises(ValueError):
        manifest.build_manifest(root, **{**META, **bad})


def test_build_refuses_folder_without_data(tmp_path):
    (tmp_path / "vacia").mkdir()
    with pytest.raises(ValueError):
        manifest.build_manifest(tmp_path / "vacia", **META)
    with pytest.raises(ValueError):
        manifest.build_manifest(tmp_path / "no_existe", **META)


def test_roundtrip_and_verify_detects_changes(tmp_path):
    root = _tree(tmp_path / "datos")
    path = manifest.write_manifest(manifest.build_manifest(root, **META), tmp_path / "m" / "man.csv")
    assert manifest.read_manifest(path)[0]["bytes"] == len(b"volumen A")
    assert {r["status"] for r in manifest.verify_manifest(path, root)} == {"ok"}
    (root / "e155" / "a.mnc").write_bytes(b"volumen A modificado")
    (root / "e155" / "b.mnc.gz").unlink()
    (root / "e155" / "c.mnc").write_bytes(b"nuevo")
    status = {r["file"]: r["status"] for r in manifest.verify_manifest(path, root)}
    assert status == {"e155/a.mnc": "changed", "e155/a_landmarks.tag": "ok",
                      "e155/b.mnc.gz": "missing", "e155/c.mnc": "extra"}


def test_same_size_different_content_is_changed(tmp_path):
    root = _tree(tmp_path / "datos")
    path = manifest.write_manifest(manifest.build_manifest(root, **META), tmp_path / "man.csv")
    (root / "e155" / "a.mnc").write_bytes(b"volumen Z")
    status = {r["file"]: r["status"] for r in manifest.verify_manifest(path, root)}
    assert status["e155/a.mnc"] == "changed"


@pytest.mark.parametrize("rel", ["../fuera.mnc", "/abs/a.mnc", "e155\\a.mnc"])
def test_read_rejects_unsafe_paths(tmp_path, rel):
    p = tmp_path / "man.csv"
    p.write_text(",".join(manifest.FIELDS) + f"\n{rel},1,00,FaceBase,3-JZA6,CC BY 4.0,2026-11-20\n",
                 encoding="utf-8")
    with pytest.raises(ValueError):
        manifest.read_manifest(p)


def test_read_rejects_wrong_header(tmp_path):
    p = tmp_path / "man.csv"
    p.write_text("file,sha256\na.mnc,00\n", encoding="utf-8")
    with pytest.raises(ValueError):
        manifest.read_manifest(p)


def test_command_line_build_and_verify(tmp_path, capsys):
    root = _tree(tmp_path / "datos")
    out = tmp_path / "man.csv"
    assert manifest.main(["build", str(root), "--source", "FaceBase", "--record", "3-JZA6",
                          "--license", "CC BY 4.0", "--downloaded", "2026-11-20",
                          "--out", str(out)]) == 0
    assert "3 archivos" in capsys.readouterr().out
    assert manifest.main(["verify", str(out), str(root)]) == 0
    (root / "e155" / "a.mnc").write_bytes(b"otro")
    assert manifest.main(["verify", str(out), str(root)]) == 1
    assert "changed: e155/a.mnc" in capsys.readouterr().out
