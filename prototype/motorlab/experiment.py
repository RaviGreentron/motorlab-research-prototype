"""Reproducible synthetic study runner and auditable artifact registry."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import platform
import time
import uuid
import os
import pickle
import importlib.metadata
import numpy as np
import psutil
from sklearn.metrics import precision_recall_fscore_support, confusion_matrix
from .signals import synthesize, extract, aggregate
from .contracts import CHANNELS, WINDOW_SECONDS
from .models import FEATURES, DetectorSuite
from .intelligence import diagnose, fuse, persistent_alerts
from .forecast import backtest

DATA=Path(__file__).resolve().parents[2]/'data'
FAULTS=['healthy','load_variation','voltage_imbalance','current_imbalance','phase_loss','harmonics',
        'transient','dropout','timestamp_gap','degradation','bearing_wear','thermal','combined','startup','shutdown','healthy']
ELECTRICAL={'voltage_imbalance','current_imbalance','phase_loss','harmonics','transient','degradation','combined'}


def clean(obj):
    if isinstance(obj,dict): return {str(k):clean(v) for k,v in obj.items()}
    if isinstance(obj,(list,tuple)): return [clean(v) for v in obj]
    if isinstance(obj,np.ndarray): return clean(obj.tolist())
    if isinstance(obj,np.generic): return clean(obj.item())
    if isinstance(obj,float) and not np.isfinite(obj): return None
    return obj


def dump(path,obj):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(clean(obj),indent=2,allow_nan=False),encoding='utf-8')


def waveform(record):
    result=extract(record); n=min(len(record['timestamps']),1200)
    x=record['values'][:n]
    return {'waveform':{'time_s':(np.arange(n)/10000).tolist(),
            'channels':{c:clean(x[:,j].tolist()) for j,c in enumerate(CHANNELS)}},
            'spectrum':{'frequency_hz':result['spectrum'].get('frequency_hz',[])[:501],
            'amplitude':[a[0] for a in result['spectrum'].get('amplitude',[])[:501]]}}


def metrics(labels,predictions,dt,groups):
    y=np.asarray(labels,bool); p=np.asarray(predictions,bool)
    precision,recall,f1,_=precision_recall_fscore_support(y,p,average='binary',zero_division=0)
    tn,fp,fn,tp=confusion_matrix(y,p,labels=[False,True]).ravel()
    false_events=0; true_events=0; detected=0; delays=[]
    for g in sorted(set(groups)):
        ix=np.where(np.asarray(groups)==g)[0]; yy=y[ix]; pp=p[ix]
        prev=False
        for a,b in zip(yy,pp):
            false=bool(b and not a)
            false_events+=int(false and not prev); prev=false
        starts=np.where(yy & ~np.r_[False,yy[:-1]])[0]
        for start in starts:
            end=start
            while end<len(yy) and yy[end]: end+=1
            hits=np.where(pp[start:end])[0]; true_events+=1
            if len(hits): detected+=1; delays.append(float(hits[0]*dt))
    healthy_days=float((~y).sum()*dt/86400)
    def wilson(success,total):
        if not total: return None
        ph=success/total; z=1.96; denominator=1+z*z/total
        centre=(ph+z*z/(2*total))/denominator
        radius=z*np.sqrt(ph*(1-ph)/total+z*z/(4*total*total))/denominator
        return [float(centre-radius),float(centre+radius)]
    return {'precision':float(precision),'recall':float(recall),'f1':float(f1),
            'recall_wilson95_descriptive':wilson(int(tp),int(tp+fn)),
            'fpr_wilson95_descriptive':wilson(int(fp),int(tn+fp)),
            'interval_caution':'Window-level intervals ignore within-event dependence; not population uncertainty.',
            'false_positive_rate':float(fp/max(1,tn+fp)), 'tp':int(tp),'fp':int(fp),'tn':int(tn),'fn':int(fn),
            'sample_count':len(y),'false_events':false_events,'healthy_motor_days':healthy_days,
            'false_events_per_motor_day':false_events/healthy_days if healthy_days else None,
            'event_recall':detected/true_events if true_events else None,'true_events':true_events,
            'mean_detection_delay_s':float(np.mean(delays)) if delays else None,
            'caution':'Scenario-block events, not operational incidents. False events count false-positive window runs within blocks. Short exposure makes motor-day extrapolation unstable; delay is window-level, not sample-accurate fault onset lead time.'}


def run_study(seed=42,window_seconds=1.,overlap=0.):
    if window_seconds not in WINDOW_SECONDS: raise ValueError('Unsupported window')
    if overlap!=0: raise ValueError('Benchmark uses disjoint windows; overlap available in signals.windows for replay')
    before=time.perf_counter(); cpu_before=time.process_time()
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8]
    root=DATA/run_id; root.mkdir(parents=True,exist_ok=False)
    config={'seed':seed,'window_seconds':window_seconds,'overlap':overlap,'sample_rate_hz':10000,
            'windows_per_motor':240,'phase_convention':'phase_to_neutral','feature_schema':'motorlab.features/1'}
    motors=[]; dsp_times=[]; samples_hash=hashlib.sha256()
    for motor_n in range(3):
        motor_id=f'SIM-{motor_n+1:02d}'; rows=[]
        for i in range(240):
            partition='train' if i<80 else 'early_stop' if i<120 else 'calibration' if i<160 else 'test'
            scenario='healthy' if i<160 else FAULTS[(i-160)//5]
            regime='light' if i%2==0 else 'full'
            rng=np.random.default_rng(seed+motor_n*10000+i)
            load=(.65 if regime=='light' else 1.)*(1+rng.normal(0,.025))
            sample_seed=seed+motor_n*10000+i
            raw=synthesize(scenario,window_seconds,sample_seed,load=load,motor_id=motor_id)
            samples_hash.update(raw['values'].tobytes()); samples_hash.update(raw['timestamps'].tobytes())
            started=time.perf_counter(); out=extract(raw); dsp_times.append(time.perf_counter()-started)
            rows.append({'index':i,'time_s':i*window_seconds,'scenario':scenario,'partition':partition,
                         'regime':regime,'load':load,'sample_seed':sample_seed,'quality':out['quality'],
                         'features':out['features'],'optional_features':out['optional_features'],'mcsa':out['mcsa'],
                         'metadata':dict(out['metadata'],motor_id=motor_id,operating_state=regime),
                         'timestamp_us':int(i*window_seconds*1e6),'scores':{},'contributors':[]})
        motors.append({'id':motor_id,'records':rows,**waveform(synthesize('healthy',window_seconds,seed+motor_n*10000,motor_id=motor_id,load=rows[0]['load']))})
    suites={}; timings={}; valid=lambda r:r['quality']['valid'] and r['scenario'] not in ('startup','shutdown')
    for m in motors:
        for regime in ('light','full'):
            # Entire SIM-03 is held out; use pooled SIM-01/02 training, never SIM-03 fit/calibration.
            donors=motors[:2] if m['id']=='SIM-03' else [m]
            partitions=[]
            for part in ('train','early_stop','calibration'):
                rs=[r for donor in donors for r in donor['records'] if r['partition']==part and r['regime']==regime and valid(r)]
                partitions.append(np.array([[r['features'][k] for k in FEATURES] for r in rs]))
            suite=DetectorSuite(seed).fit(*partitions); suites[(m['id'],regime)]=suite
            timings[f"{m['id']}/{regime}"]=suite.training_seconds
            pickle_path=root/f"{m['id']}-{regime}.pkl"
            with pickle_path.open('wb') as f: pickle.dump(suite,f)
            dump(root/f"{m['id']}-{regime}-training.json",{'history':suite.ae.history,'thresholds':suite.thresholds,
                 'donor_motors':[d['id'] for d in donors],'features':FEATURES,'calibration_quantile':.99})
            selected=[r for r in m['records'] if r['regime']==regime and valid(r)]
            x=np.array([[r['features'][k] for k in FEATURES] for r in selected])
            started=time.perf_counter(); scored=suite.score(x)
            timings[f"{m['id']}/{regime}/inference_ms_per_window"]=(time.perf_counter()-started)*1000/len(x)
            diagnostics=suite.statistical_diagnostics(x)
            for j,r in enumerate(selected):
                r['scores']={k:{field:clean(vals[j]) for field,vals in result.items()} for k,result in scored.items()}
                r['contributors']=suite.contributors(x[j]); r['statistical_diagnostics']={
                    'classical_z_max':diagnostics['classical_z_max'][j], 'mahalanobis_squared':diagnostics['mahalanobis_squared'][j],
                    **diagnostics['sequential'][j]}
    for m in motors:
        ratios=[]; validity=[]
        for r in m['records']:
            a=max([s['ratio'] for s in r['scores'].values()],default=float('nan'))
            opt=r['optional_features']; vib=opt.get('vibration',{}); thermal=opt.get('temperature',{})
            vr=max(np.atleast_1d(vib.get('rms',0)))/.5 if vib.get('status')=='VALID' else None
            tr=max(0,(float(thermal.get('mean',45))-45)/10) if thermal.get('status')=='VALID' else None
            r['fused']=fuse({'electrical':a,'vibration':vr,'thermal':tr}) if valid(r) else {'status':'UNASSESSABLE','score':None,'missing':['valid electrical window or steady regime']}
            r['intelligence']=diagnose(r['features'],r['fused']['score'] or 0,valid(r))
            ratios.append(r['fused']['score'] if r['fused']['score'] is not None else np.nan); validity.append(valid(r))
        persisted=persistent_alerts(ratios,validity)
        for r,p in zip(m['records'],persisted): r['persistent_alert']=bool(p)
    results={}
    evaluation=[(m,r) for m in motors for r in m['records'] if r['partition']=='test' and valid(r)]
    labels=[r['scenario'] in ELECTRICAL for m,r in evaluation]
    groups=[m['id']+'/'+str((r['index']-160)//5)+'/'+r['scenario'] for m,r in evaluation]
    for model in ('A','B','C'):
        results[model]=metrics(labels,[r['scores'][model]['alert'] for m,r in evaluation],window_seconds,groups)
        results[model]['per_motor']={m['id']:metrics([r['scenario'] in ELECTRICAL for mm,r in evaluation if mm is m],
            [r['scores'][model]['alert'] for mm,r in evaluation if mm is m],window_seconds,
            [str((r['index']-160)//5)+'/'+r['scenario'] for mm,r in evaluation if mm is m]) for m in motors}
    results['fusion']=metrics([r['scenario'] in ELECTRICAL|{'bearing_wear','thermal'} for m,r in evaluation],
        [r['persistent_alert'] for m,r in evaluation],window_seconds,groups)
    # Independent physical-feature trajectory: synthetic temperature, one observation per minute.
    rng=np.random.default_rng(seed); t=np.arange(120); history=45+.05*t+.0008*t*t+rng.normal(0,.12,len(t))
    forecasts=backtest(history)
    proc=psutil.Process()
    report={'run_id':run_id,'created_at':datetime.now(timezone.utc).isoformat(),'provenance':'SIMULATED','config':config,
        'motors':motors,'metrics':results,'forecast':{'feature':'temperature_degC','cadence_seconds':60,'history':history.tolist(),'models':forecasts},
        'benchmark':{'elapsed_seconds':time.perf_counter()-before,'process_cpu_seconds':time.process_time()-cpu_before,
            'dsp_median_ms':float(np.median(dsp_times)*1000),'dsp_p95_ms':float(np.quantile(dsp_times,.95)*1000),
            'dsp_scalar_values_per_second':float(6*10000*window_seconds/np.mean(dsp_times)),
            'resident_memory_mb':proc.memory_info().rss/1024**2,'model_timings':timings,
            'platform':platform.platform(),'python':platform.python_version(),'logical_cpus':os.cpu_count(),
            'total_ram_gb':psutil.virtual_memory().total/1024**3,'gpu':'NOT USED — CPU NumPy autoencoder'},
        'capabilities':{'synthetic':'AVAILABLE','csv_replay':'LIBRARY_AVAILABLE','influx':'BLOCKED — no authorized contract',
            'A':'AVAILABLE','B':'AVAILABLE','C':'AVAILABLE — CPU NumPy autoencoder','D':'AVAILABLE — classical',
            'chronos':'NOT RUN — separate model trial','timesfm':'NOT RUN — version/license selection required',
            'real_rul':'RUL_NOT_ESTIMABLE','real_motor_suitability':'INCONCLUSIVE'},
        'manifest':{'raw_sha256':samples_hash.hexdigest(),'feature_schema':'motorlab.features/1','feature_names':FEATURES,
            'partition_ranges':{'train':[0,80],'early_stop':[80,120],'calibration':[120,160],'test':[160,240]},
            'split_unit':'disjoint synthetic windows; bounds half-open','held_out_motor':'SIM-03',
            'threshold_rule':'99th percentile of separate healthy calibration; experimental not industrial acceptance',
            'model_versions':{'A':'robust-MAD/1','B':'sklearn-IsolationForest/1','C':'numpy-tanh-AE/1','D':'rolling-classical/1'},
            'dependencies':{p:importlib.metadata.version(p) for p in ['numpy','scipy','scikit-learn','fastapi','statsmodels']},
            'limitations':['Electrical detector metrics exclude sensor failures and transition windows; exclusion counts are reported.',
                'Bearing/thermal scenarios count as electrical negatives; fusion evaluates these separately.',
                'Short synthetic windows are not representative degradation histories; no industrial acceptance established.',
                'Optional sensor fusion thresholds are illustrative and uncalibrated, not promoted as validated.']}}
    report['manifest']['source_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')}
    report['manifest']['exclusions']={s:sum(r['scenario']==s for m in motors for r in m['records'] if r['partition']=='test' and not valid(r)) for s in FAULTS}
    report['aggregates']={str(period):aggregate([r for m in motors for r in m['records']],period) for period in (10,60,300,900,3600)}
    report=clean(report); dump(root/'report.json',report)
    dump(root/'manifest.json',report['manifest']); dump(DATA/'latest.json',{'run_id':run_id})
    return report


def load_run(run_id=None):
    if run_id is None: run_id=json.loads((DATA/'latest.json').read_text())['run_id']
    if not run_id or any(c not in '0123456789Tabcdef-' for c in run_id): raise ValueError('Invalid run id')
    return json.loads((DATA/run_id/'report.json').read_text(encoding='utf-8'))


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('--seed',type=int,default=42); p.add_argument('--window',type=float,default=1.)
    args=p.parse_args(); report=run_study(args.seed,args.window)
    print(json.dumps({'run_id':report['run_id'],'metrics':report['metrics'],'benchmark':report['benchmark']},indent=2))
