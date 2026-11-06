/* engine/sphere.js — ортографічна проєкція сфери (глобус, небесна сфера).

   Тексти з basic_physics/00-kinematics-rotation.html (у 09 — ідентичні).
   dragSphere сюди не входить: у двох файлах він різний (шайба для дотику
   проти мішеней ручок) і лишається локальним. */
import {BRAND} from './theme.js';
import {DEG} from './format.js';
import {txt,dot} from './canvas.js';

/* ---------- сфера: ортографічна проєкція ---------- */
/* V = {rot, tilt, R, cx, cy}; rot — азимут камери, tilt — нахил осі до глядача */
export function sphPt(lat,lon,V){
  const la=lat*DEG, lo=(lon+V.rot)*DEG, t=V.tilt*DEG;
  const ct=Math.cos(t), st=Math.sin(t);
  const X=Math.cos(la)*Math.cos(lo), Y=Math.cos(la)*Math.sin(lo), Z=Math.sin(la);
  return {x:V.cx+V.R*Y, y:V.cy-V.R*(-X*st+Z*ct), front:(X*ct+Z*st)>=0};
}

/* крива на сфері: передня частина суцільна, задня — штрихова й бліда */
export function sphCurve(g,V,gen,n,color,wd,opt){
  opt=opt||{};
  let run=null,cur=null;
  const flush=()=>{
    if(run&&run.length>1&&!(cur===false&&opt.hideBack)){
      g.strokeStyle=color;
      g.lineWidth=cur?wd:Math.max(1,wd-0.8);
      g.setLineDash(cur?(opt.dash||[]):[3,3]);
      g.globalAlpha=cur?1:0.45;
      g.beginPath(); run.forEach((p,i)=>i?g.lineTo(p.x,p.y):g.moveTo(p.x,p.y)); g.stroke();
      g.globalAlpha=1; g.setLineDash([]);
    }
    run=null;
  };
  for(let i=0;i<=n;i++){
    const c=gen(i/n);
    const p=sphPt(c[0],c[1],V);
    if(run===null){run=[p]; cur=p.front;}
    else if(p.front!==cur){run.push(p); flush(); run=[p]; cur=p.front;}
    else run.push(p);
  }
  flush();
}

/* сітка меридіанів і паралелей + диск сфери */
export function sphBase(g,V,fill){
  dot(g,V.cx,V.cy,V.R,fill);
  g.strokeStyle=BRAND.axis; g.lineWidth=1.2;
  g.beginPath(); g.arc(V.cx,V.cy,V.R,0,7); g.stroke();
  for(let la=-60;la<=60;la+=30) sphCurve(g,V,u=>[la,u*360],120,BRAND.grid,1);
  for(let lo=0;lo<360;lo+=30) sphCurve(g,V,u=>[-90+u*180,lo],60,BRAND.grid,1);
}

/* вісь обертання сфери */
export function sphAxis(g,V,color,labN,labS){
  const N=sphPt(90,0,V),S=sphPt(-90,0,V);
  g.strokeStyle=color; g.lineWidth=1.5; g.setLineDash([4,3]);
  g.beginPath();
  g.moveTo(S.x,S.y); g.lineTo(N.x,N.y); g.stroke(); g.setLineDash([]);
  dot(g,N.x,N.y,3.5,color); dot(g,S.x,S.y,3.5,color);
  txt(g,labN,N.x+7,N.y-4,{color:BRAND.sec,size:11,bold:true});
  txt(g,labS,S.x+7,S.y+12,{color:BRAND.sec,size:11,bold:true});
}

