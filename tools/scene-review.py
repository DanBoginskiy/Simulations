#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Перевіряльник сцен за SCENE-REVIEW.md.

Половину пунктів переліку в коді не видно, тому тут два роди перевірок:
читання джерела (швидко, без браузера) і прогін сторінки в headless Chrome
(повільно, зате бачить намальоване). Звіт має стати порожнім — це і є
критерій готовності етапів 1–3.

  python3 tools/scene-review.py                     # усі фізичні файли, усі перевірки
  python3 tools/scene-review.py --static            # лише читання джерела
  python3 tools/scene-review.py --no-sweep          # без проходу діапазонів ручок
  python3 tools/scene-review.py basic_physics/09-*.html
"""
import re,sys,os,glob,json,time
HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.dirname(HERE)
sys.path.insert(0,HERE)

SIZES=[(390,844),(768,1024),(1440,900)]
VAGUE=re.compile(r'(зараз|поточн\w*|обран\w*|вибран\w*)$',re.I)

# Одиниці, які самі по собі назвою величини не є. Усе інше на осі — уже назва:
# «I/I₀», «T/T₀», «η», «k», «частка», «№ дошки» кажуть, що відкладено, і одиниці
# не потребують, бо безрозмірні.
UNITS=set('''
м см мм мкм нм км м/с см/с мм/с км/с м/с² см/с² рад рад/с рад/с² ° ′ ″ ᵐ
кг г т кг·м/с г·м/с Н кН мН Н·м кН·м Дж кДж МДж мДж мкДж еВ кеВ МеВ
Вт кВт МВт мВт Вт/кг Вт/м² кВт·год
К K °C °К Па кПа МПа мм рт. ст. атм
А мА мкА кА В кВ мВ мкВ Ом кОм МОм Кл мкКл нКл пКл
Ф мкФ нФ пФ Гн мГн мкГн Вб мВб мкВб Тл мТл мкТл нТл
В/м кВ/м МВ/м В/см
Гц кГц МГц ГГц с мс мкс нс пс хв год доба рік
л мл м³ см³ дм³ кг/м³ г/см³ г/м³ моль ммоль дптр
% ‰ кг/моль г/моль м²/с Дж/(кг·К) Дж/К
'''.split())
def only_unit(y):
    parts=[q.strip() for q in y.split(' · ')]
    return bool(parts) and all(q in UNITS for q in parts)

# ─────────────────────────── розбір джерела ───────────────────────────

def span(s,i,op='(',cl=')'):
    d=0;q=None
    while i<len(s):
        c=s[i]
        if q:
            if c=='\\': i+=2; continue
            if c==q: q=None
        elif c in '\'"`': q=c
        elif c==op: d+=1
        elif c==cl:
            d-=1
            if d==0: return i
        i+=1
    raise ValueError('дужка не закрита')

def field(s,a,b,name):
    d=0;q=None;i=a
    while i<b:
        c=s[i]
        if q:
            if c=='\\': i+=2; continue
            if c==q: q=None
            i+=1; continue
        if c in '\'"`': q=c; i+=1; continue
        if c in '{[(': d+=1
        elif c in '}])': d-=1
        elif d==1 and re.match(r'%s\s*:'%re.escape(name),s[i:b]):
            j=s.index(':',i)+1
            while j<b and s[j]==' ': j+=1
            k=j;dd=0;qq=None
            while k<b:
                ch=s[k]
                if qq:
                    if ch=='\\': k+=2; continue
                    if ch==qq: qq=None
                elif ch in '\'"`': qq=ch
                elif ch in '{[(': dd+=1
                elif ch in '}])':
                    if dd==0: break
                    dd-=1
                elif ch==',' and dd==0: break
                k+=1
            return s[j:k].strip()
        i+=1
    return None

def unq(v):
    if v is None: return None
    v=v.strip()
    return v[1:-1] if len(v)>1 and v[0] in '\'"' and v[-1]==v[0] else None

def static(path):
    """Пункти, що видно в коді: 4.2, 4.4, 2.1."""
    s=open(path,encoding='utf-8').read()
    out=[]
    L=lambda i:s[:i].count('\n')+1
    for m in re.finditer(r'\bdrawChart\s*\(',s):
        a=m.end()-1
        try: b=span(s,a)
        except ValueError: continue
        oi=s.index('{',a)
        y=unq(field(s,oi,b,'yLab'))
        # 4.2: на осі мусить бути назва величини, а не лише одиниця
        if y is not None and ',' not in y and only_unit(y):
            out.append((L(m.start()),'4.2','вісь без назви величини: yLab=%r'%y))
        ser=field(s,oi,b,'series')
        if ser:
            for lm in re.finditer(r"label\s*:\s*'([^']*)'",ser):
                if VAGUE.match(lm.group(1)):
                    out.append((L(m.start()),'4.4','розпливчаста легенда: %r'%lm.group(1)))
    # 4.4 у розмітці легенд і підказок
    for m in re.finditer(r'<span class="chip[^"]*"></span>([^<]+)</span>',s):
        if VAGUE.match(m.group(1).strip()):
            out.append((L(m.start()),'4.4','розпливчаста легенда розмітки: %r'%m.group(1)))
    for m in re.finditer(r"\['([^']+)',",s):
        if VAGUE.match(m.group(1)):
            out.append((L(m.start()),'4.4','розпливчаста назва в підказці: %r'%m.group(1)))
    # 2.1: стеля довжини стрілки — Math.min(<число>, …) прямо в аргументі arrow()
    for m in re.finditer(r'\barrow\s*\(',s):
        a=m.end()-1
        try: b=span(s,a)
        except ValueError: continue
        for c in re.finditer(r'Math\.min\(\s*(\d+(?:\.\d+)?)\s*,',s[a:b]):
            out.append((L(m.start()),'2.1','стеля довжини стрілки: Math.min(%s, …)'%c.group(1)))
    return out

# ─────────────────────────── прогін сторінки ───────────────────────────

HOOK=r"""
window.__R={clash:[],dup:[],num:[]};
(function(){
  /* Підписи осей стоять одним рядком — зліва величина, справа аргумент. */
  const dc=window.drawChart;
  window.drawChart=function(box,opt){
    try{
      const g=box.g,w=box.w,K=(typeof TK!=='undefined'?TK:1);
      g.save(); g.font=(10.5*K)+'px system-ui,sans-serif';
      const a=g.measureText(opt.yLab||'').width, b=g.measureText(opt.xLab||'t, с').width;
      g.restore();
      if(a+b+10>w) __R.clash.push([(box.el&&box.el.id)||'?',opt.yLab,opt.xLab||'t, с',Math.round(w)]);
    }catch(e){}
    return dc.apply(this,arguments);
  };
  /* Усі написи сцени за один кадр: дублі й числа в коді не видно. */
  /* Перехоплюємо не txt(), а сам fillText: у physics_tasks txt() спершу зрізає
     з рядка числа («v = 12,3 м/с» → «v»), і, читаючи його доводи, ми бачили б
     на сцені числа, яких там немає. Місце теж записуємо: txtN і pillN самі
     кличуть txt, тож один підпис інакше потрапляв би до списку двічі й
     виглядав дублем. Дубль — це рядок, намальований у двох різних точках. */
  window.__SEEN=[]; window.__CUR=null;
  const P=CanvasRenderingContext2D.prototype, ft=P.fillText, st=P.strokeText;
  P.fillText=function(t,x,y){
    try{ if(this===__CUR) __SEEN.push([String(t),Math.round(x||0),Math.round(y||0)]); }catch(e){}
    return ft.apply(this,arguments);
  };
  P.strokeText=function(t,x,y){ return st.apply(this,arguments); };
})();
window.__scan=function(id){
  const b=(typeof cvx==='function')?cvx(id):null; if(!b) return null;
  __CUR=b.g; __SEEN=[];
  /* не в кожного модуля є scene(): деякі малюють одразу з render() */
  const M=MODULES[ACT], draw=M.scene||M.render;
  if(typeof draw!=='function'){ __CUR=null; return null; }
  try{ draw.call(M); }catch(e){ __CUR=null; return {err:String(e&&e.message||e)}; }
  __CUR=null;
  const seen=__SEEN.slice();
  const at={};
  for(const [t,x,y] of seen){
    const k=t.trim(); if(!k) continue;
    (at[k]=at[k]||[]).push([x,y]);
  }
  const dup=[];
  for(const k in at){
    /* «+», «−», «→», «0» повторюються законно: це знаки різних зарядів і
       поділки, а не та сама величина, названа двічі. Дубль — це підпис із
       літерою, довший за один знак. */
    if(k.length>22||k.length<2||!/[A-Za-zА-Яа-яІіЇїЄєҒґ]/.test(k)) continue;
    const ps=at[k];
    let far=false;
    for(let i=0;i<ps.length&&!far;i++) for(let j=i+1;j<ps.length;j++)
      if(Math.hypot(ps[i][0]-ps[j][0],ps[i][1]-ps[j][1])>6){far=true; break;}
    if(far) dup.push(k);
  }
  return {dup,num:seen.filter(([t])=>/\d/.test(t)).map(([t])=>t),
          labels:seen.map(([t])=>t),all:seen.length};
};
/* Межі намальованого — без заголовка вгорі й смуги ручок унизу. Де ця смуга
   починається, знає сам модуль: gcol(b).gtop. Стала величина тут не годиться —
   у половині модулів саме внизу кадру й лежить креслення (доріжка, підлога),
   і відрізавши смугу на око, ми міряли б поля не того, що видно. */
/* Пункт 6.1: кожна величина з умови мусить бути на кресленні. Що саме задано
   студентові, точно знає сама задача — TASKS[mid].vars[].s; шукану позначають
   на сцені літерою X. */
window.__given=function(mid){
  try{
    if(typeof TASKS==='undefined'||!TASKS[mid]) return null;
    return (TASKS[mid].vars||[]).map(v=>v.s);
  }catch(e){ return null; }
};
window.__gtop=function(id){
  try{
    const M=MODULES[ACT]; if(!M.gcol) return null;
    const b=cvx(id); if(!b) return null;
    const C=M.gcol(b);
    return (C&&isFinite(C.gtop))?C.gtop:null;
  }catch(e){ return null; }
};
window.__ink=function(id,top,bot){
  const el=document.getElementById(id); if(!el) return null;
  const g=el.getContext('2d'), W=el.width, H=el.height;
  const d=g.getImageData(0,0,W,H).data;
  const r=el.getBoundingClientRect(), k=W/Math.max(1,r.width);
  const y0=Math.round(top*k), y1=Math.round(H-bot*k);
  let lo=W, hi=-1;
  for(let y=Math.max(0,y0);y<Math.min(H,y1);y++){
    const row=y*W*4;
    for(let x=0;x<W;x++) if(d[row+x*4+3]>24){ if(x<lo)lo=x; if(x>hi)hi=x; }
  }
  if(hi<0) return {empty:true};
  return {left:lo/k, right:(W-1-hi)/k, w:r.width};
};
"""

def runtime(rel,sizes=SIZES):
    from cdp import Page
    out=[]
    for w,h in sizes:
        p=Page(); p.metrics(w,h,dpr=2,mobile=(w<900))
        p.goto('file://'+os.path.join(ROOT,rel),1.7)
        p.js(HOOK)
        mods=json.loads(p.js("JSON.stringify(Object.keys(MODULES))"))
        tasks='TASKS' in (p.js("Object.keys(window).join(' ')") or '') or 'physics_tasks' in rel
        for m in mods:
            p.js("activate('%s')"%m); time.sleep(0.4)
            r=p.js("JSON.stringify(__scan('%sscene')||null)"%m)
            r=json.loads(r) if r else None
            if r and r.get('err'):
                out.append(('%dx%d'%(w,h),m,'—','виняток у scene(): '+r['err']))
            elif r:
                for d in r['dup']:
                    # перелік на розгляд, не вирок: див. межу пункту 3.1 у SCENE-REVIEW.md
                    out.append(('%dx%d'%(w,h),m,'3.1?','напис двічі на сцені (на розгляд): %r'%d))
                if tasks:
                    # 6.4: готова формула на сцені задачі — це вже відповідь
                    for t in (r.get('labels') or []):
                        u=t.strip()
                        if len(u)<5 or len(u)>48: continue
                        if '=' not in u and '√' not in u: continue
                        if not re.search(r'[A-Za-zА-Яа-яα-ωΑ-Ω]',u): continue
                        # «X = τ₁/τ₂» — це означення шуканої величини, якого
                        # вимагає 6.1, а не готовий розв'язок: ліворуч сам X.
                        if re.match(r'^X[₀-₉0-9]?\s*=',u): continue
                        if re.search(r'[=√^]\s*[^\s]', u) and re.search(r'[+\-·*/()]|√', u):
                            out.append(('%dx%d'%(w,h),m,'6.4','формула на сцені задачі: %r'%u))
                    # Поділка лінійки чи кінець шкали — не «число з умови»:
                    # підстановкою з них відповідь не виходить. Шукаємо саме
                    # значення — число разом з одиницею або зі знаком рівності.
                    VAL=re.compile(r'\d.*(=|\b(м|см|мм|км|кг|г|с|мс|К|°|Па|кПа|Н|Дж|В|А|Ом|Гц|нм|мкм|моль|%)\b)')
                    for t in sorted({u for u in (r['num'] or []) if VAL.search(u)})[:4]:
                        out.append(('%dx%d'%(w,h),m,'6.4','число з умови на сцені задачі: %r'%t))
                    gv=p.js("JSON.stringify(__given('%s'))"%m)
                    gv=json.loads(gv) if gv and gv!='null' else None
                    if gv is not None:
                        blob=' '.join(r.get('labels') or [])
                        miss=[v for v in gv if v and v not in blob]
                        for v in miss:
                            out.append(('%dx%d'%(w,h),m,'6.1','величини з умови немає на сцені: %r'%v))
                        if 'X' not in blob:
                            out.append(('%dx%d'%(w,h),m,'6.1','шукану величину не позначено на сцені літерою X'))
            # 5.1 центрування: поля зліва й справа без заголовка й повзунків
            gt=p.js("__gtop('%sscene')"%m)
            k=p.js("JSON.stringify(__ink('%sscene',46,%s)||null)"
                   %(m,('Math.max(0,el0h-%g)'%gt) if gt else '0'))
            if gt:
                k=p.js("JSON.stringify((function(){const el=document.getElementById('%sscene');"
                       "return __ink('%sscene',46,Math.max(0,el.getBoundingClientRect().height-%g))})()||null)"
                       %(m,m,gt))
            k=json.loads(k) if k else None
            if k and not k.get('empty') and k['w']>0:
                l,rr=k['left'],k['right']
                # Межа з переліку: різниця полів понад 12 % ширини кадру.
                # Відносна межа тут не годиться — при полях 13 і 7 px вона
                # спрацьовує, хоч креслення просто заповнює кадр.
                if abs(l-rr)>0.12*k['w']:
                    # перелік на розгляд: у межі намальованого входять і підписи,
                    # і смуги вибору — див. межу пункту 5.1 у SCENE-REVIEW.md
                    out.append(('%dx%d'%(w,h),m,'5.1?','поля не рівні, глянути на знімок: %d і %d px при ширині %d'
                                %(round(l),round(rr),round(k['w']))))
        for c in json.loads(p.js("JSON.stringify(__R.clash)")):
            out.append(('%dx%d'%(w,h),c[0],'3.5','підписи осей зійшлися: «%s» + «%s» у %d px'%(c[1],c[2],c[3])))
        for e in json.loads(p.js("JSON.stringify(window.__err||[])")):
            out.append(('%dx%d'%(w,h),'—','—','помилка виконання: '+e))
        p.close()
    return out

# ───────────────── 2.1: чи не завмирає довжина стрілки ─────────────────

SWEEP_HOOK=r"""
window.__AR=[]; window.__ARI=0;
(function(){
  const a=window.arrow;
  window.arrow=function(g,x1,y1,x2,y2){
    try{ __AR.push([__ARI++,Math.round(Math.hypot(x2-x1,y2-y1)*10)/10]); }catch(e){}
    return a.apply(this,arguments);
  };
})();
window.__sweep=function(mid,slid,n){
  const el=document.getElementById(slid); if(!el) return null;
  const lo=+el.min, hi=+el.max, keep=el.value, out=[];
  for(let k=0;k<n;k++){
    el.value=String(lo+(hi-lo)*k/(n-1));
    el.dispatchEvent(new Event('input',{bubbles:true}));
    __AR=[]; __ARI=0;
    try{ const M=MODULES[mid]; (M.scene||M.render).call(M); }catch(e){ }
    out.push(__AR.slice());
  }
  el.value=keep; el.dispatchEvent(new Event('input',{bubbles:true}));
  return out;
};
/* Ручка на полотні — теж діапазон, і в багатьох файлах єдиний. Ведемо її від
   краю до краю кадру: межі всередині move() самі й обріжуть зайве. */
window.__grips=function(mid){
  try{ const g=MODULES[mid].grips(); return g?g.length:0; }catch(e){ return 0; }
};
window.__sweepGrip=function(mid,gi,n,ax){
  /* Ручку ведемо по одній осі за раз: у двовимірної ручки (місце предмета й
     його висота в одному хваті) діагональний хід означає, що одна величина
     давно вперлася в межу, поки друга ще йде, — і це виглядало б завмиранням. */
  const b=cvx(mid+'scene'); if(!b) return null;
  const out=[];
  let sx=null,sy=null;
  try{ const g0=MODULES[mid].grips()[gi]; if(!g0) return null; sx=g0.x; sy=g0.y; }catch(e){ return null; }
  for(let k=0;k<n;k++){
    const f=k/(n-1);
    try{
      const g=MODULES[mid].grips()[gi]; if(!g||!g.move) return null;
      if(ax==='y') g.move(sx, 4+(b.h-8)*f);
      else g.move(4+(b.w-8)*f, sy);
    }catch(e){ return null; }
    __AR=[]; __ARI=0;
    try{ const M=MODULES[mid]; (M.scene||M.render).call(M); }catch(e){ }
    /* Разом із кадром запам'ятовуємо, де стала сама ручка: коли величина
       дійшла до свого краю, ручка стоїть, і такий крок про стелю нічого не
       каже — то просто кінець діапазону. */
    let gp=null;
    try{ const g2=MODULES[mid].grips()[gi]; gp=[Math.round(g2.x*10)/10,Math.round(g2.y*10)/10]; }catch(e){}
    out.push({a:__AR.slice(),p:gp});
  }
  return out;
};
"""

def sweep(rel,N=13):
    from cdp import Page
    p=Page(); p.metrics(1440,900,dpr=2,mobile=False)
    p.goto('file://'+os.path.join(ROOT,rel),1.7)
    p.js(HOOK)
    out=[]
    for m in json.loads(p.js("JSON.stringify(Object.keys(MODULES))")):
        p.js("activate('%s')"%m); time.sleep(0.35)
        sl=json.loads(p.js("""JSON.stringify([...document.querySelectorAll('#%s input[type=range]')]
            .map(i=>i.id).filter(Boolean))"""%m))
        ng=p.js("__grips('%s')"%m) or 0
        runs=[('повзунок '+x,"__sweep('%s','%s',%d)"%(m,x,N)) for x in sl]
        for g in range(ng):
            for ax in ('x','y'):
                runs.append(('ручка %d по %s'%(g,ax),"__sweepGrip('%s',%d,%d,'%s')"%(m,g,N,ax)))
        for s,expr in runs:
            r=p.js("JSON.stringify(%s)"%expr)
            if not r or r=='null': continue
            frames=json.loads(r)
            if not frames: continue
            if isinstance(frames[0],dict):
                # лишаємо тільки кроки, на яких ручка зрушила з місця
                keep=[f for k,f in enumerate(frames)
                      if k==0 or f['p'] is None or frames[k-1]['p'] is None or f['p']!=frames[k-1]['p']]
                frames=[f['a'] for f in keep]
            if not frames or not frames[0] or len(frames)<6: continue
            # Номер стрілки в кадрі — це порядок виклику arrow(). Він щось
            # означає лише тоді, коли кількість стрілок на всьому проході та
            # сама: інакше №19 на одному кроці й №19 на іншому — різні стрілки.
            if len(set(len(f) for f in frames))!=1: continue
            k=len(frames[0])
            for i in range(k):
                L=[f[i][1] for f in frames]
                rng=max(L)-min(L)
                if rng<8: continue          # не масштабована стрілка — стеля їй ні до чого
                top=max(L)
                # Стеля спрацьовує саме на максимумі: довжина доходить до неї
                # й далі стоїть, хоч ручку ведуть далі.
                plateau=sum(1 for v in L if top-v<0.6)
                # Звіряти з числовою стелею в коді марно: та сама константа
                # буває й висотою смуги, і кеглем. Значення має сам факт —
                # ручку ведуть, а стрілка стоїть.
                if plateau>=max(4,int(len(L)*0.45)):
                    out.append('%s / %s → стрілка №%d стоїть на %g px у %d з %d робочих кроків (розмах %g px)'
                               %(m,s,i,top,plateau,len(L),round(rng,1)))
    p.close()
    return [('усі ширини','—','2.1',x) for x in out]


# ─────────────────────────── звіт ───────────────────────────

def main():
    args=[a for a in sys.argv[1:] if not a.startswith('--')]
    only_static='--static' in sys.argv
    only_run='--runtime' in sys.argv
    no_sweep=only_static or '--no-sweep' in sys.argv
    os.chdir(ROOT)
    files=args or (sorted(glob.glob('basic_physics/*.html'))
                   +sorted(glob.glob('physics_tasks/*.html'))
                   +sorted(glob.glob('Theoretical-Mechanics/*.html')))
    total=0
    for f in files:
        rows=[]
        if not only_run:
            rows+=[('—',str(l),c,t) for l,c,t in static(f)]
        if not only_static:
            rows+=runtime(f)
        if not no_sweep:
            rows+=sweep(f)
        # Та сама вада на трьох ширинах — це одна вада. Складаємо ширини в один
        # рядок: інакше звіт утричі довший, а працювати з ним утричі важче.
        agg={}
        for a,b,c,t in rows:
            k=(b,c,re.sub(r'\d+','№',t))
            g=agg.setdefault(k,{'w':[],'t':t})
            if a not in g['w']: g['w'].append(a)
            g['t']=t     # числа лишаємо від найширшого кадру — він іде останнім
        total+=len(agg)
        print('%-52s %s'%(f,'OK' if not agg else '%d зауважень'%len(agg)))
        for (b,c,_),g in agg.items():
            w=','.join(x for x in g['w'] if x!='—') or '—'
            print('    %-26s %-6s %-5s %s'%(w,b,c,g['t']))
    print('---- усього зауважень: %d у %d файлах'%(total,len(files)))
    return 1 if total else 0

if __name__=='__main__': sys.exit(main())
