/* engine/dom.js — найменший спільний знаменник: пошук елемента за id.

   Дві копії в серії: 51 файл має $ без запасного елемента (тут), 22 файли
   (physics_tasks/, частина basic_physics/) повертають NULLEL замість null.
   Друга поведінка лишається в тих файлах локальною. */
export const $=id=>document.getElementById(id);
