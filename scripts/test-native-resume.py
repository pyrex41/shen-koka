#!/usr/bin/env python3
"""Reject stale native compiler checkpoints and always rerun the final link."""
import argparse,copy,hashlib,json,pathlib
from native_build import validated_resume_prefix
p=argparse.ArgumentParser();p.add_argument('build',type=pathlib.Path);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
r=json.loads(a.build.read_text());expected=0
for step in r['steps'][:-1]:
    if step['exit_code']!=0:break
    expected+=1
# An incomplete record's last step may itself be a completed library.
if len(r['steps'])<len(r['commands']) and r['steps'] and r['steps'][-1]['exit_code']==0:expected+=1
checks={'successful-prefix':len(validated_resume_prefix(r,r))==expected}
for key in ['kernel_sha256','generator_sha256','flake_lock_sha256','compat_sha256','runtime_sources','generated_sources','commands']:
    bad=copy.deepcopy(r);bad[key]=None
    try:validated_resume_prefix(bad,r);checks[key]=False
    except ValueError:checks[key]=True
bad=copy.deepcopy(r);bad['steps'][0]['argv']=[]
try:validated_resume_prefix(bad,r);checks['step-command']=False
except ValueError:checks['step-command']=True
full=copy.deepcopy(r);full['steps']=[{'argv':c,'exit_code':0} for c in r['commands']]
checks['always-relink']=len(validated_resume_prefix(full,r))==len(r['commands'])-1
record={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'expected_prefix':expected,'input_sha256':hashlib.sha256(a.build.read_bytes()).hexdigest(),'helper_sha256':hashlib.sha256(pathlib.Path(__file__).with_name('native_build.py').read_bytes()).hexdigest()}
a.output.write_text(json.dumps(record,indent=2)+'\n');print(record['status']);raise SystemExit(0 if all(checks.values()) else 1)
