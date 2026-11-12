"""usage: python3 -I anim_into.py <char.glb> <lib.glb> <out.glb> clip[,clip]  — 이름이 같은 뼈로 동작을 옮겨 미리보기용 파일을 만든다"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kaykit_swap as ks, kk_build as kb
C = ks.G(sys.argv[1]); L = ks.G(sys.argv[2])
cn = {x.get('name'): i for i, x in enumerate(C.j['nodes'])}; ln = {i: x.get('name') for i, x in enumerate(L.j['nodes'])}
for clip in sys.argv[4].split(','):
    ch, _ = kb.clip_data(L, clip)
    tracks = {(cn[ln[n]], p): (T, V) for (n, p), (T, V) in ch.items() if ln[n] in cn}
    kb.add_clip(C, clip, tracks)
C.compact(); C.save(sys.argv[3])
