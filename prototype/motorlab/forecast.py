"""Expanding-origin physical-feature forecasts; intervals calibrated on earlier origins."""
import time
import numpy as np
from scipy.stats import theilslopes
from statsmodels.tsa.holtwinters import ExponentialSmoothing


def predict(y,horizon,method):
    y=np.asarray(y,float); t=np.arange(len(y)); future=np.arange(len(y),len(y)+horizon)
    if not np.isfinite(y).all() or len(y)<8: raise ValueError('Forecast requires >=8 finite observations')
    if method=='naive': return np.full(horizon,y[-1])
    if method=='linear': return np.polyval(np.polyfit(t,y,1),future)
    if method=='robust':
        slope,intercept,_,_=theilslopes(y,t); return intercept+slope*future
    if method=='holt': return np.asarray(ExponentialSmoothing(y,trend='add',initialization_method='estimated').fit().forecast(horizon))
    raise ValueError('Unknown forecast method')


def backtest(y,horizon=5,initial=40,step=5):
    if horizon<1 or step<horizon: raise ValueError('Use disjoint backtest horizons: step >= horizon >= 1')
    y=np.asarray(y,float); result={}
    for method in ('naive','linear','robust','holt'):
        errors=[]; covered=[]; origins=[]; before=time.perf_counter()
        for origin in range(initial,len(y)-horizon+1,step):
            p=predict(y[:origin],horizon,method); e=p-y[origin:origin+horizon]
            if len(errors)>=4:
                widths=np.quantile(np.abs(errors),.9,axis=0)
                covered.append((np.abs(e)<=widths).tolist())
            errors.append(e); origins.append(origin)
        if not errors: raise ValueError('Insufficient rolling origins')
        e=np.asarray(errors); widths=np.quantile(np.abs(e),.9,axis=0)
        future=predict(y,horizon,method)
        truths=np.array([y[o:o+horizon] for o in origins]); forecasts=truths+e
        result[method]={'mae':float(np.abs(e).mean()),'rmse':float(np.sqrt((e*e).mean())),
            'bias':float(e.mean()),'smape_pct':float(np.mean(200*np.abs(e)/np.maximum(np.abs(truths)+np.abs(forecasts),1e-8))),
            'mae_by_horizon':np.abs(e).mean(0).tolist(),'interval_coverage':float(np.mean(covered)) if covered else None,
            'coverage_origins':len(covered),'origins':origins,'latency_ms':(time.perf_counter()-before)*1000/len(errors),
            'forecast':future.tolist(),'lower':(future-widths).tolist(),'upper':(future+widths).tolist(),
            'nominal_coverage':.9,'interval_method':'past-origin absolute residual quantile; descriptive, not guaranteed',
            'rul_status':'RUL_NOT_ESTIMABLE'}
    return result
