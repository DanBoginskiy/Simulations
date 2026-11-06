/* engine/grips.js — пряме керування на сцені: ручки, полиці, шкали, мішені дотику.

   Тексти з basic_physics/09-magnetic-field-forces.html (варіанти 40–69 файлів).
   gaugeGrips і gaugeCol мають у серії по 4–5 варіантів, тож лишаються
   локальними у сторінках. */
import {BRAND} from './theme.js';
import {$} from './dom.js';
import {fmt} from './format.js';
import {TK,CVW,txt,pill,dot} from './canvas.js';
import {NUMW} from './numbers.js';
import {hitLayer} from './layout.js';

/* ---------- пряме керування на сцені ---------- */
export const clamp=(v,lo,hi)=>v<lo?lo:(v>hi?hi:v);

export const snap=(v,st)=>Math.round(v/st)*st;

/* Реєстр ручок — гачок для оснастки: харнес бере звідси список і синтетично
   тягне кожну ручку в крайні положення кадру. Без реєстру перевірка осліпла б
   тієї ж миті, коли керування переїхало з повзунків на полотно. */
export const GRIPS=[];

/* ---- жест належить тому, хто вміє його прийняти -------------------------
   Полотно з ручками мусить забирати дотик собі, інакше палець замість ручки
   тягне сторінку. Полотно без ручок — навпаки: воно не має заважати
   прокручувати. Графіки лишають вертикальну прокрутку сторінці, а горизонтальні
   рухи беруть собі — саме ними ведуть перехрестя. */
export const DRAGCV=new Set();

export function mkHit(el,G){
  const b=document.createElement('b'); b.className='hit';
  const at=e=>{const r=el.getBoundingClientRect(); return [e.clientX-r.left,e.clientY-r.top];};
  b.addEventListener('pointerdown',e=>{
    const h=b.__h; if(!h) return;
    /* На пристрої, де є і сенсор, і миша, мішень дістається й миші. Тоді
       беремо ручку лише якщо курсор справді на ній, а не будь-де в межах
       сорока чотирьох пікселів: поруч можуть бути кнопки, намальовані на
       самому полотні, і їхній натиск мішень не має права забирати. */
    if(e.pointerType==='mouse'){
      const p0=at(e);
      if(Math.hypot(p0[0]-h.x,p0[1]-h.y)>(h.r||10)+6) return;
    }
    G.st._grab=h.id; G.st._over=h.id; G.st._froz=null;
    if(b.setPointerCapture) b.setPointerCapture(e.pointerId);
    /* кадр заморожуємо ДО першої зміни величини — той самий порядок, що й на полотні */
    G.listFn();
    const p=at(e); h.move(p[0],p[1]);
    if(e.preventDefault) e.preventDefault();
  });
  b.addEventListener('pointermove',e=>{
    if(G.st._grab==null) return;
    const p=at(e);
    for(const h of G.listFn()) if(h.id===G.st._grab){h.move(p[0],p[1]); break;}
    if(e.preventDefault) e.preventDefault();
  });
  const off=()=>{G.st._grab=null; G.st._froz=null;};
  b.addEventListener('pointerup',off);
  b.addEventListener('pointercancel',off);
  return b;
}

export function syncHits(){
  for(const G of GRIPS){
    const el=$(G.id);
    if(!el||!el.isConnected||!el.getClientRects().length) continue;
    /* поки ручку тягнуть, шар не чіпаємо: захоплення вказівника тримає жест
       на тій мішені, яка його почала, і перебудова її просто знищила б */
    if(G.st._grab!=null) continue;
    const sec=el.closest('.module');
    const L=hitLayer(el);
    if(sec&&!sec.classList.contains('active')){
      if(L.childElementCount) L.textContent='';
      continue;
    }
    L.style.left=el.offsetLeft+'px'; L.style.top=el.offsetTop+'px';
    L.style.width=el.offsetWidth+'px'; L.style.height=el.offsetHeight+'px';
    const list=G.listFn();
    while(L.childElementCount>list.length) L.removeChild(L.lastChild);
    while(L.childElementCount<list.length) L.appendChild(mkHit(el,G));
    for(let i=0;i<list.length;i++){
      const h=list[i], b=L.children[i];
      b.__h=h;
      if(h.hbox){
        /* ручка з власною зоною захоплення — доріжка повзунка, відрізок,
           смуга: мішень повторює саме її, інакше пальцем можна взяти лише
           кружок, а мишею — усю доріжку, і дві поведінки розходяться */
        b.style.left=h.hbox.x+'px'; b.style.top=h.hbox.y+'px';
        b.style.width=h.hbox.w+'px'; b.style.height=h.hbox.h+'px';
        b.style.borderRadius=Math.min(h.hbox.h,h.hbox.w)/2+'px';
      } else {
        const S=Math.max(44,2*(h.r+8));
        b.style.left=(h.x-S/2)+'px'; b.style.top=(h.y-S/2)+'px';
        b.style.width=S+'px'; b.style.height=S+'px';
        b.style.borderRadius='50%';
      }
    }
  }
}

/* Масштаб сцени рахується з фактичного розмаху (§10). Але щойно ми тягнемо
   величину, від якої той розмах залежить, виникає контур: палець рухає
   величину → росте розмах → падає sc → ручка тікає з-під пальця. Тому на час
   жесту кадр заморожується: geo() віддає знімок, зроблений на pointerdown,
   і світ не перемасштабовується посеред руху. Після відпускання масштаб
   перепідбирається один раз. Правило §10 не порушене — воно просто не
   застосовується 60 разів за секунду посеред жесту. */
export function frozen(st,b,calc){
  const f=st._froz;
  if(f&&f.w===b.w&&f.h===b.h) return f.G;
  const G=calc(b);
  if(st._grab!=null) st._froz={w:b.w,h:b.h,G};
  return G;
}

/* Сталий масштаб (§10). Кадр підбирається під ВЕРХНЮ МЕЖУ діапазону величин, а не під
   їхні поточні значення. Інакше знаменник масштабу — та сама величина, яку тягнуть, добуток
   `величина × sc` майже сталий, і малюнок не змінюється: студент крутить ручку, а на екрані
   нічого не відбувається. Запобіжник: якщо вміст усе-таки виліз за розрахункову межу
   (похідна величина, крайова комбінація), масштаб один раз зменшується під нього. */
export function fitScale(w,h,padW,padH,maxX,maxY,nowX,nowY){
  const X=Math.max(maxX,nowX||0), Y=Math.max(maxY,nowY||0);
  /* Відступ, розрахований на широкий кадр, на вузькому з'їдав усю ширину:
     різниця ставала від'ємною, і сцена вивертався навиворіт. Стеля в 0,62
     кадру не дає відступові перерости саме креслення. */
  w=Math.max(1,w); h=Math.max(1,h);
  const pw=Math.min(padW*TK,w*0.62), ph=Math.min(padH*TK,h*0.62);
  /* Масштаб нулем чи мінусом бути не має права: він іде в радіус дуги, а
     від'ємний радіус — виняток, який убиває весь цикл кадрів. */
  return Math.max(1e-6,Math.min((w-pw)/Math.max(1e-6,X),(h-ph)/Math.max(1e-6,Y)));
}

/* Ручка: {id, x, y, r, color, hint, move(px,py)} — x, y, r у екранних пікселях
   (радіус 13 px — це палець, а не метри), а move() сам переводить піксель назад
   у фізику через geo(), захоплену в замиканні. Хелпер не знає жодної фізики.
   listFn() мусить бути чистою: її кличе і scene() (щоб намалювати ручки),
   і цей хелпер (щоб влучити) — одна геометрія, один код, жодного дублювання. */
export function grip(id,st,listFn){
  const c=$(id);
  GRIPS.push({id,st,listFn}); DRAGCV.add(id);
  const pos=e=>{const r=c.getBoundingClientRect(); return [e.clientX-r.left,e.clientY-r.top];};
  const pick=(px,py)=>{
    let best=null,bd=1e9;
    for(const h of listFn()){
      const d=Math.hypot(px-h.x,py-h.y);
      /* На вузькому кадрі ручка мала, а палець — ні: зона захоплення росте. */
      if(d<=h.r+6+(CVW<NUMW?10:0)&&d<bd){bd=d; best=h;}
    }
    /* у ручку діаметром 16 px влучити важко. Якщо схибили — приймаємо дотик
       у межах доріжки шкали: ручка стрибає під палець. Ручки на самій сцені
       зони hit не мають, тож їх це не зачіпає. */
    if(!best) for(const h of listFn()) if(h.hit&&h.hit(px,py)){best=h; break;}
    return best;
  };
  c.addEventListener('pointerdown',e=>{
    /* дотик і стилус ідуть через мішені (.hit), полотно лишає їх сторінці */
    if(e.pointerType!=='mouse') return;
    const p=pos(e), h=pick(p[0],p[1]);
    if(!h) return;
    st._grab=h.id; st._over=h.id; st._froz=null;
    if(c.setPointerCapture) c.setPointerCapture(e.pointerId);
    /* Знімок кадру треба зробити ДО першої зміни величини. listFn() кличе
       geo(), а той, побачивши _grab, кладе кадр у _froz. Без цього рядка
       заморожувався б кадр, порахований уже за новим значенням, — і сцени,
       де жест скидає час розгортки, стрибали б на першому ж дотику. */
    listFn();
    h.move(p[0],p[1]);
    if(e.preventDefault) e.preventDefault();
  });
  c.addEventListener('pointermove',e=>{
    if(e.pointerType!=='mouse') return;
    const p=pos(e);
    if(st._grab!=null){
      for(const h of listFn()) if(h.id===st._grab){h.move(p[0],p[1]); break;}
      c.style.cursor='grabbing';
    } else {
      const h=pick(p[0],p[1]);
      st._over=h?h.id:null;
      c.style.cursor=h?'grab':'';
    }
  });
  const off=()=>{st._grab=null; st._froz=null; c.style.cursor=st._over?'grab':'';};
  c.addEventListener('pointerup',off);
  c.addEventListener('pointercancel',off);
  c.addEventListener('pointerleave',()=>{st._over=null; if(st._grab==null) c.style.cursor='';});
  /* Клавіатура. 298 повзунків були доступні з клавіатури, полотно саме по собі —
     ні; без цього переїзд на сцену був би системною регресією доступності (§14).
     Tab всередині полотна перебирає ручки, стрілки зсувають на 4 px, Shift — на 16. */
  c.tabIndex=0;
  c.addEventListener('keydown',e=>{
    const L=listFn(); if(!L.length) return;
    const k=e.key;
    if(k==='Tab'){
      const i=L.findIndex(h=>h.id===st._over);
      st._over=L[(i+(e.shiftKey?-1:1)+L.length+1)%L.length].id;
      if(e.preventDefault) e.preventDefault();
      return;
    }
    const d={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]}[k];
    if(!d) return;
    const h=L.filter(x=>x.id===st._over)[0]||L[0];
    st._over=h.id;
    const s=e.shiftKey?16:4;
    h.move(h.x+d[0]*s,h.y+d[1]*s);
    if(e.preventDefault) e.preventDefault();
  });
  c.addEventListener('blur',()=>{if(st._grab==null) st._over=null;});
}

/* Полиця зразків. Властивість речовини — коефіцієнт тертя, проникність,
   питомий опір — не має розміру, який можна потягнути: її обирають клацанням
   по підписаному зразку. M = {x0, y, dx}; list = [[назва, значення, підпис?], …].
   Полиця живе на сцені поруч із тілом, а не в бічній колонці — щоб вибір
   речовини лишався частиною креслення. */
/* Полиця з карток на вузькому кадрі не вміщалася й вилазила за край: крок
   стискається рівно настільки, щоб уся полиця лишилася в кадрі, а підписи
   всередині карток доганяє o.max. Ручки беруть ту саму геометрію. */
export function shelfFit(M,n){
  const room=CVW-M.x0-6, need=n*M.dx;
  return (need>room&&room>40)?{...M,dx:room/n}:M;
}

export function shelf(g,M,list,cur,lab){
  M=shelfFit(M,list.length);
  if(lab) txt(g,lab,M.x0-8,M.y+4,{color:BRAND.mut,size:10,align:'right',max:M.x0-10});
  list.forEach((m,i)=>{
    const x=M.x0+i*M.dx, on=Math.abs(cur-m[1])<1e-9;
    g.fillStyle=on?'rgba(27,175,122,.16)':'#fff';
    g.strokeStyle=on?BRAND.k3:BRAND.axis; g.lineWidth=on?2:1;
    g.beginPath(); g.roundRect(x+3,M.y-13,M.dx-6,26,6); g.fill(); g.stroke();
    txt(g,m[0],x+M.dx/2,M.y-1,{color:on?BRAND.ink:BRAND.sec,size:10.5,bold:on,align:'center',max:M.dx-9});
    txt(g,m[2]==null?fmt(m[1],2):m[2],x+M.dx/2,M.y+11,{color:BRAND.mut,size:9.5,align:'center',max:M.dx-9});
  });
}

/* Шкала величини просто в кадрі. Це не повзунок із бічної колонки: смужка
   стоїть на сцені поруч із тим, на що впливає, тягнеться пальцем за верхівку
   й перебирається з клавіатури нарівні з рештою ручок. Її беруть тоді, коли
   величина не має власного розміру в кресленні (частота, коефіцієнт опору,
   кількість витків) — саме той випадок, для якого §19 іще припускав повзунок. */
export function gauge(g,x,yb,H,frac,col,lab){
  g.strokeStyle=BRAND.axis; g.lineWidth=1;
  g.beginPath(); g.roundRect(x-8,yb-H,16,H,4); g.stroke();
  const f=Math.max(0,Math.min(1,frac));
  g.fillStyle=col; g.globalAlpha=0.32; g.fillRect(x-5,yb-f*H,10,f*H); g.globalAlpha=1;
  if(lab) txt(g,lab,x,yb+14,{color:BRAND.sec,size:9.5,bold:true,align:'center'});
  return yb-f*H;
}

/* Колонка шкал так само стискається під ширину кадру — інакше на телефоні
   останні шкали опинялися за краєм і стати на них пальцем було нічим. */
export function gcolFit(C,n){
  const room=CVW-C.x0-10, need=n*C.dx;
  return (need>room&&room>40)?{...C,dx:room/n}:C;
}

/* Термометр — фізичний прилад, а не повзунок: стовпчик росте від колби вгору,
   і саме за його верхівку задають температуру. Повертає екранну висоту
   верхівки, щоб туди сіла ручка. frac ∈ [0,1]. */
export function therm(g,x,yb,H,frac,col,lab){
  g.strokeStyle=BRAND.axis; g.lineWidth=1.8;
  g.beginPath(); g.roundRect(x-7,yb-H-6,14,H+6,7); g.stroke();
  const fh=Math.max(0,Math.min(1,frac))*H;
  g.fillStyle=col; g.globalAlpha=0.5;
  g.beginPath(); g.roundRect(x-4,yb-fh,8,fh,4); g.fill(); g.globalAlpha=1;
  dot(g,x,yb+6,9,col);
  if(lab) txt(g,lab,x,yb+30,{color:BRAND.sec,size:10.5,bold:true,align:'center'});
  return yb-fh;
}

/* pre — префікс id: у сцені може бути дві полиці (речовина тіла й речовина
   опори), і без префікса їхні ручки мали б однакові імена */
export function shelfGrips(M,list,set,pre){
  M=shelfFit(M,list.length);
  return list.map((m,i)=>({id:(pre||'sh')+i, x:M.x0+i*M.dx+M.dx/2, y:M.y, r:M.dx/2-2,
    /* mode: ручка перемикає режим, а не змінює величину — масштабу дозволено від неї
       залежати, і перевірка сталого масштабу такі ручки пропускає (§10) */
    bare:true, mode:true, color:BRAND.k3, hint:m[0], move:()=>set(m[1])}));
}

/* Сталий словник ручки: спокій / наведення / захоплення. Підпис з'являється
   лише при наведенні — у спокої креслення лишається чистим (брендбук §1). */
export function drawGrip(g,h,st){
  const on=st._over===h.id, gr=st._grab===h.id;
  /* bare — ручкою є сам об'єкт сцени (заряд, тіло): свого кружка вона не малює,
     інакше накрила б те, за що тягнуть */
  const hr=Math.max(4,h.r);
  if(!h.bare) dot(g,h.x,h.y,hr,h.color,'#fff');
  if(on||gr){
    g.strokeStyle=gr?BRAND.ink:BRAND.sec; g.lineWidth=gr?2:1.2;
    g.beginPath(); g.arc(h.x,h.y,hr+4,0,7); g.stroke();
    if(h.hint) pill(g,h.hint,h.x,h.y-h.r-12,{color:BRAND.ink,size:11,bold:true});
  }
}

