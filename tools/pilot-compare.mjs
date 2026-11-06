#!/usr/bin/env node
/* Звірка пілотів міграції: оригінал проти dist/ — знімки й числа.

   Той самий сценарій, що й tests/pages/pilots.spec.mjs (час заморожено, кадри
   проганяються вручну), але замість «пройшло/ні» друкує таблицю для
   docs/engine-pilot.md і кладе пари знімків першого модуля в docs/engine-pilot/.

     npm run build && node tools/pilot-compare.mjs [--png]
*/
import fs from 'node:fs';
import path from 'node:path';
import {chromium} from '@playwright/test';
import {ROOT, PILOTS, WIDTHS, capture, pixelDiff} from '../tests/pages/harness.mjs';

const png = process.argv.includes('--png');
const OUT = path.join(ROOT, 'docs/engine-pilot');
if (png) fs.mkdirSync(OUT, {recursive: true});
const browser = await chromium.launch();
const ctx = await browser.newContext({deviceScaleFactor: 1});
const rows = [];
let bad = 0;
for (const rel of PILOTS){
  const p0 = await ctx.newPage();
  await p0.goto('file://' + path.join(ROOT, rel));
  const mods = await p0.evaluate(() => Object.keys(MODULES));
  await p0.close();
  for (const size of WIDTHS){
    let px = 0, total = 0, nums = 0, drawn = 0, same = true;
    for (const mid of mods){
      const [a, b] = [await ctx.newPage(), await ctx.newPage()];
      const o = await capture(a, rel, size, mid), d = await capture(b, 'dist/' + rel, size, mid);
      const diff = await pixelDiff(a, o.png, d.png);
      px += diff.diff; total += diff.total;
      const numsO = (o.snap.text.match(/\d+(?:[.,]\d+)?/g) || []);
      nums += numsO.length + o.snap.state.length; drawn += o.snap.drawn.length;
      same &&= o.snap.text === d.snap.text && JSON.stringify(o.snap.drawn) === JSON.stringify(d.snap.drawn)
        && JSON.stringify(o.snap.state) === JSON.stringify(d.snap.state);
      if (png && mid === mods[0]){
        const slug = path.basename(rel, '.html') + '-' + size[0];
        for (const [tag, r] of [['orig', rel], ['dist', 'dist/' + rel]]){
          const pg = await ctx.newPage();
          const s = await capture(pg, r, size, mid, {fullPage: false});
          fs.writeFileSync(path.join(OUT, `${slug}-${tag}.png`), s.png);
          await pg.close();
        }
      }
      await a.close(); await b.close();
    }
    if (px || !same) bad++;
    rows.push(`| \`${rel}\` | ${size[0]} | ${mods.length} | ${px} з ${total.toLocaleString('uk-UA')} | ${nums} | ${drawn} | ${same ? 'так' : '**ні**'} |`);
  }
}
await browser.close();
console.log('| пілот | ширина, px | модулів | пікселів відмінності | чисел у тексті й стані | рядків на полотні | числа збіглися |');
console.log('|---|---:|---:|---:|---:|---:|:---:|');
console.log(rows.join('\n'));
process.exit(bad ? 1 : 0);
