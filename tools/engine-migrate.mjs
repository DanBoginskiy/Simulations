#!/usr/bin/env node
/* Переносить сторінку серії на рушій: оригінал → src/<той самий шлях>.

   Інструмент консервативний: прибирає з власного скрипту сторінки лише ті
   оголошення, текст яких (без коментарів і пробілів, з CLR.→BRAND.) ДОСЛІВНО
   збігається з експортом engine/, і лише ті послідовності інструкцій, що
   дослівно збігаються з тілом функції-інсталятора рушія (watchCanvases,
   installFolding, installFullscreen). Решта лишається локальною — і
   перелічується у звіті як «розбіжність», щоб автор вирішив, що з нею робити.

     node tools/engine-migrate.mjs Mechanics/inertial-frames.html          # лише звіт
     node tools/engine-migrate.mjs --write basic_physics/09-*.html           # записати src/

   Оригінал не змінюється. Після запису сторінку збирають tools/build.mjs і
   звіряють із оригіналом tests/pages/pilots.spec.mjs.
*/
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {parse} from 'acorn';
import {engineExports} from './build.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

function strip(src){
  const cs = [];
  try { parse(src, {ecmaVersion: 'latest', sourceType: 'module', onComment: cs, allowReturnOutsideFunction: true}); }
  catch { try { parse(src, {ecmaVersion: 'latest', onComment: cs, allowReturnOutsideFunction: true}); } catch {} }
  let s = src;
  for (const c of cs.sort((a, b) => b.start - a.start)) s = s.slice(0, c.start) + s.slice(c.end);
  return s;
}
export const norm = src => strip(src).replace(/^\s*export\s+/, '').replace(/\bCLR\./g, 'BRAND.').replace(/\s+/g, '').replace(/;$/, '');

/* Варіанти, які не збігаються з рушієм дослівно, але поводяться так само за
   замовчуваних налаштувань рушія. Кожен рядок тут — доведена рівність, а не
   «схоже»: для txt/pill з 21 файлу різниця лише в підлозі кегля TXTMIN, яка в
   рушії за замовчуванням 0, а Math.max(size,0) = size для будь-якого кегля. */
const EQUIV = {
  txt: [`function txt(g,s,x,y,o={}){
  let sz=(o.size||11)*TK;
  const F=k=>(o.bold?'600 ':'')+k+'px system-ui,sans-serif';
  g.fillStyle=o.color||CLR.ink;
  g.font=F(sz);
  if(o.max>0){
    const wd=g.measureText(s).width;
    if(wd>o.max){sz=Math.max(sz*0.55,sz*o.max/wd); g.font=F(sz);}
  }
  g.textAlign=o.align||'left'; g.textBaseline=o.base||'alphabetic';
  g.fillText(s,x,y);
  return sz;
}`],
  pill: [`function pill(g,s,x,y,o={}){
  g.font=(o.bold?'600 ':'')+(o.size||11.5)*TK+'px system-ui,sans-serif';
  const wd=g.measureText(s).width+14*TK;
  g.fillStyle=o.bg||'rgba(252,252,251,.92)';
  g.beginPath(); g.roundRect(x-wd/2,y-13*TK,wd,19*TK,9*TK); g.fill();
  txt(g,s,x,y+1,{...o,align:'center'});
}`],
};
/* Сталі сторінки, які в рушії стали налаштуванням: const TXTMIN=12.5 → setTextFloor(12.5). */
const CONFIG = {TXTMIN: 'setTextFloor'};

function installers(exp){
  const out = [];
  for (const [name, e] of exp){
    if (!/^(install|watch)[A-Z]/.test(name)) continue;
    const src = fs.readFileSync(e.file, 'utf8');
    const ast = parse(src, {ecmaVersion: 'latest', sourceType: 'module'});
    for (const st of ast.body){
      const d = st.declaration;
      if (d && d.type === 'FunctionDeclaration' && d.id.name === name)
        out.push({name, rel: e.rel, body: d.body.body.map(b => norm(src.slice(b.start, b.end)))});
    }
  }
  return out;
}

export function plan(rel){
  const html = fs.readFileSync(path.join(ROOT, rel), 'utf8');
  const re = /<script(?![^>]*\b(?:id|src)=)[^>]*>([\s\S]*?)<\/script>/g;
  let m, last = null;
  while ((m = re.exec(html))) last = m;
  if (!last) throw new Error(rel + ': немає власного скрипту');
  const js = last[1], jsStart = last.index + last[0].indexOf('>') + 1;
  const ast = parse(js, {ecmaVersion: 'latest'});
  const exp = engineExports();
  const take = [], keep = [], cut = [];      // cut: [start,end,replacement]
  for (const st of ast.body){
    const names = st.type === 'FunctionDeclaration' ? [st.id.name]
      : st.type === 'VariableDeclaration' ? st.declarations.map(d => d.id.name) : [];
    /* const a=1, b=2 — у рушії це окремі оголошення; беремо, лише якщо
       кожне ім'я є в рушії з тим самим початковим значенням (const/let не
       розрізняємо: сторінка цих імен не переприсвоює, рушій — лише сам). */
    if (names.length > 1 && names.every(n => exp.has(n))){
      const same = st.declarations.every(d => {
        const e = norm(exp.get(d.id.name).text).replace(/^(const|let|var)/, '');
        return e === norm(js.slice(d.start, d.end));
      });
      if (same){ for (const n of names) take.push({n, rel: exp.get(n).rel}); cut.push([st.start, st.end, '']); }
      else keep.push(...names);
      continue;
    }
    if (names.length !== 1 || !exp.has(names[0])) { if (names.length === 1 && exp.has(names[0])) keep.push(names[0]); continue; }
    const n = names[0], e = exp.get(n), own = norm(js.slice(st.start, st.end));
    if (own === norm(e.text) || (EQUIV[n] || []).some(t => norm(t) === own)){
      take.push({n, rel: e.rel}); cut.push([st.start, st.end, '']);
    } else if (CONFIG[n] && st.type === 'VariableDeclaration' && st.declarations[0].init.type === 'Literal'){
      const fn = CONFIG[n];
      take.push({n: fn, rel: exp.get(fn).rel});
      cut.push([st.start, st.end, `${fn}(${st.declarations[0].init.raw});`]);
    } else keep.push(n);
  }
  /* інсталятори: дослівна послідовність інструкцій верхнього рівня */
  const body = ast.body.map(b => norm(js.slice(b.start, b.end)));
  for (const ins of installers(exp)){
    for (let i = 0; i + ins.body.length <= body.length; i++){
      if (ins.body.every((s, k) => body[i + k] === s)){
        const a = ast.body[i], b = ast.body[i + ins.body.length - 1];
        cut.push([a.start, b.end, ins.name + '();']);
        take.push({n: ins.name, rel: ins.rel});
        break;
      }
    }
  }
  return {html, js, jsStart, take, keep, cut, ast};
}

/* Переписати скрипт: прибрати взяте, вставити імпорти на місце першого
   прибраного оголошення. Коментар над прибраним оголошенням іде разом із ним. */
export function migrate(rel){
  const p = plan(rel);
  let {js} = p;
  const cuts = p.cut.sort((a, b) => a[0] - b[0]);
  /* Імпортуємо лише те, до чого сторінка справді звертається; внутрішній стан
     рушія (NUMLAST, FSP…) збірка підтягне сама як залежність. */
  let rest = '', q = 0;
  for (const [a, b, rep] of cuts){ rest += js.slice(q, a) + rep; q = b; }
  rest = strip(rest + js.slice(q));
  const used = n => new RegExp('(?<![\\w$.])' + n.replace(/\$/g, '\\$') + '(?![\\w$])').test(rest);
  const byMod = new Map();
  for (const t of p.take) if (used(t.n)) (byMod.get(t.rel) || byMod.set(t.rel, []).get(t.rel)).push(t.n);
  const depth = '../'.repeat(rel.split('/').length);   // src/<dir>/<file> → корінь
  const imports = [...byMod].sort().map(([r, ns]) => `import {${ns.join(',')}} from '${depth}${r}';`).join('\n') + '\n';
  let out = '', pos = 0, first = true;
  for (const [a, b, rep] of cuts){
    /* разом із оголошенням забираємо коментар, що стоїть упритул над ним */
    let a2 = a;
    const before = js.slice(pos, a);
    const lm = before.match(/(?:\n|^)((?:[ \t]*(?:\/\*[\s\S]*?\*\/|\/\/[^\n]*)[ \t]*\n)+)[ \t]*$/);
    if (lm && !rep) a2 = a - lm[0].length + (lm[0].startsWith('\n') ? 1 : 0);
    out += js.slice(pos, a2);
    if (first){ out += imports; first = false; }
    out += rep;
    pos = b;
    if (!rep && js[pos] === '\n') pos++;
  }
  out += js.slice(pos);
  const html = p.html.slice(0, p.jsStart) + out + p.html.slice(p.jsStart + js.length);
  return {html, plan: p};
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)){
  const write = process.argv.includes('--write');
  for (const rel of process.argv.slice(2).filter(a => !a.startsWith('--'))){
    const {html, plan: p} = migrate(rel);
    console.log(`== ${rel}`);
    console.log(`   з рушія (${p.take.length}): ${p.take.map(t => t.n).join(', ')}`);
    console.log(`   лишаються локальними, хоч рушій має таке ім'я (${p.keep.length}): ${p.keep.join(', ') || '—'}`);
    if (write){
      const dst = path.join(ROOT, 'src', rel);
      fs.mkdirSync(path.dirname(dst), {recursive: true});
      fs.writeFileSync(dst, html);
      console.log(`   записано ${path.relative(ROOT, dst)}`);
    }
  }
}
