import json,subprocess
from pathlib import Path
O=Path('F:/Github-PR/ci-evidence/heartbeat1340-llm-sdk');N='heartbeat1340-llm-sdk-linux-last'
code='''from pathlib import Path
import os,signal,json
found=[]
for p in Path('/proc').iterdir():
 if p.name.isdigit():
  try:
   c=(p/'cmdline').read_bytes().split(b'\\0')[0].decode()
   if c.startswith('npm i @vitest/coverage-v8@'):
    os.kill(int(p.name),signal.SIGUSR1);found.append({'pid':int(p.name),'command':c.strip()})
  except (FileNotFoundError,PermissionError):pass
print(json.dumps({'opened':bool(found),'targets':found}))'''
p=subprocess.run(['docker','exec',N,'python3','-c',code],capture_output=True,timeout=20);(O/'linux-last-inspector-final-signal.stdout.raw').write_bytes(p.stdout);(O/'linux-last-inspector-final-signal.stderr.raw').write_bytes(p.stderr);assert p.returncode==0;d=json.loads(p.stdout);print(d,flush=True)
if d['opened']:
 script=r'''(async()=>{
 let ws;let timer;const pending=new Map();let id=0
 const run=async()=>{
  const list=await(await fetch('http://127.0.0.1:9229/json/list')).json();ws=new WebSocket(list[0].webSocketDebuggerUrl)
  await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=()=>reject(new Error('open failed'))})
  ws.onmessage=ev=>{const d=JSON.parse(ev.data);if(pending.has(d.id)){pending.get(d.id)(d);pending.delete(d.id)}}
  const call=expression=>new Promise(resolve=>{const n=++id;pending.set(n,resolve);ws.send(JSON.stringify({id:n,method:'Runtime.evaluate',params:{expression,returnByValue:true}}))})
  const expression=`JSON.stringify({requests:process._getActiveRequests().map(r=>({constructor:r?.constructor?.name,path:typeof r.path==='string' && r.path.startsWith('/home/node/validation/')?r.path:undefined})),handles:process._getActiveHandles().map(h=>({constructor:h?.constructor?.name,remoteAddress:typeof h.remoteAddress==='string'?h.remoteAddress:undefined,remotePort:typeof h.remotePort==='number'?h.remotePort:undefined,readyState:typeof h.readyState==='string'?h.readyState:undefined,eventNames:typeof h.eventNames==='function'?h.eventNames().filter(x=>typeof x==='string'):[],registryPath:h._httpMessage?.host==='registry.npmjs.org' && typeof h._httpMessage.path==='string'?h._httpMessage.path.split('?')[0]:undefined}))})`
  const answer=await call(expression);const value=answer.result?.result?.value
  if(typeof value==='string')console.log(value);else console.log(JSON.stringify({status:'no-permitted-value',exceptionClass:answer.result?.exceptionDetails?.exception?.className}))
  await call("setTimeout(()=>{try{process.mainModule.require('node:inspector').close()}catch{}},20); true")
  return {status:'inspector-close-scheduled'}
 }
 try{const result=await Promise.race([run(),new Promise(resolve=>{timer=setTimeout(()=>resolve({status:'inspector-evaluation-timeout'}),12000)})]);console.log(JSON.stringify(result))}catch(e){console.log(JSON.stringify({status:'inspector-read-failed',constructor:e.constructor.name}))}finally{clearTimeout(timer);if(ws)ws.close();setTimeout(()=>process.exit(0),30)}
})()'''
 p=subprocess.run(['docker','exec','-i',N,'/usr/local/bin/node','-'],input=script.encode(),capture_output=True,timeout=20);(O/'linux-last-inspector-final-active.stdout.raw').write_bytes(p.stdout);(O/'linux-last-inspector-final-active.stderr.raw').write_bytes(p.stderr);print('inspector client',p.returncode,flush=True)
