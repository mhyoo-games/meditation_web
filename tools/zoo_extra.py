"""힐링 마을 주민 동물 6종 (곰, 판다, 여우, 너구리, 다람쥐, 사슴) — 1단계(일상) 모습만.
animals.py 와 같은 species 훅 방식. 사용법: python3 zoo_extra.py <kenney glb> <출력폴더> [bear panda ...] [check]
"""
import sys, os, math, copy
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig_hamster as rh, make_hamster as mh
import animals as an
from rig_hamster import sd_ell, sd_cap, J_HEAD, J_LEGL, J_LEGR
from animals import Species, J_TAIL, EJ, headn, sd_flatcap, chain, N_TORSO, N_HEAD
from make_hamster import C, Rx, Ry, Rz


def soft_mouth(decal, st, y0=0.424, dk='#4A2A30'):
    dk = C(dk)
    decal(0, y0, 0.0026, 0.01, dk, off=0.003, nr=3)
    for s in (-1, 1): decal(s * 0.014, y0 - 0.013, 0.016, 0.005, dk, roll=s * 0.6, off=0.003, nr=3)
    decal(0, y0 - 0.027, 0.017, 0.012, C('#6B2B32'), top=0.3, off=0.0026)
    decal(0, y0 - 0.032, 0.01, 0.006, C('#FF7E8F'), off=0.0036, nr=4)
    return True


# =============================== 곰 ===============================
class Bear(Species):
    key, name = 'bear', '곰'
    eye_xy = (0.098, 0.505)
    tail_pivot, ear_pivot = (0, 0.16, -0.15), (0.165, 0.625, -0.02)
    HC, HR = np.array([0, 0.47, 0.0]), np.array([0.238, 0.205, 0.205])
    def sdf(self, sh, st, ctx):
        HC, HR = self.HC, self.HR
        sh.add(lambda p: sd_ell(p, (0, 0.17, -0.175), (0.045, 0.045, 0.04)), J_TAIL, 'tail', 0.02)
        sh.add(lambda p: sd_ell(p, HC, HR), J_HEAD, 'head', 0.08)
        for s in (-1, 1):
            sh.add(lambda p, s=s: sd_ell(p, (s * 0.12, 0.41, 0.085), (0.095, 0.078, 0.085)), J_HEAD, 'cheek', 0.05)
            sh.add(lambda p, s=s: sd_ell(p, (s * 0.165, 0.635, -0.02), (0.068, 0.064, 0.045)), EJ(s), 'ear', 0.035)
        sh.add(lambda p: sd_ell(p, (0, 0.41, 0.16), (0.082, 0.062, 0.07)), J_HEAD, 'muzzle', 0.05)
        sh.add(lambda p: sd_ell(p, (0, 0.44, 0.222), (0.03, 0.02, 0.02)), J_HEAD, 'nose', 0.012)
        return HC, HR
    def color(self, P, N, lab, col, st, ctx):
        F_, W_ = C(st['fur']), C(st['white'])
        col[np.isin(lab, ['head', 'cheek', 'tail'])] = F_
        col[lab == 'muzzle'] = W_
        em = lab == 'ear'; col[em] = F_
        col[em & (N[:, 2] > 0.45) & (np.abs(np.abs(P[:, 0]) - 0.165) < 0.035) & (P[:, 1] > 0.62)] = C(st.get('earin', st['white']))
        col[lab == 'nose'] = C('#2A1C18')
    def mouth(self, decal, hit, st): return soft_mouth(decal, st, 0.418)


# =============================== 판다 ===============================
class Panda(Bear):
    key, name = 'panda', '판다'
    def color(self, P, N, lab, col, st, ctx):
        n = headn(P, ctx['HC'], ctx['HR']); B_, W_ = C(st['fur']), C(st['white'])
        col[np.isin(lab, ['head', 'cheek', 'muzzle', 'tail'])] = W_
        col[lab == 'ear'] = B_
        hm = np.isin(lab, ['head', 'cheek'])
        for s in (-1, 1):   # 눈 주위 검은 무늬 (살짝 기울어진 물방울)
            dx, dy = P[:, 0] - s * 0.1, P[:, 1] - 0.497
            r = np.sqrt((dx * math.cos(0.5) + s * dy * math.sin(0.5)) ** 2 / 0.058 ** 2 + (-s * dx * math.sin(0.5) + dy * math.cos(0.5)) ** 2 / 0.045 ** 2)
            col[hm & (r < 1.0) & (N[:, 2] > 0.25)] = B_
        col[lab == 'nose'] = C('#1A1418')
    def eyes(self, decal, hit, st, ex, ey):
        for s in (-1, 1):
            decal(s * ex, ey, 0.03, 0.034, C('#FFFFFF'), off=0.0032)
            decal(s * ex, ey, 0.022, 0.026, C('#14101A'), off=0.0042)
            decal(s * ex + s * 0.008, ey + 0.01, 0.008, 0.008, C('#FFFFFF'), off=0.0052)
            decal(s * 0.165, 0.42, 0.032, 0.02, C('#FFB3C2'), nr=5)
        return True


# =============================== 여우 ===============================
class Fox(Species):
    bbox = ((-0.46, -0.01, -0.64), (0.46, 1.05, 0.37))
    key, name = 'fox', '여우'
    eye_xy = (0.1, 0.51)
    tail_pivot, ear_pivot = (0, 0.16, -0.15), (0.13, 0.6, -0.02)
    def sdf(self, sh, st, ctx):
        HC, HR = np.array([0, 0.475, 0.0]), np.array([0.232, 0.198, 0.2])
        pts = [(0, 0.16, -0.155), (0, 0.15, -0.26), (0.02, 0.2, -0.36), (0.05, 0.3, -0.42), (0.08, 0.42, -0.42)]
        pts = [np.array(p) for p in pts]
        RR = [0.04, 0.07, 0.095, 0.085, 0.06]
        for i, (a, b) in enumerate(zip(pts[:-1], pts[1:])):            # 굵은 솜털 꼬리
            r0, r1 = RR[i], RR[i + 1]
            sh.add(lambda p, a=a, b=b, r0=r0, r1=r1: sd_cap(p, a, b, r0, r1), J_TAIL, 'tail', 0.03)
        sh.add(lambda p: sd_ell(p, (0.08, 0.47, -0.41), (0.065, 0.06, 0.06)), J_TAIL, 'tailtip', 0.04)
        sh.add(lambda p: sd_ell(p, HC, HR), J_HEAD, 'head', 0.08)
        for s in (-1, 1):
            sh.add(lambda p, s=s: sd_ell(p, (s * 0.13, 0.41, 0.08), (0.1, 0.072, 0.08)), J_HEAD, 'cheek', 0.05)
            sh.add(lambda p, s=s: sd_ell(p, (s * 0.22, 0.4, 0.02), (0.055, 0.03, 0.045), Rz(s * 0.45)), J_HEAD, 'cheek', 0.03)
            a = np.array([s * 0.13, 0.6, -0.02]); b = np.array([s * 0.2, 0.83, -0.04])
            sh.add(lambda p, a=a, b=b: sd_flatcap(p, a, b, 0.08, 0.014, 2.4), EJ(s), 'ear', 0.035)
        sh.add(lambda p: sd_ell(p, (0, 0.41, 0.165), (0.058, 0.045, 0.085)), J_HEAD, 'muzzle', 0.05)   # 뾰족한 주둥이
        sh.add(lambda p: sd_ell(p, (0, 0.428, 0.245), (0.02, 0.015, 0.015)), J_HEAD, 'nose', 0.01)
        return HC, HR
    def color(self, P, N, lab, col, st, ctx):
        n = headn(P, ctx['HC'], ctx['HR']); F_, W_ = C(st['fur']), C(st['white']); D_ = C(st.get('mark') or '#3A2620')
        hm = lab == 'head'; col[hm] = F_
        col[hm & (n[:, 1] < -0.3) & (n[:, 2] > 0.25)] = W_
        cm = lab == 'cheek'; col[cm] = W_
        col[lab == 'muzzle'] = W_
        col[lab == 'muzzle'] = np.where((P[lab == 'muzzle', 1] > 0.43)[:, None], F_, W_)
        em = lab == 'ear'; col[em] = F_; col[em & (P[:, 1] > 0.76)] = D_
        col[em & (N[:, 2] > 0.4) & (P[:, 1] > 0.62) & (P[:, 1] < 0.76) & (np.abs(np.abs(P[:, 0]) - (0.135 + (P[:, 1] - 0.6) * 0.3)) < 0.03)] = W_
        col[lab == 'tail'] = F_; col[lab == 'tailtip'] = W_
        col[lab == 'nose'] = C('#1C1616')
    def mouth(self, decal, hit, st): return soft_mouth(decal, st, 0.412)


# =============================== 너구리 ===============================
class Raccoon(Species):
    bbox = ((-0.46, -0.01, -0.64), (0.46, 1.05, 0.37))
    key, name = 'raccoon', '너구리'
    eye_xy = (0.1, 0.505)
    tail_pivot, ear_pivot = (0, 0.16, -0.15), (0.14, 0.61, -0.02)
    def sdf(self, sh, st, ctx):
        HC, HR = np.array([0, 0.472, 0.0]), np.array([0.236, 0.2, 0.2])
        pts = [np.array(p) for p in [(0, 0.16, -0.155), (0, 0.14, -0.26), (0.01, 0.2, -0.36), (0.03, 0.3, -0.42), (0.05, 0.42, -0.42)]]
        chain(sh, pts, 0.05, 0.06, J_TAIL, 'tail', 0.03, 0.025)
        sh.add(lambda p: sd_ell(p, HC, HR), J_HEAD, 'head', 0.08)
        for s in (-1, 1):
            sh.add(lambda p, s=s: sd_ell(p, (s * 0.125, 0.41, 0.085), (0.1, 0.075, 0.085)), J_HEAD, 'cheek', 0.05)
            sh.add(lambda p, s=s: sd_ell(p, (s * 0.21, 0.41, 0.02), (0.05, 0.03, 0.045), Rz(s * 0.4)), J_HEAD, 'cheek', 0.03)
            a = np.array([s * 0.14, 0.6, -0.02]); b = np.array([s * 0.18, 0.72, -0.03])
            sh.add(lambda p, a=a, b=b: sd_flatcap(p, a, b, 0.07, 0.03, 2.4), EJ(s), 'ear', 0.035)
        sh.add(lambda p: sd_ell(p, (0, 0.415, 0.155), (0.065, 0.046, 0.065)), J_HEAD, 'muzzle', 0.05)
        sh.add(lambda p: sd_ell(p, (0, 0.438, 0.212), (0.022, 0.016, 0.016)), J_HEAD, 'nose', 0.01)
        return HC, HR
    def color(self, P, N, lab, col, st, ctx):
        n = headn(P, ctx['HC'], ctx['HR']); F_, W_, M_ = C(st['fur']), C(st['white']), C(st['mark'])
        hm = lab == 'head'; col[hm] = F_
        mask = np.isin(lab, ['head', 'cheek']) & (N[:, 2] > 0.2) & (np.abs(P[:, 1] - 0.5 + 0.08 * np.abs(P[:, 0])) < 0.038) & (np.abs(P[:, 0]) < 0.2)
        brow = hm & (N[:, 2] > 0.3) & (P[:, 1] > 0.545) & (P[:, 1] < 0.585) & (np.abs(np.abs(P[:, 0]) - 0.09) < 0.05)
        col[lab == 'cheek'] = W_; col[brow] = W_; col[mask] = M_
        col[hm & (np.abs(P[:, 0]) < 0.018) & (N[:, 2] > 0.2) & (P[:, 1] > 0.5)] = M_     # 이마 줄
        col[lab == 'muzzle'] = W_
        em = lab == 'ear'; col[em] = F_; col[em & (P[:, 1] > 0.69)] = W_
        tm = lab == 'tail'; col[tm] = F_; col[tm & (np.sin((P[:, 1] * 0.8 - P[:, 2]) * 36) > 0.2)] = M_
        col[lab == 'nose'] = C('#1C1616')
    def mouth(self, decal, hit, st): return soft_mouth(decal, st, 0.42)


# =============================== 다람쥐 ===============================
class Squirrel(Species):
    bbox = ((-0.46, -0.01, -0.64), (0.46, 1.05, 0.37))
    key, name = 'squirrel', '다람쥐'
    eye_xy = (0.1, 0.51)
    tail_pivot, ear_pivot = (0, 0.16, -0.15), (0.13, 0.64, -0.02)
    def sdf(self, sh, st, ctx):
        HC, HR = np.array([0, 0.472, 0.0]), np.array([0.228, 0.2, 0.198])
        # 등 뒤로 크게 말아 올린 꼬리
        ang = np.linspace(-1.2, 2.6, 9)
        pts = [np.array([0, 0.16, -0.16])] + [np.array([0, 0.42 + 0.25 * math.sin(a), -0.33 - 0.14 * math.cos(a)]) for a in ang]
        for i, (a, b) in enumerate(zip(pts[:-1], pts[1:])):
            r = 0.05 + 0.05 * math.sin(math.pi * min(1, (i + 1) / 7))
            sh.add(lambda p, a=a, b=b, r=r: sd_cap(p, a, b, r * 0.85, r), J_TAIL, 'tail', 0.035)
        sh.add(lambda p: sd_ell(p, HC, HR), J_HEAD, 'head', 0.08)
        for s in (-1, 1):
            sh.add(lambda p, s=s: sd_ell(p, (s * 0.12, 0.405, 0.09), (0.1, 0.082, 0.088)), J_HEAD, 'cheek', 0.05)   # 볼주머니
            a = np.array([s * 0.13, 0.63, -0.02]); b = np.array([s * 0.15, 0.75, -0.03])
            sh.add(lambda p, a=a, b=b: sd_flatcap(p, a, b, 0.045, 0.022, 2.2), EJ(s), 'ear', 0.03)
            sh.add(lambda p, s=s: sd_ell(p, (s * 0.152, 0.77, -0.03), (0.016, 0.03, 0.012)), EJ(s), 'tuft', 0.015)
        sh.add(lambda p: sd_ell(p, (0, 0.418, 0.15), (0.06, 0.044, 0.055)), J_HEAD, 'muzzle', 0.05)
        sh.add(lambda p: sd_ell(p, (0, 0.44, 0.196), (0.017, 0.012, 0.012)), J_HEAD, 'nose', 0.01)
        return HC, HR
    def color(self, P, N, lab, col, st, ctx):
        n = headn(P, ctx['HC'], ctx['HR']); F_, W_, M_ = C(st['fur']), C(st['white']), C(st['mark'])
        hm = lab == 'head'; col[hm] = F_
        col[hm & (n[:, 1] < -0.35) & (n[:, 2] > 0.2)] = W_
        for s in (-1, 1):   # 눈 위아래 흰 줄
            col[hm & (N[:, 2] > 0.2) & (np.abs(P[:, 1] - 0.565) < 0.012) & (np.abs(P[:, 0] - s * 0.1) < 0.05)] = W_
        col[hm & (n[:, 2] < -0.1) & (np.abs(n[:, 0] - 0.0) < 0.12)] = M_    # 등 줄무늬
        col[lab == 'cheek'] = W_; col[lab == 'muzzle'] = W_
        col[lab == 'ear'] = F_; col[lab == 'tuft'] = M_
        tm = lab == 'tail'; col[tm] = F_ * np.array([1.08, 1.04, 1.0, 1]); col[tm & (np.abs(P[:, 0]) > 0.075)] = W_ * np.array([0.95, 0.9, 0.82, 1])
        col[lab == 'nose'] = C('#5A2E28')
    def mouth(self, decal, hit, st):
        soft_mouth(decal, st, 0.424)
        for s in (-1, 1): decal(s * 0.009, 0.388, 0.0085, 0.013, C('#FFFFFF'), off=0.0044, nr=4)   # 앞니
        return True


# =============================== 사슴 ===============================
class Deer(Species):
    key, name = 'deer', '사슴'
    eye_xy = (0.1, 0.505)
    tail_pivot, ear_pivot = (0, 0.17, -0.15), (0.17, 0.585, -0.03)
    def sdf(self, sh, st, ctx):
        HC, HR = np.array([0, 0.47, 0.0]), np.array([0.225, 0.2, 0.2])
        sh.add(lambda p: sd_ell(p, (0, 0.2, -0.175), (0.04, 0.05, 0.035)), J_TAIL, 'tail', 0.02)
        sh.add(lambda p: sd_ell(p, HC, HR), J_HEAD, 'head', 0.08)
        for s in (-1, 1):
            sh.add(lambda p, s=s: sd_ell(p, (s * 0.115, 0.41, 0.085), (0.09, 0.075, 0.08)), J_HEAD, 'cheek', 0.05)
            # 옆으로 뻗은 나뭇잎 귀
            sh.add(lambda p, s=s, R=Rz(s * 1.0) @ Rx(0.2): sd_ell(p, (s * 0.25, 0.57, -0.02), (0.035, 0.085, 0.022), R), EJ(s), 'ear', 0.03)
            # 작은 뿔 (가지 두 개)
            a = np.array([s * 0.085, 0.64, -0.03]); b = a + np.array([s * 0.035, 0.12, -0.03]); c = b + np.array([s * 0.04, 0.06, 0.02]); d = b + np.array([-s * 0.01, 0.075, -0.02])
            mid = a + (b - a) * 0.55; e = mid + np.array([s * 0.055, 0.03, 0.03])
            for u, v, r0, r1 in ((a, b, 0.02, 0.016), (b, c, 0.015, 0.011), (b, d, 0.015, 0.011), (mid, e, 0.014, 0.01)):
                sh.add(lambda p, u=u, v=v, r0=r0, r1=r1: sd_cap(p, u, v, r0, r1), J_HEAD, 'antler', 0.012)
        sh.add(lambda p: sd_ell(p, (0, 0.405, 0.155), (0.07, 0.052, 0.075)), J_HEAD, 'muzzle', 0.05)
        sh.add(lambda p: sd_ell(p, (0, 0.428, 0.222), (0.026, 0.018, 0.016)), J_HEAD, 'nose', 0.012)
        return HC, HR
    def color(self, P, N, lab, col, st, ctx):
        n = headn(P, ctx['HC'], ctx['HR']); F_, W_ = C(st['fur']), C(st['white'])
        hm = lab == 'head'; col[hm] = F_
        col[hm & (n[:, 1] < -0.35) & (n[:, 2] > 0.2)] = W_
        spot = hm & (n[:, 2] < 0.1) & (n[:, 1] > -0.2) & (np.sin(P[:, 0] * 80) * np.sin(P[:, 1] * 70 + P[:, 2] * 40) > 0.75)
        col[spot] = W_
        col[lab == 'cheek'] = F_ * np.array([1.06, 1.04, 1.0, 1]); col[lab == 'muzzle'] = W_
        em = lab == 'ear'; col[em] = F_; col[em & (N[:, 2] > 0.3)] = C('#F4C9B8')
        col[lab == 'antler'] = C('#E8D7B8')
        col[lab == 'tail'] = W_
        col[lab == 'nose'] = C('#2A1C18')
    def mouth(self, decal, hit, st): return soft_mouth(decal, st, 0.41)


SPECIES = {'bear': Bear(), 'panda': Panda(), 'fox': Fox(), 'raccoon': Raccoon(), 'squirrel': Squirrel(), 'deer': Deer()}
PAL = {
    'bear': dict(white='#EED9B8', fur='#8E5E3B', mark=None, earin='#C99A72'),
    'panda': dict(white='#FAFAF5', fur='#24222A', mark=None),
    'fox': dict(white='#FFF6EC', fur='#E8823A', mark='#3A2620'),
    'raccoon': dict(white='#F4F1EC', fur='#8E8C96', mark='#2A2830'),
    'squirrel': dict(white='#FFF1DC', fur='#C9783C', mark='#5A3420'),
    'deer': dict(white='#FFF5E6', fur='#B97C4A', mark=None),
}


def stage1(key):
    st = copy.deepcopy(an.stages_for('dog')[0])          # 1단계 공통 설정을 빌려 씀
    st.update(PAL[key]); st['species'] = SPECIES[key]; st['pattern'] = 'base'
    st['eyes'] = 'cute'; st['mouth'] = 'smile'; st['outfit'] = an.OUTFIT['dog']
    st['gicol'] = st['pantscol'] = st['fur']; st['trim'] = st['white']
    st['extra_joints'] = SPECIES[key].extra(st)
    return st


if __name__ == '__main__':
    kg, kacc = rh.read_glb(sys.argv[1]); out = sys.argv[2]
    args = sys.argv[3:]; check = 'check' in args
    keys = [a for a in args if a in SPECIES] or list(SPECIES)
    for key in keys:
        d = os.path.join(out, key); os.makedirs(d, exist_ok=True)
        st = stage1(key); p = f"{d}/{key}_stage1.glb"
        tris, chk, aura = rh.write(st, 0, kg, kacc, p)
        print(key, 'tris', tris, flush=True)
        if check:
            idle = rh.pose_mats(kg, kacc, 'idle', 0.0)
            par = {N_TORSO: rh.J_TORSO, N_HEAD: J_HEAD}
            if st['extra_joints']: idle = np.concatenate([idle, np.stack([idle[par[pn]] for _, pn, _ in st['extra_joints']])])
            rh.render(chk, aura, idle, 0.4, f"{d}/_r_a.png", zoom=0.95)
            rh.render(chk, aura, idle, 2.6, f"{d}/_r_b.png", zoom=0.95)
