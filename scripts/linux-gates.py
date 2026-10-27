import hashlib,io,json,os,socket,subprocess,tarfile,urllib.request
from pathlib import Path
ROOT=Path('F:/Github-PR/ci-evidence/heartbeat1340-llm-sdk');S=Path('C:/Users/lyz/AppData/Local/Temp/github-pr-1340-llm-sdk');SRC=Path('F:/Github-PR/inspection/heartbeat1340-llm-sdk-js');socket.setdefaulttimeout(90)
runner=r'''import hashlib,json,os,shutil,subprocess,tarfile
from pathlib import Path
R=Path('/home/node/validation');OUT=R/'output';OUT.mkdir();RUN=R/'runtimes';RUN.mkdir()
for version in ['16.20.2','18.20.8','20.20.2']:
 with tarfile.open(R/f'node-v{version}-linux-x64.tar.xz') as t:t.extractall(RUN)
results=[]
def run(work,version,tag,args):
 runtime=RUN/f'node-v{version}-linux-x64';node=runtime/'bin/node';npm=runtime/'lib/node_modules/npm/bin/npm-cli.js';env=os.environ.copy();env['PATH']=str(runtime/'bin')+':'+env['PATH'];env['npm_config_cache']=str(R/'npm-cache');cmd=[str(node)]+([str(npm)]+args[1:] if args[0]=='npm' else args);log=OUT/(tag+'.raw.log')
 with log.open('wb') as f:p=subprocess.run(cmd,cwd=work,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=600)
 row={'tag':tag,'cwd':str(work),'command':cmd,'exit':p.returncode};results.append(row);(OUT/'receipt.json').write_text(json.dumps(results,indent=2));print(tag,p.returncode,flush=True);assert p.returncode==0
for kind in ['baseline','candidate']:
 for version in ['16.20.2','18.20.8','20.20.2']:
  work=R/f'{kind}-node{version}';shutil.copytree(R/'sources'/kind,work);tag=f'{kind}-node{version}'
  run(work,version,tag+'-version',['--version']);run(work,version,tag+'-npm-version',['npm','--version']);run(work,version,tag+'-ci',['npm','ci','--no-audit','--no-fund']);run(work,version,tag+'-build',['npm','run','build'])
  if version=='20.20.2':
   run(work,version,tag+'-install-coverage',['npm','i','-D','@vitest/coverage-v8@^2.1.6','--no-audit','--no-fund']);run(work,version,tag+'-lint',['npm','run','lint']);run(work,version,tag+'-test-coverage',['npm','test','--','--coverage']);run(work,version,tag+'-dependency-versions',['npm','ls','vitest','@vitest/coverage-v8','--json'])
  changed=[]
  for p in (R/'sources'/kind).rglob('*'):
   if p.is_file():
    rel=p.relative_to(R/'sources'/kind);after=work/rel
    if after.read_bytes()!=p.read_bytes():changed.append(str(rel))
  (OUT/(tag+'-source-after.json')).write_text(json.dumps({'changedFromCanonicalSource':changed,'ciDependencyOverlayAllowed':version=='20.20.2'},indent=2));assert set(changed)<=({'package.json','package-lock.json'} if version=='20.20.2' else set())
'''
archives=[]
for v in ['16.20.2','18.20.8','20.20.2']:
 name=f'node-v{v}-linux-x64.tar.xz';p=S/name
 if not p.exists():urllib.request.urlretrieve(f'https://nodejs.org/dist/v{v}/{name}',p)
 expected=next(x.split()[0] for x in (S/f'SHASUMS256-{v}.txt').read_text().splitlines() if x.endswith(name));assert hashlib.sha256(p.read_bytes()).hexdigest()==expected;archives.append((name,p))
manifest=json.loads((ROOT/'baseline-source-manifest.json').read_text());tarpath=S/'linux-input.tar'
with tarfile.open(tarpath,'w') as t:
 for kind in ['baseline','candidate']:
  files={x['path']:(S/'baseline-node18.20.8'/x['path']).read_bytes() for x in manifest['files']}
  if kind=='candidate':files.update({p:(SRC/p).read_bytes().replace(b'\r\n',b'\n') for p in ['src/utils.ts','test/headers.test.ts']})
  for name,data in files.items():
   info=tarfile.TarInfo('sources/'+kind+'/'+name);info.size=len(data);info.mode=0o644;t.addfile(info,io.BytesIO(data))
 for name,p in archives:t.add(p,arcname=name)
 data=runner.encode();info=tarfile.TarInfo('runner.py');info.size=len(data);info.mode=0o644;t.addfile(info,io.BytesIO(data))
receipt={'inputTarSha256':hashlib.sha256(tarpath.read_bytes()).hexdigest(),'container':'heartbeat1340-llm-sdk-linux','image':'node:24.22.1-bookworm','limitMemory':'3g','cpus':2,'nonrootUser':'node'};(ROOT/'linux-launch.json').write_text(json.dumps(receipt,indent=2))
commands=[['docker','create','--name','heartbeat1340-llm-sdk-linux','--user','node','--workdir','/home/node','--memory','3g','--cpus','2','--label','codex.owner=heartbeat1340-llm-sdk','node:24.22.1-bookworm','sleep','infinity'],['docker','start','heartbeat1340-llm-sdk-linux'],['docker','cp',str(tarpath),'heartbeat1340-llm-sdk-linux:/home/node/input.tar'],['docker','exec','heartbeat1340-llm-sdk-linux','bash','-lc','mkdir /home/node/validation && tar -xf /home/node/input.tar -C /home/node/validation && python3 /home/node/validation/runner.py']]
for i,cmd in enumerate(commands):
 with (S/f'linux-launch-{i}.raw.log').open('wb') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=1800)
 print('launch',i,p.returncode,flush=True);assert p.returncode==0
p=subprocess.run(['docker','cp','heartbeat1340-llm-sdk-linux:/home/node/validation/output',str(S/'linux-output')],capture_output=True);print('copy logs',p.returncode,flush=True);assert p.returncode==0
