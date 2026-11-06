/* engine/canvas.js — полотно, що підганяється під пристрій, і примітиви креслення.

   Тексти функцій перенесено з basic_physics/09-magnetic-field-forces.html без
   змін (крім CLR → BRAND: рушій не бачить палітри сторінки, а базові токени
   однакові в усіх 73 файлах). Дві ручки налаштування, яких у копіях не було,
   за замовчуванням дають рівно ту саму поведінку, що й найпоширеніша копія:
     setScaleFloor(k) — нижня межа множника кегля TK (0,55 у 41 файлі; 1 —
                        «старі» файли, де кегль не масштабувався зовсім);
     setTextFloor(px) — підлога кегля жирних підписів (0 — немає; 12,5 — 09).
   Стан модуля (TK, CVW, CVCH) читають і сторінки — як живі прив'язки. */
import {BRAND} from './theme.js';
import {$} from './dom.js';

export const CV={};

/* ---- кадр підганяється під пристрій сам ---------------------------------
   Розмір полотна задає тільки CSS, а все, що малюється всередині, рахується
   від цього розміру. TK — множник кегля: напис на 11 px, доречний на широкому
   кадрі, на телефоні накриває півсцени. Опора своя для кожного роду полотна:
   сцені вистачає місця з 560 px, графікові — з 300 (їх по два-три в ряд), тож
   на широкому екрані TK рівно 1 і жоден кадр не змінюється. Це множник, а не
   поріг: планшет дістає своє проміжне значення без жодного медіазапиту. */
export const TKSCENE=560;
export const TKCHART=300;
export let TKMIN=0.55;
export let TK=1;
export let CVW=1e4;
export let CVCH=false;
/* TKMIN=1 вимикає масштабування кегля: так поводилися файли до адаптації
   (cvx без TK у Mechanics/ і частині math_analysis/). */
export function setScaleFloor(k){ TKMIN=k; }

export const tkOf=(w,ref)=>Math.max(TKMIN,Math.min(1,w/ref));

export function cvx(id){
  if(CV[id]){TK=CV[id].tk; CVW=CV[id].w; CVCH=CV[id].ch; return CV[id];}
  const c=$(id); const r=c.getBoundingClientRect();
  if(r.width<2||r.height<2) return null;
  const d=window.devicePixelRatio||1;
  c.width=Math.round(r.width*d); c.height=Math.round(r.height*d);
  const g=c.getContext('2d'); g.setTransform(d,0,0,d,0,0);
  const ch=!!c.closest('.chartbox');
  TK=tkOf(r.width,ch?TKCHART:TKSCENE); CVW=r.width; CVCH=ch;
  return CV[id]={g,w:r.width,h:r.height,el:c,tk:TK,ch};
}

/* Кадр застаріває не лише від вікна: полотно міняє розмір і коли згортається
   бічна панель, і коли перемикається вкладка, і коли пристрій повертають, і
   коли вікно переносять на монітор з іншим DPR. Ловимо все — інакше сцена
   лишається намальованою під учорашній розмір і тягнеться інтерполяцією. */
/* запам'ятані рамки графіків — тут, а не в chart.js, бо їх скидає разом із
   кадрами dropCV() */
export const CHFIT={};
export function dropCV(){for(const k in CV) delete CV[k]; for(const k in CHFIT) delete CHFIT[k];}

/* Підписки, що скидають кеш кадрів. У файлах серії це були інструкції
   верхнього рівня одразу після dropCV(); тут — одна функція, яку сторінка
   кличе в тому самому місці. */
export function watchCanvases(){
  addEventListener('orientationchange',dropCV);
  if(window.visualViewport) visualViewport.addEventListener('resize',dropCV);
  (function dpr(){
    if(!window.matchMedia) return;
    const mq=matchMedia('(resolution: '+(window.devicePixelRatio||1)+'dppx)');
    const on=()=>{dropCV(); dpr();};
    if(mq.addEventListener) mq.addEventListener('change',on,{once:true});
    else if(mq.addListener) mq.addListener(on);
  })();
  /* ResizeObserver — єдиний, хто бачить зміну самого полотна, а не вікна.
     Скидаємо той кадр, що справді змінився; рамки графіків — усі, вони
     прив'язані до кегля. */
  if(window.ResizeObserver){
    const RO=new ResizeObserver(es=>{
      for(const e of es) if(e.target.id) delete CV[e.target.id];
      for(const k in CHFIT) delete CHFIT[k];
    });
    const watch=()=>document.querySelectorAll('canvas[id]').forEach(c=>RO.observe(c));
    addEventListener('DOMContentLoaded',watch);
    watch();
  }
}

/* Ліве поле дорівнює правому — креслення стоїть посередині кадру (§5.1
   переліку сцен). padL і padR — смуги під те, що виходить за саме креслення:
   мітки на лівій стінці, підпис, що відходить праворуч. Коли креслення не
   влазить, лишається хоч padL: краще зсув, ніж обрізаний край. */
export function centerX(frameW,contentW,padL,padR){
  padL=padL||0; padR=(padR==null)?padL:padR;
  return Math.max(padL,padL+(frameW-padL-padR-contentW)/2);
}

/* Будь-який кегль проходить через TK. Додатково o.max (пікселі) стискає
   рядок, коли він мусить уміститись усередині предмета, що змінює розмір. */
/* Нижня межа кеглю для підписів величин. Жирним на полотні малюють саме їх —
   назви векторів, символи, значення; пояснювальні рядки йдуть без жиру й
   лишаються дрібними. Дев'ять з половиною пікселів на проєкторі в аудиторії
   не читаються, тож для підписів ставимо підлогу. */
export let TXTMIN=0;
export function setTextFloor(px){ TXTMIN=px; }

export function txt(g,s,x,y,o={}){
  let sz=(o.bold?Math.max(o.size||11,TXTMIN):(o.size||11))*TK;
  const F=k=>(o.bold?'600 ':'')+k+'px system-ui,sans-serif';
  g.fillStyle=o.color||BRAND.ink;
  g.font=F(sz);
  if(o.max>0){
    const wd=g.measureText(s).width;
    if(wd>o.max){sz=Math.max(sz*0.55,sz*o.max/wd); g.font=F(sz);}
  }
  g.textAlign=o.align||'left'; g.textBaseline=o.base||'alphabetic';
  g.fillText(s,x,y);
  return sz;
}

export function pill(g,s,x,y,o={}){
  g.font=(o.bold?'600 ':'')+(o.bold?Math.max(o.size||11.5,TXTMIN):(o.size||11.5))*TK+'px system-ui,sans-serif';
  const wd=g.measureText(s).width+14*TK;
  g.fillStyle=o.bg||'rgba(252,252,251,.92)';
  g.beginPath(); g.roundRect(x-wd/2,y-13*TK,wd,19*TK,9*TK); g.fill();
  txt(g,s,x,y+1,{...o,align:'center'});
}

export function arrow(g,x1,y1,x2,y2,color,w=2){
  const a=Math.atan2(y2-y1,x2-x1),L=6.5+w*1.2;
  if(Math.hypot(x2-x1,y2-y1)<1.5) return;
  g.strokeStyle=color; g.fillStyle=color; g.lineWidth=w; g.lineCap='round';
  g.beginPath(); g.moveTo(x1,y1); g.lineTo(x2-Math.cos(a)*L*0.6,y2-Math.sin(a)*L*0.6); g.stroke();
  g.beginPath(); g.moveTo(x2,y2);
  g.lineTo(x2-L*Math.cos(a-0.44),y2-L*Math.sin(a-0.44));
  g.lineTo(x2-L*Math.cos(a+0.44),y2-L*Math.sin(a+0.44));
  g.closePath(); g.fill();
}

export function dot(g,x,y,r,fill,ring){
  /* На вузькому кадрі похідний радіус може вийти від'ємним — Canvas на це
     кидає виняток і кадр обривається на півдорозі. Нуль просто нічого не малює. */
  r=Math.max(0,r);
  g.beginPath(); g.arc(x,y,r,0,7);
  g.fillStyle=fill; g.fill();
  if(ring){g.strokeStyle=ring; g.lineWidth=2; g.stroke();}
}

export function niceStep(raw){
  if(!(raw>0)) return 1;
  const p=Math.pow(10,Math.floor(Math.log10(raw)));
  for(const m of [1,2,5,10]) if(raw<=m*p) return m*p;
  return 10*p;
}

/* дуга кута навколо точки (x,y): від a1 до a2 в екранних радіанах */
export function arc(g,x,y,r,a1,a2,color,w=1.2){
  if(!(r>0)) return;
  g.strokeStyle=color; g.lineWidth=w;
  g.beginPath(); g.arc(x,y,r,a1,a2,a2<a1); g.stroke();
}

