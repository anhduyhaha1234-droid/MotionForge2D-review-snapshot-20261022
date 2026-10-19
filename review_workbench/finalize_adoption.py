import datetime, hashlib, json, pathlib, re, subprocess, sys

HERE=pathlib.Path(__file__).resolve().parents[1]
UP=HERE/'work'/'upstream'
OUT=HERE/'outputs'/'motionforge-video-skills-20261012'
SKILL=OUT/'motionforge-video-craft'
data=json.loads((UP/'SOURCE_LOCK.json').read_text(encoding='utf-8'))
data.append(json.loads((UP/'RESOLVED_LINK_LOCK.json').read_text(encoding='utf-8')))
detail=json.loads((UP/'DETAIL_LOCK.json').read_text(encoding='utf-8'))
records=[]
for row in data:
    files=[]
    for f in row['files'] + [f for f in detail if f['repo']==row['repo']]:
        rec={k:v for k,v in f.items() if k in ('path','url','sha256','bytes','error')}
        if 'local' in f and 'sha256' in f:
            assert hashlib.sha256(pathlib.Path(f['local']).read_bytes()).hexdigest()==f['sha256']
        rec['downloaded_not_necessarily_read_in_full']=True
        files.append(rec)
    records.append({'repo':row['repo'],'url':row['url'],'commit':row.get('commit'),
                    'retrieved_utc':row['retrieved_utc'],'tree_truncated':row.get('tree_truncated'),
                    'skill_paths':row['skill_paths'],'license_paths':row['license_paths'],
                    'files':files,'installed':False,'local_renderer_executed':False})
lock={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'scope':'Research and reference contract only. No production integration or R6 review.',
      'read_coverage':'README/SKILL and relevant excerpts for decisions; selected render, review and EDL call paths. Not a complete repository audit.',
      'resolved_user_url':{'original':'https://github.com/199.../motion-dev-animations-skill','candidate':'https://github.com/199-biotechnologies/motion-dev-animations-skill','basis':'Public search result matches exact repository name; original URL incomplete.'},
      'license_primary_sources':['https://webflow.com/legal/product-terms','https://www.remotion.dev/docs/license/pricing'],
      'sources':records}
(SKILL/'references'/'SOURCE_LOCK.json').write_text(json.dumps(lock,ensure_ascii=False,indent=2),encoding='utf-8')

main=pathlib.Path('C:/Users/Admin/MotionForge2D')
old=pathlib.Path('C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs')
docs=[main/'docs/pm/HERMES_AUTOPILOT_RULES.md',main/'AGENTS.md',main/'docs/pm/SESSION_PROTOCOL.md',main/'docs/pm/CODEX_PM_HANDOFF.md',main/'docs/pm/ROADMAP.md']
docs += [old/'motionforge-r5-review-20261012'/n for n in ['REVIEW_VI.md','CORRECTION_MATRIX.md','TECH_DECISION_VI.md','SESSION_OPENING_PROPOSAL.md','NEXT_HERMES_MANAGER_PROMPT.md','FINAL_GUARD.json']]
docs += [old/'motionforge-tech-conformance-20261012'/n for n in ['TECHNOLOGY_AUDIT_VI.md','TECH_CONFORMANCE_MATRIX.md','SESSION_OPENING_PROPOSAL.md','NEXT_HERMES_MANAGER_PROMPT.md','SOURCE_LOCK_FINAL.json']]
observed=[]
for p in docs:
    b=p.read_bytes()
    observed.append({'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
context={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'kind':'handoff_acknowledgement_not_new_review','runtime_process_owner_reverified':False,'inherited_verdict':'R5 CHANGES_REQUESTED','quality_accepted':0,'new_Hermes_dispatch':False,'new_workers_created':False,'project_files_modified_by_this_turn':False,'global_skills_installed':False,'document_hashes_at_packaging_not_full_turn_guard':observed}
(OUT/'CONTEXT_RECEIPT.json').write_text(json.dumps(context,ensure_ascii=False,indent=2),encoding='utf-8')

validator=subprocess.run([sys.executable,'-X','utf8','C:/Users/Admin/.codex/skills/.system/skill-creator/scripts/quick_validate.py',str(SKILL)],capture_output=True,text=True,encoding='utf-8')
assert validator.returncode==0,validator.stdout+validator.stderr
missing=[]
for p in OUT.rglob('*.md'):
    content=p.read_text(encoding='utf-8')
    for target in re.findall(r'\]\(([^)]+)\)',content):
        if target.startswith(('https:','http:','#','C:')): continue
        if not (p.parent/target).exists(): missing.append({'file':str(p),'link':target})
assert not missing,missing
checks=json.loads((OUT/'CONTRACT_CHECKS.json').read_text(encoding='utf-8'))
assert checks['passed']==checks['total']==20
manifest=[]
for p in sorted(OUT.rglob('*')):
    if p.is_file() and p.name!='PACKET_MANIFEST.json':
        b=p.read_bytes()
        manifest.append({'path':p.relative_to(OUT).as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
(OUT/'PACKET_MANIFEST.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_repositories':len(records),'source_fetch_errors':[f for r in records for f in r['files'] if 'error' in f],'skill_validation':validator.stdout.strip(),'contract_checks':{'passed':20,'total':20},'broken_relative_links':missing,'files':manifest},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'repositories':len(records),'files':len(manifest),'skill_validation':validator.stdout.strip(),'contract_checks':'20/20','broken_links':len(missing)}))
