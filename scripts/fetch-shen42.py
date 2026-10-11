#!/usr/bin/env python3
"""Fetch exact upstream distribution without rewriting its licensed contents."""
import hashlib,json,pathlib,shutil,tarfile,tempfile,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
URL='https://github.com/Shen-Language/shen-sources/releases/download/shen-42.2/ShenOSKernel-42.2.tar.gz'
def verify(directory,lock):
    actual={str(p.relative_to(directory)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in directory.rglob('*') if p.is_file()}
    if actual!=lock['sha256_by_file']: raise ValueError('pristine distribution hash mismatch')
def main():
    lock=json.loads((ROOT/'comparison/shen42.2-source.lock.json').read_text())
    target=ROOT/'vendor/ShenOSKernel-42.2'
    if target.exists():
        verify(target,lock);print('Verified existing pristine ShenOSKernel 42.2');return
    target.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.shen42-',dir=target.parent) as temp:
        temp=pathlib.Path(temp); archive=temp/'archive.tar.gz'
        with urllib.request.urlopen(URL,timeout=60) as response:
            payload=response.read(2*1024*1024+1)
        if len(payload)>2*1024*1024: raise ValueError('archive exceeds budget')
        if hashlib.sha256(payload).hexdigest()!=lock['distribution_sha256']:
            raise ValueError('upstream archive hash mismatch')
        archive.write_bytes(payload)
        with tarfile.open(archive) as tar:
            members=tar.getmembers()
            if sum(m.size for m in members)>16*1024*1024: raise ValueError('extraction exceeds budget')
            for member in members:
                path=pathlib.PurePosixPath(member.name)
                if path.is_absolute() or '..' in path.parts or path.parts[0]!='ShenOSKernel-42.2':
                    raise ValueError('unexpected archive path')
                if not (member.isfile() or member.isdir()): raise ValueError('unexpected archive member')
            tar.extractall(temp,members=members)
        verify(temp/'ShenOSKernel-42.2',lock)
        (temp/'ShenOSKernel-42.2').rename(target)
    print('Fetched and verified pristine ShenOSKernel 42.2')
if __name__=='__main__':main()
