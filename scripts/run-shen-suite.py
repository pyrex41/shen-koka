#!/usr/bin/env python3
"""Run the unchanged pinned distribution; never infer success from final globals."""
import argparse, collections, hashlib, json, os, pathlib, re, signal, subprocess, time
ROOT = pathlib.Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()
def execute(argv, cwd, out, seconds):
    start = time.monotonic()
    result = dict(argv=argv, cwd=str(cwd), exit_code=None, blocker=None)
    with (out/'stdout').open('wb') as stdout, (out/'stderr').open('wb') as stderr:
        try:
            p = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE, stdout=stdout,
                                 stderr=stderr, start_new_session=True)
            try:
                # The only input requested by this distribution is failure continuation.
                p.communicate(b'y\n' * 512, timeout=seconds)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid, signal.SIGKILL); p.communicate()
                result['blocker'] = 'timeout'
            result['exit_code'] = p.returncode
        except OSError as e: result['blocker'] = str(e)
    result['seconds'] = time.monotonic()-start
    result['logs'] = {n: {'sha256':sha(out/n), 'bytes':(out/n).stat().st_size} for n in ['stdout','stderr']}
    return result

def parse_canonical(text, lock, cells):
    # Every group emits cumulative counters, before the suite resets them.
    reports = list(re.finditer(r'passed \.\.\. (\d+)\s+failed \.\.\. (\d+)\s+pass rate \.\.\. [^\n]+', text))
    headers = list(re.finditer(r'^('+'|'.join(re.escape(g['name']) for g in lock['groups'])+r'): ', text, re.M))
    expected = [g['name'] for g in lock['groups'] for _ in range(g['assertion_count'])]
    for i, h in enumerate(headers[:len(cells)]):
        if h.group(1) != expected[i]: break
        end = headers[i+1].start() if i+1 < len(headers) else len(text)
        body = text[h.end():end]
        cell = cells[i]
        cell['observation'] = body
        if 'failed with error ' in body or 'failed; continue?' in body:
            cell['status'] = 'FAIL'
        elif re.search(r'(?m)^passed(?:\s|$)', body): cell['status'] = 'PASS'
    counts = [(int(r[1]),int(r[2])) for r in reports]
    total = 0
    valid = len(counts)==len(lock['groups']) and len(headers)==len(cells)
    for g, count in zip(lock['groups'], counts):
        total += g['assertion_count']
        valid &= sum(count)==total
    return {'group_reports':counts, 'complete_reports':bool(valid)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--launcher',default=str(ROOT/'bin/shen-koka'))
    ap.add_argument('--script-command',default='script',help='empty for a direct filename launcher')
    ap.add_argument('--distribution',type=pathlib.Path,default=ROOT/'kernel')
    ap.add_argument('--output',type=pathlib.Path,required=True)
    ap.add_argument('--timeout',type=float,default=1500)
    ap.add_argument('--previous',type=pathlib.Path)
    args=ap.parse_args(); args.output.mkdir(parents=True,exist_ok=False)
    lockpath=ROOT/'comparison/shen-suite.lock.json'; lock=json.loads(lockpath.read_text())
    errors=[]
    for name, digest in lock['sha256_by_file'].items():
        p=args.distribution/'tests'/name
        if not p.is_file() or sha(p)!=digest: errors.append(name)
    identities={x['id']:x for x in json.loads((ROOT/'comparison/assertions.json').read_text())}
    launcher=pathlib.Path(args.launcher).absolute()
    build_record=ROOT/'.build/build.json'
    if launcher==ROOT/'bin/shen-koka':
        if not build_record.is_file(): errors.append('missing build provenance')
        else:
            build=json.loads(build_record.read_text())
            if build['binary_sha256']!=sha(ROOT/'.build/shen-koka'): errors.append('binary changed after build')
            for name,digest in build['sources'].items():
                if sha(ROOT/name)!=digest: errors.append('stale build: '+name)
    report={'schema_version':1,'candidate_sha':git('rev-parse','HEAD'),
            'dirty':bool(git('status','--porcelain')),'suite_lock_sha256':sha(lockpath),
            'launcher_sha256':sha(launcher) if launcher.is_file() else None,
            'runtime_binary_sha256':sha(ROOT/'.build/shen-koka') if launcher==ROOT/'bin/shen-koka' and (ROOT/'.build/shen-koka').is_file() else None,
            'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'src').rglob('*')) if p.is_file()},
            'flake_lock_sha256':sha(ROOT/'flake.lock'),
            'inventory_errors':errors,'lanes':{}}
    for lane in ['canonical','bundled_extensions']:
        spec=lock[lane]; out=args.output/lane; out.mkdir()
        if lane=='canonical':
            cells=[{'id':f"{g['id']}/{i:03}",'status':'UNKNOWN'} for g in spec['groups'] for i in range(1,g['assertion_count']+1)]
            cwd=args.distribution/'tests'
        else:
            cells=[{'id':c['id'],'name':c['name'],'status':'UNKNOWN'} for c in spec['cases']]
            cwd=args.distribution
        if errors:
            result={'blocker':'pinned suite inventory mismatch','exit_code':None}
        else:
            result=execute([str(launcher)]+([args.script_command] if args.script_command else [])+[spec['entrypoint']],cwd,out,args.timeout)
            text=(out/'stdout').read_text(errors='replace')
            if lane=='canonical': result.update(parse_canonical(text,spec,cells))
            else:
                observations=re.findall(r'^(ok|not ok) - (.+)$',text,re.M)
                for cell,(status,name) in zip(cells,observations):
                    if cell['name']!=name: break
                    cell.update(status='PASS' if status=='ok' else 'FAIL',observation=name)
                result['complete_reports']=(len(observations)==8 and bool(re.search(r'passed \.\.\. \d+\s+failed \.\.\. \d+',text)))
        for cell in cells: cell.update(identities[cell['id']])
        result['assertions']=cells
        result['counts']={s:sum(c['status']==s for c in cells) for s in ['PASS','FAIL','UNKNOWN']}
        result['denominator']=spec['assertion_count']
        result['status']='FAIL' if result['counts']['FAIL'] else 'UNKNOWN'
        if result['counts']['PASS']==result['denominator'] and result['exit_code']==0 and result.get('complete_reports'):
            result['status']='PASS'
        report['lanes'][lane]=result
    report['regressions']=[]
    if args.previous:
        old=json.loads(args.previous.read_text())
        for lane,current in report['lanes'].items():
            previous={x['id']:x['status'] for x in old['lanes'][lane]['assertions']}
            report['regressions'] += [x['id'] for x in current['assertions'] if previous.get(x['id'])=='PASS' and x['status']!='PASS']
    report['status']='PASS' if all(x['status']=='PASS' for x in report['lanes'].values()) and not report['regressions'] else 'UNKNOWN'
    if report['regressions'] or any(x['status']=='FAIL' for x in report['lanes'].values()): report['status']='FAIL'
    (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    for lane,r in report['lanes'].items(): print(lane,r['counts'],'/',r['denominator'],r['status'],r.get('blocker') or '')
    return 0 if report['status']=='PASS' else 1
if __name__=='__main__': raise SystemExit(main())
