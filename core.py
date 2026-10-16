"""tosu-native FC table access. Legacy rosu-pp-py is deliberately not used."""
from dataclasses import dataclass
import json
import math
from pathlib import Path
from urllib.request import build_opener, ProxyHandler
ACCURACIES=(95,97,99,100)
BASE='http://127.0.0.1:24050'

@dataclass(frozen=True)
class Selection:
    path:str
    checksum:str
    mode:int
    mods:int
    combo:int
    title:str
    difficulty:str
    mod_text:str
    ranked:int
    @property
    def key(self):
        return self.path,self.checksum,self.mode,self.mods,self.combo

def selection(data):
    menu=data.get('menu',{})
    if menu.get('state')!=5 or menu.get('gameMode') not in (0,3):return None
    bm=menu.get('bm',{});file=bm.get('path',{}).get('file','')
    if not file.endswith('.osu') or not bm.get('md5'):return None
    songs=data.get('settings',{}).get('folders',{}).get('songs','')
    md=bm.get('metadata',{});mods=menu.get('mods',{})
    return Selection(str(Path(songs)/bm['path'].get('folder','')/file),bm['md5'],menu['gameMode'],
        int(mods.get('num',0)),int(bm.get('stats',{}).get('maxCombo',0)),
        f"{md.get('artist','')} - {md.get('title','')}",md.get('difficulty',''),mods.get('str') or 'NM',int(bm.get('rankedStatus',0)))

class Client:
    def __init__(self):self.opener=build_opener(ProxyHandler({}))
    def get(self,path):
        with self.opener.open(BASE+path,timeout=3) as response:return json.load(response)
    def current(self):return selection(self.get('/json'))
    def calculate(self,selected):
        data=self.get('/json');now=selection(data)
        if now is None or now.key!=selected.key:raise ValueError('Selection changed')
        values=tuple(data['menu']['pp'].get(str(a)) for a in ACCURACIES)
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 for v in values):raise ValueError('Invalid pp table')
        if values[-1]<=0:raise ValueError('Calculator not ready')
        return values
