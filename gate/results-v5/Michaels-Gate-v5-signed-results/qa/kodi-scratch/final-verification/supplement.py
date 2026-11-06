from audit import R,S,H,snapshot
import json,ast,tarfile,time
M=R/'reference-model'
print('COMMAND python3 -B supplement.py; CWD /workspace; static only')
for rel,base in [('reference-model/MANIFEST.sha256',M),('reference-model/MANIFEST-E.sha256',M),('reference-model/artifacts/inherited/V4_SOURCE.sha256',R/'inherited/v4/reference-model'),('reference-model/artifacts/CREW_EVIDENCE.sha256',M/'crew-evidence'),('reference-model/artifacts/v3_inherited/FROZEN_BATTERY.sha256',M)]:
 rows=[]
 for ln in (R/rel).read_text().splitlines():
  h,p=ln.split(maxsplit=1); fp=base/p; rows.append((p,'MISSING' if not fp.is_file() else 'OK' if H(fp.read_bytes())==h else 'MISMATCH'))
 print('HASH_LIST',rel,'BASE',str(base.relative_to(R)),'ENTRIES',len(rows),'FAILURES',[x for x in rows if x[1]!='OK'])
print('DIGESTS')
for rel in ['FILES.sha256','FILES.sha256.sig','PACKET.sig','SEAL.json','keys/NOTICE.md','keys/SYNTHETIC-test-log.pub','keys/SYNTHETIC-packet.pub','reference-model/artifacts/F1_FROZEN.json','reference-model/artifacts/F1_IMPL.json','reference-model/artifacts/F2_IMPL.json','reference-model/artifacts/q8F1_results.json','reference-model/artifacts/q8F2_results.json','reference-model/report.md','reference-model/HANDOFF.md','reference-model/artifacts/F2_TESTLOG.txt','reference-model/q8F.py','reference-model/q8F2.py','reference-model/corpora5.py']:
 print(H((R/rel).read_bytes()),rel)
# AST parse only; never import runnable package modules during this check.
fail=[]; n=0
for p in R.rglob('*.py'):
 n+=1
 try: ast.parse(p.read_text(),filename=str(p))
 except SyntaxError as e: fail.append((str(p.relative_to(R)),str(e)))
print('PYTHON_AST_SYNTAX',n,'FAILURES',fail)
meta1=json.loads((S/'pre-metadata.json').read_text()); meta2=json.loads((S/'final-metadata.json').read_text()); print('FULL_METADATA_EQUAL',meta1==meta2)
with tarfile.open('/workspace/michaels-gate-v5-candidate.tar','r:') as t: print('ARCHIVE_ROOTS',sorted({m.name.split('/')[0] for m in t}))
print('ARCHIVE_FINAL_SHA256',H(Path('/workspace/michaels-gate-v5-candidate.tar').read_bytes()))
print('NOW',time.strftime('%Y-%m-%d %H:%M:%S %Z%z'))
print('EXIT 0 (inspection script completed; findings are not an overall package PASS)')
