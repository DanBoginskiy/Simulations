/* Спільне для сторінкових тестів: перелік сторінок і детермінований час. */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
export const SECTIONS = ['Analytic-Geometry', 'Mechanics', 'Theoretical-Mechanics', 'basic_physics', 'math_analysis', 'physics_tasks'];

function htmlIn(dir){
  const p = path.join(ROOT, dir);
  if (!fs.existsSync(p)) return [];
  const out = [];
  for (const e of fs.readdirSync(p, {withFileTypes: true}).sort((a, b) => a.name.localeCompare(b.name))){
    if (e.isDirectory()) out.push(...htmlIn(path.join(dir, e.name)));
    else if (e.name.endsWith('.html')) out.push(path.join(dir, e.name));
  }
  return out;
}
export const originals = () => SECTIONS.flatMap(htmlIn);
export const built = () => htmlIn('dist');
export const PILOTS = ['Mechanics/inertial-frames.html', 'basic_physics/00-kinematics-rotation.html', 'basic_physics/09-magnetic-field-forces.html'];
export const fileUrl = rel => pathToFileURL(path.join(ROOT, rel)).href;

/* Заморожений час. Сторінки анімуються циклом requestAnimationFrame з dt від
   performance.now(): підміняємо обидва й проганяємо кадри самі, сталим кроком
   1/60 с. Math.random засіяно (mulberry32), Date.now прив'язано до того самого
   годинника — дві версії сторінки бачать однакову послідовність усього. */
export const FREEZE = `(() => {
  let now = 0;
  const q = [];
  performance.now = () => now;
  Date.now = () => 1767225600000 + Math.floor(now);
  window.requestAnimationFrame = cb => (q.push(cb), q.length);
  window.cancelAnimationFrame = () => {};
  let a = 20261106;
  Math.random = () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  window.__frames = n => { for (let i = 0; i < n; i++){ now += 1000 / 60; for (const cb of q.splice(0)) cb(now); } };
  /* що намальовано на полотні текстом — для звірки чисел */
  window.__drawn = [];
  const ft = CanvasRenderingContext2D.prototype.fillText;
  CanvasRenderingContext2D.prototype.fillText = function(t, ...r){ window.__drawn.push(String(t)); return ft.call(this, t, ...r); };
})();`;

/* Числа сторінки: увесь видимий текст, текст на полотнах за останні кадри і
   числові поля стану активного модуля. */
export const SNAPSHOT = `(() => {
  const mid = typeof ACT !== 'undefined' ? ACT : null;
  const st = [];
  if (mid && typeof MODULES !== 'undefined'){
    const M = MODULES[mid];
    for (const k of Object.keys(M).sort()){
      const v = M[k];
      if (typeof v === 'number' && isFinite(v)) st.push(k + '=' + v.toPrecision(12));
    }
  }
  return {module: mid, text: document.body.innerText, drawn: window.__drawn.slice(), state: st};
})()`;

/* Попіксельна різниця двох PNG — у самому браузері, без залежностей. */
export async function pixelDiff(page, a, b){
  return page.evaluate(async ([a, b]) => {
    const load = src => new Promise((ok, no) => { const i = new Image(); i.onload = () => ok(i); i.onerror = no; i.src = src; });
    const [A, B] = await Promise.all([load(a), load(b)]);
    if (A.width !== B.width || A.height !== B.height) return {size: [A.width, A.height, B.width, B.height], diff: -1};
    const c = document.createElement('canvas'); c.width = A.width; c.height = A.height;
    const g = c.getContext('2d');
    g.drawImage(A, 0, 0); const da = g.getImageData(0, 0, c.width, c.height).data;
    g.clearRect(0, 0, c.width, c.height);
    g.drawImage(B, 0, 0); const db = g.getImageData(0, 0, c.width, c.height).data;
    let n = 0;
    for (let i = 0; i < da.length; i += 4)
      if (da[i] !== db[i] || da[i + 1] !== db[i + 1] || da[i + 2] !== db[i + 2] || da[i + 3] !== db[i + 3]) n++;
    return {diff: n, total: da.length / 4};
  }, ['data:image/png;base64,' + a.toString('base64'), 'data:image/png;base64,' + b.toString('base64')]);
}

export const WIDTHS = [[390, 844], [820, 1180], [1280, 900]];

/* Відкрити сторінку із замороженим часом, увімкнути модуль, прогнати кадри,
   зняти знімок і числа. Однаковий сценарій для оригіналу і для dist/. */
export async function capture(page, rel, [w, h], mid, {fullPage = true} = {}){
  await page.setViewportSize({width: w, height: h});
  await page.addInitScript(FREEZE);
  await page.goto(fileUrl(rel), {waitUntil: 'load'});
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(() => window.__frames(30));
  if (mid) await page.evaluate(id => activate(id), mid);
  await page.evaluate(() => { window.__frames(60); window.__drawn.length = 0; window.__frames(5); });
  const snap = await page.evaluate(SNAPSHOT);
  const png = await page.screenshot({fullPage, animations: 'disabled', caret: 'hide'});
  return {png, snap};
}
export async function modulesOf(page, rel){
  await page.goto(fileUrl(rel), {waitUntil: 'load'});
  return page.evaluate(() => Object.keys(MODULES));
}
