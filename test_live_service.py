import unittest
from unittest.mock import patch
from live_service import snapshot,Live
DATA={'state':{'number':2},'beatmap':{'checksum':'abc','time':{'live':2000}},'play':{'mode':{'number':0},'mods':{'number':64},'pp':{'current':123.4},'hits':{'300':20,'100':1,'0':2},'combo':{'current':3,'max':10}},'folders':{'songs':r'C:\osu-test\Songs','beatmap':'folder'},'files':{'beatmap':'map.osu'}}
class Tests(unittest.TestCase):
 def test_request_preserves_mods_misses_and_combo_loss(self):
  identity,request,current=snapshot(DATA)
  self.assertEqual(identity,{'checksum':'abc','mode':0,'mods':64})
  self.assertEqual(request['hits']['0'],2);self.assertEqual(request['combo'],3);self.assertEqual(request['maxCombo'],10)
  self.assertEqual(current,123.4)
 def test_selection_and_failed_play_are_not_live(self):
  self.assertIsNone(snapshot({**DATA,'state':{'number':5}}))
  self.assertIsNone(snapshot({**DATA,'play':{**DATA['play'],'failed':True}}))
 def test_backend_stale_state_is_never_returned(self):
  live=Live(lambda:None);live.set({'status':'ok','current':1,'forecast':2,'_updated':10})
  with patch('live_service.time.monotonic',return_value=10.5):self.assertEqual(live.get()['forecast'],2)
  with patch('live_service.time.monotonic',return_value=13):self.assertEqual(live.get(),{'status':'idle'})
if __name__=='__main__':unittest.main()
