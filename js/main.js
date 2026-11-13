// 마음 산책 — three.js (맵: 단풍마을 · 별빛 마법학교)
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import * as SkeletonUtils from 'three/addons/utils/SkeletonUtils.js';
import { createRecords, LEVELS, ACH, REWARDS } from './records.js';
import { saintFor, fortuneFor } from './blessing.js';
import { MAPS, MAP_ORDER, BOOK_TITLES, PASSAGES, STARS } from './maps.js';
import { createAudio, HEART_SUTRA } from './audio.js';
const MAPKEY = (() => { const q = new URLSearchParams(location.search).get('map'); if (MAPS[q]) return q; try { const s = localStorage.getItem('mw_map'); if (MAPS[s]) return s; } catch (e) { } return 'village'; })();
const MAP = MAPS[MAPKEY];
const LAYOUT = (await import(MAP.layout)).default;
const FOREST = !!MAP.jumpMap;   // 점프 맵: 발판 위로 오르내리는 진짜 높이 계산을 씀
import { createNav } from './nav.js';
import { createMinimap } from './minimap.js';
import { createCourse } from './jumpcourse.js';

// ---------------------------------------------------------------- 동물
const ANIMALS = [
  ['hamster', '햄스터', 3.017], ['rabbit', '토끼', 3.069], ['cat', '고양이', 2.756], ['dog', '강아지', 3.058], ['bear', '곰', 3.044], ['panda', '판다', 3.047],
  ['fox', '여우', 2.721], ['raccoon', '너구리', 2.964], ['squirrel', '다람쥐', 3.113], ['deer', '사슴', 2.866], ['lion', '사자', 2.84],
].map(([k, s, u]) => ({ k, s, n: (MAP.who && MAP.who[k]) || s, u: MAP.u[k] || u, job: MAP.jobs[k] }));
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
// 그래픽 메모리가 모자라 브라우저가 화면(WebGL)을 거둬 가면: 멈춘 채 두지 않고 안내 후 다시 불러옴
let glLost = false;
canvas.addEventListener('webglcontextlost', e => {
  e.preventDefault(); glLost = true;
  try { rec.save(); sessionStorage.setItem('mw_resume', JSON.stringify({ t: Date.now(), pick: pickKey })); } catch (err) { }
  const o = $('glLost'); if (o) o.hidden = false;
  setTimeout(() => location.reload(), 2500);
});
canvas.addEventListener('webglcontextrestored', () => location.reload());
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, cam));
const bloom = new UnrealBloomPass(new THREE.Vector2(256, 256), 0.6, 0.55, 0.85); composer.addPass(bloom);
composer.addPass(new OutputPass());
function resize() { const w = innerWidth, h = innerHeight; renderer.setSize(w, h, false); composer.setSize(w, h); cam.aspect = w / h; cam.updateProjectionMatrix(); }
addEventListener('resize', resize); resize();

// 낮 · 노을 · 밤
const glowMats = [];   // 등불·연등·창 (밤에 더 밝게)
const TIME = {
  cur: MAP.time,
  day: { sky: 'day', fog: 0xF4D8BC, fogN: 45, fogF: 160, hemi: [0xFFF1DD, 0x8E7050, 1.3], sun: [0xFFE2B8, 2.2], pos: [-30, 42, 24], fill: 0.45, lamp: 0, glow: 1.0, bloom: 0.25, exp: 1.0 },
  dusk: { sky: 'dusk', tint: 0xFFB27A, fog: 0xD99A78, fogN: 30, fogF: 130, hemi: [0xFFD2B0, 0x6A4A50, 1.15], sun: [0xFFA060, 1.9], pos: [-44, 18, 10], fill: 0.45, lamp: 1.8, glow: 1.25, bloom: 0.5, exp: 1.05 },
  night: { sky: 'night', fog: 0x1C2440, fogN: 22, fogF: 110, hemi: [0x5468A8, 0x1A1424, 0.55], sun: [0x9CB4FF, 0.55], pos: [30, 40, -20], fill: 0.12, lamp: 3.2, glow: 1.25, bloom: 0.8, exp: 1.05 },
};
function applyTime(k) {
  TIME.cur = k; const T = TIME[k]; if (k === 'night' && started && typeof rec !== 'undefined') rec.add('night');
  const sky = skyTex[T.sky]; scene.background = sky || new THREE.Color(T.fog);
  scene.fog.color.set(T.fog); scene.fog.near = T.fogN; scene.fog.far = T.fogF;
  hemi.color.set(T.hemi[0]); hemi.groundColor.set(T.hemi[1]); hemi.intensity = T.hemi[2];
  sun.color.set(T.sun[0]); sun.intensity = T.sun[1]; sun.userData.off = T.pos; fill.intensity = T.fill;
  glowMats.forEach(m => m.color.setScalar(T.glow)); bloom.strength = T.bloom; renderer.toneMappingExposure = T.exp;
  if (MAP.key === 'school') { if (!moon) moon = makeMoon(); moon.visible = k !== 'day'; moon.material.opacity = k === 'night' ? 1 : 0.55; }
  TIME.lamp = T.lamp; if (mountains) mountains.material.color.set(k === 'night' ? 0x2A3350 : k === 'dusk' ? 0x8A5A5E : 0x9AA8A0);
  const b = document.getElementById('btnTime'); if (b) b.textContent = { day: '☀️ 낮', dusk: '🌇 노을', night: '🌙 밤' }[k];
}
sun.userData.off = TIME.dusk.pos;

// 마법학교의 큰 달 (밤·노을)
let moon = null;
function makeMoon() {
  const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d');
  const r = g.createRadialGradient(128, 128, 40, 128, 128, 128); r.addColorStop(0, 'rgba(255,250,230,1)'); r.addColorStop(0.36, 'rgba(255,246,220,1)'); r.addColorStop(0.42, 'rgba(255,240,200,0.35)'); r.addColorStop(1, 'rgba(255,230,180,0)');
  g.fillStyle = r; g.fillRect(0, 0, 256, 256);
  g.fillStyle = 'rgba(220,210,190,0.35)'; [[110, 105, 12], [150, 140, 9], [120, 155, 7], [148, 100, 6]].forEach(([x, y, rr]) => { g.beginPath(); g.arc(x, y, rr, 0, 7); g.fill(); });
  const m = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(c), transparent: true, depthWrite: false, fog: false }));
  m.scale.setScalar(46); m.position.set(-70, 62, -120); m.renderOrder = -1; scene.add(m); return m;
}

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
    if (Math.abs(lx) <= p.h[0] && Math.abs(lz) <= p.h[1]) {
      const t = (p.h[1] - lz) / (2 * p.h[1]);
      let f = t;
      if (p.st) {   // 계단: 디딤판 위에서는 평평하게, 턱에서만 짧게 올라감 → 발이 계단에 닿아 보임
        const u = t / p.sl, k = Math.floor(u), fr = u - k, e = fr > 0.82 ? (fr - 0.82) / 0.18 : 0;
        f = Math.min(p.st, k + 1 + e * e * (3 - 2 * e)) / p.st;
      }
      y = Math.max(y, p.y0 + (p.y1 - p.y0) * f);
    }
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
const POI = MAP.poi(BLD);
const minimap = createMinimap({ key: MAP.key, nav, bound: LAYOUT.bound, layout: LAYOUT, poi: POI, water: MAP.water || [], icon: MAP.icon, onPick: (x, z) => walkTo(x, z) }); minimap.visible = false;   // 지도 (길찾기 격자로 바닥을 그림)
const ACTION_INFO = {
  temple_bow: { label: '🙇 절하기', enter: 'Sit_Floor_Down', loop: 'Bow', exit: 'Sit_Floor_StandUp', msg: '부처님께 천천히 절을 올려요.', rec: 'bowTime',
    modes: { b108: { label: '📿 108배', loop: 'Bow', speed: 1.55, msg: '108배를 시작해요. 천천히, 숨과 함께.' } } },
  temple_moktak: { label: '🪵 목탁 치기', enter: 'Sit_Floor_Down', loop: 'Moktak', exit: 'Sit_Floor_StandUp', msg: '똑, 똑, 똑… 목탁 소리에 마음을 실어요.', rec: 'pray' },
  temple_donate: { label: '🪙 시주하기', enter: 'Interact', loop: 'Pray_Stand', exit: null, msg: '시주함에 마음을 담아 넣었어요. (게임 안의 시주예요)', rec: 'pray', count: 'donate' },
  temple_incense: { label: '🌫️ 향 피우기', count: 'incense', rec: 'pray', enter: 'Interact', loop: 'Pray_Stand', exit: null, msg: '향 연기가 피어올라요.' },
  church_choir: { label: '🎵 성가대 함께하기', enter: null, loop: 'Sing', exit: null, msg: '성가대와 함께 노래해요. 이웃들도 모여들어요.', rec: 'sing' },
  cathedral_baptism: { label: '💧 세례 받기', enter: 'Interact', loop: 'Pray_Stand', exit: null, msg: '맑은 물로 축복을 받아요.', rec: 'pray' },
  church_pew: { label: '🙏 앉아서 기도하기', enter: 'Sit_Chair_Down', loop: 'Pray_Sit', exit: 'Sit_Chair_StandUp', msg: '두 손을 모아 기도해요.', rec: 'pray' },
  cathedral_pew: { label: '🙏 앉아서 기도하기', enter: 'Sit_Chair_Down', loop: 'Pray_Sit', exit: 'Sit_Chair_StandUp', msg: '두 손을 모아 기도해요.', rec: 'pray' },
  // 별빛 마법학교
  hall_sit: { label: '🍲 식탁에 앉기', enter: 'Sit_Chair_Down', loop: 'Sit_Chair_Idle', exit: 'Sit_Chair_StandUp', msg: '떠 있는 촛불 아래, 따뜻한 호박 수프 냄새가 나요.', rec: 'meditate' },
  hall_candle: { label: '🕯️ 촛불 띄우기', count: 'candle', enter: 'Interact', loop: 'Pray_Stand', exit: null, msg: '작은 촛불이 천천히 떠올라 다른 촛불들과 함께 빛나요.', rec: 'pray' },
  library_read: { label: '📖 책 읽기', enter: 'Sit_Chair_Down', loop: 'Read', exit: 'Sit_Chair_StandUp', msg: '', rec: 'read' },
  library_shelf: { label: '📚 책 고르기', count: 'books', enter: 'Interact', loop: 'Idle', exit: null, msg: '', rec: 'read' },
  magic_cast: { label: '✨ 마법 연습', count: 'spells', enter: null, loop: 'Spellcasting', exit: null, msg: '마법진 위에서 주문을 외워요. 빛 방울이 피어올라요.', rec: 'magic' },
  stars: { label: '🔭 별 보기', enter: 'Interact', loop: 'Idle', exit: null, msg: '', rec: 'stars' },
  forest_stump: { label: '🪵 그루터기에 앉기', enter: 'Sit_Chair_Down', loop: 'Sit_Chair_Idle', exit: 'Sit_Chair_StandUp', msg: '모닥불 타는 소리를 들으며 쉬어요.', rec: 'meditate' },
  forest_view: { label: '🌄 경치 보기', enter: null, loop: 'Idle', exit: null, msg: '나무 꼭대기에서 숲을 내려다봐요. 바람이 시원해요.', rec: 'meditate' },
  cathedral_candle: { label: '🕯️ 촛불 켜기', count: 'candle', rec: 'pray', enter: 'Interact', loop: 'Pray_Stand', exit: null, msg: '작은 초에 불을 밝혔어요.' },
};
const SPOTS = [];
for (const [kind, list] of Object.entries(ACT)) for (const [x, z, yaw] of list) SPOTS.push({ kind, x, z, yaw, taken: null });
const OUT = MAP.out(BLD);
const SPAWN = LAYOUT.spawn.plaza;

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
    this.mixer.addEventListener('loop', e => { if (this.onLoop) this.onLoop(e.action); });
    this.mixer.addEventListener('finished', () => { if (this.onFinish) { const f = this.onFinish; this.onFinish = null; f(); } });
    this.root.rotation.order = 'YXZ'; scene.add(this.root); this.play('Idle');
  }
  play(n, fade = 0.25) {
    const a = this.acts[n]; if (!a || this.cur === a) return;
    a.reset().setEffectiveTimeScale(1).setEffectiveWeight(1).fadeIn(fade).play();
    if (this.cur) this.cur.fadeOut(fade);
    this.cur = a; this.curName = n;
  }
  place(x, z, yaw) { this.pos.set(x, groundH(x, z), z); if (yaw !== undefined) this.yaw = yaw; this.sync(); }
  glideTo(x, z, yaw, dur, done) {   // 자리로 순간이동하지 않고 살짝 걸어 들어가며 돌아섬
    const d = Math.hypot(x - this.pos.x, z - this.pos.z);
    if (d < 0.02 && (yaw === undefined || Math.abs(Math.atan2(Math.sin(yaw - this.yaw), Math.cos(yaw - this.yaw))) < 0.05)) { this.place(x, z, yaw); done && done(); return; }
    this.glide = { x0: this.pos.x, z0: this.pos.z, y0: this.yaw, x1: x, z1: z, y1: yaw === undefined ? this.yaw : yaw, t: 0, dur: Math.max(0.35, dur || d / 1.2), done };
    if (d > 0.08) { this.play('Walking_A', 0.25); this.cur && this.cur.setEffectiveTimeScale(0.7); }
  }
  sync() {
    this.root.position.copy(this.pos); this.root.position.y += this.jy || 0; this.root.rotation.y = this.yaw;
    const th = this.rollA || 0; this.root.rotation.x = th;   // 2단 점프 앞구르기: 몸 가운데를 축으로 돌도록 발밑 위치를 보정
    if (th) { const c = ROLL_C, sn = Math.sin(th); this.root.position.x -= c * sn * Math.sin(this.yaw); this.root.position.z -= c * sn * Math.cos(this.yaw); this.root.position.y += c * (1 - Math.cos(th)); }
  }
  turnTo(yaw, dt, k = 8) { let d = yaw - this.yaw; d = Math.atan2(Math.sin(d), Math.cos(d)); this.yaw += d * Math.min(1, dt * k); }
  step(dx, dz, sp, dt) {
    const nx = this.pos.x + dx * sp * dt, nz = this.pos.z + dz * sp * dt;
    if (FOREST && this === player && this.pos.y > groundH(this.pos.x, this.pos.z) + 0.3) {   // 발판 위·공중에서는 땅의 바위·뿌리는 상관없고 큰 나무 줄기만 막음
      if (!trunkBlocked(nx, nz)) { this.pos.x = nx; this.pos.z = nz; return true; }
      if (!trunkBlocked(nx, this.pos.z)) { this.pos.x = nx; return true; }
      if (!trunkBlocked(this.pos.x, nz)) { this.pos.z = nz; return true; }
      return false;
    }
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
  hold(type) {   // 손에 드는 소품 (책·지팡이)
    this.unhold();
    const bone = (this.root.getObjectByName(type === 'book' ? 'handslotl' : 'handslotr') || this.root.getObjectByName(type === 'book' ? 'handslot.l' : 'handslot.r')); if (!bone) return;
    const g = new THREE.Group();
    if (type === 'book') {
      const cover = new THREE.MeshToonMaterial({ color: [0x7A2E2E, 0x2E4E7A, 0x3A6A3A, 0x5A3A6A][Math.floor(Math.random() * 4)], gradientMap: grad }), page = new THREE.MeshToonMaterial({ color: 0xF4ECD8, gradientMap: grad });
      for (const s of [-1, 1]) {
        const c = new THREE.Mesh(new THREE.BoxGeometry(0.34, 0.03, 0.46), cover); c.position.set(s * 0.17, 0, 0); c.rotation.z = -s * 0.18; g.add(c);
        const p = new THREE.Mesh(new THREE.BoxGeometry(0.31, 0.05, 0.42), page); p.position.set(s * 0.16, 0.03, 0); p.rotation.z = -s * 0.18; g.add(p);
      }
      g.position.set(0.25, 0.1, 0.15); g.rotation.set(-1.0, 0, 0.3);
    } else {
      const w = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.04, 0.9, 6), new THREE.MeshToonMaterial({ color: 0x5A3A22, gradientMap: grad })); w.position.y = 0.35; g.add(w);
      const tip = new THREE.Mesh(new THREE.SphereGeometry(0.07, 10, 8), new THREE.MeshBasicMaterial({ color: 0xBFE4FF })); tip.position.y = 0.82; g.add(tip); glowMats.push(tip.material);
      g.rotation.set(1.2, 0, 0);
    }
    bone.add(g); this.held = g;
  }
  unhold() { if (this.held) { this.held.parent && this.held.parent.remove(this.held); this.held.traverse(o => { if (o.geometry) o.geometry.dispose(); }); this.held = null; } }
  doAction(spot, onDone) {
    if (spot.kind === 'library_read') this.hold('book'); else if (spot.kind === 'magic_cast') this.hold('wand');
    const A = ACTION_INFO[spot.kind]; this.acting = spot; this.mode = this.mode || null; this.path = null;
    const loopName = (this.mode && A.modes && A.modes[this.mode].loop) || A.loop;
    const loop = () => { if (this.acting !== spot) return; this.play(loopName, 0.6); const ts = this.mode && A.modes[this.mode].speed; if (ts && this.cur) this.cur.setEffectiveTimeScale(ts); };
    this.glideTo(spot.x, spot.z, spot.yaw, null, () => {
      if (this.acting !== spot) return;
      this.play('Idle', 0.25);
      if (A.enter && this.acts[A.enter]) { setTimeout(() => { if (this.acting !== spot) return; this.play(A.enter, 0.45); this.onFinish = loop; }, 180); } else loop();
    });
    onDone && onDone(A);
  }
  endAction(after) {
    this.unhold();
    const spot = this.acting; if (!spot) { after && after(); return; }
    const A = ACTION_INFO[spot.kind]; this.acting = null; if (spot.taken === this) spot.taken = null;
    this.mode = null; this.glide = null;
    const _after = after; after = () => {
      const p = blockedR(this.pos.x, this.pos.z, RAD) ? freeSpotNear(this.pos.x, this.pos.z, 1.5) : null;
      if (p) this.glideTo(p[0], p[1], undefined, null, () => { this.play('Idle', 0.3); _after && _after(); }); else _after && _after();
    };
    if (A.exit && this.acts[A.exit]) { this.play(A.exit, 0.45); this.onFinish = () => { this.play('Idle', 0.4); after && after(); }; }
    else { this.onFinish = null; this.play('Idle'); after && after(); }
  }
  update(dt) {
    this.mixer.update(dt);
    if (this.glide) {
      const g = this.glide; g.t += dt; const k = Math.min(1, g.t / g.dur), e = k * k * (3 - 2 * k);
      this.pos.x = g.x0 + (g.x1 - g.x0) * e; this.pos.z = g.z0 + (g.z1 - g.z0) * e;
      let dy = g.y1 - g.y0; dy = Math.atan2(Math.sin(dy), Math.cos(dy)); this.yaw = g.y0 + dy * e;
      if (k >= 1) { this.glide = null; g.done && g.done(); }
    }
    if (FOREST && this === player && course) { forestStep(this, dt); this.sync(); return; }
    const gy = groundH(this.pos.x, this.pos.z), dyv = gy - this.pos.y;
    this.pos.y += dyv * Math.min(1, dt * (dyv > 0 ? 9 : 7));   // 올라갈 때·내려갈 때 부드럽게
    if (this.air) airStep(this, dt, gy);
    this.sync();
  }
}

// ---------------------------------------------------------------- 주민
class Villager extends Actor {
  constructor(def, model, home) { super(def, model); this.home = home; this.state = 'idle'; this.t = 1 + Math.random() * 4; }
  choose() {
    const r = Math.random(); let tgt = null; this.plan = null;
    if (r < 0.45) {
      const kinds = MAP.npcKinds;
      const kind = kinds[Math.floor(Math.random() * kinds.length)];
      const free = SPOTS.filter(s => s.kind === kind && !s.taken);
      if (free.length) { const s = free[Math.floor(Math.random() * free.length)]; s.taken = this; this.plan = s; tgt = [s.x, s.z]; }
    }
    if (!tgt) {
      const pools = [...Object.values(OUT), [this.home]];
      const pool = pools[Math.floor(Math.random() * pools.length)]; const p = pool[Math.floor(Math.random() * pool.length)];
      tgt = [p[0] + (Math.random() - 0.5) * 0.8, p[1] + (Math.random() - 0.5) * 0.8]; this.cheer = pool === OUT[MAP.cheerPool] && Math.random() < 0.4;
    }
    if (this.goTo(tgt[0], tgt[1])) this.state = 'walk';
    else { if (this.plan) this.plan.taken = null; this.plan = null; this.state = 'idle'; this.t = 2; }
  }
  update(dt) {
    if (this.state === 'idle') { this.t -= dt; if (this.t <= 0) this.choose(); }
    else if (this.state === 'walk') {
      if (this.hurry) this.play('Running_A'); else { this.play('Walking_A'); if (this.cur) this.cur.setEffectiveTimeScale(0.9); }
      if (this.follow(dt, this.hurry ? RUN * 0.85 : WALK * 0.8)) {
        this.hurry = false;
        if (this.plan) { this.state = 'act'; this.t = this.plan.kind === 'temple_donate' ? 6 + Math.random() * 4 : this.plan.kind === 'church_choir' ? 9999 : 25 + Math.random() * 35; this.doAction(this.plan); if (this.plan.kind === 'cathedral_candle') lightCandle(); if (this.plan.kind === 'temple_incense') smoke.puff(); }
        else { this.state = 'idle'; this.t = 6 + Math.random() * 14; if (this.cheer) { this.play('Cheer', 0.3); this.onFinish = () => this.play('Idle'); } else this.play('Idle'); }
      }
    } else if (this.state === 'act') { this.t -= dt; if (this.t <= 0) { this.state = 'busy'; this.endAction(() => { this.state = 'idle'; this.t = 1; }); } }
    if (player && this.state === 'walk') { const px = this.pos.x - player.pos.x, pz = this.pos.z - player.pos.z, pd = Math.hypot(px, pz); if (pd < 0.6 && pd > 0.01) this.step(px / pd, pz / pd, 0.6, dt); }
    super.update(dt);
  }
}

// ---------------------------------------------------------------- 낙엽·향 연기·촛불
function makeMotes(n = 260) {   // 마법학교: 천천히 떠오르는 빛 먼지·반딧불
  const cv = document.createElement('canvas'); cv.width = cv.height = 64; const g2 = cv.getContext('2d');
  const gr = g2.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.3, 'rgba(255,240,200,0.8)'); gr.addColorStop(1, 'rgba(255,220,150,0)');
  g2.fillStyle = gr; g2.fillRect(0, 0, 64, 64);
  const geo = new THREE.BufferGeometry(), pos = new Float32Array(n * 3), col = new Float32Array(n * 3), L = [];
  const pal = [new THREE.Color('#FFE6A0'), new THREE.Color('#A8D8FF'), new THREE.Color('#E0B8FF'), new THREE.Color('#B8FFD0')];
  for (let i = 0; i < n; i++) { L.push({ x: (Math.random() - 0.5) * 40, y: Math.random() * 8, z: (Math.random() - 0.5) * 40, v: 0.08 + Math.random() * 0.2, w: Math.random() * 6 }); const c = pal[i % 4]; col.set([c.r, c.g, c.b], i * 3); }
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3)); geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
  const pts = new THREE.Points(geo, new THREE.PointsMaterial({ size: 0.16, map: new THREE.CanvasTexture(cv), vertexColors: true, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, fog: false }));
  pts.frustumCulled = false; scene.add(pts);
  return (dt, cx, cz, t) => {
    for (let i = 0; i < n; i++) {
      const l = L[i]; l.y += l.v * dt;
      if (l.y > 9) { l.y = 0.2; l.x = (Math.random() - 0.5) * 40; l.z = (Math.random() - 0.5) * 40; }
      const gx = cx + l.x + Math.sin(t * 0.4 + l.w) * 0.7, gz = cz + l.z + Math.cos(t * 0.35 + l.w) * 0.7;
      pos[i * 3] = gx; pos[i * 3 + 1] = groundH(gx, gz) + l.y + Math.sin(t * 1.7 + l.w) * 0.1; pos[i * 3 + 2] = gz;
    }
    geo.attributes.position.needsUpdate = true;
    pts.material.opacity = 0.6 + 0.4 * Math.sin(t * 0.9);
  };
}
function makeLeaves(n = 420) {
  const g = new THREE.PlaneGeometry(0.13, 0.09);
  const mesh = new THREE.InstancedMesh(g, new THREE.MeshLambertMaterial({ side: THREE.DoubleSide }), n); mesh.frustumCulled = false;
  const cols = (FOREST ? ['#7DBA4E', '#A6CF5A', '#5E9A3E', '#C8DE6A', '#8FC456', '#E8D06A'] : ['#D9382B', '#E8552E', '#F07A2E', '#F2C230', '#C42F2F', '#F29A38']).map(c => new THREE.Color(c));
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
  b.innerHTML = `<img src="${asset(`${MAP.portraits}${a.k}.png`)}" alt="" width="96" height="120">${a.n}<small>${a.s} · ${a.job}</small>`;
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
  const splat = texL.load(asset(MAP.splat)); splat.colorSpace = THREE.NoColorSpace; splat.flipY = false;
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
  const jobs = [['village', MAP.world], ['props', 'assets/props.glb'], ['anims', 'assets/animations/kaykit_animations.glb'], ...ANIMALS.map(a => [a.k, `${MAP.chars}${a.k}.glb`])];
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
  .then(() => {
    $('start').disabled = false; $('start').textContent = '산책 시작';
    try { const r = JSON.parse(sessionStorage.getItem('mw_resume') || 'null'); sessionStorage.removeItem('mw_resume');
      if (r && Date.now() - r.t < 120000) { const b = document.querySelector(`#pick [data-k="${r.pick}"]`); if (b) b.click(); toast('화면을 다시 불러왔어요', '그래픽 메모리가 모자라 잠깐 꺼졌어요. 기록은 그대로예요'); } } catch (e) { }
  })
  .catch(e => { $('start').textContent = '불러오지 못했어요'; console.error(e); });

// ---------------------------------------------------------------- 시작
let player = null, npcs = [], audio = null, leaves = null, started = false;
const camState = { yaw: 0, pitch: 0.42, dist: 7.5, tgt: new THREE.Vector3() };
let sitting = false, pendingAction = null;
const marker = new THREE.Mesh(new THREE.RingGeometry(0.18, 0.26, 24), new THREE.MeshBasicMaterial({ color: 0xFFF1D0, transparent: true, opacity: 0.85, depthWrite: false }));
marker.rotation.x = -Math.PI / 2; marker.visible = false; scene.add(marker);

async function startWalk() {
  await ready; if (started) return; started = true; $('btnJump').hidden = false; minimap.visible = true; document.body.classList.toggle('school', MAP.key === 'school');
  if (!audio) { audio = createAudio(MAP.key); audio.start(); } audio.setVolume(parseFloat($('vol').value));
  for (const a of ANIMALS) {
    const m = prepModel(models[a.k]);
    if (a.k === pickKey) { player = new Actor(a, m); const s = LAYOUT.spawn.plaza; player.place(s[0], s[2] + 0.6, Math.PI); }
    else { const v = new Villager(a, m, [LAYOUT.homes[a.k][0], LAYOUT.homes[a.k][2]]); const sp = OUT.walk[npcs.length % OUT.walk.length]; v.place(sp[0] + Math.random(), sp[1] + Math.random(), Math.random() * 6.28); npcs.push(v); }
  }
  if (!leaves) leaves = MAP.key === 'school' ? makeMotes() : makeLeaves(); camState.tgt.copy(player.pos); applyTime(TIME.cur);
  if (FOREST) { camState.dist = 9; camState.pitch = 0.32; $('climb').hidden = false; joy.show(); }
  $('intro').hidden = true; $('hud').hidden = false; $('help').hidden = false;
  setTimeout(() => { $('help').hidden = true; }, 15000);
  hookAudioText();
  rec.zone(MAP.baseZone);
  if (rec.visit()) { const r = rec.data; setTimeout(() => toast(r.days.length === 1 ? `${MAP.icon} ${MAP.title}에 온 걸 환영해요` : `${MAP.icon} 오늘도 와 주셨네요`, r.streak > 1 ? `${r.streak}일째 이어서 들렀어요` : '명상하고 기도하면 마음 점수가 쌓여요 (🏅)'), 1200); }
  if (TIME.cur === 'night') rec.add('night');
  updateBadge();
}
$('start').onclick = startWalk;

// ---------------------------------------------------------------- 조작
const keys = new Set();
// 휴대폰 조이스틱 (점프 맵): 왼손 엄지로 밀어서 걷기
const joy = (() => {
  const el = $('joy'), knob = el.querySelector('i'), J = { on: false, x: 0, y: 0, id: null };
  const touch = matchMedia('(pointer: coarse)').matches;
  J.show = () => { if (touch) el.hidden = false; }; J.hide = () => { el.hidden = true; J.on = false; J.x = J.y = 0; };
  const mv = e => { const r = el.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2, R = r.width / 2;
    let x = (e.clientX - cx) / R, y = (e.clientY - cy) / R; const l = Math.hypot(x, y); if (l > 1) { x /= l; y /= l; }
    J.x = Math.abs(x) < 0.12 ? 0 : x; J.y = Math.abs(y) < 0.12 ? 0 : y; knob.style.transform = `translate(${x * R * 0.55}px, ${y * R * 0.55}px)`; };
  el.addEventListener('pointerdown', e => { e.preventDefault(); e.stopPropagation(); try { el.setPointerCapture(e.pointerId); } catch (err) { } J.on = true; J.id = e.pointerId; if (player && (player.acting || sitting)) stopActing(); mv(e); });
  el.addEventListener('pointermove', e => { if (J.on && e.pointerId === J.id) mv(e); });
  const up = e => { if (e.pointerId !== J.id) return; J.on = false; J.x = J.y = 0; knob.style.transform = ''; };
  el.addEventListener('pointerup', up); el.addEventListener('pointercancel', up);
  return J;
})();
addEventListener('keydown', e => {
  if (e.target.tagName === 'INPUT') return;
  if (e.code === 'AltLeft' || e.code === 'AltRight') { e.preventDefault(); if (!e.repeat && started) jump(); return; }   // Alt = 점프 (브라우저 메뉴로 넘어가지 않게 막음)
  if (e.metaKey || e.ctrlKey) { keys.clear(); return; }   // 단축키를 누르는 동안 손 뗀 키가 '눌린 채'로 남지 않게
  keys.add(e.code);
  if (/Arrow|Key[WASD]/.test(e.code) && player && (player.acting || sitting)) stopActing();
  if (e.code === 'KeyE') { const b = $('btnAct'); if (!b.hidden) b.click(); }
  if (e.code === 'Space' && started) { e.preventDefault(); if (!e.repeat) jump(); }
  if (e.code === 'KeyM' && started) minimap.toggle();
  if (e.code === 'Escape') { minimap.close(); }
  if (e.code === 'Escape') ['recPanel', 'baptPanel', 'talkMenu', 'goMenu'].forEach(id => { $(id).hidden = true; });
});
addEventListener('keyup', e => { keys.delete(e.code); if (e.code === 'AltLeft' || e.code === 'AltRight' || e.code === 'Space') e.preventDefault(); if (e.key === 'Meta') keys.clear(); });
// 다른 창·탭으로 갔다 오면 손 뗀 키가 눌린 채로 남아 혼자 걸어가던 문제 → 그때마다 눌린 키를 비움
addEventListener('blur', () => keys.clear()); document.addEventListener('visibilitychange', () => keys.clear());
// 누른 버튼에 초점이 남아 있으면 Space·Enter가 그 버튼(예: 가 보기 메뉴)을 다시 눌러 저절로 걸어가 버림 → 누른 뒤 초점을 뺌
document.addEventListener('click', e => { const b = e.target.closest && e.target.closest('button'); if (b) setTimeout(() => b.blur(), 0); }, true);
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
  if (FOREST && player && player.pos.y > 1.4) { if (!climb.tapHint) { climb.tapHint = 1; toast('발판 위에서는 방향키(조이스틱)와 점프로 움직여요', 'Alt 점프 · 공중에서 한 번 더 = 앞구르기'); } return; }
  ndc.set(e.clientX / innerWidth * 2 - 1, -(e.clientY / innerHeight) * 2 + 1); ray.setFromCamera(ndc, cam);
  const targets = [terrainMesh, ...MAP.clickTargets.map(n => villageRoot.getObjectByName(n))].filter(Boolean);
  if (!terrainMesh) return;
  const hit = ray.intersectObjects(targets, true).find(h => h.face && h.face.normal.y > 0.6);
  if (hit) walkTo(hit.point.x, hit.point.z);
});
canvas.addEventListener('wheel', e => { camState.dist = THREE.MathUtils.clamp(camState.dist * (1 + Math.sign(e.deltaY) * 0.1), 2.5, 24); e.preventDefault(); }, { passive: false });

function walkTo(x, z, then) {
  stopActing(() => {
    if (player.goTo(x, z)) { const end = player.path[player.path.length - 1]; marker.visible = true; marker.position.set(end[0], groundH(end[0], end[1]) + 0.04, end[1]); pendingAction = then || null; }
    else toast('그곳으로 가는 길을 찾지 못했어요', '조금 움직인 뒤 다시 눌러 보거나 🆘 끼임 탈출을 써 보세요');
  });
}
$('btnGo').onclick = () => { const m = $('goMenu'), h = $('hud').getBoundingClientRect(); m.style.top = ($('hud').querySelector('.tools').getBoundingClientRect().bottom - h.top + 6) + 'px'; m.hidden = !m.hidden; $('talkMenu').hidden = true; };
// 가 보기 메뉴와 시작 화면의 맵 고르기 (맵마다 다름)
{
  const gm = $('goMenu'), tail = gm.querySelector('hr');
  for (const [k, p] of Object.entries(POI)) { const b = document.createElement('button'); b.dataset.go = k; b.textContent = p.name; gm.insertBefore(b, tail); }
  const mb = document.createElement('button'); mb.dataset.go = 'maps'; mb.textContent = '🗺️ 다른 곳으로 (맵 고르기)'; gm.append(mb);
  const box = $('maps');
  for (const k of MAP_ORDER) {
    const m = MAPS[k], b = document.createElement('button'); b.className = 'mapCard' + (k === MAPKEY ? ' on' : ''); b.setAttribute('aria-pressed', k === MAPKEY);
    b.innerHTML = `<span class="mi">${m.icon}</span><b>${m.title}</b>`;
    b.onclick = () => { if (k === MAPKEY) return; try { localStorage.setItem('mw_map', k); } catch (e) { } const q = new URLSearchParams(location.search); q.set('map', k); location.search = q.toString(); };
    box.append(b);
  }
  $('placeName').textContent = MAP.names[MAP.baseZone][0]; $('placeSub').textContent = MAP.names[MAP.baseZone][1];
  $('mapTitle').textContent = MAP.title; $('mapLead').textContent = MAP.tagline; document.title = `${MAP.title} — 마음 산책`;
  try { localStorage.setItem('mw_map', MAPKEY); } catch (e) { }
}
$('goMenu').addEventListener('click', e => {
  const b = e.target.closest('[data-go]'); if (!b || !player) return; $('goMenu').hidden = true;
  const k = b.dataset.go;
  if (k === 'rescue') { rescue(); return; }
  if (k === 'maps') { resetToIntro(); $('maps').scrollIntoView({ block: 'center' }); return; }
  if (k === 'reset') { resetToIntro(); return; }
  if (POI[k] && POI[k].tp === 'rest') { const r = course && course.rests[climb.rest]; if (!r) { toast('아직 들른 쉼터가 없어요', '큰 나무를 오르다 깃발 있는 넓은 덱에 닿으면 쉼터가 돼요'); return; } climb.used = true; teleport(r.x, r.y, r.z + 0.01); return; }
  if (POI[k] && POI[k].tp === 'down') { const j = LAYOUT.jump[0]; teleport(j.x, groundH(j.x, j.z + 1.4), j.z + 1.4); return; }
  const p = POI[k] && POI[k].home ? [LAYOUT.homes[pickKey][0], LAYOUT.homes[pickKey][2]] : POI[k].p; walkTo(p[0], p[1]);
});
const ORDER = ['dusk', 'night', 'day'];
$('btnTime').onclick = () => applyTime(ORDER[(ORDER.indexOf(TIME.cur) + 1) % 3]);
$('vol').oninput = e => audio && audio.setVolume(parseFloat(e.target.value));

// 명상 (그 자리에 앉아 호흡)
let breathT = 0;
function toggleSit() {
  if (player && player.air) return;
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
  if (player && player.acting) { if (player.acting.kind === 'church_choir') { audio && audio.setChurchChoir(false); releaseChoir(); } player.onLoop = null; player.endAction(after); $('btnAct').classList.remove('on'); $('actMsg').hidden = true; return; }
  if (after) after();
}
function startAction(spot, mode = null) {
  if (spot.taken && spot.taken !== player) { const alt = SPOTS.filter(s => s.kind === spot.kind && !s.taken).sort((a, b) => Math.hypot(a.x - player.pos.x, a.z - player.pos.z) - Math.hypot(b.x - player.pos.x, b.z - player.pos.z))[0]; if (!alt) return; spot = alt; }
  const go = () => {
    if (spot.taken && spot.taken !== player) return;
    spot.taken = player; marker.visible = false; player.mode = mode;
    const A = ACTION_INFO[spot.kind], M = mode && A.modes ? A.modes[mode] : null;
    player.doAction(spot, () => {
      showActBar(true); const b = $('btnAct'); b.hidden = false; b.classList.add('on'); b.textContent = '일어나기'; $('btnAlt').hidden = true; $('actMore').hidden = true; moreKey = '';
      $('actMsg').textContent = (M && M.msg) || A.msg; $('actMsg').hidden = false;
    });
    if (A.count) rec.add(A.count);
    count108 = 0; player.onLoop = null;
    if (spot.kind === 'temple_incense') { smoke.puff(); audio && audio.chime(); }
    if (spot.kind === 'cathedral_candle') { lightCandle(); audio && audio.chime(); }
    if (spot.kind === 'temple_bow') {
      audio && audio.moktakOnce();
      player.onLoop = act => {
        if (act !== player.acts.Bow) return; rec.add('bows');
        if (mode === 'b108') {
          count108++; $('actMsg').textContent = `📿 108배  ${count108} / 108`; if (count108 % 9 === 0) audio && audio.moktakOnce(0);
          if (count108 >= 108) { rec.add('b108'); audio && audio.ring('temple'); toast('📿 108배를 모두 마쳤어요', '수고했어요. 마음이 한결 맑아졌기를.'); stopActing(); }
        }
      };
      if (mode === 'b108') setTimeout(() => { if (player && player.mode === 'b108') $('actMsg').textContent = '📿 108배  0 / 108'; }, 900);
    }
    if (spot.kind === 'temple_donate') setTimeout(() => { audio && audio.coin(); sparkle(spot.x, spot.z, 1.2); }, 700);
    if (spot.kind === 'church_choir') { audio && audio.setChurchChoir(true); summonChoir(); $('capText').textContent = '성가대가 오르간에 맞춰 함께 노래하고 있어요. 🎵'; }
    if (spot.kind === 'library_read') setTimeout(() => { if (player && player.acting === spot) { const t = BOOK_TITLES[Math.floor(Math.random() * BOOK_TITLES.length)]; $('actMsg').textContent = `📖 ${t} — “${PASSAGES[Math.floor(Math.random() * PASSAGES.length)]}”`; } }, 1800);
    if (spot.kind === 'library_read') player.onLoop = act => { if (act === player.acts.Read && Math.random() < 0.5) { $('actMsg').textContent = `📖 “${PASSAGES[Math.floor(Math.random() * PASSAGES.length)]}”`; audio && audio.page && audio.page(); } };
    if (spot.kind === 'library_shelf') setTimeout(() => { if (player && player.acting === spot) { $('actMsg').textContent = `📚 ${BOOK_TITLES[Math.floor(Math.random() * BOOK_TITLES.length)]}을(를) 꺼냈어요. 표지가 살짝 반짝여요.`; audio && audio.page && audio.page(); sparkle(spot.x, spot.z, 1.8, 10); } }, 900);
    if (spot.kind === 'stars') setTimeout(() => { if (player && player.acting === spot) { const st = STARS[Math.floor(Math.random() * STARS.length)]; $('actMsg').textContent = `🔭 오늘 밤엔 ‘${st}’가 또렷하게 보여요. (지어낸 별자리예요)`; audio && audio.chime(); rec.add('starsSeen'); } }, 1500);
    if (spot.kind === 'hall_candle') setTimeout(() => { if (player && player.acting === spot) { floatCandle(spot.x, spot.z); audio && audio.chime(); } }, 900);
    if (spot.kind === 'magic_cast') { castT = 0; }
    if (spot.kind === 'cathedral_baptism') setTimeout(() => { if (player && player.acting === spot) { audio && audio.bless(); sparkle(spot.x, spot.z, 1.6, 40); openBaptism(); } }, 1600);
  };
  if (Math.hypot(spot.x - player.pos.x, spot.z - player.pos.z) < 0.6) go();
  else walkTo(spot.x, spot.z, go);
}
let count108 = 0;
function showActBar(on) { $('actBar').hidden = !on; }
$('btnAct').onclick = () => { if (!player) return; if (player.acting) { stopActing(); return; } if (nearSpot) startAction(nearSpot); };
$('btnAlt').onclick = () => { if (!player || player.acting || !nearSpot) return; const A = ACTION_INFO[nearSpot.kind]; if (A.modes) startAction(nearSpot, Object.keys(A.modes)[0]); };
function nearest(kind) { return SPOTS.filter(s => s.kind === kind && !s.taken).sort((a, b) => Math.hypot(a.x - player.pos.x, a.z - player.pos.z) - Math.hypot(b.x - player.pos.x, b.z - player.pos.z))[0] || null; }
// 그 장소에서 할 수 있는 일 (멀리 있어도 누르면 그 자리로 걸어가서 시작)
const ZONE_ACTS = MAP.zoneActs;
let moreKey = '';
function setMore(list) {
  const key = list.map(x => x.join(':')).join('|'); if (key === moreKey) return; moreKey = key;
  const box = $('actMore'); box.innerHTML = '';
  for (const [kind, mode] of list) {
    const A = ACTION_INFO[kind], b = document.createElement('button');
    b.className = 'act' + (mode ? ' alt' : ''); b.textContent = mode ? A.modes[mode].label : A.label;
    b.onclick = () => { if (!player || player.acting) return; const sp = nearest(kind); if (sp) startAction(sp, mode || null); else { $('actMsg').textContent = '지금은 자리가 모두 찼어요. 조금 뒤에 다시 해 보세요.'; $('actMsg').hidden = false; setTimeout(() => { if (!player.acting) $('actMsg').hidden = true; }, 2000); } };
    box.append(b);
  }
  box.hidden = !list.length;
}
function updateActionButton() {
  if (!player || player.acting) return;
  let best = null, bd = 2.2;
  for (const s of SPOTS) { if (FOREST && (s.kind === 'forest_view' ? player.pos.y < LAYOUT.top - 1 : player.pos.y > groundH(player.pos.x, player.pos.z) + 0.5)) continue; const d = Math.hypot(s.x - player.pos.x, s.z - player.pos.z); if (d < bd && !s.taken) { bd = d; best = s; } }
  if (!best) for (const it of LAYOUT.interiors) if (insideRect(it, player.pos.x, player.pos.z)) best = MAP.roofKind[it.roof] ? nearest(MAP.roofKind[it.roof]) : null;
  nearSpot = best; const b = $('btnAct'), b2 = $('btnAlt');
  if (best) {
    const A = ACTION_INFO[best.kind]; b.hidden = false; b.textContent = A.label;
    if (A.modes) { const m = Object.values(A.modes)[0]; b2.hidden = false; b2.textContent = m.label; } else b2.hidden = true;
  } else { b.hidden = true; b2.hidden = true; }
  // 그 장소 안이면 할 수 있는 다른 일도 함께 보여 줌
  const zl = (ZONE_ACTS[zoneNow] || []).filter(([k, m]) => !(best && best.kind === k && (!m || ACTION_INFO[k].modes)));
  setMore(sitting ? [] : zl);
  showActBar(!sitting && (!!best || zl.length > 0));
}

// ---------------------------------------------------------------- 자막
let zoneNow = MAP.baseZone, ttsOn = false, lastLine = -1;
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
$('btnNext').onclick = () => audio && (MAP.key === 'school' ? audio.nextSchool(zoneNow) : audio.nextSong(zoneNow));
$('btnBell').onclick = () => audio && audio.ring(zoneNow);
function setZone(z) {
  if (z === zoneNow) return; zoneNow = z; if (started) rec.zone(z);
  $('caption').hidden = z === MAP.baseZone;
  $('ttsWrap').hidden = z !== 'temple'; $('btnNext').hidden = !(z === 'church' || z === 'cathedral' || (MAP.key === 'school' && z !== MAP.baseZone));
  if (z !== 'temple' && 'speechSynthesis' in window) speechSynthesis.cancel();
  if (z === 'temple') { $('capTitle').textContent = '마하반야바라밀다심경 · 목탁에 맞춰 독경하고 있어요'; $('capText').textContent = ''; lastLine = -1; }
  if (z === 'church') { $('capTitle').textContent = '♪ ' + (songTitle.church || '오르간 찬송가'); $('capText').textContent = '오르간이 찬송가와 크리스마스 캐럴을 연주하고 있어요.'; }
  if (z === 'cathedral') { $('capTitle').textContent = '♪ ' + (songTitle.cathedral || '성가대'); $('capText').textContent = '성가대가 노래하고, 종소리가 가끔 울려요.'; }
  if (z === 'hall') { $('capTitle').textContent = '♪ ' + (songTitle.hall || '촛불 아래의 왈츠'); $('capText').textContent = '천장 위로 촛불이 떠 있고, 하프와 첼레스타가 조용히 연주해요.'; }
  if (z === 'library') { $('capTitle').textContent = '♪ ' + (songTitle.library || '책장 사이의 꿈'); $('capText').textContent = '책장 넘기는 소리, 시계 소리, 멀리서 들려오는 은은한 선율.'; }
  $('btnBell').hidden = FOREST;
  if (z === 'canopy') { $('capTitle').textContent = '🌳 하늘 정원'; $('capText').textContent = '꼭대기에 올랐어요. 바람 소리를 들으며 쉬어 가요. 내려갈 때는 가 보기 → 땅으로 내려가기.'; }
  if (z === 'tower') { $('capTitle').textContent = '♪ ' + (songTitle.tower || '별의 노래'); $('capText').textContent = '망원경으로 별자리를 찾아보세요.'; }
  const nm = MAP.names[z] || MAP.names[MAP.baseZone]; $('placeName').textContent = nm[0]; $('placeSub').textContent = nm[1];
}

// ---------------------------------------------------------------- 끼임 탈출 · 처음으로
function freeSpotNear(x, z, maxR = 8) {   // 가까운 빈자리를 나선형으로 찾기
  if (!blockedR(x, z, RAD + 0.1)) return [x, z];
  for (let r = 0.3; r <= maxR; r += 0.3) {
    const n = Math.ceil(r * 8);
    for (let k = 0; k < n; k++) { const a = k / n * Math.PI * 2, px = x + Math.cos(a) * r, pz = z + Math.sin(a) * r; if (!blockedR(px, pz, RAD + 0.1) && nav.find(px, pz, SPAWN[0], SPAWN[2])) return [px, pz]; }
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
      for (let r = 0.6; r <= 6 && !p; r += 0.4) for (let k = 0; k < 16 && !p; k++) { const a = k / 16 * Math.PI * 2, x = player.pos.x + Math.cos(a) * r, z = player.pos.z + Math.sin(a) * r; if (!blockedR(x, z, RAD + 0.1)) { const q = nav.find(x, z, SPAWN[0], SPAWN[2]); if (q) p = [x, z]; } }
    }
    if (!p) { const s = LAYOUT.spawn.plaza; p = [s[0], s[2] + 0.6]; }
    player.place(p[0], p[1]); camState.tgt.set(player.pos.x, player.pos.y + 0.7, player.pos.z);
    $('actMsg').textContent = '빠져나왔어요!'; $('actMsg').hidden = false; setTimeout(() => { if (!player || !player.acting) $('actMsg').hidden = true; }, 1800);
  });
}
function resetToIntro() {   // 처음 화면(동물 고르기)으로
  if (!started) return; $('btnJump').hidden = true; minimap.visible = false; $('climb').hidden = true; joy.hide();
  if (sitting) { sitting = false; $('btnSit').classList.remove('on'); $('btnSit').textContent = '명상하기'; $('breath').hidden = true; }
  for (const a of [player, ...npcs]) { if (!a) continue; a.mixer.stopAllAction(); a.mixer.uncacheRoot(a.root); scene.remove(a.root); a.unhold && a.unhold();
    a.root.traverse(o => { if (o.isSkinnedMesh && o.skeleton) o.skeleton.dispose(); if (o.material && o.material !== outlineMat) o.material.dispose(); }); }   // 다시 시작할 때마다 뼈 텍스처가 쌓이던 것 정리
  SPOTS.forEach(s => { s.taken = null; });
  player = null; npcs = []; pendingAction = null; nearSpot = null; marker.visible = false; wasIndoor = null;
  for (const r of Object.values(roofs)) if (r) r.visible = true;
  if ('speechSynthesis' in window) speechSynthesis.cancel();
  audio && audio.setLevels(Object.fromEntries([[MAP.baseZone, 1], ...MAP.zones.map(z => [z, 0])])); setZone(MAP.baseZone);
  ['hud', 'caption', 'actMsg', 'help', 'goMenu', 'btnAct', 'actBar', 'talkMenu', 'recPanel', 'baptPanel'].forEach(id => { $(id).hidden = true; });
  audio && audio.setChurchChoir(false); bubbles.splice(0).forEach(b => b.el.remove()); rec.save();
  $('intro').hidden = false; started = false;
}

// ---------------------------------------------------------------- 마음 기록 · 업적 · 보상
const toastQ = []; let toastBusy = false;
function toast(title, sub = '') { toastQ.push([title, sub]); if (!toastBusy) nextToast(); }
function nextToast() {
  const it = toastQ.shift(); if (!it) { toastBusy = false; return; } toastBusy = true;
  const t = $('toast'); t.innerHTML = ''; t.append(document.createTextNode(it[0])); if (it[1]) { const sm = document.createElement('small'); sm.textContent = it[1]; t.append(sm); }
  t.hidden = false; setTimeout(() => { t.hidden = true; setTimeout(nextToast, 300); }, 3200);
}
const rec = createRecords(
  a => { toast(`${a.icon} 업적: ${a.name}`, a.desc); audio && audio.chime(); },
  (lv, L) => { toast(`${L[2]} ${L[1]} 단계가 되었어요`, (REWARDS.find(r => r[0] === lv) || [0, '마음 점수가 쌓였어요'])[1]); audio && audio.bless(); updateBadge(); }
);
function updateBadge() { const L = LEVELS[rec.level()]; $('lvBadge').textContent = `${L[2]} ${L[1]}`; }
updateBadge();
const fmtT = s => s >= 3600 ? `${Math.floor(s / 3600)}시간 ${Math.floor(s % 3600 / 60)}분` : `${Math.floor(s / 60)}분 ${Math.floor(s % 60)}초`;
function renderRecords() {
  const r = rec.data, p = rec.points(), lv = rec.level(), L = LEVELS[lv], N = LEVELS[lv + 1];
  const pct = N ? Math.round((p - L[0]) / (N[0] - L[0]) * 100) : 100;
  $('recLevel').innerHTML = `<div class="lvl"><span class="ic">${L[2]}</span><div style="flex:1"><b>${L[1]}</b> · 마음 점수 ${p}${N ? ` <small>(다음 ${N[2]} ${N[1]}까지 ${N[0] - p})</small>` : ''}<div class="bar"><i style="width:${pct}%"></i></div></div></div>`;
  const tt = r.todayD === new Date().toDateString() ? r.todayT : r.todayT;
  const st = [['명상', fmtT(r.t.meditate)], ['기도', fmtT(r.t.pray)], ['책 읽기', fmtT(r.t.read || 0)], ['마법 연습', (r.n.spells || 0) + '번'], ['점프', (r.n.jumps || 0) + '번 (2단 ' + (r.n.flash || 0) + ')'], ['숲 꼭대기', (r.n.forestTop || 0) + '번' + ((r.rec || {}).forestTime ? ' · 최고 ' + Math.floor(r.rec.forestTime / 60) + '분 ' + (r.rec.forestTime % 60) + '초' : '')], ['절한 시간', fmtT(r.t.bowTime)], ['성가대', fmtT(r.t.sing)], ['절', r.n.bows + '번'], ['108배', r.n.b108 + '번'], ['목탁', r.n.moktak + '번'], ['시주', r.n.donate + '번'], ['촛불·향', (r.n.candle + r.n.incense) + '번'], ['들른 날', r.days.length + '일'], ['연속', r.streak + '일 (최고 ' + r.best + ')'], ['오늘 명상', fmtT((tt && tt.meditate) || 0)]];
  $('recStats').innerHTML = st.map(([k, v]) => `<div>${k}<b>${v}</b></div>`).join('');
  $('recAch').innerHTML = ACH.map(a => {
    const got = r.got[a.id]; let pr = '';
    if (!got && a.prog) { const [c, m, f] = a.prog(r); pr = `<small>${f ? f(c) : Math.floor(c)} / ${f ? f(m) : m}</small>`; }
    return `<div class="${got ? 'got' : ''}"><span class="i">${a.icon}</span><span><b>${a.name}</b>${a.desc}${got ? `<small>${got}</small>` : pr}</span></div>`;
  }).join('');
  $('recRewards').innerHTML = REWARDS.map(([l, t]) => `<li class="${lv >= l ? 'got' : ''}">${LEVELS[l][2]} ${LEVELS[l][1]}: ${t}</li>`).join('');
}
$('btnRec').onclick = () => { renderRecords(); $('recPanel').hidden = false; };
document.querySelectorAll('[data-close]').forEach(b => b.onclick = () => { $(b.dataset.close).hidden = true; });
document.querySelectorAll('.sheet').forEach(sh => sh.addEventListener('click', e => { if (e.target === sh) sh.hidden = true; }));
addEventListener('beforeunload', () => rec.save());
addEventListener('visibilitychange', () => { if (document.hidden) rec.save(); });

// 마법학교: 촛불 띄우기, 마법 연습 빛 방울
const floaters = [];
function floatCandle(x, z) {
  const g = new THREE.Group();
  g.add(new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 0.28, 8), new THREE.MeshToonMaterial({ color: 0xF6EFD8 })));
  const fl = new THREE.Mesh(new THREE.SphereGeometry(0.045, 8, 6), new THREE.MeshBasicMaterial({ color: 0xFFD08A })); fl.scale.set(1, 1.8, 1); fl.position.y = 0.2; g.add(fl);
  g.position.set(x, groundH(x, z) + 1.2, z); scene.add(g); floaters.push({ g, t: 0, top: 5.6 + Math.random() * 1.6, x0: x, z0: z, w: Math.random() * 6 });
}
let castT = 0;
function updateMagic(dt, t) {
  for (const f of floaters) { f.t += dt; const k = Math.min(1, f.t / 8); f.g.position.y += ((f.top - f.g.position.y) * 0.4) * dt; f.g.position.x = f.x0 + Math.sin(t * 0.3 + f.w) * 0.6 * k; f.g.position.z = f.z0 - k * 2 + Math.cos(t * 0.25 + f.w) * 0.6 * k; }
  if (player && player.acting && player.acting.kind === 'magic_cast') {
    castT += dt;
    if (Math.random() < dt * 14) {
      const a = player.yaw, hx = player.pos.x + Math.sin(a) * 0.5, hz = player.pos.z + Math.cos(a) * 0.5;
      const sp = new THREE.Sprite(sparkMat.clone()); sp.material.color.setHSL(Math.random(), 0.7, 0.75); sp.scale.setScalar(0.08 + Math.random() * 0.1);
      sp.position.set(hx + (Math.random() - 0.5) * 0.3, player.pos.y + 1.0 + Math.random() * 0.3, hz + (Math.random() - 0.5) * 0.3); scene.add(sp);
      sparkles.push({ sp, v: 0.6 + Math.random() * 0.9, life: 1.6 + Math.random(), t: 0, wob: Math.random() * 6 });
    }
    if (castT > 6) { castT = 0; rec.add('spells'); audio && audio.chime(); }
  }
}

// 반짝이 (시주·세례·업적)
const sparkles = [];
const glowDot = (() => { const c = document.createElement('canvas'); c.width = c.height = 64; const g = c.getContext('2d'); const r = g.createRadialGradient(32, 32, 0, 32, 32, 32); r.addColorStop(0, 'rgba(255,255,255,1)'); r.addColorStop(0.35, 'rgba(255,255,255,0.7)'); r.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = r; g.fillRect(0, 0, 64, 64); return new THREE.CanvasTexture(c); })();
const sparkMat = new THREE.SpriteMaterial({ map: glowDot, color: 0xFFE7A0, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, fog: false });
function sparkle(x, z, h = 1.2, n = 24) {
  const y = groundH(x, z);
  for (let i = 0; i < n; i++) {
    const sp = new THREE.Sprite(sparkMat.clone()); sp.scale.setScalar(0.08 + Math.random() * 0.08);
    sp.position.set(x + (Math.random() - 0.5) * 0.6, y + 0.4 + Math.random() * h, z + (Math.random() - 0.5) * 0.6); scene.add(sp);
    sparkles.push({ sp, v: 0.3 + Math.random() * 0.5, life: 1.4 + Math.random() * 1.2, t: 0, wob: Math.random() * 6 });
  }
}
function updateSparkles(dt) {
  for (let i = sparkles.length - 1; i >= 0; i--) {
    const s = sparkles[i]; s.t += dt; s.sp.position.y += s.v * dt; s.sp.position.x += Math.sin(s.t * 3 + s.wob) * 0.004;
    s.sp.material.opacity = Math.max(0, 1 - s.t / s.life) * (0.6 + 0.4 * Math.sin(s.t * 12 + s.wob));
    if (s.t > s.life) { scene.remove(s.sp); s.sp.material.dispose(); sparkles.splice(i, 1); }
  }
}
// 단계 보상: 빛 방울(2) · 반딧불(3) · 꽃잎(5) · 빛 고리(7)
const aura = (() => {
  const n = 14, g = new THREE.Group(), dots = [];
  for (let i = 0; i < n; i++) { const m = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowDot, color: i % 3 ? 0xFFE08A : 0xB8FFB0, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, fog: false })); m.scale.setScalar(0.07); g.add(m); dots.push({ m, a: Math.random() * 6.28, r: 0.5 + Math.random() * 0.6, h: 0.3 + Math.random() * 1.3, s: 0.3 + Math.random() * 0.5 }); }
  const halo = new THREE.Mesh(new THREE.TorusGeometry(0.28, 0.025, 8, 32), new THREE.MeshBasicMaterial({ color: 0xFFE7A0, transparent: true, opacity: 0.85, fog: false }));
  halo.rotation.x = Math.PI / 2; g.add(halo); scene.add(g);
  const petals = [];
  return {
    update(dt, t) {
      const lv = rec.level(); g.visible = !!player; if (!player) return;
      g.position.copy(player.pos);
      const calm = sitting || !!player.acting, showDots = (lv >= 2 && calm) || lv >= 3;
      dots.forEach((d, i) => {
        d.m.visible = showDots && (calm || i < 6);
        d.a += dt * d.s * (calm ? 0.7 : 1.2);
        const r = calm ? d.r : 0.9 + d.r * 0.6;
        d.m.position.set(Math.cos(d.a) * r, d.h + Math.sin(t * 1.3 + i) * 0.15, Math.sin(d.a) * r);
        d.m.material.opacity = (0.5 + 0.5 * Math.sin(t * 2.2 + i * 1.7)) * (calm ? 0.9 : 0.6);
      });
      halo.visible = lv >= 7; halo.position.y = 1.62 + Math.sin(t * 1.5) * 0.03;
      if (lv >= 5 && player.curName && /Walk|Run/.test(player.curName) && Math.random() < dt * 9) {
        const p = new THREE.Sprite(new THREE.SpriteMaterial({ color: Math.random() < 0.5 ? 0xFFB0C8 : 0xFFD8E4, transparent: true, depthWrite: false }));
        p.scale.set(0.09, 0.06, 1); p.position.set(player.pos.x + (Math.random() - 0.5) * 0.4, player.pos.y + 0.1, player.pos.z + (Math.random() - 0.5) * 0.4); scene.add(p);
        petals.push({ p, t: 0, vx: (Math.random() - 0.5) * 0.4, vz: (Math.random() - 0.5) * 0.4 });
      }
      for (let i = petals.length - 1; i >= 0; i--) {
        const q = petals[i]; q.t += dt; q.p.position.x += q.vx * dt; q.p.position.z += q.vz * dt; q.p.position.y += (q.t < 0.4 ? 0.5 : -0.15) * dt;
        q.p.material.rotation += dt * 2; q.p.material.opacity = Math.max(0, 1 - q.t / 2.2);
        if (q.t > 2.2) { scene.remove(q.p); q.p.material.dispose(); petals.splice(i, 1); }
      }
    },
  };
})();

// ---------------------------------------------------------------- 성가대
function summonChoir() {
  const spots = SPOTS.filter(s => s.kind === 'church_choir' && !s.taken);
  const free = npcs.filter(v => v.state === 'idle' || (v.state === 'walk' && !v.plan) || (v.state === 'walk' && v.plan && v.plan.kind !== 'church_choir'))
    .sort((a, b) => a.pos.distanceTo(player.pos) - b.pos.distanceTo(player.pos)).slice(0, Math.min(6, spots.length));
  free.forEach((v, i) => {
    const s = spots[i]; if (!s) return;
    if (v.plan && v.plan.taken === v) v.plan.taken = null;
    s.taken = v; v.plan = s; v.choir = true; v.hurry = true;
    if (v.goTo(s.x, s.z)) v.state = 'walk'; else { s.taken = null; v.plan = null; v.choir = false; }
    setTimeout(() => bubble(v, ['🎵', '🎶', '😊', '🙌'][i % 4], true), 400 + i * 300);
  });
}
function releaseChoir() {
  npcs.forEach(v => { if (v.choir) { v.choir = false; if (v.state === 'act') v.t = 1 + Math.random() * 4; else if (v.plan && v.plan.kind === 'church_choir') { v.plan.taken = null; v.plan = null; v.state = 'idle'; v.t = 1; } } });
}
// 음표가 떠오름
function choirNotes(dt) {
  if (!player || !player.acting || player.acting.kind !== 'church_choir') return;
  if (Math.random() < dt * 3) {
    const singers = [player, ...npcs.filter(v => v.acting && v.acting.kind === 'church_choir')]; const a = singers[Math.floor(Math.random() * singers.length)];
    const el = document.createElement('div'); el.className = 'bubble emo'; el.style.background = 'transparent'; el.style.boxShadow = 'none'; el.textContent = Math.random() < 0.5 ? '♪' : '♫';
    el.style.color = ['#D9572E', '#5A3EA8', '#2E7A4A', '#C8902A'][Math.floor(Math.random() * 4)]; el.classList.add('note');
    $('bubbles').append(el); bubbles.push({ el, a, t: 0, life: 2.2, rise: true, dx: (Math.random() - 0.5) * 30 });
  }
}

// ---------------------------------------------------------------- 세례 · 오늘의 운세
function openBaptism() {
  let nm = ''; try { nm = localStorage.getItem('mw_name') || ''; } catch (e) { }
  $('baptName').value = nm; $('baptAsk').hidden = false; $('baptOut').hidden = true; $('baptPanel').hidden = false;
  setTimeout(() => $('baptName').focus(), 50);
}
$('baptGo').onclick = () => {
  const nm = $('baptName').value.trim().slice(0, 16); if (!nm) { $('baptName').focus(); return; }
  try { localStorage.setItem('mw_name', nm); } catch (e) { }
  const sa = saintFor(nm), f = fortuneFor(nm), animal = ANIMALS.find(a => a.k === pickKey);
  const esc = t => t.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  $('baptOut').innerHTML = `<p>${esc(nm)} 님(${animal ? animal.s : ''})의 세례명은</p><div class="saint">${sa.name}</div><p>“${sa.meaning}”이라는 뜻을 담았어요.</p>
    <div class="fort"><b>오늘의 운세</b> <span class="stars">${'★'.repeat(f.stars)}${'☆'.repeat(5 - f.stars)}</span> ${f.luck}<p>${f.text}</p>
    <p>행운의 색 <b style="color:${f.color[1]}">● ${f.color[0]}</b> · 행운의 물건 <b>${f.item}</b> · 행운의 숫자 <b>${f.number}</b></p>
    <p><i>${f.word}</i></p></div><p class="hint">같은 이름이면 세례명은 늘 같고, 운세는 날마다 바뀌어요. 재미로 즐겨 주세요.</p>
    <button class="primary" data-close2>고마워요</button>`;
  $('baptAsk').hidden = true; $('baptOut').hidden = false; rec.add('baptism');
  $('baptOut').querySelector('[data-close2]').onclick = () => { $('baptPanel').hidden = true; };
  bubble(player, '💧', true); sparkle(player.pos.x, player.pos.z, 1.8, 30);
};
$('baptName').addEventListener('keydown', e => { if (e.key === 'Enter') $('baptGo').click(); e.stopPropagation(); });

// ---------------------------------------------------------------- 말하기 (정해진 말·이모티콘)
const EMOJI = ['😊', '🙏', '❤️', '🍁', '🌸', '✨', '🎵', '👋', '🙇', '😴', '👍', '☕', '🥰', '😢', '🌙', '🕊️', '🍂', '🎉'];
const PHRASES = ['안녕하세요 👋', '반가워요 😊', '고마워요 🙏', '평안하세요 🕊️', '좋은 하루 보내요 ☀️', '함께 걸어요 🍁', '같이 기도해요 🙏', '노래해요 🎵', '잠깐 쉬어 가요 ☕', '오늘도 수고했어요 💪', '잘 자요 🌙', '또 만나요 👋'];
const REPLY = { '😊': ['😊', '🥰', '👋'], '🙏': ['🙏', '🕊️', '✨'], '❤️': ['❤️', '🥰', '😊'], '👋': ['👋', '😊', '🍁'], '😢': ['🫂', '❤️', '🍵'], '🎵': ['🎶', '🎵', '😊'], '😴': ['🌙', '😴', '💤'] };
const bubbles = [];
function bubble(actor, text, emo = false, life = 3.2) {
  if (!actor) return;
  for (const b of bubbles) if (b.a === actor && !b.rise) b.t = b.life;   // 같은 동물의 말풍선은 하나만
  const el = document.createElement('div'); el.className = 'bubble' + (emo ? ' emo' : ''); el.textContent = text;
  $('bubbles').append(el); bubbles.push({ el, a: actor, t: 0, life });
}
const headV = new THREE.Vector3();
function updateBubbles(dt) {
  const W = innerWidth, H = innerHeight;
  for (let i = bubbles.length - 1; i >= 0; i--) {
    const b = bubbles[i]; b.t += dt;
    if (b.t > b.life || !b.a.root.parent) { b.el.remove(); bubbles.splice(i, 1); continue; }
    headV.copy(b.a.pos); headV.y += (b.rise ? 1.4 + b.t * 0.5 : 1.72); headV.project(cam);
    const vis = headV.z < 1 && Math.abs(headV.x) < 1.1 && Math.abs(headV.y) < 1.1;
    b.el.style.display = vis ? '' : 'none';
    b.el.style.left = ((headV.x + 1) / 2 * W + (b.dx || 0)) + 'px'; b.el.style.top = ((1 - headV.y) / 2 * H) + 'px';
    if (b.rise) b.el.style.opacity = String(Math.max(0, 1 - b.t / b.life)); else if (b.t > b.life - 0.4) b.el.classList.add('fade');
  }
}
function say(text, emo) {
  if (!player) return; bubble(player, text, emo); rec.add('emote');
  const key = emo ? text : (text.match(/\p{Extended_Pictographic}/u) || ['😊'])[0];
  const near = npcs.filter(v => v.pos.distanceTo(player.pos) < 8).sort((a, b) => a.pos.distanceTo(player.pos) - b.pos.distanceTo(player.pos)).slice(0, 2);
  near.forEach((v, i) => setTimeout(() => { const opts = REPLY[key] || [key, '😊', '👋']; bubble(v, opts[Math.floor(Math.random() * opts.length)], true); if (!v.acting && v.state === 'idle') { v.turnTo(Math.atan2(player.pos.x - v.pos.x, player.pos.z - v.pos.z), 1, 1); } }, 900 + i * 700 + Math.random() * 500));
}
$('emoGrid').innerHTML = EMOJI.map(e => `<button data-e="${e}">${e}</button>`).join('');
$('phrList').innerHTML = PHRASES.map(p => `<button data-p="${p}">${p}</button>`).join('');
$('talkMenu').addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; $('talkMenu').hidden = true; if (b.dataset.e) say(b.dataset.e, true); else say(b.dataset.p, false); });
$('btnTalk').onclick = () => { const m = $('talkMenu'); m.style.top = ($('hud').querySelector('.tools').getBoundingClientRect().bottom + 6) + 'px'; m.hidden = !m.hidden; $('goMenu').hidden = true; };
let npcChatT = 12;
function npcChatter(dt) {   // 주민들도 가끔 이모티콘을 띄움
  npcChatT -= dt; if (npcChatT > 0 || !player) return; npcChatT = 14 + Math.random() * 20;
  const near = npcs.filter(v => v.pos.distanceTo(player.pos) < 12); if (!near.length) return;
  const v = near[Math.floor(Math.random() * near.length)];
  const k = v.acting ? v.acting.kind : '';
  const pool = k.startsWith('temple') ? ['🙏', '🙇', '🕊️', '✨'] : k === 'church_choir' ? ['🎵', '🎶'] : k.includes('pew') ? ['🙏', '✨', '🕊️'] : ['😊', '🍁', '👋', '☕', '🍂', '🌸'];
  bubble(v, pool[Math.floor(Math.random() * pool.length)], true);
}

// 목탁 소리를 손짓에 맞춰
const MOK_T = 2.4, MOK_HITS = [0.15, 0.75, 1.35, 1.95];
function moktakHits() {
  for (const a of [player, ...npcs]) {
    if (!a || !a.acting || a.acting.kind !== 'temple_moktak' || a.curName !== 'Moktak') { if (a) a.mokPrev = -1; continue; }
    const t = a.cur.time % MOK_T, p = a.mokPrev ?? -1; a.mokPrev = t;
    if (p < 0) continue;
    for (const h of MOK_HITS) if ((p < h && t >= h) || (p > t && (h > p || h <= t))) {
      if (a === player) { audio && audio.moktakOnce(0.0); rec.add('moktak'); }
      else if (player && a.pos.distanceTo(player.pos) < 9) audio && audio.moktakOnce(0.0);
    }
  }
}
function recordTime(dt) {
  if (!player) return;
  if (sitting) rec.time('meditate', dt);
  else if (player.acting && !player.glide) { const A = ACTION_INFO[player.acting.kind]; if (A.rec) rec.time(A.rec, dt); }
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

// ---------------------------------------------------------------- 점프 · 2단 점프
// 땅에서 한 번 누르면 폴짝, 공중에서 한 번 더 누르면 바라보는 쪽으로 휙 날아가요 (빛 꼬리).
const GRAV = 17, JUMP_V = 5.6, DASH_V = FOREST ? 6 : 8.5, DASH_T = FOREST ? 0.3 : 0.4, DASH_UP = FOREST ? 2.4 : 3.4, ROLL_T = 0.46, ROLL_C = 0.62;   // 점프 맵은 2단 점프가 조금 짧아 발판을 맞추기 쉬움
const dashCol = MAP.key === 'school' ? 0xA8D8FF : FOREST ? 0xB8F2A0 : 0xFFB070;
function jump() {
  const p = player; if (!p || sitting || p.glide) return;
  if (p.acting) { stopActing(); return; }
  if (!p.air) {
    p.air = true; p.vy = JUMP_V; p.jy = FOREST ? 0 : Math.max(0, p.jy || 0); p.flashed = false; p.dash = null; p.fallTop = p.pos.y;
    p.play('Jump', 0.12); audio && audio.hop(); rec.add('jumps');
  } else if (!p.flashed) {
    p.flashed = true; p.vy = Math.max(p.vy, 0) + DASH_UP; p.roll = 0;
    p.dash = { x: Math.sin(p.yaw), z: Math.cos(p.yaw), t: 0 };
    audio && audio.whoosh(); rec.add('flash');
    trail(p, 14);
  }
}
function airStep(a, dt, gy) {
  a.vy -= GRAV * dt; a.jy += a.vy * dt;
  airMove(a, dt);
  if (a.jy <= 0 && a.vy < 0) {
    a.jy = 0; a.air = false; a.dash = null; a.roll = null; a.rollA = 0;
    a.play('Idle', 0.15); audio && audio.land(); puff(a.pos.x, a.pos.z);
  }
}
function airMove(a, dt) {
  if (a.dash) {
    const d = a.dash; d.t += dt; const k = 1 - d.t / DASH_T;
    if (k <= 0) a.dash = null; else { a.step(d.x, d.z, DASH_V * (0.4 + 0.6 * k), dt); if (Math.random() < 0.6) trail(a, 1); }
  }
  if (a.roll !== undefined && a.roll !== null) {
    a.roll += dt; const k = Math.min(1, a.roll / ROLL_T), e = k < 0.5 ? 2 * k * k : 1 - 2 * (1 - k) * (1 - k);
    a.rollA = e * Math.PI * 2; if (k >= 1) { a.roll = null; a.rollA = 0; }
  }
}
// ---------------------------------------------------------------- 점프 맵: 진짜 높이 (발판 위·아래)
const course = FOREST ? createCourse(scene, LAYOUT, grad, groundH) : null;
const TRUNK_C = course ? [course.goal.x, course.goal.z] : [0, 0], TRUNK_R = (LAYOUT.trunkR || 2.6) + 0.35;
function trunkBlocked(x, z) { return Math.hypot(x - TRUNK_C[0], z - TRUNK_C[1]) < TRUNK_R || Math.hypot(x, z) > LAYOUT.bound; }
const climb = { t0: null, used: false, rest: -1, done: false, top: 0 };
function forestStep(a, dt) {
  if (a.air) {
    const y0 = a.pos.y; a.vy -= GRAV * dt; let ny = y0 + a.vy * dt;
    airMove(a, dt);
    if (a.vy <= 0) { const s = course.surface(a.pos.x, a.pos.z, y0, 0.03); if (ny <= s.y) { ny = s.y; a.pos.y = ny; forestLand(a, s); return; } }
    a.pos.y = ny; a.fallTop = Math.max(a.fallTop || ny, ny);
  } else {
    const s = course.surface(a.pos.x, a.pos.z, a.pos.y, 0.4);
    if (s.y < a.pos.y - 0.18) { a.air = true; a.vy = 0; a.flashed = false; a.fallTop = a.pos.y; if (!a.acting) a.play('Jump', 0.2); }   // 발판 끝에서 걸어 나가면 떨어짐
    else { a.pos.y = s.y; a.standOn = s.it; }
  }
}
function forestLand(a, s) {
  a.air = false; a.dash = null; a.roll = null; a.rollA = 0; a.standOn = s.it;
  const fell = (a.fallTop || a.pos.y) - a.pos.y;
  if (!a.acting) a.play('Idle', 0.15); audio && audio.land(); puff(a.pos.x, a.pos.z, a.pos.y);
  if (fell > 4) { rec.add('falls'); if (fell > 7 || Math.random() < 0.35) bubble(a, ['괜찮아요!', '다시 한 칸씩', '후~ 숨 고르고', '조금만 더'][Math.floor(Math.random() * 4)]); }
  const j = s.it && s.it.j; if (!j) return;
  if (j.t === 'rest') {
    const i = course.rests.indexOf(j);
    if (i > climb.rest) { climb.rest = i; toast(`🪶 쉼터 ${i + 1}에 왔어요`, '가 보기 메뉴에서 이곳으로 다시 올 수 있어요 (순간이동)'); audio && audio.chime(); sparkle(a.pos.x, a.pos.z, 1.0, 16); }
  }
  if (j.t === 'goal' && !climb.done) forestGoal(a);
}
function forestGoal(a) {
  climb.done = true; const t = climb.t0 === null ? null : tAll - climb.t0;
  rec.add('forestTop'); if (!climb.used) rec.add('forestPure');
  const best = t !== null && !climb.used && rec.low('forestTime', Math.round(t));
  const tt = t === null ? '' : `${Math.floor(t / 60)}분 ${Math.round(t % 60)}초`;
  toast('🌳 하늘 정원에 올랐어요!', (tt ? `걸린 시간 ${tt}` : '') + (climb.used ? ' · 쉼터 순간이동을 썼어요' : best ? ' · 최고 기록!' : ''));
  audio && audio.bless(); sparkle(a.pos.x, a.pos.z, 2.0, 60);
  npcs.forEach((n, i) => setTimeout(() => n.play && n.play('Cheer'), 200 + i * 120));
}
function teleport(x, y, z) {
  stopActing(() => { player.path = null; player.air = false; player.vy = 0; player.dash = null; player.pos.set(x, y, z); player.fallTop = y; camState.tgt.set(x, y + 0.7, z); marker.visible = false; });
}
function climbHud() {
  if (!FOREST || !player) return;
  const h = Math.max(0, player.pos.y), onGround = !player.air && h < 0.7;
  if (onGround && !player.acting) { climb.t0 = null; climb.used = false; climb.done = false; }
  else if (climb.t0 === null && !climb.done && h > 0.3) climb.t0 = tAll;
  climb.top = Math.max(climb.top, h); if (camTick % 30 === 0) rec.high('forestHeight', Math.round(h * 10) / 10);
  const el = $('climb'); if (camTick % 4) return;
  const t = climb.t0 !== null && !climb.done ? tAll - climb.t0 : null, top = LAYOUT.top;
  const r = (rec.data.rec || {}), bt = r.forestTime;
  el.innerHTML = `<b>🌲 ${h.toFixed(1)}m</b> / ${top}m<i style="width:${Math.min(100, h / top * 100)}%"></i><small>${t !== null ? '⏱ ' + Math.floor(t / 60) + ':' + String(Math.floor(t % 60)).padStart(2, '0') + ' · ' : ''}${bt ? '최고 ' + Math.floor(bt / 60) + ':' + String(bt % 60).padStart(2, '0') : '아직 꼭대기 기록 없음'}${climb.used ? ' · 쉼터 씀' : ''}</small>`;
}
function trail(a, n) {
  for (let i = 0; i < n; i++) {
    const m = sparkMat.clone(); m.color.setHex(dashCol);
    const sp = new THREE.Sprite(m); sp.scale.setScalar(0.1 + Math.random() * 0.14);
    sp.position.set(a.pos.x + (Math.random() - 0.5) * 0.5, a.pos.y + (a.jy || 0) + 0.3 + Math.random() * 0.8, a.pos.z + (Math.random() - 0.5) * 0.5); scene.add(sp);
    sparkles.push({ sp, v: 0.05 + Math.random() * 0.2, life: 0.5 + Math.random() * 0.5, t: 0, wob: Math.random() * 6 });
  }
}
function puff(x, z, yy) {
  const y = yy === undefined ? groundH(x, z) : yy;
  for (let i = 0; i < 8; i++) {
    const m = sparkMat.clone(); m.color.setHex(0xEDE3D2); m.opacity = 0.5;
    const sp = new THREE.Sprite(m); sp.scale.setScalar(0.12 + Math.random() * 0.1);
    const ang = i / 8 * Math.PI * 2; sp.position.set(x + Math.cos(ang) * 0.25, y + 0.08, z + Math.sin(ang) * 0.25); scene.add(sp);
    sparkles.push({ sp, v: 0.08, life: 0.45, t: 0, wob: ang });
  }
}
$('btnJump').addEventListener('pointerdown', e => { e.preventDefault(); e.stopPropagation(); jump(); });

// ---------------------------------------------------------------- 루프
const clock = new THREE.Clock(); let tAll = 0;
const tmpV = new THREE.Vector3(), dirV = new THREE.Vector3(); const camRay = new THREE.Raycaster(); let keyStuck = 0, camTick = 0, camFree = 99, camCur = 7.5, wasIndoor = null, inK = 0;
function frame() {
  const dt = Math.min(clock.getDelta(), 0.05); tAll += dt;
  if (player) {
    let ix = 0, iz = 0;
    if (keys.has('KeyW') || keys.has('ArrowUp')) iz += 1; if (keys.has('KeyS') || keys.has('ArrowDown')) iz -= 1;
    if (keys.has('KeyA') || keys.has('ArrowLeft')) ix += 1; if (keys.has('KeyD') || keys.has('ArrowRight')) ix -= 1;
    let mag = 1; if (joy.on && (joy.x || joy.y)) { ix = -joy.x; iz = -joy.y; mag = Math.min(1, Math.hypot(joy.x, joy.y)); }
    if (keys.has('KeyQ')) camState.yaw += dt * 1.6; if (keys.has('KeyR')) camState.yaw -= dt * 1.6;
    if (keys.has('PageUp')) camState.pitch = Math.min(1.45, camState.pitch + dt); if (keys.has('PageDown')) camState.pitch = Math.max(0.05, camState.pitch - dt);
    let sp = keys.has('ShiftLeft') || keys.has('ShiftRight') ? RUN : WALK;
    if (FOREST && (player.air || player.pos.y > 0.7)) sp = player.air ? 2.9 : Math.max(sp, 2.2);   // 점프 맵: 공중·발판 위에서는 조금 더 빠르게
    if ((ix || iz) && !player.acting && !sitting && !player.glide) {
      player.path = null; pendingAction = null; marker.visible = false;
      const fy = camState.yaw + Math.PI, fx = Math.sin(fy), fz = Math.cos(fy);
      let mx = fx * iz + fz * ix, mz = fz * iz - fx * ix; const l = Math.hypot(mx, mz); mx /= l; mz /= l;
      if (!player.step(mx, mz, sp * (mag < 0.5 ? 0.6 : 1), dt)) { keyStuck += dt; if (keyStuck > 1.2) { keyStuck = 0; unstick(player, 3); } } else keyStuck = 0;
      player.turnTo(Math.atan2(mx, mz), dt, player.air ? 5 : 10); if (!player.air) player.play(sp > WALK ? 'Running_A' : 'Walking_A');
    } else if (player.path) {
      if (!player.air) player.play('Walking_A');
      if (player.follow(dt, WALK)) { marker.visible = false; player.play('Idle'); if (pendingAction) { const f = pendingAction; pendingAction = null; f(); } }
    } else if (!sitting && !player.acting && !player.glide && !player.air && player.curName !== 'Idle' && !player.onFinish) player.play('Idle');
    if (course) course.update(tAll);
    player.update(dt);
    npcs.forEach(n => n.update(dt));
    climbHud();
    separate(dt);
    moktakHits(); recordTime(dt); choirNotes(dt); npcChatter(dt); rec.tick(tAll);
    let indoor = null;
    for (const it of LAYOUT.interiors) { const r = roofs[it.roof], inn = insideRect(it, player.pos.x, player.pos.z, 0.4); if (r) r.visible = !inn; if (inn) indoor = it; }
    if (indoor !== wasIndoor) { if (indoor && !down) { camState.pitch = Math.max(camState.pitch, 0.62); } wasIndoor = indoor; }   // 들어갈 때 한 번만 살짝 올려 줌 — 그다음은 마음대로 돌려 보기
    camState.tgt.lerp(tmpV.set(player.pos.x, player.pos.y + 0.7, player.pos.z), Math.min(1, dt * 5));
    if (sitting || player.acting) camState.yaw += dt * 0.04;
    const pitch = camState.pitch, dist = camState.dist;
    const cp = Math.cos(pitch);
    dirV.set(Math.sin(camState.yaw) * cp, Math.sin(pitch), Math.cos(camState.yaw) * cp);
    inK += ((indoor ? 1 : 0) - inK) * Math.min(1, dt * 2);
    hemi.intensity = TIME[TIME.cur].hemi[2] * (1 + inK * (TIME.cur === 'night' ? (MAP.key === 'school' ? 2.2 : 1.4) : TIME.cur === 'dusk' ? 0.5 : 0.15));
    seeU.uSeeR.value += ((indoor ? 3.4 : 0.8 + camCur * 0.06) - seeU.uSeeR.value) * Math.min(1, dt * 3);
    camFree = dist;   // 가리는 벽·지붕·나무는 점무늬로 비쳐 보이니 카메라는 당기지 않고 마음대로 돌려 볼 수 있음
    camCur += (Math.min(dist, camFree) - camCur) * Math.min(1, dt * (camFree < camCur ? 12 : 3));
    cam.position.copy(camState.tgt).addScaledVector(dirV, camCur);
    const gy = groundH(cam.position.x, cam.position.z) + 0.5; if (cam.position.y < gy) cam.position.y = gy;
    cam.lookAt(camState.tgt); seeU.uCam.value.copy(cam.position); seeU.uTgt.value.copy(camState.tgt);
    marker.material.opacity = 0.5 + 0.35 * Math.sin(tAll * 5);
    if (audio) {
      const lv = Object.fromEntries([[MAP.baseZone, 1], ...MAP.zones.map(z => [z, 0])]); let best = MAP.baseZone, bv = 0.3;
      for (const [k, z] of Object.entries(Z)) {
        if (z.ymin !== undefined && player.pos.y < z.ymin) { lv[k] = 0; continue; }
        const d = Math.hypot(player.pos.x - z.center[0], player.pos.z - z.center[2]);
        const v = THREE.MathUtils.clamp((z.radius * 1.3 - d) / (z.radius * 0.7), 0, 1); lv[k] = v * v * (3 - 2 * v);
        if (lv[k] > bv) { bv = lv[k]; best = k; }
      }
      lv[MAP.baseZone] = 1 - 0.85 * Math.max(...MAP.zones.map(z => lv[z] || 0)); audio.setLevels(lv); setZone(best);
    }
    if (sitting) { breathT += dt; const ph = breathT % 10, inhale = ph < 4; $('breath').classList.toggle('in', inhale); $('breathText').textContent = inhale ? '숨을 들이쉬어요' : '천천히 내쉬어요'; }
    camTick++; if (camTick % 6 === 0) updateActionButton();
    leaves && leaves(dt, camState.tgt.x, camState.tgt.z, tAll);
    minimap.update(player, npcs, camState.yaw);
    smoke.update(dt); updateSparkles(dt); updateMagic(dt, tAll); aura.update(dt, tAll); updateBubbles(dt);
    if (camTick % 15 === 0) { const c = $('caption'); document.documentElement.style.setProperty('--capH', (c.hidden ? 22 : c.offsetHeight + 30) + 'px'); }
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
}
// 한 장면에서 오류가 나도 다음 장면은 계속 그림 (예전에는 오류 하나로 화면이 멈춰 '꺼진' 것처럼 보였음)
let frameErr = 0;
function loop() {
  requestAnimationFrame(loop);
  if (glLost) return;
  try { frame(); } catch (e) { if (frameErr++ < 3) console.error('frame', e); }
}
requestAnimationFrame(loop);
window.__dbg = { THREE_V: THREE.Vector3, applyTime, TIME, get bloom() { return BLOOM_ON; }, set bloom(v) { BLOOM_ON = v; }, get player() { return player; }, get npcs() { return npcs; }, startWalk, walkTo, POI, SPOTS, startAction, camState, nav, setPick: k => { pickKey = k; }, rec, groundH, say, jump, renderer, keys, get course() { return course; }, climb, teleport, resetToIntro, applyTime, nearSpot: () => nearSpot };
