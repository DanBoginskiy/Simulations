#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Знімок усіх чисел симуляції — щоб звірити «до» і «після» правок.

Беремо три незалежні зрізи:
  1. еталонні відповіді задач: TASKS[mid].ref(...) на сітці значень кожної
     змінної (низ, середина, верх діапазону) — це сама фізика задачі;
  2. числа бічних панелей після N кроків часу зі сталим dt — це те, що
     читає студент;
  3. числа, намальовані на полотні, перехоплені на fillText.

Стан задається детерміновано: сторінка щойно завантажена, ручок не чіпаємо,
час просуваємо однаково. Різниця в будь-якому зрізі означає, що правка
зачепила фізику або виведення чисел.

  python3 tools/control-numbers.py --out до.json  basic_physics/09-*.html
  python3 tools/control-numbers.py --cmp до.json --out після.json  basic_physics/09-*.html
"""
import sys,os,json,time,glob,argparse
HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.dirname(HERE)
sys.path.insert(0,HERE)

HOOK=r"""
window.__CN={draw:[]};
/* Живий цикл кадрів зупиняємо: інакше час модуля рухається між тим, як ми
   його виставили, і тим, як прочитали, — і два однакові файли дають різні
   числа. Далі час рухаємо тільки самі, сталим кроком. */
window.requestAnimationFrame=function(){return 0;};
(function(){
  const P=CanvasRenderingContext2D.prototype, ft=P.fillText;
  P.fillText=function(t,x,y){
    try{ const s=String(t); if(/\d/.test(s)) __CN.draw.push(s); }catch(e){}
    return ft.apply(this,arguments);
  };
})();
/* Еталонні відповіді задач на сітці значень: саме вони не мають права
   зрушити з місця від жодної правки оформлення. */
window.__refs=function(){
  if(typeof TASKS==='undefined') return null;
  const out={};
  for(const mid in TASKS){
    const T=TASKS[mid], vars=T.vars||[];
    const parts=T.parts||[{what:T.what,ref:T.ref}];
    const env={};
    for(const c in (T.consts||{})) env[c]=T.consts[c].v;
    const rows=[];
    for(let k=0;k<3;k++){
      for(const v of vars) env[v.s]=v.lo+(v.hi-v.lo)*k/2;
      for(const p of parts){
        if(typeof p.ref!=='function') continue;
        let r; try{ r=p.ref(env); }catch(e){ r='ERR'; }
        rows.push((p.what||'')+'@'+k+'='+(typeof r==='number'?r.toPrecision(12):String(r)));
      }
    }
    out[mid]=rows;
  }
  return out;
};
/* Третій зріз — сама фізика модуля: усі числові поля стану й значення всіх
   методів без аргументів. У задачах числа з панелей і полотна прибрано
   навмисне, тож без цього зрізу порівнювати там було б нічого. */
window.__state=function(mid){
  const M=MODULES[mid]; if(!M) return [];
  const out=[];
  for(const k of Object.keys(M).sort()){
    const v=M[k];
    if(typeof v==='number'&&isFinite(v)) out.push(k+'='+v.toPrecision(12));
    else if(typeof v==='function'&&v.length===0&&!/^(init|tick|render|scene|table|charts|reset|gdraw|grips|geo|diagram|setTask|syncAns|updBtn|showMode|showGeom|gcol|push|build|compute)$/.test(k)){
      let r; try{ r=v.call(M); }catch(e){ continue; }
      if(typeof r==='number'&&isFinite(r)) out.push(k+'()='+r.toPrecision(12));
    }
  }
  return out;
};
window.__panel=function(mid){
  const sec=document.getElementById(mid); if(!sec) return [];
  /* Беремо самі числа, а не текст цілком: розмітка формул може змінитися
     (наприклад, символьну частину почне малювати KaTeX), а числа — ні. Саме
     вони тут і є предметом звірки. Дубль MathML, який KaTeX кладе поруч із
     версткою, прибираємо, інакше кожне число порахувалося б двічі. */
  const cl=sec.cloneNode(true);
  /* Символьний запис — не число. Індекс μ₀ чи показник v² складаються з тих
     самих цифр, але жодного обчислення за ними немає: обчислене значення код
     завжди подає через fmt() звичайним текстом. Тому символьні вузли —
     формули KaTeX і старий запис через <var>/<i>/<sub>/<sup> — відкидаємо. */
  for(const m of cl.querySelectorAll('.katex,var,i,sub,sup,[data-tex]')) m.remove();
  const out=[];
  for(const el of cl.querySelectorAll('b,.kv b,td,output,.numrow b')){
    const n=(el.textContent||'').match(/\d+(?:[.,]\d+)?/g);
    if(n) out.push(n.join('|'));
  }
  return out;
};
/* У задачі числа сховані, доки не показано відповідь: щоб порівнювати було що,
   відкриваємо їх і переводимо модуль у вільний режим. */
window.__open=function(mid){
  const M=MODULES[mid]; if(!M) return;
  try{ if('showAns' in M){ M.showAns=true; if(M.syncAns) M.syncAns(); } }catch(e){}
  try{ if('mode' in M && M.mode!=='free'){ M.mode='free'; if(M.showMode) M.showMode(); } }catch(e){}
};
window.__step=function(mid,n,dt){
  const M=MODULES[mid]; if(!M) return;
  /* Час беремо з нуля й рухаємо самі: інакше в знімок потрапляє те, скільки
     кадрів устиг намалювати живий цикл між activate() і зчитуванням, і два
     однакові файли дають різні числа. */
  try{ if('playing' in M) M.playing=true; if('t' in M) M.t=0; if('waitT' in M) M.waitT=0; }catch(e){}
  for(let i=0;i<n;i++){ try{ M.tick(dt); }catch(e){} }
};
"""

def snap(rel,steps=40,dt=0.05):
    from cdp import Page
    p=Page(); p.metrics(1440,900,dpr=2,mobile=False)
    p.goto('file://'+os.path.join(ROOT,rel),1.8)
    p.js(HOOK)
    mods=json.loads(p.js("JSON.stringify(Object.keys(MODULES))"))
    refs=p.js("JSON.stringify(__refs())")
    data={'refs':json.loads(refs) if refs and refs!='null' else None,'mod':{}}
    for m in mods:
        p.js("activate('%s')"%m); time.sleep(0.3)
        p.js("__open('%s')"%m); time.sleep(0.2)
        p.js("__CN.draw=[]")
        p.js("__step('%s',%d,%g)"%(m,steps,dt))
        time.sleep(0.2)
        panel=json.loads(p.js("JSON.stringify(__panel('%s'))"%m))
        state=json.loads(p.js("JSON.stringify(__state('%s'))"%m))
        draw=json.loads(p.js("JSON.stringify(__CN.draw.slice(0,400))"))
        data['mod'][m]={'panel':panel,'draw':draw,'state':state}
    p.close()
    return data

def diff(a,b,rel):
    out=[]
    if a.get('refs')!=b.get('refs'):
        ra,rb=a.get('refs') or {},b.get('refs') or {}
        for k in sorted(set(ra)|set(rb)):
            if ra.get(k)!=rb.get(k):
                for x,y in zip(ra.get(k,[]),rb.get(k,[])):
                    if x!=y: out.append('%s еталон задачі: %s → %s'%(k,x,y))
                if len(ra.get(k,[]))!=len(rb.get(k,[])):
                    out.append('%s: змінилася кількість еталонів'%k)
    for m in sorted(set(a['mod'])|set(b['mod'])):
        A=a['mod'].get(m,{}); B=b['mod'].get(m,{})
        for key,name in (('state','стан'),('panel','панель'),('draw','полотно')):
            x,y=A.get(key,[]),B.get(key,[])
            if x!=y:
                sx,sy=set(x),set(y)
                gone=sorted(sx-sy)[:6]; new=sorted(sy-sx)[:6]
                out.append('%s/%s: зникло %s · з\'явилося %s'%(m,name,gone,new))
    return out

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('files',nargs='+')
    ap.add_argument('--out',required=True)
    ap.add_argument('--cmp')
    a=ap.parse_args()
    os.chdir(ROOT)
    files=[]
    for f in a.files: files+=sorted(glob.glob(f))
    res={}
    for f in files:
        res[f]=snap(f)
        print('знято %s'%f)
    json.dump(res,open(a.out,'w'),ensure_ascii=False,indent=1)
    if a.cmp:
        old=json.load(open(a.cmp))
        bad=0
        for f in files:
            if f not in old: print('%s — нема в знімку «до»'%f); continue
            d=diff(old[f],res[f],f)
            print('%-52s %s'%(f,'числа збіглися' if not d else 'РОЗБІЖНОСТІ: %d'%len(d)))
            for x in d[:20]: print('    '+x)
            bad+=len(d)
        print('---- розбіжностей:',bad)
        sys.exit(1 if bad else 0)
