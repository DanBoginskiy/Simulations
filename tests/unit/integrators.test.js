/* Фізичні тести інтеграторів рушія. Допуски — tests/TOLERANCES.md
   (записані до першого запуску; не послаблювати). */
import {describe, it, expect} from 'vitest';
import {rk4, verlet, euler, eulerCromer, verletN, eulerCromerN, advance} from '../../engine/integrators.js';
import {cross2} from '../../engine/vec.js';

/* ---------------- 1. гармонічний осцилятор ---------------- */
const W = 1, H = 0.01, N = 1e4;
const acc = x => -W * W * x;
const energy = (x, v) => 0.5 * (v * v + W * W * x * x);
/* Один крок кожного інтегратора у формі (x, v) → [x, v]. */
const STEP = {
  euler: (x, v, h) => { const y = euler(0, [x, v], h, (t, s) => [s[1], acc(s[0])]); return [y[0], y[1]]; },
  eulerCromer: (x, v, h) => eulerCromer(x, v, h, acc),
  verlet: (x, v, h) => verlet(x, v, h, acc),
  rk4: (x, v, h) => { const y = rk4(0, [x, v], h, (t, s) => [s[1], acc(s[0])]); return [y[0], y[1]]; },
};
function runOsc(step, n, h = H){
  let x = 1, v = 0, t = 0;
  const E0 = energy(x, v), Es = [E0], ups = [];
  for (let i = 0; i < n; i++){
    const [x1, v1] = step(x, v, h);
    if (x < 0 && x1 >= 0) ups.push(t + h * (-x) / (x1 - x));   // висхідний перетин нуля
    x = x1; v = v1; t += h; Es.push(energy(x, v));
  }
  const period = (ups[ups.length - 1] - ups[0]) / (ups.length - 1);
  return {E0, Es, period, x, v};
}
const maxDev = (Es, E0, a = 0, b = Es.length) => {
  let m = 0; for (let i = a; i < b; i++) m = Math.max(m, Math.abs(Es[i] / E0 - 1)); return m;
};
const T0 = 2 * Math.PI / W;

describe('гармонічний осцилятор: енергія за 10⁴ кроків', () => {
  it('явний Ейлер накачує енергію: росте щокроку, рівно як (1+h²ω²)^N', () => {
    const r = runOsc(STEP.euler, N);
    for (let i = 1; i < r.Es.length; i++) expect(r.Es[i]).toBeGreaterThan(r.Es[i - 1]);
    const theory = Math.pow(1 + H * H * W * W, N);
    expect(Math.abs(r.Es[N] / r.E0 / theory - 1)).toBeLessThanOrEqual(1e-9);
    expect(r.Es[N] / r.E0 - 1).toBeGreaterThan(0.5);
  });
  it('Ейлер–Кромер: дрейф енергії обмежений (≤1e-2), огинаюча не росте', () => {
    const r = runOsc(STEP.eulerCromer, N);
    expect(maxDev(r.Es, r.E0)).toBeLessThanOrEqual(1e-2);
    const long = runOsc(STEP.eulerCromer, 1e5);
    const early = maxDev(long.Es, long.E0, 0, 1e4 + 1), late = maxDev(long.Es, long.E0, 9e4, 1e5 + 1);
    expect(late).toBeLessThanOrEqual(early * 1.05);
  });
  it('швидкісний Верле: дрейф енергії обмежений (≤1e-4), огинаюча не росте', () => {
    const r = runOsc(STEP.verlet, N);
    expect(maxDev(r.Es, r.E0)).toBeLessThanOrEqual(1e-4);
    const long = runOsc(STEP.verlet, 1e5);
    const early = maxDev(long.Es, long.E0, 0, 1e4 + 1), late = maxDev(long.Es, long.E0, 9e4, 1e5 + 1);
    expect(late).toBeLessThanOrEqual(early * 1.05);
  });
  it('RK4: енергія повільно спадає, як (1 − h⁶/72 + h⁸/576)^N', () => {
    const r = runOsc(STEP.rk4, N);
    const g = 1 - Math.pow(H, 6) / 72 + Math.pow(H, 8) / 576;
    const theory = Math.pow(g, N) - 1;
    expect(Math.abs((r.Es[N] / r.E0 - 1) - theory)).toBeLessThanOrEqual(1e-11);
    expect(r.Es[N]).toBeLessThan(r.E0);
  });
});

describe('гармонічний осцилятор: період', () => {
  const tol = {euler: 1e-4, eulerCromer: 1e-4, verlet: 1e-4, rk4: 1e-7};
  for (const k of Object.keys(STEP)){
    it(`${k}: |T/T₀ − 1| ≤ ${tol[k]}`, () => {
      const r = runOsc(STEP[k], N);
      expect(Math.abs(r.period / T0 - 1)).toBeLessThanOrEqual(tol[k]);
    });
  }
});

/* ---------------- 2. задача Кеплера ---------------- */
const kepAcc = q => { const r2 = q[0] * q[0] + q[1] * q[1], r3 = r2 * Math.sqrt(r2); return [-q[0] / r3, -q[1] / r3]; };
const kepE = (q, v) => 0.5 * (v[0] * v[0] + v[1] * v[1]) - 1 / Math.hypot(q[0], q[1]);
function runKepler(kind, n = 2e4, h = 1e-3){
  let q = [1, 0], v = [0, 1.2];
  const L0 = cross2(q, v), E0 = kepE(q, v);
  let dL = 0, dE = 0;
  for (let i = 0; i < n; i++){
    if (kind === 'rk4'){
      const y = rk4(0, [...q, ...v], h, (t, s) => { const a = kepAcc(s); return [s[2], s[3], a[0], a[1]]; });
      q = [y[0], y[1]]; v = [y[2], y[3]];
    } else [q, v] = (kind === 'verlet' ? verletN : eulerCromerN)(q, v, h, kepAcc);
    dL = Math.max(dL, Math.abs(cross2(q, v) / L0 - 1));
    dE = Math.max(dE, Math.abs(kepE(q, v) / E0 - 1));
  }
  return {dL, dE};
}
describe('задача Кеплера: момент імпульсу', () => {
  it('Верле зберігає L до округлення (≤1e-11), енергію — в межах 1e-4', () => {
    const r = runKepler('verlet');
    expect(r.dL).toBeLessThanOrEqual(1e-11);
    expect(r.dE).toBeLessThanOrEqual(1e-4);
  });
  it('Ейлер–Кромер зберігає L до округлення (≤1e-11)', () => {
    expect(runKepler('eulerCromer').dL).toBeLessThanOrEqual(1e-11);
  });
  it('RK4: L зберігається наближено (≤1e-6)', () => {
    expect(runKepler('rk4').dL).toBeLessThanOrEqual(1e-6);
  });
});

/* ---------------- 3. кидок без опору ---------------- */
const g = 9.8, v0 = 20, al = Math.PI / 4, hP = 1e-3, nP = 2800;
const vx0 = v0 * Math.cos(al), vy0 = v0 * Math.sin(al);
const exact = t => [vx0 * t, vy0 * t - g * t * t / 2];
const fP = (t, s) => [s[2], s[3], 0, -g];
const accP = () => [0, -g];
function runProj(kind){
  let s = [0, 0, vx0, vy0], q = [0, 0], v = [vx0, vy0];
  for (let i = 0; i < nP; i++){
    if (kind === 'rk4') s = rk4(i * hP, s, hP, fP);
    else if (kind === 'euler') s = euler(i * hP, s, hP, fP);
    else { [q, v] = (kind === 'verlet' ? verletN : eulerCromerN)(q, v, hP, accP); s = [...q, ...v]; }
  }
  return {t: nP * hP, x: s[0], y: s[1]};
}
describe('кидок без опору проти аналітики', () => {
  for (const k of ['verlet', 'rk4']){
    it(`${k} точний для сталої сили (≤1e-9 м)`, () => {
      const r = runProj(k), [xe, ye] = exact(r.t);
      expect(Math.hypot(r.x - xe, r.y - ye)).toBeLessThanOrEqual(1e-9);
    });
  }
  it('явний Ейлер: похибка y рівно +g·h·t/2, x точний', () => {
    const r = runProj('euler'), [xe, ye] = exact(r.t);
    expect(Math.abs(r.x - xe)).toBeLessThanOrEqual(1e-9);
    expect(Math.abs((r.y - ye) - g * hP * r.t / 2)).toBeLessThanOrEqual(1e-9);
  });
  it('Ейлер–Кромер: похибка y рівно −g·h·t/2, x точний', () => {
    const r = runProj('eulerCromer'), [xe, ye] = exact(r.t);
    expect(Math.abs(r.x - xe)).toBeLessThanOrEqual(1e-9);
    expect(Math.abs((r.y - ye) + g * hP * r.t / 2)).toBeLessThanOrEqual(1e-9);
  });
  it('дальність (Верле, інтерполяція точки падіння) = v₀² sin2α / g з точністю 1e-6 м', () => {
    let q = [0, 0], v = [vx0, vy0], prev = q;
    for (;;){
      prev = q; [q, v] = verletN(q, v, hP, accP);
      if (q[1] < 0) break;
    }
    const R = prev[0] + (q[0] - prev[0]) * prev[1] / (prev[1] - q[1]);
    expect(Math.abs(R - v0 * v0 * Math.sin(2 * al) / g)).toBeLessThanOrEqual(1e-6);
  });
});

describe('advance: кадр розбивається на підкроки', () => {
  it('кінцевий час рівно t+dt, крок не довший за hMax', () => {
    const hs = [];
    const [t] = advance(0, [1, 0], 0.05, 0.004, (tt, s) => [s[1], -s[0]], (tt, y, h, f) => { hs.push(h); return rk4(tt, y, h, f); });
    expect(Math.abs(t - 0.05)).toBeLessThan(1e-12);
    expect(Math.max(...hs)).toBeLessThanOrEqual(0.004);
  });
});
