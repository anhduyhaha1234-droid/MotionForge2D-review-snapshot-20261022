import concurrent.futures, datetime, hashlib, json, pathlib, urllib.request

ROOT = pathlib.Path(__file__).parent / 'upstream'
REPOS = ['AbubakrChan/product-launch-motion','charlie947/motion-graphics-skills','howseen-ai/claude-motion-design','nateherkai/hyperframes-student-kit','Barty-Bart/motion-graphics','cth9191/animate','whaleyxbt/claude-motion','haidrrrry/claude-remotion-skill','motiondivision/motion','heygen-com/hyperframes','remotion-dev/remotion','remotion-dev/skills','greensock/gsap-skills','LottieFiles/motion-design-skill']

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent':'MotionForge-read-only-research','Accept':'application/vnd.github+json'})
    with urllib.request.urlopen(req, timeout=40) as response:
        return response.read()

def inspect(repo):
    folder = ROOT / repo.replace('/','__')
    folder.mkdir(parents=True, exist_ok=True)
    result = {'repo':repo,'url':'https://github.com/'+repo,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':[]}
    try:
        commit = json.loads(get('https://api.github.com/repos/'+repo+'/commits/HEAD'))
        result['commit'] = commit['sha']
        tree = json.loads(get('https://api.github.com/repos/'+repo+'/git/trees/'+commit['sha']+'?recursive=1'))
        (folder/'tree.json').write_text(json.dumps(tree,indent=2),encoding='utf-8')
        result['tree_truncated'] = tree.get('truncated')
        paths = [e['path'] for e in tree['tree'] if e['type']=='blob']
        result['skill_paths'] = [p for p in paths if p.lower().endswith('skill.md')]
        result['license_paths'] = [p for p in paths if p.rsplit('/',1)[-1].lower() in ('license','license.md','license.txt','notice')]
        selected = [p for p in paths if ('/' not in p and p.lower() in ('readme.md','license','license.md','license.txt','notice','package.json','skill.md'))]
        selected += result['skill_paths'][:20]
        result['code_candidates'] = [p for p in paths if p.endswith(('.mjs','.py','.ts','.js')) and any(s in p.lower() for s in ('render','export','timeline','validate','caption','transcript','beat','qa','review'))][:60]
        for path in dict.fromkeys(selected):
            url = 'https://raw.githubusercontent.com/'+repo+'/'+commit['sha']+'/'+path
            try:
                data = get(url)
                dest = folder/path
                dest.parent.mkdir(parents=True,exist_ok=True)
                dest.write_bytes(data)
                result['files'].append({'path':path,'url':url,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'local':str(dest)})
            except Exception as exc:
                result['files'].append({'path':path,'error':str(exc)})
    except Exception as exc:
        result['error']=str(exc)
    return result

if __name__ == '__main__':
    ROOT.mkdir(parents=True,exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(inspect,REPOS))
    (ROOT/'SOURCE_LOCK.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    for r in results:
        print(json.dumps({k:r.get(k) for k in ('repo','commit','error','skill_paths','license_paths','code_candidates')},ensure_ascii=False))
