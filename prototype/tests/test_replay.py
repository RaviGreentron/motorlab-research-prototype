import csv
import json
import numpy as np
from motorlab.signals import synthesize
from motorlab.contracts import CHANNELS
from motorlab.replay import replay


def test_csv_replay_overlap_and_provenance(tmp_path):
    raw=synthesize(seconds=.5)
    csv_path=tmp_path/'raw.csv'; meta=tmp_path/'metadata.json'
    with csv_path.open('w',newline='') as f:
        w=csv.writer(f); w.writerow(['timestamp_us',*CHANNELS])
        w.writerows([[int(t),*v] for t,v in zip(raw['timestamps'],raw['values'])])
    meta.write_text(json.dumps(raw['metadata']))
    result=replay(csv_path,meta,tmp_path/'result.json',.2,.5)
    assert len(result['windows'])==4
    assert result['provenance']=='SIMULATED'
    assert all(r['quality']['valid'] for r in result['windows'])
    assert all(abs(r['features']['i_rms_1']-10)<.01 for r in result['windows'])
    assert result['model_status'].startswith('UNAVAILABLE')


def test_replay_preserves_gap_rejection(tmp_path):
    raw=synthesize('timestamp_gap',seconds=.2)
    csv_path=tmp_path/'gap.csv'; meta=tmp_path/'metadata.json'
    with csv_path.open('w',newline='') as f:
        w=csv.writer(f); w.writerow(['timestamp_us',*CHANNELS])
        w.writerows([[int(t),*v] for t,v in zip(raw['timestamps'],raw['values'])])
    meta.write_text(json.dumps(raw['metadata']))
    result=replay(csv_path,meta,tmp_path/'result.json',.2)
    assert not result['windows'][0]['quality']['valid']
    assert not result['windows'][0]['features']
