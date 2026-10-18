#!/usr/bin/env python3
"""Extract exact expression/expectation text without executing or rewriting tests."""
import hashlib,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1]
def forms(source):
    token=re.compile(r'\\\*.*?\*\\|\\\\[^\n]*|"[^"]*"|[()\[\]]|[^\s()\[\]"]+',re.S)
    ts=[m for m in token.finditer(source) if not m[0].startswith(('\\*','\\\\'))]
    pos=0
    def read():
        nonlocal pos
        t=ts[pos];pos+=1
        if t[0] in ('(', '['):
            close=')' if t[0]=='(' else ']'; children=[]
            while ts[pos][0]!=close: children.append(read())
            end=ts[pos].end();pos+=1
            return {'text':source[t.start():end],'children':children}
        return {'text':t[0],'children':[]}
    result=[]
    while pos<len(ts): result.append(read())
    return result

def inventory():
    lock=json.loads((ROOT/'comparison/shen-suite.lock.json').read_text());result=[]
    src=(ROOT/'kernel/tests/kerneltests.shen').read_text()
    reports=[f['children'] for f in forms(src) if f['children'] and f['children'][0]['text']=='report']
    assert len(reports)==40
    for group,report in zip(lock['canonical']['groups'],reports):
        assert json.loads(report[1]['text'])==group['name']
        pairs=report[2:];assert len(pairs)==2*group['assertion_count']
        for i in range(0,len(pairs),2):
            result.append({'id':f"{group['id']}/{i//2+1:03}",'expression':pairs[i]['text'],'expectation':pairs[i+1]['text']})
    ext=(ROOT/'kernel/tests/extensions/programmable-pattern-matching/tests.shen').read_text()
    assertions=[f['children'] for f in forms(ext) if f['children'] and f['children'][0]['text'].startswith('extension-tests.assert-')]
    assert len(assertions)==20
    for case,form in zip(lock['bundled_extensions']['cases'],assertions):
        assert json.loads(form[1]['text'])==case['name']
        result.append({'id':case['id'],'expression':form[2]['text'],'expectation':form[3]['text'] if len(form)>3 else 'error'})
    for c in result:
        for field in ['expression','expectation']:c[field+'_sha256']=hashlib.sha256(c[field].encode()).hexdigest()
    return result
if __name__=='__main__':print(json.dumps(inventory(),indent=2))
