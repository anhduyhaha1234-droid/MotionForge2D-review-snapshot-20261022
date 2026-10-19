const fs=require('node:fs'), path=require('node:path'), crypto=require('node:crypto'), assert=require('node:assert/strict');
const {execFileSync}=require('node:child_process');
const root='C:/Users/Admin/AppData/Roaming/npm/node_modules/9router';
const out='C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/9router-gemini-20261016';
assert.equal(JSON.parse(fs.readFileSync(path.join(root,'package.json'),'utf8')).version,'0.5.95','Refuse unknown version');
const chunks=path.join(root,'app/.next-cli-build/server/chunks');
const file=path.join(chunks,'8895.js');
const oldText='let l=c===e.h.OPENAI_RESPONSES&&o===e.h.OPENAI_RESPONSES;if(l&&!L)';
const newText='if("antigravity"===p&&o===e.h.OPENAI){let b="data: [DONE]\\n\\n";q?.appendConvertedChunk?.(b),a.enqueue(k.encode(b))}'+oldText;
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const protectedFiles=['5330.js','8499.js','436.js'].map(name=>({name,sha256:sha(fs.readFileSync(path.join(chunks,name)))}));
const before=fs.readFileSync(file,'utf8');
if(before.includes(newText)) {console.log('Already installed; no edits');process.exit(0);}
assert.equal(before.split(oldText).length-1,1,'Ambiguous stream implementation');
const after=before.replace(oldText,newText);
assert.equal(after.replace(newText,oldText),before,'Unexpected scope change');
const backup=path.join(out,'backups/8895.js');
fs.mkdirSync(path.dirname(backup),{recursive:true});
assert.equal(fs.existsSync(backup),false,'Do not overwrite preimage');
fs.copyFileSync(file,backup);
fs.writeFileSync(file,after,'utf8');
try{execFileSync(process.execPath,['--check',file]);}catch(e){fs.writeFileSync(file,before,'utf8');throw e;}
for(const p of protectedFiles)assert.equal(sha(fs.readFileSync(path.join(chunks,p.name))),p.sha256);
const receipt={utc:new Date().toISOString(),version:'0.5.95',file,backup,beforeSha256:sha(before),afterSha256:sha(after),protectedFiles,scope:'Append one DONE on Antigravity-to-OpenAI translated SSE EOF; no auth/model/other-provider changes'};
fs.writeFileSync(path.join(out,'sse-fix-receipt.json'),JSON.stringify(receipt,null,2));
console.log(JSON.stringify(receipt,null,2));
