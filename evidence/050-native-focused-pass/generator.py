"""Direct KL-to-Koka lowering. Generated callbacks never capture host state.
Tail calls and protected tail bodies return requests to the shared machine;
non-tail calls root the surrounding native locals and suspended VM frames.
"""
import json, math, pathlib, re

class Symbol(str): pass
NUMBER = re.compile(r'^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$')

def read_kl(source):
    i=0
    def read():
        nonlocal i
        while i<len(source) and source[i].isspace(): i+=1
        if i==len(source): raise ValueError('unexpected end of KL')
        c=source[i];i+=1
        if c=='(':
            xs=[]
            while True:
                while i<len(source) and source[i].isspace():i+=1
                if i==len(source):raise ValueError('unclosed KL list')
                if source[i]==')':i+=1;return xs
                xs.append(read())
        if c==')':raise ValueError('unexpected closing parenthesis')
        if c=='"':
            start=i
            while i<len(source) and source[i]!='"':i+=1
            if i==len(source):raise ValueError('unclosed KL string')
            s=source[start:i];i+=1;return s
        start=i-1
        while i<len(source) and not source[i].isspace() and source[i] not in '()':i+=1
        token=source[start:i]
        return float(token) if NUMBER.fullmatch(token) else Symbol(token)
    forms=[]
    while i<len(source):
        if source[i].isspace():i+=1
        else:forms.append(read())
    return forms

def quote(s):return json.dumps(str(s),ensure_ascii=False)

def block(lines):
    flattened=[]
    for line in lines:
        if line.startswith('{\n') and line.endswith('\n}'):
            flattened.extend(part[2:] if part.startswith('  ') else part for part in line[2:-2].splitlines())
        else:flattened.append(line)
    return '{\n'+ '\n'.join('  '+line.replace('\n','\n  ') for line in flattened)+'\n}'

class Compiler:
    def __init__(self):self.jobs=[];self.serial=0
    def fresh(self):
        self.serial+=1;return 'x'+str(self.serial)
    def schedule(self,params,body,captures=()):
        i=len(self.jobs);self.jobs.append((list(params),body,list(captures)));return i
    def closure(self,params,body,env):
        names=list(env);code=self.schedule(params,body,names)
        return 'make-compiled(w,%d,%d,[%s],[])'%(len(params),code,','.join(env[n] for n in names))
    def expr(self,x,env,tail=False):
        def value(y):return self.expr(y,env)
        def statement_expression(lines):
            code=block(lines)
            return code if tail else "(fn() "+code+")()"
        def finish(code):return 'Done('+code+')' if tail else 'keep-native(roots,'+code+')'
        if isinstance(x,Symbol):return finish(env.get(x,'Sym('+quote(x)+')'))
        if isinstance(x,str):return finish('Text('+quote(x)+')')
        if isinstance(x,float):
            n=repr(x) if math.isfinite(x) else ('-1.0 / 0.0' if x<0 else '1.0 / 0.0')
            return finish('Num('+n+')')
        if x==[]:return finish('Nil')
        if not isinstance(x,list):raise ValueError('unsupported KL value')
        op=x[0];args=x[1:];tag=op if isinstance(op,Symbol) else None
        if tag==Symbol('defun'):
            if len(args)!=3 or not isinstance(args[0],Symbol) or not isinstance(args[1],list) or not all(isinstance(p,Symbol) for p in args[1]):raise ValueError('malformed defun')
            name,params,body=args;code=self.schedule(params,body)
            return statement_expression(['define-function(w,'+quote(name)+',make-compiled(w,%d,%d,[],[]))'%(len(params),code),finish('Sym('+quote(name)+')')])
        if tag==Symbol('lambda'):
            if len(args)!=2 or not isinstance(args[0],Symbol):raise ValueError('malformed lambda')
            return finish(self.closure([args[0]],args[1],env))
        if tag==Symbol('freeze'):
            if len(args)!=1:raise ValueError('malformed freeze')
            return finish(self.closure([],args[0],env))
        if tag==Symbol('let'):
            if len(args)!=3 or not isinstance(args[0],Symbol):raise ValueError('malformed let')
            name,binding,body=args;v=self.fresh();ctx={**env,name:v}
            return statement_expression(['val '+v+'='+value(binding),self.expr(body,ctx,tail)])
        if tag==Symbol('type') and len(args)==2:return self.expr(args[0],env,tail)
        if tag in (Symbol('and'),Symbol('or')) and len(args)==2:
            a,b=args;t=Symbol('true');f=Symbol('false')
            branch=[Symbol('if'),b,t,f]
            return self.expr([Symbol('if'),a,branch if tag=='and' else t,f if tag=='and' else branch],env,tail)
        if tag==Symbol('cond'):
            nested=[Symbol('simple-error'),'cond: no true branch']
            for clause in reversed(args):
                if not isinstance(clause,list) or len(clause)!=2:raise ValueError('malformed cond')
                nested=[Symbol('if'),clause[0],clause[1],nested]
            return self.expr(nested,env,tail)
        if tag==Symbol('if'):
            if len(args)!=3:raise ValueError('malformed if')
            test,yes,no=args
            return 'if boolean('+value(test)+') then '+block([self.expr(yes,env,tail)])+' else '+block([self.expr(no,env,tail)])
        if tag==Symbol('trap-error'):
            if len(args)!=2:raise ValueError('malformed trap-error')
            b=self.fresh();h=self.fresh()
            lines=['val '+b+'=keep-native(roots,'+self.closure([],args[0],env)+')','val '+h+'=keep-native(roots,'+self.closure([],args[1],env)+')']
            lines.append('Protected('+b+','+h+')' if tail else 'keep-native(roots,invoke-protected(w,'+b+','+h+'))')
            return statement_expression(lines)
        f=self.fresh();lines=['val '+f+'='+value(op)];av=[]
        for arg in args:
            v=self.fresh();lines.append('val '+v+'='+value(arg));av.append(v)
        xs='['+','.join(av)+']'
        lines.append('TailApply('+f+','+xs+')' if tail else 'keep-native(roots,invoke(w,'+f+','+xs+'))')
        return statement_expression(lines)
    def write(self,out,groups):
        """groups preserves file/form order; return module names and entry code IDs."""
        out=pathlib.Path(out);out.mkdir(parents=True,exist_ok=True)
        entries=[[self.schedule([],form) for form in forms] for forms in groups]
        bodies=[];i=0
        while i<len(self.jobs):
            params,body,captures=self.jobs[i];env={};lines=[]
            for j,name in enumerate(captures):
                v=self.fresh();lines.append('val '+v+'=native-arg(captured,%d)'%j);env[name]=v
            for j,name in enumerate(params):
                v=self.fresh();lines.append('val '+v+'=native-arg(args,%d)'%j);env[name]=v
            lines.append(self.expr(body,env,True))
            bodies.append('fun code%d(w:world,roots:ref<global,list<value>>,captured:list<value>,args:list<value>): <st<global>,exn,div,console> native-result '%i+block(lines))
            i+=1
        modules=[]
        for start in range(0,len(bodies),40):
            name='klpart'+str(start//40);modules.append(name)
            lines=['module '+name,'import shen/values','import shen/world','import shen/machine',*bodies[start:start+40],'pub fun install(w:world): <st<global>,exn,div> () '+block(['install-native(w,%d,code%d)'%(j,j) for j in range(start,min(start+40,len(bodies)))])]
            (out/(name+'.kk')).write_text('\n'.join(lines)+'\n')
        return {'modules':modules,'entries':entries,'code_count':len(bodies)}
