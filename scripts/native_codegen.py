"""Direct KL-to-Koka lowering. Generated callbacks never capture host state.
Tail calls and protected tail bodies return requests to the shared machine;
non-tail calls root the surrounding native locals and suspended VM frames.
"""
import json, math, pathlib, re

class Symbol(str): pass
NUMBER = re.compile(r'^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$')

def read_kl(source):
    forms=[];stack=[forms];i=0
    while i<len(source):
        c=source[i]
        if c.isspace():i+=1;continue
        if c=='(':
            xs=[];stack[-1].append(xs);stack.append(xs);i+=1;continue
        if c==')':
            if len(stack)==1:raise ValueError('unexpected closing parenthesis')
            stack.pop();i+=1;continue
        if c=='"':
            start=i+1;i=source.find('"',start)
            if i<0:raise ValueError('unclosed KL string')
            stack[-1].append(source[start:i]);i+=1;continue
        start=i
        while i<len(source) and not source[i].isspace() and source[i] not in '()':i+=1
        token=source[start:i]
        stack[-1].append(float(token) if NUMBER.fullmatch(token) else Symbol(token))
    if len(stack)!=1:raise ValueError('unclosed KL list')
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
    def normalize(self,x):
        if not isinstance(x,list) or not x or not isinstance(x[0],Symbol):return x
        tag=x[0];args=x[1:]
        if tag in ('and','or') and len(args)==2:
            a,b=args;t=Symbol('true');f=Symbol('false');branch=[Symbol('if'),b,t,f]
            return [Symbol('if'),a,branch if tag=='and' else t,f if tag=='and' else branch]
        if tag=='cond':
            nested=[Symbol('simple-error'),'cond: no true branch']
            for clause in reversed(args):
                if not isinstance(clause,list) or len(clause)!=2:raise ValueError('malformed cond')
                nested=[Symbol('if'),clause[0],clause[1],nested]
            return nested
        if tag=='type' and len(args)==2:return self.normalize(args[0])
        return x
    def constant(self,x,env):
        if isinstance(x,Symbol):return env.get(x,'Sym('+quote(x)+')')
        if isinstance(x,str):return 'Text('+quote(x)+')'
        if isinstance(x,float):
            n=repr(x) if math.isfinite(x) else ('-1.0 / 0.0' if x<0 else '1.0 / 0.0')
            return 'Num('+n+')'
        if x==[]:return 'Nil'
        return None
    def save(self,expression,lines):
        v=self.fresh();lines.append('val '+v+'=keep-native(roots,'+expression+')');return v
    def call_parts(self,x,env):
        lines,op=self.value(x[0],env)
        # value() emits effects in order and roots computed results. Literals
        # and lexical values need no duplicate roots or live CPS temporaries.
        f=op;args=[]
        for arg in x[1:]:
            statements,v=self.value(arg,env);lines.extend(statements);args.append(v)
        return lines,f,'['+','.join(args)+']'
    def value(self,x,env):
        x=self.normalize(x);literal=self.constant(x,env)
        if literal is not None:return [],literal
        if not isinstance(x,list):raise ValueError('unsupported KL value')
        tag=x[0] if isinstance(x[0],Symbol) else None;args=x[1:]
        if tag=='defun' and len(args)==3:
            name,params,body=args
            if not isinstance(name,Symbol) or not isinstance(params,list) or not all(isinstance(p,Symbol) for p in params):raise ValueError('malformed defun')
            code=self.schedule(params,body)
            return ['define-function(w,'+quote(name)+',make-compiled(w,%d,%d,[],[]))'%(len(params),code)],'Sym('+quote(name)+')'
        if tag=='lambda' and len(args)==2:
            if not isinstance(args[0],Symbol):raise ValueError('malformed lambda')
            lines=[];v=self.save(self.closure([args[0]],args[1],env),lines);return lines,v
        if tag=='freeze' and len(args)==1:
            lines=[];v=self.save(self.closure([],args[0],env),lines);return lines,v
        if tag=='let' and len(args)==3:
            name,binding,body=args
            if not isinstance(name,Symbol):raise ValueError('malformed let')
            lines,b=self.value(binding,env);v=self.save(b,lines)
            more,result=self.value(body,{**env,name:v});return lines+more,result
        if tag=='if' and len(args)==3:
            lines,test=self.value(args[0],env)
            yes,y=self.value(args[1],env);no,n=self.value(args[2],env)
            expression='if boolean('+test+') then '+block(yes+[y])+' else '+block(no+[n])
            v=self.fresh();lines.append('val '+v+'='+expression);return lines,v
        if tag=='trap-error' and len(args)==2:
            lines=[];body=self.save(self.closure([],args[0],env),lines);hndl=self.save(self.closure([],args[1],env),lines)
            v=self.save('invoke-protected(w,'+body+','+hndl+')',lines);return lines,v
        lines,f,args=self.call_parts(x,env);v=self.save('invoke(w,'+f+','+args+')',lines);return lines,v
    def tail(self,x,env):
        x=self.normalize(x)
        if isinstance(x,list) and x:
            tag=x[0] if isinstance(x[0],Symbol) else None;args=x[1:]
            if tag=='let' and len(args)==3:
                name,binding,body=args
                if not isinstance(name,Symbol):raise ValueError('malformed let')
                lines,b=self.value(binding,env);v=self.save(b,lines)
                return lines+self.tail(body,{**env,name:v})
            if tag=='if' and len(args)==3:
                lines,test=self.value(args[0],env)
                return lines+['if boolean('+test+') then '+block(self.tail(args[1],env))+' else '+block(self.tail(args[2],env))]
            if tag=='trap-error' and len(args)==2:
                lines=[];body=self.save(self.closure([],args[0],env),lines);hndl=self.save(self.closure([],args[1],env),lines)
                return lines+['Protected('+body+','+hndl+')']
            special=(tag=='defun' and len(args)==3) or (tag=='lambda' and len(args)==2) or (tag=='freeze' and len(args)==1)
            if not special:
                lines,f,arguments=self.call_parts(x,env);return lines+['TailApply('+f+','+arguments+')']
        lines,v=self.value(x,env);return lines+['Done('+v+')']
    def write(self,out,groups):
        out=pathlib.Path(out);out.mkdir(parents=True,exist_ok=True)
        entries=[[self.schedule([],form) for form in forms] for forms in groups]
        bodies=[];i=0
        while i<len(self.jobs):
            params,body,captures=self.jobs[i];env={};lines=[]
            for j,name in enumerate(captures):
                v=self.fresh();lines.append('val '+v+'=native-arg(captured,%d)'%j);env[name]=v
            for j,name in enumerate(params):
                v=self.fresh();lines.append('val '+v+'=native-arg(args,%d)'%j);env[name]=v
            lines.extend(self.tail(body,env))
            bodies.append('fun code%d(w:world,roots:ref<global,list<value>>,captured:list<value>,args:list<value>): <st<global>,exn,div,console> native-result '%i+block(lines));i+=1
        modules=[]
        for start in range(0,len(bodies),40):
            name='klpart'+str(start//40);modules.append(name)
            lines=['module '+name,'import shen/values','import shen/world','import shen/machine',*bodies[start:start+40],'pub fun install(w:world): <st<global>,exn,div> () '+block(['install-native(w,%d,code%d)'%(j,j) for j in range(start,min(start+40,len(bodies)))])]
            (out/(name+'.kk')).write_text('\n'.join(lines)+'\n')
        return {'modules':modules,'entries':entries,'code_count':len(bodies)}
