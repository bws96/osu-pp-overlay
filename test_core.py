import copy
import unittest
from unittest.mock import patch
from core import Client,selection
DATA={'settings':{'folders':{'songs':r'C:\osu-test\Songs'}},'menu':{'state':5,'gameMode':0,'mods':{'num':64,'str':'DT'},'bm':{'md5':'a','rankedStatus':4,'path':{'folder':'test','file':'test.osu'},'stats':{'maxCombo':704},'metadata':{'title':'test'}},'pp':{'95':442.42,'97':473.71,'99':527.81,'100':565.68}}}
class Tests(unittest.TestCase):
 def test_uses_current_tosu_table_without_legacy_calculator(self):
  c=Client()
  with patch.object(c,'get',return_value=DATA):self.assertEqual(c.calculate(selection(DATA)),(442.42,473.71,527.81,565.68))
 def test_mod_switch_rejects_stale_selection(self):
  changed=copy.deepcopy(DATA);changed['menu']['mods']['num']=0
  c=Client()
  with patch.object(c,'get',return_value=changed):
   with self.assertRaises(ValueError):c.calculate(selection(DATA))
 def test_gameplay_and_unsupported_modes_hidden(self):
  changed=copy.deepcopy(DATA);changed['menu']['state']=2
  self.assertIsNone(selection(changed))
  changed['menu']['state']=5;changed['menu']['gameMode']=1
  self.assertIsNone(selection(changed))
 def test_mania_selection_and_mods_preserved(self):
  changed=copy.deepcopy(DATA);changed['menu']['gameMode']=3;changed['menu']['mods']={'num':32768,'str':'4K'}
  self.assertEqual(selection(changed).mode,3);self.assertEqual(selection(changed).mods,32768)
 def test_missing_negative_and_nonfinite_pp_rejected(self):
  for bad in (None,-1,True,float('nan'),float('inf')):
   changed=copy.deepcopy(DATA);changed['menu']['pp']['99']=bad
   c=Client()
   with patch.object(c,'get',return_value=changed):
    with self.assertRaises(ValueError):c.calculate(selection(changed))
if __name__=='__main__':unittest.main()
