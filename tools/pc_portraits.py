"""마법학교 동물 초상 (돌 받침 위): python3 -I pc_portraits.py <chars dir(k.glb)> <out dir> <base png>"""
import sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glbview as gv
chars, out, basep = sys.argv[1:4]; os.makedirs(out, exist_ok=True)
base = Image.open(basep).convert('RGBA'); base = base.crop(base.getbbox()); bw = 214; base = base.resize((bw, int(base.height * bw / base.width)), Image.LANCZOS)
for f in sorted(os.listdir(chars)):
    if not f.endswith('.glb'): continue
    k = f[:-4]
    img = gv.draw(gv.load(os.path.join(chars, f), 'Idle', 0.5), 600, 0.3)
    a = (gv.draw.mask * 255).astype(np.uint8)
    im = Image.fromarray(np.dstack([img, a]), 'RGBA'); im = im.crop(im.getbbox())
    h = 214; im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
    cv = Image.new('RGBA', (240, 300), (0, 0, 0, 0))
    by = 300 - base.height - 2; cv.alpha_composite(base, ((240 - bw) // 2, by))
    cv.alpha_composite(im, ((240 - im.width) // 2, max(0, by + int(base.height * 0.42) - h)))
    cv.save(os.path.join(out, k + '.png'), optimize=True); print(k)
