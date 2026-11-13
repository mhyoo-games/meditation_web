"""그림책풍(Pepper&Carrot 느낌) 1단계 동물 머리 11종: 크고 동그란 눈(흰자·색 홍채·큰 동공·윗눈꺼풀 선).
사용법: python3 pc_heads.py <kenney glb> <출력폴더> [key ...] [check]"""
import sys, os, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig_hamster as rh, animals as an, zoo_extra as zx
from animals import N_TORSO, N_HEAD, J_TORSO, J_HEAD
IRIS = {   # 홍채 색 (바깥, 위쪽 그늘)
    'hamster': ('#7A5230', '#3E2614'), 'rabbit': ('#B8566A', '#5E2030'), 'cat': ('#A8D04A', '#4E7A1E'), 'dog': ('#8A5A2E', '#42260E'),
    'lion': ('#E8B032', '#8A5A10'), 'bear': ('#6E4A2A', '#34200E'), 'panda': ('#5A4A3E', '#241A14'), 'fox': ('#E89A2A', '#8A4A0E'),
    'raccoon': ('#8A7246', '#3E2E14'), 'squirrel': ('#6E4422', '#301A0A'), 'deer': ('#5E3A20', '#28160A'),
}
KEYS = list(IRIS)

def stage1(key):
    if key == 'hamster': st = copy.deepcopy(rh.STAGES[0]); st['si'] = 0
    elif key in an.SPECIES: st = an.stages_for(key)[0]
    else: st = zx.stage1(key)
    st['eyes'] = 'pc'; st['iris'], st['iris2'] = IRIS[key]
    return st

if __name__ == '__main__':
    kg, kacc = rh.read_glb(sys.argv[1]); out = sys.argv[2]; args = sys.argv[3:]
    check = 'check' in args; keys = [a for a in args if a in IRIS] or KEYS
    for key in keys:
        d = os.path.join(out, key); os.makedirs(d, exist_ok=True); st = stage1(key)
        p = f'{d}/{key}_stage1.glb'; tris, chk, aura = rh.write(st, 0, kg, kacc, p); print(key, 'tris', tris, flush=True)
        if check:
            idle = rh.pose_mats(kg, kacc, 'idle', 0.0)
            par = {N_TORSO: J_TORSO, N_HEAD: J_HEAD}
            import numpy as np
            if st.get('extra_joints'): idle = np.concatenate([idle, np.stack([idle[par[pn]] for _, pn, _ in st['extra_joints']])])
            rh.render(chk, aura, idle, 0.3, f'{d}/_r_a.png', zoom=1.6)
