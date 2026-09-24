import sys,json,time,urllib.request,os
sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parent))
from app import api

# Deployment endpoint. Override with ATMAN_RELAY_URL.
# Default is a loopback placeholder for local simulation only.
RELAY_URL = os.environ.get("ATMAN_RELAY_URL", "http://127.0.0.1:18790").rstrip("/")
for _ in range(30):
 try:
  with urllib.request.urlopen(RELAY_URL+'/health',timeout=3) as r:
   if json.load(r).get('status')=='online':break
 except OSError:pass
 time.sleep(2)
result=api({'training':{'id':sys.argv[1],'command':'review'}})
print(json.dumps({'reply':result.get('reply'),'training':result.get('training')},indent=2))
