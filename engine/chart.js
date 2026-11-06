/* engine/chart.js — лінійний графік із перехрестям-підказкою.

   drawChart — варіант 21 файлу (Theoretical-Mechanics/, basic_physics/): поділки
   осі x через niceStep, підписи серій розведено по вертикалі, вісь нуля — лише
   коли нуль у межах. У серії є ще сім варіантів (див. docs/engine-inventory.md);
   вони лишаються у своїх файлах, доки автор не вирішить, який із них канон. */
import {BRAND} from './theme.js';
import {$} from './dom.js';
import {fmt} from './format.js';
import {CHFIT,txt,dot,niceStep} from './canvas.js';

/* простий лінійний графік із перехрестям-підказкою; рамки запам'ятовує
   CHFIT з canvas.js */
export function drawChart(box,opt){
  const {g,w,h}=box;
  /* Нижнє поле більше за верхнє: під віссю стоять і числа поділок, і назва
     самої осі — рядком нижче, при правому краї поля графіка. */
  const L=44,R=54,T=12,B=40,pw=w-L-R,ph=h-T-B;
  if(pw<40||ph<30){g.clearRect(0,0,w,h); return null;}
  /* ---- масштаб графіка не «дихає» ---------------------------------------
     Рамка, з якою графік з'явився, лишається сталою. Вона розширюється лише
     тоді, коли крива справді вийшла за межі осей, і назад ніколи не
     стискається — інакше та сама крива щокадру стрибала б угору-вниз.
     Якщо модуль перемкнули на іншу величину (розмах відрізняється в рази),
     рамку беруть заново — один раз. Пам'ять у кожного полотна власна. */
  let yMin=opt.yMin, yMax=opt.yMax;
  {
    const ckey=(box.el&&box.el.id)||opt.yLab||'';
    const want=yMax-yMin, f=CHFIT[ckey];
    if(ckey&&want>0){
      if(f&&want<=f.span*4&&want*4>=f.span){
        yMin=f.lo; yMax=f.hi;
        let lo=Infinity,hi=-Infinity;
        for(const s of (opt.series||[])) if(s&&s.ys)
          for(const v of s.ys) if(isFinite(v)){if(v<lo)lo=v; if(v>hi)hi=v;}
        const pad=(yMax-yMin)*0.04;
        if(isFinite(lo)&&lo<yMin) yMin=lo-pad;
        if(isFinite(hi)&&hi>yMax) yMax=hi+pad;
      }
      CHFIT[ckey]={lo:yMin,hi:yMax,span:yMax-yMin};
    }
  }
  const X=t=>L+t/opt.tMax*pw;
  const Y=y=>T+(1-(y-yMin)/(yMax-yMin))*ph;
  g.clearRect(0,0,w,h);
  g.lineWidth=1;
  const yd=opt.yDec||0;
  const st=niceStep((yMax-yMin)/4.5);
  for(let y=Math.ceil(yMin/st)*st;y<=yMax+1e-9;y+=st){
    g.strokeStyle=BRAND.grid; g.beginPath(); g.moveTo(L,Y(y)+.5); g.lineTo(L+pw,Y(y)+.5); g.stroke();
    txt(g,fmt(Math.abs(y)<1e-9?0:y,yd),L-6,Y(y)+3,{color:BRAND.mut,size:10,align:'right'});
  }
  const xs=opt.xStep||niceStep(opt.tMax/5);
  for(let t=0;t<=opt.tMax+1e-9;t+=xs){
    g.strokeStyle=t<1e-9?BRAND.axis:BRAND.grid;
    g.beginPath(); g.moveTo(X(t)+.5,T); g.lineTo(X(t)+.5,T+ph); g.stroke();
    txt(g,fmt(t,opt.xDec||0),X(t),T+ph+15,{color:BRAND.mut,size:10,align:'center'});
  }
  if(yMin<0&&yMax>0){
    g.strokeStyle=BRAND.axis; g.beginPath(); g.moveTo(L,Y(0)+.5); g.lineTo(L+pw,Y(0)+.5); g.stroke();
  }
  /* одиниці осей — у верхньому рядку кадру: біля самих осей вони
     наїжджають то на верхню поділку, то на прямий підпис серії */
  txt(g,opt.yLab,2,9,{color:BRAND.mut,size:10.5});
  /* Назва осі абсцис — під самою віссю, у тому місці, де поле графіка
     закінчується. Угорі вона читалася як другий заголовок і зліплювалася
     з назвою осі ординат на вузькому кадрі. */
  txt(g,opt.xLab||'t, с',L+pw,T+ph+31,{color:BRAND.mut,size:10.5,align:'right'});
  const ends=[];
  for(const s of opt.series){
    if(!s.ts||s.ts.length<2) continue;
    g.strokeStyle=s.color; g.lineWidth=2; g.lineJoin='round'; g.setLineDash(s.dash||[]);
    g.beginPath();
    for(let i=0;i<s.ts.length;i++){const px=X(s.ts[i]),py=Y(s.ys[i]); i?g.lineTo(px,py):g.moveTo(px,py);}
    g.stroke(); g.setLineDash([]);
    const lx=X(s.ts[s.ts.length-1]),ly=Y(s.ys[s.ys.length-1]);
    dot(g,lx,ly,3,s.color);
    ends.push({x:lx,y:ly,label:s.label});
  }
  /* прямі підписи серій розводимо по вертикалі — інакше при близьких
     значеннях вони лягають один на одного і жоден не читається */
  ends.sort((a,b)=>a.y-b.y);
  for(let i=1;i<ends.length;i++)
    if(ends[i].y-ends[i-1].y<13) ends[i].y=ends[i-1].y+13;
  for(const e of ends) txt(g,e.label,e.x+7,Math.min(h-4,e.y+4),{color:BRAND.ink,size:11,bold:true});
  if(opt.hover!=null&&opt.hover>=L&&opt.hover<=L+pw&&opt.series[0].ts.length>1){
    const t=(opt.hover-L)/pw*opt.tMax;
    const s0=opt.series[0];
    const tc=Math.min(t,s0.ts[s0.ts.length-1]);
    const hx=X(tc);
    g.strokeStyle=BRAND.axis; g.setLineDash([3,3]);
    g.beginPath(); g.moveTo(hx+.5,T); g.lineTo(hx+.5,T+ph); g.stroke(); g.setLineDash([]);
    const vals=[];
    for(const s of opt.series){
      let i=s.ts.length-1;
      while(i>0&&s.ts[i]>tc) i--;
      const v=s.ys[Math.min(i+(s.ts[i]<tc?1:0),s.ys.length-1)];
      dot(g,hx,Y(v),3.5,'#fff',s.color); vals.push(v);
    }
    return {t:tc,vals,px:hx};
  }
  return null;
}

export function makeTip(wrapId){
  const w=$(wrapId); const d=document.createElement('div');
  d.className='tip'; w.appendChild(d); return d;
}

/* Перехрестя ставить і курсор, і палець: на сенсорі pointermove без
   натиснутої кнопки не приходить, тож саме pointerdown робить підказку
   доступною на телефоні та планшеті. Наступний дотик поза полотном її знімає. */
export function hover(canvasId,state){
  const c=$(canvasId);
  const at=e=>{const r=c.getBoundingClientRect();
    state.x=e.clientX-r.left; state.cy=e.clientY-r.top;};
  c.addEventListener('pointermove',e=>{if(e.pointerType==='mouse'||e.buttons) at(e);});
  c.addEventListener('pointerdown',e=>{at(e); if(e.pointerType!=='mouse') e.preventDefault();});
  c.addEventListener('pointerleave',()=>{state.x=null;});
  addEventListener('pointerdown',e=>{if(!c.contains(e.target)) state.x=null;},true);
}

/* показати підказку графіка; names = [[підпис,колір],…] */
export function showTip(el,r,unit,st,names,dec){
  if(!r){el.style.display='none'; return;}
  el.innerHTML='<div class="th">'+(st.xlab||'t')+' = '+fmt(r.t,st.xdec==null?1:st.xdec)+' '+(st.xunit||'с')+'</div>'+
    r.vals.map((v,i)=>'<div><span class="chip" style="background:'+names[i][1]+'"></span>'+
      names[i][0]+' — '+fmt(v,dec==null?1:dec)+' '+unit+'</div>').join('');
  el.style.display='block';
  const bw=el.offsetWidth;
  el.style.left=Math.max(2,Math.min(r.px+14,el.parentElement.clientWidth-bw-4))+'px';
  el.style.top=Math.max(20,(st.cy||60)-10)+'px';
}

