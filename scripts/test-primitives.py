#!/usr/bin/env python3
"""Required primitive inventory, observable goldens, and wrong-arity rejection."""
import hashlib,json,pathlib,re,shutil,subprocess,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=json.loads((ROOT/'comparison/primitives.json').read_text())
source=(ROOT/'src/shen/machine.kk').read_text()
implemented=set(re.findall(r'^\s*\("([^"]+)",',source,re.M))
expected=set(spec['required_primitives'])|set(spec['host_extensions'])
covered={n for c in spec['cases'] for n in c['covers']}
errors=[]
actual_arities={name:(0 if not args.strip() else len(args.split(','))) for name,args in re.findall(r'^\s*\("([^"]+)",\[(.*?)\]\)',source,re.M)}
for name,arity in spec['required_primitives'].items():
 if actual_arities.get(name)!=arity:errors.append({'arity_mismatch':name,'expected':arity,'actual':actual_arities.get(name)})
if implemented!=expected:errors.append({'inventory_mismatch':{'missing':sorted(expected-implemented),'extra':sorted(implemented-expected)}})
if covered!=set(spec['required_primitives']):errors.append({'golden_coverage_mismatch':True})
cases=list(spec['cases'])
for name,arity in {**spec['required_primitives'],**spec['machine_dispatch']}.items():
 cases.append({'id':'arity/'+name,'source':'(trap-error ('+name+' '+' '.join(['0']*(arity+1))+') (lambda E caught))','expected':'caught'})
cases += [
 {'id':'dispatch/eval-kl','source':'(eval-kl (cons + (cons 20 (cons 22 ()))))','expected':'42'},
 {'id':'dispatch/thaw','source':'(thaw (freeze 42))','expected':'42'}]
report={'inventory_errors':errors,'denominator':len(cases),'cases':{}}
with tempfile.TemporaryDirectory(prefix='shen-primitives-') as tmp:
 binary=pathlib.Path(tmp)/'run';shutil.copy2(ROOT/'.build/shen-koka',binary)
 report['binary_sha256']=hashlib.sha256(binary.read_bytes()).hexdigest()
 for case in cases:
  row=dict(case,status='UNKNOWN')
  try:
   with tempfile.TemporaryDirectory(prefix='shen-primitive-case-') as cwd:
    path=pathlib.Path(cwd);(path/'input.bin').write_bytes(bytes([65,0,255]))
    p=subprocess.run([str(binary),'kl','-e',case['source']],cwd=cwd,capture_output=True,text=True,timeout=30)
    row.update(stdout=p.stdout,stderr=p.stderr,exit_code=p.returncode)
    ok=p.returncode==0 and p.stdout.strip()==case['expected']
    if 'write-byte' in case.get('covers',[]):
     raw=(path/'output.bin').read_bytes();row['file_hex']=raw.hex();ok &= raw==bytes([255])
    row['status']='PASS' if ok else 'FAIL'
  except (OSError,subprocess.TimeoutExpired) as e:row['blocker']=str(e)
  report['cases'][case['id']]=row
report['counts']={s:sum(c['status']==s for c in report['cases'].values()) for s in ['PASS','FAIL','UNKNOWN']}
report['status']='PASS' if not errors and report['counts']['PASS']==report['denominator'] else 'FAIL'
print(json.dumps(report,indent=2))
raise SystemExit(0 if report['status']=='PASS' else 1)
