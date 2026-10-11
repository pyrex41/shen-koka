#!/usr/bin/env python3
"""Extract exact expression/expectation text without executing or rewriting tests."""
import argparse,hashlib,json,pathlib,re
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

def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node["children"])

def extract(distribution):
    """Inventory top-level assertions in upstream entrypoint load order."""
    canonical=[]; extensions=[]
    reports=[f['children'] for f in forms((distribution/'tests/kerneltests.shen').read_text())
             if f['children'] and f['children'][0]['text']=='report']
    for index, report in enumerate(reports,1):
        pairs=report[2:]
        if len(pairs)%2: raise ValueError('unpaired canonical assertion')
        canonical.append({'id':f'canonical/{index:03}', 'name':json.loads(report[1]['text']),
                          'assertion_count':len(pairs)//2, 'pairs':pairs})
    entry=distribution/'tests/extensions/runme.shen'
    for form in forms(entry.read_text()):
        children=form['children']
        if not children or children[0]['text']!='load': continue
        relative=json.loads(children[1]['text'])
        for assertion in walk(forms((distribution/relative).read_text())):
            args=assertion['children']
            if not args or not args[0]['text'].startswith('extension-tests.assert-'): continue
            if args[0]['text'] not in ('extension-tests.assert-equal','extension-tests.assert-error'):
                raise ValueError('unknown assertion kind: '+args[0]['text'])
            extensions.append({'id':f'extensions/{len(extensions)+1:03}',
                               'name':json.loads(args[1]['text']), 'source':relative,
                               'expression':args[2]['text'],
                               'expectation':args[3]['text'] if len(args)>3 else 'error'})
    return canonical,extensions

def inventory(lockpath=ROOT/'comparison/shen-suite.lock.json', distribution=ROOT/'kernel'):
    lock=json.loads(lockpath.read_text());result=[]
    groups,extensions=extract(distribution)
    if len(groups)!=len(lock['canonical']['groups']): raise ValueError('group count drift')
    for group,actual in zip(lock['canonical']['groups'],groups):
        if (group['name'],group['assertion_count'])!=(actual['name'],actual['assertion_count']):
            raise ValueError('canonical inventory drift: '+group['name'])
        pairs=actual['pairs']
        for i in range(0,len(pairs),2):
            result.append({'id':f"{group['id']}/{i//2+1:03}", 'expression':pairs[i]['text'],
                           'expectation':pairs[i+1]['text']})
    if len(extensions)!=len(lock['bundled_extensions']['cases']): raise ValueError('extension count drift')
    for case,actual in zip(lock['bundled_extensions']['cases'],extensions):
        if case['name']!=actual['name']: raise ValueError('extension order drift')
        result.append({**actual,'id':case['id']})
    if len(result)!=lock['canonical']['assertion_count']+lock['bundled_extensions']['assertion_count']:
        raise ValueError('denominator drift')
    for c in result:
        for field in ['expression','expectation']:
            c[field+'_sha256']=hashlib.sha256(c[field].encode()).hexdigest()
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--lock',type=pathlib.Path,default=ROOT/'comparison/shen-suite.lock.json')
    ap.add_argument('--distribution',type=pathlib.Path,default=ROOT/'kernel')
    args=ap.parse_args()
    print(json.dumps(inventory(args.lock,args.distribution),indent=2))
