// 마음 기록: 명상·기도·절·노래 시간과 횟수를 이 브라우저에만 저장 (어디로도 보내지 않음)
const KEY = 'mw_rec_v1';
const today = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`; };
const dayNum = s => Math.round(new Date(s + 'T12:00:00').getTime() / 864e5);

// 점수: 초 단위 기록은 10초에 1점, 횟수 기록은 하나에 몇 점
export const POINTS = { meditate: 0.1, pray: 0.1, sing: 0.1, bowTime: 0.05, read: 0.1, magic: 0.1, stars: 0.1, books: 1, spells: 1, starsSeen: 2, bows: 3, b108: 108, moktak: 0.2, donate: 2, incense: 2, candle: 2, baptism: 5, visit: 10, emote: 0.5 };
export const LEVELS = [
  [0, '씨앗', '🌰'], [40, '새싹', '🌱'], [120, '잎새', '🍃'], [300, '단풍잎', '🍁'], [700, '산들바람', '🌬️'],
  [1400, '고요한 숲', '🌲'], [2600, '맑은 연못', '🪷'], [4500, '달빛', '🌙'], [8000, '깨달음', '✨'],
];
// 단계마다 생기는 것 (보상)
export const REWARDS = [
  [1, '이름 옆에 칭호가 붙어요'], [2, '기도·명상할 때 둘레에 빛 방울이 떠올라요'], [3, '밤이 아니어도 반딧불이 따라다녀요'],
  [5, '걸을 때 발밑에 꽃잎이 흩날려요'], [7, '머리 위에 은은한 빛 고리가 생겨요'],
];
const fmtMin = s => `${Math.floor(s / 60)}분`;
export const ACH = [
  { id: 'first', icon: '👣', name: '첫 산책', desc: '처음으로 산책을 나왔어요', ok: r => r.days.length >= 1 },
  { id: 'med10', icon: '🧘', name: '고요한 10분', desc: '명상 모두 10분', ok: r => r.t.meditate >= 600, prog: r => [r.t.meditate, 600, fmtMin] },
  { id: 'med60', icon: '🕯️', name: '한 시간의 고요', desc: '명상 모두 1시간', ok: r => r.t.meditate >= 3600, prog: r => [r.t.meditate, 3600, fmtMin] },
  { id: 'bow10', icon: '🙇', name: '열 번의 절', desc: '절 10번', ok: r => r.n.bows >= 10, prog: r => [r.n.bows, 10] },
  { id: 'b108', icon: '📿', name: '108배', desc: '108배를 끝까지', ok: r => r.n.b108 >= 1 },
  { id: 'mok100', icon: '🪵', name: '목탁 백 번', desc: '목탁 100번 두드리기', ok: r => r.n.moktak >= 100, prog: r => [r.n.moktak, 100] },
  { id: 'mok1000', icon: '🎋', name: '목탁 천 번', desc: '목탁 1000번 두드리기', ok: r => r.n.moktak >= 1000, prog: r => [r.n.moktak, 1000] },
  { id: 'donate', icon: '🪙', name: '마음의 시주', desc: '시주함에 처음 넣기', ok: r => r.n.donate >= 1 },
  { id: 'incense', icon: '🌫️', name: '향 한 줄기', desc: '향 피우기', ok: r => r.n.incense >= 1 },
  { id: 'candle', icon: '🕯️', name: '작은 촛불', desc: '성당에서 촛불 켜기', ok: r => r.n.candle >= 1 },
  { id: 'pray30', icon: '🙏', name: '30분 기도', desc: '기도 모두 30분', ok: r => r.t.pray >= 1800, prog: r => [r.t.pray, 1800, fmtMin] },
  { id: 'choir', icon: '🎵', name: '성가대 데뷔', desc: '성가대에서 1분 노래', ok: r => r.t.sing >= 60, prog: r => [r.t.sing, 60, s => `${Math.floor(s)}초`] },
  { id: 'choir30', icon: '🎼', name: '성가대 단골', desc: '성가대에서 30분 노래', ok: r => r.t.sing >= 1800, prog: r => [r.t.sing, 1800, fmtMin] },
  { id: 'baptism', icon: '💧', name: '새 이름', desc: '성당에서 세례명 받기', ok: r => r.n.baptism >= 1 },
  { id: 'pilgrim', icon: '🗺️', name: '세 곳 순례', desc: '절·교회·성당에 모두 가 보기', ok: r => ['temple', 'church', 'cathedral'].every(z => r.zones.includes(z)) },
  { id: 'night', icon: '🌙', name: '밤 산책', desc: '밤의 마을 걸어 보기', ok: r => r.n.night >= 1 },
  { id: 'hello', icon: '👋', name: '다정한 이웃', desc: '말·이모티콘 10번 건네기', ok: r => r.n.emote >= 10, prog: r => [r.n.emote, 10] },
  { id: 'school', icon: '🏰', name: '마법학교 입학', desc: '별빛 마법학교에 가 보기', ok: r => r.zones.includes('school') },
  { id: 'read10', icon: '📖', name: '책벌레', desc: '도서관에서 10분 읽기', ok: r => (r.t.read || 0) >= 600, prog: r => [r.t.read || 0, 600, fmtMin] },
  { id: 'books10', icon: '📚', name: '열 권의 책', desc: '책장에서 책 10권 고르기', ok: r => (r.n.books || 0) >= 10, prog: r => [r.n.books || 0, 10] },
  { id: 'spell1', icon: '✨', name: '첫 마법', desc: '마법진에서 마법 연습하기', ok: r => (r.n.spells || 0) >= 1 },
  { id: 'spell30', icon: '🪄', name: '꼬마 마법사', desc: '마법 연습 30번', ok: r => (r.n.spells || 0) >= 30, prog: r => [r.n.spells || 0, 30] },
  { id: 'stars5', icon: '🔭', name: '별지기', desc: '천문대에서 별자리 5번 찾기', ok: r => (r.n.starsSeen || 0) >= 5, prog: r => [r.n.starsSeen || 0, 5] },
  { id: 'streak3', icon: '🔥', name: '사흘 연속', desc: '3일 이어서 들르기', ok: r => r.best >= 3, prog: r => [r.streak, 3] },
  { id: 'streak7', icon: '🌈', name: '일주일 연속', desc: '7일 이어서 들르기', ok: r => r.best >= 7, prog: r => [r.streak, 7] },
  { id: 'days30', icon: '🏡', name: '단골 주민', desc: '30일 들르기', ok: r => r.days.length >= 30, prog: r => [r.days.length, 30] },
];

function blank() { return { v: 1, t: { meditate: 0, pray: 0, sing: 0, bowTime: 0, read: 0, magic: 0, stars: 0 }, n: { bows: 0, b108: 0, moktak: 0, donate: 0, incense: 0, candle: 0, baptism: 0, night: 0, emote: 0, books: 0, spells: 0, starsSeen: 0 }, days: [], streak: 0, best: 0, zones: [], got: {}, todayT: {}, pts: 0 }; }

export function createRecords(onUnlock, onLevel) {
  let r = blank();
  try { const s = JSON.parse(localStorage.getItem(KEY) || 'null'); if (s && s.v === 1) r = Object.assign(blank(), s, { t: Object.assign(blank().t, s.t), n: Object.assign(blank().n, s.n) }); } catch (e) { }
  let dirty = false, lastSave = 0;
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(r)); } catch (e) { } dirty = false; };
  const points = () => {
    let p = 0; for (const k in r.t) p += (r.t[k] || 0) * (POINTS[k] || 0); for (const k in r.n) p += (r.n[k] || 0) * (POINTS[k] || 0);
    return Math.floor(p + r.days.length * POINTS.visit);
  };
  const level = (p = points()) => { let i = 0; while (i + 1 < LEVELS.length && p >= LEVELS[i + 1][0]) i++; return i; };
  let lv = level();
  function check() {
    for (const a of ACH) if (!r.got[a.id] && a.ok(r)) { r.got[a.id] = today(); dirty = true; onUnlock && onUnlock(a); }
    const nl = level(); if (nl > lv) { lv = nl; onLevel && onLevel(nl, LEVELS[nl]); }
  }
  function visit() {
    const d = today(); if (r.days.includes(d)) return false;
    const prev = r.days[r.days.length - 1]; r.days.push(d); if (r.days.length > 400) r.days = r.days.slice(-400);
    r.streak = prev && dayNum(d) - dayNum(prev) === 1 ? r.streak + 1 : 1; r.best = Math.max(r.best, r.streak);
    r.todayT = {}; dirty = true; check(); save(); return true;
  }
  return {
    data: r, points, level: () => lv,
    visit,
    time(kind, dt) { r.t[kind] = (r.t[kind] || 0) + dt; const d = today(); if (r.todayD !== d) { r.todayD = d; r.todayT = {}; } r.todayT[kind] = (r.todayT[kind] || 0) + dt; dirty = true; },
    add(kind, k = 1) { r.n[kind] = (r.n[kind] || 0) + k; dirty = true; check(); },
    zone(z) { if (!r.zones.includes(z)) { r.zones.push(z); dirty = true; check(); } },
    tick(now) { if (dirty && now - lastSave > 5) { lastSave = now; check(); save(); } },
    save,
  };
}
