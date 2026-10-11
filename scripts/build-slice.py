#!/usr/bin/env python3
"""Package exactly a Yggdrasil slice in a native Koka interpreter executable.
This is an interpreter-backed builder, not the planned direct KL-to-Koka compiler.
"""
import argparse,collections,hashlib,json,pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('manifest',type=pathlib.Path);p.add_argument('output',type=pathlib.Path);a=p.parse_args()
    manifest=a.manifest.resolve()
    if manifest.is_dir():manifest=manifest/'yggdrasil.manifest.txt'
    fields=collections.defaultdict(list)
    for line in manifest.read_text().splitlines():
        if '=' in line:
            k,v=line.split('=',1);fields[k].append(v)
    def one(k):
        if len(fields[k])!=1:raise ValueError('expected exactly one '+k)
        return fields[k][0]
    if one('manifest-version')!='4':raise ValueError('unsupported manifest version')
    needs=one('needs-eval')
    if needs not in ('true','false'):raise ValueError('invalid needs-eval')
    if needs=='true':print('UNSUPPORTED: eval-capable standalone slice',file=sys.stderr);return 3
    if one('init-order')!='checked':raise ValueError('initializer order is not checked')
    kernel=one('kernel');initializer=one('init');users=fields['user']
    if not users:raise ValueError('empty user file list')
    def source(name):
        path=(manifest.parent/name).resolve()
        if not path.is_relative_to(manifest.parent):raise ValueError('manifest path escapes slice directory')
        return path
    files=[source(kernel)]+[source(u) for u in users]
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    runtime=out/'src';import shutil;shutil.copytree(ROOT/'src/shen',runtime/'shen')
    # main, boot, and upstream kernel are not dependencies of this generated module.
    lines=['import shen/values','import shen/world','import shen/machine','import shen/read-kl','import shen/io','import std/num/int32','fun run-slice() {',' val w=new-world()']
    for k,v in [('stinput',0),('stoutput',1),('sterror',2)]:lines.append(f' global-set(w,"*{k}*",Stream({v}));')
    for k,v in [('home-directory',''),('language','Koka'),('implementation','Koka 3.2.3'),('port','shen-koka'),('porters','Shen-Koka contributors'),('os','Unix'),('release','0.0.1')]:lines.append(f' global-set(w,"*{k}*",Text({json.dumps(v)}));')
    def load(path):lines.append(' parse-kl('+json.dumps(path.read_text(),ensure_ascii=False)+').foreach(fn(form) { evaluate(w,form); () })')
    load(files[0]);lines.append(' invoke(w,Sym('+json.dumps(initializer)+'),[]);')
    for f in files[1:]:load(f)
    lines+=[' ()','}','pub fun main() { try(run-slice,fn(e) { println("shen-koka slice: "++e.message); process-exit(1.int32) }) }']
    (out/'program.kk').write_text('\n'.join(lines)+'\n')
    command=['koka','-i'+str(runtime),'-O2','--builddir='+str(out/'cache'),'-o',str(out/'run'),str(out/'program.kk')]
    with (out/'compile.log').open('w') as log:
        result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=900)
    record={'schema_version':1,'execution':'Koka KLambda interpreter with embedded manifest-only sources','direct_kl_compiler':False,'manifest_sha256':digest(manifest),'inputs':{str(f.relative_to(manifest.parent)):digest(f) for f in files},'initializer':initializer,'argv':command,'exit_code':result.returncode,'runtime_sources':{str(f.relative_to(runtime)):digest(f) for f in runtime.rglob('*') if f.is_file()}}
    if result.returncode==0:
        (out/'run').chmod(0o755);record['executable_sha256']=digest(out/'run')
    (out/'build.json').write_text(json.dumps(record,indent=2)+'\n')
    return result.returncode
if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,OSError,subprocess.TimeoutExpired) as e:print(str(e),file=sys.stderr);raise SystemExit(1)
