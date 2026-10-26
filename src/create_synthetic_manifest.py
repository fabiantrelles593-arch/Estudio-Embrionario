"""Crea un manifiesto de pruebas desde las máscaras sintéticas del demo."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo"
INPUT = DEMO / "synthetic_morphology.csv"
OUTPUT = DEMO / "synthetic_manifest.csv"


def main() -> None:
    if not INPUT.is_file():
        raise FileNotFoundError(
            f"No existe {INPUT}; ejecuta primero: python src/demo_pipeline.py"
        )
    source = pd.read_csv(INPUT)
    rows = []
    for item in source.to_dict(orient="records"):
        image_id = str(item["image_id"])
        rows.append({
            "observation_id": item["observation_id"],
            "specimen_id": item["specimen_id"],
            "image_id": image_id,
            "stage": "not_applicable",
            "modality": "SYNTHETIC",
            "view": "synthetic_2D",
            "section_id": "not_applicable",
            "source": "internally_generated_demo",
            "asset_identifier": image_id,
            "license_status": "not_applicable",
            "pixel_size": "",
            "pixel_size_unit": "",
            "segmentation_method": "known_synthetic_mask_thresholded_from_png",
            "segmentation_operator": "automated_demo",
            "quality_flag": "PASS",
            "notes": "Synthetic software-validation fixture; not biological evidence.",
            "image_path": f"{image_id}.png",
        })
    pd.DataFrame(rows).to_csv(OUTPUT, index=False)
    print(f"Manifiesto sintético generado: {OUTPUT}")
    print(f"Observaciones: {len(rows)}; no son datos embrionarios.")


if __name__ == "__main__":
    main()
