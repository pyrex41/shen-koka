#!/usr/bin/env python3
"""Record numeric/character observations without normalizing disagreements away."""
import argparse,hashlib,json,pathlib,subprocess,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
CASES={
 'mixed':'(+ 1 0.5)', 'division':'(/ 3 2)',
 'zero-division':'(trap-error (/ 1 0) (/. E caught))',
 'negative-zero':'(str -0.0)',
 'large-integer':'(= 9007199254740992 9007199254740993)',
 'exponent':'(= 1e3 1000)',
 'integer-predicate':'[(integer? 1) (integer? 1.5)]',
 'unicode-pos':'(pos "λx" 1)', 'unicode-code':'(string->n "λ")',
 'unicode-tail':'(tlstr "λx")', 'unicode-roundtrip':'(n->string 955)',
 'nul-roundtrip':'(string->n (n->string 0))',
 'empty-code':'(trap-error (string->n "") (/. E caught))',
 'negative-pos':'(trap-error (pos "a" -1) (/. E caught))',
 'past-end-pos':'(trap-error (pos "a" 1) (/. E caught))',
 'fraction-pos':'(pos "ab" 0.5)',
}
def main():
 p=argparse.ArgumentParser();p.add_argument('--go',type=pathlib.Path,required=True);p.add_argument('--lua',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
 commands={'koka':[str(ROOT/'bin/shen-koka'),'eval','-e'],'go':[str(a.go.resolve()),'eval','-e'],'lua':['luajit',str(a.lua.resolve()/'bin/shen'),'-e']}
 result={'cases':CASES,'observations':{},'commands':commands,'candidate_sha256':hashlib.sha256((ROOT/'.build/shen-koka').read_bytes()).hexdigest(),'go_sha256':hashlib.sha256(a.go.read_bytes()).hexdigest(),'lua_sha':subprocess.check_output(['git','-C',str(a.lua),'rev-parse','HEAD'],text=True).strip()}
 for name,command in commands.items():
  rows=result['observations'][name]={}
  for case,source in CASES.items():
   try:
    with tempfile.TemporaryDirectory(prefix='shen-boundary-') as cwd:
     # Lua boot locates its KL modules relative to the reference checkout.
     r=subprocess.run(command+[source],cwd=a.lua if name=='lua' else cwd,capture_output=True,timeout=30)
    rows[case]={'stdout':r.stdout.decode(errors='backslashreplace'),'stderr':r.stderr.decode(errors='backslashreplace'),'stdout_hex':r.stdout.hex(),'stderr_hex':r.stderr.hex(),'exit_code':r.returncode,'status':'OBSERVED'}
   except subprocess.TimeoutExpired as e:rows[case]={'status':'UNKNOWN','blocker':'30-second timeout','stdout_hex':(e.stdout or b'').hex(),'stderr_hex':(e.stderr or b'').hex()}
   except OSError as e:rows[case]={'status':'UNKNOWN','blocker':str(e)}
   (a.output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
 result['exact_agreement']={case:all(result['observations'][n][case].get('status')=='OBSERVED' and result['observations'][n][case].get('exit_code')==0 for n in commands) and len({result['observations'][n][case].get('stdout') for n in commands})==1 for case in CASES}
 (a.output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result['exact_agreement']))
if __name__=='__main__':main()
