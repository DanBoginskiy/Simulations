/* engine/numbers.js — числа зі сцени переїжджають під полотно на вузькому кадрі.

   Тексти з basic_physics/09-magnetic-field-forces.html (варіант 22 файлів;
   у physics_tasks/ txtN/pillN свідомо інші — числа там сховано). Скидання
   буферів, яке цикл кадрів робив присвоєнням NUMS=[]; CAPS=[], тепер —
   resetNums(): імпортовану змінну ES-модуль переприсвоїти не дає. */
import {BRAND} from './theme.js';
import {CVW,CVCH,txt,pill} from './canvas.js';

/* ---- числа зі сцени ------------------------------------------------------
   Число на кресленні читається лише тоді, коли кресленню є де дихати. Щойно
   кадр вужчає, воно не зникає, а переїжджає в кутовий блок: сцена лишається
   картинкою, де зміну величини показують самі вектори, а числа лишаються
   числами й більше не накладаються на об'єкти. Поріг — ширина самого полотна,
   тож планшет у портреті поводиться як планшет, а не як збільшений телефон. */
export const NUMW=560;

export let NUMS=[];

export function txtN(g,s,x,y,o={}){
  if(CVCH||CVW>=NUMW) return txt(g,s,x,y,o);
  NUMS.push([o.name||'',s,o.color||BRAND.ink]);
}

export function pillN(g,s,x,y,o={}){
  if(CVCH||CVW>=NUMW) return pill(g,s,x,y,o);
  NUMS.push([o.name||'',s,o.color||BRAND.ink]);
}

/* Заголовок сцени й пояснення під ним на широкому кадрі стоять у лівому
   верхньому куті полотна. На вузькому вони накривають саме креслення — і теж
   переїжджають у DOM, рядком над полотном, де їх ще й можна виділити. */
export let CAPS=[];

export function capN(g,s,x,y,o={}){
  if(CVCH||CVW>=NUMW) return txt(g,s,x,y,o);
  CAPS.push([s,o.color||BRAND.ink,!!o.bold]);
}

/* Числа лягають рядком одразу під кресленням, у тій самій панелі. На полотні
   для них місця немає — сцена на телефоні заповнена вщерть, і будь-яка плашка
   неминуче накрила б об'єкт; окремий рядок не накриває нічого, його можна
   виділити, і він не коштує читання полотна щокадру. */
export let NUMLAST='';

export function showNums(mid){
  const RESC=/^m[1-9](scene|orb|earth|globe|sky|sph)$/;
  let c=null;
  for(const q of document.querySelectorAll('#'+mid+' canvas')) if(RESC.test(q.id)){c=q; break;}
  if(!c) return;
  const host=c.closest('.panel')||c.parentElement;
  let row=host.querySelector(':scope > .numrow');
  const rows=NUMS.slice(0,6);
  const html=rows.map(r=>'<span>'+(r[0]?'<i>'+r[0]+'</i> ':'')+
    '<b style="color:'+r[2]+'">'+r[1]+'</b></span>').join('');
  let cap=host.querySelector(':scope > .caprow');
  const chtml=CAPS.map(c=>'<span'+(c[2]?' class="b"':'')+
    ' style="color:'+c[1]+'">'+c[0]+'</span>').join('');
  if(!CAPS.length){ if(cap) cap.remove(); }
  else{
    if(!cap){cap=document.createElement('div'); cap.className='caprow';
      let an=c; while(an.parentElement&&an.parentElement!==host) an=an.parentElement;
      host.insertBefore(cap,an);}
    if(cap.innerHTML!==chtml) cap.innerHTML=chtml;
  }
  if(!rows.length){ if(row) row.remove(); NUMLAST=''; return; }
  if(!row){row=document.createElement('div'); row.className='numrow'; host.appendChild(row); NUMLAST='';}
  if(html!==NUMLAST){row.innerHTML=html; NUMLAST=html;}
}


export function resetNums(){ NUMS=[]; CAPS=[]; }
