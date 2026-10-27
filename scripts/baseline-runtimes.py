import hashlib,json,os,subprocess,tarfile,urllib.request,zipfile
from pathlib import Path
SRC=Path('F:/Github-PR/inspection/heartbeat1340-llm-sdk-js');OUT=Path('F:/Github-PR/ci-evidence/heartbeat1340-llm-sdk');STAGE=Path('C:/Users/lyz/AppData/Local/Temp/github-pr-1340-llm-sdk');STAGE.mkdir(exist_ok=True)
HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=SRC).decode().strip();records=[]
entries=subprocess.check_output(['git','ls-tree','-r','-z',HEAD],cwd=SRC).split(b'\0')
files=[]
for entry in entries:
 if not entry:continue
 info,name=entry.split(b'\t');mode,kind,oid=info.decode().split();name=name.decode();assert kind=='blob'
 data=subprocess.check_output(['git','cat-file','blob',oid],cwd=SRC);raw=(SRC/name).read_bytes();files.append((name,data));records.append({'path':name,'mode':mode,'blob':oid,'canonicalSha256':hashlib.sha256(data).hexdigest(),'windowsRawSha256':hashlib.sha256(raw).hexdigest(),'sameBytes':data==raw,'crlfOnly':raw.replace(b'\r\n',b'\n')==data})
(OUT/'baseline-source-manifest.json').write_text(json.dumps({'head':HEAD,'files':records},indent=2))
for version in ['20.20.2','18.20.8','16.20.2']:
 name=f'node-v{version}-win-x64';archive=STAGE/(name+'.zip');runtime=STAGE/name
 if not archive.exists():
  urllib.request.urlretrieve(f'https://nodejs.org/dist/v{version}/SHASUMS256.txt',STAGE/f'SHASUMS256-{version}.txt');urllib.request.urlretrieve(f'https://nodejs.org/dist/v{version}/{name}.zip',archive)
 checks=(STAGE/f'SHASUMS256-{version}.txt').read_text();expected=next(x.split()[0] for x in checks.splitlines() if x.endswith(name+'.zip'));assert hashlib.sha256(archive.read_bytes()).hexdigest()==expected
 if not runtime.exists():
  with zipfile.ZipFile(archive) as z:z.extractall(STAGE)
 work=STAGE/f'baseline-node{version}'
 assert not work.exists(),str(work)
 for path,data in files:
  dest=work/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
 env=os.environ.copy();env['PATH']=str(runtime)+os.pathsep+env['PATH'];env['GIT_TERMINAL_PROMPT']='0';env['GCM_INTERACTIVE']='Never'
 npm=runtime/'node_modules/npm/bin/npm-cli.js';node=runtime/'node.exe';commands=[[str(node),'--version'],[str(node),str(npm),'--version'],[str(node),str(npm),'ci','--no-audit','--no-fund'],[str(node),str(npm),'run','build']]
 results=[]
 for i,cmd in enumerate(commands):
  log=STAGE/f'baseline-node{version}-{i}.raw.log'
  with log.open('wb') as f:p=subprocess.run(cmd,cwd=work,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=600)
  results.append({'command':cmd,'exit':p.returncode,'rawLog':str(log)});print(version,i,p.returncode,flush=True)
  (OUT/f'baseline-node{version}-receipt.json').write_text(json.dumps({'head':HEAD,'sourceManifest':'baseline-source-manifest.json','stage':str(work),'runtimeArchiveSha256':expected,'results':results},indent=2))
  if p.returncode:break
