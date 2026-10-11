#!/usr/bin/env python3
"""Compile every pinned kernel form, preserving its original load-time order."""
import argparse,hashlib,json,pathlib,shutil,subprocess,sys,time
from native_codegen import Compiler,read_kl
from native_build import run_compiler
ROOT=pathlib.Path(__file__).resolve().parents[1]
MODULES=['yacc','core','load','prolog','reader','sequent','sys','toplevel','track','writer','backend','macros','declarations','t-star','types','extension-features','extension-expand-dynamic','extension-launcher']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 sys.setrecursionlimit(10000)
 p=argparse.ArgumentParser();p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--cache',type=pathlib.Path);a=p.parse_args()
 out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 # Refuse drift between the ordinary loader and the native form order.
 literal='['+','.join(json.dumps(n) for n in MODULES)+']'
 if literal not in (ROOT/'src/shen/boot.kk').read_text():raise ValueError('kernel module order differs from interpreter')
 files=[ROOT/'kernel/klambda'/(n+'.kl') for n in MODULES]
 plan=Compiler().write(out/'generated',[read_kl(f.read_bytes().decode()) for f in files])
 shutil.copytree(ROOT/'src/shen',out/'src/shen');shutil.copytree(ROOT/'compat',out/'compat')
 main=(ROOT/'src/shen/main.kk').read_text()
 old='boot(w,get-env-value("SHEN_KOKA_ROOT").default("."))'
 if main.count(old)!=3:raise ValueError('CLI boot call sites changed')
 main=main.replace(old,'boot-compiled(w)').replace('shen-koka 0.0.1 experimental;', 'shen-koka 0.0.1 experimental native-kernel;')
 lines=['import '+m for m in plan['modules']]+[main,'fun boot-compiled(w:world) {',' initialize-platform(w)',' prepare-native(w,%d)'%plan['code_count']]
 lines+=[' '+m+'/install(w)' for m in plan['modules']]
 for entries in plan['entries']:
  for code in entries:lines.append(' invoke(w,make-compiled(w,0,%d,[],[]),[]);'%code)
 lines+=[' load-compat(w,get-env-value("SHEN_KOKA_ROOT").default("."))','}']
 (out/'program.kk').write_text('\n'.join(lines)+'\n')
 stage=pathlib.Path('/tmp/shen-koka-native-anf');stage.mkdir(exist_ok=True)
 shutil.copytree(out/'src',stage/'src',dirs_exist_ok=True);shutil.copytree(out/'generated',stage/'generated',dirs_exist_ok=True);shutil.copy2(out/'program.kk',stage/'program.kk')
 command=['koka','-j1','-i'+str(stage/'src'),'-i'+str(stage/'generated'),'-O2','--builddir='+str(a.cache.resolve() if a.cache else pathlib.Path('/tmp/shen-koka-native-anf-cache')),'-o',str(stage/'run'),str(stage/'program.kk')]
 start=time.monotonic();print('Compiling '+str(plan['code_count'])+' native kernel callbacks',flush=True)
 r=run_compiler(command,1800)
 (out/'compile.log').write_text(r.stdout)
 if r.returncode==0:shutil.copy2(stage/'run',out/'native')
 record={'direct_kl_compiler':True,'kernel_forms':sum(map(len,plan['entries'])),'native_callbacks':plan['code_count'],'kernel_sha256':{f.name:sha(f) for f in files},'generator_sha256':sha(ROOT/'scripts/native_codegen.py'),'runtime_sources':{str(f.relative_to(out/'src')):sha(f) for f in (out/'src').rglob('*') if f.is_file()},'command':command,'exit_code':r.returncode,'seconds':time.monotonic()-start}
 if r.returncode==0:
  (out/'native').chmod(0o755);record['binary_sha256']=sha(out/'native')
  (out/'run').write_text('#!/usr/bin/env bash\nset -euo pipefail\nroot=$(cd "$(dirname "$0")" && pwd)\nexport SHEN_KOKA_ROOT="$root"\nexec "$root/native" "$@"\n');(out/'run').chmod(0o755)
 (out/'build.json').write_text(json.dumps(record,indent=2)+'\n');return r.returncode
if __name__=='__main__':sys.exit(main())
