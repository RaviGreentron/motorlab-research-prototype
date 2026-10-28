import numpy as np
import pytest
from motorlab.synthetic_rul import estimate, evaluate


def test_noiseless_quadratic_endpoint_is_recovered():
    t=np.arange(50); y=10+.01*t*t
    r=estimate(y,110)
    assert r['status']=='SYNTHETIC_RUL_ONLY'
    assert abs(r['median_steps']-51)<=1
    assert r['provenance']=='SIMULATED'


def test_non_crossing_is_not_estimable():
    assert estimate(np.ones(50)*20,70)['status']=='RUL_NOT_ESTIMABLE'


def test_short_trajectory_rejected():
    with pytest.raises(ValueError): estimate(np.arange(5),100)


def test_evaluation_retains_known_truth():
    r=evaluate()
    assert len(r['backtests'])==4 and r['mae_steps']<15
    assert all(x['actual_steps']>0 for x in r['backtests'])
