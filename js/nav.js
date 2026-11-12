// 길찾기: 0.4m 격자 위 A* + 직선으로 펴기
export function createNav(bound, cell, blockedFn, lineBlocked) {
  const N = Math.ceil((bound * 2) / cell), W = N;
  const free = new Uint8Array(N * N);
  const cx = i => -bound + (i + 0.5) * cell;
  for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) free[j * W + i] = blockedFn(cx(i), cx(j)) ? 0 : 1;
  const toCell = v => Math.max(0, Math.min(N - 1, Math.floor((v + bound) / cell)));

  function nearestFree(i, j, maxR = 12) {
    if (free[j * W + i]) return [i, j];
    for (let r = 1; r <= maxR; r++) {
      let best = null, bd = 1e9;
      for (let dj = -r; dj <= r; dj++) for (let di = -r; di <= r; di++) {
        if (Math.max(Math.abs(di), Math.abs(dj)) !== r) continue;
        const a = i + di, b = j + dj; if (a < 0 || b < 0 || a >= N || b >= N || !free[b * W + a]) continue;
        const d = di * di + dj * dj; if (d < bd) { bd = d; best = [a, b]; }
      }
      if (best) return best;
    }
    return null;
  }
  // 이진 힙
  function Heap() { const a = [], p = []; return {
    push(v, pr) { a.push(v); p.push(pr); let k = a.length - 1; while (k > 0) { const q = (k - 1) >> 1; if (p[q] <= p[k]) break; [a[q], a[k]] = [a[k], a[q]]; [p[q], p[k]] = [p[k], p[q]]; k = q; } },
    pop() { const top = a[0], lv = a.pop(), lp = p.pop(); if (a.length) { a[0] = lv; p[0] = lp; let k = 0; for (;;) { const l = 2 * k + 1, r = l + 1; let m = k; if (l < a.length && p[l] < p[m]) m = l; if (r < a.length && p[r] < p[m]) m = r; if (m === k) break; [a[m], a[k]] = [a[k], a[m]]; [p[m], p[k]] = [p[k], p[m]]; k = m; } } return top; },
    get size() { return a.length; } }; }
  const g = new Float32Array(N * N), came = new Int32Array(N * N), stamp = new Uint32Array(N * N); let run = 0;
  const DIRS = [[1, 0, 1], [-1, 0, 1], [0, 1, 1], [0, -1, 1], [1, 1, Math.SQRT2], [1, -1, Math.SQRT2], [-1, 1, Math.SQRT2], [-1, -1, Math.SQRT2]];

  function los(ax, az, bx, bz) {
    const d = Math.hypot(bx - ax, bz - az), n = Math.ceil(d / 0.15);
    for (let k = 1; k <= n; k++) { const t = k / n; if (lineBlocked(ax + (bx - ax) * t, az + (bz - az) * t)) return false; }
    return true;
  }
  function find(sx, sz, tx, tz) {
    let s = nearestFree(toCell(sx), toCell(sz), 4), t = nearestFree(toCell(tx), toCell(tz), 12);
    if (!s || !t) return null;
    const exact = free[toCell(tz) * W + toCell(tx)] && !lineBlocked(tx, tz);
    const goal = exact ? [tx, tz] : [cx(t[0]), cx(t[1])];
    if (los(sx, sz, goal[0], goal[1])) return [goal];
    run++; const si = s[1] * W + s[0], ti = t[1] * W + t[0];
    const H = new Heap(); g[si] = 0; stamp[si] = run; came[si] = -1; H.push(si, 0);
    let found = false, it = 0;
    while (H.size && it++ < 60000) {
      const c = H.pop(); if (c === ti) { found = true; break; }
      const ci = c % W, cj = (c / W) | 0, gc = g[c];
      for (const [di, dj, w] of DIRS) {
        const a = ci + di, b = cj + dj; if (a < 0 || b < 0 || a >= N || b >= N) continue;
        const n = b * W + a; if (!free[n]) continue;
        if (di && dj && (!free[cj * W + a] || !free[b * W + ci])) continue;   // 모서리 끼어 가기 금지
        const ng = gc + w;
        if (stamp[n] !== run || ng < g[n]) {
          stamp[n] = run; g[n] = ng; came[n] = c;
          const hx = Math.abs(a - t[0]), hz = Math.abs(b - t[1]);
          H.push(n, ng + (hx + hz) + (Math.SQRT2 - 2) * Math.min(hx, hz));
        }
      }
    }
    if (!found) return null;
    const cells = []; for (let c = ti; c !== -1; c = came[c]) cells.push([cx(c % W), cx((c / W) | 0)]);
    cells.reverse(); cells[cells.length - 1] = goal;
    // 직선으로 펴기
    const out = []; let ax = sx, az = sz, k = 0;
    while (k < cells.length) {
      let far = k;
      for (let m = cells.length - 1; m > k; m--) if (los(ax, az, cells[m][0], cells[m][1])) { far = m; break; }
      out.push(cells[far]); [ax, az] = cells[far]; k = far + 1;
    }
    return out;
  }
  return { find, free, N, cell };
}
