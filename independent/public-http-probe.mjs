import http from 'node:http';
import { once } from 'node:events';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const [checkoutArg, outputArg, label='baseline'] = process.argv.slice(2);
if (!checkoutArg || !outputArg) throw new Error('usage: node probe.mjs CHECKOUT OUTPUT_DIR LABEL');
const checkout=resolve(checkoutArg), output=resolve(outputArg);
await mkdir(output,{recursive:true});
const observed=[];
const server=http.createServer(async(req,res)=>{
  const body=[];for await(const chunk of req)body.push(chunk);
  observed.push({method:req.method,path:req.url,headers:req.headers,rawHeaders:req.rawHeaders,body:Buffer.concat(body).toString('utf8')});
  res.setHeader('content-type','application/json');
  res.end(JSON.stringify(req.url==='/api/tags'?{models:[]}:{model:'local-probe',response:'local',done:true}));
});
server.listen(0,'127.0.0.1');await once(server,'listening');
const host=`http://127.0.0.1:${server.address().port}`;
const cases=[
 ['tuple-repeat',()=>[['x-probe-values','first'],['x-probe-values','second']]],
 ['tuple-mixed-case',()=>[['X-Probe-Values','first'],['x-probe-values','second']]],
 ['tuple-repeat-mixed',()=>[['X-Probe-Values','first'],['x-probe-values','second'],['X-Probe-Values','third']]],
 ['tuple-single',()=>[['x-probe-values','first, second']]],
 ['headers-repeat',()=>new Headers([['x-probe-values','first'],['x-probe-values','second']])],
 ['record-merged',()=>({'x-probe-values':'first, second'})],
 ['record-case-variants',()=>({'X-Probe-Values':'first','x-probe-values':'second'})],
 ['tuple-default-control',()=>[['content-type','text/plain'],['accept','text/plain'],['x-probe-values','first']]],
 ['record-default-control',()=>({'CONTENT-TYPE':'text/plain',ACCEPT:'text/plain','x-probe-values':'first'})],
 ['headers-default-control',()=>new Headers({'content-type':'text/plain',accept:'text/plain','x-probe-values':'first'})],
 ['tuple-cookie-repeat',()=>[['cookie','a=1'],['cookie','b=2']]],
 ['tuple-set-cookie-repeat',()=>[['set-cookie','a=1'],['set-cookie','b=2']]],
 ['headers-set-cookie-repeat',()=>new Headers([['set-cookie','a=1'],['set-cookie','b=2']])],
 ['tuple-whitespace',()=>[['x-probe-values',' first '],['x-probe-values',' second ']]],
 ['no-headers',()=>undefined],
];
const snapshot=input=>input instanceof Headers?JSON.stringify([...input.entries()]):JSON.stringify(input);
const freezeInput=input=>{if(Array.isArray(input)){input.forEach(Object.freeze);Object.freeze(input);}else if(input&&!(input instanceof Headers))Object.freeze(input);return input;};
const receipts=[];
const capture=async(fn)=>{const before=observed.length;const result=await fn();if(observed.length!==before+1)throw Error('expected exactly one local HTTP request');return {request:observed.at(-1),result};};
try {
 const modules=[['node',await import(pathToFileURL(join(checkout,'dist/index.mjs')))],['browser',await import(pathToFileURL(join(checkout,'dist/browser.mjs')))]];
 for(const [entry,{Ollama}] of modules){
  for(const [name,make] of cases){
   const input=freezeInput(make()),before=snapshot(input);
   const expectedHeaders=Object.fromEntries(new Headers(input).entries());
   const native=await capture(async()=>{const r=await fetch(host+'/api/tags',{headers:input});return r.json();});
   const sdk=new Ollama({host,headers:input});
   for(const method of ['list','generate']){
    const got=await capture(()=>method==='list'?sdk.list():sdk.generate({model:'local-probe',prompt:'local',stream:false}));
    const keys=Object.keys(expectedHeaders).filter(k=>!['content-type','accept','user-agent'].includes(k));
    // Set-Cookie has special Headers iteration behavior. Native on-wire receipt is authoritative.
    const comparisons=keys.map(key=>({key,native:native.request.headers[key]??null,sdk:got.request.headers[key]??null,equal:JSON.stringify(native.request.headers[key]??null)===JSON.stringify(got.request.headers[key]??null)}));
    const controls={contentType:got.request.headers['content-type']==='application/json',accept:got.request.headers.accept==='application/json',callerUnchanged:snapshot(input)===before,expectedPath:got.request.path===(method==='list'?'/api/tags':'/api/generate'),expectedResult:method==='list'?Array.isArray(got.result.models):got.result.done===true};
    receipts.push({entry,name,method,expectedHeaders,native:native.request,sdk:got.request,comparisons,controls,pass:comparisons.every(x=>x.equal)&&Object.values(controls).every(Boolean)});
   }
   if(snapshot(input)!==before)throw Error('caller input mutated');
  }
  const a=new Ollama({host,headers:{'x-client':'alpha'}}),b=new Ollama({host,headers:{'x-client':'beta'}});
  for(const [name,client,value] of [['client-a-first',a,'alpha'],['client-b',b,'beta'],['client-a-second',a,'alpha']]){
   const got=await capture(()=>client.list());receipts.push({entry,name,method:'list',sdk:got.request,pass:got.request.headers['x-client']===value});
  }
 }
 const files={};
 for(const f of ['src/utils.ts','src/browser.ts','src/index.ts','src/interfaces.ts','package.json','package-lock.json','dist/index.mjs','dist/browser.mjs']){const bytes=await readFile(join(checkout,f));files[f]={bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')};}
 const report={label,node:process.version,platform:process.platform,arch:process.arch,checkout,startedLocalHost:host,externalNetworkUsed:false,sourceFiles:files,cases:receipts.length,passed:receipts.filter(x=>x.pass).length,failed:receipts.filter(x=>!x.pass).length,receipts};
 await writeFile(join(output,label+'.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({label,cases:report.cases,passed:report.passed,failed:report.failed,failures:receipts.filter(x=>!x.pass).map(({entry,name,method,comparisons,controls})=>({entry,name,method,comparisons,controls}))},null,2));
} finally {server.closeAllConnections();await new Promise((resolve,reject)=>server.close(err=>err?reject(err):resolve()));}
