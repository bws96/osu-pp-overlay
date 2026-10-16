"""First-run installer and launcher for the pinned official tosu release."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import time
from urllib.request import urlopen
import zipfile
from core import Client

ROOT = Path(__file__).resolve().parent
VERSION = '4.26.2'
URL = f'https://github.com/tosuapp/tosu/releases/download/v{VERSION}/tosu-windows-v{VERSION}.zip'
SHA256 = 'd34c2bfc495959fcc79ff01f10b7dc9aea77eb508ed23c8f0d0fb8342773faa3'


def install():
    destination = ROOT / 'runtime' / f'tosu-{VERSION}'
    marker = destination / '.verified.json'
    if marker.exists():
        record = json.loads(marker.read_text())
        exe = destination / record['exe']
        if exe.is_file() and hashlib.sha256(exe.read_bytes()).hexdigest() == record['exe_sha256']:
            return exe
        raise RuntimeError('tosu verification failed. Remove runtime folder and try again.')
    print(f'Downloading official tosu v{VERSION} (43 MB)...', flush=True)
    with urlopen(URL, timeout=120) as response:
        payload = response.read(150 * 1024 * 1024 + 1)
    if len(payload) > 150 * 1024 * 1024 or hashlib.sha256(payload).hexdigest() != SHA256:
        raise RuntimeError('Official release SHA256 mismatch; install stopped.')
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        base = destination.resolve()
        for info in archive.infolist():
            target = (base / info.filename).resolve()
            if not target.is_relative_to(base):
                raise RuntimeError('Invalid path in archive')
        archive.extractall(destination)
    candidates = list(destination.rglob('tosu.exe'))
    if len(candidates) != 1:
        raise RuntimeError('tosu.exe was not found uniquely in the official release.')
    exe = candidates[0]
    marker.write_text(json.dumps(dict(exe=str(exe.relative_to(destination)), exe_sha256=hashlib.sha256(exe.read_bytes()).hexdigest())))
    return exe


def ensure_personal_service():
    try:
        with urlopen('http://127.0.0.1:24051/health',timeout=2) as response:
            if json.load(response).get('app')=='osu-fc-personal':return
        raise RuntimeError('Port 24051 is occupied by another program')
    except __import__('urllib.error',fromlist=['URLError']).URLError:
        pass
    pythonw=Path(sys.executable).with_name('pythonw.exe')
    subprocess.Popen([str(pythonw if pythonw.exists() else Path(sys.executable)),str(ROOT/'personal_service.py')],cwd=ROOT,creationflags=subprocess.CREATE_NO_WINDOW)
    for _ in range(20):
        try:
            with urlopen('http://127.0.0.1:24051/health',timeout=1) as response:
                if json.load(response).get('app')=='osu-fc-personal':return
        except OSError:pass
        time.sleep(.2)
    raise RuntimeError('Personal record service did not start; see personal.log')


def main():
    from configure_ingame import prepare
    prepare()
    client = Client()
    try:
        with client.opener.open('http://127.0.0.1:24050/', timeout=2) as response:
            if response.status != 200:
                raise RuntimeError('Reader dashboard is not ready')
    except Exception:
        exe = install()
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
        log = (ROOT / 'tosu.log').open('ab')
        process = subprocess.Popen([str(exe)], cwd=exe.parent, stdout=log, stderr=log,
                                   startupinfo=startup, creationflags=subprocess.CREATE_NO_WINDOW)
        log.close()
        print('Waiting for tosu local API...', flush=True)
        for _ in range(80):
            if process.poll() is not None:
                raise RuntimeError('tosu exited. See tosu.log.')
            try:
                with client.opener.open('http://127.0.0.1:24050/', timeout=2) as response:
                    if response.status == 200:
                        break
            except Exception:
                pass
            time.sleep(0.25)
        else:
            raise RuntimeError('tosu startup timed out. See tosu.log.')
    from configure_ingame import configure
    configure()
    ensure_personal_service()
    print('Use osu! fullscreen as usual. No desktop window is required.')



if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'Launch failed: {error}', file=sys.stderr)
        print('Manual download: ' + URL, file=sys.stderr)
        sys.exit(1)

