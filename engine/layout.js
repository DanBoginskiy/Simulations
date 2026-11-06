/* engine/layout.js — адаптивна розкладка: дотик, згортання панелей, повний екран.

   Тексти перенесено з basic_physics/09-magnetic-field-forces.html без змін.
   Інструкції верхнього рівня, які в кожному файлі стояли між оголошеннями
   (підписки на resize, кнопки «на весь екран»), зібрано у дві функції —
   installFolding() і installFullscreen(); сторінка кличе їх у тому самому
   місці, де стояли ці інструкції, тож порядок підписок не змінюється. */
import {CV,CHFIT} from './canvas.js';

export function touchRoles(){
  /* Сцена більше не глушить прокрутку: дотик до неї гортає сторінку, як дотик
     до будь-якого іншого місця. Ручки ловлять жест власними мішенями (syncHits).
     Графіки лишають вертикальну прокрутку сторінці, а горизонтальні рухи беруть
     собі — саме ними ведуть перехрестя. */
  for(const c of document.querySelectorAll('canvas[id]')){
    c.style.touchAction=c.closest('.chartbox')?'pan-y':'auto';
  }
}

/* ---- мішені для дотику -------------------------------------------------
   Полотно — один елемент, і різних touch-action для різних його ділянок не
   буває: або весь кадр забирає жест собі, або весь віддає сторінці. Через це
   палець, покладений на порожнє місце сцени, не гортав сторінку. Тепер ручки
   винесено в окремі DOM-мішені поверх полотна: дотик ловлять тільки вони, а
   решта сцени лишається звичайною сторінкою. Миша працює як раніше — її
   обслуговує саме полотно, бо мишею сторінку не гортають. */
export function hitLayer(el){
  let L=el.__hits;
  if(!L||!L.isConnected){
    const par=el.parentNode;
    if(getComputedStyle(par).position==='static') par.style.position='relative';
    L=document.createElement('div'); L.className='hits';
    par.insertBefore(L,el.nextSibling); el.__hits=L;
  }
  return L;
}

/* ---- підказка «поверніть телефон» --------------------------------------- */
export function rotHint(){
  if(document.querySelector('.rothint')) return;
  const d=document.createElement('div'); d.className='rothint';
  d.textContent='поверніть телефон — сцені стане просторіше';
  document.body.appendChild(d);
  setTimeout(()=>d.remove(),4000);
}

/* ---- бічні панелі згортаються на вузькому екрані ------------------------- */
export function foldPanels(){
  const narrow=innerWidth<=760;
  for(const side of document.querySelectorAll('.side')){
    const ps=[...side.querySelectorAll(':scope > .panel')];
    ps.forEach((p,i)=>{
      const h=p.querySelector(':scope > h3'); if(!h) return;
      if(!h.dataset.fold){
        h.dataset.fold='1';
        h.addEventListener('click',()=>{if(innerWidth<=760) p.classList.toggle('fold');});
      }
      if(narrow){if(!p.dataset.init){p.dataset.init='1'; if(i>0) p.classList.add('fold');}}
      else p.classList.remove('fold');
    });
  }
}

export function installFolding(){
  addEventListener('resize',foldPanels);
}

/* Розкриття сцени на весь екран. Розмір полотна задає тільки CSS, тож у
   повноекранному режимі висоту доводиться проставляти явно: полотна ділять
   між собою те, що лишилося від решти вмісту панелі. Кеш CV після цього
   скидається — наступний кадр перемалює сцену вже в новому розмірі. */
export let FSP=null;

export function fsEl(){return document.fullscreenElement||document.webkitFullscreenElement||
  document.querySelector('.panel.fsfake');}

export function fsFit(){
  const el=fsEl();
  if(FSP&&FSP!==el){FSP.querySelectorAll('canvas').forEach(c=>{c.style.height='';}); FSP=null;}
  if(el){
    FSP=el;
    const cans=[...el.querySelectorAll('canvas')];
    if(cans.length){
      cans.forEach(c=>{c.style.height='0px';});
      let rest=0;
      for(const ch of el.children){
        if(ch.classList.contains('fsb')) continue;
        const m=getComputedStyle(ch);
        rest+=ch.getBoundingClientRect().height+
          (parseFloat(m.marginTop)||0)+(parseFloat(m.marginBottom)||0);
      }
      const cs=getComputedStyle(el);
      const rows=new Set(cans.map(c=>Math.round(c.getBoundingClientRect().top))).size||1;
      const avail=el.clientHeight-(parseFloat(cs.paddingTop)||0)-
        (parseFloat(cs.paddingBottom)||0)-rest-14*(rows-1);
      let hh=Math.max(160,avail/rows);
      cans.forEach(c=>{c.style.height=hh+'px';});
      const over=el.scrollHeight-el.clientHeight;
      if(over>1){hh=Math.max(160,hh-over/rows); cans.forEach(c=>{c.style.height=hh+'px';});}
    }
  }
  for(const k in CV) delete CV[k];
  for(const k in CHFIT) delete CHFIT[k];
}


export function installFullscreen(){
  window.addEventListener('resize',fsFit);
  document.addEventListener('fullscreenchange',fsFit);
  document.addEventListener('webkitfullscreenchange',fsFit);
  document.addEventListener('keydown',e=>{
    if(e.key==='Escape'){const p=document.querySelector('.panel.fsfake');
      if(p){p.classList.remove('fsfake'); fsFit();}}
  });
  /* Кнопку дістає панель кожної сцени — ті полотна, що їх малюють модулі
     (графіки лишаються в своїх панелях без кнопки). */
  (function(){
    const RE=/^m[1-9](scene|orb|earth|globe|sky|sph)$/, seen=new Set();
    for(const c of document.querySelectorAll('canvas')){
      if(!RE.test(c.id)) continue;
      const p=c.closest('.panel'); if(!p||seen.has(p)) continue; seen.add(p);
      p.classList.add('fswrap');
      const b=document.createElement('button');
      b.type='button'; b.className='fsb'; b.title='на весь екран'; b.textContent='\u2922';
      b.addEventListener('click',()=>{
        if(fsEl()===p){
          if(document.exitFullscreen) document.exitFullscreen();
          else if(document.webkitExitFullscreen) document.webkitExitFullscreen();
          else {p.classList.remove('fsfake'); fsFit();}
          return;
        }
        const req=p.requestFullscreen||p.webkitRequestFullscreen;
        if(req) Promise.resolve(req.call(p)).catch(()=>{p.classList.add('fsfake'); fsFit();});
        else {p.classList.add('fsfake'); fsFit();}
        /* Де можна — просимо альбомну самі (Android); де не можна (iOS) —
           просто показуємо підказку, яка зникне, щойно телефон повернуть. */
        try{screen.orientation&&screen.orientation.lock&&
          Promise.resolve(screen.orientation.lock('landscape')).catch(()=>{});}catch(e){}
        if(innerWidth<=760&&innerWidth<innerHeight) rotHint();
      });
      p.appendChild(b);
    }
  })();
}
