// 단풍마을 소리 — 녹음 파일 없이 Web Audio로 모두 합성
// 마을: 오르골·칼림바 즉흥 음악 + 바람·새·낙엽
// 절: 목탁 + 반야심경 독경(한글 음절의 모음으로 목소리 합성) + 범종 + 풍경
// 교회: 오르간 찬송가·크리스마스 캐럴 (작곡 1900년 이전, 퍼블릭 도메인 선율)
// 성당: 성가대(합창 합성) + 오르간 + 종 (그레고리오 성가풍 키리에는 자작 선율)

export const HEART_SUTRA = [
  '마하반야바라밀다심경',
  '관자재보살 행심반야바라밀다시 조견오온개공 도일체고액',
  '사리자 색불이공 공불이색 색즉시공 공즉시색 수상행식 역부여시',
  '사리자 시제법공상 불생불멸 불구부정 부증불감',
  '시고 공중무색 무수상행식 무안이비설신의 무색성향미촉법',
  '무안계 내지 무의식계 무무명 역무무명진 내지 무노사 역무노사진',
  '무고집멸도 무지역무득 이무소득고',
  '보리살타 의반야바라밀다고 심무가애 무가애고 무유공포',
  '원리전도몽상 구경열반 삼세제불 의반야바라밀다고',
  '득아뇩다라삼먁삼보리 고지 반야바라밀다',
  '시대신주 시대명주 시무상주 시무등등주',
  '능제일체고 진실불허 고설 반야바라밀다주 즉설주왈',
  '아제아제 바라아제 바라승아제 모지 사바하',
  '아제아제 바라아제 바라승아제 모지 사바하',
  '아제아제 바라아제 바라승아제 모지 사바하',
];

// ---------------------------------------------------------------- 음 이름 → 주파수
const NOTE = { C: -9, D: -7, E: -5, F: -4, G: -2, A: 0, B: 2 };
export function hz(n) {
  if (n === 'R') return 0;
  const m = /^([A-G])([#b]?)(\d)$/.exec(n);
  let s = NOTE[m[1]] + (m[2] === '#' ? 1 : m[2] === 'b' ? -1 : 0) + (parseInt(m[3]) - 4) * 12;
  return 440 * Math.pow(2, s / 12);
}
const P = s => s.trim().split(/\s+/).map(t => { const [n, d] = t.split(':'); return [n, parseFloat(d)]; });

// 퍼블릭 도메인 선율 (박 단위: 4분음표 = 1)
export const SONGS = {
  church: [
    { title: '기쁘다 구주 오셨네 (Joy to the World, 1839)', key: 'D', bpm: 96, mel: P(`
      D5:1 C#5:0.75 B4:0.25 A4:1.5 G4:0.5 F#4:1 E4:1 D4:1.5 A4:0.5 B4:1.5 B4:0.5 C#5:1.5 C#5:0.5 D5:3
      D5:0.5 D5:0.5 C#5:0.5 B4:0.5 A4:0.5 A4:0.75 G4:0.25 F#4:0.5 D5:0.5 D5:0.5 C#5:0.5 B4:0.5 A4:0.5 A4:0.75 G4:0.25 F#4:0.5
      F#4:0.5 F#4:0.5 F#4:0.5 F#4:0.5 F#4:0.25 G4:0.25 A4:1.5 G4:0.25 F#4:0.25 E4:0.5 E4:0.5 E4:0.5 E4:0.25 F#4:0.25 G4:1.5
      F#4:0.25 E4:0.25 D4:0.5 D5:1 B4:0.5 A4:0.75 G4:0.25 F#4:0.5 G4:0.5 F#4:1 E4:1 D4:3 R:1`) },
    { title: '나 같은 죄인 살리신 (Amazing Grace, 1835)', key: 'G', bpm: 72, meter: 3, mel: P(`
      D4:1 G4:2 B4:0.5 G4:0.5 B4:2 A4:1 G4:2 E4:1 D4:2 D4:1 G4:2 B4:0.5 G4:0.5 B4:2 A4:1 D5:3 D5:2
      B4:1 D5:1.5 B4:0.5 D5:0.5 B4:0.5 G4:2 D4:1 E4:1.5 G4:0.5 G4:0.5 E4:0.5 D4:2 D4:1 G4:2 B4:0.5 G4:0.5 B4:2 A4:1 G4:3 R:2`) },
    { title: '징글벨 (Jingle Bells, 1857)', key: 'G', bpm: 120, bells: true, mel: P(`
      B4:1 B4:1 B4:2 B4:1 B4:1 B4:2 B4:1 D5:1 G4:1.5 A4:0.5 B4:4
      C5:1 C5:1 C5:1.5 C5:0.5 C5:1 B4:1 B4:1 B4:0.5 B4:0.5 B4:1 A4:1 A4:1 B4:1 A4:2 D5:2
      B4:1 B4:1 B4:2 B4:1 B4:1 B4:2 B4:1 D5:1 G4:1.5 A4:0.5 B4:4
      C5:1 C5:1 C5:1.5 C5:0.5 C5:1 B4:1 B4:1 B4:0.5 B4:0.5 D5:1 D5:1 C5:1 A4:1 G4:4 R:2`) },
    { title: '고요한 밤 거룩한 밤 (Silent Night, 1818)', key: 'C', bpm: 54, meter: 3, mel: P(`
      G4:1.5 A4:0.5 G4:1 E4:3 G4:1.5 A4:0.5 G4:1 E4:3 D5:2 D5:1 B4:3 C5:2 C5:1 G4:3
      A4:2 A4:1 C5:1.5 B4:0.5 A4:1 G4:1.5 A4:0.5 G4:1 E4:3 A4:2 A4:1 C5:1.5 B4:0.5 A4:1 G4:1.5 A4:0.5 G4:1 E4:3
      D5:2 D5:1 F5:1.5 D5:0.5 B4:1 C5:3 E5:3 C5:1.5 G4:0.5 E4:1 G4:1.5 F4:0.5 D4:1 C4:6`) },
  ],
  cathedral: [
    { title: '키리에 — 그레고리오 성가풍 (자작 선율)', key: 'D', bpm: 66, chant: true, vowels: 'i i e e e i o', mel: P(`
      D4:1 F4:1 E4:1 G4:1 F4:1 E4:1 D4:2 R:0.5 A4:1 A4:1 C5:1 B4:0.5 A4:0.5 G4:1 A4:2 R:0.5
      F4:1 G4:1 A4:1 G4:1 F4:1 E4:1 F4:1 D4:3 R:1.5 A4:1 C5:1 D5:1 C5:1 A4:1 G4:1 A4:2 R:0.5
      F4:1 E4:1 G4:1 F4:1 E4:1 D4:1 C4:1 D4:3 R:2`) },
    { title: '오소서 오소서 임마누엘 (Veni Emmanuel, 15세기)', key: 'Em', bpm: 76, choir: true, mel: P(`
      E4:1 G4:1 B4:1 B4:1 B4:1 A4:1 C5:1 B4:1 A4:1 G4:2 R:1 A4:1 B4:1 G4:1 E4:1 G4:1 A4:1 F#4:1 E4:1 D4:1 E4:3 R:1
      A4:1 A4:1 E4:1 E4:1 F#4:1 G4:2 F#4:1 E4:1 D4:3 R:1 G4:1 A4:1 B4:1 B4:1 B4:1 A4:1 C5:1 B4:1 A4:1 G4:2 R:1
      D5:2 D5:2 B4:2 R:1 B4:1 B4:1 A4:1 C5:1 B4:1 A4:1 G4:2 R:1 A4:1 B4:1 G4:1 E4:1 G4:1 A4:1 F#4:1 E4:1 D4:1 E4:4 R:2`) },
    { title: '고요한 밤 (Stille Nacht, 1818 오베른도르프 성당)', key: 'C', bpm: 52, choir: true, meter: 3, mel: P(`
      G4:1.5 A4:0.5 G4:1 E4:3 G4:1.5 A4:0.5 G4:1 E4:3 D5:2 D5:1 B4:3 C5:2 C5:1 G4:3
      A4:2 A4:1 C5:1.5 B4:0.5 A4:1 G4:1.5 A4:0.5 G4:1 E4:3 A4:2 A4:1 C5:1.5 B4:0.5 A4:1 G4:1.5 A4:0.5 G4:1 E4:3
      D5:2 D5:1 F5:1.5 D5:0.5 B4:1 C5:3 E5:3 C5:1.5 G4:0.5 E4:1 G4:1.5 F4:0.5 D4:1 C4:6 R:2`) },
  ],
};

// 조성별 화음 (I, IV, V, vi)
const KEYS = {
  C: { I: ['C', 'E', 'G'], IV: ['F', 'A', 'C'], V: ['G', 'B', 'D'], vi: ['A', 'C', 'E'], root: { I: 'C3', IV: 'F2', V: 'G2', vi: 'A2' } },
  D: { I: ['D', 'F#', 'A'], IV: ['G', 'B', 'D'], V: ['A', 'C#', 'E'], vi: ['B', 'D', 'F#'], root: { I: 'D3', IV: 'G2', V: 'A2', vi: 'B2' } },
  G: { I: ['G', 'B', 'D'], IV: ['C', 'E', 'G'], V: ['D', 'F#', 'A'], vi: ['E', 'G', 'B'], root: { I: 'G2', IV: 'C3', V: 'D3', vi: 'E3' } },
  Em: { I: ['E', 'G', 'B'], IV: ['A', 'C', 'E'], V: ['B', 'D#', 'F#'], vi: ['D', 'F#', 'A'], root: { I: 'E2', IV: 'A2', V: 'B2', vi: 'D3' } },
};
const PC = n => n.replace(/\d/, '');
function pickChord(key, notes) {
  const K = KEYS[key]; let best = 'I', sc = -1;
  for (const c of ['I', 'V', 'IV', 'vi']) {
    let s = 0; notes.forEach(([n, d], i) => { if (K[c].includes(PC(n))) s += d * (i === 0 ? 1.5 : 1); });
    if (c === 'I') s += 0.3;
    if (s > sc) { sc = s; best = c; }
  }
  return best;
}
const chordNotes = (key, c) => { let prev = 0; return KEYS[key][c].map(p => { let f = hz(p + '3'); while (f < prev) f *= 2; prev = f; return f; }); };

// ---------------------------------------------------------------- 엔진
export function createAudio() {
  const ctx = new (window.AudioContext || window.webkitAudioContext)();
  const master = ctx.createGain(); master.gain.value = 0.8;
  const comp = ctx.createDynamicsCompressor(); comp.threshold.value = -16; comp.ratio.value = 3;
  master.connect(comp).connect(ctx.destination);

  function impulse(sec, decay, bright = 1) {
    const n = Math.floor(ctx.sampleRate * sec), b = ctx.createBuffer(2, n, ctx.sampleRate);
    for (let c = 0; c < 2; c++) {
      const d = b.getChannelData(c); let lp = 0;
      for (let i = 0; i < n; i++) { const w = Math.random() * 2 - 1; lp = lp + (w - lp) * bright; d[i] = lp * Math.pow(1 - i / n, decay); }
    }
    return b;
  }
  const noiseBuf = (() => { const n = ctx.sampleRate * 2, b = ctx.createBuffer(1, n, ctx.sampleRate), d = b.getChannelData(0); for (let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1; return b; })();

  function bus(revSec, revDecay, wet, bright) {
    const g = ctx.createGain(); g.gain.value = 0;
    const dry = ctx.createGain(); dry.gain.value = 1 - wet * 0.5;
    const rv = ctx.createConvolver(); rv.buffer = impulse(revSec, revDecay, bright);
    const wg = ctx.createGain(); wg.gain.value = wet;
    const input = ctx.createGain();
    input.connect(dry).connect(g); input.connect(rv).connect(wg).connect(g); g.connect(master);
    return { input, out: g, level: 0 };
  }
  const B = {
    village: bus(2.2, 3, 0.35, 0.5), temple: bus(3.2, 2.5, 0.45, 0.35),
    church: bus(2.6, 2.8, 0.4, 0.45), cathedral: bus(6.5, 2.2, 0.7, 0.3),
  };
  B.village.out.gain.value = 1;

  // ---------------- 소리 재료
  const organWave = ctx.createPeriodicWave(new Float32Array([0, 1, 0.55, 0.35, 0.3, 0.12, 0.1, 0.05, 0.12]), new Float32Array(9));
  function organ(dest, f, t, d, v = 0.12) {
    if (!f) return;
    for (const det of [-3, 3]) {
      const o = ctx.createOscillator(); o.setPeriodicWave(organWave); o.frequency.value = f; o.detune.value = det;
      const g = ctx.createGain(); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(v, t + 0.04); g.gain.setValueAtTime(v, t + Math.max(0.05, d - 0.06)); g.gain.linearRampToValueAtTime(0, t + d + 0.12);
      o.connect(g).connect(dest); o.start(t); o.stop(t + d + 0.2);
    }
  }
  function pluck(dest, f, t, v = 0.12, dec = 1.6, h = 4) {      // 오르골·칼림바
    const o = ctx.createOscillator(); o.type = 'sine'; o.frequency.value = f;
    const o2 = ctx.createOscillator(); o2.type = 'sine'; o2.frequency.value = f * h;
    const g = ctx.createGain(), g2 = ctx.createGain();
    g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(v, t + 0.005); g.gain.exponentialRampToValueAtTime(0.0005, t + dec);
    g2.gain.setValueAtTime(0, t); g2.gain.linearRampToValueAtTime(v * 0.25, t + 0.003); g2.gain.exponentialRampToValueAtTime(0.0005, t + dec * 0.25);
    o.connect(g).connect(dest); o2.connect(g2).connect(dest); o.start(t); o2.start(t); o.stop(t + dec + 0.1); o2.stop(t + dec);
  }
  function pad(dest, freqs, t, d, v = 0.035, type = 'triangle', cutoff = 1200) {
    const f = ctx.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = cutoff;
    const g = ctx.createGain(); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(v, t + d * 0.3); g.gain.linearRampToValueAtTime(v * 0.8, t + d * 0.75); g.gain.linearRampToValueAtTime(0, t + d + 0.8);
    f.connect(g).connect(dest);
    for (const fr of freqs) for (const det of [-6, 6]) { const o = ctx.createOscillator(); o.type = type; o.frequency.value = fr; o.detune.value = det; o.connect(f); o.start(t); o.stop(t + d + 1); }
  }
  function noiseHit(dest, t, freq, q, v, dec, type = 'bandpass') {
    const s = ctx.createBufferSource(); s.buffer = noiseBuf; s.playbackRate.value = 0.8 + Math.random() * 0.4;
    const f = ctx.createBiquadFilter(); f.type = type; f.frequency.value = freq; f.Q.value = q;
    const g = ctx.createGain(); g.gain.setValueAtTime(v, t); g.gain.exponentialRampToValueAtTime(0.0005, t + dec);
    s.connect(f).connect(g).connect(dest); s.start(t, Math.random()); s.stop(t + dec + 0.05);
  }
  function moktak(t, v = 0.5) {
    const d = B.temple.input;
    const o = ctx.createOscillator(); o.type = 'sine'; o.frequency.setValueAtTime(820, t); o.frequency.exponentialRampToValueAtTime(690, t + 0.08);
    const g = ctx.createGain(); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(v, t + 0.002); g.gain.exponentialRampToValueAtTime(0.001, t + 0.16);
    const o2 = ctx.createOscillator(); o2.type = 'sine'; o2.frequency.value = 1310;
    const g2 = ctx.createGain(); g2.gain.setValueAtTime(v * 0.35, t); g2.gain.exponentialRampToValueAtTime(0.001, t + 0.05);
    o.connect(g).connect(d); o2.connect(g2).connect(d); o.start(t); o2.start(t); o.stop(t + 0.2); o2.stop(t + 0.08);
    noiseHit(d, t, 2400, 6, v * 0.5, 0.025);
  }
  function bell(dest, f0, t, v = 0.3, dec = 14, beat = 0.4) {     // 범종·성당 종 (맥놀이)
    const parts = [[1, 1], [2.0, 0.5], [2.76, 0.35], [5.4, 0.18], [8.9, 0.08], [0.5, 0.6]];
    for (const [m, a] of parts) for (const db of [0, beat]) {
      const o = ctx.createOscillator(); o.type = 'sine'; o.frequency.value = f0 * m + db;
      const g = ctx.createGain(); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(v * a * 0.5, t + 0.01); g.gain.exponentialRampToValueAtTime(0.0005, t + dec / Math.sqrt(m));
      o.connect(g).connect(dest); o.start(t); o.stop(t + dec + 0.2);
    }
  }
  function chime(dest, t) { const f = [1760, 2093, 2349, 2637, 3136][Math.floor(Math.random() * 5)]; pluck(dest, f, t, 0.04, 2.5, 2.7); }
  function sleigh(dest, t, v = 0.05) { for (let i = 0; i < 3; i++) noiseHit(dest, t + i * 0.025, 7000 + Math.random() * 2000, 4, v, 0.08, 'highpass'); }

  // ---------------- 목소리 (포먼트 합성)
  const FORM = { a: [700, 1220, 2600], e: [480, 1850, 2500], eo: [580, 1000, 2500], o: [400, 760, 2400], u: [320, 800, 2250], eu: [330, 1400, 2400], i: [280, 2250, 3000], m: [250, 1000, 2200] };
  const JUNG = ['a', 'e', 'a', 'e', 'eo', 'e', 'eo', 'e', 'o', 'a', 'e', 'e', 'o', 'u', 'eo', 'e', 'i', 'u', 'eu', 'i', 'i'];
  const NASAL = new Set([4, 16, 21]);   // 받침 ㄴ ㅁ ㅇ
  const HISS = new Set([9, 10, 12, 13, 14, 18]);   // 초성 ㅅ ㅆ ㅈ ㅉ ㅊ ㅎ
  function voice(dest, n = 3, base = 110, spread = 7, level = 0.08, src = 'sawtooth') {
    const out = ctx.createGain(); out.gain.value = 0; out.connect(dest);
    const fs = [0, 1, 2].map(k => { const f = ctx.createBiquadFilter(); f.type = 'bandpass'; f.Q.value = [8, 12, 14][k]; f.frequency.value = FORM.a[k]; const g = ctx.createGain(); g.gain.value = [1, 0.6, 0.25][k]; f.connect(g).connect(out); return f; });
    const oscs = [];
    for (let i = 0; i < n; i++) {
      const o = ctx.createOscillator(); o.type = src; o.frequency.value = base; o.detune.value = (i - (n - 1) / 2) * spread;
      const vib = ctx.createOscillator(); vib.frequency.value = 4.5 + Math.random(); const vg = ctx.createGain(); vg.gain.value = 3; vib.connect(vg).connect(o.detune);
      fs.forEach(f => o.connect(f)); o.start(); vib.start(); oscs.push(o);
    }
    return {
      out, fs, oscs, level,
      vowel(v, t, tau = 0.03) { FORM[v].forEach((fr, k) => fs[k].frequency.setTargetAtTime(fr * (base > 180 ? 1.15 : 1), t, tau)); },
      pitch(f, t, tau = 0.04) { oscs.forEach(o => o.frequency.setTargetAtTime(f, t, tau)); },
      amp(a, t, tau = 0.03) { out.gain.setTargetAtTime(a * level, t, tau); },
    };
  }
  let monks = null, choir = null, choirLow = null, cSing = null, cSingLow = null, churchSing = false;

  // ---------------- 반야심경 스케줄
  const sutra = []; HEART_SUTRA.forEach((line, li) => { [...line].forEach(ch => sutra.push({ ch, li })); sutra.push({ ch: '\n', li }); });
  const SYL = 0.34; let sIdx = 0, sT = 0, nextBell = 0, nextChime = 0;
  const listeners = { syllable: null, song: null };

  function scheduleTemple(now, ahead) {
    if (!monks) {
      monks = voice(B.temple.input, 4, 110, 9, 0.11);
      const lo = voice(B.temple.input, 2, 55, 5, 0.06); monks.lo = lo;
    }
    if (sT < now) sT = now + 0.05;
    if (!nextBell) nextBell = now + 1.5;
    while (sT < now + ahead) {
      const s = sutra[sIdx]; const t = sT; let dur = SYL;
      if (s.ch === ' ' ) { dur = 0; }
      else if (s.ch === '\n') { dur = SYL * 2; monks.amp(0, t, 0.06); monks.lo.amp(0, t, 0.06); moktak(t, 0.32); }
      else {
        const c = s.ch.charCodeAt(0) - 0xAC00, cho = Math.floor(c / 588), jung = Math.floor((c % 588) / 28), jong = c % 28;
        const v = JUNG[jung] || 'a';
        const endLine = sutra[sIdx + 1] && sutra[sIdx + 1].ch === '\n';
        const f = endLine ? 98 : 110 * (1 + 0.004 * Math.sin(sIdx));
        for (const vv of [monks, monks.lo]) {
          vv.pitch(vv === monks ? f : f / 2, t); vv.vowel(v, t);
          vv.amp(0.25, t, 0.01); vv.amp(1, t + 0.03, 0.03); vv.amp(0.55, t + SYL * 0.72, 0.03);
          if (NASAL.has(jong)) vv.vowel('m', t + SYL * 0.6, 0.03);
        }
        if (HISS.has(cho)) noiseHit(B.temple.input, t, 5200, 2, 0.05, 0.06);
        moktak(t, sIdx % 2 === 0 ? 0.5 : 0.42);
        const myIdx = sIdx;
        if (listeners.syllable) { const ms = Math.max(0, (t - ctx.currentTime) * 1000); setTimeout(() => listeners.syllable(s.li, myIdx, sutra), ms); }
      }
      sT += dur; sIdx = (sIdx + 1) % sutra.length;
      if (sIdx === 0) sT += 2.5;
    }
    if (nextBell < now + ahead) { bell(B.temple.input, 64, nextBell, 0.35, 16, 0.35); nextBell += 38 + Math.random() * 10; }
    if (nextChime < now + ahead) { chime(B.temple.input, nextChime); nextChime = (nextChime || now) + 3 + Math.random() * 7; }
  }

  // ---------------- 노래 스케줄 (교회·성당)
  function songPlayer(zone) {
    const st = { i: Math.floor(Math.random() * SONGS[zone].length), n: 0, t: 0, beat: 0, cur: null };
    return st;
  }
  const players = { church: songPlayer('church'), cathedral: songPlayer('cathedral') };
  let nextToll = 0;
  function scheduleSong(zone, now, ahead) {
    const S = players[zone], dest = B[zone].input;
    if (S.t < now) { S.t = now + 0.3; }
    while (S.t < now + ahead) {
      const song = SONGS[zone][S.i]; S.cur = song;
      if (S.n === 0 && listeners.song) { const ms = Math.max(0, (S.t - ctx.currentTime) * 1000); setTimeout(() => listeners.song(zone, song.title), ms); }
      const spb = 60 / song.bpm; const [n, d] = song.mel[S.n]; const f = hz(n); const t = S.t, dur = d * spb;
      if (song.chant || song.choir) {
        if (!choir) { choir = voice(B.cathedral.input, 6, 220, 14, 0.07); choirLow = voice(B.cathedral.input, 4, 110, 10, 0.05); }
        const vw = song.chant ? 'eaiou'.split('')[S.n % 5] : ['a', 'o', 'a', 'e', 'o'][S.n % 5];
        if (f) {
          choir.pitch(f, t, 0.05); choirLow.pitch(f / 2, t, 0.05); choir.vowel(vw, t, 0.08); choirLow.vowel(vw, t, 0.08);
          choir.amp(1, t, 0.06); choirLow.amp(song.chant ? 0.8 : 0.6, t, 0.06);
          choir.amp(0.75, t + dur * 0.8, 0.05); choirLow.amp(0.45, t + dur * 0.8, 0.05);
        } else { choir.amp(0, t, 0.15); choirLow.amp(0, t, 0.15); }
        if (song.chant && S.n === 0) organ(dest, hz('D2'), t, 60 / song.bpm * 40, 0.04);
      } else if (f) organ(dest, f, t, dur * 0.95, 0.09);
      if (zone === 'church' && !song.chant && !song.choir) {          // 성가대에 함께하면 오르간 선율을 여러 목소리로 같이 부름
        if (churchSing && !cSing) { cSing = voice(B.church.input, 7, 262, 16, 0.075); cSingLow = voice(B.church.input, 5, 131, 12, 0.05); }
        if (cSing) {
          if (churchSing && f) {
            const vw = ['a', 'o', 'e', 'a', 'o', 'i'][S.n % 6];
            cSing.pitch(f, t, 0.05); cSingLow.pitch(f / 2, t, 0.05); cSing.vowel(vw, t, 0.08); cSingLow.vowel(vw, t, 0.08);
            cSing.amp(1, t, 0.05); cSingLow.amp(0.7, t, 0.05); cSing.amp(0.7, t + dur * 0.85, 0.04); cSingLow.amp(0.45, t + dur * 0.85, 0.04);
          } else { cSing.amp(0, t, 0.2); cSingLow.amp(0, t, 0.2); }
        }
      }
      // 화음: 박 묶음마다 (2박)
      const meter = song.meter || 4, grp = meter === 3 ? 3 : 2;
      if (!song.chant) {
        const startBeat = S.beat, endBeat = S.beat + d;
        if (Math.floor(endBeat / grp - 1e-6) > Math.floor(startBeat / grp - 1e-6) || S.n === 0) {
          const gStart = Math.ceil(startBeat / grp - 1e-6) * grp; const tStart = t + (gStart - startBeat) * spb;
          const win = []; let acc = 0; for (let k = S.n; k < song.mel.length && acc < grp; k++) { win.push(song.mel[k]); acc += song.mel[k][1]; }
          const c = pickChord(song.key, win.filter(w => w[0] !== 'R'));
          const tri = chordNotes(song.key, c, 3), root = hz(KEYS[song.key].root[c]);
          if (song.choir) { pad(dest, tri, tStart, grp * spb, 0.02, 'sine', 900); organ(dest, root, tStart, grp * spb, 0.05); }
          else { tri.forEach(fr => organ(dest, fr, tStart, grp * spb * 0.98, 0.04)); organ(dest, root, tStart, grp * spb * 0.98, 0.07); }
          if (song.bells) for (let k = 0; k < grp * 2; k++) sleigh(dest, tStart + k * spb / 2, 0.035);
        }
      }
      S.beat += d; S.t += dur; S.n++;
      if (S.n >= song.mel.length) {
        S.n = 0; S.beat = 0; S.i = (S.i + 1) % SONGS[zone].length; S.t += 3.0;
        if (zone === 'cathedral') { choir && choir.amp(0, S.t - 2.8, 0.3); choirLow && choirLow.amp(0, S.t - 2.8, 0.3); bell(dest, 98, S.t - 2.5, 0.25, 9, 0.6); }
      }
    }
    if (zone === 'cathedral') { if (!nextToll) nextToll = now + 0.5; if (nextToll < now + ahead) { bell(dest, 131, nextToll, 0.12, 8, 0.5); nextToll += 45; } }
  }

  // ---------------- 마을 즉흥 음악 + 자연 소리
  const PENTA = ['C4', 'D4', 'E4', 'G4', 'A4', 'C5', 'D5', 'E5', 'G5', 'A5'].map(hz);
  const PROG = [['C3', 'E3', 'G3', 'B3'], ['A2', 'C3', 'E3', 'G3'], ['F2', 'A2', 'C3', 'E3'], ['G2', 'B2', 'D3', 'A3']].map(c => c.map(hz));
  let vT = 0, vStep = 0, nextBird = 0, nextRustle = 0, last = 4;
  let wind = null;
  function scheduleVillage(now, ahead) {
    const d = B.village.input, spb = 60 / 68 / 2;
    if (!wind) {
      const s = ctx.createBufferSource(); s.buffer = noiseBuf; s.loop = true;
      const f = ctx.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = 500;
      const g = ctx.createGain(); g.gain.value = 0.035;
      const l = ctx.createOscillator(); l.frequency.value = 0.07; const lg = ctx.createGain(); lg.gain.value = 300; l.connect(lg).connect(f.frequency);
      s.connect(f).connect(g).connect(master); s.start(); l.start(); wind = g;
    }
    if (vT < now) vT = now + 0.1;
    while (vT < now + ahead) {
      if (vStep % 16 === 0) pad(d, PROG[(vStep / 16) % 4], vT, spb * 16, 0.022, 'sine', 900);
      if (vStep % 16 === 0) pluck(d, PROG[(vStep / 16) % 4][0], vT, 0.09, 2.5, 3);
      const p = vStep % 4 === 0 ? 0.55 : vStep % 2 === 0 ? 0.3 : 0.14;
      if (Math.random() < p) {
        last = Math.max(0, Math.min(PENTA.length - 1, last + Math.round((Math.random() - 0.5) * 4)));
        pluck(d, PENTA[last], vT, 0.06 + Math.random() * 0.04, 1.8, 4);
      }
      vT += spb; vStep++;
    }
    if (nextBird < now + ahead) {
      const t = Math.max(nextBird, now), n = 2 + Math.floor(Math.random() * 4), f0 = 2600 + Math.random() * 1800;
      for (let i = 0; i < n; i++) {
        const o = ctx.createOscillator(); o.type = 'sine'; const g = ctx.createGain(); const tt = t + i * 0.13;
        o.frequency.setValueAtTime(f0, tt); o.frequency.exponentialRampToValueAtTime(f0 * (1.3 + Math.random() * 0.3), tt + 0.06); o.frequency.exponentialRampToValueAtTime(f0 * 0.9, tt + 0.1);
        g.gain.setValueAtTime(0, tt); g.gain.linearRampToValueAtTime(0.025, tt + 0.01); g.gain.exponentialRampToValueAtTime(0.0005, tt + 0.11);
        o.connect(g).connect(d); o.start(tt); o.stop(tt + 0.13);
      }
      nextBird = t + 2.5 + Math.random() * 6;
    }
    if (nextRustle < now + ahead) { const t = Math.max(nextRustle, now); for (let i = 0; i < 6; i++) noiseHit(d, t + i * 0.05, 3000 + Math.random() * 2000, 1.2, 0.012, 0.12); nextRustle = t + 4 + Math.random() * 8; }
  }

  // ---------------- 구역 음량
  const target = { village: 1, temple: 0, church: 0, cathedral: 0 };
  function setLevels(lv) {
    Object.assign(target, lv);
    for (const k in B) B[k].out.gain.setTargetAtTime(target[k], ctx.currentTime, 0.6);
    if (wind) wind.gain.setTargetAtTime(0.035 * (0.4 + 0.6 * target.village), ctx.currentTime, 0.8);
  }
  function tick() {
    const now = ctx.currentTime, ahead = 0.4;
    scheduleVillage(now, ahead);
    if (target.temple > 0.003) scheduleTemple(now, ahead); else if (monks) { monks.amp(0, now, 0.2); monks.lo.amp(0, now, 0.2); sT = 0; }
    for (const z of ['church', 'cathedral']) if (target[z] > 0.003) scheduleSong(z, now, ahead); else players[z].t = 0;
  }
  let timer = null;
  return {
    ctx, listeners, setLevels,
    start() { ctx.resume(); if (!timer) timer = setInterval(tick, 100); },
    setVolume(v) { master.gain.setTargetAtTime(v, ctx.currentTime, 0.1); },
    nextSong(zone) { const S = players[zone]; if (!S) return; S.n = 0; S.beat = 0; S.i = (S.i + 1) % SONGS[zone].length; S.t = 0; if (choir) { choir.amp(0, ctx.currentTime, 0.1); choirLow.amp(0, ctx.currentTime, 0.1); } },
    chime() { const t = ctx.currentTime + 0.02; [2093, 2637, 3136].forEach((f, i) => pluck(master, f, t + i * 0.12, 0.05, 2.2, 2.7)); },
    moktakOnce(delay = 0.05) { moktak(ctx.currentTime + delay, 0.6); },
    setChurchChoir(on) { churchSing = on; if (!on && cSing) { cSing.amp(0, ctx.currentTime, 0.3); cSingLow.amp(0, ctx.currentTime, 0.3); } },
    coin() { const t = ctx.currentTime + 0.02; [0, 0.09, 0.15].forEach((d, i) => { pluck(master, [3520, 4186, 3951][i], t + d, 0.05, 0.5, 5); noiseHit(master, t + d, 6000, 6, 0.04, 0.05); }); bell(master, 392, t + 0.35, 0.06, 4, 0.3); },
    bless() { const t = ctx.currentTime + 0.02; [1047, 1319, 1568, 2093].forEach((f, i) => pluck(master, f, t + i * 0.18, 0.05, 3.2, 2.5)); pad(master, [262, 330, 392, 523], t, 3.5, 0.025, 'sine', 1400); },
    ring(zone) { const t = ctx.currentTime + 0.02; if (zone === 'temple') bell(B.temple.input, 64, t, 0.4, 16, 0.35); else if (zone === 'cathedral') bell(B.cathedral.input, 98, t, 0.3, 9, 0.6); else bell(B.church.input, 196, t, 0.2, 5, 0.8); },
  };
}
