"""One real request through the installed Hermes native-image tool envelope.
Configuration additions exist only in this process until root approves them.
"""
import asyncio
import copy
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
from unittest.mock import patch
import yaml
from smoke import OUT, MODEL, BASE, request, usage

SCRATCH=Path(__file__).resolve().parent
os.environ['HERMES_HOME']=str(SCRATCH/'isolated-hermes-home')
os.environ['PYTHONDONTWRITEBYTECODE']='1'
os.environ['VISION_TOOLS_DEBUG']='false'
CONFIG=Path('C:/Users/Admin/AppData/Local/hermes/config.yaml')
SITE=Path('C:/Users/Admin/AppData/Local/Programs/Python/Python311/Lib/site-packages')

async def main():
    receipt_path=OUT/'HERMES_NATIVE_TOOL_RECEIPT.json'
    if receipt_path.exists(): raise SystemExit('Receipt exists; no repeated live request')
    baseline=json.loads((OUT/'DIRECT_IMAGE_RECEIPT.json').read_text(encoding='utf-8'))
    if not baseline['pass']: raise SystemExit('Initial image test not passed')
    config_bytes=CONFIG.read_bytes()
    cfg=yaml.safe_load(config_bytes)
    candidate=copy.deepcopy(cfg)
    candidate.setdefault('providers',{}).setdefault('custom',{}).setdefault('models',{}).setdefault(MODEL,{})['supports_vision']=True
    status,raw,_=request('/api/keys')
    if status!=200: raise SystemExit('Gateway key unavailable; no model call')
    key=next(k['key'] for k in json.loads(raw)['keys'] if k.get('isActive'))
    runtime={'provider':'custom','model':MODEL,'base_url':BASE+'/v1','api_key':key,'api_mode':'chat_completions'}
    from agent.auxiliary_client import scoped_runtime_main, resolve_vision_provider_client
    from agent.image_routing import _lookup_supports_vision, decide_image_input_mode
    from tools import vision_tools
    from run_agent import AIAgent
    with scoped_runtime_main(runtime), patch('hermes_cli.config.load_config',return_value=cfg), patch('hermes_cli.config.load_config_readonly',return_value=cfg):
        before={'capability':_lookup_supports_vision('custom',MODEL,cfg),'image_input_mode':decide_image_input_mode('custom',MODEL,cfg),'native_fast_path':vision_tools._should_use_native_vision_fast_path(),'vision_requirements':vision_tools.check_vision_requirements()}
        provider,client,model=resolve_vision_provider_client(main_runtime=runtime)
        before['aux_route']={'provider':provider,'model':model,'base_url':str(client.base_url) if client else None}
        if client: client.close()
    image_path=OUT/'vision_fixture.png'
    question=baseline['prompt']
    with scoped_runtime_main(runtime), patch('hermes_cli.config.load_config',return_value=candidate), patch('hermes_cli.config.load_config_readonly',return_value=candidate):
        after={'capability':_lookup_supports_vision('custom',MODEL,candidate),'image_input_mode':decide_image_input_mode('custom',MODEL,candidate),'native_fast_path':vision_tools._should_use_native_vision_fast_path()}
        assert after['native_fast_path'],after
        # Guard the tool from silently entering any auxiliary/model fallback.
        async def forbidden_aux(*a,**kw): raise RuntimeError('Unexpected auxiliary call')
        with patch.object(vision_tools,'async_call_llm',forbidden_aux):
            envelope=await vision_tools._handle_vision_analyze({'image_url':str(image_path),'question':question})
        assert isinstance(envelope,dict) and envelope.get('_multimodal'),str(envelope)[:400]
        dummy=AIAgent.__new__(AIAgent)
        dummy.provider='custom'; dummy.model=MODEL
        content=dummy._tool_result_content_for_active_model('vision_analyze',envelope)
        assert isinstance(content,list) and any(p.get('type')=='image_url' for p in content)
    args={'image_url':str(image_path),'question':question}
    messages=[{'role':'user','content':'Use the vision_analyze result to answer the image question exactly as JSON. The code is not in the filename or prompt.'},{'role':'assistant','content':None,'tool_calls':[{'id':'call_vision_fixture_g1c03','type':'function','function':{'name':'vision_analyze','arguments':json.dumps(args)}}]},{'role':'tool','tool_call_id':'call_vision_fixture_g1c03','content':content}]
    body={'model':MODEL,'messages':messages,'max_tokens':1024,'stream':False}
    before_usage=usage()
    status,raw,seconds=request('/v1/chat/completions',body,key)
    parsed=json.loads(raw)
    text=(parsed.get('choices') or [{}])[0].get('message',{}).get('content','')
    s=text.strip()
    if s.startswith('```'): s=s.split('\n',1)[1].rsplit('```',1)[0].strip()
    try: answer=json.loads(s)
    except Exception: answer={}
    expected=baseline['expected']
    checks={k: (answer.get(k)==v if k in ['code','right_shape_count'] else v in str(answer.get(k,'')).lower()) for k,v in expected.items()}
    receipt={'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'test':'Installed Hermes vision_analyze -> native envelope -> installed AIAgent tool-result unwrap -> actual 9router image tool message','session_context_source':'20261017_115944_b2a338; copied model/provider identity only; session not mutated or dispatched','actual_session_test':False,'configuration_change_installed':False,'candidate_override':{'providers':{'custom':{'models':{MODEL:{'supports_vision':True}}}}},'config_sha256_before':hashlib.sha256(config_bytes).hexdigest(),'config_sha256_after':hashlib.sha256(CONFIG.read_bytes()).hexdigest(),'before':before,'after_candidate_process_only':after,'tool_envelope':{'multimodal':True,'part_types':[p['type'] for p in content],'image_sha256':baseline['image_sha256'],'text_summary':envelope.get('text_summary')},'requested_model':MODEL,'http_status':status,'seconds':seconds,'raw_response_redacted':parsed,'checks':checks,'pass':status==200 and all(checks.values()),'usage_rows':usage(before_usage),'model_request_count':1,'manual_account_override':False,'files':{str(SITE/p):hashlib.sha256((SITE/p).read_bytes()).hexdigest() for p in ['tools/vision_tools.py','agent/image_routing.py','agent/auxiliary_client.py','run_agent.py']}}
    receipt_path.write_text(json.dumps(receipt,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:receipt[k] for k in ['before','after_candidate_process_only','http_status','seconds','checks','pass','usage_rows']},indent=2))
    raise SystemExit(0 if receipt['pass'] else 1)

if __name__=='__main__': asyncio.run(main())
