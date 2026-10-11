#!/usr/bin/env python3
"""Compile every pinned kernel form, preserving its original load-time order."""
import argparse,hashlib,json,pathlib,shutil,subprocess,sys,time
from native_codegen import Compiler,read_kl
from native_build import run_compilation_steps,serial_native_build,artifact_notices,sync_sources,validated_resume_prefix
ROOT=pathlib.Path(__file__).resolve().parents[1]
MODULES=['yacc','core','load','prolog','reader','sequent','sys','toplevel','track','writer','backend','macros','declarations','t-star','types','extension-features','extension-expand-dynamic','extension-launcher']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
@serial_native_build
def main():
 sys.setrecursionlimit(10000)
 p=argparse.ArgumentParser();p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--cache',type=pathlib.Path);p.add_argument('--resume',type=pathlib.Path,help='reuse an identical successful library prefix; always relink');p.add_argument('--debug',action='store_true',help='retain debug information');p.add_argument('--timeout',type=float,default=1800);p.add_argument('--module-size',type=int,default=16);a=p.parse_args()
 out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);artifact_notices(out)
 for name in ['build-native-kernel.py','native_build.py']:shutil.copy2(ROOT/'scripts'/name,out/name)
 generator_snapshot=(ROOT/'scripts/native_codegen.py').read_bytes();(out/'native_codegen.py').write_bytes(generator_snapshot)
 # Refuse drift between the ordinary loader and the native form order.
 literal='['+','.join(json.dumps(n) for n in MODULES)+']'
 if literal not in (ROOT/'src/shen/boot.kk').read_text():raise ValueError('kernel module order differs from interpreter')
 files=[ROOT/'kernel/klambda'/(n+'.kl') for n in MODULES]
 plan=Compiler().write(out/'generated',[read_kl(f.read_bytes().decode()) for f in files],module_size=a.module_size)
 # Explicit source roots are always reparsed by Koka. Import each batch through
 # a tiny root so completed modules can be reused on a bounded retry.
 batches=[]
 for i,module in enumerate(plan['modules']):
  batch='klbatch'+str(i);batches.append(batch)
  (out/'generated'/(batch+'.kk')).write_text('module '+batch+'\nimport '+module+'\npub inline fun batch-size(): int { '+module+'/callback-count() }\n')
 shutil.copytree(ROOT/'src/shen',out/'src/shen');shutil.copytree(ROOT/'compat',out/'compat')
 main=(ROOT/'src/shen/main.kk').read_text()
 old='boot(w,get-env-value("SHEN_KOKA_ROOT").default("."))'
 if main.count(old)!=3:raise ValueError('CLI boot call sites changed')
 main=main.replace(old,'boot-compiled(w)').replace('shen-koka 0.0.1 experimental;', 'shen-koka 0.0.1 experimental native-kernel;')
 lines=['import '+m for m in plan['modules']]+[main,'fun boot-compiled(w:world) {',' initialize-platform(w)',' prepare-native(w,%d)'%plan['code_count']]
 lines+=[' '+m+'/install(w)' for m in plan['modules']]
 # A loop preserves form order without creating one enormous CPS boot body.
 entries=[code for group in plan['entries'] for code in group]
 lines.append(' ['+','.join(map(str,entries))+'].foreach(fn(code) { invoke(w,make-compiled(w,0,code,[],[]),[]); () })')
 lines+=[' load-compat(w,get-env-value("SHEN_KOKA_ROOT").default("."))','}']
 (out/'program.kk').write_text('\n'.join(lines)+'\n')
 stage=pathlib.Path('/tmp/shen-koka-native-anf');stage.mkdir(exist_ok=True)
 sync_sources(out/'src',stage/'src');sync_sources(out/'generated',stage/'generated');shutil.copy2(out/'program.kk',stage/'program.kk')
 common=['koka','-j1','-i'+str(stage/'src'),'-i'+str(stage/'generated'),'-O2']+([] if a.debug else ['--no-debug'])+['--builddir='+str(a.cache.resolve() if a.cache else pathlib.Path('/tmp/shen-koka-native-anf-cache'))]
 commands=[common+['--library',str(stage/'generated'/(m+'.kk'))] for m in batches]
 commands.append(common+['-o',str(stage/'run'),str(stage/'program.kk')])
 identity={'kernel_sha256':{f.name:sha(f) for f in files},'generator_sha256':sha(out/'native_codegen.py'),'flake_lock_sha256':sha(ROOT/'flake.lock'),'compat_sha256':{str(f.relative_to(out/'compat')):sha(f) for f in (out/'compat').rglob('*') if f.is_file()},'runtime_sources':{str(f.relative_to(out/'src')):sha(f) for f in (out/'src').rglob('*') if f.is_file()},'generated_sources':{str(f.relative_to(out)):sha(f) for f in [out/'program.kk',*sorted((out/'generated').glob('*.kk'))]},'commands':commands}
 prefix=[];resume=None
 if a.resume:
  prior=a.resume.resolve();prior=prior/'build.json' if prior.is_dir() else prior
  prefix=validated_resume_prefix(json.loads(prior.read_text()),identity)
  resume={'build_json':str(prior),'sha256':sha(prior),'reused_library_steps':len(prefix)}
  print('Reusing '+str(len(prefix))+' validated library steps; final imports will be checked by Koka',flush=True)
 start=time.monotonic();print('Compiling '+str(plan['code_count'])+' native kernel callbacks',flush=True)
 r=run_compilation_steps(commands[len(prefix):],a.timeout,output=out)
 (out/'compile.log').write_text(r.stdout)
 if r.returncode==0:shutil.copy2(stage/'run',out/'native')
 record={'direct_kl_compiler':True,'kernel_forms':sum(map(len,plan['entries'])),'native_callbacks':plan['code_count'],'module_size':a.module_size,'kernel_sha256':{f.name:sha(f) for f in files},'generator_sha256':sha(out/'native_codegen.py'),'flake_lock_sha256':sha(ROOT/'flake.lock'),'compat_sha256':{str(f.relative_to(out/'compat')):sha(f) for f in (out/'compat').rglob('*') if f.is_file()},'runtime_sources':{str(f.relative_to(out/'src')):sha(f) for f in (out/'src').rglob('*') if f.is_file()},'commands':commands,'steps':[dict(step,reused_from=resume['sha256']) for step in prefix]+r.steps,'resume':resume,'debug_info':a.debug,'timeout_seconds':a.timeout,'exit_code':r.returncode,'seconds':time.monotonic()-start}
 record['generated_sources']={str(f.relative_to(out)):sha(f) for f in [out/'program.kk',*sorted((out/'generated').glob('*.kk'))]}
 record['builder_sources']={name:sha(out/name) for name in ['build-native-kernel.py','native_build.py']}
 if r.returncode==0:
  (out/'native').chmod(0o755);record['binary_sha256']=sha(out/'native')
  (out/'run').write_text('#!/usr/bin/env bash\nset -euo pipefail\nroot=$(cd "$(dirname "$0")" && pwd)\nexport SHEN_KOKA_ROOT="$root"\nexec "$root/native" "$@"\n');(out/'run').chmod(0o755)
 (out/'build.json').write_text(json.dumps(record,indent=2)+'\n');return r.returncode
if __name__=='__main__':sys.exit(main())
