#!/usr/bin/env python3
"""Compile the semantic corpus as native callbacks; compare its fixed goldens.
The complete Shen distribution remains the primary gate.
"""
import argparse,ast,hashlib,json,pathlib,shutil,subprocess,sys,time
from native_codegen import Compiler,read_kl,quote
from native_build import run_compiler
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--cache',type=pathlib.Path);a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 module=ast.parse((ROOT/'scripts/test-runtime.py').read_text())
 cases=next(ast.literal_eval(n.value) for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='cases' for t in n.targets))
 work=pathlib.Path('/tmp/shen-koka-native-anf');work.mkdir(exist_ok=True)
 shutil.copytree(ROOT/'src/shen',work/'src/shen',dirs_exist_ok=True)
 gen=Compiler();plan=gen.write(work/'generated',[read_kl(source) for source,expected in cases.values()])
 lines=['import shen/values','import shen/world','import shen/machine','import shen/io','import std/os/env','import std/num/int32']
 lines += ['import '+m for m in plan['modules']]
 lines += ['fun run-case() {',' val w=new-world()',' prepare-native(w,%d)'%plan['code_count']]
 lines += [' '+m+'/install(w)' for m in plan['modules']]
 lines += [' match get-args() {']
 for name,entries in zip(cases,plan['entries']):
  lines+=['   ['+quote(name)+'] -> {']
  for code in entries:lines+=['     println(render(invoke(w,make-compiled(w,0,%d,[],[]),[])))'%code]
  lines+=['   }']
 lines+=['   _ -> throw("unknown native case")',' }','}','pub fun main() { try(run-case,fn(e) { println(e.message); process-exit(1.int32) }) }']
 (work/'program.kk').write_text('\n'.join(lines)+'\n')
 stage=work/'generated'
 command=['koka','-j1','-i'+str(work/'src'),'-i'+str(stage),'-O2','--builddir='+str(a.cache.resolve() if a.cache else pathlib.Path('/tmp/shen-koka-native-anf-cache')),'-o',str(work/'run'),str(work/'program.kk')]
 start=time.monotonic()
 print('Compiling '+str(plan['code_count'])+' native callbacks',flush=True)
 r=run_compiler(command,900)
 (out/'compile.log').write_text(r.stdout)
 record={'command':command,'compile_exit_code':r.returncode,'build_seconds':time.monotonic()-start,'cases':{}}
 if r.returncode==0:
  (work/'run').chmod(0o755);record['binary_sha256']=hashlib.sha256((work/'run').read_bytes()).hexdigest()
  for name,(source,expected) in cases.items():
   try:
    p=subprocess.run([str(work/'run'),name],capture_output=True,text=True,timeout=30)
    record['cases'][name]={'source':source,'expected':expected,'stdout':p.stdout,'stderr':p.stderr,'exit_code':p.returncode,'status':'PASS' if p.returncode==0 and p.stdout.strip()==expected else 'FAIL'}
   except subprocess.TimeoutExpired:record['cases'][name]={'status':'UNKNOWN','blocker':'30 second timeout'}
   except OSError as e:record['cases'][name]={'status':'UNKNOWN','blocker':str(e)}
 shutil.copytree(work/'generated',out/'generated');shutil.copytree(work/'src',out/'src');shutil.copy2(work/'program.kk',out/'program.kk')
 if r.returncode==0:shutil.copy2(work/'run',out/'run')
 (out/'report.json').write_text(json.dumps(record,indent=2)+'\n')
 print(json.dumps({'compile_exit':r.returncode,'counts':{s:sum(c['status']==s for c in record['cases'].values()) for s in ['PASS','FAIL','UNKNOWN']}}))
 return 0 if r.returncode==0 and all(c['status']=='PASS' for c in record['cases'].values()) else 1
if __name__=='__main__':sys.exit(main())
