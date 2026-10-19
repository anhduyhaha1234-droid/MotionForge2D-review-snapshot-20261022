import json, pathlib, hashlib, urllib.request, concurrent.futures
ROOT=pathlib.Path(__file__).parent/'upstream'
LOCK=json.loads((ROOT/'SOURCE_LOCK.json').read_text(encoding='utf-8'))
PINS={r['repo']:r['commit'] for r in LOCK}
WANTED={
'AbubakrChan/product-launch-motion':['references/01-renderer-contract.md','references/08-qa-and-direction.md','scripts/word-timings.mjs'],
'howseen-ai/claude-motion-design':['skill/motion-design/scripts/render_template.py','skill/motion-design/scripts/remake/remake_qa.py'],
'nateherkai/hyperframes-student-kit':['.agents/skills/cut-silences/scripts/cut-silences.mjs','scripts/validate-beat-sync.mjs'],
'cth9191/animate':['plugins/animate/skills/animate/tools/review.mjs'],
'heygen-com/hyperframes':['skills/hyperframes-core/SKILL.md','skills/hyperframes-animation/SKILL.md','skills/hyperframes-cli/SKILL.md','packages/cli/src/commands/render/execute.ts','packages/cli/package.json'],
'remotion-dev/skills':['skills/remotion-markup/rules/animations.md','skills/remotion-markup/rules/timing.md'],
'motiondivision/motion':['packages/motion/package.json'],
'LottieFiles/motion-design-skill':['skills/motion-design/director/context-adaptation.md']}
def fetch(item):
    repo,path=item
    url=f'https://raw.githubusercontent.com/{repo}/{PINS[repo]}/{path}'
    rec={'repo':repo,'commit':PINS[repo],'path':path,'url':url}
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'MotionForge-read-only-research'})
        with urllib.request.urlopen(req,timeout=40) as r: data=r.read()
        dest=ROOT/repo.replace('/','__')/path
        assert not dest.exists(), str(dest)
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(data)
        rec.update(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),local=str(dest))
    except Exception as e: rec['error']=str(e)
    return rec
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    result=list(pool.map(fetch,[(repo,path) for repo,paths in WANTED.items() for path in paths]))
(ROOT/'DETAIL_LOCK.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
for r in result: print(r['repo'],r['path'],r.get('error',r.get('bytes')))
