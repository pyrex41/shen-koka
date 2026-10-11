#!/usr/bin/env python3
import importlib.util,unittest
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
class Extensions(unittest.TestCase):
 def check(self,text,names=('first','second')):
  cells=[{'name':name,'status':'UNKNOWN'} for name in names]
  result=r.parse_extensions(text,{'assertion_count':len(names)},cells)
  return result,cells
 def test_complete(self):
  self.assertTrue(self.check('ok - first\nok - second\npassed ... 2\nfailed ... 0\n')[0]['complete_reports'])
 def test_new_denominator(self):
  names=tuple('case '+str(i) for i in range(123))
  text=''.join('ok - '+name+'\n' for name in names)+'passed ... 123\nfailed ... 0\n'
  self.assertTrue(self.check(text,names)[0]['complete_reports'])
 def test_duplicate(self):
  self.assertFalse(self.check('ok - first\nok - first\npassed ... 2\nfailed ... 0\n')[0]['complete_reports'])
 def test_truncated(self):
  self.assertFalse(self.check('ok - first\npassed ... 2\nfailed ... 0\n')[0]['complete_reports'])
 def test_spoofed_skip(self):
  result,cells=self.check('ok - first\nSKIP - second\npassed ... 2\nfailed ... 0\n')
  self.assertFalse(result['complete_reports']);self.assertEqual(cells[1]['status'],'UNKNOWN')
 def test_failure_visible(self):
  result,cells=self.check('ok - first\nnot ok - second\npassed ... 1\nfailed ... 1\n')
  self.assertTrue(result['complete_reports']);self.assertEqual(cells[1]['status'],'FAIL')
 def test_wrong_counters(self):
  self.assertFalse(self.check('ok - first\nok - second\npassed ... 1\nfailed ... 1\n')[0]['complete_reports'])
if __name__=='__main__':unittest.main()
