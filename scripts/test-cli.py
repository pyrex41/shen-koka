#!/usr/bin/env python3
"""Observable CLI contracts; the complete Shen suite remains the primary gate."""
import argparse,hashlib,json,os,pathlib,shutil,subprocess,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
CASES={
 'string-output':(['eval','-e','(cn "foo" "bar")'],'foobar\n',0,None),
 'fail-sentinel':(['eval','-e','(trap-error (fail) (/. E unexpected))'],'shen.fail!\n',0,None),
 'ordered-actions':(['eval','-e','(set *cli-order* 1)','-e','(value *cli-order*)'],'1\n1\n',0,None),
 'multiple-forms':(['eval','-e','(set *cli-multi* 1) (+ (value *cli-multi*) 1)'],'2\n',0,None),
 'set-action':(['eval','--set','*cli-value*','9','--eval','(value *cli-value*)'],'9\n',0,None),
 'quiet-still-evaluates':(['eval','-q','-e','(do (write-byte 81 (stoutput)) 42)'],'Q',0,None),
 'script-no-echo':(['script','{script}'],'only-once\n',0,'(output "only-once~%")'),
 'script-argv':(['script','{script}','alpha','beta'],'argv-ok\n',0,'(if (= (tl (value *argv*)) ["alpha" "beta"]) (output "argv-ok~%") (simple-error "bad argv"))'),
 'script-error':(['script','{script}'],'shen-koka: boom\n',1,'(simple-error "boom")'),
 'invalid-option':(['eval','--bogus'],'shen-koka: Invalid eval argument: --bogus\n',1,None),
}
def main():
 argparse.ArgumentParser(description=__doc__).parse_args()
 report={'binary_sha256':None,'cases':{}}
 with tempfile.TemporaryDirectory(prefix='shen-cli-binary-') as binary_dir:
  binary=pathlib.Path(binary_dir)/'shen-koka';shutil.copy2(ROOT/'.build/shen-koka',binary)
  report['binary_sha256']=hashlib.sha256(binary.read_bytes()).hexdigest()
  for name,(args,expected,exit_code,source) in CASES.items():
   row={'args':args,'source':source,'expected_stdout':expected,'expected_exit_code':exit_code,'status':'UNKNOWN'}
   try:
    with tempfile.TemporaryDirectory(prefix='shen-cli-case-') as cwd:
     script=pathlib.Path(cwd)/'program.shen'
     if source is not None:script.write_text(source+'\n')
     command=[str(binary),*[str(script) if x=='{script}' else x for x in args]]
     p=subprocess.run(command,cwd=cwd,env={**os.environ,'SHEN_KOKA_ROOT':str(ROOT)},input='',capture_output=True,text=True,timeout=30)
    row.update(stdout=p.stdout,stderr=p.stderr,exit_code=p.returncode,status='PASS' if p.returncode==exit_code and p.stdout==expected else 'FAIL')
   except (OSError,subprocess.TimeoutExpired) as e:row['blocker']=str(e)
   report['cases'][name]=row
 report['counts']={s:sum(c['status']==s for c in report['cases'].values()) for s in ['PASS','FAIL','UNKNOWN']}
 print(json.dumps(report,indent=2))
 return 0 if report['counts']['PASS']==len(CASES) else 1
if __name__=='__main__':raise SystemExit(main())
