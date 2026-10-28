"""Run reproducible multi-window studies and write measured validation evidence."""
import json
import time
from pathlib import Path
import numpy as np
from motorlab.experiment import run_study, dump, DATA
from motorlab.signals import synthesize, extract
from motorlab.synthetic_rul import evaluate


def main():
    studies=[]
    for window,seed in ((.1,42),(.2,42),(.5,42),(1.,42),(2.,42),(5.,42),(1.,7)):
        r=run_study(seed,window)
        studies.append({k:r[k] for k in ('run_id','config','metrics','forecast','benchmark','manifest')})
        print(f"Completed window={window}, seed={seed}, run={r['run_id']}",flush=True)
    # Same-seed reproducibility compares results, not run identifiers or clock-dependent timings.
    repeat=run_study(42,1.)
    reference=next(r for r in studies if r['config']['window_seconds']==1 and r['config']['seed']==42)
    reproducible=reference['manifest']['raw_sha256']==repeat['manifest']['raw_sha256'] and reference['metrics']==repeat['metrics']
    summary={'studies':studies,'reference_run':reference['run_id'],'latest_reference_run':repeat['run_id'],
             'deterministic_repeat':{'status':'PASS' if reproducible else 'FAIL','raw_hash_and_detection_metrics_equal':reproducible},
             'synthetic_rul':evaluate(), 'suitability':'INCONCLUSIVE FOR REAL MOTORS; REVISE NORMAL-LOAD FALSE ALARMS'}
    dump(DATA/'validation-summary.json',summary)
    assert reproducible,'Same-seed outputs changed'


if __name__=='__main__': main()
