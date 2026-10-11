import pathlib,subprocess,os,signal,time,json,hashlib,tempfile
root=pathlib.Path('/workspace/scratch/3e502de53f0d');repo=root/'shen-koka';out=repo/'evidence/129-yggdrasil-koka-host';out.mkdir();artifact=repo/'artifacts/yggdrasil-koka-host'
argv=[str(root/'yggdrasil-koka-native'),'shake',str(root/'pinned/yggdrasil/tests/fib.shen'),str(artifact),'--host',str(repo/'bin/shen-koka')]
started=time.monotonic();env=os.environ.copy()
with tempfile.TemporaryDirectory(prefix='shen-host-cache-') as cache:
 env['XDG_CACHE_HOME']=cache
 p=subprocess.Popen(argv,env=env,cwd=repo,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
 try:stdout,stderr=p.communicate(timeout=900);timed=False
 except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);stdout,stderr=p.communicate();timed=True
 finally:
  try:os.killpg(p.pid,signal.SIGKILL)
  except ProcessLookupError:pass
(out/'stdout').write_bytes(stdout);(out/'stderr').write_bytes(stderr)
r={'argv':argv,'timeout_seconds':900,'seconds':time.monotonic()-started,'exit_code':p.returncode,'timed_out':timed,'binary_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [root/'yggdrasil-koka-native',repo/'.build/shen-koka']},'artifacts':{str(f.relative_to(artifact)):{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in artifact.rglob('*') if f.is_file()},'status':'UNKNOWN' if timed else 'PASS' if p.returncode==0 else 'FAIL'}
(out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
