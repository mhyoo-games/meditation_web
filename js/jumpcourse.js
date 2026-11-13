// 점프 맵(하늘 오름 숲)의 발판: 배치 파일의 jump 목록으로 그림을 만들고, 발밑 높이를 알려 줌.
// 발판은 아래에서는 통과하고(뛰어서 밑에서 올라탈 수 있음) 위에서만 밟혀요.
import * as THREE from 'three';

export function createCourse(scene, L, grad, groundH) {
  const J = L.jump || []; if (!J.length) return null;
  const toon = c => new THREE.MeshToonMaterial({ color: c, gradientMap: grad });
  const M = {
    stump: toon(0x7A5236), stumpTop: toon(0xD8B484), fungus: toon(0xE8A85A), fungusTop: toon(0xF6D7A0), fungusRim: toon(0xB86A38),
    bark: toon(0x6E4A30), plank: toon(0xB07A48), leaf: toon(0x6FB055), leafVein: toon(0x4E8A3C), vine: toon(0x4E7A36),
    deck: toon(0xC08A54), rail: toon(0x7A5030), lamp: new THREE.MeshBasicMaterial({ color: 0xFFE2A0 }), gold: toon(0xF2D27A),
  };
  const G = {
    cyl: new THREE.CylinderGeometry(1, 1, 1, 20), cylLo: new THREE.CylinderGeometry(1, 1, 1, 10), box: new THREE.BoxGeometry(1, 1, 1),
    half: new THREE.CylinderGeometry(1, 1, 1, 20, 1, false, 0, Math.PI), sph: new THREE.SphereGeometry(1, 12, 8),
  };
  G.cyl.translate(0, -0.5, 0); G.cylLo.translate(0, -0.5, 0); G.half.translate(0, -0.5, 0); G.box.translate(0, -0.5, 0);
  const root = new THREE.Group(); root.name = 'jumpCourse'; scene.add(root);
  const mesh = (g, m, x, y, z, sx, sy, sz, ry = 0) => { const o = new THREE.Mesh(g, m); o.position.set(x, y, z); o.scale.set(sx, sy, sz); o.rotation.y = ry; o.castShadow = true; o.receiveShadow = true; return o; };
  const T = L.jump.find(j => j.t === 'goal'); const tx = T.x, tz = T.z;
  const items = [];
  for (const j of J) {
    const g = new THREE.Group(); g.position.set(j.x, j.y, j.z); root.add(g);
    const out = Math.atan2(j.x - tx, j.z - tz);   // 줄기 바깥쪽을 보는 방향
    if (j.t === 'stump') {
      const h = j.y - groundH(j.x, j.z) + 0.05;
      g.add(mesh(G.cyl, M.stump, 0, 0, 0, j.r, h, j.r)); g.add(mesh(G.cyl, M.stumpTop, 0, 0.012, 0, j.r * 0.96, 0.03, j.r * 0.96));
    } else if (j.t === 'fungus') {   // 줄기에 붙은 선반 버섯 (반달)
      const o = mesh(G.half, M.fungus, 0, 0, 0, j.r * 1.05, 0.2, j.r * 1.05, out - Math.PI / 2); g.add(o);
      g.add(mesh(G.half, M.fungusTop, 0, 0.012, 0, j.r * 0.98, 0.03, j.r * 0.98, out - Math.PI / 2));
      g.add(mesh(G.half, M.fungusRim, 0, -0.2, 0, j.r * 0.8, 0.12, j.r * 0.8, out - Math.PI / 2));
      // 반달의 곧은 쪽이 줄기 쪽을 보도록 조금 줄기 쪽으로
      g.children.forEach(c => { c.position.x -= Math.sin(out) * j.r * 0.35; c.position.z -= Math.cos(out) * j.r * 0.35; });
    } else if (j.t === 'branch') {   // 줄기에서 뻗은 가지 + 그 위 나무 판자
      const len = j.len, w = j.w;
      const p = mesh(G.box, M.plank, 0, 0, 0, len, 0.16, w, out); g.add(p);   // 판자는 길 방향(줄기를 도는 방향)으로 길게
      const tx_ = Math.cos(out), tz_ = -Math.sin(out);
      for (const s of [-1, 1]) g.add(mesh(G.box, M.rail, tx_ * len * 0.42 * s, 0.005, tz_ * len * 0.42 * s, 0.08, 0.03, w * 1.02, out));
      const rr = Math.hypot(j.x - tx, j.z - tz), back = Math.max(0.3, rr - 2.4);   // 줄기에서 판자 밑까지 받침 가지
      g.add(mesh(G.box, M.bark, -Math.sin(out) * back / 2, -0.14, -Math.cos(out) * back / 2, 0.32, 0.3, back, out));
    } else if (j.t === 'leaf') {     // 넝쿨에 매달려 살랑이는 큰 잎
      const lf = mesh(G.cyl, M.leaf, 0, 0, 0, j.r * 1.12, 0.07, j.r * 0.86, out); g.add(lf);
      g.add(mesh(G.box, M.leafVein, 0, 0.012, 0, 0.05, 0.02, j.r * 1.7, out + Math.PI / 2));
      const vine = mesh(G.cylLo, M.vine, 0, 2.6, 0, 0.022, 2.6, 0.022); vine.castShadow = false; g.add(vine);   // 위로 뻗은 넝쿨 (짧게)
    } else if (j.t === 'rest') {     // 쉼터: 넓은 덱 + 난간 기둥 + 등불
      g.add(mesh(G.cyl, M.deck, 0, 0, 0, j.r, 0.18, j.r));
      for (let k = 0; k < 10; k++) { const a = k / 10 * Math.PI * 2; if (Math.abs(Math.atan2(Math.sin(a - out), Math.cos(a - out))) < 0.5) continue; g.add(mesh(G.cylLo, M.rail, Math.sin(a) * j.r * 0.94, 0.55, Math.cos(a) * j.r * 0.94, 0.04, 0.55, 0.04)); }
      g.add(mesh(G.cylLo, M.rail, Math.sin(out + 2.2) * j.r * 0.7, 1.3, Math.cos(out + 2.2) * j.r * 0.7, 0.05, 1.3, 0.05));
      const lamp = mesh(G.box, M.lamp, Math.sin(out + 2.2) * j.r * 0.7, 1.45, Math.cos(out + 2.2) * j.r * 0.7, 0.2, 0.22, 0.2); lamp.castShadow = false; g.add(lamp);
      const flag = mesh(G.box, M.gold, Math.sin(out - 2.0) * j.r * 0.75, 1.2, Math.cos(out - 2.0) * j.r * 0.75, 0.5, 0.3, 0.03, out); g.add(flag);
      g.add(mesh(G.cylLo, M.rail, Math.sin(out - 2.0) * j.r * 0.75 - 0.25 * Math.cos(out), 1.2, Math.cos(out - 2.0) * j.r * 0.75 + 0.25 * Math.sin(out), 0.03, 1.2, 0.03));
    } else if (j.t === 'goal') {     // 정상: 줄기를 둘러싼 둥근 덱 + 난간
      g.add(mesh(G.cyl, M.deck, 0, 0, 0, j.r, 0.25, j.r));
      for (let k = 0; k < 28; k++) { const a = k / 28 * Math.PI * 2; g.add(mesh(G.cylLo, M.rail, Math.sin(a) * j.r * 0.97, 0.7, Math.cos(a) * j.r * 0.97, 0.05, 0.7, 0.05)); }
      for (let k = 0; k < 4; k++) { const a = k / 4 * Math.PI * 2 + 0.4, l = mesh(G.sph, M.lamp, Math.sin(a) * j.r * 0.97, 0.95, Math.cos(a) * j.r * 0.97, 0.12, 0.12, 0.12); l.castShadow = false; g.add(l); }
    }
    items.push({ j, g, y0: j.y, hx: j.t === 'branch' ? j.len / 2 + 0.05 : 0, hz: j.t === 'branch' ? j.w / 2 + 0.05 : 0, out });
  }
  function topOf(it, t) { return it.j.bob ? it.y0 + Math.sin(t * it.j.sp + it.j.ph) * it.j.bob : it.y0; }
  function inside(it, x, z, pad) {
    const dx = x - it.j.x, dz = z - it.j.z;
    if (it.j.t === 'fungus') {   // 반달: 줄기 쪽으로 0.35r 옮긴 원의 바깥쪽 절반
      const sx = Math.sin(it.out), sz = Math.cos(it.out), cx = dx + sx * it.j.r * 0.35, cz = dz + sz * it.j.r * 0.35, r = it.j.r * 1.05 + pad;
      return cx * sx + cz * sz >= -pad && cx * cx + cz * cz <= r * r;
    }
    if (it.hz) { const c = Math.cos(it.out), s = Math.sin(it.out), lz = dx * s + dz * c, lx = dx * c - dz * s; return Math.abs(lx) <= it.hx + pad && Math.abs(lz) <= it.hz + pad; }
    return dx * dx + dz * dz <= (it.j.r + pad) * (it.j.r + pad);
  }
  let now = 0;
  return {
    root, items, goal: T, rests: items.filter(i => i.j.t === 'rest').map(i => i.j), total: J.length,
    update(t) { now = t; for (const it of items) if (it.j.bob) it.g.position.y = topOf(it, t); },
    /** 발밑 높이: (x,z)에서 y+tol 아래에 있는 가장 높은 면. {y, it} */
    surface(x, z, y, tol, pad = 0.12) {
      let best = groundH(x, z), hit = null;
      for (const it of items) { const top = topOf(it, now); if (top <= y + tol && top > best && inside(it, x, z, pad)) { best = top; hit = it; } }
      return { y: best, it: hit };
    },
    index(it) { return it ? items.indexOf(it) : -1; },
  };
}
