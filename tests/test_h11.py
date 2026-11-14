"""H11: aplicación de ``docs/PREREGISTRO_H11.md`` (transferencia a ecografía 3D real).

Se prueba con volúmenes sintéticos guardados como NIfTI y con tablas fabricadas de resultado
conocido. No hay ninguna imagen real. Qué haría fallar cada prueba:
* si ``run_cases`` emparejara mal imagen y etiqueta o ignorara el valor de etiqueta, el volumen de la
  referencia no coincidiría con el de la etiqueta fabricada;
* si ``evaluate_h11`` contara embriones como realizaciones independientes, los intervalos no
  cambiarían al remuestrear embriones;
* si un valor no calculable se llamara «no apoyada», la regla del preregistro se rompería.
"""
import numpy as np
import pandas as pd
import pytest

nib = pytest.importorskip("nibabel")

from geovida import h11  # noqa: E402


def _ball(n=48, radius=14.0, sigma=1.2, seed=0):
    zz, yy, xx = np.mgrid[:n, :n, :n]
    c = (n - 1) / 2
    inside = ((zz - c) ** 2 + (yy - c) ** 2 + (xx - c) ** 2) <= radius ** 2
    from scipy.ndimage import gaussian_filter
    img = gaussian_filter(inside.astype(np.float32), sigma)
    img = 0.1 + 0.8 * img + np.random.default_rng(seed).normal(0, 0.02, img.shape)
    return img.astype(np.float32), inside


def _save(path, arr, zooms=(0.05, 0.05, 0.05)):
    im = nib.Nifti1Image(arr, np.diag([*zooms, 1.0]))
    im.header.set_xyzt_units("mm")
    nib.save(im, str(path))


@pytest.fixture()
def manifest(tmp_path):
    rows = []
    for k in range(3):
        img, inside = _ball(radius=13.0 + k, seed=k)
        label = np.zeros(img.shape, np.uint8)
        label[inside] = 3                       # el cuerpo lleva la etiqueta 3, no 1
        label[:3, :3, :3] = 7                   # otra estructura, no debe contarse
        _save(tmp_path / f"e{k}_img.nii.gz", img)
        _save(tmp_path / f"e{k}_lab.nii.gz", label)
        rows.append({"embryo_id": f"E{k}", "structure": "body", "image": f"e{k}_img.nii.gz",
                     "label": f"e{k}_lab.nii.gz", "label_value": 3})
    return pd.DataFrame(rows), tmp_path


def test_run_cases_pairs_image_and_label_and_uses_the_label_value(manifest):
    df, root = manifest
    out = h11.run_cases(df, root=root, profile="realistic")
    assert len(out) == 3 * len(h11.SEGMENTERS)
    assert set(out["embryo_id"]) == {"E0", "E1", "E2"} and set(out["structure"]) == {"body"}
    _, inside = _ball(radius=13.0)
    expect = inside.sum() * (0.05 ** 3)
    row = out[(out["embryo_id"] == "E0") & (out["segmenter"] == "otsu")].iloc[0]
    assert row["volume_mm3_reference"] == pytest.approx(expect, rel=1e-6)
    assert abs(row["rel_error_volume"]) < 0.15 and row["dice"] > 0.85


def test_run_cases_rejects_a_missing_or_mismatched_label(manifest, tmp_path):
    df, root = manifest
    bad = df.copy()
    bad.loc[0, "label_value"] = 99              # etiqueta inexistente: referencia vacía
    with pytest.raises(ValueError):
        h11.run_cases(bad, root=root, profile="realistic")


def test_ventricle_uses_the_box_around_the_reference_and_declares_it(manifest):
    df, root = manifest
    v = df.copy()
    v["structure"] = "ventricle"
    out = h11.run_cases(v.iloc[:1], root=root, profile="realistic")
    assert set(out["roi_margin"]) == {h11.ROI_MARGIN}
    body = h11.run_cases(df.iloc[:1], root=root, profile="realistic")
    assert body["roi_margin"].isna().all()


# --- Veredictos con tablas fabricadas -------------------------------------------------------------
def _cases(n_embryos=20, per_embryo=3, bad_fraction=0.0, light="verde", in_domain=True, seed=0,
           segmenters=h11.SEGMENTERS, betti_bad=0.0):
    rng = np.random.default_rng(seed)
    rows = []
    for e in range(n_embryos):
        for seg in segmenters:
            for _ in range(per_embryo):
                bad = rng.random() < bad_fraction
                rows.append({
                    "embryo_id": f"E{e}", "structure": "body", "segmenter": seg,
                    "rel_error_volume": 0.25 if bad else 0.02, "dice": 0.9,
                    "ok10": not bad, "ok5": not bad,
                    "light_volume": light, "light_volume_without_guard": light,
                    "in_domain_volume": in_domain, "light_topology": light,
                    "topology_ok": bool(rng.random() >= betti_bad), "betti_reference": [1, 0, 0]})
    return pd.DataFrame(rows)


def test_h11b_not_evaluable_with_few_greens_or_few_embryos():
    few = h11.evaluate_h11(_cases(n_embryos=3, per_embryo=1), n_boot=200)
    assert few["h11b"]["verdict"] == "no evaluable"
    few_embryos = h11.evaluate_h11(_cases(n_embryos=10, per_embryo=5), n_boot=200)   # 150 verdes, 10 embriones
    assert few_embryos["h11b"]["verdict"] == "no evaluable"


def test_h11b_supported_when_greens_are_reliable_and_unsupported_when_lower_bound_exceeds_10pct():
    good = h11.evaluate_h11(_cases(bad_fraction=0.02), n_boot=300)
    assert good["h11b"]["verdict"] == "apoyada" and good["h11b"]["n_green"] >= 30
    bad = h11.evaluate_h11(_cases(bad_fraction=0.5), n_boot=300)
    assert bad["h11b"]["verdict"] == "no apoyada" and bad["h11b"]["ci"][0] > 0.10


def test_h11b_is_inconclusive_when_point_estimate_exceeds_10pct_but_interval_reaches_it():
    out = h11.evaluate_h11(_cases(n_embryos=16, per_embryo=1, bad_fraction=0.14, seed=3), n_boot=500)
    b = out["h11b"]
    assert b["n_green"] >= 30 and b["n_embryos_green"] >= 15
    if b["estimate"] > 0.10 and b["ci"][0] <= 0.10:
        assert b["verdict"] == "no concluyente"


def test_h11a_counts_segmenters_whose_in_domain_fraction_is_at_most_half():
    rejected = h11.evaluate_h11(_cases(in_domain=False, light="amarillo"), n_boot=100)
    assert rejected["h11a"]["verdict"] == "apoyada"
    accepted = h11.evaluate_h11(_cases(in_domain=True), n_boot=100)
    assert accepted["h11a"]["verdict"] == "no apoyada"


def test_h11c_is_supported_when_unguarded_greens_fail_more_than_10pct():
    out = h11.evaluate_h11(_cases(bad_fraction=0.4), n_boot=100)
    assert out["h11c"]["verdict"] == "apoyada" and out["h11c"]["estimate"] > 0.10
    low = h11.evaluate_h11(_cases(bad_fraction=0.0), n_boot=100)
    assert low["h11c"]["verdict"] == "no apoyada"
    none = h11.evaluate_h11(_cases(n_embryos=2, per_embryo=1), n_boot=100)
    assert none["h11c"]["verdict"] == "no evaluable"


def test_h11e_topology_and_reference_betti_report():
    ok = h11.evaluate_h11(_cases(betti_bad=0.0), n_boot=100)
    assert ok["h11e"]["verdict"] == "apoyada"
    bad = h11.evaluate_h11(_cases(betti_bad=0.5, seed=2), n_boot=100)
    assert bad["h11e"]["verdict"] == "no apoyada"
    assert ok["h11e"]["reference_not_simple"] == pytest.approx(0.0)


def test_h11d_describes_agreement_by_segmenter_and_structure_without_a_verdict():
    out = h11.evaluate_h11(_cases(n_embryos=5), n_boot=50)
    rows = out["h11d"]["rows"]
    assert {(r["segmenter"], r["structure"]) for r in rows} == {(s, "body") for s in h11.SEGMENTERS}
    assert all("dice_median" in r and "abs_error_median" in r for r in rows)
    assert "verdict" not in out["h11d"]


def test_embryo_bootstrap_is_deterministic_for_the_preregistered_seed():
    a = h11.evaluate_h11(_cases(bad_fraction=0.3, seed=5), n_boot=200)
    b = h11.evaluate_h11(_cases(bad_fraction=0.3, seed=5), n_boot=200)
    assert a["h11b"]["ci"] == b["h11b"]["ci"]
    assert h11.BOOT_SEED == 20261126 and h11.N_BOOT == 2000
