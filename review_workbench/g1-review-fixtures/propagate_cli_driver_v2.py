import sys,json
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import r6_propagate as p
p.NS=Path(sys.argv[2])
p.K.PLAN={'S0021':{'frames':3,'start_frame':0}}
p.G.gate_shot_before_propagate=lambda sid: None
p.build_key_fids=lambda sid,n: [1,3]
p.stage_shot_assets=lambda *args: None
fixture_child=Path(sys.argv[3])
p.blend_script=lambda: fixture_child
sys.argv=['r6_propagate.py','S0021','--nproc','1']
p.main()
print('ROOT_PROBE_PARENT_RETURNED_NORMALLY')
