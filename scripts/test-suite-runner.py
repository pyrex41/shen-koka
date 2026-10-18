#!/usr/bin/env python3
import importlib.util,unittest
import json
from pathlib import Path
spec=importlib.util.spec_from_file_location('runner',Path(__file__).with_name('run-shen-suite.py'));r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
class Reports(unittest.TestCase):
 def check(self,text):
  cells=[{'status':'UNKNOWN'},{'status':'UNKNOWN'}]
  result=r.parse_canonical(text,{'groups':[{'name':'group','assertion_count':2}]},cells)
  return result,cells
 def test_complete(self):
  result,cells=self.check('group: a = b\npassed\ngroup: c = d\npassed\npassed ... 2\nfailed ... 0\npass rate ... 100%\n')
  self.assertTrue(result['complete_reports']);self.assertEqual([c['status'] for c in cells],['PASS','PASS'])
 def test_summary_is_not_an_assertion(self):
  result,cells=self.check('group: a = b\npassed\ngroup: c = d\npassed ... 2\nfailed ... 0\npass rate ... 100%\n')
  self.assertFalse(result['complete_reports']);self.assertEqual(cells[1]['status'],'UNKNOWN')
 def test_inconsistent_counters(self):
  result,_=self.check('group: a = b\npassed\ngroup: c = d\npassed\npassed ... 1\nfailed ... 1\npass rate ... 50%\n')
  self.assertFalse(result['complete_reports'])
 def test_failure(self):
  result,cells=self.check('group: a = b\npassed\ngroup: c = d\nfailed with error boom\nfailed; continue?\npassed ... 1\nfailed ... 1\npass rate ... 50%\n')
  self.assertFalse(result['complete_reports']);self.assertEqual(cells[1]['status'],'FAIL')
 def test_duplicate_run(self):
  text='group: a = b\npassed\ngroup: c = d\npassed\npassed ... 2\nfailed ... 0\npass rate ... 100%\n'
  self.assertFalse(self.check(text+text)[0]['complete_reports'])
 def test_unreached(self):
  self.assertEqual([x['status'] for x in self.check('boot failed')[1]],['UNKNOWN','UNKNOWN'])
 def test_official_431_denominator_keeps_source_derived_cells(self):
  lock=json.loads((Path(__file__).parents[1]/'comparison/shen-suite.lock.json').read_text())['canonical']
  identities={x['id']:x for x in json.loads((Path(__file__).parents[1]/'comparison/assertions.json').read_text())}
  cells=[{'id':f"{g['id']}/{i:03}",'status':'UNKNOWN'} for g in lock['groups'] for i in range(1,g['assertion_count']+1)]
  r.enrich_assertion_identities(cells,identities,canonical=True,canonical_groups=lock['groups'],source_commit=lock.get('source_commit'))
  self.assertEqual(len(cells),154)
  self.assertEqual(cells[2]['id'],'canonical/01/003')
  self.assertEqual(cells[2]['identity_source'],'comparison/shen-suite.lock.json')
  self.assertNotIn('expression',cells[0])
  self.assertEqual(cells[0]['group_name'],'S43.1 public functions')
  self.assertEqual(cells[-1]['id'],'canonical/40/003')
if __name__=='__main__':unittest.main()
