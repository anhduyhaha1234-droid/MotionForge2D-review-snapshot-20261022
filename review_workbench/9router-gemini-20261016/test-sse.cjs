const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = 'C:/Users/Admin/AppData/Roaming/npm/node_modules/9router/app/.next-cli-build/server/chunks';
const oldText = 'let l=c===e.h.OPENAI_RESPONSES&&o===e.h.OPENAI_RESPONSES;if(l&&!L)';
const newText = 'if("antigravity"===p&&o===e.h.OPENAI){let b="data: [DONE]\\n\\n";q?.appendConvertedChunk?.(b),a.enqueue(k.encode(b))}'+oldText;
const candidate = process.argv.includes('--candidate');
const sources = fs.readdirSync(root).filter(x=>x.endsWith('.js')).map(name=>({name, text:fs.readFileSync(path.join(root,name),'utf8')}));
const modules = {}, cache = {}, loaded = new Set();
const sharedGlobal = {};
const externals = {};
const route = fs.readFileSync(path.join(root,'../app/api/v1/chat/completions/route.js'),'utf8');
for (const m of route.matchAll(/(\d+):a=>\{a.exports=require\("([^"]+)"\)\}/g)) externals[m[1]]=m[2];
function req(id) {
  if (id === 47370 || id === 9248) return {uw(){},E5(){return Promise.resolve();}};
  if(externals[id]) return require(externals[id]);
  if(cache[id]) return cache[id].exports;
  if(!modules[id]) {
    const re = new RegExp('(?:[,{])'+id+':');
    const file = sources.find(x=>!loaded.has(x.name)&&re.test(x.text));
    if(!file) throw new Error('Missing module '+id);
    let text=file.text;
    if(candidate && file.name==='8895.js') {
      assert.equal(text.split(oldText).length-1,1);
      assert.equal(text.includes(newText),false,'candidate already installed');
      text=text.replace(oldText,newText);
    }
    const exp={};
    const context={exports:exp,global:sharedGlobal,globalThis:sharedGlobal,require,process,console,TextEncoder,TextDecoder,TransformStream,ReadableStream,WritableStream,Response,Request,Headers,URL,URLSearchParams,Buffer,Uint8Array,Blob,File,FormData,AbortSignal,AbortController,DOMException,performance,fetch:()=>{throw new Error('No network in fixture');},setTimeout,clearTimeout,setInterval:(...args)=>{const t=setInterval(...args);t.unref();return t;},clearInterval,structuredClone,crypto:require('node:crypto').webcrypto};
    context.MessagePort=MessagePort; context.MessageChannel=MessageChannel;
    context.__filename=path.join(root,file.name); context.__dirname=root;
    Object.setPrototypeOf(context,globalThis);
    vm.runInNewContext(text,context,{filename:file.name});
    Object.assign(modules,exp.modules); loaded.add(file.name);
  }
  const module={exports:{}};cache[id]=module;modules[id](module,module.exports,req);return module.exports;
}
req.d=(obj,defs)=>{for(const [key,get]of Object.entries(defs))Object.defineProperty(obj,key,{enumerable:true,get});};
req.r=obj=>Object.defineProperty(obj,'__esModule',{value:true});
req.n=obj=>{const get=obj&&obj.__esModule?()=>obj.default:()=>obj;req.d(get,{a:get});return get;};
req.o=(a,b)=>Object.prototype.hasOwnProperty.call(a,b);
req.e=async()=>{};

async function run(label, {upstreamDone=false, tools=false, target='openai', tail=false, provider='antigravity'}={}) {
  const formats=req(14170).h;
  const transformer=req(71857).i5(formats.ANTIGRAVITY,target,provider,null,null,'gemini-3.8-flash-high','fixture',{messages:[]});
  const part=tools?{functionCall:{name:'ping',args:{token:'xin chào'}}}:{text:'xin chào'};
  const event={response:{responseId:'fixture-id',modelVersion:'gemini-3.8-flash-n',candidates:[{index:0,content:{role:'model',parts:[part]},finishReason:'STOP'}],usageMetadata:{promptTokenCount:7,candidatesTokenCount:3,totalTokenCount:10}}};
  let wire='data: '+JSON.stringify(event)+(tail?'':'\n\n')+(upstreamDone?'data: [DONE]\n\n':'');
  const bytes=new TextEncoder().encode(wire);
  const stream=new ReadableStream({start(controller){for(let i=0;i<bytes.length;i+=3)controller.enqueue(bytes.slice(i,i+3));controller.close();}});
  const output=await new Response(stream.pipeThrough(transformer)).text();
  const done=(output.match(/data: \[DONE\]/g)||[]).length;
  if(provider==='antigravity'&&target==='openai') {
    assert.equal(done,1,label+': expected exactly one DONE');
    assert.ok(output.endsWith('data: [DONE]\n\n'),label+': DONE must be last');
    assert.ok(output.includes(tools?'tool_calls':'xin chào'),label+': content missing');
    assert.ok(output.includes('finish_reason'),label+': finish missing');
  } else assert.equal(done,0,label+': unrelated stream changed');
  return {label,pass:true,doneCount:done};
}
(async()=>{
  const tests=[];
  for(const [label,opts]of [['text fragmented utf8',{}],['upstream DONE',{upstreamDone:true}],['tool call',{tools:true}],['tail without newline',{tail:true}],['Claude client',{target:'claude'}],['native Gemini client',{target:'antigravity'}],['other provider unchanged',{provider:'gemini'}]]) {
    try{tests.push(await run(label,opts));}catch(e){tests.push({label,pass:false,error:e.message});}
  }
  console.log(JSON.stringify({candidate,tests,loadedModules:Object.keys(cache).length,pass:tests.every(x=>x.pass)},null,2));
  process.exitCode=tests.every(x=>x.pass)?0:1;
})().catch(e=>{console.error(e);process.exitCode=1;});
