import hashlib,json,os,shutil,subprocess,tarfile
from pathlib import Path
O=Path('F:/Github-PR/ci-evidence/heartbeat1340-llm-sdk');S=Path('C:/Users/lyz/AppData/Local/Temp/github-pr-1340-llm-sdk');R=S/'node-v20.20.2-win-x64';node=str(R/'node.exe');npm=str(R/'node_modules/npm/bin/npm-cli.js');env=os.environ.copy();env['PATH']=str(R)+os.pathsep+env['PATH'];records=[]
for kind in ['candidate-final2']:
 work=S/f'{kind}-node18.20.8';dest=S/f'{kind}-package';dest.mkdir();consumer=S/f'{kind}-consumer';consumer.mkdir()
 commands=[('pack',[node,npm,'pack','--json','--pack-destination',str(dest)],work)]
 def run(tag,cmd,cwd):
  log=S/f'{kind}-{tag}.raw.log'
  with log.open('wb') as f:p=subprocess.run(cmd,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=600)
  records.append({'kind':kind,'tag':tag,'command':cmd,'cwd':str(cwd),'exit':p.returncode,'rawLog':str(log)});(O/'package-final2-receipt.json').write_text(json.dumps(records,indent=2));print(kind,tag,p.returncode,flush=True);assert p.returncode==0
 run(*commands[0]);tgz=next(dest.glob('*.tgz'))
 run('install',[node,npm,'install',str(tgz),'--no-audit','--no-fund'],consumer)
 manifests=[]
 with tarfile.open(tgz) as t:
  for member in t.getmembers():
   if not member.isfile():continue
   rel=Path(member.name).relative_to('package');data=t.extractfile(member).read();installed=consumer/'node_modules/ollama'/rel;assert installed.read_bytes()==data;manifests.append({'path':str(rel).replace('\\','/'),'mode':oct(member.mode),'sha256':hashlib.sha256(data).hexdigest(),'installedEqual':True})
 (O/f'{kind}-packed-installed-files.json').write_text(json.dumps({'tarballSha256':hashlib.sha256(tgz.read_bytes()).hexdigest(),'files':manifests},indent=2))
 shutil.copyfile(O/'installed-http-probe.mjs',consumer/'probe.mjs')
 run('installed-http',[node,'probe.mjs',str(S/f'{kind}-installed-http.json')],consumer)
 shutil.copyfile(S/f'{kind}-installed-http.json',O/f'{kind}-installed-http.json')
