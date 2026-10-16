"""Real-time forecast worker for stable osu!/mania. Reads tosu's existing API."""
import json
import logging
from pathlib import Path
import queue
import subprocess
from portable_runtime import NODE
import threading
import time
from core import Client

ROOT=Path(__file__).resolve().parent

class NativeWorker:
    def __init__(self,binding):
        self.binding=binding
        self.process=subprocess.Popen([NODE,str(ROOT/'live_calculator.cjs')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,encoding='utf-8',bufsize=1,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        self.responses=queue.Queue()
        threading.Thread(target=self.read,daemon=True).start()
    def read(self):
        for line in self.process.stdout:self.responses.put(line)
        self.responses.put(None)
    def calculate(self,data):
        self.process.stdin.write(json.dumps({**data,'binding':self.binding})+'\n');self.process.stdin.flush()
        try:line=self.responses.get(timeout=8)
        except queue.Empty:raise RuntimeError('Forecast calculator timed out')
        if line is None:raise RuntimeError('Forecast calculator stopped')
        result=json.loads(line)
        if not result.get('ok'):raise RuntimeError(result.get('error'))
        return result
    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:self.process.kill()

def snapshot(data):
    if data.get('state',{}).get('number')!=2:return None
    play=data.get('play',{});mode=play.get('mode',{}).get('number')
    if mode not in (0,3) or play.get('failed'):return None
    bm=data.get('beatmap',{});name=data.get('files',{}).get('beatmap','')
    if not bm.get('checksum') or not name.endswith('.osu'):return None
    folder=data.get('folders',{})
    path=str(Path(folder.get('songs',''))/folder.get('beatmap','')/name)
    mods=play.get('mods',{}).get('number',0)
    identity={'checksum':bm['checksum'],'mode':mode,'mods':mods}
    request=dict(path=path,**identity,time=bm.get('time',{}).get('live',0),hits=play.get('hits',{}),
        combo=play.get('combo',{}).get('current',0),maxCombo=play.get('combo',{}).get('max',0),score=play.get('score',0))
    return identity,request,play.get('pp',{}).get('current',0)

class Live:
    def __init__(self,binding_provider):
        self.binding_provider=binding_provider;self.payload={'status':'idle'};self.lock=threading.Lock();self.worker=None
    def set(self,payload):
        with self.lock:self.payload=payload
    def get(self):
        with self.lock:result=dict(self.payload)
        if time.monotonic()-result.pop('_updated',0)>2:return {'status':'idle'}
        return result
    def run(self):
        client=Client()
        while True:
            try:
                state=snapshot(client.get('/json/v2'))
                if state is None:
                    self.set({'status':'idle'});time.sleep(.2);continue
                identity,request,current=state
                if any(self.payload.get(k)!=v for k,v in identity.items()):
                    self.set({**identity,'status':'ok','current':current,'forecast':None,'time':request['time'],'_updated':time.monotonic()})
                if self.worker is None:self.worker=NativeWorker(self.binding_provider())
                result=self.worker.calculate(request)
                # Discard results if the song/ruleset/mods changed while calculating.
                check=snapshot(client.get('/json/v2'))
                if check is None or check[0]!=identity or check[1]['time']<request['time']:continue
                self.set({**identity,'status':'ok','current':current,'forecast':result['forecast'],
                    'accuracy':result['accuracy'],'remaining':result['remaining'],'time':request['time'],'_updated':time.monotonic()})
            except Exception as error:
                logging.warning('Live estimate: %s',error)
                self.set({'status':'error'})
                if self.worker:self.worker.close();self.worker=None
                time.sleep(1)
            time.sleep(.12)
