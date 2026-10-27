import hashlib,json,os,subprocess
from pathlib import Path
SRC=Path('F:/Github-PR/inspection/heartbeat1340-llm-sdk-js');OUT=Path('F:/Github-PR/ci-evidence/heartbeat1340-llm-sdk');STAGE=Path('C:/Users/lyz/AppData/Local/Temp/github-pr-1340-llm-sdk')
base=STAGE/'baseline-node20.20.2';files=[]
manifest=json.loads((OUT/'baseline-source-manifest.json').read_text())
for row in manifest['files']:
 path=row['path'];data=(STAGE/'baseline-node18.20.8'/path).read_bytes();assert hashlib.sha256(data).hexdigest()==row['canonicalSha256'];files.append((path,data))
changed={p:(SRC/p).read_bytes().replace(b'\r\n',b'\n') for p in ['src/utils.ts','test/headers.test.ts']}
rows=[]
for path,data in dict(files+list(changed.items())).items():rows.append({'path':path,'mode':'100644','sha256':hashlib.sha256(data).hexdigest(),'blob':hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()})
(OUT/'candidate-source-manifest.json').write_text(json.dumps({'baseline':manifest['head'],'branch':'fix-preserve-repeated-header-values','files':rows},indent=2))
def run(work,version,tag,commands,allowfail=False):
 runtime=STAGE/f'node-v{version}-win-x64';node=str(runtime/'node.exe');npm=str(runtime/'node_modules/npm/bin/npm-cli.js');env=os.environ.copy();env['PATH']=str(runtime)+os.pathsep+env['PATH'];result=[]
 for i,args in enumerate(commands):
  cmd=[node]+([npm]+args if args[0]=='npm' else args);cmd=[x for x in cmd if x!='npm'];log=STAGE/f'{tag}-{i}.raw.log'
  with log.open('wb') as f:p=subprocess.run(cmd,cwd=work,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=600)
  item={'command':cmd,'exit':p.returncode,'rawLog':str(log)};result.append(item);print(tag,i,p.returncode,flush=True)
  (OUT/f'{tag}-receipt.json').write_text(json.dumps({'stage':str(work),'runtime':version,'results':result},indent=2))
  if p.returncode and not allowfail:return False
 return True
for version in ['20.20.2','18.20.8','16.20.2']:
 work=STAGE/f'candidate-final2-node{version}';assert not work.exists()
 for path,data in dict(files+list(changed.items())).items():
  dest=work/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
 assert run(work,version,f'candidate-final2-node{version}-build', [['npm','ci','--no-audit','--no-fund'],['npm','run','build']])
 if version=='20.20.2':
  assert run(work,version,'candidate-final2-node20-ci-test',[
   ['npm','i','-D','@vitest/coverage-v8@^2.1.6','--no-audit','--no-fund'],
   ['npm','run','lint'],['npm','test','--','--coverage'],['node_modules/prettier/bin/prettier.cjs','--check','test/headers.test.ts'],['npm','ls','vitest','@vitest/coverage-v8','--json']])
