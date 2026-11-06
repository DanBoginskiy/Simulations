/* engine/format.js — числа так, як їх пише серія: кома, справжній мінус, степені.

   fmt — варіант 71 файлу з 73 (у Mechanics/kinematics-point.html і
   newton-dynamics.html є ще перевірка на нескінченність, там вона лишається
   локальною). Модуль чистий — без DOM, його імпортують і тести. */

export const fmt=(n,d=1)=>(+n).toFixed(d).replace('.',',').replace('-','−');

export const DEG=Math.PI/180;

export const SUP={'-':'⁻','0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹'};

export function sci(n,d=3){
  if(!isFinite(n)||n===0) return fmt(0,d);
  const e=Math.floor(Math.log10(Math.abs(n)));
  return fmt(n/Math.pow(10,e),d)+'·10'+String(e).split('').map(c=>SUP[c]||c).join('');
}

/* час доби в годинній мірі: 14 г 32 хв 07 с */
export function hms24(hours){
  let tot=Math.round((((hours%24)+24)%24)*3600);
  if(tot>=86400) tot-=86400;
  const h=Math.floor(tot/3600),m=Math.floor(tot%3600/60),s=tot%60;
  return h+' г '+String(m).padStart(2,'0')+' хв '+String(s).padStart(2,'0')+' с';
}

export function hm24(hours){
  let tot=Math.round((((hours%24)+24)%24)*60);
  if(tot>=1440) tot-=1440;
  return Math.floor(tot/60)+' г '+String(tot%60).padStart(2,'0')+' хв';
}

/* тривалість: 2 год 02 хв 00 с або 47 хв 12 с */
export function durHM(min){
  const tot=Math.round(Math.abs(min)*60);
  const h=Math.floor(tot/3600),m=Math.floor(tot%3600/60),s=tot%60;
  return (h?h+' год '+String(m).padStart(2,'0')+' хв ':m+' хв ')+String(s).padStart(2,'0')+' с';
}

