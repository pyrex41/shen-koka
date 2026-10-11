"""Bounded serial native build with complete final logs and process-group cleanup."""
import os,signal,subprocess,types,fcntl,functools,time,pathlib,shutil

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


def run_compiler(command,timeout):
    p=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
    timed_out=False
    try:output,_=p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out=True;os.killpg(p.pid,signal.SIGKILL);output,_=p.communicate()
    return types.SimpleNamespace(returncode=124 if timed_out else p.returncode,
                                 stdout=output.decode(errors='replace'),timed_out=timed_out)

def artifact_notices(out):
    root=pathlib.Path(__file__).resolve().parents[1]
    notices=out/'notices';notices.mkdir(exist_ok=True)
    for source,name in [(root/'kernel/UPSTREAM-LICENSE','SHEN-UPSTREAM-LICENSE'),(root/'kernel/PROVENANCE.md','SHEN-PROVENANCE.md'),(root/'third-party/KOKA-LICENSE','KOKA-LICENSE')]:
        shutil.copy2(source,notices/name)
