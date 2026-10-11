#!/usr/bin/env python3
import hashlib, importlib.util, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('inventory',ROOT/'scripts/inventory-assertions.py')
i=importlib.util.module_from_spec(spec);spec.loader.exec_module(i)
class Inventory(unittest.TestCase):
 def test_historical_identities(self):
  actual=i.inventory()
  expected=json.loads((ROOT/'comparison/assertions.json').read_text())
  self.assertEqual(len(actual),142)
  for a,b in zip(actual,expected):
   self.assertEqual({k:a[k] for k in b},b)
 def test_new_profile(self):
  lock=ROOT/'comparison/shen42.2-suite.lock.json'
  dist=ROOT/'vendor/ShenOSKernel-42.2'
  actual=i.inventory(lock,dist)
  self.assertEqual(len(actual),266)
  self.assertEqual(actual,json.loads((ROOT/'comparison/shen42.2-assertions.json').read_text()))
  self.assertEqual(len({x['id'] for x in actual}),266)
  self.assertEqual(len({x['name'] for x in actual if 'name' in x}),123)
 def test_pristine_distribution(self):
  lock=json.loads((ROOT/'comparison/shen42.2-source.lock.json').read_text())
  dist=ROOT/'vendor/ShenOSKernel-42.2'
  files={str(p.relative_to(dist)):hashlib.sha256(p.read_bytes()).hexdigest() for p in dist.rglob('*') if p.is_file()}
  self.assertEqual(files,lock['sha256_by_file'])
 def test_nested_forms(self):
  nodes=i.forms('(let A 1 (do (extension-tests.assert-equal "first" A 1) (extension-tests.assert-error "second" (freeze boom))))')
  assertions=[x for x in i.walk(nodes) if x['children'] and x['children'][0]['text'].startswith('extension-tests.assert-')]
  self.assertEqual(len(assertions),2)
if __name__=='__main__': unittest.main()
