// 지도: 구석의 작은 동그란 지도(내 주변) + 누르면 펼쳐지는 큰 지도(장소 이름, 눌러서 그곳으로 걷기)
// 바닥 그림은 길찾기 격자(갈 수 있는 곳 / 막힌 곳)와 높이맵(물), 건물 안(실내 칸)으로 한 번만 그려 둠.
const THEMES = {
  village: { ground: '#E9C48E', path: '#D9AA6E', block: '#8E5A3C', inside: '#F6E2C0', water: '#7FB7C9', edge: '#5A3A2A', me: '#E8542E', npc: '#FFF6E6', label: '#3A2418', bg: '#C98F5E' },
  school: { ground: '#8D86B0', path: '#A69FC6', block: '#3C3766', inside: '#C9BEE6', water: '#4E6FA8', edge: '#24204A', me: '#9CD2FF', npc: '#FFE7A0', label: '#1E1A3C', bg: '#4A4478' },
};

export function createMinimap({ key, nav, bound, layout, poi, water = [], onPick, icon }) {
  const T = THEMES[key] || THEMES.village;
  const N = nav.N, cell = nav.cell, S = 512;   // 바닥 그림 크기 (px)
  const base = document.createElement('canvas'); base.width = base.height = S;
  {
    const g = base.getContext('2d'), px = S / N;
    g.fillStyle = T.bg; g.fillRect(0, 0, S, S);
    for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) {
      const x = -bound + (i + 0.5) * cell, z = -bound + (j + 0.5) * cell;
      if (Math.hypot(x, z) > bound) continue;
      const wet = water.some(([wx, wz, wr]) => Math.hypot(x - wx, z - wz) < wr);
      g.fillStyle = wet ? T.water : nav.free[j * N + i] ? T.ground : T.block;
      g.fillRect(i * px, j * px, px + 0.6, px + 0.6);
    }
    g.fillStyle = T.inside; g.globalAlpha = 0.9;
    for (const it of layout.interiors || []) {
      g.save(); g.translate(w2p(it.c[0]), w2p(it.c[1])); g.rotate(-(it.r || 0)); g.fillRect(-it.h[0] * S / (2 * bound), -it.h[1] * S / (2 * bound), it.h[0] * S / bound, it.h[1] * S / bound); g.restore();
    }
    g.globalAlpha = 1;
    g.strokeStyle = T.edge; g.lineWidth = 6; g.beginPath(); g.arc(S / 2, S / 2, S / 2 - 3, 0, 7); g.stroke();
  }
  function w2p(v) { return (v + bound) / (2 * bound) * S; }

  // ---- 작은 지도
  const mini = document.createElement('canvas'); mini.id = 'miniMap'; mini.width = mini.height = 300; mini.title = '지도 펼치기 (M)';
  document.getElementById('app').append(mini);
  const VIEW = 22;   // 작은 지도에 보이는 반지름 (m)
  // ---- 큰 지도
  const sheet = document.createElement('section'); sheet.id = 'mapSheet'; sheet.className = 'sheet'; sheet.hidden = true;
  sheet.innerHTML = `<div class="sheetCard mapCardBig"><button class="close" aria-label="닫기">✕</button><h2>${icon || '🗺️'} 지도</h2><div class="mapWrap"><canvas width="${S}" height="${S}"></canvas></div><p class="hint">장소 이름이나 지도를 누르면 그곳으로 걸어가요 · M 키로 열고 닫기</p></div>`;
  document.getElementById('app').append(sheet);
  const big = sheet.querySelector('canvas'), wrap = sheet.querySelector('.mapWrap');
  const labels = [];
  for (const [k, p] of Object.entries(poi)) {
    if (!p.p) continue;
    const b = document.createElement('button'); b.className = 'mapLabel'; b.textContent = p.name;
    b.style.left = (w2p(p.p[0]) / S * 100) + '%'; b.style.top = (w2p(p.p[1]) / S * 100) + '%';
    b.onclick = e => { e.stopPropagation(); close(); onPick(p.p[0], p.p[1]); };
    wrap.append(b); labels.push(b);
  }
  big.addEventListener('click', e => {
    const r = big.getBoundingClientRect(), x = (e.clientX - r.left) / r.width * 2 * bound - bound, z = (e.clientY - r.top) / r.height * 2 * bound - bound;
    if (Math.hypot(x, z) > bound - 1) return; close(); onPick(x, z);
  });
  sheet.querySelector('.close').onclick = () => close();
  mini.addEventListener('click', () => open());
  function open() { sheet.hidden = false; }
  function close() { sheet.hidden = true; }

  function arrow(g, x, y, yaw, r, col) {
    g.save(); g.translate(x, y); g.rotate(-yaw + Math.PI);
    g.fillStyle = col; g.strokeStyle = 'rgba(0,0,0,.55)'; g.lineWidth = r * 0.25;
    g.beginPath(); g.moveTo(0, -r * 1.25); g.lineTo(r * 0.85, r * 0.85); g.lineTo(0, r * 0.4); g.lineTo(-r * 0.85, r * 0.85); g.closePath(); g.fill(); g.stroke(); g.restore();
  }
  function cone(g, x, y, camYaw, r) {
    const a = Math.atan2(-Math.cos(camYaw), -Math.sin(camYaw));   // 카메라가 보는 쪽
    g.save(); g.fillStyle = 'rgba(255,255,255,.22)'; g.beginPath(); g.moveTo(x, y); g.arc(x, y, r, a - 0.55, a + 0.55); g.closePath(); g.fill(); g.restore();
  }
  let tick = 0;
  return {
    open, close, toggle() { sheet.hidden ? open() : close(); },
    set visible(v) { mini.hidden = !v; if (!v) close(); },
    update(player, npcs, camYaw) {
      if (!player || (tick++ % 3)) return;
      const m = mini.getContext('2d'), W = mini.width, sc = W / (2 * VIEW), k = S / (2 * bound);
      m.clearRect(0, 0, W, W); m.save(); m.beginPath(); m.arc(W / 2, W / 2, W / 2 - 2, 0, 7); m.clip();
      m.fillStyle = T.bg; m.fillRect(0, 0, W, W);
      const sx = w2p(player.pos.x) - VIEW * k, sz = w2p(player.pos.z) - VIEW * k;
      m.drawImage(base, sx, sz, 2 * VIEW * k, 2 * VIEW * k, 0, 0, W, W);
      const P = (x, z) => [W / 2 + (x - player.pos.x) * sc, W / 2 + (z - player.pos.z) * sc];
      m.fillStyle = T.npc; m.strokeStyle = T.edge; m.lineWidth = 2;
      for (const n of npcs) { const [x, y] = P(n.pos.x, n.pos.z); if (x < -10 || y < -10 || x > W + 10 || y > W + 10) continue; m.beginPath(); m.arc(x, y, 6, 0, 7); m.fill(); m.stroke(); }
      m.font = 'bold 22px sans-serif'; m.textAlign = 'center';
      for (const p of Object.values(poi)) { if (!p.p) continue; const [x, y] = P(p.p[0], p.p[1]); if (x < 20 || y < 20 || x > W - 20 || y > W - 20) continue; m.fillStyle = 'rgba(255,255,255,.85)'; m.strokeStyle = T.edge; m.lineWidth = 5; m.strokeText(p.name, x, y); m.fillStyle = T.label; m.fillText(p.name, x, y); }
      cone(m, W / 2, W / 2, camYaw, 70);
      arrow(m, W / 2, W / 2, player.yaw, 16, T.me);
      m.restore(); m.strokeStyle = T.edge; m.lineWidth = 6; m.beginPath(); m.arc(W / 2, W / 2, W / 2 - 3, 0, 7); m.stroke();
      // 북쪽 표시
      m.fillStyle = T.edge; m.font = 'bold 26px sans-serif'; m.fillText('N', W / 2, 30);
      if (!sheet.hidden) {
        const g = big.getContext('2d'); g.drawImage(base, 0, 0);
        g.fillStyle = T.npc; g.strokeStyle = T.edge; g.lineWidth = 2;
        for (const n of npcs) { g.beginPath(); g.arc(w2p(n.pos.x), w2p(n.pos.z), 5, 0, 7); g.fill(); g.stroke(); }
        g.fillStyle = 'rgba(255,255,255,.5)'; g.beginPath(); g.arc(w2p(player.pos.x), w2p(player.pos.z), 22, 0, 7); g.fill();
        arrow(g, w2p(player.pos.x), w2p(player.pos.z), player.yaw, 13, T.me);
      }
    },
  };
}
