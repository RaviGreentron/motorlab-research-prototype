"""Loopback research API. Never imports production credentials or clients."""
from pathlib import Path
import json
import sqlite3
import threading
from typing import Literal
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict
from .experiment import DATA, run_study, load_run, waveform
from .signals import synthesize

app=FastAPI(title='MotorLab Research API',version='1.0.0',description='Isolated synthetic research. No production access.')
run_lock=threading.Lock()


class StudyConfig(BaseModel):
    model_config=ConfigDict(extra='forbid')
    seed:int=Field(default=42,ge=0,le=2**31-1)
    window_seconds:Literal[.1,.2,.5,1.,2.,5.]=1.
    overlap:Literal[0.]=0.


class Note(BaseModel):
    model_config=ConfigDict(extra='forbid')
    motor_id:str=Field(pattern=r'^SIM-0[123]$')
    index:int=Field(ge=0,lt=240)
    text:str=Field(min_length=1,max_length=4000)


@app.exception_handler(HTTPException)
async def http_error(request,exc):
    return JSONResponse(status_code=exc.status_code,content={'error':{'code':str(exc.status_code),'message':str(exc.detail)}})


@app.exception_handler(RequestValidationError)
async def validation_error(request,exc):
    return JSONResponse(status_code=422,content={'error':{'code':'INVALID_INPUT','message':str(exc)}})


@app.middleware('http')
async def local_mutations(request:Request,call_next):
    # Browser same-origin protection: no cross-origin writes to local research artifacts.
    if request.method not in ('GET','HEAD','OPTIONS'):
        origin=request.headers.get('origin')
        if origin and origin not in ('http://127.0.0.1:8765','http://localhost:8765','http://localhost:5173','http://127.0.0.1:5173'):
            return JSONResponse(status_code=403,content={'error':{'code':'ORIGIN_DENIED','message':'Local same-origin requests only'}})
    return await call_next(request)


def get_report(run_id=None):
    try: return load_run(run_id)
    except (ValueError,FileNotFoundError): raise HTTPException(404,'Research run not found')


@app.get('/api/v1/health')
def health(): return {'status':'ok','production_access':False,'provenance':'SIMULATED'}


@app.get('/api/v1/runs')
def runs(limit:int=Query(20,ge=1,le=100),offset:int=Query(0,ge=0)):
    files=sorted(DATA.glob('*/report.json'),reverse=True)
    return {'total':len(files),'items':[{'run_id':p.parent.name} for p in files[offset:offset+limit]]}


@app.get('/api/v1/runs/latest')
def latest(): return get_report()


@app.post('/api/v1/runs',status_code=201)
def create_run(config:StudyConfig):
    if not run_lock.acquire(blocking=False): raise HTTPException(409,'An experiment is already running')
    try: return run_study(**config.model_dump())
    finally: run_lock.release()


@app.get('/api/v1/runs/{run_id}/export')
def export(run_id:str):
    report=get_report(run_id)
    return JSONResponse(report,headers={'Content-Disposition':f'attachment; filename="{run_id}.json"'})


@app.get('/api/v1/runs/{run_id}/waveform')
def get_waveform(run_id:str,motor_id:str,index:int=Query(0,ge=0,lt=240)):
    report=get_report(run_id)
    motor=next((m for m in report['motors'] if m['id']==motor_id),None)
    if not motor: raise HTTPException(404,'Motor not found')
    row=motor['records'][index]
    result=waveform(synthesize(row['scenario'],report['config']['window_seconds'],row['sample_seed'],load=row['load'],motor_id=motor_id))
    return dict(result,provenance=report['provenance'],run_id=run_id,motor_id=motor_id,index=index,quality=row['quality'])


@app.get('/api/v1/runs/{run_id}/features')
def features(run_id:str,motor_id:str,start:float=Query(0,ge=0),end:float=Query(1e6,ge=0),limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0)):
    if end<start: raise HTTPException(422,'end must be >= start')
    report=get_report(run_id); motor=next((m for m in report['motors'] if m['id']==motor_id),None)
    if not motor: raise HTTPException(404,'Motor not found')
    rows=[r for r in motor['records'] if start<=r['time_s']<end]
    return {'run_id':run_id,'provenance':report['provenance'],'total':len(rows),'items':rows[offset:offset+limit]}


def connection():
    DATA.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(DATA/'notes.sqlite')
    c.execute('CREATE TABLE IF NOT EXISTS notes(id INTEGER PRIMARY KEY,run_id TEXT,motor_id TEXT,idx INTEGER,text TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP)')
    return c


@app.get('/api/v1/runs/{run_id}/notes')
def notes(run_id:str):
    get_report(run_id)
    with connection() as c:
        rows=c.execute('SELECT id,motor_id,idx,text,created_at FROM notes WHERE run_id=? ORDER BY id',(run_id,)).fetchall()
    return {'items':[dict(zip(['id','motor_id','index','text','created_at'],row)) for row in rows]}


@app.post('/api/v1/runs/{run_id}/notes',status_code=201)
def add_note(run_id:str,note:Note):
    get_report(run_id)
    with connection() as c:
        row=c.execute('INSERT INTO notes(run_id,motor_id,idx,text) VALUES(?,?,?,?)',(run_id,note.motor_id,note.index,note.text))
        c.commit(); identity=row.lastrowid
    return {'id':identity,**note.model_dump(),'run_id':run_id}


@app.get('/api/v1/capabilities')
def capabilities(): return {'influx':{'status':'BLOCKED','reason':'Requires explicit live read authorization and verified schema'},'rul':{'status':'RUL_NOT_ESTIMABLE'}}


dist=Path(__file__).resolve().parents[1]/'frontend'/'dist'
if dist.exists(): app.mount('/',StaticFiles(directory=dist,html=True),name='dashboard')
