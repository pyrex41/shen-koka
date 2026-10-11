"""Bounded serial native build with complete final logs and process-group cleanup."""
import os,signal,subprocess,types,fcntl,functools,time,pathlib,shutil,resource,sys,json

def serial_native_build(main):
    """Protect shared generated modules and cache until the artifact is copied."""
    @functools.wraps(main)
    def locked(*args,**kwargs):
        with open("/tmp/shen-koka-native-anf.lock","a") as lock:
            deadline=time.monotonic()+30
            while True:
                try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);break
                except BlockingIOError:
                    if time.monotonic()>=deadline:raise RuntimeError("another native build holds the shared workspace lock")
                    time.sleep(0.1)
            try:return main(*args,**kwargs)
            finally:fcntl.flock(lock,fcntl.LOCK_UN)
    return locked


def memory_events():
    try:return {k:int(v) for k,v in (line.split() for line in pathlib.Path('/sys/fs/cgroup/memory.events').read_text().splitlines())}
    except OSError:return None

def run_compiler(command,timeout,cancel_path=None):
    start=time.monotonic();before=memory_events();usage_before=resource.getrusage(resource.RUSAGE_CHILDREN)
    p=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
    timed_out=False;cancelled=False
    while True:
        remaining=timeout-(time.monotonic()-start)
        cancelled=cancel_path is not None and pathlib.Path(cancel_path).exists()
        if remaining<=0 or cancelled:
            timed_out=not cancelled
            try:os.killpg(p.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            output,_=p.communicate();break
        try:output,_=p.communicate(timeout=min(1,remaining));break
        except subprocess.TimeoutExpired:pass
        except KeyboardInterrupt:
            cancelled=True
            try:os.killpg(p.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            output,_=p.communicate();break
    usage=resource.getrusage(resource.RUSAGE_CHILDREN)
    metrics={'seconds':time.monotonic()-start,'children_peak_rss_high_water_bytes':usage.ru_maxrss*(1 if sys.platform=='darwin' else 1024),'child_user_seconds':usage.ru_utime-usage_before.ru_utime,'child_system_seconds':usage.ru_stime-usage_before.ru_stime,'memory_events_before':before,'memory_events_after':memory_events()}
    return types.SimpleNamespace(returncode=130 if cancelled else 124 if timed_out else p.returncode,
                                 stdout=output.decode(errors='replace'),timed_out=timed_out,cancelled=cancelled,resources=metrics)

def run_compilation_steps(commands,timeout,per_step=300,output=None):
    deadline=time.monotonic()+timeout;logs=[];steps=[];code=0
    for i,command in enumerate(commands):
        remaining=deadline-time.monotonic()
        if remaining<=0:code=124;break
        print('Native build step %d/%d: %s'%(i+1,len(commands),command[-1]),flush=True)
        r=run_compiler(command,min(remaining,per_step),None if output is None else pathlib.Path(output)/'CANCEL');code=r.returncode
        steps.append({'argv':command,'exit_code':code,'cancelled':r.cancelled,'resources':r.resources})
        logs.append('COMMAND '+json.dumps(command)+'\n'+r.stdout)
        if output is not None:
            pathlib.Path(output,'compile.log').write_text('\n'.join(logs))
            pathlib.Path(output,'progress.json').write_text(json.dumps({'steps':steps,'exit_code':code,'total_steps':len(commands)},indent=2)+'\n')
        if code:break
    return types.SimpleNamespace(returncode=code,stdout='\n'.join(logs),steps=steps,timed_out=code==124)


def artifact_notices(out):
    root=pathlib.Path(__file__).resolve().parents[1]
    notices=out/'notices';notices.mkdir(exist_ok=True)
    for source,name in [(root/'kernel/UPSTREAM-LICENSE','SHEN-UPSTREAM-LICENSE'),(root/'kernel/PROVENANCE.md','SHEN-PROVENANCE.md'),(root/'third-party/KOKA-LICENSE','KOKA-LICENSE')]:
        shutil.copy2(source,notices/name)

def sync_sources(source,destination):
    """Keep identical staging mtimes so a bounded retry can reuse compiled modules."""
    source=pathlib.Path(source);destination=pathlib.Path(destination)
    for path in source.rglob('*'):
        if not path.is_file():continue
        target=destination/path.relative_to(source)
        if target.is_file() and target.read_bytes()==path.read_bytes():continue
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
