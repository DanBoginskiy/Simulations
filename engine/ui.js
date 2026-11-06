/* engine/ui.js — елементи керування: перемикачі-сегменти й повзунки.

   Тексти з basic_physics/09-magnetic-field-forces.html (seg, slider) і
   Mechanics/inertial-frames.html (setSeg). Повзунок — варіант 37 файлів:
   градус пишеться впритул до числа («30°»), інші одиниці — через пробіл. */
import {$} from './dom.js';
import {fmt} from './format.js';

export function seg(id,cb){
  const el=$(id);
  el.addEventListener('click',e=>{
    const b=e.target.closest('button'); if(!b) return;
    el.querySelectorAll('button').forEach(x=>x.classList.toggle('active',x===b));
    cb(b.dataset.v);
  });
}

export function setSeg(id,v){
  $(id).querySelectorAll('button').forEach(x=>x.classList.toggle('active',x.dataset.v===v));
}

export function slider(id,unit,dec,cb){
  const i=$(id),o=$(id+'o');
  const show=()=>{o.textContent=fmt(+i.value,dec)+(unit?(unit==='°'?'':' ')+unit:'');};
  i.addEventListener('input',()=>{show(); cb(+i.value);});
  show();
  return {el:i,set(v){i.value=v; show(); cb(+i.value);}};
}

