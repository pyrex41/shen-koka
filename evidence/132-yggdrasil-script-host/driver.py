import pathlib,json,subprocess,os,signal,time,tempfile,hashlib
root=pathlib.Path('/workspace/scratch/3e502de53f0d');repo=root/'shen-koka';out=repo/'evidence/132-yggdrasil-script-host';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();report={'case_denominator':1,'required_hosts':['shen-go','shen-lua','shen-koka'],'hosts':{},'yggdrasil_binary_sha256':sha(root/'yggdrasil-koka-script-host')}
for name,host,style in [('shen-go',root/'reference-shen-go','sub'),('shen-lua',root/'pinned/shen-lua/bin/shen','positional'),('shen-koka',repo/'bin/shen-koka','script')]:
 artifact=repo/('artifacts/script-host-'+name);argv=[str(root/'yggdrasil-koka-script-host'),'shake',str(root/'pinned/yggdrasil/tests/fib.shen'),str(artifact),'--host',str(host),'--eval-style',style];start=time.monotonic()
 with tempfile.TemporaryDirectory(prefix='shen-script-host-') as cache:
  env={**os.environ,'XDG_CACHE_HOME':cache,'SHEN_FASL':'off'};p=subprocess.Popen(argv,cwd=repo,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
  try:stdout,stderr=p.communicate(timeout=900);timed=False
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);stdout,stderr=p.communicate();timed=True
  finally:
   try:os.killpg(p.pid,signal.SIGKILL)
   except ProcessLookupError:pass
 (out/(name+'.stdout')).write_bytes(stdout);(out/(name+'.stderr')).write_bytes(stderr)
 files={str(f.relative_to(artifact)):{'bytes':f.stat().st_size,'sha256':sha(f)} for f in artifact.rglob('*') if f.is_file()};r={'argv':argv,'exit_code':p.returncode,'timed_out':timed,'seconds':time.monotonic()-start,'artifacts':files,'status':'UNKNOWN' if timed else 'PASS' if p.returncode==0 and all(files.get(n,{}).get('bytes',0)>0 for n in ['kernel.kl','yggdrasil.manifest','yggdrasil.manifest.txt','fib.kl']) else 'FAIL'};report['hosts'][name]=r
 (out/'progress.json').write_text(json.dumps(report,indent=2)+'\n');print(name,r['status'],r['seconds'],flush=True)
report['matching_artifacts']={n:len({r['artifacts'].get(n,{}).get('sha256') for r in report['hosts'].values()})==1 for n in ['kernel.kl','yggdrasil.manifest','yggdrasil.manifest.txt']};report['status']='PASS' if all(r['status']=='PASS' for r in report['hosts'].values()) and all(report['matching_artifacts'].values()) else 'FAIL';report['koka_binary_sha256']=sha(repo/'.build/shen-koka');(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'],flush=True)
