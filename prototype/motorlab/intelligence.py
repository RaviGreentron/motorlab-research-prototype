"""Evidence rules: research thresholds, never operational advice."""
import numpy as np


def persistent_alerts(ratios, valid=None, on=1., off=.8, count=2, severe=3.):
    valid=np.ones(len(ratios),bool) if valid is None else np.asarray(valid,bool)
    active=False; streak=0; result=[]
    for ratio,ok in zip(ratios,valid):
        if not ok or not np.isfinite(ratio): active=False; streak=0; result.append(False); continue
        streak=streak+1 if ratio>on else 0
        if ratio>=severe or streak>=count: active=True
        if ratio<off: active=False
        result.append(active)
    return np.asarray(result)


def fuse(evidence):
    available={k:float(v) for k,v in evidence.items() if v is not None and np.isfinite(v)}
    if not available: return {'status':'UNASSESSABLE','score':None,'missing':list(evidence)}
    score=max(available.values()) # preserve severe single sensor evidence
    return {'status':'CRITICAL' if score>=3 else 'WARNING' if score>1 else 'NORMAL',
            'score':score,'available':list(available),'missing':[k for k in evidence if k not in available],
            'method':'max-evidence experimental; not probability',
            'pattern':'correlated' if sum(v>1 for v in available.values())>1 else 'single-signal-or-normal'}


def diagnose(features,ratio,quality=True):
    if not quality or ratio is None or not np.isfinite(ratio): return {'status':'UNASSESSABLE','hypotheses':[],'health_index':None,'recommendation':'Inspect sensor data integrity','rul_status':'RUL_NOT_ESTIMABLE'}
    hypotheses=[]
    for key,threshold,label in [('v_imbalance_pct',3.,'Voltage imbalance'),('i_imbalance_pct',5.,'Current imbalance'),('i_thd_pct',8.,'Abnormal current harmonics')]:
        if features.get(key) is not None and features[key]>threshold:
            hypotheses.append({'category':label,'supporting_features':{key:features[key]},'contradictory_evidence':[],
                'required_measurements':'Verified calibrated synchronized electrical channels','method':'experimental rule',
                'evidence_strength':'feature-level only','validation_status':'SYNTHETIC_ONLY',
                'limitations':'Does not distinguish supply, load, wiring and internal motor causes'})
    current=[features.get(f'i_rms_{i}') for i in (1,2,3)]
    if all(v is not None and np.isfinite(v) for v in current) and max(current)>0 and min(current)/max(current)<.1:
        hypotheses.append({'category':'Phase loss or sensor fault','supporting_features':{'phase_rms_A':current},
            'contradictory_evidence':[],'required_measurements':'Independent sensor/wiring check','method':'phase amplitude ratio',
            'evidence_strength':'ambiguous','validation_status':'SYNTHETIC_ONLY','limitations':'Cannot separate open phase from sensor loss'})
    return {'status':'ANOMALY_DETECTED_CAUSE_UNKNOWN' if ratio>1 and not hypotheses else 'HYPOTHESIS' if hypotheses else 'NO_ANOMALY_DETECTED',
            'hypotheses':hypotheses,'health_index':float(np.clip(100-25*max(0,ratio-.5),0,100)),
            'health_label':'EXPERIMENTAL HEALTH INDEX — uncalibrated; not remaining life',
            'recommendation':'Urgent engineering review' if ratio>=3 else 'Inspection suggested' if ratio>1 else 'Observation',
            'rul_status':'RUL_NOT_ESTIMABLE','service_window':None,'limitations':'No measured failure trajectories or validated endpoint'}


def rul_eligibility(provenance,endpoint=None,histories=0,validated=False):
    return {'status':'ELIGIBLE_FOR_RESEARCH' if endpoint and histories>=3 and validated else 'RUL_NOT_ESTIMABLE',
            'provenance':provenance,'endpoint':endpoint,'histories':histories,'validated':validated}
