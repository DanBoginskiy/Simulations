# Пілот рушія: три симуляції на `engine/`

Перші три сторінки, перенесені на рушій. Оригінали лежать на своїх місцях
**без змін** — сторінки, якими користуються, поки ці самі. Перенесені версії
живуть у `src/`, а збірка кладе в `dist/` знову самодостатні HTML.

| пілот | оригінал | `src/` | `dist/` | з рушія взято | лишилося локально, хоч ім'я є в рушії |
|---|---:|---:|---:|---:|---|
| `Mechanics/inertial-frames.html` | 71 КБ, 1468 рядків | 71 КБ, 1445 | 75 КБ | 10 | `cvx`, `slider`, `arrow`, `dot`, `niceStep`, `drawChart`, `hover` |
| `basic_physics/00-kinematics-rotation.html` | 161 КБ, 2744 | 134 КБ, 2251 | 163 КБ | 54 | — |
| `basic_physics/09-magnetic-field-forces.html` | 590 КБ, 3333 | 545 КБ, 2565 | 588 КБ | 71 | — |

Файл про магнітне поле — справді `basic_physics/09-magnetic-field-forces.html`
(перевірено: інших файлів про магнітне поле в `basic_physics/` немає). Великий
розмір — це вбудований KaTeX; його не чіпали (див. «рішення»).

## Як це влаштовано

```
src/<розділ>/<файл>.html  ──  import {fmt} from '../../engine/format.js';
        │                      import {cvx,txt} from '../../engine/canvas.js';
        ▼
tools/build.mjs           ──  замість import вставляє ТЕКСТ потрібних оголошень
        │                      (лише названих і того, від чого вони залежать)
        ▼
dist/<розділ>/<файл>.html ──  один файл, без мережі, без модулів, як і раніше
```

* `engine/*.js` — звичайні ES-модулі без залежностей; тести імпортують їх напряму.
* Скрипт сторінки лишається класичним (не `type="module"`): глобальні імена,
  порядок виконання і гачки перевірок (`activate`, `MODULES`) — як в оригіналі.
* Збірка зупиняється, якщо рушій звертається до імені сторінки (`CLR`,
  `MODULES`…), якщо на верхньому рівні модуля є побічна дія, якщо сторінка
  повторно оголошує імпортоване ім'я, або якщо зібраний скрипт не компілюється.
* `tools/engine-migrate.mjs <файл> [--write]` переносить сторінку
  консервативно: прибирає лише ті оголошення, що **дослівно** (без коментарів і
  пробілів) збігаються з рушієм або з доведено рівносильним варіантом, і лише ті
  блоки інструкцій, що дослівно збігаються з тілом `watchCanvases`/`installFolding`/
  `installFullscreen`. Решту лишає локальною і перелічує. Після нього в пілотах
  зроблено вручну дві речі: `NUMS=[]; CAPS=[];` у циклі кадрів → `resetNums()`
  (ES-модуль не дає переприсвоїти імпорт), і в `inertial-frames` — `txt`/`pill` із
  рушія (рівносильні: локальний `cvx` не змінює `TK`, тож `TK ≡ 1`, а `TXTMIN = 0`).

```bash
npm ci
npm run build                      # src/ → dist/
npm test                           # фізичні тести рушія (vitest)
npx playwright test                # сторінки: завантаження + звірка пілотів
node tools/pilot-compare.mjs --png # таблиця нижче і знімки в docs/engine-pilot/
```

## Як доведено, що нічого не змінилося

**Детермінований час.** Сторінки анімуються циклом `requestAnimationFrame`, у
якому `dt` береться з `performance.now()`. Перед завантаженням сторінки
(`addInitScript`) обидва підмінено: `requestAnimationFrame` лише ставить кадр у
чергу, `performance.now()` повертає штучний годинник, а тест сам проганяє кадри
сталим кроком 1/60 с (30 кадрів після завантаження, `activate(модуль)`, ще 65).
`Math.random` засіяно (mulberry32 — `inertial-frames` малює краплі дощу
випадково), `Date.now` прив'язано до того самого годинника. Оригінал і `dist/`
бачать однакову послідовність усього.

**Що порівнюється** — для кожного пілота, кожної ширини (390, 820, 1280 px) і
**кожного модуля-вкладки** (3 + 5 + 6 = 14 модулів × 3 ширини = 42 пари):

1. знімок усієї сторінки (`fullPage`), попіксельно;
2. увесь видимий текст сторінки (`innerText`) — числа в панелях, формули з
   підставленими значеннями, підписи повзунків;
3. кожен рядок, намальований на полотнах за останні 5 кадрів (перехоплення
   `CanvasRenderingContext2D.fillText`);
4. усі числові поля стану активного модуля (`MODULES[ACT]`, 12 значущих цифр).

Еталоном є сам оригінал, знятий тим самим браузером у той самий момент, тож
порівняння не залежить від шрифтів машини (у CI теж працює).

**Контроль, що звірка не сліпа.** У копії `dist/inertial-frames` текст `txt`
зсунули на 3 px — звірка показала 8296 різних пікселів. Без зсуву — 0.

## Результат

| пілот | ширина, px | модулів | пікселів відмінності | чисел у тексті й стані | рядків на полотні | числа збіглися |
|---|---:|---:|---:|---:|---:|:---:|
| `Mechanics/inertial-frames.html` | 390 | 3 | 0 з 2 278 380 | 56 | 420 | так |
| `Mechanics/inertial-frames.html` | 820 | 3 | 0 з 4 174 620 | 56 | 470 | так |
| `Mechanics/inertial-frames.html` | 1280 | 3 | 0 з 4 062 720 | 56 | 490 | так |
| `basic_physics/00-kinematics-rotation.html` | 390 | 5 | 0 з 4 819 620 | 188 | 1060 | так |
| `basic_physics/00-kinematics-rotation.html` | 820 | 5 | 0 з 9 989 240 | 226 | 1220 | так |
| `basic_physics/00-kinematics-rotation.html` | 1280 | 5 | 0 з 8 468 480 | 229 | 1200 | так |
| `basic_physics/09-magnetic-field-forces.html` | 390 | 6 | 0 з 4 451 070 | 155 | 1050 | так |
| `basic_physics/09-magnetic-field-forces.html` | 820 | 6 | 0 з 9 891 660 | 205 | 1265 | так |
| `basic_physics/09-magnetic-field-forces.html` | 1280 | 6 | 0 з 9 845 760 | 205 | 1265 | так |

**0 пікселів відмінності в усіх 42 парах; текст, рядки на полотні і стан модулів
збіглися дослівно.** Знімки першого модуля у `docs/engine-pilot/`
(`<файл>-<ширина>-orig.png` і `-dist.png`; квантовано до 64 кольорів, щоб не
роздувати репозиторій) — пари побайтно однакові.

| | 390 | 820 | 1280 |
|---|---|---|---|
| inertial-frames | [orig](engine-pilot/inertial-frames-390-orig.png) · [dist](engine-pilot/inertial-frames-390-dist.png) | [orig](engine-pilot/inertial-frames-820-orig.png) · [dist](engine-pilot/inertial-frames-820-dist.png) | [orig](engine-pilot/inertial-frames-1280-orig.png) · [dist](engine-pilot/inertial-frames-1280-dist.png) |
| 00-kinematics-rotation | [orig](engine-pilot/00-kinematics-rotation-390-orig.png) · [dist](engine-pilot/00-kinematics-rotation-390-dist.png) | [orig](engine-pilot/00-kinematics-rotation-820-orig.png) · [dist](engine-pilot/00-kinematics-rotation-820-dist.png) | [orig](engine-pilot/00-kinematics-rotation-1280-orig.png) · [dist](engine-pilot/00-kinematics-rotation-1280-dist.png) |
| 09-magnetic-field-forces | [orig](engine-pilot/09-magnetic-field-forces-390-orig.png) · [dist](engine-pilot/09-magnetic-field-forces-390-dist.png) | [orig](engine-pilot/09-magnetic-field-forces-820-orig.png) · [dist](engine-pilot/09-magnetic-field-forces-820-dist.png) | [orig](engine-pilot/09-magnetic-field-forces-1280-orig.png) · [dist](engine-pilot/09-magnetic-field-forces-1280-dist.png) |

Ті самі 42 звірки — у `tests/pages/pilots.spec.mjs`, тож CI повторює їх на кожному push.

## Рішення для Даіла

Скрізь, де був вибір, узято консервативний варіант; ось що лишилося вирішити.

1. **Канон хелперів «старого» покоління.** У `inertial-frames` лишилися локальними
   сім хелперів, чия поведінка відрізняється від рушія (`docs/engine-inventory.md` §3.2).
   Переведення на рушій змінить картинку: `arrow` перестане малювати
   наконечник нульового вектора (це виправлення, див. знахідку §5.1),
   `slider` писатиме «90°» замість «90 °», `hover` запрацює пальцем, `drawChart`
   ставитиме поділки t через `niceStep`, а не строго через 2 с, а `cvx`
   масштабуватиме кегль на телефоні. Кожне — окреме рішення.
2. **KaTeX.** Лишився вбудованим у сторінку як був (`<script id="katex-js">`,
   +390 КБ у `src/` теж). Варіант: збірка вставляє KaTeX з `tools/katex/`, і
   `src/` худне до ~150 КБ. Не зроблено, бо це зміна формату джерела.
3. **Каркас сторінки** (`MODULES`, `activate`, цикл кадрів) поки в кожній
   сторінці: чотири варіанти циклу, один із них без `try/catch`. Варто вибрати
   один (з `try/catch` і `window.__err`) і винести в рушій.
4. **Імена.** Модулі названо за змістом інвентаризації: `canvas`, `chart`,
   `numbers`, `layout`, `grips`, `ui`, `dom`, `format`, `theme`, `sphere`, `vec`,
   `integrators`. `CLR.paper` у сторінках насправді `--card` брендбука —
   перейменування зачепило б усі 73 файли, тож не зроблено.
5. **g = 9,8 чи 9,81** — одне значення для всієї серії чи свідомо різні за курсами.
6. **Залежність збірки.** `tools/build.mjs` розбирає JS парсером `acorn`
   (devDependency) — без нього не можна надійно вибрати лише потрібні
   оголошення. Сам рушій і зібрані сторінки залежностей не мають.
7. **`dist/` не в git** (вихід збірки, у `.gitignore`); публікація на GitHub Pages
   — окреме рішення, CI лише збирає і тестує.
