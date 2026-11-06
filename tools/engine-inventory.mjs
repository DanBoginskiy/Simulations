#!/usr/bin/env node
/* Інвентаризація спільного коду симуляцій.

   Кожен HTML серії — самодостатній: «спільні утиліти» (fmt, cvx, drawChart…)
   скопійовано в кожен файл. Скрипт розбирає власний <script> кожного файлу
   парсером acorn, збирає оголошення верхнього рівня, нормалізує їх тексти
   (без коментарів і пробілів) і рахує, скільки файлів мають «ту саму» функцію
   і скільки різних варіантів її тіла існує.

     node tools/engine-inventory.mjs                # таблиця в stdout
     node tools/engine-inventory.mjs --json out.json
     node tools/engine-inventory.mjs --variants fmt # показати варіанти fmt
     node tools/engine-inventory.mjs --md           # таблиці для docs/engine-inventory.md
*/
import fs from 'node:fs';
import path from 'node:path';
import {parse} from 'acorn';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const DIRS = ['Analytic-Geometry','Mechanics','Theoretical-Mechanics','basic_physics','math_analysis','physics_tasks'];

export function htmlFiles(root = ROOT, dirs = DIRS){
  const out = [];
  for (const d of dirs){
    const p = path.join(root, d);
    if (!fs.existsSync(p)) continue;
    for (const f of fs.readdirSync(p).sort()) if (f.endsWith('.html')) out.push(path.join(d, f));
  }
  return out;
}

/* Власний скрипт файлу: усі <script> без id і без src (KaTeX має id). */
export function ownScripts(html){
  const out = [];
  const re = /<script(?<a>[^>]*)>(?<b>[\s\S]*?)<\/script>/g;
  let m;
  while ((m = re.exec(html))) if (!/\bid=|\bsrc=/.test(m.groups.a)) out.push(m.groups.b);
  return out;
}

function norm(src){
  /* Порівнюємо тексти без коментарів і без пробілів: стиль запису не є
     відмінністю, а от будь-яка зміна токена — є. */
  const comments = [];
  try { parse(src, {ecmaVersion: 'latest', onComment: comments, allowReturnOutsideFunction: true}); }
  catch { /* фрагмент може не бути самостійною програмою */ }
  let s = src;
  for (const c of comments.sort((a, b) => b.start - a.start)) s = s.slice(0, c.start) + s.slice(c.end);
  return s.replace(/\s+/g, '');
}

export function topDecls(js){
  const ast = parse(js, {ecmaVersion: 'latest', sourceType: 'script'});
  const out = [];
  for (const n of ast.body){
    if (n.type === 'FunctionDeclaration') out.push({name: n.id.name, kind: 'function', src: js.slice(n.start, n.end)});
    else if (n.type === 'VariableDeclaration'){
      for (const d of n.declarations) if (d.id.type === 'Identifier')
        out.push({name: d.id.name, kind: n.kind, src: n.kind + ' ' + js.slice(d.start, d.end)});
    }
  }
  return out;
}

export function inventory(root = ROOT){
  const files = [];
  const decls = {};          // name -> {variant hash -> [files]}
  for (const rel of htmlFiles(root)){
    const html = fs.readFileSync(path.join(root, rel), 'utf8');
    const title = (html.match(/<title>([\s\S]*?)<\/title>/) || [, ''])[1].trim();
    const info = {
      path: rel, title, bytes: Buffer.byteLength(html),
      katexInline: /id="katex-js"/.test(html) && /katex\.renderToString/.test(html),
      cdn: /<(script|link)[^>]+(src|href)="https?:/.test(html),
      raf: /requestAnimationFrame/.test(html), names: [], parseError: null,
    };
    for (const js of ownScripts(html)){
      let ds;
      try { ds = topDecls(js); } catch (e){ info.parseError = String(e.message); continue; }
      for (const d of ds){
        info.names.push(d.name);
        const h = norm(d.src);
        ((decls[d.name] ??= {})[h] ??= {src: d.src, files: []}).files.push(rel);
      }
    }
    files.push(info);
  }
  return {files, decls};
}

/* Категорії — щоб таблиця читалася за змістом, а не за абеткою. */
export const CATEGORY = [
  ['Інтегратори й чисельні методи', /^(rk4|verlet|integrate|simpson|numDer|ellipK|bisect)$/],
  ['Форматування чисел', /^(fmt|sci|SUP|hms24|hm24|durHM|letterOf|smart)$/],
  ['Тема й кольори, фізичні сталі', /^(CLR|DEG|G|QE|ME|MP|MU0|EPS0|KE|AMU|TOL|MATS)$/],
  ['Полотно й примітиви креслення (вектори)', /^(CV|cvx|TK|TKSCENE|TKCHART|TKMIN|CVW|CVCH|tkOf|dropCV|txt|TXTMIN|pill|arrow|dot|arc|therm|gauge|marks|iso|fitIso|line3|arrow3|poly3|axes3|floor3|arc3|par3|cl3|cap2|labReg|labBox|labHit|labPlace|labWidth|MEAS|hole|sph\w+|dragSphere|dragCam|oxo|helix)$/],
  ['Векторна алгебра', /^(v3\w+|m2\w+|mZero|mMul|mT|det2|det3|rankM|lineThrough|lnorm|lval|ldist|lsigned|lfoot|lmeet|lclip|plane|pval|pdist|pfoot|rref|rankOf|solveGen|cramer|detN|invN|mulNv|mulNN)$/],
  ['Графіки й осі', /^(drawChart|CHFIT|niceStep|makeTip|hover|showTip|axesXY|band|gfit|FIT|fitStep|fitBot|seqGeo|pathXY|planeGeo|planeGrid|spaceGeo|fixedFrame)$/],
  ['Повзунки, ручки, елементи керування', /^(seg|setSeg|slider|clamp|snap|GRIPS|frozen|grip|gpos|shelf|shelfFit|shelfGrips|gaugeGrips|gaugeCol|gcolOf|gcolFit|drawGrip|slideGrip|railGrip|tipGrip|orbitGrip|slideTrack|numIn|matIn|syncMats|mFrame|mCells|MCW|MCH|mcellXY|showM|showMTop|NULLEL)$/],
  ['Адаптивна розкладка й дотик', /^(centerX|fitScale|touchRoles|hitLayer|DRAGCV|mkHit|syncHits|rotHint|foldPanels|FSP|fsEl|fsFit|NUMW|NUMS|txtN|pillN|CAPS|capN|NUMLAST|showNums|LOUD)$/],
  ['Формули (KaTeX)', /^(tex|texTo|texAll)$/],
  ['Каркас сторінки', /^(\$|MODULES|ACT|activate|LAST|loop)$/],
];
export function categoryOf(name){
  for (const [c, re] of CATEGORY) if (re.test(name)) return c;
  return 'Інше (предметні хелпери)';
}
const short = f => f.replace(/^(Analytic-Geometry|Mechanics|Theoretical-Mechanics|basic_physics|math_analysis|physics_tasks)\//, (m, d) =>
  ({'Analytic-Geometry': 'AG', 'Mechanics': 'Mech', 'Theoretical-Mechanics': 'TM', 'basic_physics': 'BP', 'math_analysis': 'MA', 'physics_tasks': 'PT'})[d] + '/')
  .replace(/\.html$/, '').replace(/^(\w+\/)(\d+[ab]?|demo-\d+)-.*$/, '$1$2');
/* Множина файлів стисло: «усі AG (15)», або перелік, якщо їх мало. */
function filesBrief(files, all){
  const byDir = {};
  for (const f of files) (byDir[f.split('/')[0]] ??= []).push(f);
  const out = [];
  for (const [d, fs_] of Object.entries(byDir)){
    const total = all.filter(f => f.startsWith(d + '/')).length;
    const tag = short(fs_[0]).split('/')[0];
    if (fs_.length === total) out.push(`усі ${tag} (${total})`);
    else if (total - fs_.length <= 4 && fs_.length > 4){
      const miss = all.filter(f => f.startsWith(d + '/') && !fs_.includes(f)).map(f => short(f).split('/')[1]);
      out.push(`${tag} (${fs_.length} з ${total}, крім ${miss.join(', ')})`);
    } else out.push(fs_.map(short).join(', '));
  }
  return out.join('; ');
}
export function markdown({files, decls}){
  const all = files.map(f => f.path);
  let md = '| файл | тема (title) | розмір, КБ | KaTeX вбудовано |\n|---|---|---:|:---:|\n';
  for (const f of files) md += `| \`${f.path}\` | ${f.title.replace(/\|/g, '\\|')} | ${(f.bytes / 1024).toFixed(0)} | ${f.katexInline ? 'так' : '—'} |\n`;
  const rows = Object.entries(decls).map(([n, v]) => {
    const vs = Object.values(v).sort((a, b) => b.files.length - a.files.length);
    return {n, vs, tot: vs.reduce((s, x) => s + x.files.length, 0)};
  }).filter(r => r.tot >= 3 && !/^M\d+[A-Z]?$|^PARTS\d$/.test(r.n));
  const byCat = {};
  for (const r of rows) (byCat[categoryOf(r.n)] ??= []).push(r);
  let md2 = '';
  for (const [c] of [...CATEGORY, ['Інше (предметні хелпери)']]){
    const rs = byCat[c]; if (!rs) continue;
    rs.sort((a, b) => b.tot - a.tot || a.n.localeCompare(b.n));
    md2 += `\n### ${c}\n\n| ім'я | файлів | варіантів | де (найпоширеніший варіант першим) |\n|---|---:|---:|---|\n`;
    for (const r of rs){
      const where = r.vs.map((x, i) => (r.vs.length > 1 ? `**в${i + 1}** (${x.files.length}): ` : '') + filesBrief(x.files, all)).join('<br>');
      md2 += `| \`${r.n}\` | ${r.tot} | ${r.vs.length} | ${where} |\n`;
    }
  }
  return {files: md, repeated: md2};
}

if (import.meta.url === 'file://' + process.argv[1]){
  const {files, decls} = inventory();
  const arg = process.argv.slice(2);
  if (arg[0] === '--json'){ fs.writeFileSync(arg[1], JSON.stringify({files, decls}, null, 1)); process.exit(0); }
  if (arg[0] === '--md'){ const m = markdown({files, decls}); console.log(m.files + '\n<!-- repeated -->\n' + m.repeated); process.exit(0); }
  if (arg[0] === '--variants'){
    const v = decls[arg[1]] || {};
    Object.values(v).sort((a, b) => b.files.length - a.files.length).forEach((x, i) => {
      console.log(`--- варіант ${i + 1}: ${x.files.length} файлів\n${x.files.join('\n')}\n${x.src}\n`);
    });
    process.exit(0);
  }
  for (const f of files) console.log(`${f.path}\t${f.bytes}\t${f.katexInline ? 'KaTeX' : '-'}\t${f.cdn ? 'CDN' : ''}\t${f.parseError || ''}`);
  const rows = Object.entries(decls).map(([n, v]) => {
    const vs = Object.values(v); return [n, vs.reduce((s, x) => s + x.files.length, 0), vs.length];
  }).filter(r => r[1] >= 3).sort((a, b) => b[1] - a[1]);
  for (const r of rows) console.log(r.join('\t'));
}
