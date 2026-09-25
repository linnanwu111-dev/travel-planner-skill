import importlib.util,json,pathlib,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('planning',ROOT/'travel-planner/scripts/planning.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class HotelContractTests(unittest.TestCase):
 def setUp(self):
  self.p=json.loads((ROOT/'travel-planner/examples/planning-demo.json').read_text())
  pid=self.p['places'][0]['id']
  self.p['activities']=[{'id':'arrival','kind':'hotel','place_id':pid,'title':'酒店放行李','start':'2026-10-01T14:00:00+08:00','end':'2026-10-01T14:30:00+08:00'}, {'id':'return','kind':'stay','place_id':pid,'title':'返回酒店','start':'2026-10-01T22:00:00+08:00','end':'2026-10-01T23:00:00+08:00'}]
  self.p['transfers']=[]
  self.cost={'id':'hotel-cost','activity_id':'arrival','category':'住宿','unit':'间·晚','quantity':2,'low_cents':29000,'high_cents':29000,'paid_cents':0,'status':'reference','source_ids':['s-demo']}
  self.p['costs']=[self.cost]
 def test_misclassified_hotel_rejected(self):
  self.p['activities'][0]['kind']='place'
  with self.assertRaisesRegex(m.Invalid,'住宿费用必须关联hotel'):m.export(self.p)
 def test_lodging_on_return_rejected_even_with_arrival_cost(self):
  self.p['costs'].append({**self.cost,'id':'duplicate','activity_id':'return'})
  with self.assertRaisesRegex(m.Invalid,'住宿费用必须关联hotel'):m.validate(self.p)
 def test_missing_hotel_cost_rejected(self):
  self.p['costs']=[]
  with self.assertRaisesRegex(m.Invalid,'缺住宿费用'):m.validate(self.p)
 def test_unknown_price_is_explicit(self):
  self.cost.update(status='unknown',low_cents=None,high_cents=None)
  result=m.validate(self.p)
  self.assertEqual(result['unknown_cost_items'],1)
  self.assertEqual(result['known_low_cents'],0)
 def test_relink_preserves_price_and_counts_once(self):
  self.cost['activity_id']='return'
  with self.assertRaises(m.Invalid):m.export(self.p)
  self.cost['activity_id']='arrival'
  packet=m.export(self.p)
  self.assertEqual(packet['costs'],[self.cost])
  self.assertEqual(packet['budget_summary']['known_low_cents'],58000)
  self.assertEqual(packet['activities'][1]['kind'],'stay')
 def test_hotel_breakfast_not_reclassified(self):
  self.p['activities'][1]['kind']='meal'
  self.assertTrue(m.validate(self.p)['valid'])

if __name__=='__main__':unittest.main()
