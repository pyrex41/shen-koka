import pathlib,subprocess,os,tempfile,json,time,hashlib,shutil
root=pathlib.Path('/workspace/scratch/3e502de53f0d/shen-koka');base=root.parent;out=root/'evidence/140-dynamic-deployment';out.mkdir(exist_ok=True);fixture=root/'comparison/slices/dynamic/program.shen';expected=(fixture.parent/'expected').read_bytes();artifact=root/'artifacts/dynamic-deployment-redirected';report={'expected':expected.decode(),'source_sha256':hashlib.sha256(fixture.read_bytes()).hexdigest(),'baseline_full_suite':'../131-eval-slice-full/report.json','native_full_suite':'../135-native-kernel-resumed-full/report.json'}
with tempfile.TemporaryDirectory(prefix='dynamic-reference-') as cwd:
 p=subprocess.run([str(base/'reference-shen-go'),'script',str(fixture)],cwd=cwd,capture_output=True,timeout=60)
 (out/'reference.load-output').write_bytes((pathlib.Path(cwd)/'load-output.txt').read_bytes())
(out/'reference.stdout').write_bytes(p.stdout);(out/'reference.stderr').write_bytes(p.stderr);report['reference']={'exit_code':p.returncode,'matches_golden':p.stdout==expected,'stderr_empty':not p.stderr};print('reference',report['reference'],flush=True)
while not (root/'evidence/139-dynamic-deployment/report.json').exists():time.sleep(1)
argv=[str(base/'yggdrasil-koka-script-host'),'build',str(fixture),str(artifact),'--target','koka','--host',str(base/'reference-shen-go')];start=time.monotonic()
with tempfile.TemporaryDirectory(prefix='dynamic-shake-cache-') as cache:
 p=subprocess.run(argv,cwd=root,env={**os.environ,'YGGDRASIL_SHEN_KOKA_DIR':str(root),'XDG_CACHE_HOME':cache},capture_output=True,timeout=960)
(out/'build.stdout').write_bytes(p.stdout);(out/'build.stderr').write_bytes(p.stderr);report['build']={'argv':argv,'exit_code':p.returncode,'seconds':time.monotonic()-start}
for name in ['build.json','compile.log']:
 if (artifact/'koka-artifact'/name).exists():shutil.copy2(artifact/'koka-artifact'/name,out/name)
if (artifact/'yggdrasil.manifest.txt').exists():shutil.copy2(artifact/'yggdrasil.manifest.txt',out/'yggdrasil.manifest.txt')
if p.returncode==0:
 with tempfile.TemporaryDirectory(prefix='dynamic-artifact-') as cwd:
  q=subprocess.run([str(artifact/'koka-artifact/run')],cwd=cwd,env={**os.environ,'SHEN_KOKA_ROOT':'/nonexistent-kernel'},capture_output=True,timeout=120)
  (out/'run.load-output').write_bytes((pathlib.Path(cwd)/'load-output.txt').read_bytes())
  report['runtime_file']=(pathlib.Path(cwd)/'runtime-loaded.shen').read_text() if (pathlib.Path(cwd)/'runtime-loaded.shen').exists() else None
 (out/'run.stdout').write_bytes(q.stdout);(out/'run.stderr').write_bytes(q.stderr);report['run']={'exit_code':q.returncode,'matches_golden':q.stdout==expected,'stderr_empty':not q.stderr,'cwd_profile':'empty directory, nonexistent installed kernel'}
report['status']='PASS' if report['reference']['exit_code']==0 and report['reference']['matches_golden'] and p.returncode==0 and report.get('run',{}).get('exit_code')==0 and report['run']['matches_golden'] and report['run']['stderr_empty'] else 'FAIL';(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(report,flush=True)
