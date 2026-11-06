import os,sys,json,hashlib,stat,tarfile,subprocess,platform,time
from pathlib import Path
R=Path('/workspace/michaels-gate-v5-candidate'); S=Path(__file__).parent
H=lambda b:hashlib.sha256(b).hexdigest()
def snapshot(label):
 rows=[]; meta=[]
 for p in sorted(R.rglob('*')):
  rel=str(p.relative_to(R)); st=p.lstat(); typ='dir' if stat.S_ISDIR(st.st_mode) else 'file' if stat.S_ISREG(st.st_mode) else 'unsafe'
  meta.append({'path':rel,'type':typ,'mode':oct(stat.S_IMODE(st.st_mode)),'size':st.st_size})
  if typ=='file': rows.append(f'{H(p.read_bytes())}  {rel}\n')
 data=''.join(rows).encode(); (S/f'{label}-tree.sha256').write_bytes(data); (S/f'{label}-metadata.json').write_text(json.dumps(meta,indent=2))
 print(label,'files',len(rows),'tree_digest',H(data),'bytes',sum(x['size'] for x in meta if x['type']=='file'),'unsafe',[x['path'] for x in meta if x['type']=='unsafe'])
 return {ln.split('  ',1)[1].strip():ln.split('  ',1)[0] for ln in rows}
def run(cmd,cwd=R):
 print('COMMAND',json.dumps(cmd),'CWD',str(cwd),flush=True)
 p=subprocess.run(cmd,cwd=cwd,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 print(p.stdout,end=''); print('EXIT',p.returncode,flush=True)
 return p.returncode
if __name__=='__main__':
 print('DATE',time.strftime('%Y-%m-%d %H:%M:%S %Z%z')); print('ENV',platform.platform(),sys.version); run(['python3','-c','import numpy,cryptography; print("numpy",numpy.__version__,"cryptography",cryptography.__version__)'])
 pre=snapshot('pre'); a=Path('/workspace/michaels-gate-v5-candidate.tar'); print('ARCHIVE',a.stat().st_size,H(a.read_bytes()))
 listed={ln.split('  ',1)[1]:ln.split('  ',1)[0] for ln in (R/'FILES.sha256').read_text().splitlines()}
 print('UNSIGNED_FILES',sorted(set(pre)-set(listed))); print('MISSING_FILES',sorted(set(listed)-set(pre)))
 print('MANIFEST_MISMATCH',[p for p,h in listed.items() if pre.get(p)!=h])
 entries=[]; unsafe=[]; seen=set(); tarfiles={}; tarmodes={}
 with tarfile.open(a,'r:') as t:
  for m in t:
   parts=Path(m.name).parts
   if m.name.startswith('/') or '..' in parts or not (m.isdir() or m.isfile()) or m.name in seen: unsafe.append(m.name)
   seen.add(m.name); entries.append({'name':m.name,'type':m.type.decode(),'size':m.size,'mode':oct(m.mode)})
   if m.isfile():
    rel='/'.join(parts[1:]); tarfiles[rel]=H(t.extractfile(m).read()); tarmodes[rel]=m.mode
 (S/'archive-inventory.json').write_text(json.dumps(entries,indent=2))
 print('ARCHIVE_UNSAFE',unsafe); print('ARCHIVE_MATCHES_TREE',tarfiles==pre,'file_count',len(tarfiles)); print('ARCHIVE_ONLY',sorted(set(tarfiles)-set(pre))); print('TREE_ONLY',sorted(set(pre)-set(tarfiles))); print('ARCHIVE_CHANGED',[p for p in pre if p in tarfiles and pre[p]!=tarfiles[p]])
 print('ARCHIVE_MODE_MISMATCH',[p for p in pre if p in tarmodes and stat.S_IMODE((R/p).stat().st_mode)!=tarmodes[p]])
 print('PRIVATE_KEY_METADATA_ONLY',[(p,oct(stat.S_IMODE((R/p).stat().st_mode))) for p in pre if p.endswith(('.key','.pem'))]); print('NO_PRIVATE_KEY_CONTENT_PRINTED')
 run(['python3','-B','verify_static.py'])
 snapshot('post-static')
