"""One-click installer and quiet login supervisor for the bundled overlay."""
from pathlib import Path
import contextlib
import ctypes
import hashlib
import json
import logging
from logging.handlers import RotatingFileHandler
import os
import shutil
import subprocess
import sys
import time
from urllib.request import urlopen
ROOT=Path(__file__).resolve().parent
TITLE='osu! PP Overlay'
NO_WINDOW=getattr(subprocess,'CREATE_NO_WINDOW',0)

def message(text,error=False):
    ctypes.windll.user32.MessageBoxW(None,text,TITLE,0x10 if error else 0x40)

def startup_path():
    return Path(os.environ['APPDATA'])/'Microsoft'/'Windows'/'Start Menu'/'Programs'/'Startup'/'osu PP Overlay.vbs'

def register_startup(root):
    exe=root/'runtime'/'python'/'pythonw.exe'
    command=f'"{exe}" "{root / "launcher.py"}" --background'
    text='Set shell = CreateObject("WScript.Shell")\r\nshell.Run "'+command.replace('"','""')+'", 0, False\r\n'
    path=startup_path();path.parent.mkdir(parents=True,exist_ok=True)
    # UTF-16 is supported by Windows Script Host even for non-ASCII usernames.
    path.write_text(text,encoding='utf-16')

def verify(root):
    manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    for name,digest in manifest['files'].items():
        target=(root/name).resolve()
        if not target.is_relative_to(root.resolve()):raise RuntimeError('Invalid package path')
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest()!=digest:
            raise RuntimeError('Package verification failed: '+name)
    return manifest

def install():
    manifest=verify(ROOT)
    identity=hashlib.sha256((ROOT/'manifest.json').read_bytes()).hexdigest()[:12]
    base=Path(os.environ['LOCALAPPDATA'])/'osuPPOverlay'
    dest=base/('v5-'+identity)
    if not (dest/'installed.json').exists():
        dest.mkdir(parents=True,exist_ok=True)
        # Only ship files explicitly listed in the build manifest.
        for name in manifest['files']:
            target=dest/name;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/name,target)
        shutil.copy2(ROOT/'manifest.json',dest/'manifest.json')
        verify(dest)
        (dest/'installed.json').write_text(json.dumps({'version':5,'id':identity}),encoding='utf-8')
    register_startup(dest)
    subprocess.Popen([str(dest/'runtime'/'python'/'pythonw.exe'),str(dest/'launcher.py'),'--background'],cwd=dest,creationflags=NO_WINDOW)
    message('설치 및 자동 실행 등록을 완료했습니다.\n\nosu!stable을 실행하면 자동으로 표시됩니다.\nPython / Node.js는 별도 설치할 필요 없습니다.\n\n위치 조정: Ctrl + Shift + Space\n\n설치 위치:\n'+str(dest))

def assert_local_reader():
    # Never silently reconfigure somebody else's already running tosu instance.
    try:
        with urlopen('http://127.0.0.1:24050/',timeout=1):pass
    except OSError:return
    expected=str(ROOT/'runtime'/'tosu-4.26.2'/'tosu.exe').casefold()
    command="[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false); Get-Process -Name tosu -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Path"
    paths=subprocess.check_output(['powershell','-NoProfile','-Command',command],text=True,encoding='utf-8',creationflags=NO_WINDOW,timeout=15)
    if expected not in [p.strip().casefold() for p in paths.splitlines()]:
        raise RuntimeError('다른 tosu가 이미 실행 중입니다. 기존 tosu/오버레이를 종료한 뒤 이 패키지의 Start.cmd를 실행하거나 Windows에 다시 로그인해 주세요.')
    try:
        with urlopen('http://127.0.0.1:24051/health',timeout=1) as response:health=json.load(response)
    except OSError:return
    if health.get('root')!=str(ROOT):
        raise RuntimeError('다른 PP 서비스가 실행 중입니다. 기존 오버레이를 종료하거나 Windows에 다시 로그인해 주세요.')

def background():
    from ctypes import wintypes
    ctypes.windll.kernel32.CreateMutexW.restype=wintypes.HANDLE
    mutex=ctypes.windll.kernel32.CreateMutexW(None,False,'Local\\osuPPOverlayPortableV5')
    if ctypes.windll.kernel32.GetLastError()==183:return
    logger=logging.getLogger('startup');logger.setLevel(logging.INFO)
    logger.addHandler(RotatingFileHandler(ROOT/'startup.log',maxBytes=500000,backupCount=1,encoding='utf-8'))
    os.chdir(ROOT)
    os.environ['PATH']=str(ROOT/'runtime'/'node')+os.pathsep+os.environ.get('PATH','')
    from bootstrap import main
    from configure_ingame import configure
    try:
        assert_local_reader()
    except Exception as error:
        logger.exception('Conflicting reader');message(str(error),True);return
    # Keep startup output available even when pythonw has no console.
    with (ROOT/'launcher-output.log').open('a',encoding='utf-8',buffering=1) as output:
        with contextlib.redirect_stdout(output),contextlib.redirect_stderr(output):
            started=False;last_ensure=0
            while True:
                try:
                    if not started or time.monotonic()-last_ensure>60:
                        main();started=True;last_ensure=time.monotonic()
                    configure()
                except Exception:
                    logger.exception('Waiting for game / reader')
                time.sleep(2)
    ctypes.windll.kernel32.CloseHandle(mutex)

if __name__=='__main__':
    try:
        if '--check' in sys.argv:
            verify(ROOT)
            import ssl,ctypes,logging.handlers,http.server
            from portable_runtime import NODE
            subprocess.run([NODE,'--version'],check=True)
            print('PASS: manifest, bundled Python modules and bundled Node')
        elif '--background' in sys.argv:background()
        elif '--disable-startup' in sys.argv:
            path=startup_path()
            if path.exists() and str(ROOT) in path.read_text(encoding='utf-16'):
                path.unlink();message('이 패키지의 자동 실행을 해제했습니다.\n현재 실행 중인 오버레이는 Windows 로그아웃 시 종료됩니다.')
            else:message('이 패키지로 등록된 자동 실행 항목이 없습니다.')
        else:install()
    except Exception as error:
        message('설치를 완료하지 못했습니다.\n\n'+str(error),True)
        raise SystemExit(1)
