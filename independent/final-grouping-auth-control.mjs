import {writeFile,readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {join} from 'node:path';
const root='C:/Users/lyz/AppData/Local/Temp/github-pr-1340-llm-sdk';
const out='F:/Github-PR/ci-evidence/heartbeat1340-go-ai/ollama-header-review';
const priorToken=process.env.OLLAMA_API_KEY;
const priorFetch=globalThis.fetch;
const cases=[
 ['tuple-title-whitespace',()=>[['Authorization','   ']]],
 ['tuple-mixed-title-whitespace',()=>[['Authorization','   '],['X-Values','first'],['X-Values','second']]],
 ['tuple-mixed-upper-token',()=>[['AUTHORIZATION','user-token'],['X-Values','first'],['X-Values','second']]],
 ['tuple-auth-dup-whitespace',()=>[['Authorization','   '],['Authorization','   ']]],
 ['tuple-auth-dup-token',()=>[['Authorization','user-token'],['Authorization','second-token']]],
 ['tuple-auth-dup-mixedcase',()=>[['Authorization','   '],['AUTHORIZATION','user-token']]],
 ['tuple-auth-dup-lowerfirst',()=>[['authorization','user-token'],['AUTHORIZATION','second-token']]],
 ['tuple-auth-dup-emptyfirst',()=>[['Authorization',''],['Authorization','user-token']]],
 ['tuple-auth-dup-lastwhitespace',()=>[['Authorization','user-token'],['Authorization','   ']]],
 ['tuple-auth-dup-empty',()=>[['Authorization',''],['Authorization','']]],
 ['tuple-upper-token',()=>[['AUTHORIZATION','user-token']]],
 ['record-title-whitespace',()=>({Authorization:'   '})],
 ['record-upper-token',()=>({AUTHORIZATION:'user-token'})],
 ['headers-title-whitespace',()=>new Headers([['Authorization','   ']])],
 ['headers-upper-token',()=>new Headers([['AUTHORIZATION','user-token']])],
];
const snapshot=h=>h instanceof Headers?[...h.entries()]:JSON.parse(JSON.stringify(h));
const receipts=[];const source={};let networkAttempts=0;
try{
 process.env.OLLAMA_API_KEY='synthetic-env-token';
 globalThis.fetch=async()=>{networkAttempts++;throw Error('Unexpected real/global fetch blocked by independent probe');};
 for(const variant of ['baseline','candidate']){
  const stage=join(root,variant==='candidate'?'candidate-final2-node18.20.8':'baseline-node18.20.8');
  const bytes=await readFile(join(stage,'src/utils.ts'));source[variant]={stage,utilsSha256:createHash('sha256').update(bytes).digest('hex')};
  for(const entry of ['index','browser']){
   const{Ollama}=await import(pathToFileURL(join(stage,'dist',entry+'.mjs')));
   for(const[name,make]of cases){
    const input=make(),before=snapshot(input);const calls=[];
    const transport=async(url,init)=>{calls.push({url:String(url),method:init?.method??'GET',headers:snapshot(init?.headers??{}),nativeHeaders:[...new Headers(init?.headers).entries()]});return new Response(JSON.stringify({models:[]}),{status:200,headers:{'content-type':'application/json'}});};
    const client=new Ollama({host:'https://ollama.com',headers:input,fetch:transport});
    const result=await client.list();if(calls.length!==1||!Array.isArray(result.models))throw Error('Unexpected stub interaction');
    receipts.push({variant,entry,name,inputBefore:before,inputAfter:snapshot(input),callerMutated:JSON.stringify(before)!==JSON.stringify(snapshot(input)),...calls[0]});
   }
  }
 }
 const rows=[];
 for(const entry of ['index','browser'])for(const[name]of cases){const baseline=receipts.find(r=>r.variant==='baseline'&&r.entry===entry&&r.name===name);const candidate=receipts.find(r=>r.variant==='candidate'&&r.entry===entry&&r.name===name);rows.push({entry,name,baselineHeaders:baseline.headers,candidateHeaders:candidate.headers,baselineNativeHeaders:baseline.nativeHeaders,candidateNativeHeaders:candidate.nativeHeaders,headersChanged:JSON.stringify(baseline.headers)!==JSON.stringify(candidate.headers),baselineCallerMutated:baseline.callerMutated,candidateCallerMutated:candidate.callerMutated});}
 const injected=r=>JSON.stringify(r.headers).includes('Bearer synthetic-env-token'); const addedEnv=[]; for(const row of rows){const b=receipts.find(r=>r.variant==='baseline'&&r.entry===row.entry&&r.name===row.name),c=receipts.find(r=>r.variant==='candidate'&&r.entry===row.entry&&r.name===row.name);row.baselineEnvInjected=injected(b);row.candidateEnvInjected=injected(c);if(!injected(b)&&injected(c))addedEnv.push({entry:row.entry,name:row.name});} const report={addedEnv,node:process.version,platform:process.platform,arch:process.arch,transport:'UNIT TRANSPORT STUB ONLY: Config.fetch captures RequestInit; global fetch replaced with throwing guard; no HTTP server or cloud call.',syntheticEnvToken:true,networkAttempts,source,cases:receipts.length,receipts,comparisons:rows};
 await writeFile(join(out,'final-grouping-auth-control.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({cases:report.cases,networkAttempts,source,addedEnv,comparisons:rows},null,2));
}finally{
 if(priorToken===undefined)delete process.env.OLLAMA_API_KEY;else process.env.OLLAMA_API_KEY=priorToken;
 globalThis.fetch=priorFetch;
}
