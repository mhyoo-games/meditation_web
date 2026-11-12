// 단풍마을 산책 — three.js
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { clone as skClone } from 'three/addons/utils/SkeletonUtils.js';
import LAYOUT from '../assets/village/village_layout.js';
import { createAudio, HEART_SUTRA } from './audio.js';

// ---------------------------------------------------------------- 동물
const ANIMALS = [
  { k: 'hamster', n: '햄스터', e: '🐹', u: 3.017, job: '프로그래머' },
  { k: 'rabbit', n: '토끼', e: '🐰', u: 3.069, job: '제빵사' },
  { k: 'cat', n: '고양이', e: '🐱', u: 2.756, job: '바리스타' },
  { k: 'dog', n: '강아지', e: '🐶', u: 3.058, job: '우체부' },
  { k: 'bear', n: '곰', e: '🐻', u: 3.044, job: '니트 스웨터' },
  { k: 'panda', n: '판다', e: '🐼', u: 3.047, job: '초록 셔츠' },
  { k: 'fox', n: '여우', e: '🦊', u: 2.721, job: '와인색 코트' },
  { k: 'raccoon', n: '너구리', e: '🦝', u: 2.964, job: '푸른 셔츠' },
  { k: 'squirrel', n: '다람쥐', e: '🐿️', u: 3.113, job: '단풍색 셔츠' },
  { k: 'deer', n: '사슴', e: '🦌', u: 2.866, job: '크림 니트' },
  { k: 'lion', n: '사자', e: '🦁', u: 2.84, job: '마을 경비대장' },
];
const CH_SCALE = 1.25;          // 마을 축척에 맞춘 캐릭터 크기
const WALK = 1.55, RUN = 2.6;   // m/s

// ---------------------------------------------------------------- 파일 불러오기 (GitHub Pages: .glb 그대로 / 미리보기: base64 JS)
async function bin(path) {
  if (window.ASSET_JS) { const m = await import(window.ASSET_JS(path)); const t = atob(m.default), u = new Uint8Array(t.length); for (let i = 0; i < t.length; i++) u[i] = t.charCodeAt(i); return u.buffer; }
  const r = await fetch(path); if (!r.ok) throw new Error(path + ' ' + r.status); return r.arrayBuffer();
}
const loader = new GLTFLoader();
const parse = buf => new Promise((res, rej) => loader.parse(buf, '', res, rej));

// ---------------------------------------------------------------- 장면
const canvas = document.getElementById('view');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0xF2D2AC, 26, 78);
const cam = new THREE.PerspectiveCamera(42, 1, 0.1, 300);
scene.add(new THREE.HemisphereLight(0xFFF1DD, 0x8E7050, 1.35));
const sun = new THREE.DirectionalLight(0xFFDDB0, 2.1); sun.position.set(-30, 42, 24); scene.add(sun);
const fill = new THREE.DirectionalLight(0xB8C8FF, 0.45); fill.position.set(25, 18, -30); scene.add(fill);

// 하늘 (노을빛 그라데이션)
{
  const g = new THREE.SphereGeometry(200, 32, 16);
  const m = new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, fog: false, uniforms: { sunDir: { value: new THREE.Vector3(-0.55, 0.32, 0.77).normalize() } },
    vertexShader: 'varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
    fragmentShader: `varying vec3 vP; uniform vec3 sunDir;
      void main(){ float h = clamp(vP.y, -0.2, 1.0);
        vec3 top = vec3(0.50,0.68,0.90), hor = vec3(1.0,0.84,0.66), low = vec3(0.95,0.78,0.60);
        vec3 c = h > 0.0 ? mix(hor, top, pow(h, 0.6)) : low;
        float s = max(dot(normalize(vP), sunDir), 0.0); c += vec3(1.0,0.75,0.45) * pow(s, 24.0) * 0.6 + vec3(1.0,0.85,0.6) * pow(s, 400.0);
        gl_FragColor = vec4(c, 1.0); }` });
  scene.add(new THREE.Mesh(g, m));
}
const grad = new THREE.DataTexture(new Uint8Array([110, 110, 110, 255, 190, 190, 190, 255, 255, 255, 255, 255]), 3, 1, THREE.RGBAFormat);
grad.minFilter = grad.magFilter = THREE.NearestFilter; grad.needsUpdate = true;
const outlineMat = new THREE.MeshBasicMaterial({ color: 0x2A1A14, side: THREE.BackSide });
outlineMat.onBeforeCompile = s => { s.vertexShader = s.vertexShader.replace('#include <skinning_vertex>', '#include <skinning_vertex>\ntransformed += normalize(objectNormal) * 0.018;'); };
function resize() { const w = innerWidth, h = innerHeight; renderer.setSize(w, h, false); cam.aspect = w / h; cam.updateProjectionMatrix(); }
addEventListener('resize', resize); resize();

// ---------------------------------------------------------------- 땅 높이·막힌 곳
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
const RAD = 0.32;
function blocked(x, z) {
  if (Math.hypot(x, z) > 33) return true;
  for (const b of LAYOUT.blockers) { const [lx, lz] = local(b, x, z); if (Math.abs(lx) < b.h[0] + RAD && Math.abs(lz) < b.h[1] + RAD) return true; }
  return false;
}

// ---------------------------------------------------------------- 장소
const BLD = LAYOUT.buildings, Z = LAYOUT.zones;
const T0 = BLD.temple.position, CA = BLD.cathedral.position;
const POI = {
  temple: { p: [BLD.temple.door[0], BLD.temple.door[2] + 1.5], name: '단풍사 (절)' },
  church: { p: [BLD.church.door[0] + 1.2, BLD.church.door[2]], name: '은행나무 교회' },
  cathedral: { p: [BLD.cathedral.door[0] - 1.4, BLD.cathedral.door[2]], name: '별빛 성당' },
  plaza: { p: [0, 4.6], name: '단풍 광장' },
  pond: { p: [-4.0, 11.6], name: '연못' },
};
const SEATS = [   // 명상 방석·자리 (x, z, 바라보는 방향 yaw)
  [T0[0] - 1.6, T0[2] + 3.4, Math.PI], [T0[0] + 1.6, T0[2] + 3.4, Math.PI], [T0[0] - 2.8, T0[2] + 5.2, Math.PI], [T0[0] + 2.8, T0[2] + 5.2, Math.PI],
  [T0[0] - 4.0, T0[2] + 3.6, Math.PI * 0.9], [T0[0] + 3.4, T0[2] + 6.6, Math.PI * 1.1],
];
const SPOTS = {   // 주민이 가서 머무는 곳
  church: [[BLD.church.door[0] + 1.6, BLD.church.door[2] - 0.8], [BLD.church.door[0] + 2.2, BLD.church.door[2] + 0.7], [BLD.church.door[0] + 1.0, BLD.church.door[2] + 1.6]],
  cathedral: [[CA[0] - 5.0, CA[2] + 2.4], [CA[0] - 5.6, CA[2] + 3.6], [CA[0] - 6.4, CA[2] - 0.4]],
  plaza: [[2.6, 2.4], [-2.4, 2.6], [2.2, -2.6], [-2.8, -2.0], [0, -3.4]],
  pond: [[-4.4, 11.2], [-5.2, 15.4], [-10.6, 13.6]],
  walk: [[0, -9], [-9, 1.2], [10, 3], [0, 10], [-5, 6], [6, 7], [3, -6], [-3, -6], [-12, 4], [12, 6]],
};

// ---------------------------------------------------------------- 캐릭터
let ANIMS = [];
function prepModel(g) {
  const root = g.scene, outlines = [];
  root.traverse(o => {
    if (!o.isMesh) return; o.frustumCulled = false;
    const nm = o.material.name;
    if (nm === 'Decal') { o.material = new THREE.MeshToonMaterial({ vertexColors: true, gradientMap: grad, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }); o.renderOrder = 1; }
    else if (nm === 'Glow') { o.material = new THREE.MeshBasicMaterial({ vertexColors: true, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false }); }
    else if (nm === 'DarkGlow' || nm === 'AuraGlow' || nm === 'AuraDark') o.visible = false;
    else { o.material = new THREE.MeshToonMaterial({ vertexColors: true, gradientMap: grad }); if (o.isSkinnedMesh) outlines.push(o); }
  });
  outlines.forEach(o => { const ol = new THREE.SkinnedMesh(o.geometry, outlineMat); ol.frustumCulled = false; ol.bind(o.skeleton, o.bindMatrix); o.parent.add(ol); });
  const b = root.getObjectByName('Bolts'); if (b) b.visible = false;
  return { root, clips: g.animations };
}
class Actor {
  constructor(def, model) {
    this.def = def; this.root = model.root; this.root.scale.setScalar(CH_SCALE / def.u);
    const own = new Set(model.clips.map(c => c.name));
    const clips = model.clips.concat(ANIMS.filter(c => !own.has(c.name)));
    this.mixer = new THREE.AnimationMixer(this.root); this.acts = {};
    clips.forEach(c => { this.acts[c.name] = this.mixer.clipAction(c); });
    for (const n of ['Sit_Floor_Down', 'Sit_Floor_StandUp', 'Sit_Chair_Down', 'Sit_Chair_StandUp', 'Cheer', 'Interact', 'PickUp']) if (this.acts[n]) { this.acts[n].setLoop(THREE.LoopOnce, 1); this.acts[n].clampWhenFinished = true; }
    if (this.acts['trait-idle']) this.acts['trait-idle'].play();
    this.pos = new THREE.Vector3(); this.yaw = 0; this.cur = null; this.speed = 0; this.busy = 0;
    this.mixer.addEventListener('finished', e => { if (this.onFinish) { const f = this.onFinish; this.onFinish = null; f(e.action.getClip().name); } });
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
  step(dirX, dirZ, sp, dt) {   // 미끄러지며 걷기
    const nx = this.pos.x + dirX * sp * dt, nz = this.pos.z + dirZ * sp * dt;
    if (!blocked(nx, nz)) { this.pos.x = nx; this.pos.z = nz; return true; }
    if (!blocked(nx, this.pos.z)) { this.pos.x = nx; return true; }
    if (!blocked(this.pos.x, nz)) { this.pos.z = nz; return true; }
    return false;
  }
  update(dt) {
    this.mixer.update(dt);
    const gy = groundH(this.pos.x, this.pos.z); this.pos.y += (gy - this.pos.y) * Math.min(1, dt * 12);
    this.sync();
  }
}

// ---------------------------------------------------------------- 주민 (NPC)
class Villager extends Actor {
  constructor(def, model, home) { super(def, model); this.home = home; this.state = 'idle'; this.t = 1 + Math.random() * 4; this.target = null; this.stuck = 0; }
  choose() {
    const r = Math.random(); let tgt, act;
    const free = SEATS.filter(s => !s.taken);
    if (r < 0.22 && free.length) { const s = free[Math.floor(Math.random() * free.length)]; s.taken = this; tgt = [s[0], s[1]]; act = { kind: 'sit', yaw: s[2], seat: s, dur: 30 + Math.random() * 40 }; }
    else {
      const pool = r < 0.37 ? SPOTS.church : r < 0.52 ? SPOTS.cathedral : r < 0.68 ? SPOTS.plaza : r < 0.8 ? SPOTS.pond : r < 0.9 ? [this.home] : SPOTS.walk;
      tgt = pool[Math.floor(Math.random() * pool.length)];
      act = { kind: pool === SPOTS.plaza && Math.random() < 0.4 ? 'cheer' : 'stay', dur: 8 + Math.random() * 18, face: pool === SPOTS.church ? [BLD.church.position[0], BLD.church.position[2]] : pool === SPOTS.cathedral ? [CA[0] - 5.2, CA[2] + 2.9] : null };
    }
    this.target = [tgt[0] + (Math.random() - 0.5) * 0.6, tgt[1] + (Math.random() - 0.5) * 0.6]; this.next = act; this.state = 'walk'; this.stuck = 0; this.detour = 0;
  }
  update(dt) {
    if (this.state === 'idle' || this.state === 'stay') { this.t -= dt; if (this.t <= 0) { if (this.seat) { this.standUp(); } else this.choose(); } }
    else if (this.state === 'walk') {
      const dx = this.target[0] - this.pos.x, dz = this.target[1] - this.pos.z, d = Math.hypot(dx, dz);
      if (d < 0.25) { this.arrive(); }
      else {
        let a = Math.atan2(dx, dz) + this.detour; const sp = WALK * 0.8;
        let ok = this.step(Math.sin(a), Math.cos(a), sp, dt);
        if (!ok) { this.detour = this.detour >= 0 ? -(Math.abs(this.detour) + 0.7) : Math.abs(this.detour) + 0.7; if (Math.abs(this.detour) > 2.4) this.detour = 0; this.stuck += dt; }
        else { this.detour *= Math.pow(0.4, dt); this.stuck = Math.max(0, this.stuck - dt * 0.5); }
        if (this.stuck > 3) { if (this.next.seat) this.next.seat.taken = null; this.state = 'idle'; this.t = 0.5; this.play('Idle'); }
        this.turnTo(a, dt); this.play('Walking_A'); if (this.cur) this.cur.setEffectiveTimeScale(0.9);
      }
    }
    // 주인공과 부딪히지 않게 살짝 비켜서기
    if (player && this.state === 'walk') { const px = this.pos.x - player.pos.x, pz = this.pos.z - player.pos.z, pd = Math.hypot(px, pz); if (pd < 0.7 && pd > 0.01) this.step(px / pd, pz / pd, 0.8, dt); }
    super.update(dt);
  }
  arrive() {
    const a = this.next;
    if (a.kind === 'sit') { this.seat = a.seat; this.state = 'sitting'; this.yawTo = a.yaw; this.yaw = a.yaw; this.play('Sit_Floor_Down', 0.3); this.onFinish = () => { this.play('Sit_Floor_Idle', 0.4); this.state = 'stay'; this.t = a.dur; }; return; }
    if (a.face) this.yaw = Math.atan2(a.face[0] - this.pos.x, a.face[1] - this.pos.z);
    this.state = 'stay'; this.t = a.dur;
    if (a.kind === 'cheer') { this.play('Cheer', 0.3); this.onFinish = () => this.play('Idle'); } else this.play('Idle');
  }
  standUp() { const s = this.seat; this.seat = null; this.state = 'busy'; this.play('Sit_Floor_StandUp', 0.3); this.onFinish = () => { if (s) s.taken = null; this.play('Idle'); this.state = 'idle'; this.t = 1; }; }
}

// ---------------------------------------------------------------- 낙엽
function makeLeaves(n = 420) {
  const g = new THREE.PlaneGeometry(0.13, 0.09); g.translate(0, 0, 0);
  const m = new THREE.MeshLambertMaterial({ side: THREE.DoubleSide });
  const mesh = new THREE.InstancedMesh(g, m, n); mesh.frustumCulled = false;
  const cols = ['#D9382B', '#E8552E', '#F07A2E', '#F2C230', '#C42F2F', '#F29A38'].map(c => new THREE.Color(c));
  const L = []; const M = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), s = new THREE.Vector3(1, 1, 1), p = new THREE.Vector3();
  for (let i = 0; i < n; i++) { L.push({ x: (Math.random() - 0.5) * 36, y: Math.random() * 9, z: (Math.random() - 0.5) * 36, v: 0.35 + Math.random() * 0.45, w: Math.random() * 6, r: Math.random() * 6 }); mesh.setColorAt(i, cols[i % cols.length]); }
  scene.add(mesh);
  return (dt, cx, cz, t) => {
    for (let i = 0; i < n; i++) {
      const l = L[i]; l.y -= l.v * dt; l.r += dt * 1.5;
      const gx = cx + l.x + Math.sin(t * 0.7 + l.w) * 0.8, gz = cz + l.z + Math.cos(t * 0.5 + l.w) * 0.6;
      const gy = groundH(gx, gz);
      if (l.y < gy - 1) { l.y = 8 + Math.random() * 3; l.x = (Math.random() - 0.5) * 36; l.z = (Math.random() - 0.5) * 36; }
      const yy = Math.max(l.y, gy + 0.02);
      e.set(l.y > gy ? l.r : -Math.PI / 2, l.r * 0.7, l.y > gy ? l.r * 0.4 : 0); q.setFromEuler(e); p.set(gx, yy, gz); M.compose(p, q, s); mesh.setMatrixAt(i, M);
    }
    mesh.instanceMatrix.needsUpdate = true;
  };
}

// ---------------------------------------------------------------- UI
const $ = id => document.getElementById(id);
let pickKey = 'hamster';
const pick = $('pick');
ANIMALS.forEach(a => {
  const b = document.createElement('button'); b.setAttribute('role', 'radio'); b.setAttribute('aria-checked', String(a.k === pickKey)); b.dataset.k = a.k;
  b.innerHTML = `<span class="em" aria-hidden="true">${a.e}</span>${a.n}<small>${a.job}</small>`;
  b.onclick = () => { pickKey = a.k; pick.querySelectorAll('button').forEach(x => x.setAttribute('aria-checked', String(x.dataset.k === pickKey))); };
  pick.appendChild(b);
});

// ---------------------------------------------------------------- 불러오기
const models = {}; let villageRoot = null, terrainMesh = null, ready = null;
async function loadAll(progress) {
  const jobs = [['village', 'assets/village/village.glb'], ['anims', 'assets/animations/kaykit_animations.glb'], ...ANIMALS.map(a => [a.k, `assets/characters/${a.k}.glb`])];
  let done = 0;
  await Promise.all(jobs.map(async ([k, p]) => { const g = await parse(await bin(p)); models[k] = g; done++; progress(done / jobs.length); }));
  ANIMS = models.anims.animations;
  villageRoot = models.village.scene;
  villageRoot.traverse(o => {
    if (!o.isMesh) return;
    if (o.material.name === 'Glow') o.material = new THREE.MeshBasicMaterial({ vertexColors: true, transparent: true, depthWrite: false });
    else o.material = new THREE.MeshToonMaterial({ vertexColors: true, gradientMap: grad });
  });
  scene.add(villageRoot);
  terrainMesh = villageRoot.getObjectByName('terrain');
  villageRoot.children.forEach(c => { if (c.name !== 'terrain' && c.name !== 'nature') camHits.push(c); });
}
ready = loadAll(p => { $('start').textContent = `불러오는 중… ${Math.round(p * 100)}%`; })
  .then(() => { $('start').disabled = false; $('start').textContent = '산책 시작'; })
  .catch(e => { $('start').textContent = '불러오지 못했어요'; console.error(e); });

// ---------------------------------------------------------------- 시작
let player = null, npcs = [], audio = null, leaves = null, started = false;
const camState = { yaw: 0, pitch: 0.42, dist: 7.5, tgt: new THREE.Vector3() };
let moveTarget = null, sitting = false, autoName = null;
const marker = new THREE.Mesh(new THREE.RingGeometry(0.18, 0.26, 24), new THREE.MeshBasicMaterial({ color: 0xFFF1D0, transparent: true, opacity: 0.85, depthWrite: false }));
marker.rotation.x = -Math.PI / 2; marker.visible = false; scene.add(marker);

$('start').onclick = async () => {
  await ready; if (started) return; started = true;
  audio = createAudio(); audio.start(); audio.setVolume(parseFloat($('vol').value));
  const homes = LAYOUT.homes;
  for (const a of ANIMALS) {
    const m = prepModel(a.k === pickKey ? models[a.k] : models[a.k]);
    if (a.k === pickKey) { player = new Actor(a, m); const s = LAYOUT.spawn.plaza; player.place(s[0], s[2] + 0.6, Math.PI); }
    else { const v = new Villager(a, m, [homes[a.k][0], homes[a.k][2]]); const sp = SPOTS.walk[npcs.length % SPOTS.walk.length]; v.place(sp[0] + Math.random(), sp[1] + Math.random(), Math.random() * 6.28); npcs.push(v); }
  }
  leaves = makeLeaves();
  camState.tgt.copy(player.pos);
  $('intro').hidden = true; $('hud').hidden = false; $('help').hidden = false; $('caption').hidden = true;
  setTimeout(() => { $('help').hidden = true; }, 15000);
  hookAudioText();
};

// ---------------------------------------------------------------- 조작
const keys = new Set();
addEventListener('keydown', e => { if (e.target.tagName === 'INPUT') return; keys.add(e.code); if (sitting && /Arrow|Key[WASD]/.test(e.code)) toggleSit(); });
addEventListener('keyup', e => keys.delete(e.code));
const pointers = new Map(); let pinch0 = 0, down = null;
canvas.addEventListener('pointerdown', e => { canvas.setPointerCapture(e.pointerId); pointers.set(e.pointerId, [e.clientX, e.clientY]); down = { x: e.clientX, y: e.clientY, t: performance.now(), moved: 0 }; if (pointers.size === 2) { const [a, b] = [...pointers.values()]; pinch0 = Math.hypot(a[0] - b[0], a[1] - b[1]); } });
canvas.addEventListener('pointermove', e => {
  if (!pointers.has(e.pointerId)) return; const [px, py] = pointers.get(e.pointerId); const dx = e.clientX - px, dy = e.clientY - py; pointers.set(e.pointerId, [e.clientX, e.clientY]);
  if (down) down.moved += Math.abs(dx) + Math.abs(dy);
  if (pointers.size === 2) { const [a, b] = [...pointers.values()]; const d = Math.hypot(a[0] - b[0], a[1] - b[1]); if (pinch0) camState.dist = THREE.MathUtils.clamp(camState.dist * pinch0 / d, 3.5, 16); pinch0 = d; return; }
  if (down && down.moved > 6) { camState.yaw -= dx * 0.006; camState.pitch = THREE.MathUtils.clamp(camState.pitch + dy * 0.004, 0.12, 1.25); }
});
const ray = new THREE.Raycaster(), ndc = new THREE.Vector2();
canvas.addEventListener('pointerup', e => {
  pointers.delete(e.pointerId); if (pointers.size < 2) pinch0 = 0;
  if (!started || !down) return; const click = down.moved < 8 && performance.now() - down.t < 450; down = null;
  if (!click || !terrainMesh) return;
  ndc.set(e.clientX / innerWidth * 2 - 1, -(e.clientY / innerHeight) * 2 + 1); ray.setFromCamera(ndc, cam);
  const hit = ray.intersectObject(terrainMesh, true)[0];
  if (hit) { if (sitting) toggleSit(); moveTarget = [hit.point.x, hit.point.z]; autoName = null; marker.visible = true; marker.position.set(hit.point.x, groundH(hit.point.x, hit.point.z) + 0.04, hit.point.z); }
});
canvas.addEventListener('wheel', e => { camState.dist = THREE.MathUtils.clamp(camState.dist * (1 + Math.sign(e.deltaY) * 0.1), 3.5, 16); e.preventDefault(); }, { passive: false });

$('btnGo').onclick = () => { $('goMenu').hidden = !$('goMenu').hidden; };
$('goMenu').addEventListener('click', e => {
  const b = e.target.closest('[data-go]'); if (!b || !player) return; $('goMenu').hidden = true;
  const k = b.dataset.go; const p = k === 'home' ? [LAYOUT.homes[pickKey][0], LAYOUT.homes[pickKey][2]] : POI[k].p;
  if (sitting) toggleSit(); moveTarget = [p[0], p[1]]; autoName = b.textContent; marker.visible = true; marker.position.set(p[0], groundH(p[0], p[1]) + 0.04, p[1]);
});
$('vol').oninput = e => audio && audio.setVolume(parseFloat(e.target.value));

// 명상 (앉아서 호흡)
let breathT = 0;
function toggleSit() {
  if (!player) return;
  if (!sitting) {
    sitting = true; moveTarget = null; marker.visible = false; $('btnSit').classList.add('on'); $('btnSit').textContent = '일어나기';
    player.play('Sit_Floor_Down', 0.3); player.onFinish = () => { if (sitting) player.play('Sit_Floor_Idle', 0.4); };
    $('breath').hidden = false; breathT = 0; camState.dist = Math.max(camState.dist, 8); camState.pitch = Math.max(camState.pitch, 0.5);
  } else {
    sitting = false; $('btnSit').classList.remove('on'); $('btnSit').textContent = '명상하기';
    player.play('Sit_Floor_StandUp', 0.3); player.onFinish = () => player.play('Idle');
    $('breath').hidden = true;
  }
}
$('btnSit').onclick = toggleSit;

// ---------------------------------------------------------------- 자막 (반야심경·곡 제목)
let zoneNow = 'village', ttsOn = false, lastLine = -1;
const LINE_START = []; { let k = 0; HEART_SUTRA.forEach((l, i) => { LINE_START[i] = k; k += l.length + 1; }); }
function hookAudioText() {
  audio.listeners.syllable = (li, idx) => {
    if (zoneNow !== 'temple') return;
    const line = HEART_SUTRA[li], pos = idx - LINE_START[li];
    $('capText').innerHTML = `<span class="done">${line.slice(0, pos)}</span><span class="now">${line[pos] || ''}</span><span class="todo">${line.slice(pos + 1)}</span>`;
    if (li !== lastLine) { lastLine = li; if (ttsOn && 'speechSynthesis' in window) { speechSynthesis.cancel(); const u = new SpeechSynthesisUtterance(line); u.lang = 'ko-KR'; u.rate = 0.8; u.pitch = 0.4; u.volume = 0.55; speechSynthesis.speak(u); } }
  };
  audio.listeners.song = (zone, title) => { if (zoneNow === zone) $('capTitle').textContent = '♪ ' + title; songTitle[zone] = title; };
}
const songTitle = {};
$('tts').onchange = e => { ttsOn = e.target.checked; if (!ttsOn && 'speechSynthesis' in window) speechSynthesis.cancel(); };
$('btnNext').onclick = () => audio && audio.nextSong(zoneNow);
$('btnBell').onclick = () => audio && audio.ring(zoneNow);
function setZone(z) {
  if (z === zoneNow) return; zoneNow = z;
  const cap = $('caption'); cap.hidden = z === 'village';
  $('ttsWrap').hidden = z !== 'temple'; $('btnNext').hidden = !(z === 'church' || z === 'cathedral');
  if (z !== 'temple' && 'speechSynthesis' in window) speechSynthesis.cancel();
  if (z === 'temple') { $('capTitle').textContent = '마하반야바라밀다심경 · 목탁에 맞춰 독경하고 있어요'; $('capText').textContent = ''; lastLine = -1; }
  if (z === 'church') { $('capTitle').textContent = '♪ ' + (songTitle.church || '오르간 찬송가'); $('capText').textContent = '오르간이 찬송가와 크리스마스 캐럴을 연주하고 있어요.'; }
  if (z === 'cathedral') { $('capTitle').textContent = '♪ ' + (songTitle.cathedral || '성가대'); $('capText').textContent = '성가대가 노래하고, 종소리가 가끔 울려요.'; }
  const names = { village: ['단풍마을', '천천히 걸어 보세요'], temple: ['단풍사', '목탁 소리와 반야심경'], church: ['은행나무 교회', '찬송가와 캐럴'], cathedral: ['별빛 성당', '성가대와 오르간'] };
  $('placeName').textContent = names[z][0]; $('placeSub').textContent = names[z][1];
}

// ---------------------------------------------------------------- 루프
const clock = new THREE.Clock(); let tAll = 0;
const tmpV = new THREE.Vector3(); const camRay = new THREE.Raycaster(); let camTick = 0, camFree = 99, camCur = 7.5; const camHits = [];
function frame() {
  const dt = Math.min(clock.getDelta(), 0.05); tAll += dt;
  if (player) {
    // 이동
    let ix = 0, iz = 0;
    if (keys.has('KeyW') || keys.has('ArrowUp')) iz += 1; if (keys.has('KeyS') || keys.has('ArrowDown')) iz -= 1;
    if (keys.has('KeyA') || keys.has('ArrowLeft')) ix += 1; if (keys.has('KeyD') || keys.has('ArrowRight')) ix -= 1;
    let mvx = 0, mvz = 0, sp = keys.has('ShiftLeft') || keys.has('ShiftRight') ? RUN : WALK;
    if (ix || iz) {
      moveTarget = null; marker.visible = false;
      const fy = camState.yaw + Math.PI; const fx = Math.sin(fy), fz = Math.cos(fy);
      mvx = fx * iz + fz * ix; mvz = fz * iz - fx * ix; const l = Math.hypot(mvx, mvz); mvx /= l; mvz /= l;
    } else if (moveTarget) {
      const dx = moveTarget[0] - player.pos.x, dz = moveTarget[1] - player.pos.z, d = Math.hypot(dx, dz);
      if (d < 0.2) { moveTarget = null; marker.visible = false; } else { mvx = dx / d; mvz = dz / d; if (d < 0.6) sp *= Math.max(0.3, d / 0.6); }
    }
    if ((mvx || mvz) && !sitting) {
      let moved = player.step(mvx, mvz, sp, dt);
      if (!moved && moveTarget) { const a = Math.atan2(mvx, mvz); for (const o of [0.8, -0.8, 1.5, -1.5]) { if (player.step(Math.sin(a + o), Math.cos(a + o), sp, dt)) { moved = true; break; } } }
      player.turnTo(Math.atan2(mvx, mvz), dt, 10);
      player.play(sp > WALK ? 'Running_A' : 'Walking_A');
    } else if (!sitting && player.curName !== 'Idle' && !player.onFinish) player.play('Idle');
    player.update(dt);
    npcs.forEach(n => n.update(dt));
    // 카메라
    camState.tgt.lerp(tmpV.set(player.pos.x, player.pos.y + 0.7, player.pos.z), Math.min(1, dt * 5));
    if (sitting) camState.yaw += dt * 0.05;
    const cp = Math.cos(camState.pitch);
    const dir = tmpV.set(Math.sin(camState.yaw) * cp, Math.sin(camState.pitch), Math.cos(camState.yaw) * cp);
    if (++camTick % 4 === 0 && camHits.length) {      // 지붕·나무에 가리면 카메라를 앞으로
      camRay.set(camState.tgt, dir); camRay.far = camState.dist;
      const h = camRay.intersectObjects(camHits, true)[0]; camFree = h ? Math.max(1.6, h.distance - 0.35) : camState.dist;
    }
    camCur += (Math.min(camState.dist, camFree) - camCur) * Math.min(1, dt * (camFree < camCur ? 12 : 3));
    cam.position.copy(camState.tgt).addScaledVector(dir, camCur);
    const gy = groundH(cam.position.x, cam.position.z) + 0.5; if (cam.position.y < gy) cam.position.y = gy;
    cam.lookAt(camState.tgt);
    marker.material.opacity = 0.5 + 0.35 * Math.sin(tAll * 5);
    // 소리 구역
    if (audio) {
      const lv = { village: 1, temple: 0, church: 0, cathedral: 0 }; let best = 'village', bv = 0.3;
      for (const [k, z] of Object.entries(Z)) {
        const d = Math.hypot(player.pos.x - z.center[0], player.pos.z - z.center[2]);
        const v = THREE.MathUtils.clamp((z.radius * 1.35 - d) / (z.radius * 0.75), 0, 1); lv[k] = v * v * (3 - 2 * v);
        if (lv[k] > bv) { bv = lv[k]; best = k; }
      }
      lv.village = 1 - 0.85 * Math.max(lv.temple, lv.church, lv.cathedral); audio.setLevels(lv); setZone(best);
    }
    if (sitting) { breathT += dt; const ph = breathT % 10, inhale = ph < 4; $('breath').classList.toggle('in', inhale); $('breathText').textContent = inhale ? '숨을 들이쉬어요' : '천천히 내쉬어요'; }
    leaves && leaves(dt, camState.tgt.x, camState.tgt.z, tAll);
  } else {
    // 시작 전: 마을 위를 천천히 도는 카메라
    const a = tAll * 0.05; cam.position.set(Math.sin(a) * 30, 16, Math.cos(a) * 30); cam.lookAt(0, 0, -4);
  }
  renderer.render(scene, cam);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
