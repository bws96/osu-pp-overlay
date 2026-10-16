"""Local personal-record service. Reads scores.db; serves only the selected map."""
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import subprocess
from portable_runtime import NODE
import threading
import time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit
from core import Client,selection
from local_scores import parse_scores

ROOT=Path(__file__).resolve().parent
PORT=24051
ALIASES=json.loads((ROOT/'account_aliases.json').read_text(encoding='utf-8-sig'))
if (ROOT/'account_aliases.local.json').is_file():
    ALIASES.update(json.loads((ROOT/'account_aliases.local.json').read_text(encoding='utf-8-sig')))
NO_WINDOW=getattr(subprocess,'CREATE_NO_WINDOW',0)

def find_binding():
    # Resolve the exact native calculator already loaded by this application's tosu.
    command="[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false); $p=Get-Process -Name tosu -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq '"+str(ROOT/'runtime'/'tosu-4.26.2'/'tosu.exe').replace("'", "''")+"' }; $p | ForEach-Object { $_.Modules | Where-Object { $_.ModuleName -like 'binding-*.node' } | Select-Object -First 1 -ExpandProperty FileName }"
    output=subprocess.check_output(['powershell','-NoProfile','-Command',command],text=True,encoding='utf-8',creationflags=NO_WINDOW,timeout=12).strip()
    for line in output.splitlines():
        path=Path(line.strip())
        if path.suffix=='.node' and path.is_file():return str(path)
    raise RuntimeError('tosu calculator is not loaded yet')

class Records:
    def __init__(self):
        self.payload={'status':'idle'};self.lock=threading.Lock();self.index={};self.fingerprint=None
        self.cache={};self.binding=None;self.sessions={};self.last_result=None
    def set(self,payload):
        with self.lock:self.payload=payload
    def get(self):
        with self.lock:return dict(self.payload)
    def capture_result(self,client,data,user):
        if data.get('menu',{}).get('state')!=7:return
        result=client.get('/json/v2').get('resultsScreen',{})
        if result.get('playerName','').casefold()!=user.casefold():return
        checksum=data.get('menu',{}).get('bm',{}).get('md5')
        mode=result.get('mode',{}).get('number')
        hits=result.get('hits',{});score=int(result.get('score',0))
        mods=int(result.get('mods',{}).get('number',0));combo=int(result.get('maxCombo',0))
        signature=(checksum,user,mode,score,mods,combo,tuple(sorted(hits.items())))
        if signature==self.last_result or not checksum or mode not in (0,3) or not combo:return
        row=dict(mode=mode,name=user,checksum=checksum,great=hits.get('300',0),ok=hits.get('100',0),
            meh=hits.get('50',0),perfects=hits.get('geki',0),goods=hits.get('katu',0),miss=hits.get('0',0),
            score=score,combo=combo,mods=mods,score_id=result.get('scoreId',0),ticks=0)
        self.sessions.setdefault(checksum,[]).append(row)
        self.cache.clear();self.last_result=signature

    def run(self):
        client=Client()
        while True:
            try:
                data=client.get('/json');menu=data.get('menu',{})
                user=data.get('userProfile',{}).get('name','')
                self.capture_result(client,data,user)
                names={user.casefold()}|{name.casefold() for name in ALIASES.get(str(data.get('userProfile',{}).get('id','')),[])}
                selected=selection(data)
                if selected is None or not user:
                    self.set({'status':'idle'});time.sleep(.6);continue
                identity={'checksum':selected.checksum,'mode':selected.mode,'username':user}
                db=Path(data['settings']['folders']['game'])/'scores.db'
                stat=db.stat();fingerprint=(str(db),stat.st_mtime_ns,stat.st_size)
                if fingerprint!=self.fingerprint:
                    # A partial/in-progress write must never replace a valid index.
                    updated=parse_scores(db.read_bytes())
                    if db.stat().st_mtime_ns!=stat.st_mtime_ns:continue
                    self.index=updated;self.fingerprint=fingerprint;self.cache.clear()
                key=(selected.path,selected.checksum,selected.mode,user.casefold(),fingerprint)
                if key not in self.cache:
                    self.set({**identity,'status':'loading'})
                    rows=[r for r in self.index.get(selected.checksum,[])+self.sessions.get(selected.checksum,[]) if r['mode']==selected.mode and r['name'].casefold() in names]
                    if not rows:record=None
                    else:
                        if self.binding is None:self.binding=find_binding()
                        input_data={'binding':self.binding,'path':selected.path,'mode':selected.mode,'scores':rows}
                        result=subprocess.run([NODE,str(ROOT/'record_calculator.cjs')],input=json.dumps(input_data),text=True,encoding='utf-8',capture_output=True,creationflags=NO_WINDOW,timeout=30)
                        answer=json.loads(result.stdout)
                        if not answer.get('ok'):raise RuntimeError(answer.get('error','record calculation failed'))
                        record=answer['record']
                    if len(self.cache)>=128:self.cache.pop(next(iter(self.cache)))
                    self.cache[key]=record
                record=self.cache[key]
                self.set({**identity,'status':'ok' if record else 'none','source':'local','record':record})
            except Exception as error:
                logging.warning('Personal record: %s',error)
                self.set({'status':'error'});time.sleep(2)
            time.sleep(.5)

class Handler(BaseHTTPRequestHandler):
    records=None
    live=None
    def do_GET(self):
        route=urlsplit(self.path).path
        if route not in ('/health','/personal','/live'):
            self.send_error(404);return
        payload=({'app':'osu-fc-personal','version':5,'root':str(ROOT)} if route=='/health' else self.live.get() if route=='/live' else self.records.get())
        body=json.dumps(payload,ensure_ascii=False).encode('utf-8')
        self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin','*');self.send_header('Access-Control-Allow-Private-Network','true')
        self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def log_message(self,*args):pass

if __name__=='__main__':
    handler=RotatingFileHandler(ROOT/'personal.log',maxBytes=500_000,backupCount=1,encoding='utf-8')
    logging.basicConfig(handlers=[handler],level=logging.INFO)
    records=Records();Handler.records=records
    (ROOT/'personal.pid').write_text(str(__import__('os').getpid()))
    try:server=ThreadingHTTPServer(('127.0.0.1',PORT),Handler)
    except OSError:raise SystemExit('Personal record service is already running or port is in use')
    from live_service import Live
    live=Live(find_binding);Handler.live=live
    threading.Thread(target=live.run,daemon=True).start()
    threading.Thread(target=records.run,daemon=True).start()
    server.serve_forever()
