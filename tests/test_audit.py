import pandas as pd
from src.audit_dataset import audit_dataframe

def base_row(i='O1', specimen='S1'):
    return dict(observation_id=i,specimen_id=specimen,image_id='I1',stage=14,modality='H&E',view='lateral',source='X',asset_identifier='A1',license_status='verified',segmentation_method='semi-auto',quality_flag='PASS')

def test_valid_dataset():
    r=audit_dataframe(pd.DataFrame([base_row()]))
    assert r.ok
    assert r.n_specimens==1

def test_duplicate_observation_is_flagged():
    a=base_row('O1'); b=base_row('O1', 'S2')
    r=audit_dataframe(pd.DataFrame([a,b]))
    assert not r.ok
    assert 'O1' in r.duplicated_observation_ids

def test_blank_required_field_is_flagged():
    row = base_row()
    row['source'] = '   '
    r = audit_dataframe(pd.DataFrame([row]))
    assert not r.ok
    assert r.missing_required['source'] == 1


def test_fractional_stage_is_invalid():
    row = base_row()
    row['stage'] = 14.5
    r = audit_dataframe(pd.DataFrame([row]))
    assert not r.ok
    assert '14.5' in r.invalid_stages


def test_pending_license_makes_audit_fail():
    row = base_row()
    row['license_status'] = 'pending'
    r = audit_dataframe(pd.DataFrame([row]))
    assert not r.ok
    assert r.license_pending == 1


def test_nonpassing_quality_makes_audit_fail():
    row = base_row()
    row['quality_flag'] = 'REVIEW'
    r = audit_dataframe(pd.DataFrame([row]))
    assert not r.ok
    assert r.quality_not_pass['review'] == 1


def test_empty_dataset_is_not_valid():
    r = audit_dataframe(pd.DataFrame(columns=list(base_row().keys())))
    assert not r.ok
    assert r.n_rows == 0


def test_synthetic_fixture_uses_not_applicable_stage():
    row = base_row()
    row['modality'] = 'SYNTHETIC'
    row['stage'] = 'not_applicable'
    r = audit_dataframe(pd.DataFrame([row]))
    assert r.ok
    assert r.invalid_stages == []


def test_biological_record_cannot_use_not_applicable_stage():
    row = base_row()
    row['stage'] = 'not_applicable'
    r = audit_dataframe(pd.DataFrame([row]))
    assert not r.ok
    assert 'not_applicable' in r.invalid_stages
