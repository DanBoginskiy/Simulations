/* Базова палітра рушія збігається з брендбуком і з палітрою кожної сторінки. */
import {describe, it, expect} from 'vitest';
import fs from 'node:fs';
import {BRAND, ENV} from '../../engine/theme.js';
import {inventory} from '../../tools/engine-inventory.mjs';

const book = fs.readFileSync(new URL('../../BRANDBOOK.md', import.meta.url), 'utf8');
const token = t => (book.match(new RegExp('`' + t + '`\\s*\\|\\s*`(#[0-9a-f]{6})`', 'i')) || [])[1];

describe('theme.js', () => {
  it('токени збігаються з таблицями BRANDBOOK.md §2', () => {
    for (const k of ['k1', 'k2', 'k3', 'ink', 'sec', 'mut', 'grid', 'axis']) expect(BRAND[k]).toBe(token('--' + k));
    /* CLR.paper у JS — це тло полотна, тобто --card брендбука, а не --paper сторінки */
    expect(BRAND.paper).toBe(token('--card'));
    expect(ENV.ground).toBe(token('CLR.ground'));
    expect(ENV.water).toBe(token('CLR.water'));
    expect(ENV.drop).toBe(token('CLR.drop'));
  });
  it('у кожній сторінці CLR містить базові токени з тими самими значеннями', () => {
    const {decls} = inventory();
    const bad = [];
    for (const v of Object.values(decls.CLR)){
      const clr = Function('return (' + v.src.replace(/^const CLR=/, '') + ')')();
      for (const k of Object.keys(BRAND)) if (clr[k] !== BRAND[k]) bad.push(`${v.files.join(',')}: ${k}=${clr[k]}`);
    }
    expect(bad).toEqual([]);
  });
});
