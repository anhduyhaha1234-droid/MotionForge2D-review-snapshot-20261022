from pathlib import Path
import sys,os
from PIL import Image
base=Path(sys.argv[1]);mode=os.environ['ROOT_OUTPUT_CASE']
if mode=='rc7':sys.exit(7)
names={'valid':['0001.jpg','0002.jpg'],'wrong':['9001.jpg','9002.jpg'],'extra':['0000.jpg','0001.jpg','0002.jpg'],'corrupt':['0001.jpg','0002.jpg']}[mode]
for name in names:
    if mode=='corrupt':(base/'blend'/name).write_bytes(b'not-jpeg');continue
    im=Image.new('RGB',(640,368));im.paste((120,80,30),(0,0,320,368));im.save(base/'blend'/name)
