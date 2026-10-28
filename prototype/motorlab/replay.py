"""Offline raw CSV -> quality-gated feature JSON, no model or database mutation."""
import argparse
import json
from pathlib import Path
from .signals import read_csv, windows, extract, aggregate
from .contracts import WindowConfig
from .experiment import dump


def replay(csv_path,metadata_path,output,seconds=1.,overlap=0.):
    metadata=json.loads(Path(metadata_path).read_text(encoding='utf-8'))
    record=read_csv(csv_path,metadata); rows=[]
    for window in windows(record,seconds,overlap):
        item=extract(window); item.pop('spectrum',None)
        item['timestamp_us']=int(window['timestamps'][0]); rows.append(item)
    report={'source':str(csv_path),'provenance':metadata.get('provenance'),'windows':rows,
            'model_status':'UNAVAILABLE — replay requires separately verified healthy baseline',
            'rul_status':'RUL_NOT_ESTIMABLE','aggregates':aggregate(rows,60)}
    dump(output,report); return report


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('csv'); p.add_argument('metadata'); p.add_argument('output')
    p.add_argument('--window',type=float,default=1.); p.add_argument('--overlap',type=float,default=0.)
    a=p.parse_args(); r=replay(a.csv,a.metadata,a.output,a.window,a.overlap)
    print(json.dumps({'windows':len(r['windows']),'provenance':r['provenance'],'model_status':r['model_status']}))
