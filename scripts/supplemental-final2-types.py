import json,os,subprocess
from pathlib import Path
S=Path('C:/Users/lyz/AppData/Local/Temp/github-pr-1340-llm-sdk');O=Path('F:/Github-PR/ci-evidence/heartbeat1340-llm-sdk');runtime=S/'node-v20.20.2-win-x64';node=str(runtime/'node.exe');npm=str(runtime/'node_modules/npm/bin/npm-cli.js');env=os.environ.copy();env['PATH']=str(runtime)+os.pathsep+env['PATH'];rows=[]
for kind in ['candidate-final2']:
 work=S/f'{kind}-node20.20.2'
 cmds=[]
 if kind=='candidate-final2':cmds.append([node,'node_modules/typescript/bin/tsc','--noEmit'])
 cmds += [[node,npm,'i','--no-save','@types/node@20','--no-audit','--no-fund'],[node,'node_modules/typescript/bin/tsc','--noEmit','--lib','es2020,dom'],[node,npm,'ls','@types/node','--json']]
 for i,cmd in enumerate(cmds):
  pth=S/f'{kind}-supplemental-types-{i}.raw.log'
  with pth.open('wb') as f:p=subprocess.run(cmd,cwd=work,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=600)
  rows.append({'kind':kind,'command':cmd,'exit':p.returncode,'rawLog':str(pth)});print(kind,i,p.returncode,flush=True);(O/'supplemental-final2-types-receipt.json').write_text(json.dumps(rows,indent=2))
