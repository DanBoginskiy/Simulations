/* Кожна сторінка — і оригінал, і зібрана з src/ — відкривається без помилок
   на кожній своїй вкладці:
   0 pageerror і 0 console.error (tests/TOLERANCES.md §5). */
import {test, expect} from '@playwright/test';
import {originals, built, fileUrl} from './harness.mjs';

const pages = [...originals(), ...built()];
test('є що перевіряти', () => { expect(originals().length).toBeGreaterThan(0); });

for (const rel of pages){
  test(`завантаження: ${rel}`, async ({page}) => {
    const errors = [];
    page.on('pageerror', e => errors.push('pageerror: ' + e.message));
    page.on('console', m => { if (m.type() === 'error') errors.push('console.error: ' + m.text()); });
    await page.goto(fileUrl(rel), {waitUntil: 'load'});
    await page.waitForTimeout(700);      // кілька живих кадрів циклу анімації
    /* кожна вкладка-модуль: activate() і MODULES — глобальні імена сторінки */
    const mods = await page.evaluate(() => typeof MODULES === 'undefined' ? [] : Object.keys(MODULES));
    for (const m of mods){
      await page.evaluate(id => activate(id), m);
      await page.waitForTimeout(250);
    }
    /* цикл кадрів ловить винятки і складає їх у window.__err — теж помилка */
    const trapped = await page.evaluate(() => window.__err || []);
    expect([...errors, ...trapped.map(e => 'loop: ' + e)]).toEqual([]);
  });
}
