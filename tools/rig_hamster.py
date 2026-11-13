"""햄스터 4단계 각성 — Kenney Mini Characters 뼈대/애니메이션 사용 (CC0).
이음새 없는 SDF 메시 + 곡면 데칼 얼굴 + 부드러운 스킨 가중치.
사용법: python3 rig_hamster.py <kenney character glb> <출력폴더> [check]
"""
import json, struct, math, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_hamster as mh
from make_hamster import C, Rx, Ry, Rz, basis_y, torus, icosphere, lathe, FLAME, gradient_color

# ================= Kenney GLB 읽기 =================
def read_glb(path):
    d = open(path, 'rb').read()
    jl = struct.unpack('<I', d[12:16])[0]; g = json.loads(d[20:20 + jl]); b = d[20 + jl + 8:]
    def acc(i):
        a = g['accessors'][i]; v = g['bufferViews'][a['bufferView']]
        dt = {5126: 'f4', 5123: 'u2', 5121: 'u1', 5125: 'u4'}[a['componentType']]
        n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]
        o = v.get('byteOffset', 0) + a.get('byteOffset', 0)
        return np.frombuffer(b, dt, a['count'] * n, o).reshape(a['count'], n).copy()
    return g, acc

# ================= SDF =================
def sd_ell(p, c, r, R=None):
    q = p - np.asarray(c, float)
    if R is not None: q = q @ np.asarray(R)
    r = np.asarray(r, float)
    k0 = np.linalg.norm(q / r, axis=-1); k1 = np.linalg.norm(q / (r * r), axis=-1)
    return k0 * (k0 - 1) / np.maximum(k1, 1e-9)
def sd_cap(p, a, b, ra, rb):
    a, b = np.asarray(a, float), np.asarray(b, float); pa = p - a; ba = b - a
    h = np.clip((pa @ ba) / (ba @ ba), 0, 1)
    return np.linalg.norm(pa - h[:, None] * ba, axis=-1) - (ra + (rb - ra) * h)
def smin(a, b, k):
    if k <= 0: return np.minimum(a, b)
    h = np.maximum(k - np.abs(a - b), 0) / k
    return np.minimum(a, b) - h * h * k * 0.25

class Shape:
    """프리미티브 목록: (fn, joint, label, k)"""
    def __init__(self): self.prims = []
    def add(self, fn, joint, label, k): self.prims.append((fn, joint, label, k))
    def eval(self, p, detail=False):
        d = None; raw = []
        for fn, j, lab, k in self.prims:
            v = fn(p); raw.append(v)
            d = v if d is None else smin(d, v, k)
        if not detail: return d
        return d, np.stack(raw, 1)
    def grad(self, p, h=2e-4):
        g = np.zeros_like(p)
        for i in range(3):
            e = np.zeros(3); e[i] = h
            g[:, i] = (self.eval(p + e) - self.eval(p - e)) / (2 * h)
        return g
    def project(self, p, it=4):
        for _ in range(it):
            f = self.eval(p); g = self.grad(p)
            p = p - (f / np.maximum((g * g).sum(1), 1e-9))[:, None] * g
        return p

# ================= Surface Nets =================
def surface_nets(shape, lo, hi, cell):
    xs = [np.arange(lo[i], hi[i] + cell, cell) for i in range(3)]
    nx, ny, nz = map(len, xs)
    G = np.stack(np.meshgrid(*xs, indexing='ij'), -1).reshape(-1, 3)
    F = np.concatenate([shape.eval(G[i:i + 400000]) for i in range(0, len(G), 400000)]).reshape(nx, ny, nz).astype('f4')
    ins = F < 0
    corners = [(a, b, c) for a in (0, 1) for b in (0, 1) for c in (0, 1)]
    cs = [ins[a:nx - 1 + a, b:ny - 1 + b, c:nz - 1 + c] for a, b, c in corners]
    anyin = np.logical_or.reduce(cs); allin = np.logical_and.reduce(cs)
    act = np.argwhere(anyin & ~allin)
    vid = -np.ones((nx - 1, ny - 1, nz - 1), np.int64); vid[tuple(act.T)] = np.arange(len(act))
    edges = [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7), (0, 4), (1, 5), (2, 6), (3, 7)]
    acc = np.zeros((len(act), 3)); cnt = np.zeros(len(act))
    i, j, k = act.T
    for e0, e1 in edges:
        c0, c1 = np.array(corners[e0]), np.array(corners[e1])
        f0 = F[i + c0[0], j + c0[1], k + c0[2]]; f1 = F[i + c1[0], j + c1[1], k + c1[2]]
        m = (f0 < 0) != (f1 < 0)
        t = np.where(m, f0 / np.where(m, f0 - f1, 1), 0)
        acc += m[:, None] * (c0 + t[:, None] * (c1 - c0)); cnt += m
    P = (act + acc / cnt[:, None]) * cell + np.asarray(lo)
    quads = []
    # x축 에지
    m = ins[:-1, 1:-1, 1:-1] != ins[1:, 1:-1, 1:-1]; e = np.argwhere(m); a, b, c = e[:, 0], e[:, 1] + 1, e[:, 2] + 1
    quads.append(np.stack([vid[a, b - 1, c - 1], vid[a, b, c - 1], vid[a, b, c], vid[a, b - 1, c]], 1))
    m = ins[1:-1, :-1, 1:-1] != ins[1:-1, 1:, 1:-1]; e = np.argwhere(m); a, b, c = e[:, 0] + 1, e[:, 1], e[:, 2] + 1
    quads.append(np.stack([vid[a - 1, b, c - 1], vid[a, b, c - 1], vid[a, b, c], vid[a - 1, b, c]], 1))
    m = ins[1:-1, 1:-1, :-1] != ins[1:-1, 1:-1, 1:]; e = np.argwhere(m); a, b, c = e[:, 0] + 1, e[:, 1] + 1, e[:, 2]
    quads.append(np.stack([vid[a - 1, b - 1, c], vid[a, b - 1, c], vid[a, b, c], vid[a - 1, b, c]], 1))
    Q = np.vstack(quads)
    T = np.vstack([Q[:, [0, 1, 2]], Q[:, [0, 2, 3]]])
    P = shape.project(P, 3)
    N = shape.grad(P); N /= np.linalg.norm(N, axis=1, keepdims=True)
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    flip = (fn * N[T].mean(1)).sum(1) < 0
    T[flip] = T[flip][:, ::-1]
    return P, N, T

# ================= 리그 정보 =================
J_ROOT, J_LEGL, J_LEGR, J_TORSO, J_ARML, J_ARMR, J_HEAD = range(7)

# ================= 단계별 햄스터 =================
import copy
STAGES = copy.deepcopy(mh.STAGES)
STAGES[1]['glasses'] = None                                    # 2단계: 안경 벗음
STAGES[2]['aura'] = dict(style='light', n=20, h=(0.6, 1.0), R=0.48, core='#FFFFFF', col='#38E6FF', sparks=28,
                         bolts=7, arcs=3, halo='#7FF4FF', boltcore='#FFFFFF')
STAGES[3] = dict(key='stage4', name='최종 · 흑번개', S=1.17, rad=(0.375, 0.415, 0.345),
                 white='#ADA6BF', fur='#25222E', mark='#E3194B', pattern='stripes', ears='tuft',
                 eyes='glow', eyecol='#FF2E55', sclera='#07040C', brow='#07040C', glasses=None, mouth='firm', fangs=True,
                 crest='#25222E', wrist='#E3194B', paw='#8C8598', earin='#C44A6A', blush=False,
                 aura=dict(style='dark', n=22, h=(0.65, 1.1), R=0.5, core='#2A0E1C', col='#07040C', sparks=26, sparkcol='#FF2E63',
                           bolts=8, arcs=3, halo='#FF1F55', boltcore='#000000'))
STAGES[0].update(gi=True, crestlv=0, mus=0.0)
STAGES[1].update(gi=True, crestlv=0, ears='round', eyes='brave2', mus=0.45)
STAGES[2].update(gi=True, crestlv=0, ears='round', mus=0.75)
STAGES[3].update(gi=False, crestlv=0, ears='round', pecs=True, abs=True, pantscol='#2A2333', belt='#E3194B', mus=1.0)
AURA_SHELL = {}   # 오라는 입자 방식(aura.js)으로 대체
# 1단계: 직업이 느껴지는 일상복 (햄스터 = 프로그래머 후드티)
STAGES[0].update(gi=False, outfit=dict(top='#7FD1C3', collar='crew', hood=True, strings='#FFFFFF', pocket=True, pants='#3B4A6B', sleeve=0.232))
# 2단계: 머리띠 없이 손목에 천을 감은 도복
STAGES[1].update(headband=None, wraps='#F2EEE6', gisleeve=0.185)
for _st in STAGES:
    if _st.get('aura'): _st['aura'].update(n=0, sparks=0)
TOP_SCALE = [1.0, 1.05, 1.11, 1.17, 1.24]

def build(st, si):
    big = st['key'] != 'stage1'
    m4 = st.get('muscle', False)
    sh = Shape()
    HC, HR = np.array([0, 0.475, 0.0]), np.array([0.245, 0.205, 0.21])
    mus = st.get('mus', 0.0)
    BC, BR = np.array([0, 0.245, -0.01]), np.array([0.19 + 0.03 * mus, 0.165 + 0.006 * mus, 0.165 + 0.018 * mus])
    sh.add(lambda p: sd_ell(p, BC, BR), J_TORSO, 'body', 0)
    SP = st.get('species')
    BBOX = ((-0.42, -0.01, -0.3), (0.42, 0.86, 0.32))
    if SP is None:
        sh.add(lambda p: sd_ell(p, (0, 0.17, -0.17), (0.035, 0.035, 0.035)), J_TORSO, 'tail', 0.02)
        sh.add(lambda p: sd_ell(p, HC, HR), J_HEAD, 'head', 0.08)
        for s in (-1, 1):
            sh.add(lambda p, s=s: sd_ell(p, (s * 0.125, 0.405, 0.095), (0.1, 0.085, 0.09)), J_HEAD, 'cheek', 0.05)
        sh.add(lambda p: sd_ell(p, (0, 0.415, 0.15), (0.072, 0.052, 0.06)), J_HEAD, 'muzzle', 0.05)
        sh.add(lambda p: sd_ell(p, (0, 0.44, 0.205), (0.022, 0.016, 0.016)), J_HEAD, 'nose', 0.012)
        # 귀
        for s in (-1, 1):
            if st['ears'] == 'point':
                R = Rz(-s * 0.35)
                sh.add(lambda p, s=s, R=R: sd_ell(p, (s * 0.165, 0.69, -0.03), (0.07, 0.13, 0.03), R), J_HEAD, 'ear', 0.035)
            else:
                R = Rz(-s * 0.45)
                sh.add(lambda p, s=s, R=R: sd_ell(p, (s * 0.17, 0.645, -0.03), (0.078, 0.078, 0.03), R), J_HEAD, 'ear', 0.03)
                if st['ears'] == 'tuft':
                    sh.add(lambda p, s=s: sd_ell(p, (s * 0.22, 0.73, -0.035), (0.02, 0.05, 0.015), Rz(-s * 0.6)), J_HEAD, 'mark', 0.02)
    else:
        HC, HR = SP.sdf(sh, st, dict(BC=BC, BR=BR, mus=mus))
        BBOX = SP.bbox
    # 볏 (3단계)
    lv = st.get('crestlv', 0)
    if lv:
        tufts = [(0, 0.68, -0.04, 0.12, 0.9), (0.06, 0.67, -0.05, 0.1, 1.0), (-0.06, 0.67, -0.05, 0.1, 1.0), (0.0, 0.63, -0.13, 0.1, 1.3)]
        if lv == 1: tufts = [(0, 0.675, 0.0, 0.065, 0.55)]
        if lv == 2: tufts = [(0, 0.678, -0.02, 0.09, 0.75), (0.055, 0.67, -0.035, 0.07, 0.9), (-0.055, 0.67, -0.035, 0.07, 0.9)]
        for x, y, z, ln, tilt in tufts:
            R = Rx(-tilt) @ Rz(-x * 4)
            sh.add(lambda p, c=(x, y, z), ln=ln, R=R: sd_ell(p, np.array(c) + R @ np.array([0, ln * 0.6, 0]), (0.03, ln, 0.022), R), J_HEAD, 'crest', 0.03)
    # 팔 (기본자세: 옆으로 뻗음)
    ar = 1.0 + 0.32 * mus
    for s, J in ((1, J_ARML), (-1, J_ARMR)):
        sh.add(lambda p, s=s: sd_cap(p, (s * 0.12, 0.29, -0.01), (s * 0.25, 0.285, 0.01), 0.05 * ar, 0.042 * (1 + 0.45 * mus)), J, 'arm', 0.05)
        if mus > 0:
            sh.add(lambda p, s=s: sd_ell(p, (s * 0.128, 0.31, -0.006), (0.052 + 0.024 * mus, 0.048 + 0.02 * mus, 0.052 + 0.016 * mus)), J, 'arm', 0.04)
            sh.add(lambda p, s=s: sd_ell(p, (s * 0.178, 0.303 + 0.012 * mus, 0.012), (0.046 + 0.016 * mus, 0.036 + 0.024 * mus, 0.04 + 0.02 * mus)), J, 'arm', 0.03)
        sh.add(lambda p, s=s: sd_ell(p, (s * (0.27 + 0.02 * (ar - 1)), 0.285, 0.015), (0.048 * ar, 0.052 * ar, 0.055 * ar)), J, 'paw', 0.03)
    # 다리
    for s, J in ((1, J_LEGL), (-1, J_LEGR)):
        sh.add(lambda p, s=s: sd_cap(p, (s * 0.085, 0.15, -0.02), (s * 0.09, 0.055, 0.0), 0.06 * (1 + 0.28 * mus), 0.055 * (1 + 0.15 * mus)), J, 'leg', 0.05)
        sh.add(lambda p, s=s: sd_ell(p, (s * 0.09, 0.032, 0.035), (0.065, 0.034, 0.085)), J, 'foot', 0.03)

    OUT = st.get('outfit')
    GI = st.get('gi', False) or bool(OUT); BELT_Y = 0.165
    HEM = 0.112 if (OUT and OUT.get('shorts')) else 0.072
    SX = OUT.get('sleeve', 0.232) if OUT else st.get('gisleeve', 0.232)
    sh.add(lambda p: np.maximum(sd_ell(p, BC, BR + 0.009), p[:, 1] - BELT_Y), J_TORSO, 'pantsb', 0.006)
    for s, J in ((1, J_LEGL), (-1, J_LEGR)):
        sh.add(lambda p, s=s: np.maximum(sd_cap(p, (s * 0.085, 0.17, -0.02), (s * 0.093, 0.08, 0.0), 0.069 * (1 + 0.25 * mus), 0.074 * (1 + 0.15 * mus)), HEM - p[:, 1]), J, 'pants', 0.012)
    if GI:
        sh.add(lambda p: np.maximum(sd_ell(p, BC, BR + 0.012), np.maximum(BELT_Y - 0.014 - p[:, 1], p[:, 1] - 0.37)), J_TORSO, 'gitop', 0.006)
        for s, J in ((1, J_ARML), (-1, J_ARMR)):
            sh.add(lambda p, s=s: np.maximum(sd_cap(p, (s * 0.1, 0.29, -0.01), (s * 0.25, 0.287, 0.008), 0.06 + 0.03 * mus, 0.066 + 0.026 * mus), s * p[:, 0] - SX),
                   J, 'sleeve', 0.01)
    if OUT and OUT.get('hood'):
        sh.add(lambda p: sd_ell(p, (0, 0.338, -0.135), (0.15, 0.075, 0.08)), J_TORSO, 'hood', 0.02)
    if OUT and OUT.get('panel'):
        pw_, py_ = OUT['panel'].get('w', 0.13), OUT['panel'].get('y', 0.33)
        sh.add(lambda p: np.maximum(sd_ell(p, BC, BR + 0.019), np.maximum(np.abs(p[:, 0]) - pw_, np.maximum(p[:, 1] - py_, 0.06 - p[:, 2]))), J_TORSO, 'panel', 0.004)
    if mus > 0 and not st.get('pecs'):          # 도복 속 가슴 근육 (은은하게)
        for s in (-1, 1):
            sh.add(lambda p, s=s: sd_ell(p, (s * 0.068, 0.3, 0.1 + 0.012 * mus), (0.06 + 0.012 * mus, 0.045, 0.045)), J_TORSO, 'body', 0.04)
    if st.get('abs'):
        for yy in (0.268, 0.232, 0.196):
            zf = BR[2] * math.sqrt(max(0.0, 1 - ((yy - BC[1]) / BR[1]) ** 2)) + BC[2]
            for s in (-1, 1):
                sh.add(lambda p, s=s, yy=yy, zf=zf: sd_ell(p, (s * 0.032, yy, zf - 0.012), (0.027, 0.016, 0.022)), J_TORSO, 'body', 0.012)
    if st.get('pecs'):
        for s in (-1, 1):
            sh.add(lambda p, s=s: sd_ell(p, (s * 0.072, 0.302, 0.13), (0.08, 0.056, 0.05)), J_TORSO, 'body', 0.035)
    P, N, T = surface_nets(sh, BBOX[0], BBOX[1], 0.006)
    d, raw = sh.eval(P, True)
    joints = np.array([pr[1] for pr in sh.prims]); labels = [pr[2] for pr in sh.prims]

    # ---- 스킨 가중치: 관절 그룹별 거리의 softmin ----
    NJ = 7 + len(st.get('extra_joints', []))
    gd = np.full((len(P), NJ), 1e3)
    for jj in range(NJ):
        m = joints == jj
        if m.any(): gd[:, jj] = raw[:, m].min(1)
    tau = np.where(np.arange(NJ) == J_HEAD, 0.02, np.where(np.arange(NJ) >= 7, 0.012, 0.014))
    W = np.exp(-(gd - gd.min(1, keepdims=True)) / tau); W[:, J_ROOT] = 0
    top = np.argsort(-W, 1)[:, :4]; Wt = np.take_along_axis(W, top, 1); Wt[Wt < 0.02] = 0; Wt /= Wt.sum(1, keepdims=True)

    # ---- 색 ----
    lab = np.array(labels)[raw.argmin(1)]
    for cl in ('pantsb', 'pants', 'gitop', 'sleeve'):          # 옷이 표면에 닿아 있으면 옷이 우선
        idx = [i for i, l in enumerate(labels) if l == cl]
        if idx: lab[(raw[:, idx].min(1) < 0.0045) & ~np.isin(lab, ['paw', 'foot'])] = cl
    white, fur = C(st['white']), C(st['fur']); mark = C(st['mark']) if st['mark'] else fur
    pinkc = C(st.get('paw', '#8E7BD6' if m4 else '#F7A8B4'))
    bc_fn = mh.body_color(st)
    nh = (P - HC) / HR; nh /= np.linalg.norm(nh, axis=1, keepdims=True)
    nb = (P - BC) / BR; nb /= np.linalg.norm(nb, axis=1, keepdims=True)
    col = np.tile(white, (len(P), 1))
    hm = np.isin(lab, ['head', 'cheek', 'muzzle']); col[hm] = bc_fn(nh[hm], P[hm])
    bm = np.isin(lab, ['body', 'leg']); col[bm] = bc_fn(nb[bm], P[bm])
    col[np.isin(lab, ['cheek', 'muzzle'])] = white
    col[lab == 'tail'] = fur; col[lab == 'nose'] = C('#F27D92')
    col[np.isin(lab, ['paw', 'foot'])] = pinkc
    col[lab == 'arm'] = fur if big else white
    col[np.isin(lab, ['crest', 'mark'])] = C(st.get('crest') or st['mark'] or st['fur'])
    em = lab == 'ear'
    inner = em & (N[:, 2] > 0.35) & (np.abs(np.abs(P[:, 0]) - 0.17 - 0.012 * (st['ears'] == 'point')) < 0.04) & (np.abs(P[:, 1] - (0.70 if st['ears'] == 'point' else 0.65)) < (0.08 if st['ears'] == 'point' else 0.045))
    col[em] = fur; col[inner] = C(st.get('earin', '#FF6FB5' if m4 else '#F7A8B4'))
    if SP is not None: SP.color(P, N, lab, col, st, dict(HC=HC, HR=HR, BC=BC, BR=BR))

    gi_c, trim_c = C(st.get('gicol', '#2E3F78')), C(st.get('trim', '#F4ECD8'))
    pants_c = C(st.get('pantscol', st.get('gicol', '#2E3F78')))
    pm = np.isin(lab, ['pants', 'pantsb']); col[pm] = pants_c
    col[pm & (P[:, 1] < 0.095) & np.isin(lab, ['pants'])] = pants_c * np.array([0.78, 0.78, 0.78, 1])
    ay_ = P[:, 1]
    col[np.isin(lab, ['leg']) | (np.isin(lab, ['body', 'tail']) & (ay_ < BELT_Y))] = pants_c
    if OUT:
        top_c = C(OUT['top']); pants_c = C(OUT.get('pants', '#3B4A6B'))
        col[np.isin(lab, ['pants', 'pantsb'])] = pants_c
        col[np.isin(lab, ['pants']) & (P[:, 1] < HEM + 0.02)] = pants_c * np.array([0.82, 0.82, 0.82, 1])
        col[(lab == 'leg') & (P[:, 1] < HEM)] = C(st['fur'] if SP is not None else st['white'])
        col[(lab == 'leg') & (P[:, 1] >= HEM)] = pants_c
        chin = (P[:, 2] > 0.1) & (ay_ > 0.3)
        gm = (lab == 'gitop') | (np.isin(lab, ['body', 'head']) & (ay_ > BELT_Y - 0.015) & (ay_ < 0.345) & ~chin)
        col[gm] = top_c
        ax, ay = np.abs(P[:, 0]), P[:, 1]; fr = P[:, 2] > 0.02
        if OUT.get('stripe'):
            col[gm & (np.sin(ay * 70) > 0.55)] = C(OUT['stripe'])
        cl = OUT.get('collar', 'crew')
        if cl == 'v':
            v = (ay - 0.2) * 0.55; col[gm & fr & (ax < v)] = C(OUT.get('inner', st['white']))
        elif cl == 'shirt':
            v = (ay - 0.24) * 0.45; col[gm & fr & (ax < v)] = C(OUT.get('inner', '#FFFFFF'))
            col[gm & fr & (ax >= v) & (ax < v + 0.024) & (ay > 0.27)] = C(OUT.get('collarcol', OUT.get('inner', '#FFFFFF')))
        if OUT.get('pocket'):
            col[gm & fr & (ax < 0.075) & (ay > 0.18) & (ay < 0.235)] = top_c * np.array([0.84, 0.84, 0.84, 1])
        col[lab == 'hood'] = top_c * np.array([0.9, 0.9, 0.9, 1])
        if OUT.get('panel'):
            pc_ = C(OUT['panel']['color']); col[lab == 'panel'] = pc_
            col[(lab == 'panel') & (np.abs(P[:, 1] - 0.215) < 0.03) & (ax < 0.05)] = pc_ * np.array([0.9, 0.9, 0.9, 1])   # 주머니
        sm = lab == 'sleeve'; col[sm] = C(OUT.get('sleevecol', OUT['top']))
        col[sm & (ax > SX - 0.016)] = C(OUT.get('sleevecol', OUT['top'])) * np.array([0.85, 0.85, 0.85, 1])
    elif GI:
        chin = (P[:, 2] > 0.1) & (ay_ > 0.3)
        gm = (lab == 'gitop') | (np.isin(lab, ['body', 'head']) & (ay_ > BELT_Y - 0.015) & (ay_ < 0.345) & ~chin)
        col[gm] = gi_c
        ax, ay = np.abs(P[:, 0]), P[:, 1]; fr = P[:, 2] > 0.02
        v = (ay - 0.175) * 0.62
        col[gm & fr & (ax < v)] = white
        col[gm & fr & (ax >= v) & (ax < v + 0.021)] = trim_c
        col[gm & (ay < BELT_Y + 0.0)] = gi_c * np.array([0.85, 0.85, 0.85, 1])
        sm = lab == 'sleeve'; col[sm] = gi_c; col[sm & (ax > SX - 0.019)] = trim_c
    body = dict(P=P, N=N, T=T, C=col, J=top, W=Wt)

    # ================= 오라 껍질 (몸 실루엣을 감싸는 자연스러운 기운) =================
    shells = []
    if st['key'] in AURA_SHELL:
        cfg = AURA_SHELL[st['key']]
        specs = [(0.03, 0.2, 'aura', C(cfg['inner'], 0.9), 0.013)]
        if cfg['dark']:
            specs += [(0.075, 0.33, 'auradark', C(cfg['outer'], 0.85), 0.015), (0.1, 0.38, 'aura', C(cfg['inner'], 0.7), 0.016)]
        else:
            specs += [(0.085, 0.36, 'aura', C(cfg['outer'], 0.8), 0.015)]
        for off, topr, kind, colr, cell in specs:
            a_sh = Shape()
            a_sh.add(lambda p, off=off: sh.eval(p) - off, J_TORSO, 'a', 0)
            if topr: a_sh.add(lambda p, off=off, topr=topr: sd_ell(p, (0, 0.6 + topr * 0.35, -0.02), (0.16 + off, topr, 0.15 + off)), J_TORSO, 'b', 0.18)
            P2, N2, T2 = surface_nets(a_sh, (-0.62, -0.12, -0.5), (0.62, 1.35, 0.5), cell)
            _, raw2 = sh.eval(P2, True)
            gd2 = np.full((len(P2), 7), 1e3)
            for jj in range(7):
                m = joints == jj
                if m.any(): gd2[:, jj] = raw2[:, m].min(1)
            W2 = np.exp(-(gd2 - gd2.min(1, keepdims=True)) / 0.05); W2[:, J_ROOT] = 0
            t2 = np.argsort(-W2, 1)[:, :4]; w2 = np.take_along_axis(W2, t2, 1); w2[w2 < 0.02] = 0; w2 /= w2.sum(1, keepdims=True)
            shells.append(dict(P=P2, N=N2, T=T2, C=np.tile(colr, (len(P2), 1)), J=t2, W=w2, kind=kind))
    body['shells'] = shells

    # ================= 데칼 (곡면 스티커) =================
    decals = {'toon': [], 'glow': []}
    def hit(x, y):
        """정면에서 (x,y)로 쏜 광선이 표면에 닿는 점"""
        lo_, hi_ = -0.05, 0.4
        for _ in range(40):
            md = (lo_ + hi_) / 2
            if sh.eval(np.array([[x, y, md]]))[0] < 0: lo_ = md
            else: hi_ = md
        p = np.array([x, y, (lo_ + hi_) / 2]); n = sh.grad(p[None])[0]; return p, n / np.linalg.norm(n)
    def decal(x, y, a, b, color, roll=0.0, off=0.0022, glow=False, top=None, bottom=None, nr=7, ns=44, joint=J_HEAD, shift=(0, 0)):
        c, n = hit(x, y)
        u = np.cross((0, 1, 0), n); u /= np.linalg.norm(u); v = np.cross(n, u)
        cr, sr = math.cos(roll), math.sin(roll); u, v = cr * u + sr * v, -sr * u + cr * v
        pts = [np.array([0.0, 0.0])]
        for r in np.linspace(1 / nr, 1, nr):
            for t in np.linspace(0, 2 * math.pi, ns, endpoint=False):
                yy = math.sin(t) * b * r
                if top is not None: yy = min(yy, top * b)
                if bottom is not None: yy = max(yy, bottom * b)
                pts.append(np.array([math.cos(t) * a * r, yy]))
        pts = np.array(pts) + np.array(shift)
        Q = c + pts[:, :1] * u + pts[:, 1:] * v + n * 0.02
        Q = sh.project(Q, 5); NN = sh.grad(Q); NN /= np.linalg.norm(NN, axis=1, keepdims=True)
        Q = Q + NN * off
        F = [(0, 1 + (i + 1) % ns, 1 + i) for i in range(ns)]
        for rr in range(nr - 1):
            b0, b1 = 1 + rr * ns, 1 + (rr + 1) * ns
            for i in range(ns):
                j = (i + 1) % ns; F += [(b0 + i, b0 + j, b1 + j), (b0 + i, b1 + j, b1 + i)]
        F = np.array(F)
        fn = np.cross(Q[F[:, 1]] - Q[F[:, 0]], Q[F[:, 2]] - Q[F[:, 0]])
        if (fn * NN[F].mean(1)).sum() < 0: F = F[:, ::-1]
        decals['glow' if glow else 'toon'].append(dict(P=Q, N=NN, T=F, C=np.tile(color, (len(Q), 1)), joint=joint))
    ex, ey = (0.11, 0.505) if SP is None else SP.eye_xy
    E = st['eyes']
    if SP is not None and E != 'pc' and SP.eyes(decal, hit, st, ex, ey): E = '_custom'
    for s in (-1, 1):
        if E == 'pc':      # 그림책풍(Pepper&Carrot 느낌): 크고 동그란 눈 — 홍채를 크게, 동공은 살짝 안쪽·아래로(앞을 바라보게)
            o = st.get('pc_eye', 1.0); dk = C('#2A1A14'); gx, gy = -s * 0.009 * o, -0.006 * o      # 시선: 코 쪽으로
            ix, iy = s * ex + gx, ey + gy
            decal(s * ex, ey, 0.060 * o, 0.069 * o, dk)
            decal(s * ex, ey + 0.007 * o, 0.063 * o, 0.068 * o, dk, top=0.9, bottom=0.2)       # 윗눈꺼풀을 두껍게
            decal(s * ex, ey - 0.003 * o, 0.053 * o, 0.060 * o, C('#FFFBF2'), off=0.0030)
            decal(ix, iy, 0.045 * o, 0.054 * o, C(st.get('iris', '#7A5A34')), off=0.0038)
            decal(ix, iy + 0.024 * o, 0.043 * o, 0.022 * o, C(st.get('iris2', '#3A2A1A')), off=0.0041, nr=4)   # 윗눈꺼풀 그늘
            decal(ix, iy - 0.026 * o, 0.024 * o, 0.012 * o, C('#FFFFFF') * 0.5 + C(st.get('iris', '#7A5A34')) * 0.5, off=0.0041, nr=4)   # 아래쪽 밝은 반사
            decal(ix + gx * 0.4, iy + gy * 0.4, 0.029 * o, 0.034 * o, C('#0E0A08'), off=0.0046)
            decal(ix + s * 0.014 * o, iy + 0.018 * o, 0.014 * o, 0.014 * o, C('#FFFFFF'), off=0.0054)       # 큰 반짝이: 동공 위 바깥
            decal(ix - s * 0.012 * o, iy - 0.016 * o, 0.0065 * o, 0.0065 * o, C('#FFFFFF'), off=0.0054)
            decal(s * ex + s * 0.062 * o, ey + 0.036 * o, 0.013 * o, 0.006 * o, dk, roll=s * 0.6, nr=3)   # 바깥 눈꼬리 속눈썹
        elif E == 'cute':
            decal(s * ex, ey, 0.052, 0.064, C('#2A1A14'))
            decal(s * ex + s * 0.016, ey + 0.022, 0.019, 0.019, C('#FFFFFF'), off=0.0042)
            decal(s * ex - s * 0.017, ey - 0.022, 0.009, 0.009, C('#FFFFFF'), off=0.0042)
        elif E == 'brave2':
            decal(s * ex, ey, 0.05, 0.05, C('#2A1A14'), roll=-s * 0.12, top=0.74)
            decal(s * ex + s * 0.014, ey + 0.017, 0.015, 0.015, C('#FFFFFF'), off=0.0042)
            decal(s * ex - s * 0.015, ey - 0.02, 0.007, 0.007, C('#FFFFFF'), off=0.0042)
            decal(s * 0.11, ey + 0.058, 0.05, 0.011, C('#2A1A14'), roll=s * 0.34)
        elif E == 'brave':
            decal(s * ex, ey, 0.046, 0.05, C('#2A1A14'), top=0.72)
            decal(s * ex - s * 0.013, ey + 0.016, 0.014, 0.014, C('#FFFFFF'), off=0.0042)
            decal(s * 0.105, ey + 0.065, 0.045, 0.011, C('#2A1A14'), roll=s * 0.3)
        elif E == 'glow':
            decal(s * ex, ey, 0.05, 0.042, C(st.get('sclera', '#0E2A3A')), roll=-s * 0.15, top=0.7)
            decal(s * ex, ey - 0.002, 0.036, 0.028, C(st['eyecol']), roll=-s * 0.15, off=0.0040, glow=True)
            decal(s * ex, ey, 0.014, 0.012, C('#FFFFFF'), off=0.0055, glow=True)
            decal(s * 0.11, ey + 0.055, 0.05, 0.011, C(st.get('brow', '#0E4A5A')), roll=s * 0.38)
        elif E == 'rage':
            decal(s * ex, ey, 0.055, 0.036, C('#140C20'), roll=-s * 0.35)
            decal(s * ex, ey, 0.04, 0.022, C(st['eyecol']), roll=-s * 0.35, off=0.0040, glow=True)
            decal(s * ex, ey, 0.012, 0.01, C('#FFFFFF'), off=0.0055, glow=True)
            decal(s * 0.1, ey + 0.05, 0.06, 0.015, C('#120A1E'), roll=s * 0.5)
            decal(s * 0.19, 0.43, 0.04, 0.008, C(st['mark']), roll=s * 0.2, nr=4)
            decal(s * 0.19, 0.405, 0.035, 0.008, C(st['mark']), roll=s * 0.2, nr=4)
        if E == 'pc' and st.get('blush', True):
            decal(s * 0.178, 0.414, 0.032, 0.018, C('#F4A0A4'), nr=5)
        elif E != 'rage' and st.get('blush', True):
            decal(s * 0.175, 0.42, 0.04, 0.026, C('#FF9DB0'), nr=5)
    Mo = st['mouth']
    if SP is not None and SP.mouth(decal, hit, st): Mo = '_custom'
    if Mo == 'smile':
        decal(0, 0.392, 0.04, 0.032, C('#6B2B32'), top=0.25)
        decal(0, 0.378, 0.025, 0.014, C('#FF7E8F'), off=0.0036)
        for s in (-1, 1): decal(s * 0.0105, 0.397, 0.009, 0.011, C('#FFFFFF'), off=0.0042, nr=4)
    elif Mo == 'grin':
        decal(0, 0.395, 0.034, 0.018, C('#6B2B32'), roll=0.12, top=0.3)
        for s in (-1, 1): decal(s * 0.0105, 0.397, 0.009, 0.01, C('#FFFFFF'), off=0.0042, nr=4)
    elif Mo == 'firm':
        decal(0, 0.395, 0.03, 0.007, C('#6B2B32'), nr=4)
        if st.get('fangs'):
            for s in (-1, 1): decal(s * 0.017, 0.388, 0.006, 0.013, C('#FFFFFF'), off=0.0042, bottom=-0.7, top=0.1, nr=4)
    elif Mo == 'roar':
        decal(0, 0.385, 0.055, 0.045, C('#3A0F24'))
        decal(0, 0.362, 0.03, 0.013, C('#FF7E8F'), off=0.0036)
        for s in (-1, 1): decal(s * 0.03, 0.41, 0.009, 0.016, C('#FFFFFF'), off=0.0042, bottom=-0.6, nr=4)

    # ================= 강체 액세서리 (한 관절에 고정) =================
    acc = mh.Part(); acc_joint = []
    def acc_add(joint, fn):
        n0 = len(acc.g['toon']) + len(acc.g['glow']); fn()
        acc_joint.extend([joint] * (len(acc.g['toon']) + len(acc.g['glow']) - n0))
    FRAME = C('#1E1A1E')
    def seg(a_, b_, r_, col_, glow=False):
        d_ = np.asarray(b_) - np.asarray(a_)
        acc.add(lathe([(0, 0), (1, 0), (1, 1), (0, 1)], 10), basis_y(d_) @ np.diag([r_, np.linalg.norm(d_), r_]), a_, col_, glow=glow)
    def curve(pts, r_, col_, n=8):
        pts = [np.asarray(p, float) for p in pts]
        out = []
        for t in np.linspace(0, 1, n + 1):          # 2차 베지어
            out.append((1 - t) ** 2 * pts[0] + 2 * t * (1 - t) * pts[1] + t * t * pts[2])
        for p0, p1 in zip(out[:-1], out[1:]): seg(p0, p1, r_, col_)
        for p in out: acc.ell(p, r_, col_, sub=1)
    if st.get('glasses'):
        # 참고 그림처럼: 크고 동그란 검정 굵은 테, 얼굴 앞에 평평하게
        R0, r0 = 0.086, 0.0135
        rings = []
        for s in (-1, 1):
            cx, cyy = s * 0.113, ey + 0.004
            Rr = Ry(s * 0.2)
            need = -1e9
            for t in np.linspace(0, 2 * math.pi, 40, endpoint=False):
                for rr in (R0 + r0, R0, R0 * 0.6, 0.0):
                    lp = Rr @ np.array([math.cos(t) * rr, math.sin(t) * rr, 0])
                    p, _ = hit(cx + lp[0], cyy + lp[1])
                    need = max(need, p[2] - lp[2] + r0 + 0.007)
            gc = np.array([cx, cyy, need]); rings.append((gc, Rr))
            acc_add(J_HEAD, lambda gc=gc, Rr=Rr: acc.add(torus(R0, r0, 56, 12), Rr, gc, FRAME))
            acc_add(J_HEAD, lambda gc=gc, Rr=Rr: acc.add(icosphere(3), Rr @ np.diag([R0, R0, 0.002]), gc, C('#E6F6FF', 0.06), glow=True))
            acc_add(J_HEAD, lambda gc=gc, Rr=Rr, s=s: acc.add(icosphere(2), Rr @ Rz(-0.65) @ np.diag([0.011, 0.036, 0.002]),
                                                             gc + Rr @ np.array([-0.032, 0.03, 0.003]), C('#FFFFFF', 0.55), glow=True))
            acc_add(J_HEAD, lambda gc=gc, Rr=Rr, s=s: acc.add(icosphere(2), Rr @ Rz(-0.65) @ np.diag([0.006, 0.012, 0.002]),
                                                             gc + Rr @ np.array([-0.002, 0.052, 0.003]), C('#FFFFFF', 0.45), glow=True))
        (gl, Rl), (gr, Rg) = rings
        il, ir = gl + Rl @ np.array([R0, 0, 0]), gr + Rg @ np.array([-R0, 0, 0])
        pb, _ = hit(0, ey + 0.02)
        mid = np.array([0, ey + 0.03, max(pb[2] + 0.014, (il[2] + ir[2]) / 2 + 0.004)])
        acc_add(J_HEAD, lambda: curve([il + np.array([0, 0.012, 0]), mid, ir + np.array([0, 0.012, 0])], 0.0085, FRAME))
        for s, (gc, Rr) in ((-1, rings[0]), (1, rings[1])):
            o = gc + Rr @ np.array([s * R0, 0.01, 0])
            acc_add(J_HEAD, lambda o=o, s=s: curve([o, np.array([s * 0.262, o[1] + 0.006, 0.08]), np.array([s * 0.232, o[1] + 0.012, -0.05])], 0.008, FRAME))
    if st.get('headband'):
        hy = 0.565; ny = (hy - HC[1]) / HR[1]; k = math.sqrt(1 - ny * ny); colh = C(st['headband'])
        acc_add(J_HEAD, lambda: acc.add(torus(1.0, 0.075, 56, 10), Rx(math.pi / 2) @ np.diag([HR[0] * k + 0.012, HR[2] * k + 0.012, 0.34]), (0, hy, 0), colh))
        knot = np.array([0, hy, -HR[2] * k - 0.02])
        acc_add(J_HEAD, lambda: acc.ell(knot, (0.035, 0.03, 0.026), colh))
        for s in (-1, 1):
            acc_add(J_HEAD, lambda s=s: acc.ell(knot + np.array([s * 0.06, -0.07, -0.05]), (0.026, 0.085, 0.01), colh, Rx(-0.6) @ Rz(s * 0.5)))
    if SP is not None: SP.acc(acc_add, acc, hit, st, dict(HC=HC, HR=HR, BC=BC, BR=BR, seg=seg, curve=curve, ar=ar))
    kb = math.sqrt(1 - ((BELT_Y - BC[1]) / BR[1]) ** 2); brx, brz = BR[0] * kb + 0.021, BR[2] * kb + 0.021
    def torso_z(x, y, off=0.0):
        ny = (y - BC[1]) / BR[1]; nx = x / BR[0]
        return BC[2] + BR[2] * math.sqrt(max(0.0, 1 - nx * nx - ny * ny)) + off
    if not OUT:
        belt_c = C(st.get('belt', '#1C1A20'))
        acc_add(J_TORSO, lambda: acc.add(torus(1.0, 0.07, 64, 10), Rx(math.pi / 2) @ np.diag([brx, brz, 0.24]), (0, BELT_Y, 0), belt_c))
        knot = np.array([0.03, BELT_Y, brz + 0.006])
        acc_add(J_TORSO, lambda: acc.ell(knot, (0.026, 0.02, 0.016), belt_c))
        for s_, rz_ in ((1, -0.25), (-1, 0.35)):
            acc_add(J_TORSO, lambda s_=s_, rz_=rz_: acc.ell(knot + np.array([s_ * 0.022, -0.05, 0.006]), (0.016, 0.05, 0.008), belt_c, Rz(rz_)))
    else:
        if OUT.get('belt'):
            bc_ = C(OUT['belt'])
            acc_add(J_TORSO, lambda: acc.add(torus(1.0, 0.045, 64, 8), Rx(math.pi / 2) @ np.diag([brx - 0.004, brz - 0.004, 0.2]), (0, BELT_Y + 0.004, 0), bc_))
            acc_add(J_TORSO, lambda: acc.add(mh.box(), np.diag([0.02, 0.016, 0.006]), (0, BELT_Y + 0.004, brz + 0.006), C(OUT.get('buckle', '#D9C06A')), flat=True))
        if OUT.get('strings'):
            sc_ = C(OUT['strings'])
            for s_ in (-1, 1):
                a_ = np.array([s_ * 0.03, 0.33, torso_z(s_ * 0.03, 0.33, 0.02)]); b_ = a_ + np.array([0, -0.07, 0.012])
                acc_add(J_TORSO, lambda a_=a_, b_=b_: seg(a_, b_, 0.0045, sc_))
                acc_add(J_TORSO, lambda b_=b_: acc.ell(b_, 0.008, sc_, sub=1))
        if OUT.get('buttons'):
            bcol, xs = C(OUT['buttons'][0]), OUT['buttons'][1]
            for x_ in xs:
                for y_ in (0.205, 0.245, 0.285):
                    acc_add(J_TORSO, lambda x_=x_, y_=y_: acc.ell((x_, y_, torso_z(x_, y_, 0.015)), (0.009, 0.009, 0.005), bcol, sub=1))
        if OUT.get('panel'):
            pc_ = C(OUT['panel']['color'])
            for s_ in (-1, 1):          # 앞치마 끈
                acc_add(J_TORSO, lambda s_=s_: acc.add(torus(1.0, 0.05, 40, 6), Rx(math.pi / 2) @ np.diag([brx + 0.004, brz + 0.004, 0.16]), (0, 0.255, 0), pc_) if s_ > 0 else None)
    if st.get('wraps'):
        wc_ = C(st['wraps'])
        for s, J in ((1, J_ARML), (-1, J_ARMR)):
            for x_ in (0.198, 0.213, 0.228):
                t_ = (x_ - 0.12) / 0.13; r_ = 0.05 * ar + (0.042 * (1 + 0.45 * mus) - 0.05 * ar) * t_ + 0.004
                acc_add(J, lambda s=s, x_=x_, r_=r_: acc.add(torus(r_, 0.0085, 28, 6), Ry(math.pi / 2), (s * x_, 0.287 - 0.002 * (x_ - 0.12) / 0.13, 0.002 + 0.01 * t_), wc_))
    if st.get('wrist'):
        for s, J in ((1, J_ARML), (-1, J_ARMR)):
            acc_add(J, lambda s=s: acc.add(torus(0.046 * ar, 0.012 * ar, 28, 8), Ry(math.pi / 2), (s * 0.222, 0.287, 0.004), C(st['wrist'])))
    if st.get('flamecrown'):
        for i in range(7):
            a_ = (i - 3) * 0.32
            base = HC + np.array([math.sin(a_) * 0.16, HR[1] * 0.88, -0.03])
            dd = np.array([math.sin(a_) * 0.6, 1, -0.25]); h = (0.25 - abs(i - 3) * 0.04)
            acc_add(J_HEAD, lambda base=base, dd=dd, h=h: acc.add(FLAME, basis_y(dd) @ np.diag([0.09, h, 0.09]), base,
                                                                 gradient_color('#FFF3B0', '#FF5ACD', 0.95, 0.0, 1.3), glow=True))
    # 액세서리 → 메시 목록 (순서: toon 먼저, glow 다음으로 추가했으므로 joint 매핑을 재구성)
    acc_items = {'toon': [], 'glow': []}
    ti = gi = 0
    order = []
    # Part.add 호출 순서를 그대로 복원하기 위해 다시 계산
    allitems = []
    for key in ('toon', 'glow'):
        for item in acc.g[key]: allitems.append((key, item))
    # acc_joint 는 추가된 순서대로 쌓였으므로, 추가 순서를 추적한 seq를 쓴다
    return body, decals, acc, acc_joint, sh

# Part.add 순서 추적: mh.Part를 감싸서 각 항목에 순번을 붙임
_orig_add = mh.Part.add
def _tracked_add(self, shape, M, t, color, glow=False, flat=False):
    r = _orig_add(self, shape, M, t, color, glow, flat)
    self.seq = getattr(self, 'seq', []); self.seq.append('glow' if glow else 'toon'); return r
mh.Part.add = _tracked_add

def acc_meshes(acc, acc_joint):
    """추가 순서 → (key, item, joint)"""
    out = []; ptr = {'toon': 0, 'glow': 0}
    for kind, j in zip(getattr(acc, 'seq', []), acc_joint):
        W, N, Cc, F = acc.g[kind][ptr[kind]]; ptr[kind] += 1
        out.append((kind, dict(P=W, N=N, T=F, C=Cc), j))
    return out

CYL = lathe([(0, 0), (1, 0), (1, 1), (0, 1)], 7)

def build_aura(st):
    """반환: {'Aura': {'glow':..., 'dark':...}, 'Bolts': {...}} (각 값은 merged 튜플 또는 None)"""
    au = st.get('aura')
    if not au: return {}
    dark = au.get('style') == 'dark'
    S = 0.8; rng = np.random.default_rng(7)
    AG, AD, BG, BD = mh.Part(), mh.Part(), mh.Part(), mh.Part()
    # --- 불꽃 ---
    if dark:
        fl_main, fl_tgt = gradient_color(au['core'], au['col'], 0.62, 0.0, 1.1), AD
        fl_rim = gradient_color('#FF7A9A', au['halo'], 0.32, 0.0, 1.0)
    else:
        fl_main, fl_tgt = gradient_color(au['core'], au['col'], 0.55, 0.0, 1.2), AG
        fl_rim = None
    for i in range(au['n']):
        ang = 2 * math.pi * i / au['n'] + rng.uniform(-0.1, 0.1)
        front = max(0.0, math.cos(ang - math.pi / 2)); R0 = au['R'] * S * rng.uniform(0.92, 1.08)
        pos = np.array([math.cos(ang) * R0, rng.uniform(0.0, 0.12) * S, math.sin(ang) * R0])
        h = rng.uniform(*au['h']) * S * (1 - 0.55 * front)
        M = basis_y((math.cos(ang) * 0.25, 1, math.sin(ang) * 0.25))
        fl_tgt.add(FLAME, M @ np.diag([0.17 * S, h, 0.17 * S]), pos, fl_main, glow=True)
        if fl_rim and i % 2 == 0:
            AG.add(FLAME, M @ np.diag([0.08 * S, h * 1.08, 0.08 * S]), pos * 1.04, fl_rim, glow=True)
    for i in range(au['n'] // 2):
        ang = 2 * math.pi * (i + 0.5) / (au['n'] // 2)
        if math.cos(ang - math.pi / 2) > 0.3: continue
        pos = np.array([math.cos(ang) * au['R'] * 0.55 * S, 0.05 * S, math.sin(ang) * au['R'] * 0.55 * S])
        fl_tgt.add(FLAME, basis_y((math.cos(ang) * 0.1, 1, math.sin(ang) * 0.1)) @ np.diag([0.3 * S, au['h'][1] * 1.15 * S, 0.3 * S]), pos,
                   gradient_color(au['core'], au['col'], 0.3 if dark else 0.16, 0.0, 1.0), glow=True)
    ringc = au.get('halo', au['col'])
    if au.get('ring'): AG.add(torus(au['R'] * 1.05 * S, 0.035 * S, 48, 8), Rx(math.pi / 2), (0, 0.02 * S, 0), C(ringc, 0.55), glow=True)
    if dark and au.get('ring'): AD.add(torus(au['R'] * 0.92 * S, 0.06 * S, 48, 8), Rx(math.pi / 2), (0, 0.01 * S, 0), C('#000000', 0.6), glow=True)
    sc = C(au.get('sparkcol', au['core']))
    for i in range(au['sparks']):
        ang = rng.uniform(0, 2 * math.pi); r = au['R'] * S * rng.uniform(0.7, 1.4)
        AG.ell((math.cos(ang) * r, rng.uniform(0.1, 1.2) * S, math.sin(ang) * r), rng.uniform(0.008, 0.016), sc, sub=1, glow=True)
    # --- 번개 ---
    hc_ = au.get('halo', au['col']); halo, core = C(hc_, 0.75), C(au.get('boltcore', '#FFFFFF'), 1.0)
    halo2 = C(hc_, 0.25)
    def segment(a_, b_, w):
        d_ = b_ - a_; L_ = np.linalg.norm(d_)
        if L_ < 1e-6: return
        M = basis_y(d_)
        hs, cs = (2.6, 1.5) if dark else (3.2, 1.8)
        BG.add(CYL, M @ np.diag([w * hs, L_, w * hs]), a_, halo2, glow=True)
        BG.add(CYL, M @ np.diag([w * cs, L_, w * cs]), a_, halo, glow=True)
        (BD if dark else BG).add(CYL, M @ np.diag([w * 1.15 if dark else w * 0.75, L_, w * 1.15 if dark else w * 0.75]), a_, core, glow=True)
    def bolt(start, direction, length, nseg, jit, w, depth=0):
        p = np.asarray(start, float); d0 = np.asarray(direction, float); d0 /= np.linalg.norm(d0)
        pts = [p.copy()]
        for k in range(nseg):
            perp = rng.normal(size=3); perp -= perp.dot(d0) * d0
            p = p + d0 * length / nseg + perp / (np.linalg.norm(perp) + 1e-9) * rng.uniform(0.3, 1) * jit
            pts.append(p.copy())
        for a_, b_ in zip(pts[:-1], pts[1:]): segment(a_, b_, w)
        if depth < 2:
            for k in rng.choice(range(1, nseg), size=min(2, nseg - 1), replace=False):
                nd = d0 + rng.normal(size=3) * 0.9
                bolt(pts[k], nd, length * 0.45, max(3, nseg // 2), jit * 0.7, w * 0.6, depth + 1)
    for i in range(au['bolts']):
        ang = 2 * math.pi * i / au['bolts'] + rng.uniform(-0.2, 0.2)
        r = au['R'] * S * rng.uniform(1.05, 1.3)
        start = np.array([math.cos(ang) * r, rng.uniform(0.85, 1.05), math.sin(ang) * r])
        bolt(start, (rng.uniform(-0.3, 0.3), -1, rng.uniform(-0.3, 0.3)), rng.uniform(0.6, 0.95), 7, 0.05, 0.0045)
    for i in range(au.get('arcs', 0)):                     # 몸을 감싸는 전기 고리
        y0 = [0.2, 0.36, 0.52, 0.66][i % 4]; rr = [0.3, 0.3, 0.32, 0.3][i % 4]
        a0 = rng.uniform(0, 2 * math.pi); span = rng.uniform(2.0, 3.2)
        pts = []
        for t in np.linspace(0, span, 14):
            q = a0 + t; rj = rr * rng.uniform(0.92, 1.1)
            pts.append(np.array([math.cos(q) * rj, y0 + rng.uniform(-0.035, 0.035), math.sin(q) * rj]))
        for a_, b_ in zip(pts[:-1], pts[1:]): segment(a_, b_, 0.0035)
    out = {}
    for name, G, D in (('Aura', AG, AD), ('Bolts', BG, BD)):
        g_, d_ = G.merged('glow', np.zeros(3)), D.merged('glow', np.zeros(3))
        if g_ is not None or d_ is not None: out[name] = {'glow': g_, 'dark': d_}
    return out

# ================= GLB 쓰기 =================
KEEP_ANIMS = ['idle', 'walk', 'sprint', 'jump', 'fall', 'crouch', 'die', 'emote-yes', 'emote-no', 'pick-up',
              'attack-melee-right', 'attack-melee-left', 'attack-kick-right', 'attack-kick-left', 'interact-right', 'sit', 'static']

def write(st, si, kg, kacc, path):
    body, decals, acc, acc_joint, sh = build(st, si)
    groups = {'toon': [], 'decal': [], 'glow': [], 'aura': [], 'auradark': []}
    groups['toon'].append(body)
    for shl in body['shells']: groups[shl['kind']].append(shl)
    for d in decals['toon']: groups['decal'].append(dict(d, J=None))
    for d in decals['glow']: groups['glow'].append(dict(d, J=None))
    for kind, item, j in acc_meshes(acc, acc_joint):
        item['joint'] = j; groups['glow' if kind == 'glow' else 'toon'].append(item)
    binbuf, views, accs = bytearray(), [], []
    def push(arr, type_, comp=5126, target=None, minmax=False):
        while len(binbuf) % 4: binbuf.append(0)
        raw = np.ascontiguousarray(arr).tobytes()
        v = {'buffer': 0, 'byteOffset': len(binbuf), 'byteLength': len(raw)}
        if target: v['target'] = target
        views.append(v); binbuf.extend(raw)
        a = {'bufferView': len(views) - 1, 'componentType': comp, 'count': int(arr.shape[0]), 'type': type_}
        if minmax: a['min'] = np.atleast_1d(arr.min(0)).astype(float).tolist(); a['max'] = np.atleast_1d(arr.max(0)).astype(float).tolist()
        accs.append(a); return len(accs) - 1
    prims, tris, check = [], 0, []
    MAT = {'toon': 0, 'decal': 1, 'glow': 2, 'aura': 4, 'auradark': 5}
    for key in ('toon', 'decal', 'glow', 'aura', 'auradark'):
        mi = MAT[key]
        L = groups[key]
        if not L: continue
        P, N, Cc, I, Jn, Wn, off = [], [], [], [], [], [], 0
        for it in L:
            n = len(it['P'])
            P.append(it['P']); N.append(it['N']); Cc.append(it['C']); I.append(it['T'] + off); off += n
            if it.get('J') is not None: Jn.append(it['J']); Wn.append(it['W'])
            else:
                jj = np.zeros((n, 4), int); jj[:, 0] = it['joint']; ww = np.zeros((n, 4)); ww[:, 0] = 1; Jn.append(jj); Wn.append(ww)
        P, N, Cc, I = np.vstack(P).astype('f4'), np.vstack(N).astype('f4'), np.vstack(Cc).astype('f4'), np.vstack(I).astype('u4')
        Jn, Wn = np.vstack(Jn).astype('u1'), np.vstack(Wn).astype('f4')
        tris += len(I); check.append((key, P, N, Cc, I, Jn, Wn))
        prims.append({'attributes': {'POSITION': push(P, 'VEC3', target=34962, minmax=True), 'NORMAL': push(N, 'VEC3', target=34962),
                                     'COLOR_0': push(Cc, 'VEC4', target=34962), 'JOINTS_0': push(Jn, 'VEC4', 5121, 34962),
                                     'WEIGHTS_0': push(Wn, 'VEC4', target=34962)},
                      'indices': push(I.reshape(-1), 'SCALAR', 5125, 34963), 'material': mi})
    # 노드: 0=Hamster, 1..7 = Kenney 뼈대 그대로, 8=메시, 9=오라
    SPk = st['species'].key if st.get('species') is not None else 'hamster'
    nodes = [{'name': SPk.capitalize(), 'children': [1, 8], 'scale': [TOP_SCALE[si]] * 3}]
    for n in kg['nodes'][1:8]:
        nn = {k: n[k] for k in n if k in ('name', 'translation', 'rotation', 'scale', 'children')}
        nodes.append(nn)
    nodes.append({'name': f'{SPk}-mesh', 'mesh': 0, 'skin': 0})
    meshes = [{'name': 'hamster', 'primitives': prims}]
    aura = build_aura(st)
    for name, prs in aura.items():
        pl = []
        for key, mat in (('glow', 2), ('dark', 3)):
            if prs[key] is None: continue
            P, N, Cc, I = prs[key]; tris += len(I)
            pl.append({'attributes': {'POSITION': push(P, 'VEC3', target=34962, minmax=True), 'NORMAL': push(N, 'VEC3', target=34962),
                       'COLOR_0': push(Cc, 'VEC4', target=34962)}, 'indices': push(I.reshape(-1), 'SCALAR', 5125, 34963), 'material': mat})
        meshes.append({'name': name.lower(), 'primitives': pl})
        nodes.append({'name': name, 'mesh': len(meshes) - 1}); nodes[0]['children'].append(len(nodes) - 1)
    sk = kg['skins'][0]
    ibm = kacc(sk['inverseBindMatrices']).astype('f4')
    sk_joints = list(sk['joints'])
    def rest_world(ni):
        p = np.zeros(3); cur = ni
        while cur is not None:
            p += np.array(kg['nodes'][cur].get('translation', [0, 0, 0]))
            par = [j for j in range(1, 8) if cur in kg['nodes'][j].get('children', [])]
            cur = par[0] if par else None
        return p
    extra_ibm = []
    for name, parent_node, pivot in st.get('extra_joints', []):
        piv = np.array(pivot, float)
        nodes.append({'name': name, 'translation': (piv - rest_world(parent_node)).tolist()})
        nodes[parent_node].setdefault('children', []).append(len(nodes) - 1)
        sk_joints.append(len(nodes) - 1)
        M = np.eye(4); M[:3, 3] = -piv; extra_ibm.append(M.T.reshape(-1))
    if extra_ibm: ibm = np.vstack([ibm, np.array(extra_ibm, 'f4')])
    skins = [{'joints': sk_joints, 'inverseBindMatrices': push(ibm, 'MAT4'), 'skeleton': 1}]
    anims = []
    for an in kg['animations']:
        if an['name'] not in KEEP_ANIMS: continue
        sm, ch = [], []
        for c in an['channels']:
            tn = c['target']['node']
            if not (1 <= tn <= 7): continue
            s = an['samplers'][c['sampler']]
            ti = kacc(s['input']).astype('f4'); to = kacc(s['output']).astype('f4')
            sm.append({'input': push(ti, 'SCALAR', minmax=True), 'output': push(to, {1: 'SCALAR', 3: 'VEC3', 4: 'VEC4'}[to.shape[1]]),
                       'interpolation': s.get('interpolation', 'LINEAR')})
            ch.append({'sampler': len(sm) - 1, 'target': {'node': tn, 'path': c['target']['path']}})
        anims.append({'name': an['name'], 'samplers': sm, 'channels': ch})
    while len(binbuf) % 4: binbuf.append(0)
    gltf = {'asset': {'version': '2.0', 'generator': 'claude-procedural hamster (rig: Kenney Mini Characters, CC0)'},
            'extensionsUsed': ['KHR_materials_unlit'], 'scene': 0, 'scenes': [{'name': st['name'], 'nodes': [0]}],
            'nodes': nodes, 'meshes': meshes, 'skins': skins, 'animations': anims,
            'materials': [
                {'name': 'Toon', 'pbrMetallicRoughness': {'baseColorFactor': [1, 1, 1, 1], 'metallicFactor': 0, 'roughnessFactor': 0.9}},
                {'name': 'Decal', 'pbrMetallicRoughness': {'baseColorFactor': [1, 1, 1, 1], 'metallicFactor': 0, 'roughnessFactor': 0.9}},
                {'name': 'Glow', 'alphaMode': 'BLEND', 'doubleSided': True, 'extensions': {'KHR_materials_unlit': {}},
                 'pbrMetallicRoughness': {'baseColorFactor': [1, 1, 1, 1], 'metallicFactor': 0, 'roughnessFactor': 1}},
                {'name': 'DarkGlow', 'alphaMode': 'BLEND', 'doubleSided': True, 'extensions': {'KHR_materials_unlit': {}},
                 'pbrMetallicRoughness': {'baseColorFactor': [1, 1, 1, 1], 'metallicFactor': 0, 'roughnessFactor': 1}},
                {'name': 'AuraGlow', 'alphaMode': 'BLEND', 'doubleSided': False, 'extensions': {'KHR_materials_unlit': {}},
                 'pbrMetallicRoughness': {'baseColorFactor': [1, 1, 1, 1], 'metallicFactor': 0, 'roughnessFactor': 1}},
                {'name': 'AuraDark', 'alphaMode': 'BLEND', 'doubleSided': False, 'extensions': {'KHR_materials_unlit': {}},
                 'pbrMetallicRoughness': {'baseColorFactor': [1, 1, 1, 1], 'metallicFactor': 0, 'roughnessFactor': 1}}],
            'accessors': accs, 'bufferViews': views, 'buffers': [{'byteLength': len(binbuf)}]}
    js = json.dumps(gltf, separators=(',', ':'), ensure_ascii=False).encode(); js += b' ' * (-len(js) % 4)
    with open(path, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(binbuf)))
        f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack('<II', len(binbuf), 0x004E4942)); f.write(binbuf)
    return tris, check, aura

# ================= 포즈 렌더 (선형 블렌드 스키닝) =================
def quat_m(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
def pose_mats(kg, kacc, anim, t):
    rot = {}; trans = {}
    for an in kg['animations']:
        if an['name'] != anim: continue
        for c in an['channels']:
            s = an['samplers'][c['sampler']]; ti = kacc(s['input'])[:, 0]; to = kacc(s['output'])
            k = int(np.clip(np.searchsorted(ti, t), 0, len(ti) - 1)); v = to[k]
            (rot if c['target']['path'] == 'rotation' else trans if c['target']['path'] == 'translation' else {})[c['target']['node']] = v
    world = {}
    def wm(i):
        if i in world: return world[i]
        n = kg['nodes'][i]; M = np.eye(4)
        M[:3, :3] = quat_m(rot[i]) if i in rot else np.eye(3)
        M[:3, 3] = trans.get(i, n.get('translation', [0, 0, 0]))
        par = [j for j in range(1, 8) if i in kg['nodes'][j].get('children', [])]
        if par: M = wm(par[0]) @ M
        world[i] = M; return M
    sk = kg['skins'][0]; ibm = kacc(sk['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
    return np.array([wm(j) @ ibm[k] for k, j in enumerate(sk['joints'])])

def render(check, aura, mats, yaw, path, size=420, zoom=1.0, show_aura=False, post=None):
    from PIL import Image
    cam = Rx(0.15) @ Ry(-yaw)
    img = np.zeros((size, size, 3)); img[:] = mh.lin('#1C2040')[None, None]; zb = np.full((size, size), -1e9)
    L = np.array([0.35, 0.75, 0.55]); L /= np.linalg.norm(L)
    def proj(W):
        Q = (W - np.array([0, 0.4, 0])) @ cam.T
        return np.stack([size / 2 + Q[:, 0] * size * zoom, size / 2 - Q[:, 1] * size * zoom, Q[:, 2]], 1), Q
    items = []
    for key, P, N, Cc, I, Jn, Wn in check:
        Mv = np.einsum('vk,vkij->vij', Wn, mats[Jn.astype(int)])
        Pw = np.einsum('vij,vj->vi', Mv[:, :3, :3], P) + Mv[:, :3, 3]
        Nw = np.einsum('vij,vj->vi', Mv[:, :3, :3], N)
        items.append((key, Pw, Nw, Cc, I))
    if show_aura:
        for prs in aura.values():
            for k2 in ('dark', 'glow'):
                if prs[k2] is not None: items.append((k2, prs[k2][0], prs[k2][1], prs[k2][2], prs[k2][3]))
    if not show_aura: items = [it for it in items if it[0] not in ('aura', 'auradark')]
    for key, Pw, Nw, Cc, I in sorted(items, key=lambda x: {'toon': 0, 'decal': 0}.get(x[0], 3 if x[0] in ('dark', 'auradark') else 2)):
        if key in ('dark', 'auradark'): key = 'darkglow'
        if key == 'aura': key = 'glow'
        S2, _ = proj(Pw); Nc = Nw @ cam.T; glow = key in ('glow', 'darkglow')
        tri = S2[I]; a, b, c = tri[:, 0], tri[:, 1], tri[:, 2]
        d = (b[:, 1] - c[:, 1]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 1] - c[:, 1])
        keep = np.abs(d) > 1e-9
        if not glow: keep &= d < 0
        for t in np.nonzero(keep)[0]:
            A_, B_, C_ = tri[t]
            x0, x1 = int(max(0, min(A_[0], B_[0], C_[0]))), int(min(size - 1, max(A_[0], B_[0], C_[0])) + 1)
            y0, y1 = int(max(0, min(A_[1], B_[1], C_[1]))), int(min(size - 1, max(A_[1], B_[1], C_[1])) + 1)
            if x1 <= x0 or y1 <= y0: continue
            xs, ys = np.meshgrid(np.arange(x0, x1) + .5, np.arange(y0, y1) + .5)
            w0 = ((B_[1] - C_[1]) * (xs - C_[0]) + (C_[0] - B_[0]) * (ys - C_[1])) / d[t]
            w1 = ((C_[1] - A_[1]) * (xs - C_[0]) + (A_[0] - C_[0]) * (ys - C_[1])) / d[t]
            w2 = 1 - w0 - w1; z = w0 * A_[2] + w1 * B_[2] + w2 * C_[2]
            m = (w0 >= 0) & (w1 >= 0) & (w2 >= 0) & (z > zb[y0:y1, x0:x1] - (0.0 if not glow else 0))
            if not m.any(): continue
            col = Cc[I[t]].mean(0)
            if key == 'darkglow': img[y0:y1, x0:x1][m] = img[y0:y1, x0:x1][m] * (1 - col[3] * 0.7) + col[:3] * col[3] * 0.7
            elif glow: img[y0:y1, x0:x1][m] += col[:3] * col[3] * 0.6
            else:
                n = Nc[I[t]].mean(0); n /= np.linalg.norm(n) + 1e-9; dd = np.dot(n, L)
                shd = 1.0 if dd > 0.2 else (0.8 if dd > -0.3 else 0.64)
                zb[y0:y1, x0:x1][m] = z[m]; img[y0:y1, x0:x1][m] = col[:3] * shd
    if post is not None: img = post(img, zb, proj)
    Image.fromarray((np.clip(img, 0, 1) ** (1 / 2.2) * 255).astype('u1')).save(path)

if __name__ == '__main__':
    kg, kacc = read_glb(sys.argv[1]); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
    only = os.environ.get('ONLY')
    for si, st in enumerate(STAGES):
        if only and st['key'] != only: continue
        p = f"{out}/hamster_{st['key']}.glb"
        tris, check, aura = write(st, si, kg, kacc, p)
        print(st['key'], 'tris', tris, 'bytes', os.path.getsize(p), flush=True)
        if len(sys.argv) > 3:
            rest = pose_mats(kg, kacc, 'static', 0); idle = pose_mats(kg, kacc, 'idle', 0.0)
            render(check, aura, idle, 0.4, f"{out}/_r_{st['key']}_a.png", zoom=1.05)
            render(check, aura, idle, 2.7, f"{out}/_r_{st['key']}_b.png", zoom=1.05)
            render(check, aura, idle, 0.3, f"{out}/_r_{st['key']}_c.png", zoom=0.8, show_aura=True)
