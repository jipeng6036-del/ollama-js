import http from 'node:http'
import { createRequire } from 'node:module'
import { writeFile } from 'node:fs/promises'
const require = createRequire(import.meta.url)
const classes = [
 ['esm-node',(await import('ollama')).Ollama],
 ['esm-browser',(await import('ollama/browser')).Ollama],
 ['cjs-node',require('ollama').Ollama],
 ['cjs-browser',require('ollama/browser').Ollama],
]
const profiles = [
 ['tuple-same',[['X-Context','first'],['X-Context','second']]],
 ['tuple-casing',[['X-Context','first'],['x-context','second'],['X-Context','third']]],
 ['cookie',[['Cookie','first=1'],['Cookie','second=2']]],
 ['set-cookie',[['Set-Cookie','first=1'],['Set-Cookie','second=2']]],
 ['headers-set-cookie',new Headers([['Set-Cookie','first=1'],['Set-Cookie','second=2']])],
 ['record',{'X-Context':'first','x-context':'second'}],
]
const received=[]
const server=http.createServer(async(req,res)=>{
 const bodies=[];for await(const c of req)bodies.push(c)
 received.push({url:req.url,headers:req.headers,body:Buffer.concat(bodies).toString()})
 if(req.url==='/api/generate'){
  res.setHeader('content-type','application/x-ndjson')
  res.write(JSON.stringify({response:'边界☃',done:false})+'\n')
  res.end(JSON.stringify({response:'尾',done:true})+'\n')
 }else{res.setHeader('content-type','application/json');res.end('{"models":[]}')}
})
await new Promise(r=>server.listen(0,'127.0.0.1',r))
const host=`http://127.0.0.1:${server.address().port}`
const results=[]
try{
 for(const [profile,headers] of profiles){
  await (await fetch(host+'/native',{headers})).json();const expected=received.at(-1).headers
  const keys=[...new Set([...new Headers(headers).keys()])]
  for(const [entry,Ollama] of classes){
   const client=new Ollama({host,headers})
   for(const method of ['list','generate-stream']){
    let streamContent
    if(method==='list')await client.list()
    else {let text='';for await(const part of await client.generate({model:'transport-fixture',prompt:'probe',stream:true}))text+=part.response;streamContent=text}
    const actual=received.at(-1).headers
    const mismatches=keys.filter(k=>JSON.stringify(actual[k])!==JSON.stringify(expected[k]))
    if(method==='generate-stream'&&streamContent!=='边界☃尾')mismatches.push('stream-content')
    results.push({entry,profile,method,pass:mismatches.length===0,mismatches,expected:Object.fromEntries(keys.map(k=>[k,expected[k]])),actual:Object.fromEntries(keys.map(k=>[k,actual[k]])),streamContent})
   }
  }
 }
}finally{server.closeAllConnections();await new Promise(r=>server.close(r))}
const output={runtime:process.version,packageSource:'independently installed local npm-pack tarball',count:results.length,passed:results.filter(x=>x.pass).length,failed:results.filter(x=>!x.pass).length,results}
await writeFile(process.argv[2],JSON.stringify(output,null,2)+'\n')
console.log(JSON.stringify({runtime:output.runtime,count:output.count,passed:output.passed,failed:output.failed}))
