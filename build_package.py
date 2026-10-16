"""Build a clean offline release from a prepared, dedicated runtime directory."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parent
SOURCES=['bootstrap.py','configure_ingame.py','core.py','personal_service.py','local_scores.py',
 'live_service.py','live_calculator.cjs','record_calculator.cjs','account_aliases.json',
 'portable_runtime.py','layout.py','launcher.py','Install.cmd','Start.cmd','DisableAutoStart.cmd',
 'README.md','THIRD-PARTY.txt','NODE-LICENSE.txt','TOSU-LICENSE.txt','GPL-3.0.txt']
ENV='''ENABLE_AUTOUPDATE=false
OPEN_DASHBOARD_ON_STARTUP=false
CALCULATE_PP=true
ENABLE_INGAME_OVERLAY=true
ENABLE_KEY_OVERLAY=false
SERVER_IP=127.0.0.1
SERVER_PORT=24050
ALLOWED_IPS=127.0.0.1,localhost,absolute
INGAME_OVERLAY_KEYBIND=Control + Shift + Space
'''

def build(runtime,output):
    runtime=runtime.resolve();output=output.resolve();output.mkdir(parents=True,exist_ok=True)
    required=['python/python.exe','python/pythonw.exe','python/python311.dll','python/python311.zip',
              'python/python311._pth','python/LICENSE.txt','node/node.exe',
              'tosu-4.26.2/tosu.exe','tosu-4.26.2/.verified.json',
              'tosu-4.26.2/game-overlay/tosu-ingame-overlay.exe']
    for name in required:
        if not (runtime/name).is_file():raise RuntimeError('Missing prepared runtime: '+name)
    if not any(x.strip()==r'..\..' for x in (runtime/'python/python311._pth').read_text().splitlines()):
        raise RuntimeError('Portable Python must include ..\\.. in python311._pth')
    marker=json.loads((runtime/'tosu-4.26.2/.verified.json').read_text())
    if marker['exe']!='tosu.exe' or hashlib.sha256((runtime/'tosu-4.26.2/tosu.exe').read_bytes()).hexdigest()!=marker['exe_sha256']:
        raise RuntimeError('Bundled tosu integrity check failed')
    with tempfile.TemporaryDirectory(prefix='osu-release-',dir=output) as temp:
        stage=Path(temp)/'osu-pp-overlay';stage.mkdir()
        for name in SOURCES:shutil.copy2(ROOT/name,stage/name)
        # Never publish local aliases, logs, scores, profiles or cached app state.
        (stage/'account_aliases.json').write_text('{}\n',encoding='utf-8')
        for folder in ['counter','live_counter']:
            shutil.copytree(ROOT/folder,stage/folder,ignore=shutil.ignore_patterns('__pycache__','*.log'))
        for name in ['python','node']:
            dest=stage/'runtime'/name;dest.mkdir(parents=True)
            for p in (runtime/name).iterdir():
                if p.is_file() and (p.suffix.lower() in ('.exe','.dll','.zip','._pth') or p.name=='LICENSE.txt'):
                    shutil.copy2(p,dest/p.name)
            if name=='python':
                dlls=dest/'DLLs';dlls.mkdir()
                for p in (runtime/name/'DLLs').iterdir():
                    if p.is_file() and p.suffix.lower() in ('.pyd','.dll'):shutil.copy2(p,dlls/p.name)
        tosu=stage/'runtime'/'tosu-4.26.2';tosu.mkdir()
        for name in ['tosu.exe','.verified.json']:shutil.copy2(runtime/'tosu-4.26.2'/name,tosu/name)
        shutil.copytree(runtime/'tosu-4.26.2'/'game-overlay',tosu/'game-overlay',
            ignore=shutil.ignore_patterns('logs','settings','Cache','GPUCache','*.log'))
        (tosu/'tosu.env').write_text(ENV,encoding='ascii')
        files=sorted(p for p in stage.rglob('*') if p.is_file())
        manifest={'version':5,'platform':'windows-x64','files':{p.relative_to(stage).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
        (stage/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        archive=output/'osu-pp-overlay-oneclick-v5.zip'
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for p in files+[stage/'manifest.json']:z.write(p,'osu-pp-overlay/'+p.relative_to(stage).as_posix())
        digest=hashlib.sha256(archive.read_bytes()).hexdigest()
        (output/'osu-pp-overlay-oneclick-v5.sha256.txt').write_text(digest+'  '+archive.name+'\n',encoding='ascii')
        (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        print(f'Built {archive} ({archive.stat().st_size/1024**2:.1f} MiB)')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-dir',type=Path,default=ROOT/'runtime')
    parser.add_argument('--output-dir',type=Path,default=ROOT/'dist')
    args=parser.parse_args();build(args.runtime_dir,args.output_dir)
