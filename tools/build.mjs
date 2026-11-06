#!/usr/bin/env node
/* Збірка симуляцій: src/ → dist/.

   У src/ сторінка пише на початку власного <script> звичайні ES-імпорти:

     import {fmt,DEG} from '../../engine/format.js';
     import {cvx,txt} from '../../engine/canvas.js';

   Збірка замінює їх текстом потрібних оголошень рушія — лише тих, що названо,
   і тих, від яких вони залежать, — і пише в dist/ той самий HTML, знову
   самодостатній: один файл, без мережі, без модулів, без фреймворків. Скрипт
   сторінки лишається класичним (не type="module"), тож глобальні імена,
   порядок виконання і гачки перевірок (activate, MODULES…) — як в оригіналі.

   Правила для engine/*.js, які збірка перевіряє і за порушення зупиняється:
     • на верхньому рівні лише import, оголошення і export-оголошення —
       жодних побічних дій (їх загорнуто у функції install…/watch…);
     • одне ім'я на оголошення (const a=1, b=2 — ні);
     • рушій не звертається до імен сторінки (CLR, MODULES…): кожне вільне ім'я
       має бути або імпортом, або глобальним об'єктом браузера.
   Для сторінки: оголошення сторінки не можуть повторювати імпортовані імена.

     node tools/build.mjs            # зібрати все з src/ у dist/
     node tools/build.mjs --list     # показати, що з рушія взяла кожна сторінка
*/
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import {fileURLToPath} from 'node:url';
import {parse} from 'acorn';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SRC = path.join(ROOT, 'src');
const DIST = path.join(ROOT, 'dist');
const ENGINE = path.join(ROOT, 'engine');

class BuildError extends Error {}
const fail = msg => { throw new BuildError(msg); };

/* ---- глобальні імена браузера, до яких рушію можна звертатися ---------- */
const BROWSER_GLOBALS = new Set([
  ...Object.getOwnPropertyNames(globalThis),
  'window', 'document', 'navigator', 'location', 'screen', 'getComputedStyle',
  'innerWidth', 'innerHeight', 'devicePixelRatio', 'addEventListener',
  'removeEventListener', 'matchMedia', 'visualViewport', 'ResizeObserver',
  'requestAnimationFrame', 'cancelAnimationFrame', 'HTMLElement',
  'CanvasRenderingContext2D', 'scrollTo', 'scrollY', 'katex', 'undefined',
]);

/* ---- обхід AST без залежностей ------------------------------------------ */
function walk(node, visit, parent = null, key = null){
  if (!node || typeof node.type !== 'string') return;
  visit(node, parent, key);
  for (const k of Object.keys(node)){
    if (k === 'start' || k === 'end') continue;
    const v = node[k];
    if (Array.isArray(v)) for (const x of v) walk(x, visit, node, k);
    else if (v && typeof v.type === 'string') walk(v, visit, node, k);
  }
}
/* Ідентифікатори, що є посиланнями (не ключі об'єктів і не імена властивостей). */
function references(node){
  const refs = new Set(), bound = new Set();
  walk(node, (n, p, key) => {
    if (n.type !== 'Identifier') return;
    if (p && p.type === 'MemberExpression' && key === 'property' && !p.computed) return;
    if (p && (p.type === 'Property' || p.type === 'MethodDefinition' || p.type === 'PropertyDefinition')
        && key === 'key' && !p.computed){
      if (p.type === 'Property' && p.shorthand) refs.add(n.name);
      return;
    }
    if (p && (p.type === 'LabeledStatement' || p.type === 'BreakStatement' || p.type === 'ContinueStatement')) return;
    refs.add(n.name);
  });
  /* Грубо, але надійно: будь-яке ім'я, оголошене всередині (параметр,
     локальна змінна, функція, catch), вважаємо зв'язаним. */
  walk(node, n => {
    const pat = q => walk(q, m => { if (m.type === 'Identifier') bound.add(m.name); });
    if (n.type === 'VariableDeclarator') pat(n.id);
    if (/Function/.test(n.type)){ if (n.id) bound.add(n.id.name); n.params.forEach(pat); }
    if (n.type === 'CatchClause' && n.param) pat(n.param);
    if (n.type === 'ClassDeclaration' && n.id) bound.add(n.id.name);
  });
  return {refs, bound};
}

/* ---- розбір модулів рушія ------------------------------------------------ */
const MODS = new Map();
export function loadModule(file){
  file = path.resolve(file);
  if (MODS.has(file)) return MODS.get(file);
  if (!file.startsWith(ENGINE + path.sep)) fail(`імпорт поза engine/: ${file}`);
  if (!fs.existsSync(file)) fail(`немає модуля ${path.relative(ROOT, file)}`);
  const src = fs.readFileSync(file, 'utf8');
  const rel = path.relative(ROOT, file);
  let ast;
  const comments = [];
  try { ast = parse(src, {ecmaVersion: 'latest', sourceType: 'module', onComment: comments}); }
  catch (e){ fail(`${rel}: ${e.message}`); }
  const mod = {file, rel, src, decls: new Map(), order: [], imports: new Map(), exports: new Set()};
  MODS.set(file, mod);
  let prevEnd = 0;
  for (const st of ast.body){
    const lead = leading(src, comments, prevEnd, st.start);
    prevEnd = st.end;
    if (st.type === 'ImportDeclaration'){
      const from = path.resolve(path.dirname(file), st.source.value);
      for (const s of st.specifiers){
        if (s.type !== 'ImportSpecifier' || s.imported.name !== s.local.name)
          fail(`${rel}: підтримано лише import {a,b} from '…' без перейменувань`);
        mod.imports.set(s.local.name, from);
      }
      continue;
    }
    let decl = st, exported = false;
    if (st.type === 'ExportNamedDeclaration'){
      if (!st.declaration) fail(`${rel}: export {…} без оголошення не підтримано`);
      decl = st.declaration; exported = true;
    }
    let name;
    if (decl.type === 'FunctionDeclaration') name = decl.id.name;
    else if (decl.type === 'VariableDeclaration'){
      if (decl.declarations.length !== 1) fail(`${rel}: одне ім'я на оголошення (рядок ${line(src, decl.start)})`);
      const id = decl.declarations[0].id;
      if (id.type !== 'Identifier') fail(`${rel}: деструктуризація на верхньому рівні не підтримана`);
      name = id.name;
    } else fail(`${rel}: на верхньому рівні дозволено лише оголошення — рядок ${line(src, st.start)}`);
    const body = src.slice(decl.start, decl.end);
    const {refs, bound} = references(decl);
    mod.decls.set(name, {name, mod, text: lead + body, refs, bound, exported});
    mod.order.push(name);
    if (exported) mod.exports.add(name);
  }
  for (const to of new Set(mod.imports.values())) loadModule(to);
  for (const [name, to] of mod.imports)
    if (!MODS.get(to).exports.has(name)) fail(`${rel}: ${path.relative(ROOT, to)} не експортує ${name}`);
  /* вільні імена: лише власні оголошення, імпорти і глобальні об'єкти браузера */
  for (const d of mod.decls.values()) for (const r of d.refs){
    if (r === d.name || d.bound.has(r) || mod.decls.has(r) || mod.imports.has(r) || BROWSER_GLOBALS.has(r)) continue;
    fail(`${rel}: ${d.name} звертається до ${r}, якого немає ні в модулі, ні в імпортах`);
  }
  return mod;
}
function line(src, i){ return src.slice(0, i).split('\n').length; }
/* Коментарі, що стоять упритул над оголошенням (без порожнього рядка між
   ними), їдуть разом із ним; заголовок модуля, відділений порожнім рядком, — ні. */
function leading(src, comments, from, to){
  let start = to;
  for (const c of comments.filter(c => c.start >= from && c.end <= to).sort((a, b) => b.start - a.start)){
    if (/\n[ \t]*\n/.test(src.slice(c.end, start))) break;
    start = c.start;
  }
  return start < to ? src.slice(start, to).trimEnd() + '\n' : '';
}

/* Замикання: імена, які просить сторінка, плюс усе, від чого вони залежать. */
function closure(requests){
  const need = new Map();         // file -> Set(name)
  const stack = [...requests];
  while (stack.length){
    const [file, name] = stack.pop();
    const mod = loadModule(file);
    const d = mod.decls.get(name);
    if (!d) fail(`${mod.rel} не має ${name}`);
    const set = need.get(mod.file) || new Set();
    if (set.has(name)) continue;
    set.add(name); need.set(mod.file, set);
    for (const r of d.refs){
      if (r === name || d.bound.has(r)) continue;
      if (mod.decls.has(r)) stack.push([mod.file, r]);
      else if (mod.imports.has(r)) stack.push([mod.imports.get(r), r]);
    }
  }
  return need;
}
/* Порядок модулів: залежності раніше за залежних (за графом імпортів). */
function moduleOrder(files){
  const out = [], seen = new Set(), busy = new Set();
  const visit = f => {
    if (seen.has(f)) return;
    if (busy.has(f)) fail(`цикл імпортів через ${path.relative(ROOT, f)}`);
    busy.add(f);
    for (const to of [...new Set(MODS.get(f).imports.values())].sort()) visit(to);
    busy.delete(f); seen.add(f); out.push(f);
  };
  for (const f of [...files].sort()) visit(f);
  return out.filter(f => files.has(f));
}

/* ---- сторінка ------------------------------------------------------------ */
const IMPORT_RE = /^[ \t]*import\s*\{([^}]*)\}\s*from\s*['"]([^'"]+)['"]\s*;?[ \t]*\r?\n/gm;

export function buildPage(srcFile){
  const html = fs.readFileSync(srcFile, 'utf8');
  const relSrc = path.relative(ROOT, srcFile);
  const report = [];
  const out = html.replace(/(<script(?![^>]*\bsrc=)[^>]*>)([\s\S]*?)(<\/script>)/g, (all, open, js, close) => {
    IMPORT_RE.lastIndex = 0;
    if (!IMPORT_RE.test(js)) return all;
    IMPORT_RE.lastIndex = 0;
    const requests = [];
    let first = -1, m;
    while ((m = IMPORT_RE.exec(js))){
      if (first < 0) first = m.index;
      const file = path.resolve(path.dirname(srcFile), m[2]);
      for (const n of m[1].split(',').map(s => s.trim()).filter(Boolean)){
        if (/\s/.test(n)) fail(`${relSrc}: перейменування в імпорті (${n}) не підтримано`);
        requests.push([file, n]);
      }
    }
    for (const [file, n] of requests){
      const mod = loadModule(file);
      if (!mod.exports.has(n)) fail(`${relSrc}: ${mod.rel} не експортує ${n}`);
    }
    const need = closure(requests);
    let block = '/* ==== рушій: вбудовано tools/build.mjs з engine/ — не редагувати тут ==== */\n';
    for (const f of moduleOrder(new Set(need.keys()))){
      const mod = MODS.get(f), names = need.get(f);
      const picked = mod.order.filter(n => names.has(n));
      report.push(`${mod.rel}: ${picked.join(', ')}`);
      block += `/* ---- ${mod.rel} ---- */\n`;
      for (const n of picked) block += mod.decls.get(n).text.replace(/^export\s+/m, '') + '\n';
    }
    block += '/* ==== кінець рушія ==== */\n';
    const rest = js.replace(IMPORT_RE, '');
    const pos = first;   // імпорти стоять поспіль: позиція першого — місце вставки
    const merged = rest.slice(0, pos) + block + rest.slice(pos);
    checkScript(merged, relSrc);
    return open + merged + close;
  });
  return {html: out, report};
}

function checkScript(js, rel){
  /* Синтаксис і повторні let/const — справа V8; повторні function — ні
     (пізніша тихо перекриває ранішу), тож імена верхнього рівня звіряємо самі. */
  try { new vm.Script(js, {filename: rel}); }
  catch (e){ fail(`${rel}: зібраний скрипт не компілюється — ${e.message}`); }
  const ast = parse(js, {ecmaVersion: 'latest', sourceType: 'script'});
  const seen = new Set();
  for (const st of ast.body){
    const names = st.type === 'FunctionDeclaration' ? [st.id.name]
      : st.type === 'VariableDeclaration' ? st.declarations.flatMap(d => d.id.type === 'Identifier' ? [d.id.name] : []) : [];
    for (const n of names){
      if (seen.has(n)) fail(`${rel}: ім'я ${n} оголошено двічі (рушій і сторінка?)`);
      seen.add(n);
    }
  }
}

export function srcPages(dir = SRC){
  const out = [];
  if (!fs.existsSync(dir)) return out;
  for (const e of fs.readdirSync(dir, {withFileTypes: true}).sort((a, b) => a.name.localeCompare(b.name))){
    const p = path.join(dir, e.name);
    if (e.isDirectory()) out.push(...srcPages(p));
    else if (e.name.endsWith('.html')) out.push(p);
  }
  return out;
}

/* Перевірити всі модулі рушія, навіть ті, яких поки не імпортує жодна сторінка. */
export function checkEngine(){
  const files = fs.readdirSync(ENGINE).filter(f => f.endsWith('.js')).sort();
  for (const f of files) loadModule(path.join(ENGINE, f));
  return files.length;
}

/* Усі експорти рушія: ім'я → {rel, text} — для інструмента міграції. */
export function engineExports(){
  checkEngine();
  const out = new Map();
  for (const mod of MODS.values()) for (const n of mod.exports){
    if (out.has(n)) fail(`ім'я ${n} експортують два модулі: ${out.get(n).rel} і ${mod.rel}`);
    out.set(n, {rel: mod.rel, file: mod.file, text: mod.decls.get(n).text});
  }
  return out;
}

export function buildAll({list = false} = {}){
  checkEngine();
  const pages = srcPages();
  for (const f of pages){
    const {html, report} = buildPage(f);
    const dst = path.join(DIST, path.relative(SRC, f));
    fs.mkdirSync(path.dirname(dst), {recursive: true});
    fs.writeFileSync(dst, html);
    console.log(`${path.relative(ROOT, dst)}  ${(Buffer.byteLength(html) / 1024).toFixed(0)} КБ`);
    if (list) for (const r of report) console.log('    ' + r);
  }
  return pages.length;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)){
  try {
    const n = buildAll({list: process.argv.includes('--list')});
    console.log(`зібрано сторінок: ${n}`);
  } catch (e){
    if (e instanceof BuildError){ console.error('збірка зупинена: ' + e.message); process.exit(1); }
    throw e;
  }
}
