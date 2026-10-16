import json,struct,unittest
from pathlib import Path
from local_scores import parse_scores
from personal_service import Records

def string(value):
 raw=value.encode();return b'\x0b'+bytes([len(raw)])+raw if raw else b'\x00'
def fixture(mode=0,mods=64):
 score=struct.pack('<Bi',mode,20260924)+string('hash')+string('Player')+string('replay')
 score+=struct.pack('<6HiHBi',547,6,0,124,6,0,13080002,704,1,mods)
 score+=string('')+struct.pack('<qiq',637632068181175175,-1,3795191124)
 if mods&(1<<23):score+=struct.pack('<d',.5)
 return struct.pack('<ii',20260924,1)+string('hash')+struct.pack('<i',1)+score
class Tests(unittest.TestCase):
 def test_decodes_actual_score_fields(self):
  r=parse_scores(fixture())['hash'][0]
  self.assertEqual((r['name'],r['great'],r['ok'],r['combo'],r['mods'],r['score_id']),('Player',547,6,704,64,3795191124))
 def test_mania_and_target_practice_alignment(self):
  self.assertEqual(parse_scores(fixture(3))['hash'][0]['perfects'],124)
  self.assertEqual(parse_scores(fixture(mods=1<<23))['hash'][0]['mods'],1<<23)
 def test_partial_write_is_rejected(self):
  for drop in (1,8,30):
   with self.assertRaises((ValueError,struct.error)):parse_scores(fixture()[:-drop])
 def test_foreign_result_is_not_added(self):
  records=Records()
  class Client:
   def get(self,path):return {'resultsScreen':{'playerName':'other'}}
  records.capture_result(Client(),{'menu':{'state':7}},'Player')
  self.assertEqual(records.sessions,{})
 def test_new_session_record_is_collected_once(self):
  records=Records();data={'menu':{'state':7,'bm':{'md5':'hash'}}}
  class Client:
   def get(self,path):return {'resultsScreen':{'playerName':'Player','mode':{'number':0},'score':13080002,'maxCombo':704,'mods':{'number':64},'hits':{'300':547,'100':6,'0':0}}}
  records.capture_result(Client(),data,'Player');records.capture_result(Client(),data,'Player')
  self.assertEqual(len(records.sessions['hash']),1)
  self.assertEqual(records.sessions['hash'][0]['great'],547)
if __name__=='__main__':unittest.main()
