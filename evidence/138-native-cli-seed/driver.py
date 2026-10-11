import pathlib,os,subprocess,tempfile,json,hashlib,time,importlib.util
root=pathlib.Path('/workspace/scratch/3e502de53f0d/shen-koka');base=root.parent;spec=importlib.util.spec_from_file_location('cli_cases',root/'scripts/test-cli.py');cases=importlib.util.module_from_spec(spec);spec.loader.exec_module(cases)
out=root/'evidence/138-native-cli-seed';out.mkdir();artifact=root/'artifacts/native-kernel-006';report={'native_binary_sha256':hashlib.sha256((artifact/'native').read_bytes()).hexdigest(),'cli_case_source_sha256':hashlib.sha256((root/'scripts/test-cli.py').read_bytes()).hexdigest(),'cli':{}}
for name,(args,expected,code,source) in cases.CASES.items():
 with tempfile.TemporaryDirectory(prefix='native-cli-case-') as cwd:
  f=pathlib.Path(cwd)/'program.shen'
  if source is not None:f.write_text(source+'\n')
  argv=[str(artifact/'run'),*[str(f) if a=='{script}' else a for a in args]]
  try:
   p=subprocess.run(argv,cwd=cwd,capture_output=True,text=True,timeout=60)
   report['cli'][name]={'status':'PASS' if p.returncode==code and p.stdout==expected and not p.stderr else 'FAIL','exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'expected_stdout':expected,'expected_exit_code':code}
  except subprocess.TimeoutExpired:report['cli'][name]={'status':'UNKNOWN','blocker':'timeout'}
(out/'cli.json').write_text(json.dumps(report,indent=2)+'\n');print('native CLI', {k:v['status'] for k,v in report['cli'].items()},flush=True)
env={**os.environ,'BIFROST_ADAPTERS':str(base/'integration/bifrost/adapters.json'),'BIFROST_SHEN_KOKA':str(artifact/'run')};argv=[str(base/'bifrost-koka-stage1'),'-suite','comparison/bifrost.suite.json','-impls','shen-koka','-json'];p=subprocess.run(argv,cwd=root,env=env,capture_output=True,timeout=600);(out/'bifrost.stdout').write_bytes(p.stdout);(out/'bifrost.stderr').write_bytes(p.stderr);q=subprocess.run(['python3','scripts/check-comparison.py','--input',str(out/'bifrost.stdout'),'--required','shen-koka'],cwd=root,capture_output=True);(out/'checker.stdout').write_bytes(q.stdout);(out/'checker.stderr').write_bytes(q.stderr);report['seed']={'case_denominator':17,'argv':argv,'bifrost_exit_code':p.returncode,'checker_exit_code':q.returncode,'bifrost_binary_sha256':hashlib.sha256((base/'bifrost-koka-stage1').read_bytes()).hexdigest()};report['status']='PASS' if all(c['status']=='PASS' for c in report['cli'].values()) and p.returncode==q.returncode==0 else 'FAIL';(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print('native CLI/seed',report['status'],flush=True)
