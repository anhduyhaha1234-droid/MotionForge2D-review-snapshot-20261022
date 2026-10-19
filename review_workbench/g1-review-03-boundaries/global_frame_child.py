import sys
from pathlib import Path
from PIL import Image
base=Path(sys.argv[1]);beg=int(sys.argv[sys.argv.index('--beg')+1]);end=int(sys.argv[sys.argv.index('--end')+1])
for fid in range(beg,end):
    im=Image.new('RGB',(640,368));im.paste((120,80,30),(0,0,320,368));im.save(base/'blend'/f'{fid:04d}.jpg')
