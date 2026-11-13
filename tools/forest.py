"""하늘 오름 숲 — 아주 큰 나무를 빙글빙글 돌아 오르는 점프 코스 + 아래 숲속 빈터.
사용법: python3 forest.py <출력폴더>
출력: forest.glb, forest_layout.js, splat.png, props_used.json

발판(jump)은 배치 파일에만 적고, 그림은 게임 안(main.js)에서 그림 (흔들리는 나뭇잎 발판 때문).
코스는 점프 높이(약 0.9m)·공중 이동(약 1.4m)·2단 점프(약 2.4m 더)로 반드시 건널 수 있게 만듦 (tools/forest_check.mjs로 확인).
"""
import sys, os, json, math
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_hamster as mh
from make_hamster import C, Ry
import village as v1
from village import box, cyl, cone, ell
import village_autumn as va
import school as sc

rng = np.random.default_rng(23)
R_WORLD, BOUND = 46, 34
TRUNK = (0.0, -6.0); TR = 2.6; TOP = 28.0          # 나무 위치·굵기, 정상 발판 높이
BARK, BARK_D, BARK_L = C('#6E4A30'), C('#4E3220'), C('#8A6242')
LEAF, LEAF_D, LEAF_L = C('#5E9A48'), C('#457A36'), C('#86BE5E')
WOOD, WOOD_D = C('#9A6A40'), C('#6A4428')
PATHS = [((0, 24), (0, 8)), ((0, 8), (0, -2.5)), ((-3, 10), (-12, 12)), ((3, 10), (12, 8))]
props, blockers, lights, spots, plats = [], [], [], {}, []
sc.props, sc.blockers, sc.lights, sc.spots = props, blockers, lights, spots   # school 도우미 함수를 이 목록에 쓰게


def height(x, z):
    r = math.hypot(x, z); h = 0.0
    if r > 28: h += min(5.0, (r - 28) * 0.35) * (0.7 + 0.3 * math.sin(x * 0.21) * math.cos(z * 0.16))
    h += 0.12 * math.sin(x * 0.4) * math.cos(z * 0.33)
    return h
sc.height = height


def blk(cx, cz, hx, hz, r=0.0): blockers.append(dict(c=[round(cx, 3), round(cz, 3)], h=[round(hx, 3), round(hz, 3)], r=round(r, 4)))
def spot(kind, x, z, fx, fz): spots.setdefault(kind, []).append([round(x, 3), round(z, 3), round(math.atan2(fx - x, fz - z), 4)])


# ------------------------------------------------------------------ 큰 나무
def giant_tree(P, L):
    x0, z0 = TRUNK
    n = 34
    for i in range(n):   # 줄기: 아래가 넓고 위로 갈수록 가늘게, 살짝 비틀림
        y = i * (TOP + 6) / n; r = TR * (1.0 + 0.55 * max(0, 1 - y / 3) ** 2) * (1 - 0.18 * y / TOP)
        col = BARK if i % 3 else BARK_D
        cyl(P, (x0, y, z0), r, (TOP + 6) / n + 0.05, col)
    for k in range(9):   # 뿌리
        a = k * 2 * math.pi / 9 + 0.2
        for j in range(4):
            t = j / 3; rr = TR + 0.4 + t * 2.4; yy = 0.9 * (1 - t)
            ell(P, (x0 + math.cos(a) * rr, yy - 0.1, z0 + math.sin(a) * rr), (0.75 - 0.15 * j, 0.5 - 0.08 * j, 0.75 - 0.15 * j), BARK_D if j % 2 else BARK)
    for k in range(40):  # 나무껍질 무늬
        a = rng.random() * 2 * math.pi; y = rng.random() * TOP
        r = TR * (1 - 0.18 * y / TOP) + 0.02
        box(P, (x0 + math.cos(a) * r, y, z0 + math.sin(a) * r), (0.06, 0.5 + rng.random() * 0.8, 0.22), BARK_L, ry=-a)
    # 위쪽 잎 덩어리 (정상보다 높이 — 코스를 가리지 않게)
    for k in range(14):
        a = k * 2 * math.pi / 14 + rng.random() * 0.3; r = 2.0 + rng.random() * 6.5; y = TOP + 5 + rng.random() * 5
        ell(L, (x0 + math.cos(a) * r, y, z0 + math.sin(a) * r), (2.6 + rng.random(), 1.6 + rng.random() * 0.6, 2.6 + rng.random()), [LEAF, LEAF_D, LEAF_L][k % 3], sub=2)
    ell(L, (x0, TOP + 9.5, z0), (5.0, 2.4, 5.0), LEAF, sub=2)
    # 큰 가지 (위쪽)
    for k in range(6):
        a = k * 2 * math.pi / 6 + 0.4
        for j in range(5):
            t = j / 4; r = TR * 0.8 + t * 6.5
            ell(P, (x0 + math.cos(a) * r, TOP + 3.0 + t * 2.4, z0 + math.sin(a) * r), (0.55 - 0.08 * j, 0.45 - 0.06 * j, 0.55 - 0.08 * j), BARK)
    blk(x0, z0, TR * 1.05, TR * 1.05)   # 줄기는 둥글지만 네모 막힘으로 충분 (발판은 줄기 바깥 4m 이상)
    for k in range(9):
        a = k * 2 * math.pi / 9 + 0.2; blk(x0 + math.cos(a) * (TR + 1.4), z0 + math.sin(a) * (TR + 1.4), 0.5, 0.5)


def tree_house(P, cx, cz, y):
    """정상 발판 위의 작은 나무집 (줄기 뒤쪽)"""
    x, z = cx, cz - 2.2
    box(P, (x, y + 1.1, z), (1.3, 1.1, 0.9), C('#C89A62'))
    sc.prism_roof(P, x, z, 1.5, 1.1, y + 2.2, 1.0, C('#7A4A30'), along='x')
    box(P, (x, y + 0.85, z + 0.92), (0.35, 0.65, 0.02), WOOD_D)
    box(P, (x - 0.8, y + 1.3, z + 0.92), (0.25, 0.22, 0.02), C('#FFE2A0'), glow=True); box(P, (x + 0.8, y + 1.3, z + 0.92), (0.25, 0.22, 0.02), C('#FFE2A0'), glow=True)
    lights.append([round(x, 3), round(y + 1.6, 3), round(z + 1.4, 3), 0.8])


def lantern(P, x, z, y=None):
    y = height(x, z) if y is None else y
    cyl(P, (x, y, z), 0.06, 1.7, WOOD_D, n=8); box(P, (x, y + 1.85, z), (0.14, 0.17, 0.14), C('#FFD890'), glow=True)
    lights.append([round(x, 3), round(y + 1.85, 3), round(z, 3), 0.7]); blk(x, z, 0.12, 0.12)


def sign(P, x, z, ry):
    y = height(x, z); cyl(P, (x, y, z), 0.06, 1.2, WOOD_D, n=8); box(P, (x, y + 1.25, z), (0.55, 0.22, 0.04), WOOD, ry=ry); blk(x, z, 0.12, 0.12)


# ------------------------------------------------------------------ 점프 코스
JUMP_H, AIR, DASH = 0.92, 1.4, 2.3     # 점프 높이 · 한 번 점프로 갈 수 있는 거리(오르면서) · 2단 점프로 더 가는 거리


def course():
    """나무를 시계 반대 방향으로 돌며 오르는 발판 목록 (윗면 가운데 x,y,z)"""
    x0, z0 = TRUNK; J = []
    th = math.pi / 2 + 0.25   # 남쪽(입구 쪽)에서 시작
    y = 0.0
    def add(t, rho, y, size, **k):
        x, z = x0 + math.cos(th) * rho, z0 + math.sin(th) * rho
        d = dict(t=t, x=round(x, 3), y=round(y, 3), z=round(z, 3), r=round(size, 3), a=round(th, 4)); d.update(k); J.append(d); return d
    # 출발: 땅 위 그루터기 계단
    prev_r, prev_rho = 0.7, 4.6
    add('stump', prev_rho, 0.45, prev_r)
    y = 0.45; dbl_every = 0; n = 0
    rest_at = [9.0, 18.5]
    while y < TOP - 0.62:
        n += 1
        sect = 0 if y < 9 else 1 if y < 18.5 else 2
        if rest_at and y >= rest_at[0] - 0.6:
            # 쉼터: 넓은 나무 덱 (줄기에 붙음)
            rho = TR + 2.0; size = 1.7; gap = 0.8; dy = 0.45
            th += (prev_r + gap + size) / ((rho + prev_rho) / 2); y += dy
            add('rest', rho, y, size, n=len(J)); prev_r, prev_rho = size, rho; rest_at.pop(0); continue
        rho = [TR + 1.25, TR + 2.2, TR + 3.0][sect] + rng.uniform(-0.25, 0.35)
        size = [0.95, 0.85, 0.72][sect] * rng.uniform(0.9, 1.1)
        dbl_every += 1
        dbl = sect >= 1 and dbl_every >= (5 if sect == 1 else 4) and rng.random() < 0.7
        if dbl:   # 2단 점프로 건너는 넓은 틈 (높이는 거의 그대로)
            dbl_every = 0; gap = rng.uniform(1.9, 2.4) + (0.15 if sect == 2 else 0); dy = rng.uniform(-0.1, 0.2)   # 게임 안 2단 점프(방향키를 누른 채 꼭대기에서)는 가장자리에서 약 3.5m
        else:
            gap = rng.uniform(0.45, 0.95) + 0.1 * sect; dy = rng.uniform(0.38, 0.62) if sect < 2 else rng.uniform(0.28, 0.44)
        th += (prev_r + gap + size) / ((rho + prev_rho) / 2); y += dy
        kind = ['fungus', 'branch', 'leaf'][sect]
        extra = {}
        if kind == 'branch': extra = dict(len=round(size * 2.2, 3), w=round(size * 0.9, 3))
        if kind == 'leaf': extra = dict(bob=round(rng.uniform(0.12, 0.22), 3), ph=round(rng.uniform(0, 6.28), 3), sp=round(rng.uniform(0.6, 1.0), 3))
        add(kind, rho, y, size, dbl=bool(dbl), **extra); prev_r, prev_rho = size, rho
    # 정상: 줄기를 둘러싼 둥근 덱
    J.append(dict(t='goal', x=x0, y=round(TOP, 3), z=z0, r=TR + 3.4, a=0.0))
    # 마지막 발판에서 정상 덱까지 이어지게 (정상 덱 가장자리 = 줄기에서 6m)
    last = J[-2]; dist = math.hypot(last['x'] - x0, last['z'] - z0) - last['r'] - (TR + 3.4)
    assert dist < AIR and TOP - last['y'] < JUMP_H - 0.25, ('정상까지 너무 멂', dist, TOP - last['y'])
    return J


def check(J):
    """이웃한 발판끼리 건널 수 있는지 (가장자리 사이 거리·높이 차)"""
    bad = []
    for a, b in zip(J[:-2], J[1:-1]):
        d = math.hypot(b['x'] - a['x'], b['z'] - a['z']) - a['r'] - b['r']; dy = b['y'] - a['y']
        lim = (AIR + DASH - 0.3) if b.get('dbl') else (AIR - 0.25)
        if b['t'] == 'leaf': dy += b['bob']   # 흔들리는 잎: 가장 높이 올라간 때를 기준으로
        if d > lim or dy > JUMP_H - 0.25 + (0.5 if b.get('dbl') else 0): bad.append((J.index(b), round(d, 2), round(dy, 2)))
    return bad


# ------------------------------------------------------------------ 아래 빈터
OCC = [(0, -6, 7.5, 7.5), (0, 10, 6, 6)]
def free(x, z, pad):
    if math.hypot(x, z) > BOUND - 1: return False
    for cx, cz, hx, hz in OCC:
        if abs(x - cx) < hx + pad and abs(z - cz) < hz + pad: return False
    if min(va.seg_dist(np.array([x]), np.array([z]), p, q)[0] for p, q in PATHS) < 1.4 + pad: return False
    return True


def clearing(P):
    homes = {}
    keys = ['hamster', 'rabbit', 'cat', 'dog', 'lion', 'bear', 'panda', 'fox', 'raccoon', 'squirrel', 'deer']
    # 빈터 둘레 그루터기 의자
    for i, k in enumerate(keys):
        a = math.pi * (0.15 + 0.7 * i / (len(keys) - 1)) + math.pi; r = 7.2
        x, z = math.cos(a) * r * 1.25, 10 + math.sin(a) * -r * 0.75
        y = height(x, z); cyl(P, (x, y, z), 0.42, 0.42, BARK); cyl(P, (x, y + 0.42, z), 0.4, 0.03, C('#D8B484'))
        blk(x, z, 0.4, 0.4); spot('forest_stump', x, z + 0.0, 0, 10)
        homes[k] = [x + (0 - x) * 0.12, 0.0, z + (10 - z) * 0.12]
    # 모닥불 자리 + 돌 둘레
    for k in range(10): a = k * 2 * math.pi / 10; ell(P, (math.cos(a) * 1.1, 0.08, 10 + math.sin(a) * 1.1), (0.28, 0.18, 0.22), C('#8A8478'))
    sc.place('Bonfire_Lit', 0, 10, 1.0, block=(0.9, 0.9)); lights.append([0.0, 0.8, 10.0, 1.2])
    for x, z in ((-2.2, 19), (2.2, 19), (-2.2, 14.5), (2.2, 14.5), (-4.5, 4.0), (4.5, 4.0), (-9, 12.5), (9, 9)): lantern(P, x, z)
    sign(P, 1.6, 2.2, 0.0)
    return homes


def scatter():
    GREEN = ['PineTree_1', 'PineTree_2', 'PineTree_3']
    n = t = 0
    while n < 210 and t < 9000:
        t += 1; a = rng.random() * 6.283; r = 12 + rng.random() * 32; x, z = math.cos(a) * r, math.sin(a) * r
        if not free(x, z, 2.6): continue
        sc.place(GREEN[int(rng.integers(0, len(GREEN)))], x, z, 1.5 + rng.random() * 1.0, block=(0.3, 0.3) if r < BOUND else None); n += 1
    for k in range(150):
        x, z = (rng.random() - 0.5) * 70, (rng.random() - 0.5) * 70
        if not free(x, z, 0.3): continue
        q = rng.random()
        if q < 0.25: sc.place(f'Rock_Moss_{1 + k % 7}', x, z, 1.0 + rng.random(), block=(0.3, 0.3))
        elif q < 0.42: sc.place(['Bush_1', 'Bush_2', 'BushBerries_2'][k % 3], x, z, 1.0, block=(0.45, 0.45))
        elif q < 0.5: sc.place(['TreeStump_Moss', 'WoodLog_Moss'][k % 2], x, z, 1.0, block=(0.5, 0.5))
        else:
            for j in range(3): sc.place(['Flowers', 'Plant_1', 'Plant_2', 'Plant_3', 'Grass'][(k + j) % 5], x + rng.random(), z + rng.random(), 1.0 + rng.random() * 0.5)
    for k in range(380):
        x, z = (rng.random() - 0.5) * 70, (rng.random() - 0.5) * 70
        if free(x, z, -0.6): sc.place(['Grass_Short', 'Grass', 'Grass_2', 'Flowers'][k % 4], x, z, 1.0 + rng.random() * 0.6)


def splat(n=512):
    xs = np.linspace(-R_WORLD, R_WORLD, n); X, Z = np.meshgrid(xs, xs)
    d = np.min([va.seg_dist(X.ravel(), Z.ravel(), p, q) for p, q in PATHS], axis=0).reshape(n, n)
    noise = (np.sin(X * 1.7) * np.cos(Z * 1.3) + np.sin(X * 0.53 + Z * 0.71)) * 0.25
    R = np.clip((1.2 + noise * 0.5 - d) / 0.5, 0, 1)
    R = np.maximum(R, np.clip((3.4 - np.hypot(X, Z - 10)) / 0.5, 0, 1))           # 모닥불 빈터 흙
    R = np.maximum(R, np.clip((TR + 3.4 - np.hypot(X - TRUNK[0], Z - TRUNK[1])) / 0.8, 0, 1) * 0.9)   # 나무 밑동 둘레
    G = np.zeros_like(R)
    B = np.zeros_like(R)
    return Image.fromarray((np.stack([R, G, B, np.ones_like(R)], -1) * 255).astype(np.uint8), 'RGBA')


def build_all():
    P, L = mh.Part(), mh.Part()
    giant_tree(P, L)
    J = course(); bad = check(J); assert not bad, ('건너기 어려운 발판', bad)
    tree_house(P, TRUNK[0], TRUNK[1], TOP)
    homes = clearing(P); scatter()
    spot('forest_view', TRUNK[0], TRUNK[1] + TR + 2.6, TRUNK[0], TRUNK[1] + 30)    # 정상에서 경치 보기 (높이는 발판으로 정해짐)
    spot('forest_view', TRUNK[0] + TR + 2.6, TRUNK[1], TRUNK[0] + 30, TRUNK[1])
    n = 241; xs = np.linspace(-R_WORLD, R_WORLD, n)
    layout = {
        'buildings': {'tree': dict(name='큰 나무', position=[TRUNK[0], 0, TRUNK[1]], rotationY=0, door=[J[0]['x'], 0.0, J[0]['z'] + 1.2]),
                      'camp': dict(name='모닥불 빈터', position=[0, 0, 10], rotationY=0, door=[0.0, 0.0, 12.6]),
                      'gate': dict(name='숲 입구', position=[0, 0, 20], rotationY=0, door=[0.0, 0.0, 20.0])},
        'zones': {'canopy': dict(center=[TRUNK[0], TOP, TRUNK[1]], radius=8.0, name='하늘 정원', ymin=TOP - 1.0)},
        'spawn': {'plaza': [0.0, 0.0, 20.0]}, 'homes': homes, 'platforms': plats, 'blockers': blockers, 'interiors': [],
        'actions': spots, 'bound': BOUND, 'props': props, 'lights': lights, 'jump': J, 'top': TOP,
        'heightmap': dict(size=R_WORLD * 2, n=n, h=[round(height(x, z), 2) for z in xs for x in xs]),
    }
    groups = [('forest', P, (0, 0, 0), 0.0), ('canopy', L, (0, 0, 0), 0.0)]
    return groups, layout


if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    groups, layout = build_all()
    data, tris = sc.glb_small(groups); open(os.path.join(out, 'forest.glb'), 'wb').write(data)
    splat().save(os.path.join(out, 'splat.png'), optimize=True)
    with open(os.path.join(out, 'forest_layout.js'), 'w') as f:
        f.write('// 하늘 오름 숲 배치: 큰 나무·빈터·점프 발판(jump)·행동 자리·높이맵·막힌 곳·소품·등불\n')
        f.write('export default ' + json.dumps(layout, ensure_ascii=False, separators=(',', ':')) + ';\n')
    J = layout['jump']
    print('tris', tris, 'bytes', len(data), 'props', len(props), 'lights', len(lights), 'jump', len(J), 'dbl', sum(1 for j in J if j.get('dbl')), 'rest', sum(1 for j in J if j['t'] == 'rest'), 'last', J[-2]['y'])
