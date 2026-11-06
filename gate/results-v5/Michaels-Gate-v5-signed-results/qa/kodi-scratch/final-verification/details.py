import ast,hashlib,json,numpy as np
from pathlib import Path
from audit import R,S,H,snapshot
M=R/'reference-model'
def j(p): return json.loads(p.read_text())
def assignment(p,name):
 for n in ast.parse(p.read_text()).body:
  if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets): return ast.literal_eval(n.value)
def c(label,a,b): print(label,'PASS' if a==b else 'FAIL','actual',a,'expected',b)
print('STATIC DATA INSPECTION; no evaluation streams/tests/replay run')
fz=j(M/'artifacts/F1_FROZEN.json')
c('F1 corpus spec digest',H(json.dumps(assignment(M/'corpora5.py','SPEC'),sort_keys=True).encode()),fz['corpora_spec_sha256'])
c('F1 generator digest',H((M/'corpora5.py').read_bytes()),fz['corpora5_py_sha256'])
for lab,fp,key,field in [('v3',M/'artifacts/v3_inherited/Q8_FROZEN.json','protocol','protocol_sha256'),('v4',M/'artifacts/V4_FROZEN.json','proto4','proto4_sha256'),('E',M/'artifacts/E_FROZEN.json','proto_E','proto_E_sha256')]:
 f=j(fp); c(lab+' protocol digest',H(json.dumps(f[key],sort_keys=True).encode()),f[field])
with np.load(M/'artifacts/v3_inherited/q8_corpora.npz',allow_pickle=False) as z:
 h=hashlib.sha256()
 for k in sorted(z.files): h.update(k.encode()); h.update(np.ascontiguousarray(z[k]).tobytes())
 c('v3 logical corpus digest',h.hexdigest(),j(M/'artifacts/v3_inherited/Q8_FROZEN.json')['corpora_sha256'])
print('v3 NPZ byte size',(M/'artifacts/v3_inherited/q8_corpora.npz').stat().st_size,'sha256',H((M/'artifacts/v3_inherited/q8_corpora.npz').read_bytes()))
for st in ('F1','F2'):
 im=j(M/f'artifacts/{st}_IMPL.json'); r=j(M/f'artifacts/q8{st}_results.json');
 c(st+' results embedded freeze',r['frozen'],fz); c(st+' results embedded registration',r['impl'],im)
 tree=ast.parse((M/('q8F.py' if st=='F1' else 'q8F2.py')).read_text()); fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='acceptance')
 ns={}; exec(compile(ast.Module(body=[fn],type_ignores=[]),'<saved-data-acceptance-only>','exec'),ns)
 acc=ns['acceptance'](r['results']['F']); norm=json.loads(json.dumps(acc))
 c(st+' saved acceptance recomputed',norm,r['acceptance_F_metrics']); print(st+' criteria',{k:v[1] for k,v in acc.items()})
 print(st+' failures',[k for k,v in acc.items() if not v[1]])
 print(st+' drift5 FRR',r['results']['F']['drift5']['clean_false_reject_rate']); print(st+' holdout5 FRR',r['results']['F']['holdout5']['clean_false_reject_rate']); print(st+' bulk fraction',r['results']['F']['pkg_bulk_diluted']['max_nonimprint_mem_frac'])
 if st=='F1': a=ast.dump(fn,include_attributes=False)
 else: c('F1/F2 acceptance function AST identity',ast.dump(fn,include_attributes=False),a)
print('FREEZE_HISTORY_ARTIFACTS',[str(p.relative_to(R)) for p in R.rglob('*') if p.name=='.git' or p.suffix=='.bundle' or 'git-log' in p.name or 'git-history' in p.name])
print('F1 original freeze spec/gate hashes are historical; current registration supersedes:')
for f,k in [('V5-SPEC.md','v5_spec_sha256'),('gate/gate5.py','gate5_py_sha256')]: print(f,'original',fz[k],'current',H((M/f).read_bytes()))
for root,manifest in [(R/'inherited/v4/reference-model','artifacts/bundle/MANIFEST.json')]:
 missing=[]; mismatch=[]
 for f,h in j(root/manifest)['files'].items():
  if not (root/f).is_file(): missing.append(f)
  elif H((root/f).read_bytes())!=h: mismatch.append(f)
 print('INHERITED_V4_SIGNED_MISSING',missing,'MISMATCH',mismatch)
for rel in ['reference-model/artifacts/inherited/V4_SOURCE.sha256','reference-model/artifacts/CREW_EVIDENCE.sha256','ruling/SHA256SUMS','inherited/v4/ruling/SHA256SUMS','inherited/v3/sealed-package-sha256.txt']:
 print('PATH_MANIFEST',rel)
 for ln in (R/rel).read_text().splitlines():
  if not ln.strip(): continue
  h,f=ln.split(maxsplit=1); target=(R/rel).parent/f
  print('  PATH',f,'ABSOLUTE',Path(f).is_absolute(),'parent_relative_exists',target.is_file())
print('STATIC RUNNABLE_PATH_HITS')
for p in R.rglob('*'):
 if p.suffix not in ('.py','.sh') or not p.is_file(): continue
 for n,line in enumerate(p.read_text().splitlines(),1):
  if '/workspace/' in line: print(str(p.relative_to(R)),n,line.strip())
print('POST',snapshot('final'))
