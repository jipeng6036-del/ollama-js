import ast,hashlib,io,json,os,subprocess,tarfile,threading,time
from pathlib import Path
O=Path('F:/Github-PR/ci-evidence/heartbeat1340-llm-sdk');S=Path('C:/Users/lyz/AppData/Local/Temp/github-pr-1340-llm-sdk');SRC=Path('F:/Github-PR/inspection/heartbeat1340-llm-sdk-js');NAME='heartbeat1340-llm-sdk-linux-last'
tree=ast.parse((O/'linux-gates.py').read_text());old=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='runner' for t in n.targets)))
a=old.index('def run(');b=old.index("for kind in ['baseline','candidate']:")
run=r'''NETWORK_ACTIVE=False

def environment(version,verbose=True):
 runtime=RUN/f'node-v{version}-linux-x64';env=os.environ.copy();env['PATH']=str(runtime/'bin')+':'+env['PATH'];env['npm_config_cache']=str(R/'npm-cache')
 if NETWORK_ACTIVE:env.update(npm_config_fetch_timeout='60000',npm_config_fetch_retries='1',npm_config_maxsockets='3')
 env['npm_config_loglevel']='verbose' if verbose else 'silent'
 return runtime,env

def run(work,version,tag,args):
 runtime,env=environment(version);node=runtime/'bin/node';npm=runtime/'lib/node_modules/npm/bin/npm-cli.js';cmd=[str(node)]+([str(npm)]+args[1:] if args[0]=='npm' else args);log=OUT/(tag+'.raw.log');start=time.monotonic();timed_out=False
 print('COMMAND_BEGIN '+json.dumps({'tag':tag,'command':cmd}),flush=True)
 with log.open('wb') as f:
  p=subprocess.Popen(cmd,cwd=work,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
  def copy():
   while True:
    data=p.stdout.read1(65536)
    if not data:break
    f.write(data);f.flush();sys.stdout.buffer.write(data);sys.stdout.buffer.flush()
  thread=threading.Thread(target=copy,daemon=True);thread.start()
  try:p.wait(timeout=600)
  except subprocess.TimeoutExpired:
   timed_out=True;os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=20)
  thread.join(timeout=20)
 row={'tag':tag,'cwd':str(work),'command':cmd,'exit':p.returncode,'timedOut':timed_out,'seconds':time.monotonic()-start,'environment':{'npm_config_fetch_timeout':'60000','npm_config_fetch_retries':'1','npm_config_maxsockets':'3','npm_config_loglevel':'verbose'} if NETWORK_ACTIVE else {'npm_config_loglevel':'verbose'}};results.append(row);(OUT/'receipt.json').write_text(json.dumps(results,indent=2));print('COMMAND_END '+json.dumps(row),flush=True);assert p.returncode==0 and not timed_out

def config(key,tag):
 runtime,env=environment('20.20.2',False);cmd=[str(runtime/'bin/node'),str(runtime/'lib/node_modules/npm/bin/npm-cli.js'),'config','get',key];p=subprocess.run(cmd,cwd=R,env=env,capture_output=True,timeout=60);(OUT/(tag+'.stdout.raw')).write_bytes(p.stdout);(OUT/(tag+'.stderr.raw')).write_bytes(p.stderr);sys.stdout.buffer.write(p.stdout);sys.stdout.buffer.flush();assert p.returncode==0;return p.stdout.decode().strip()
defaults={k:config(k,'config-default-'+k) for k in ['fetch-timeout','fetch-retries','maxsockets','audit']};assert int(defaults['fetch-timeout'])*(int(defaults['fetch-retries'])+1)>600000;assert defaults['audit']=='true'
NETWORK_ACTIVE=True
effective={k:config(k,'config-effective-'+k) for k in ['fetch-timeout','fetch-retries','maxsockets','audit']};assert effective=={'fetch-timeout':'60000','fetch-retries':'1','maxsockets':'3','audit':'true'};(OUT/'network-budget.json').write_text(json.dumps({'defaults':defaults,'effective':effective,'reason':'Normal default retry budget exceeds the 600-second outer step cap; bounded recovery, root cause unconfirmed.'},indent=2))
'''
body=old[b:].replace(",'--no-audit','--no-fund'",'')
body=body.replace("(OUT/(tag+'-source-after.json')).write_text", "\n  if version=='20.20.2':\n   shutil.copyfile(work/'package.json',OUT/(tag+'-package.json'));shutil.copyfile(work/'package-lock.json',OUT/(tag+'-package-lock.json'))\n  (OUT/(tag+'-source-after.json')).write_text")
extra=r'''
for kind,artifact in [('baseline','baseline-package.tgz'),('candidate-final2','candidate-package.tgz')]:
 consumer=R/(kind+'-consumer');consumer.mkdir();shutil.copyfile(R/'installed-http-probe.mjs',consumer/'probe.mjs');run(consumer,'20.20.2',kind+'-package-install',['npm','install',str(R/artifact)]);members=[]
 with tarfile.open(R/artifact) as t:
  for member in t.getmembers():
   if not member.isfile():continue
   path=Path(member.name).relative_to('package');data=t.extractfile(member).read();installed=consumer/'node_modules/ollama'/path;assert installed.read_bytes()==data;members.append({'path':str(path),'mode':oct(member.mode),'sha256':hashlib.sha256(data).hexdigest()})
 (OUT/(kind+'-installed-files.json')).write_text(json.dumps({'tarballSha256':hashlib.sha256((R/artifact).read_bytes()).hexdigest(),'files':members},indent=2));report=OUT/(kind+'-installed-http.json');run(consumer,'20.20.2',kind+'-installed-http',['probe.mjs',str(report)]);data=json.loads(report.read_text());assert data['failed']==0 if kind=='candidate-final2' else data['failed']>0
'''
final=r'''
finally:
 audit={}
 for kind in ['baseline','candidate']:
  expected=json.loads((R/('expected-'+kind+'.json')).read_text())['files'];rows=[]
  for row in expected:
   path=R/'sources'/kind/row['path'];digest=hashlib.sha256(path.read_bytes()).hexdigest();assert digest==row.get('sha256',row.get('canonicalSha256'));assert path.stat().st_mode&511==int(row['mode'][-3:],8);rows.append({'path':row['path'],'sha256':digest,'mode':row['mode']})
  audit[kind]={'count':len(rows),'files':rows}
 (OUT/'input-source-audit.json').write_text(json.dumps(audit,indent=2));debug=OUT/'npm-debug';debug.mkdir(exist_ok=True)
 for p in (R/'npm-cache/_logs').glob('*.log'):shutil.copyfile(p,debug/p.name)
'''
runner=old[:a].replace('import hashlib,json,os,shutil,subprocess,tarfile','import hashlib,json,os,shutil,subprocess,tarfile,threading,time,signal,sys')+run+'try:\n'+''.join(' '+line+'\n' for line in (body+extra).splitlines())+final
compile(runner,'runner.py','exec');(S/'linux-last-runner.py').write_text(runner)
manifest=json.loads((O/'baseline-source-manifest.json').read_text());tarpath=S/'linux-last-input.tar'
with tarfile.open(tarpath,'w') as t:
 def add(name,data):
  info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o644;t.addfile(info,io.BytesIO(data))
 for kind in ['baseline','candidate']:
  files={x['path']:(S/'baseline-node18.20.8'/x['path']).read_bytes() for x in manifest['files']}
  if kind=='candidate':files.update({p:(SRC/p).read_bytes().replace(b'\r\n',b'\n') for p in ['src/utils.ts','test/headers.test.ts']})
  for name,data in files.items():add('sources/'+kind+'/'+name,data)
 for v in ['16.20.2','18.20.8','20.20.2']:
  p=S/f'node-v{v}-linux-x64.tar.xz';t.add(p,arcname=p.name)
 add('runner.py',runner.encode());add('expected-baseline.json',(O/'baseline-source-manifest.json').read_bytes());add('expected-candidate.json',(O/'candidate-source-manifest.json').read_bytes());add('installed-http-probe.mjs',(O/'installed-http-probe.mjs').read_bytes());add('baseline-package.tgz',next((S/'baseline-package').glob('*.tgz')).read_bytes());add('candidate-package.tgz',next((S/'candidate-final2-package').glob('*.tgz')).read_bytes())
(O/'linux-last-launch.json').write_text(json.dumps({'container':NAME,'image':'node:24.22.1-bookworm','inputTarSha256':hashlib.sha256(tarpath.read_bytes()).hexdigest(),'sourceIndexTree':'f5e7f5ec4286a58f9e1a444181aaeee2574a5f2c','environmentRecovery':{'fetch_timeout':60000,'fetch_retries':1,'maxsockets':3},'auditDisabled':False,'fullCIArgv':True},indent=2))
def step(tag,cmd,timeout=120):
 with (S/(tag+'.stdout.raw')).open('wb') as out,(S/(tag+'.stderr.raw')).open('wb') as err:
  p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  def pump(stream,dest):
   while True:
    data=stream.read1(65536)
    if not data:break
    dest.write(data);dest.flush()
  ts=[threading.Thread(target=pump,args=x) for x in [(p.stdout,out),(p.stderr,err)]]
  for th in ts:th.start()
  try:p.wait(timeout=timeout)
  except subprocess.TimeoutExpired:p.kill();p.wait();raise
  for th in ts:th.join()
 print(tag,p.returncode,flush=True);return p.returncode
assert step('linux-last-create',['docker','create','--name',NAME,'--user','node','--workdir','/home/node','--memory','3g','--cpus','2','--tmpfs','/home/node/validation:rw,exec,size=2147483648,uid=1000,gid=1000,mode=0755','--label','codex.owner=heartbeat1340-llm-sdk','node:24.22.1-bookworm','sleep','infinity'])==0
assert step('linux-last-start',['docker','start',NAME])==0
assert step('linux-last-input-copy',['docker','cp',str(tarpath),NAME+':/home/node/input.tar'])==0
code=step('linux-last-run',['docker','exec',NAME,'bash','-lc','tar -xf /home/node/input.tar -C /home/node/validation && python3 /home/node/validation/runner.py'],timeout=2400)
archive=S/'linux-last-output.tar'
with archive.open('wb') as out:p=subprocess.run(['docker','exec',NAME,'tar','-C','/home/node/validation','-cf','-','output'],stdout=out,stderr=subprocess.PIPE,timeout=120)
(S/'linux-last-export.stderr.raw').write_bytes(p.stderr);assert p.returncode==0 and archive.stat().st_size>1024
with tarfile.open(archive) as t:t.extractall(S/'linux-last-exported')
export=S/'linux-last-exported/output';assert (export/'receipt.json').is_file() and (export/'input-source-audit.json').is_file();rows=[]
for file in export.rglob('*'):
 if file.is_file():rows.append({'path':str(file.relative_to(export)),'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
(O/'linux-last-export-manifest.json').write_text(json.dumps({'runnerExit':code,'archiveSha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'files':rows},indent=2));assert step('linux-last-stop',['docker','stop','--timeout','10',NAME])==0
assert code==0,'Final bounded recovery did not complete all gates; no PR.'
