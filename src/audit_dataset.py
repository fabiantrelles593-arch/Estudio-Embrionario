from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import sys
import pandas as pd

REQUIRED = [
    'observation_id', 'specimen_id', 'image_id', 'stage', 'modality', 'view',
    'source', 'asset_identifier', 'license_status', 'segmentation_method',
    'quality_flag'
]
ALLOWED_LICENSE_STATUSES = {
    'verified', 'permission_obtained', 'public_domain', 'not_applicable'
}
ACCEPTED_QUALITY_FLAGS = {'pass', 'accepted'}

@dataclass
class AuditResult:
    ok: bool
    n_rows: int
    n_specimens: int
    duplicated_observation_ids: list[str]
    missing_required: dict[str, int]
    invalid_stages: list[str]
    multi_image_specimens: dict[str, int]
    quality_counts: dict[str, int]
    quality_not_pass: dict[str, int]
    license_pending: int
    notes: list[str]


def _blank(series: pd.Series) -> pd.Series:
    """True for NaN, null, or whitespace-only metadata values."""
    return series.isna() | series.astype('string').str.strip().eq('').fillna(True)


def audit_dataframe(df: pd.DataFrame) -> AuditResult:
    notes: list[str] = []
    missing: dict[str, int] = {}
    for col in REQUIRED:
        missing[col] = int(len(df)) if col not in df.columns else int(_blank(df[col]).sum())

    if len(df) == 0:
        notes.append('El dataset no contiene observaciones; una plantilla vacía no es evidencia de datos reales.')

    duplicated: list[str] = []
    if 'observation_id' in df.columns:
        valid_ids = df.loc[~_blank(df['observation_id']), 'observation_id'].astype(str)
        duplicated = sorted(valid_ids[valid_ids.duplicated(keep=False)].unique().tolist())
        if duplicated:
            notes.append('Hay observation_id duplicados.')

    invalid_stages: list[str] = []
    if 'stage' in df.columns:
        raw_stage = df['stage']
        numeric = pd.to_numeric(raw_stage, errors='coerce')
        valid = numeric.notna() & numeric.mod(1).eq(0) & numeric.between(12, 18)
        # Synthetic validation fixtures do not represent biological stages.
        # They must use the explicit label "not_applicable", not a fake CS stage.
        if 'modality' in df.columns:
            synthetic = df['modality'].astype('string').str.strip().str.lower().str.startswith('synthetic').fillna(False)
        else:
            synthetic = pd.Series(False, index=df.index)
        explicit_na = raw_stage.astype('string').str.strip().str.lower().eq('not_applicable').fillna(False)
        stage_ok = valid | (synthetic & explicit_na)
        bad_values = raw_stage.loc[~stage_ok & ~_blank(raw_stage)].astype(str).unique().tolist()
        # Missing stage is reported by missing_required; do not duplicate it here.
        invalid_stages = sorted(bad_values)
        if invalid_stages:
            notes.append('Hay valores de etapa no válidos: los datos biológicos requieren enteros CS12–CS18 y los sintéticos deben usar not_applicable.')

    multi: dict[str, int] = {}
    if {'specimen_id', 'image_id'}.issubset(df.columns):
        subset = df.loc[~_blank(df['specimen_id']) & ~_blank(df['image_id'])]
        counts = subset.groupby('specimen_id')['image_id'].nunique()
        multi = {str(k): int(v) for k, v in counts[counts > 1].items()}
        if multi:
            notes.append('Existen especímenes con múltiples imágenes; no contarlos automáticamente como individuos independientes.')

    quality_counts: dict[str, int] = {}
    quality_not_pass: dict[str, int] = {}
    if 'quality_flag' in df.columns:
        quality = df['quality_flag'].fillna('MISSING').astype(str).str.strip().str.lower()
        quality = quality.replace('', 'missing')
        quality_counts = {str(k): int(v) for k, v in quality.value_counts().items()}
        quality_not_pass = {k: v for k, v in quality_counts.items() if k not in ACCEPTED_QUALITY_FLAGS}
        if quality_not_pass:
            notes.append('Hay observaciones cuya calidad no está marcada como PASS o ACCEPTED; requieren revisión o exclusión documentada.')

    license_pending = 0
    if 'license_status' in df.columns:
        statuses = df['license_status'].fillna('MISSING').astype(str).str.strip().str.lower()
        statuses = statuses.replace('', 'missing')
        license_pending = int((~statuses.isin(ALLOWED_LICENSE_STATUSES)).sum())
        if license_pending:
            notes.append('Hay observaciones con licencia, permiso o estado de uso no verificado; no deben incorporarse al conjunto final hasta resolverlo.')

    specimens = int(df.loc[~_blank(df['specimen_id']), 'specimen_id'].nunique()) if 'specimen_id' in df.columns else 0
    missing_any = any(value > 0 for value in missing.values())
    ok = (
        len(df) > 0 and not missing_any and not duplicated and not invalid_stages
        and not license_pending and not quality_not_pass
    )
    return AuditResult(
        ok=ok,
        n_rows=int(len(df)),
        n_specimens=specimens,
        duplicated_observation_ids=duplicated,
        missing_required=missing,
        invalid_stages=invalid_stages,
        multi_image_specimens=multi,
        quality_counts=quality_counts,
        quality_not_pass=quality_not_pass,
        license_pending=license_pending,
        notes=notes,
    )


def audit_csv(path: str | Path) -> AuditResult:
    return audit_dataframe(pd.read_csv(path))


def save_audit(result: AuditResult, out: str | Path) -> None:
    output = Path(out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2), encoding='utf-8')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Audita metadatos y trazabilidad de un CSV.')
    parser.add_argument('csv')
    parser.add_argument('--out', default='audit.json')
    parser.add_argument('--strict', action='store_true', help='Devuelve código de salida distinto de cero si la auditoría no es válida.')
    args = parser.parse_args()
    result = audit_csv(args.csv)
    save_audit(result, args.out)
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    if args.strict and not result.ok:
        sys.exit(2)
