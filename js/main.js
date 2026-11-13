// 단풍마을 산책 — three.js
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import * as SkeletonUtils from 'three/addons/utils/SkeletonUtils.js';
import LAYOUT from '../assets/village/village_layout.js';
import { createAudio, HEART_SUTRA } from './audio.js';
import { createNav } from './nav.js';

// ---------------------------------------------------------------- 동물
const ANIMALS = [
  { k: 'hamster', n: '햄스터', u: 3.017, job: '프로그래머' },
  { k: 'rabbit', n: '토끼', u: 3.069, job: '제빵사' },
  { k: 'cat', n: '고양이', u: 2.756, job: '바리스타' },
  { k: 'dog', n: '강아지', u: 3.058, job: '우체부' },
  { k: 'bear', n: '곰', u: 3.044, job: '니트 스웨터' },
  { k: 'panda', n: '판다', u: 3.047, job: '초록 셔츠' },
  { k: 'fox', n: '여우', u: 2.721, job: '와인색 코트' },
  { k: 'raccoon', n: '너구리', u: 2.964, job: '푸른 셔츠' },
  { k: 'squirrel', n: '다람쥐', u: 3.113, job: '단풍색 셔츠' },
  { k: 'deer', n: '사슴', u: 2.866, job: '크림 니트' },
  { k: 'lion', n: '사자', u: 2.84, job: '마을 경비대장' },
];
const CH_SCALE = 1.25;
const WALK = 1.6, RUN = 2.7;

// ---------------------------------------------------------------- 파일
async function bin(path) {
  if (window.ASSET_JS) { const m = await import(window.ASSET_JS(path)); const t = atob(m.default), u = new Uint8Array(t.length); for (let i = 0; i < t.length; i++) u[i] = t.charCodeAt(i); return u.buffer; }
  const r = await fetch(path); if (!r.ok) throw new Error(path + ' ' + r.status); return r.arrayBuffer();
}
const asset = p => (window.ASSET_URL ? window.ASSET_URL(p) : p);
const loader = new GLTFLoader();
const parse = buf => new Promise((res, rej) => loader.parse(buf, '', res, rej));

// ---------------------------------------------------------------- 장면
const canvas = document.getElementById('view');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
const LOWEND = Math.min(screen.width, screen.height) < 500;
renderer.setPixelRatio(Math.min(devicePixelRatio || 1, LOWEND ? 1.5 : 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.0;
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xF6DCC0);
scene.fog = new THREE.Fog(0xF4D8BC, 40, 150);
const cam = new THREE.PerspectiveCamera(42, 1, 0.1, 500);
const hemi = new THREE.HemisphereLight(0xFFF1DD, 0x8E7050, 1.35); scene.add(hemi);
const sun = new THREE.DirectionalLight(0xFFDDB0, 2.1); sun.position.set(-30, 42, 24); scene.add(sun); scene.add(sun.target);
sun.castShadow = true; sun.shadow.mapSize.set(LOWEND ? 1024 : 2048, LOWEND ? 1024 : 2048);
Object.assign(sun.shadow.camera, { left: -24, right: 24, top: 24, bottom: -24, near: 1, far: 140 }); sun.shadow.bias = -0.0006; sun.shadow.normalBias = 0.03;
const fill = new THREE.DirectionalLight(0xB8C8FF, 0.45); fill.position.set(25, 18, -30); scene.add(fill);
// 가까운 등불 몇 개만 진짜 빛으로 (나머지는 빛나는 모양 + 번짐)
const LAMPS = Array.from({ length: LOWEND ? 4 : 8 }, () => { const l = new THREE.PointLight(0xFFA650, 0, 10, 1.4); scene.add(l); return l; });
const skyTex = {}; const texL = new THREE.TextureLoader();
function skyLoad(k, p) { texL.load(asset(p), t => { t.mapping = THREE.EquirectangularReflectionMapping; t.colorSpace = THREE.SRGBColorSpace; skyTex[k] = t; if (TIME[TIME.cur].sky === k && started) applyTime(TIME.cur); }); }
{ // 노을 하늘 (그라데이션 + 별 몇 개)
  const c = document.createElement('canvas'); c.width = 1024; c.height = 512; const x = c.getContext('2d');
  const gr = x.createLinearGradient(0, 0, 0, 512);
  [[0, '#2B2C58'], [0.28, '#5B4272'], [0.42, '#B4617A'], [0.49, '#F09A6A'], [0.53, '#F7C58A'], [0.6, '#C07A6A'], [1, '#4A3448']].forEach(([o, col]) => gr.addColorStop(o, col));
  x.fillStyle = gr; x.fillRect(0, 0, 1024, 512);
  x.fillStyle = 'rgba(255,240,220,0.8)'; for (let i = 0; i < 90; i++) { const yy = Math.random() * 130; x.globalAlpha = 0.3 + Math.random() * 0.6 * (1 - yy / 130); x.fillRect(Math.random() * 1024, yy, 1.4, 1.4); }
  x.globalAlpha = 1; const t = new THREE.CanvasTexture(c); t.mapping = THREE.EquirectangularReflectionMapping; t.colorSpace = THREE.SRGBColorSpace; skyTex.dusk = t;
}
skyLoad('day', 'assets/sky.jpg'); skyLoad('night', 'assets/sky_night.jpg');
const grad = new THREE.DataTexture(new Uint8Array([110, 110, 110, 255, 190, 190, 190, 255, 255, 255, 255, 255]), 3, 1, THREE.RGBAFormat);
grad.minFilter = grad.magFilter = THREE.NearestFilter; grad.needsUpdate = true;
const outlineMat = new THREE.MeshBasicMaterial({ color: 0x2A1A14, side: THREE.BackSide });
outlineMat.onBeforeCompile = s => { s.vertexShader = s.vertexShader.replace('#include <skinning_vertex>', '#include <skinning_vertex>\ntransformed += normalize(objectNormal) * 0.018;'); };
// 빛 번짐 (UnrealBloom)
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, cam));
const bloom = new UnrealBloomPass(new THREE.Vector2(256, 256), 0.6, 0.55, 0.85); composer.addPass(bloom);
composer.addPass(new OutputPass());
function resize() { const w = innerWidth, h = innerHeight; renderer.setSize(w, h, false); composer.setSize(w, h); cam.aspect = w / h; cam.updateProjectionMatrix(); }
addEventListener('resize', resize); resize();

// 낮 · 노을 · 밤
const glowMats = [];   // 등불·연등·창 (밤에 더 밝게)
const TIME = {
  cur: 'dusk',
  day: { sky: 'day', fog: 0xF4D8BC, fogN: 45, fogF: 160, hemi: [0xFFF1DD, 0x8E7050, 1.3], sun: [0xFFE2B8, 2.2], pos: [-30, 42, 24], fill: 0.45, lamp: 0, glow: 1.0, bloom: 0.25, exp: 1.0 },
  dusk: { sky: 'dusk', tint: 0xFFB27A, fog: 0xD99A78, fogN: 30, fogF: 130, hemi: [0xFFD2B0, 0x6A4A50, 1.15], sun: [0xFFA060, 1.9], pos: [-44, 18, 10], fill: 0.45, lamp: 1.8, glow: 1.25, bloom: 0.5, exp: 1.05 },
  night: { sky: 'night', fog: 0x1C2440, fogN: 22, fogF: 110, hemi: [0x5468A8, 0x1A1424, 0.55], sun: [0x9CB4FF, 0.55], pos: [30, 40, -20], fill: 0.12, lamp: 3.2, glow: 1.25, bloom: 0.8, exp: 1.05 },
};
function applyTime(k) {
  TIME.cur = k; const T = TIME[k];
  const sky = skyTex[T.sky]; scene.background = sky || new THREE.Color(T.fog);
  scene.fog.color.set(T.fog); scene.fog.near = T.fogN; scene.fog.far = T.fogF;
  hemi.color.set(T.hemi[0]); hemi.groundColor.set(T.hemi[1]); hemi.intensity = T.hemi[2];
  sun.color.set(T.sun[0]); sun.intensity = T.sun[1]; sun.userData.off = T.pos; fill.intensity = T.fill;
  glowMats.forEach(m => m.color.setScalar(T.glow)); bloom.strength = T.bloom; renderer.toneMappingExposure = T.exp;
  TIME.lamp = T.lamp; if (mountains) mountains.material.color.set(k === 'night' ? 0x2A3350 : k === 'dusk' ? 0x8A5A5E : 0x9AA8A0);
  const b = document.getElementById('btnTime'); if (b) b.textContent = { day: '☀️ 낮', dusk: '🌇 노을', night: '🌙 밤' }[k];
}
sun.userData.off = TIME.dusk.pos;

// 먼 산 (안개 속으로 겹겹이)
let mountains = null;
{
  const g = new THREE.BufferGeometry(), P = [], I = [], seg = 160, rows = 3;
  for (let r = 0; r <= rows; r++) for (let i = 0; i <= seg; i++) {
    const a = i / seg * Math.PI * 2, R = 95 + r * 6;
    const h = r === rows ? -6 : r === 0 ? -4 : (14 + 10 * Math.sin(a * 3 + 1) + 7 * Math.sin(a * 7.3) + 4 * Math.sin(a * 17.1 + 2)) * (r === 1 ? 1 : 0.85) + (r === 2 ? 8 : 0);
    P.push(Math.cos(a) * R, h, Math.sin(a) * R);
  }
  for (let r = 0; r < rows; r++) for (let i = 0; i < seg; i++) { const a = r * (seg + 1) + i, b = a + seg + 1; I.push(a, b, a + 1, a + 1, b, b + 1); }
  g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3)); g.setIndex(I); g.computeVertexNormals();
  mountains = new THREE.Mesh(g, new THREE.MeshLambertMaterial({ color: 0x8A5A5E, side: THREE.DoubleSide, flatShading: true })); scene.add(mountains);
}

// ---------------------------------------------------------------- 땅·막힘·길찾기
const HM = LAYOUT.heightmap;
function terrainH(x, z) {
  const n = HM.n, s = HM.size, fx = (x / s + 0.5) * (n - 1), fz = (z / s + 0.5) * (n - 1);
  const i = Math.max(0, Math.min(n - 2, Math.floor(fx))), j = Math.max(0, Math.min(n - 2, Math.floor(fz))), u = fx - i, v = fz - j;
  const h = (a, b) => HM.h[b * n + a];
  return (h(i, j) * (1 - u) + h(i + 1, j) * u) * (1 - v) + (h(i, j + 1) * (1 - u) + h(i + 1, j + 1) * u) * v;
}
function local(b, x, z) { const dx = x - b.c[0], dz = z - b.c[1], c = Math.cos(b.r), s = Math.sin(b.r); return [dx * c - dz * s, dx * s + dz * c]; }
function groundH(x, z) {
  let y = terrainH(x, z);
  for (const p of LAYOUT.platforms) {
    const [lx, lz] = local(p, x, z);
    if (Math.abs(lx) <= p.h[0] && Math.abs(lz) <= p.h[1]) { const t = (p.h[1] - lz) / (2 * p.h[1]); y = Math.max(y, p.y0 + (p.y1 - p.y0) * t); }
  }
  return y;
}
const RAD = 0.3;
// 막힌 곳(건물 벽·나무·바위·등불·소품)을 4m 칸에 나눠 두고 가까운 것만 검사
const BK = 4, BN = Math.ceil(LAYOUT.bound * 2 / BK) + 2, BUCKET = Array.from({ length: BN * BN }, () => []);
const bIdx = (x, z) => { const i = Math.floor((x + LAYOUT.bound) / BK) + 1, j = Math.floor((z + LAYOUT.bound) / BK) + 1; return i < 0 || j < 0 || i >= BN || j >= BN ? -1 : j * BN + i; };
for (const b of LAYOUT.blockers) {
  const e = Math.hypot(b.h[0], b.h[1]) + 0.8;
  for (let x = b.c[0] - e; x <= b.c[0] + e + BK; x += BK) for (let z = b.c[1] - e; z <= b.c[1] + e + BK; z += BK) {
    const k = bIdx(Math.min(x, b.c[0] + e), Math.min(z, b.c[1] + e)); if (k >= 0 && !BUCKET[k].includes(b)) BUCKET[k].push(b);
  }
}
function blockedR(x, z, rad) {
  if (Math.hypot(x, z) > LAYOUT.bound) return true;
  const k = bIdx(x, z); if (k < 0) return true;
  for (const b of BUCKET[k]) { const [lx, lz] = local(b, x, z); if (Math.abs(lx) < b.h[0] + rad && Math.abs(lz) < b.h[1] + rad) return true; }
  return false;
}
const blocked = (x, z) => blockedR(x, z, RAD);
const nav = createNav(LAYOUT.bound, 0.4, (x, z) => blockedR(x, z, RAD + 0.05), blocked);
function insideRect(r, x, z, m = 0) { const [lx, lz] = local(r, x, z); return Math.abs(lx) < r.h[0] + m && Math.abs(lz) < r.h[1] + m; }

// ---------------------------------------------------------------- 장소·행동 자리
const BLD = LAYOUT.buildings, Z = LAYOUT.zones, ACT = LAYOUT.actions;
const POI = {
  temple: { p: [BLD.temple.door[0], BLD.temple.door[2]], name: '단풍사 (절)' },
  church: { p: [BLD.church.door[0], BLD.church.door[2]], name: '은행나무 교회' },
  cathedral: { p: [BLD.cathedral.door[0], BLD.cathedral.door[2]], name: '별빛 성당' },
  plaza: { p: [0, 4.6], name: '단풍 광장' },
  pond: { p: [-4.0, 11.6], name: '연못' },
};
const ACTION_INFO = {
  temple_bow: { label: '절하기', enter: 'Sit_Floor_Down', loop: 'Bow', exit: 'Sit_Floor_StandUp', msg: '부처님께 천천히 절을 올려요.' },
  temple_incense: { label: '향 피우기', enter: 'Interact', loop: 'Pray_Stand', exit: null, msg: '향 연기가 피어올라요.' },
  church_pew: { label: '앉아서 기도하기', enter: 'Sit_Chair_Down', loop: 'Pray_Sit', exit: 'Sit_Chair_StandUp', msg: '두 손을 모아 기도해요.' },
  cathedral_pew: { label: '앉아서 기도하기', enter: 'Sit_Chair_Down', loop: 'Pray_Sit', exit: 'Sit_Chair_StandUp', msg: '두 손을 모아 기도해요.' },
  cathedral_candle: { label: '촛불 켜기', enter: 'Interact', loop: 'Pray_Stand', exit: null, msg: '작은 초에 불을 밝혔어요.' },
};
const SPOTS = [];
for (const [kind, list] of Object.entries(ACT)) for (const [x, z, yaw] of list) SPOTS.push({ kind, x, z, yaw, taken: null });
const OUT = {
  church: [[BLD.church.door[0] + 1.2, BLD.church.door[2] - 1.5], [BLD.church.door[0] + 1.8, BLD.church.door[2] + 1.6]],
  cathedral: [[BLD.cathedral.door[0] - 1.2, BLD.cathedral.door[2] - 2.0], [BLD.cathedral.door[0] - 1.8, BLD.cathedral.door[2] + 2.2]],
  temple: [[BLD.temple.door[0] - 1.5, BLD.temple.door[2] + 1.0], [-4.5, -26.5], [-0.5, -27.5]],
  plaza: [[2.6, 2.4], [-2.4, 2.6], [2.2, -2.6], [-2.8, -2.0], [0, -3.4]],
  pond: [[-4.4, 11.2], [-5.2, 15.4], [-10.6, 13.6]],
  walk: [[0, -9], [-9, 1.6], [10, 2.6], [0, 10], [-5, 6], [6, 7], [3, -6], [-3, -6], [-12, 5], [12, 6]],
};

// ---------------------------------------------------------------- 캐릭터
let ANIMS = [];
function prepModel(g) {
  const root = SkeletonUtils.clone(g.scene), outlines = [];   // 처음으로 돌아가 다시 시작해도 되게 매번 복제
  root.traverse(o => {
    if (!o.isMesh) return; o.frustumCulled = false;
    const nm = o.material.name;
    if (nm === 'Decal') { o.material = new THREE.MeshToonMaterial({ vertexColors: true, gradientMap: grad, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }); o.renderOrder = 1; }
    else if (nm === 'Glow') o.material = new THREE.MeshBasicMaterial({ vertexColors: true, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false });
    else if (nm === 'DarkGlow' || nm === 'AuraGlow' || nm === 'AuraDark') o.visible = false;
    else { o.material = new THREE.MeshToonMaterial({ vertexColors: true, gradientMap: grad }); if (o.isSkinnedMesh) outlines.push(o); }
  });
  outlines.forEach(o => { const ol = new THREE.SkinnedMesh(o.geometry, outlineMat); ol.frustumCulled = false; ol.bind(o.skeleton, o.bindMatrix); o.parent.add(ol); });
  const b = root.getObjectByName('Bolts'); if (b) b.visible = false;
  return { root, clips: g.animations };
}
const ONCE = ['Sit_Floor_Down', 'Sit_Floor_StandUp', 'Sit_Chair_Down', 'Sit_Chair_StandUp', 'Cheer', 'Interact', 'PickUp'];
class Actor {
  constructor(def, model) {
    this.def = def; this.root = model.root; this.root.scale.setScalar(CH_SCALE / def.u);
    const own = new Set(model.clips.map(c => c.name));
    const clips = model.clips.concat(ANIMS.filter(c => !own.has(c.name)));
    this.mixer = new THREE.AnimationMixer(this.root); this.acts = {};
    clips.forEach(c => { this.acts[c.name] = this.mixer.clipAction(c); });
    for (const n of ONCE) if (this.acts[n]) { this.acts[n].setLoop(THREE.LoopOnce, 1); this.acts[n].clampWhenFinished = true; }
    if (this.acts['trait-idle']) this.acts['trait-idle'].play();
    this.pos = new THREE.Vector3(); this.yaw = 0; this.cur = null; this.path = null; this.pi = 0; this.stuck = 0;
    this.mixer.addEventListener('finished', () => { if (this.onFinish) { const f = this.onFinish; this.onFinish = null; f(); } });
    scene.add(this.root); this.play('Idle');
  }
  play(n, fade = 0.25) {
    const a = this.acts[n]; if (!a || this.cur === a) return;
    a.reset().setEffectiveTimeScale(1).setEffectiveWeight(1).fadeIn(fade).play();
    if (this.cur) this.cur.fadeOut(fade);
    this.cur = a; this.curName = n;
  }
  place(x, z, yaw) { this.pos.set(x, groundH(x, z), z); if (yaw !== undefined) this.yaw = yaw; this.sync(); }
  sync() { this.root.position.copy(this.pos); this.root.rotation.y = this.yaw; }
  turnTo(yaw, dt, k = 8) { let d = yaw - this.yaw; d = Math.atan2(Math.sin(d), Math.cos(d)); this.yaw += d * Math.min(1, dt * k); }
  step(dx, dz, sp, dt) {
    const nx = this.pos.x + dx * sp * dt, nz = this.pos.z + dz * sp * dt;
    if (!blocked(nx, nz)) { this.pos.x = nx; this.pos.z = nz; return true; }
    if (blocked(this.pos.x, this.pos.z) && Math.hypot(this.pos.x, this.pos.z) < LAYOUT.bound) { this.pos.x = nx; this.pos.z = nz; return true; }   // 이미 막힌 곳 안(의자·방석에서 일어난 직후 등)이면 걸어 나올 수 있게
    if (!blocked(nx, this.pos.z)) { this.pos.x = nx; return true; }
    if (!blocked(this.pos.x, nz)) { this.pos.z = nz; return true; }
    return false;
  }
  goTo(x, z) { const p = nav.find(this.pos.x, this.pos.z, x, z); this.path = p; this.pi = 0; this.stuck = 0; return !!p; }
  follow(dt, sp) {
    if (!this.path) return true;
    let [tx, tz] = this.path[this.pi];
    let dx = tx - this.pos.x, dz = tz - this.pos.z, d = Math.hypot(dx, dz);
    while (d < 0.25 && this.pi < this.path.length - 1) { this.pi++; [tx, tz] = this.path[this.pi]; dx = tx - this.pos.x; dz = tz - this.pos.z; d = Math.hypot(dx, dz); }
    if (d < 0.2 && this.pi >= this.path.length - 1) { this.path = null; return true; }
    const last = this.pi >= this.path.length - 1; const s = last && d < 0.6 ? sp * Math.max(0.35, d / 0.6) : sp;
    const moved = this.step(dx / d, dz / d, s, dt);
    this.turnTo(Math.atan2(dx, dz), dt, 10);
    if (!moved) { this.stuck += dt; if (this.stuck > 0.6) { const end = this.path[this.path.length - 1]; this.stuck = 0; if (!this.goTo(end[0], end[1])) { this.path = null; return true; } } }
    else this.stuck = Math.max(0, this.stuck - dt);
    return false;
  }
  doAction(spot, onDone) {
    const A = ACTION_INFO[spot.kind]; this.acting = spot; this.place(spot.x, spot.z, spot.yaw);
    const loop = () => this.play(A.loop, 0.4);
    if (A.enter && this.acts[A.enter]) { this.play(A.enter, 0.3); this.onFinish = loop; } else loop();
    onDone && onDone(A);
  }
  endAction(after) {
    const spot = this.acting; if (!spot) { after && after(); return; }
    const A = ACTION_INFO[spot.kind]; this.acting = null; if (spot.taken === this) spot.taken = null;
    const _after = after; after = () => { unstick(this, 1.5); _after && _after(); };
    if (A.exit && this.acts[A.exit]) { this.play(A.exit, 0.3); this.onFinish = () => { this.play('Idle'); after && after(); }; }
    else { this.onFinish = null; this.play('Idle'); after && after(); }
  }
  update(dt) {
    this.mixer.update(dt);
    const gy = groundH(this.pos.x, this.pos.z); this.pos.y += (gy - this.pos.y) * Math.min(1, dt * 12);
    this.sync();
  }
}

// ---------------------------------------------------------------- 주민
class Villager extends Actor {
  constructor(def, model, home) { super(def, model); this.home = home; this.state = 'idle'; this.t = 1 + Math.random() * 4; }
  choose() {
    const r = Math.random(); let tgt = null; this.plan = null;
    if (r < 0.45) {
      const kinds = ['temple_bow', 'temple_bow', 'church_pew', 'cathedral_pew', 'temple_incense', 'cathedral_candle'];
      const kind = kinds[Math.floor(Math.random() * kinds.length)];
      const free = SPOTS.filter(s => s.kind === kind && !s.taken);
      if (free.length) { const s = free[Math.floor(Math.random() * free.length)]; s.taken = this; this.plan = s; tgt = [s.x, s.z]; }
    }
    if (!tgt) {
      const pools = [OUT.plaza, OUT.pond, OUT.walk, OUT.church, OUT.cathedral, OUT.temple, [this.home]];
      const pool = pools[Math.floor(Math.random() * pools.length)]; const p = pool[Math.floor(Math.random() * pool.length)];
      tgt = [p[0] + (Math.random() - 0.5) * 0.8, p[1] + (Math.random() - 0.5) * 0.8]; this.cheer = pool === OUT.plaza && Math.random() < 0.4;
    }
    if (this.goTo(tgt[0], tgt[1])) this.state = 'walk';
    else { if (this.plan) this.plan.taken = null; this.plan = null; this.state = 'idle'; this.t = 2; }
  }
  update(dt) {
    if (this.state === 'idle') { this.t -= dt; if (this.t <= 0) this.choose(); }
    else if (this.state === 'walk') {
      this.play('Walking_A'); if (this.cur) this.cur.setEffectiveTimeScale(0.9);
      if (this.follow(dt, WALK * 0.8)) {
        if (this.plan) { this.state = 'act'; this.t = 25 + Math.random() * 35; this.doAction(this.plan); if (this.plan.kind === 'cathedral_candle') lightCandle(); if (this.plan.kind === 'temple_incense') smoke.puff(); }
        else { this.state = 'idle'; this.t = 6 + Math.random() * 14; if (this.cheer) { this.play('Cheer', 0.3); this.onFinish = () => this.play('Idle'); } else this.play('Idle'); }
      }
    } else if (this.state === 'act') { this.t -= dt; if (this.t <= 0) { this.state = 'busy'; this.endAction(() => { this.state = 'idle'; this.t = 1; }); } }
    if (player && this.state === 'walk') { const px = this.pos.x - player.pos.x, pz = this.pos.z - player.pos.z, pd = Math.hypot(px, pz); if (pd < 0.6 && pd > 0.01) this.step(px / pd, pz / pd, 0.6, dt); }
    super.update(dt);
  }
}

// ---------------------------------------------------------------- 낙엽·향 연기·촛불
function makeLeaves(n = 420) {
  const g = new THREE.PlaneGeometry(0.13, 0.09);
  const mesh = new THREE.InstancedMesh(g, new THREE.MeshLambertMaterial({ side: THREE.DoubleSide }), n); mesh.frustumCulled = false;
  const cols = ['#D9382B', '#E8552E', '#F07A2E', '#F2C230', '#C42F2F', '#F29A38'].map(c => new THREE.Color(c));
  const L = []; const M = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), s = new THREE.Vector3(1, 1, 1), p = new THREE.Vector3();
  for (let i = 0; i < n; i++) { L.push({ x: (Math.random() - 0.5) * 36, y: Math.random() * 9, z: (Math.random() - 0.5) * 36, v: 0.35 + Math.random() * 0.45, w: Math.random() * 6, r: Math.random() * 6 }); mesh.setColorAt(i, cols[i % cols.length]); }
  scene.add(mesh);
  return (dt, cx, cz, t) => {
    for (let i = 0; i < n; i++) {
      const l = L[i]; l.y -= l.v * dt; l.r += dt * 1.5;
      const gx = cx + l.x + Math.sin(t * 0.7 + l.w) * 0.8, gz = cz + l.z + Math.cos(t * 0.5 + l.w) * 0.6, gy = groundH(gx, gz);
      if (l.y < gy - 1) { l.y = gy + 8 + Math.random() * 3; l.x = (Math.random() - 0.5) * 36; l.z = (Math.random() - 0.5) * 36; }
      const yy = Math.max(l.y, gy + 0.02);
      e.set(l.y > gy ? l.r : -Math.PI / 2, l.r * 0.7, l.y > gy ? l.r * 0.4 : 0); q.setFromEuler(e); p.set(gx, yy, gz); M.compose(p, q, s); mesh.setMatrixAt(i, M);
    }
    mesh.instanceMatrix.needsUpdate = true;
  };
}
const smoke = (() => {
  const n = 60, g = new THREE.SphereGeometry(0.08, 6, 4), m = new THREE.MeshBasicMaterial({ color: 0xEDE6DA, transparent: true, opacity: 0.45, depthWrite: false });
  const mesh = new THREE.InstancedMesh(g, m, n); mesh.frustumCulled = false; scene.add(mesh);
  const P = Array.from({ length: n }, () => ({ t: Math.random() * 4 })); const M = new THREE.Matrix4(), v = new THREE.Vector3(), q = new THREE.Quaternion(), s = new THREE.Vector3();
  let src = null, boost = 0;
  return {
    set(x, y, z) { src = new THREE.Vector3(x, y, z); }, puff() { boost = 6; },
    update(dt) {
      if (!src) return; boost = Math.max(0, boost - dt);
      P.forEach((p, i) => {
        p.t += dt * (1 + boost * 0.3); if (p.t > 4) p.t -= 4; const k = p.t / 4;
        v.set(src.x + Math.sin(p.t * 1.7 + i) * 0.15 * k, src.y + k * (1.8 + boost * 0.1), src.z + Math.cos(p.t * 1.3 + i) * 0.15 * k);
        const sc = (0.5 + k * 2.2) * (i % 2 || boost > 0 ? 1 : 0.4); s.set(sc, sc, sc); M.compose(v, q, s); mesh.setMatrixAt(i, M);
      });
      m.opacity = 0.3 + 0.25 * Math.min(1, boost); mesh.instanceMatrix.needsUpdate = true;
    },
  };
})();
let candleLit = 0; const candleFlames = [];
function lightCandle() {
  const C = LAYOUT.candles; if (!C) return; const i = candleLit % C.p.length; candleLit++;
  let f = candleFlames[i];
  if (!f) { f = new THREE.Mesh(new THREE.SphereGeometry(0.035, 8, 6), new THREE.MeshBasicMaterial({ color: 0xFFB43A })); f.scale.set(1, 1.8, 1); scene.add(f); candleFlames[i] = f; }
  f.position.set(C.p[i][0], C.y + 0.17, C.p[i][1]); f.visible = true;
}

// ---------------------------------------------------------------- UI
const $ = id => document.getElementById(id);
let pickKey = 'hamster';
const pick = $('pick');
ANIMALS.forEach(a => {
  const b = document.createElement('button'); b.setAttribute('role', 'radio'); b.setAttribute('aria-checked', String(a.k === pickKey)); b.dataset.k = a.k;
  b.innerHTML = `<img src="${asset(`assets/portraits/${a.k}.png`)}" alt="" width="96" height="120">${a.n}<small>${a.job}</small>`;
  b.onclick = () => { pickKey = a.k; pick.querySelectorAll('button').forEach(x => x.setAttribute('aria-checked', String(x.dataset.k === pickKey))); };
  pick.appendChild(b);
});

// ---------------------------------------------------------------- 땅 (높이맵 + 바닥 무늬 지도: 흙길·돌바닥·낙엽)
const windU = { value: 0 };
function texRepeat(p) { const t = texL.load(asset(p)); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t; }
function makeTerrain() {
  const n = HM.n, S = HM.size, g = new THREE.PlaneGeometry(S, S, n - 1, n - 1); g.rotateX(-Math.PI / 2);
  const pos = g.attributes.position;
  for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) pos.setY(j * n + i, HM.h[j * n + i]);
  g.computeVertexNormals();
  const splat = texL.load(asset('assets/tex/splat.png')); splat.colorSpace = THREE.NoColorSpace; splat.flipY = false;
  const U = { tDirt: { value: texRepeat('assets/tex/dirt.jpg') }, tStone: { value: texRepeat('assets/tex/stone.jpg') }, tSplat: { value: splat }, uSize: { value: S } };
  const m = new THREE.MeshLambertMaterial({ color: 0xffffff });
  m.onBeforeCompile = sh => {
    Object.assign(sh.uniforms, U);
    sh.vertexShader = 'varying vec3 vW;\n' + sh.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\nvW = (modelMatrix * vec4(transformed, 1.0)).xyz;');
    sh.fragmentShader = `uniform sampler2D tDirt, tStone, tSplat; uniform float uSize; varying vec3 vW;
vec3 tri(sampler2D t, vec2 p) { vec3 a = texture2D(t, p * 0.42).rgb, b = texture2D(t, mat2(0.8, 0.6, -0.6, 0.8) * p * 0.11 + 0.37).rgb; return mix(a, b, 0.45); }
float hsh(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vn(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f); return mix(mix(hsh(i), hsh(i + vec2(1, 0)), f.x), mix(hsh(i + vec2(0, 1)), hsh(i + vec2(1, 1)), f.x), f.y); }
float fbm(vec2 p) { float s = 0.0, a = 0.5; for (int k = 0; k < 4; k++) { s += a * vn(p); p = mat2(1.6, 1.2, -1.2, 1.6) * p; a *= 0.5; } return s; }
` + sh.fragmentShader.replace('#include <map_fragment>', `
  vec2 p = vW.xz; vec4 sp = texture2D(tSplat, p / uSize + 0.5);
  float big = fbm(p * 0.08), mid = fbm(p * 0.6 + 7.0), fine = vn(p * 9.0);
  vec3 gr = mix(vec3(0.22, 0.30, 0.10), vec3(0.42, 0.42, 0.15), big) * (0.82 + 0.25 * mid) * (0.9 + 0.18 * fine);
  float lf = smoothstep(0.45, 0.7, fbm(p * 1.7 + 3.0));
  vec3 leafc = mix(vec3(0.62, 0.20, 0.07), vec3(0.85, 0.48, 0.10), vn(p * 3.1)) * (0.85 + 0.25 * fine);
  vec3 leaf = mix(gr * vec3(1.15, 0.85, 0.6), leafc, lf);
  gr = mix(gr, leafc, lf * 0.25);
  vec3 c = mix(gr, leaf, sp.b);
  c = mix(c, tri(tDirt, p * 1.2) * vec3(1.05, 0.95, 0.85), sp.r);
  c = mix(c, tri(tStone, p * 1.6) * vec3(1.05, 1.0, 0.95), sp.g);
  diffuseColor.rgb *= c;`);
  };
  const mesh = new THREE.Mesh(g, m); mesh.name = 'terrain'; mesh.receiveShadow = true; scene.add(mesh); return mesh;
}

// ---------------------------------------------------------------- 소품 (Quaternius CC0: 나무·바위·풀·집·우물…)
const SWAY = /Tree|Willow|Bush|Grass|Plant|Flowers/;
// 카메라와 캐릭터 사이를 가리는 나무·집은 점무늬로 비쳐 보이게 (가까울수록 많이)
const seeU = { uCam: { value: new THREE.Vector3(0, 99, 0) }, uTgt: { value: new THREE.Vector3() }, uSeeR: { value: 1.2 } };
const SEE_VS = ['varying vec3 vSee;', '#include <worldpos_vertex>\n#ifdef USE_INSTANCING\nvSee = (modelMatrix * instanceMatrix * vec4(transformed, 1.0)).xyz;\n#else\nvSee = (modelMatrix * vec4(transformed, 1.0)).xyz;\n#endif'];
function addSee(m) {   // 건물 벽·탑도 카메라를 가리면 점무늬로 비쳐 보이게
  m.onBeforeCompile = sh => {
    Object.assign(sh.uniforms, seeU);
    sh.vertexShader = SEE_VS[0] + '\n' + sh.vertexShader.replace('#include <worldpos_vertex>', SEE_VS[1]);
    sh.fragmentShader = SEE_FS + sh.fragmentShader.replace('#include <clipping_planes_fragment>', '#include <clipping_planes_fragment>\nif (seeMask() < 0.5) discard;');
  };
  return m;
}
const SEE_FS = `uniform vec3 uCam, uTgt; uniform float uSeeR; varying vec3 vSee;
float seeMask() {
  vec3 ab = uTgt - uCam; float L = length(ab); if (L < 0.01) return 1.0; vec3 d = ab / L;
  float t = dot(vSee - uCam, d); if (t < 0.0 || t > L - 0.6 || vSee.y < uTgt.y - 0.45) return 1.0;
  float r = length(vSee - uCam - d * t); float rr = uSeeR * (0.6 + 0.4 * t / L); float k = smoothstep(rr * 0.7, rr * 1.3, r);
  float b = fract(dot(floor(gl_FragCoord.xy), vec2(0.5, 0.25)) + fract(floor(gl_FragCoord.y * 0.5) * 0.5));
  return k + step(0.62 + 0.25 * step(2.0, uSeeR), b);
}
`;
function propMaterial(name) {
  const m = new THREE.MeshLambertMaterial({ vertexColors: true, flatShading: true });
  const sway = SWAY.test(name), amp = /Grass|Plant|Flowers/.test(name) ? 0.08 : /Bush/.test(name) ? 0.03 : 0.045, see = !/Grass|Plant|Flowers|Lilypad|Rock|Barrel|Crate|Hay/.test(name);
  {
    m.onBeforeCompile = sh => {
      sh.uniforms.uWind = windU; Object.assign(sh.uniforms, seeU);
      if (see) {
        sh.vertexShader = SEE_VS[0] + '\n' + sh.vertexShader.replace('#include <worldpos_vertex>', SEE_VS[1]);
        sh.fragmentShader = SEE_FS + sh.fragmentShader.replace('#include <clipping_planes_fragment>', '#include <clipping_planes_fragment>\nif (seeMask() < 0.5) discard;');
      }
      if (!sway) return;
      sh.vertexShader = 'uniform float uWind;\n' + sh.vertexShader.replace('#include <begin_vertex>', `#include <begin_vertex>
  vec3 ip = vec3(instanceMatrix[3][0], 0.0, instanceMatrix[3][2]);
  float hk = max(0.0, transformed.y) ; float ph = uWind * 1.3 + ip.x * 0.37 + ip.z * 0.29;
  transformed.x += sin(ph) * hk * ${amp.toFixed(3)} + sin(ph * 2.7 + transformed.y) * hk * ${(amp * 0.3).toFixed(3)};
  transformed.z += cos(ph * 0.8) * hk * ${(amp * 0.6).toFixed(3)};`);
    };
  }
  return m;
}
function placeProps(gltf) {
  const src = {}; gltf.scene.traverse(o => { if (o.isMesh) src[o.name || o.parent.name] = o; });
  gltf.scene.children.forEach(n => { const mm = n.isMesh ? n : n.children.find(c => c.isMesh); if (mm) src[n.name] = mm; });
  const groups = {}; const VAR = ['r', 'r', 'o', 'o', 'o', 'g', 'g'];
  LAYOUT.props.forEach(([m, x, y, z, ry, s], i) => {
    let k = m; const h = Math.abs(Math.sin(i * 12.9898 + x * 78.233) * 43758.5453) % 1;
    if (src[m + '~r']) k = m + '~' + VAR[Math.floor(h * VAR.length)];
    (groups[k] = groups[k] || []).push([x, y, z, ry, s]);
  });
  const M = new THREE.Matrix4(), q = new THREE.Quaternion(), v = new THREE.Vector3(), sc = new THREE.Vector3(), up = new THREE.Vector3(0, 1, 0);
  const root = new THREE.Group(); root.name = 'props';
  for (const [k, list] of Object.entries(groups)) {
    const s = src[k]; if (!s) { console.warn('prop?', k); continue; }
    const geo = s.geometry; if (!geo.attributes.normal) geo.computeVertexNormals();
    const im = new THREE.InstancedMesh(geo, propMaterial(k), list.length);
    list.forEach(([x, y, z, ry, ss], i) => { q.setFromAxisAngle(up, ry); M.compose(v.set(x, y, z), q, sc.set(ss, ss, ss)); im.setMatrixAt(i, M); });
    im.castShadow = !/Grass|Plant|Flowers|Lilypad/.test(k); im.receiveShadow = true; im.computeBoundingSphere(); im.name = k;
    root.add(im);
  }
  scene.add(root); return root;
}

// ---------------------------------------------------------------- 불러오기
const models = {}; let villageRoot = null, terrainMesh = null, propsRoot = null; const roofs = {}; let ready = null;
async function loadAll(progress) {
  const jobs = [['village', 'assets/village/village.glb'], ['props', 'assets/props.glb'], ['anims', 'assets/animations/kaykit_animations.glb'], ...ANIMALS.map(a => [a.k, `assets/characters/${a.k}.glb`])];
  let done = 0;
  await Promise.all(jobs.map(async ([k, p]) => { models[k] = await parse(await bin(p)); done++; progress(done / jobs.length); }));
  ANIMS = models.anims.animations;
  villageRoot = models.village.scene;
  villageRoot.traverse(o => {
    if (!o.isMesh) return;
    if (o.name === 'water' || (o.parent && o.parent.name === 'water')) { o.material = new THREE.MeshPhongMaterial({ vertexColors: true, transparent: true, opacity: 0.88, shininess: 120, specular: 0x8899AA }); o.receiveShadow = true; return; }
    if (o.material.name === 'Glow') { const m = addSee(new THREE.MeshBasicMaterial({ vertexColors: true, transparent: true, depthWrite: false, fog: false })); glowMats.push(m); o.material = m; }
    else { o.material = addSee(new THREE.MeshToonMaterial({ vertexColors: true, gradientMap: grad })); o.castShadow = true; o.receiveShadow = true; }
  });
  scene.add(villageRoot);
  terrainMesh = makeTerrain();
  propsRoot = placeProps(models.props);
  for (const r of LAYOUT.interiors) roofs[r.roof] = villageRoot.getObjectByName(r.roof);
  const t = LAYOUT.actions.temple_incense; if (t) smoke.set(t[0][0], 2.2, t[0][1] - 1.1);
  applyTime(TIME.cur);
}
ready = loadAll(p => { $('start').textContent = `불러오는 중… ${Math.round(p * 100)}%`; })
  .then(() => { $('start').disabled = false; $('start').textContent = '산책 시작'; })
  .catch(e => { $('start').textContent = '불러오지 못했어요'; console.error(e); });

// ---------------------------------------------------------------- 시작
let player = null, npcs = [], audio = null, leaves = null, started = false;
const camState = { yaw: 0, pitch: 0.42, dist: 7.5, tgt: new THREE.Vector3() };
let sitting = false, pendingAction = null;
const marker = new THREE.Mesh(new THREE.RingGeometry(0.18, 0.26, 24), new THREE.MeshBasicMaterial({ color: 0xFFF1D0, transparent: true, opacity: 0.85, depthWrite: false }));
marker.rotation.x = -Math.PI / 2; marker.visible = false; scene.add(marker);

async function startWalk() {
  await ready; if (started) return; started = true;
  if (!audio) { audio = createAudio(); audio.start(); } audio.setVolume(parseFloat($('vol').value));
  for (const a of ANIMALS) {
    const m = prepModel(models[a.k]);
    if (a.k === pickKey) { player = new Actor(a, m); const s = LAYOUT.spawn.plaza; player.place(s[0], s[2] + 0.6, Math.PI); }
    else { const v = new Villager(a, m, [LAYOUT.homes[a.k][0], LAYOUT.homes[a.k][2]]); const sp = OUT.walk[npcs.length % OUT.walk.length]; v.place(sp[0] + Math.random(), sp[1] + Math.random(), Math.random() * 6.28); npcs.push(v); }
  }
  if (!leaves) leaves = makeLeaves(); camState.tgt.copy(player.pos); applyTime(TIME.cur);
  $('intro').hidden = true; $('hud').hidden = false; $('help').hidden = false;
  setTimeout(() => { $('help').hidden = true; }, 15000);
  hookAudioText();
}
$('start').onclick = startWalk;

// ---------------------------------------------------------------- 조작
const keys = new Set();
addEventListener('keydown', e => {
  if (e.target.tagName === 'INPUT') return; keys.add(e.code);
  if (/Arrow|Key[WASD]/.test(e.code) && player && (player.acting || sitting)) stopActing();
  if (e.code === 'KeyE') { const b = $('btnAct'); if (!b.hidden) b.click(); }
});
addEventListener('keyup', e => keys.delete(e.code));
const pointers = new Map(); let pinch0 = 0, down = null;
canvas.addEventListener('pointerdown', e => { canvas.setPointerCapture(e.pointerId); pointers.set(e.pointerId, [e.clientX, e.clientY]); down = { x: e.clientX, y: e.clientY, t: performance.now(), moved: 0 }; if (pointers.size === 2) { const [a, b] = [...pointers.values()]; pinch0 = Math.hypot(a[0] - b[0], a[1] - b[1]); } });
canvas.addEventListener('pointermove', e => {
  if (!pointers.has(e.pointerId)) return; const [px, py] = pointers.get(e.pointerId); const dx = e.clientX - px, dy = e.clientY - py; pointers.set(e.pointerId, [e.clientX, e.clientY]);
  if (down) down.moved += Math.abs(dx) + Math.abs(dy);
  if (pointers.size === 2) { const [a, b] = [...pointers.values()]; const d = Math.hypot(a[0] - b[0], a[1] - b[1]); if (pinch0) camState.dist = THREE.MathUtils.clamp(camState.dist * pinch0 / d, 2.5, 24); pinch0 = d; return; }
  if (down && down.moved > 6) { camState.yaw -= dx * 0.006; camState.pitch = THREE.MathUtils.clamp(camState.pitch + dy * 0.004, 0.05, 1.45); }
});
const ray = new THREE.Raycaster(), ndc = new THREE.Vector2();
canvas.addEventListener('pointerup', e => {
  pointers.delete(e.pointerId); if (pointers.size < 2) pinch0 = 0;
  if (!started || !down) return; const click = down.moved < 8 && performance.now() - down.t < 450; down = null;
  if (!click) return;
  ndc.set(e.clientX / innerWidth * 2 - 1, -(e.clientY / innerHeight) * 2 + 1); ray.setFromCamera(ndc, cam);
  const targets = [terrainMesh, ...['temple', 'church', 'cathedral', 'plaza'].map(n => villageRoot.getObjectByName(n))].filter(Boolean);
  if (!terrainMesh) return;
  const hit = ray.intersectObjects(targets, true).find(h => h.face && h.face.normal.y > 0.6);
  if (hit) walkTo(hit.point.x, hit.point.z);
});
canvas.addEventListener('wheel', e => { camState.dist = THREE.MathUtils.clamp(camState.dist * (1 + Math.sign(e.deltaY) * 0.1), 2.5, 24); e.preventDefault(); }, { passive: false });

function walkTo(x, z, then) {
  stopActing(() => {
    if (player.goTo(x, z)) { const end = player.path[player.path.length - 1]; marker.visible = true; marker.position.set(end[0], groundH(end[0], end[1]) + 0.04, end[1]); pendingAction = then || null; }
  });
}
$('btnGo').onclick = () => { $('goMenu').hidden = !$('goMenu').hidden; };
$('goMenu').addEventListener('click', e => {
  const b = e.target.closest('[data-go]'); if (!b || !player) return; $('goMenu').hidden = true;
  const k = b.dataset.go;
  if (k === 'rescue') { rescue(); return; }
  if (k === 'reset') { resetToIntro(); return; }
  const p = k === 'home' ? [LAYOUT.homes[pickKey][0], LAYOUT.homes[pickKey][2]] : POI[k].p; walkTo(p[0], p[1]);
});
const ORDER = ['dusk', 'night', 'day'];
$('btnTime').onclick = () => applyTime(ORDER[(ORDER.indexOf(TIME.cur) + 1) % 3]);
$('vol').oninput = e => audio && audio.setVolume(parseFloat(e.target.value));

// 명상 (그 자리에 앉아 호흡)
let breathT = 0;
function toggleSit() {
  if (!player) return;
  if (player.acting) { stopActing(); return; }
  if (!sitting) {
    sitting = true; player.path = null; marker.visible = false; $('btnSit').classList.add('on'); $('btnSit').textContent = '일어나기';
    player.play('Sit_Floor_Down', 0.3); player.onFinish = () => { if (sitting) player.play('Sit_Floor_Idle', 0.4); };
    $('breath').hidden = false; breathT = 0; camState.dist = Math.max(camState.dist, 8); camState.pitch = Math.max(camState.pitch, 0.5);
  } else {
    sitting = false; $('btnSit').classList.remove('on'); $('btnSit').textContent = '명상하기';
    player.play('Sit_Floor_StandUp', 0.3); player.onFinish = () => player.play('Idle');
    $('breath').hidden = true;
  }
}
$('btnSit').onclick = toggleSit;

// 장소에서 하는 일
let nearSpot = null;
function stopActing(after) {
  if (sitting) { toggleSit(); if (after) setTimeout(after, 700); return; }
  if (player && player.acting) { player.endAction(after); $('btnAct').classList.remove('on'); $('actMsg').hidden = true; return; }
  if (after) after();
}
function startAction(spot) {
  if (spot.taken && spot.taken !== player) { const alt = SPOTS.filter(s => s.kind === spot.kind && !s.taken).sort((a, b) => Math.hypot(a.x - player.pos.x, a.z - player.pos.z) - Math.hypot(b.x - player.pos.x, b.z - player.pos.z))[0]; if (!alt) return; spot = alt; }
  const go = () => {
    if (spot.taken && spot.taken !== player) return;
    spot.taken = player; marker.visible = false;
    player.doAction(spot, A => { const b = $('btnAct'); b.hidden = false; b.classList.add('on'); b.textContent = '일어나기'; $('actMsg').textContent = A.msg; $('actMsg').hidden = false; });
    if (spot.kind === 'temple_incense') { smoke.puff(); audio && audio.chime(); }
    if (spot.kind === 'cathedral_candle') { lightCandle(); audio && audio.chime(); }
    if (spot.kind === 'temple_bow') audio && audio.moktakOnce();
  };
  if (Math.hypot(spot.x - player.pos.x, spot.z - player.pos.z) < 0.35) go();
  else walkTo(spot.x, spot.z, go);
}
$('btnAct').onclick = () => { if (!player) return; if (player.acting) { stopActing(); return; } if (nearSpot) startAction(nearSpot); };
function nearest(kind) { return SPOTS.filter(s => s.kind === kind && !s.taken).sort((a, b) => Math.hypot(a.x - player.pos.x, a.z - player.pos.z) - Math.hypot(b.x - player.pos.x, b.z - player.pos.z))[0] || null; }
function updateActionButton() {
  if (!player || player.acting) return;
  let best = null, bd = 2.2;
  for (const s of SPOTS) { const d = Math.hypot(s.x - player.pos.x, s.z - player.pos.z); if (d < bd && !s.taken) { bd = d; best = s; } }
  if (!best) for (const it of LAYOUT.interiors) if (insideRect(it, player.pos.x, player.pos.z)) best = nearest(it.roof === 'temple_roof' ? 'temple_bow' : it.roof === 'church_roof' ? 'church_pew' : 'cathedral_pew');
  nearSpot = best; const b = $('btnAct');
  if (best) { b.hidden = false; b.textContent = ACTION_INFO[best.kind].label; } else b.hidden = true;
}

// ---------------------------------------------------------------- 자막
let zoneNow = 'village', ttsOn = false, lastLine = -1;
const LINE_START = []; { let k = 0; HEART_SUTRA.forEach((l, i) => { LINE_START[i] = k; k += l.length + 1; }); }
const songTitle = {};
function hookAudioText() {
  audio.listeners.syllable = (li, idx) => {
    if (zoneNow !== 'temple') return;
    const line = HEART_SUTRA[li], pos = idx - LINE_START[li];
    $('capText').innerHTML = `<span class="done">${line.slice(0, pos)}</span><span class="now">${line[pos] || ''}</span><span class="todo">${line.slice(pos + 1)}</span>`;
    if (li !== lastLine) { lastLine = li; if (ttsOn && 'speechSynthesis' in window) { speechSynthesis.cancel(); const u = new SpeechSynthesisUtterance(line); u.lang = 'ko-KR'; u.rate = 0.8; u.pitch = 0.4; u.volume = 0.55; speechSynthesis.speak(u); } }
  };
  audio.listeners.song = (zone, title) => { if (zoneNow === zone) $('capTitle').textContent = '♪ ' + title; songTitle[zone] = title; };
}
$('tts').onchange = e => { ttsOn = e.target.checked; if (!ttsOn && 'speechSynthesis' in window) speechSynthesis.cancel(); };
$('btnNext').onclick = () => audio && audio.nextSong(zoneNow);
$('btnBell').onclick = () => audio && audio.ring(zoneNow);
function setZone(z) {
  if (z === zoneNow) return; zoneNow = z;
  $('caption').hidden = z === 'village';
  $('ttsWrap').hidden = z !== 'temple'; $('btnNext').hidden = !(z === 'church' || z === 'cathedral');
  if (z !== 'temple' && 'speechSynthesis' in window) speechSynthesis.cancel();
  if (z === 'temple') { $('capTitle').textContent = '마하반야바라밀다심경 · 목탁에 맞춰 독경하고 있어요'; $('capText').textContent = ''; lastLine = -1; }
  if (z === 'church') { $('capTitle').textContent = '♪ ' + (songTitle.church || '오르간 찬송가'); $('capText').textContent = '오르간이 찬송가와 크리스마스 캐럴을 연주하고 있어요.'; }
  if (z === 'cathedral') { $('capTitle').textContent = '♪ ' + (songTitle.cathedral || '성가대'); $('capText').textContent = '성가대가 노래하고, 종소리가 가끔 울려요.'; }
  const names = { village: ['단풍마을', '천천히 걸어 보세요'], temple: ['단풍사', '목탁 소리와 반야심경'], church: ['은행나무 교회', '찬송가와 캐럴'], cathedral: ['별빛 성당', '성가대와 오르간'] };
  $('placeName').textContent = names[z][0]; $('placeSub').textContent = names[z][1];
}

// ---------------------------------------------------------------- 끼임 탈출 · 처음으로
function freeSpotNear(x, z, maxR = 8) {   // 가까운 빈자리를 나선형으로 찾기
  if (!blockedR(x, z, RAD + 0.1)) return [x, z];
  for (let r = 0.3; r <= maxR; r += 0.3) {
    const n = Math.ceil(r * 8);
    for (let k = 0; k < n; k++) { const a = k / n * Math.PI * 2, px = x + Math.cos(a) * r, pz = z + Math.sin(a) * r; if (!blockedR(px, pz, RAD + 0.1) && nav.find(px, pz, 0, 4.6)) return [px, pz]; }
  }
  return null;
}
function unstick(a, maxR = 8) {
  if (!a || a.acting) return false;
  if (!blockedR(a.pos.x, a.pos.z, RAD)) return false;
  const p = freeSpotNear(a.pos.x, a.pos.z, maxR); if (!p) return false;
  a.pos.x = p[0]; a.pos.z = p[1]; return true;
}
function rescue() {   // 버튼: 지금 자리에서 가장 가까운 빈자리로, 그래도 안 되면 광장으로
  if (!player) return;
  stopActing(() => {
    player.path = null; pendingAction = null; marker.visible = false;
    let p = freeSpotNear(player.pos.x, player.pos.z, 6);
    if (p && Math.hypot(p[0] - player.pos.x, p[1] - player.pos.z) < 0.05) {   // 막힌 곳은 아닌데 갇혀 있으면: 둘레에서 광장까지 길이 있는 곳으로
      p = null;
      for (let r = 0.6; r <= 6 && !p; r += 0.4) for (let k = 0; k < 16 && !p; k++) { const a = k / 16 * Math.PI * 2, x = player.pos.x + Math.cos(a) * r, z = player.pos.z + Math.sin(a) * r; if (!blockedR(x, z, RAD + 0.1)) { const q = nav.find(x, z, 0, 4.6); if (q) p = [x, z]; } }
    }
    if (!p) { const s = LAYOUT.spawn.plaza; p = [s[0], s[2] + 0.6]; }
    player.place(p[0], p[1]); camState.tgt.set(player.pos.x, player.pos.y + 0.7, player.pos.z);
    $('actMsg').textContent = '빠져나왔어요!'; $('actMsg').hidden = false; setTimeout(() => { if (!player || !player.acting) $('actMsg').hidden = true; }, 1800);
  });
}
function resetToIntro() {   // 처음 화면(동물 고르기)으로
  if (!started) return;
  if (sitting) { sitting = false; $('btnSit').classList.remove('on'); $('btnSit').textContent = '명상하기'; $('breath').hidden = true; }
  for (const a of [player, ...npcs]) { if (!a) continue; a.mixer.stopAllAction(); scene.remove(a.root); }
  SPOTS.forEach(s => { s.taken = null; });
  player = null; npcs = []; pendingAction = null; nearSpot = null; marker.visible = false; wasIndoor = null;
  for (const r of Object.values(roofs)) if (r) r.visible = true;
  if ('speechSynthesis' in window) speechSynthesis.cancel();
  audio && audio.setLevels({ village: 1, temple: 0, church: 0, cathedral: 0 }); setZone('village');
  ['hud', 'caption', 'actMsg', 'help', 'goMenu', 'btnAct'].forEach(id => { $(id).hidden = true; });
  $('intro').hidden = false; started = false;
}

// ---------------------------------------------------------------- 등불 빛·서로 비켜 가기
let BLOOM_ON = true;
function pickLamps(c) {
  const L = (LAYOUT.lights || []).map(p => [p, (p[0] - c.x) ** 2 + (p[2] - c.z) ** 2]).sort((a, b) => a[1] - b[1]);
  LAMPS.forEach((l, i) => { const e = L[i]; l.visible = !!e && TIME.lamp > 0; if (e) { l.position.set(e[0][0], e[0][1], e[0][2]); l.userData.k = e[0][3]; } });
}
function separate(dt) {   // 동물끼리 겹치지 않게 살짝 밀어 냄 (앉아 있거나 기도 중이면 그대로)
  const all = [player, ...npcs];
  for (let i = 0; i < all.length; i++) for (let j = i + 1; j < all.length; j++) {
    const a = all[i], b = all[j]; const dx = b.pos.x - a.pos.x, dz = b.pos.z - a.pos.z, d = Math.hypot(dx, dz);
    if (d > 0.62 || d < 1e-4) continue;
    const push = (0.62 - d) * 2.2, fa = a.acting || (a === player && sitting) ? 0 : 1, fb = b.acting ? 0 : 1; if (!fa && !fb) continue;
    const ka = fa / (fa + fb), kb = fb / (fa + fb);
    if (fa) a.step(-dx / d, -dz / d, push * ka, dt); if (fb) b.step(dx / d, dz / d, push * kb, dt);
  }
}

// ---------------------------------------------------------------- 루프
const clock = new THREE.Clock(); let tAll = 0;
const tmpV = new THREE.Vector3(), dirV = new THREE.Vector3(); const camRay = new THREE.Raycaster(); let keyStuck = 0, camTick = 0, camFree = 99, camCur = 7.5, wasIndoor = null, inK = 0;
function frame() {
  const dt = Math.min(clock.getDelta(), 0.05); tAll += dt;
  if (player) {
    let ix = 0, iz = 0;
    if (keys.has('KeyW') || keys.has('ArrowUp')) iz += 1; if (keys.has('KeyS') || keys.has('ArrowDown')) iz -= 1;
    if (keys.has('KeyA') || keys.has('ArrowLeft')) ix += 1; if (keys.has('KeyD') || keys.has('ArrowRight')) ix -= 1;
    if (keys.has('KeyQ')) camState.yaw += dt * 1.6; if (keys.has('KeyR')) camState.yaw -= dt * 1.6;
    if (keys.has('PageUp')) camState.pitch = Math.min(1.45, camState.pitch + dt); if (keys.has('PageDown')) camState.pitch = Math.max(0.05, camState.pitch - dt);
    const sp = keys.has('ShiftLeft') || keys.has('ShiftRight') ? RUN : WALK;
    if ((ix || iz) && !player.acting && !sitting) {
      player.path = null; pendingAction = null; marker.visible = false;
      const fy = camState.yaw + Math.PI, fx = Math.sin(fy), fz = Math.cos(fy);
      let mx = fx * iz + fz * ix, mz = fz * iz - fx * ix; const l = Math.hypot(mx, mz); mx /= l; mz /= l;
      if (!player.step(mx, mz, sp, dt)) { keyStuck += dt; if (keyStuck > 1.2) { keyStuck = 0; unstick(player, 3); } } else keyStuck = 0;
      player.turnTo(Math.atan2(mx, mz), dt, 10); player.play(sp > WALK ? 'Running_A' : 'Walking_A');
    } else if (player.path) {
      player.play('Walking_A');
      if (player.follow(dt, WALK)) { marker.visible = false; player.play('Idle'); if (pendingAction) { const f = pendingAction; pendingAction = null; f(); } }
    } else if (!sitting && !player.acting && player.curName !== 'Idle' && !player.onFinish) player.play('Idle');
    player.update(dt);
    npcs.forEach(n => n.update(dt));
    separate(dt);
    let indoor = null;
    for (const it of LAYOUT.interiors) { const r = roofs[it.roof], inn = insideRect(it, player.pos.x, player.pos.z, 0.4); if (r) r.visible = !inn; if (inn) indoor = it; }
    if (indoor !== wasIndoor) { if (indoor && !down) { camState.pitch = Math.max(camState.pitch, 0.62); } wasIndoor = indoor; }   // 들어갈 때 한 번만 살짝 올려 줌 — 그다음은 마음대로 돌려 보기
    camState.tgt.lerp(tmpV.set(player.pos.x, player.pos.y + 0.7, player.pos.z), Math.min(1, dt * 5));
    if (sitting || player.acting) camState.yaw += dt * 0.04;
    const pitch = camState.pitch, dist = camState.dist;
    const cp = Math.cos(pitch);
    dirV.set(Math.sin(camState.yaw) * cp, Math.sin(pitch), Math.cos(camState.yaw) * cp);
    inK += ((indoor ? 1 : 0) - inK) * Math.min(1, dt * 2);
    hemi.intensity = TIME[TIME.cur].hemi[2] * (1 + inK * (TIME.cur === 'night' ? 1.4 : TIME.cur === 'dusk' ? 0.5 : 0.15));
    seeU.uSeeR.value += ((indoor ? 3.4 : 0.8 + camCur * 0.06) - seeU.uSeeR.value) * Math.min(1, dt * 3);
    ++camTick; camFree = dist;   // 가리는 벽·지붕·나무는 점무늬로 비쳐 보이니 카메라는 당기지 않고 마음대로 돌려 볼 수 있음
    camCur += (Math.min(dist, camFree) - camCur) * Math.min(1, dt * (camFree < camCur ? 12 : 3));
    cam.position.copy(camState.tgt).addScaledVector(dirV, camCur);
    const gy = groundH(cam.position.x, cam.position.z) + 0.5; if (cam.position.y < gy) cam.position.y = gy;
    cam.lookAt(camState.tgt); seeU.uCam.value.copy(cam.position); seeU.uTgt.value.copy(camState.tgt);
    marker.material.opacity = 0.5 + 0.35 * Math.sin(tAll * 5);
    if (audio) {
      const lv = { village: 1, temple: 0, church: 0, cathedral: 0 }; let best = 'village', bv = 0.3;
      for (const [k, z] of Object.entries(Z)) {
        const d = Math.hypot(player.pos.x - z.center[0], player.pos.z - z.center[2]);
        const v = THREE.MathUtils.clamp((z.radius * 1.3 - d) / (z.radius * 0.7), 0, 1); lv[k] = v * v * (3 - 2 * v);
        if (lv[k] > bv) { bv = lv[k]; best = k; }
      }
      lv.village = 1 - 0.85 * Math.max(lv.temple, lv.church, lv.cathedral); audio.setLevels(lv); setZone(best);
    }
    if (sitting) { breathT += dt; const ph = breathT % 10, inhale = ph < 4; $('breath').classList.toggle('in', inhale); $('breathText').textContent = inhale ? '숨을 들이쉬어요' : '천천히 내쉬어요'; }
    camTick++; if (camTick % 6 === 0) updateActionButton();
    leaves && leaves(dt, camState.tgt.x, camState.tgt.z, tAll);
    smoke.update(dt);
    windU.value = tAll;
    sun.position.set(camState.tgt.x + sun.userData.off[0], sun.userData.off[1], camState.tgt.z + sun.userData.off[2]); sun.target.position.copy(camState.tgt);
    if (camTick % 20 === 0) pickLamps(camState.tgt);
    LAMPS.forEach((l, i) => { if (l.visible) l.intensity = l.userData.k * TIME.lamp * (0.92 + 0.08 * Math.sin(tAll * 7.3 + i * 2.1)); });
    candleFlames.forEach((f, i) => { if (f) f.scale.y = 1.6 + 0.3 * Math.sin(tAll * 9 + i); });
  } else {
    const a = tAll * 0.05; cam.position.set(Math.sin(a) * 30, 15, Math.cos(a) * 30); cam.lookAt(0, 1, -6);
    windU.value = tAll; if (camTick++ % 30 === 0) pickLamps(new THREE.Vector3(Math.sin(a) * 14, 0, Math.cos(a) * 14));
    LAMPS.forEach(l => { if (l.visible) l.intensity = l.userData.k * TIME.lamp; });
  }
  if (BLOOM_ON) composer.render(); else renderer.render(scene, cam);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
window.__dbg = { applyTime, TIME, get bloom() { return BLOOM_ON; }, set bloom(v) { BLOOM_ON = v; }, get player() { return player; }, get npcs() { return npcs; }, startWalk, walkTo, POI, SPOTS, startAction, camState, nav, setPick: k => { pickKey = k; } };
