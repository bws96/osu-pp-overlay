import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import launcher
from layout import fit,resolution

class LayoutTests(unittest.TestCase):
    def test_resolutions(self):
        for w,h in [(1280,720),(1920,1080),(2560,1440),(3840,2160),(1024,768),(3440,1440),(768,1024)]:
            for live in [False,True]:
                item={};fit(item,w,h,live)
                self.assertGreaterEqual(item['left'],0);self.assertGreaterEqual(item['top'],0)
                self.assertLessEqual(item['left']+item['width']*item['scale'],w+1)
                self.assertLessEqual(item['top']+item['height']*item['scale'],h+1)
    def test_manual_edit_and_resize(self):
        item={};fit(item,2560,1440);item['left']=700;item['top']=95
        before=copy.deepcopy(item);fit(item,2560,1440);self.assertEqual(item,before)
        fit(item,1920,1080);self.assertEqual(item['left'],525);self.assertEqual(item['top'],71)
        fit(item,2560,1440);self.assertEqual(item['left'],700)
    def test_live_right_anchor(self):
        item={};fit(item,2560,1440,True);fit(item,3440,1440,True)
        self.assertEqual(item['left']+item['width']*item['scale'],3440)
    def test_missing_resolution(self):
        self.assertIsNone(resolution({}))
        self.assertIsNone(resolution({'settings':{'resolution':{'fullscreen':True,'widthFullscreen':0,'heightFullscreen':0}}}))
        self.assertEqual(resolution({'settings':{'resolution':{'fullscreen':False,'width':1600,'height':900,'widthFullscreen':2560,'heightFullscreen':1440}}}),(1600,900))

class InstallTests(unittest.TestCase):
    def test_install_copy_and_startup_unicode(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);source=base/'source';source.mkdir()
            (source/'launcher.py').write_text('example',encoding='utf-8')
            files={'launcher.py':hashlib.sha256(b'example').hexdigest()}
            (source/'manifest.json').write_text(json.dumps({'files':files}),encoding='utf-8')
            target=base/'local';appdata=base/'user space \uac00\ub098'
            with patch.object(launcher,'ROOT',source),patch.dict(os.environ,{'LOCALAPPDATA':str(target),'APPDATA':str(appdata)}),patch.object(launcher.subprocess,'Popen') as popen,patch.object(launcher,'message'):
                launcher.install()
                dest=next((target/'osuPPOverlay').glob('v5-*'))
                self.assertEqual((dest/'launcher.py').read_text(),'example')
                startup=launcher.startup_path()
                text=startup.read_text(encoding='utf-16')
                self.assertIn(str(dest/'runtime'/'python'/'pythonw.exe'),text)
                self.assertIn('--background',text);self.assertEqual(popen.call_count,1)
                launcher.install();self.assertEqual(popen.call_count,2)
    def test_tampered_or_escaping_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'manifest.json').write_text(json.dumps({'files':{'../escape':'x'}}))
            with self.assertRaisesRegex(RuntimeError,'Invalid package path'):launcher.verify(root)
            (root/'x').write_bytes(b'bad')
            (root/'manifest.json').write_text(json.dumps({'files':{'x':'0'}}))
            with self.assertRaisesRegex(RuntimeError,'verification failed'):launcher.verify(root)

if __name__=='__main__':unittest.main()
