"""Bounded serial native build with complete final logs and process-group cleanup."""
import os,signal,subprocess,types

def run_compiler(command,timeout):
    p=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
    timed_out=False
    try:output,_=p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out=True;os.killpg(p.pid,signal.SIGKILL);output,_=p.communicate()
    return types.SimpleNamespace(returncode=124 if timed_out else p.returncode,
                                 stdout=output.decode(errors='replace'),timed_out=timed_out)
