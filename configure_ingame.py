"""Install the two native counters, retaining user position changes."""
import json
from pathlib import Path
import shutil
from urllib.request import Request
from core import Client
from layout import resolution,fit
ROOT=Path(__file__).resolve().parent
TOSU=ROOT/'runtime'/'tosu-4.26.2'

def prepare():
    for source,folder in [('counter','fc-estimates'),('live_counter','live-estimates')]:
        target=TOSU/'static'/folder;target.mkdir(parents=True,exist_ok=True)
        for p in (ROOT/source).iterdir():
            if p.is_file():shutil.copy2(p,target/p.name)

def configure():
    c=Client()
    original=c.get('/api/counters/settings/__ingame__').get('values',{})
    settings=json.loads(json.dumps(original))
    if not settings.get('profiles'):
        settings={'obs_profile':'default','ingame_profile':'default','profiles':[{'id':'default','name':'default','overlays':settings.get('overlays',[])}]}
    profile=next((p for p in settings['profiles'] if p['id']==settings.get('ingame_profile')),settings['profiles'][0])
    settings['ingame_profile']=profile['id']
    overlays=profile.setdefault('overlays',[])
    try:size=resolution(c.get('/json/v2'))
    except Exception:size=None
    if size is None:
        # Wait for actual osu resolution instead of saving this PC's desktop resolution.
        return None
    for folder,live,z in [('fc-estimates',False,20),('live-estimates',True,21)]:
        item=next((o for o in overlays if o.get('folderName')==folder),None)
        if item is None:
            item=dict(id=folder+'-portable-v5',folderName=folder,url='tosu://server/'+folder+'/?v=5',_enabled=True,_settings=False,z_index=z)
            overlays.append(item)
        fit(item,*size,live=live)
    if settings!=original:
        req=Request('http://127.0.0.1:24050/api/counters/settings/__ingame__',data=json.dumps(settings).encode(),headers={'Content-Type':'application/json'},method='POST')
        with c.opener.open(req,timeout=5) as response:
            result=json.load(response)
            if result.get('result')!='success':raise RuntimeError(result)
    return size
