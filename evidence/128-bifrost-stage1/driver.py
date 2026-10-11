import pathlib,os,json,subprocess,time,hashlib,tempfile,signal
root=pathlib.Path('/workspace/scratch/3e502de53f0d'); repo=root/'shen-koka'; out=repo/'evidence/128-bifrost-stage1';out.mkdir()
env=os.environ.copy();env.update(BIFROST_ADAPTERS=str(root/'integration/bifrost/adapters.json'),BIFROST_SHEN_KOKA=str(repo/'bin/shen-koka'),BIFROST_SHEN_GO=str(root/'reference-shen-go'),BIFROST_SHEN_LUA=str(root/'pinned/shen-lua/bin/shen'),BIFROST_YGGDRASIL_DIR=str(root/'pinned/yggdrasil'),BIFROST_YGGDRASIL_BIN=str(root/'yggdrasil-koka-native'),SHEN_FASL='off')
argv=[str(root/'bifrost-koka'),'-heavy','-only','yggdrasil-shake-parity','-impls','shen-lua,shen-go,shen-koka','-json']
start=time.monotonic()
with tempfile.TemporaryDirectory(prefix='shen-stage1-') as cwd:
 env['XDG_CACHE_HOME']=cwd+'/cache'
 p=subprocess.Popen(argv,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
 try:stdout,stderr=p.communicate(timeout=960);timed=False
 except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);stdout,stderr=p.communicate();timed=True
(out/'stdout').write_bytes(stdout);(out/'stderr').write_bytes(stderr)
r={'argv':argv,'exit_code':p.returncode,'timed_out':timed,'seconds':time.monotonic()-start,'case_denominator':1,'required_implementations':['shen-lua','shen-go','shen-koka'],'environment':{k:v for k,v in env.items() if k.startswith(('BIFROST_','SHEN_FASL','XDG_CACHE_HOME'))},'binary_sha256':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [root/'bifrost-koka',root/'yggdrasil-koka-native',root/'reference-shen-go',repo/'build/shen-koka']}}
try:r['bifrost']=json.loads(stdout)
except ValueError:r['status']='UNKNOWN'
(out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
