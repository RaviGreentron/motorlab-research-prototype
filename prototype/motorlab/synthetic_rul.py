"""Explicit toy endpoint experiment, separate from real motor RUL eligibility."""
import numpy as np


def estimate(history, endpoint, seed=42, draws=200, max_horizon=240):
    y=np.asarray(history,float)
    if len(y)<30 or not np.isfinite(y).all() or not np.isfinite(endpoint):
        raise ValueError('Need >=30 finite synthetic trajectory observations and endpoint')
    x=np.arange(len(y)); coef=np.polyfit(x,y,2); fitted=np.polyval(coef,x)
    residual=y-fitted; rng=np.random.default_rng(seed); future=np.arange(len(y),len(y)+max_horizon)
    crossings=[]
    for _ in range(draws):
        boot=fitted+rng.choice(residual,len(residual),replace=True)
        curve=np.polyval(np.polyfit(x,boot,2),future)
        ix=np.where(curve>=endpoint)[0]
        if len(ix): crossings.append(int(ix[0]+1))
    if len(crossings)<.9*draws:
        return {'status':'RUL_NOT_ESTIMABLE','reason':'Too many non-crossing bootstrap trajectories','provenance':'SIMULATED'}
    return {'status':'SYNTHETIC_RUL_ONLY','provenance':'SIMULATED','median_steps':float(np.median(crossings)),
            'interval90_steps':np.quantile(crossings,[.05,.95]).tolist(),'endpoint':endpoint,
            'method':'Quadratic fit with residual bootstrap; assumes known quadratic synthetic mechanism',
            'limitations':'Toy threshold crossing, not physical failure prognosis; intervals conditional on simulation model'}


def evaluate(seed=42):
    rng=np.random.default_rng(seed); t=np.arange(400); truth=45+.05*t+.0008*t*t
    observed=truth+rng.normal(0,.12,len(t)); endpoint=70.
    failure=int(np.where(truth>=endpoint)[0][0]); results=[]
    for origin in (60,80,100,120):
        prediction=estimate(observed[:origin],endpoint,seed)
        actual=failure-origin+1
        results.append({'origin':origin,'actual_steps':actual,'prediction':prediction,
                        'absolute_error_steps':abs(prediction['median_steps']-actual),
                        'covered':prediction['interval90_steps'][0]<=actual<=prediction['interval90_steps'][1]})
    return {'provenance':'SIMULATED','cadence_seconds':60,'endpoint_degC':endpoint,
            'endpoint_meaning':'Arbitrary simulator threshold, not motor failure temperature',
            'known_crossing_index':failure,'backtests':results,
            'mae_steps':float(np.mean([r['absolute_error_steps'] for r in results])),
            'interval_coverage':float(np.mean([r['covered'] for r in results]))}
