import pathlib,json,subprocess,time,os,tempfile,hashlib,shutil,signal
root=pathlib.Path('/workspace/scratch/3e502de53f0d/shen-koka');out=root/'evidence/130-eval-capable-slice';out.mkdir();source=root/'artifacts/metaeval-slice';artifact=root/'artifacts/metaeval-interpreted';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
shutil.copy2(root/'scripts/build-slice.py',out/'builder.py');shutil.copy2(source/'yggdrasil.manifest.txt',out/'yggdrasil.manifest.txt')
for n in ['stdout','stderr']:shutil.copy2('/tmp/metaeval-shake.'+n,out/('shake.'+n))
while not (root/'artifacts/native-kernel-005/build.json').exists():time.sleep(1)
argv=['python3',str(root/'scripts/build-slice.py'),str(source),str(artifact)];start=time.monotonic();p=subprocess.run(argv,cwd=root,capture_output=True,timeout=960)
(out/'build.stdout').write_bytes(p.stdout);(out/'build.stderr').write_bytes(p.stderr)
r={'baseline_full_suite':'../127-nix-cli-full/report.json','postchange_full_suite':'../131-eval-slice-full/report.json','argv':argv,'build_exit_code':p.returncode,'build_seconds':time.monotonic()-start,'builder_sha256':sha(out/'builder.py'),'input_sha256':{str(f.relative_to(source)):sha(f) for f in source.rglob('*') if f.is_file()},'status':'FAIL'}
if (artifact/'build.json').exists():shutil.copy2(artifact/'build.json',out/'build.json')
if (artifact/'compile.log').exists():shutil.copy2(artifact/'compile.log',out/'compile.log')
if p.returncode==0:
 with tempfile.TemporaryDirectory(prefix='shen-eval-slice-run-') as cwd:
  try:
   q=subprocess.run([str(artifact/'run')],cwd=cwd,env={**os.environ,'SHEN_KOKA_ROOT':'/nonexistent-kernel'},capture_output=True,timeout=120)
   (out/'run.stdout').write_bytes(q.stdout);(out/'run.stderr').write_bytes(q.stderr)
   golden=pathlib.Path('/workspace/scratch/3e502de53f0d/pinned/yggdrasil/tests/metaeval.expected').read_bytes();(out/'expected').write_bytes(golden)
   r['run']={'exit_code':q.returncode,'cwd_profile':'empty temporary directory','SHEN_KOKA_ROOT':'/nonexistent-kernel','matches_golden':q.stdout==golden,'stderr_empty':not q.stderr,'binary_sha256':sha(artifact/'run')};r['status']='PASS' if q.returncode==0 and q.stdout==golden and not q.stderr else 'FAIL'
  except subprocess.TimeoutExpired:r['status']='UNKNOWN';r['blocker']='artifact run timeout'
refuse=['python3',str(root/'scripts/build-slice.py'),'--native',str(source),str(root/'artifacts/metaeval-native-refused')];q=subprocess.run(refuse,capture_output=True,timeout=45);r['native_refusal']={'exit_code':q.returncode,'stdout':q.stdout.decode(),'stderr':q.stderr.decode(),'output_exists':(root/'artifacts/metaeval-native-refused').exists()}
if q.returncode!=3 or r['native_refusal']['output_exists']:r['status']='FAIL'
(out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
