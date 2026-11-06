/* Пілоти міграції: dist/ (зібрано з src/ і engine/) проти оригіналу.
   Знімок оригіналу і є еталоном — так тест не залежить від шрифтів машини,
   на якій біжить: обидві версії малює той самий браузер у ту саму хвилину.
   Допуски — tests/TOLERANCES.md §5: 0 пікселів, точний збіг чисел. */
import {test, expect} from '@playwright/test';
import {PILOTS, WIDTHS, capture, modulesOf, pixelDiff} from './harness.mjs';

const MODS = {
  'Mechanics/inertial-frames.html': ['m1', 'm2', 'm3'],
  'basic_physics/00-kinematics-rotation.html': ['m1', 'm2', 'm3', 'm4', 'm5'],
  'basic_physics/09-magnetic-field-forces.html': ['m1', 'm2', 'm3', 'm4', 'm5', 'm6'],
};

test('перелік модулів пілотів актуальний', async ({page}) => {
  for (const rel of PILOTS) expect(await modulesOf(page, rel)).toEqual(MODS[rel]);
});

for (const rel of PILOTS) for (const size of WIDTHS) for (const mid of MODS[rel]){
  test(`${rel} · ${size[0]} px · ${mid}`, async ({browser}) => {
    const ctx = await browser.newContext({deviceScaleFactor: 1});
    const [a, b] = [await ctx.newPage(), await ctx.newPage()];
    const orig = await capture(a, rel, size, mid);
    const dist = await capture(b, 'dist/' + rel, size, mid);
    expect(dist.snap.module).toBe(mid);
    expect(dist.snap.state).toEqual(orig.snap.state);
    expect(dist.snap.text).toBe(orig.snap.text);
    expect(dist.snap.drawn).toEqual(orig.snap.drawn);
    const d = await pixelDiff(a, orig.png, dist.png);
    expect(d.diff).toBe(0);
    await ctx.close();
  });
}
