#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Контрольні числа серії «Теоретична фізика. Ч. 1. Класична механіка».

Два незалежні джерела однієї й тієї самої величини:

  еталон  — numpy/scipy тут, у цьому файлі: власні формули, власні
            інтегратори, жодного рядка з коду сторінки. Де можна, еталон
            рахується ІНШИМ способом, ніж сторінка: там, де сторінка бере
            замкнену формулу, еталон інтегрує, і навпаки;
  сторінка — те, що показано студентові, прочитане з живого документа через
            CDP при вимкненому requestAnimationFrame і сталому кроці часу.

Збіг цих двох чисел і є перевіркою. Допуск указано біля кожного рядка; де
допуску немає, числа мають збігтися до останнього показаного знака.

  python3 tools/tm-checks.py 00a
"""
import sys, os, math, time

# Еталон рахується на numpy/scipy. На цій машині типовий python3 — свіжий
# homebrew без них, а потрібні пакети стоять під /usr/bin/python3. Щоб
# документована команда «python3 tools/tm-checks.py 00a» працювала, скрипт
# один раз перезапускає сам себе під тим інтерпретатором, де numpy є.
def _need_numpy():
    try:
        import numpy  # noqa: F401
        return
    except ImportError:
        pass
    for alt in ('/usr/bin/python3', '/Library/Developer/CommandLineTools/usr/bin/python3'):
        if not os.path.exists(alt) or os.path.realpath(alt) == os.path.realpath(sys.executable):
            continue
        if os.system('%s -c "import numpy, scipy" 2>/dev/null' % alt) == 0:
            os.execv(alt, [alt, os.path.abspath(__file__)] + sys.argv[1:])
    sys.exit('потрібні numpy і scipy: python3 -m pip install --user numpy scipy')

_need_numpy()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEGP = math.pi/180
G = 9.81

ROWS = []
def chk(name, ref, got, tol=None, unit=''):
    ok = (abs(ref-got) <= tol) if tol is not None else (abs(ref-got) <= 5e-4*max(1, abs(ref)))
    ROWS.append((name, ref, got, unit, ok))

def note(name, ref, got, ok, unit=''):
    ROWS.append((name, ref, got, unit, ok))

def report():
    w = max(len(r[0]) for r in ROWS)
    bad = 0
    print('%-*s %16s %16s  %s' % (w, 'що', 'очікувано', 'на сторінці', 'вердикт'))
    for name, ref, got, unit, ok in ROWS:
        f = lambda v: ('%.6g' % v) if (v == 0 or abs(v) >= 1e-4) else ('%.3e' % v)
        print('%-*s %16s %16s  %s' % (w, name, f(ref)+' '+unit, f(got)+' '+unit,
                                      'збігається' if ok else 'РОЗБІЖНІСТЬ'))
        bad += 0 if ok else 1
    print('---- розбіжностей:', bad)
    sys.exit(1 if bad else 0)

def num(p, expr):
    """CDP не серіалізує −0, NaN і Infinity як значення, тож читаємо рядком."""
    v = p.js('String(%s)' % expr)
    return float(v)

def page(rel, wait=2.4):
    """Живий документ із вимкненим rAF: час рухає тільки перевірка."""
    from cdp import Page
    p = Page(); p.metrics(1440, 1000, dpr=1)
    p.goto('file://' + os.path.join(ROOT, rel), wait)
    p.js("window.requestAnimationFrame=function(){return 0;};")
    return p

# ======================================================= 00a ==============
def ref_00a():
    out = {}
    m1 = m2 = 1.0; l1 = l2 = 1.0

    # --- вкладка 1 ---
    # узагальнені сили — з означення Q = −∂U/∂q, похідна чисельна
    U = lambda t1, t2: -(m1+m2)*G*l1*math.cos(t1) - m2*G*l2*math.cos(t2)
    t1, t2, d = math.radians(30), 0.0, 1e-6
    out['Q1'] = -(U(t1+d, t2)-U(t1-d, t2))/(2*d)
    out['Q2'] = -(U(t1, t2+d)-U(t1, t2-d))/(2*d)
    # кінетична енергія: еталон будує декартові швидкості чисельним
    # диференціюванням самого відображення кутів у координати
    def cart(t1, t2):
        return np.array([l1*math.sin(t1), -l1*math.cos(t1),
                         l1*math.sin(t1)+l2*math.sin(t2), -l1*math.cos(t1)-l2*math.cos(t2)])
    def T_num(t1, t2, w1, w2, h=1e-5):
        v = (cart(t1+w1*h, t2+w2*h) - cart(t1-w1*h, t2-w2*h))/(2*h)
        return 0.5*m1*(v[0]**2+v[1]**2) + 0.5*m2*(v[2]**2+v[3]**2)
    out['T'] = T_num(0.7, -0.4, 1.3, -0.7)

    # --- вкладка 2 ---
    R, m = 0.2, 0.01
    out['wc'] = math.sqrt(G/R)
    w = 10.0
    Ueff = lambda t: -0.5*m*R*R*w*w*math.sin(t)**2 - m*G*R*math.cos(t)
    # рівновагу шукаємо коренем похідної, а не формулою arccos
    dU = lambda t: (Ueff(t+1e-7)-Ueff(t-1e-7))/2e-7
    out['th0'] = math.degrees(brentq(dU, 0.2, math.pi/2-1e-6))
    # частоту — з другої похідної U_eff, а не з ω·sin θ₀
    t0 = math.radians(out['th0']); e = 1e-4
    d2 = (Ueff(t0+e) - 2*Ueff(t0) + Ueff(t0-e))/(e*e)
    out['fr'] = math.sqrt(d2/(m*R*R))

    # --- вкладка 3: сторінка бере аналітику, еталон інтегрує ---
    mr, wr, r0, tt = 0.1, 2.0, 0.1, 1.0
    sol = solve_ivp(lambda t, y: [y[1], wr*wr*y[0]], [0, tt], [r0, 0.0],
                    method='DOP853', rtol=1e-12, atol=1e-14, dense_output=True)
    r, rd = sol.sol(tt)
    out['r'] = float(r)
    out['N'] = float(2*mr*wr*rd)
    out['E'] = float(0.5*mr*(rd*rd + wr*wr*r*r))
    out['E0'] = 0.5*mr*wr*wr*r0*r0
    ts = np.linspace(0, tt, 400)
    hh = 0.5*mr*(sol.sol(ts)[1]**2 - wr*wr*sol.sol(ts)[0]**2)
    out['h'] = float(hh[-1])
    out['hdrift'] = float(np.max(np.abs(hh - hh[0])))

    # --- вкладка 4: сторінка складає чотири кроки, еталон інтегрує в’язь ---
    eps, dl = 0.2, 0.3
    def leg(state, v, om, T):
        s = solve_ivp(lambda t, y: [v*math.cos(y[2]), v*math.sin(y[2]), om],
                      [0, T], state, method='DOP853', rtol=1e-12, atol=1e-14)
        return [float(s.y[0][-1]), float(s.y[1][-1]), float(s.y[2][-1])]
    st = [0.0, 0.0, 0.0]
    st = leg(st,  eps, 0.0, 1.0)      # уперед ε
    st = leg(st,  0.0, dl,  1.0)      # поворот δ
    st = leg(st, -eps, 0.0, 1.0)      # назад ε
    st = leg(st,  0.0, -dl, 1.0)      # поворот −δ
    out['dx'], out['dy'], out['dphi'] = st
    return out

def page_00a():
    p = page('Theoretical-Mechanics/00a-coordinates-constraints.html')
    o = {}
    o['Q1'] = p.js("(function(){activate('m1');M1.sys='two';M1.th1=30*DEG;M1.th2=0;"
                   "M1.render();return M1.Q1();})()")
    o['Q2'] = num(p, "M1.Q2()")
    o['dof'] = int(num(p, "M1.dof()"))
    o['T'] = p.js("(function(){M1.th1=0.7;M1.th2=-0.4;M1.w1=1.3;M1.w2=-0.7;"
                  "return M1.Tgen();})()")
    o['dT'] = num(p, "Math.abs(M1.Tgen()-M1.Tcart())")
    o['wc'] = num(p, "(function(){activate('m2');M2.w=10;M2.render();return M2.wc();})()")
    o['th0'] = num(p, "M2.th0()/DEG")
    o['fr'] = num(p, "M2.fr()")
    o['hconst'] = num(p, """(function(){M2.th=0.6;M2.wd=0;M2.t=0;
      const h0=M2.h(); let d=0;
      for(let k=0;k<40000;k++){const r=verlet(M2.th,M2.wd,2e-4,x=>M2.acc(x));
        M2.th=r[0];M2.wd=r[1]; d=Math.max(d,Math.abs(M2.h()-h0));}
      return d;})()""")
    o['r'] = p.js("(function(){activate('m3');M3.r0=0.1;M3.w=2;M3.t=1;M3.render();"
                  "return M3.r();})()")
    o['N'] = num(p, "M3.N()")
    o['E'] = num(p, "M3.E()")
    o['E0'] = num(p, "M3.E0()")
    o['h'] = num(p, "M3.h()")
    o['hdrift'] = num(p, """(function(){let d=0;const h0=-0.5*M3.m*M3.w*M3.w*M3.r0*M3.r0;
      for(let i=0;i<=400;i++){M3.t=M3.tMax()*i/400; d=Math.max(d,Math.abs(M3.h()-h0));}
      M3.t=1; return d;})()""")
    o['Nvirt'] = num(p, """(function(){M3.t=0.7;
      /* N уздовж поперечної осі, δr уздовж стрижня: скалярний добуток точно нуль */
      const a=M3.phi(), N=[-Math.sin(a)*M3.N(),Math.cos(a)*M3.N()], d=[Math.cos(a),Math.sin(a)];
      return Math.abs(N[0]*d[0]+N[1]*d[1]);})()""")
    o['dx'] = p.js("(function(){activate('m4');M4.eps=0.2;M4.del=0.3;M4.render();"
                   "return M4.pose(4)[0];})()")
    o['dy'] = num(p, "M4.pose(4)[1]")
    o['dphi'] = num(p, "M4.pose(4)[2]")
    p.close()
    return o

def main_00a():
    r, g = ref_00a(), page_00a()
    chk('м1 · Q₁ = −∂U/∂θ₁ при θ₁ = 30°, θ₂ = 0', r['Q1'], g['Q1'], 1e-6, 'Н·м')
    chk('м1 · Q₂ при θ₂ = 0', r['Q2'], g['Q2'], 1e-9, 'Н·м')
    note('м1 · ступенів вільності N = 2n − k', 2, g['dof'], g['dof'] == 2)
    chk('м1 · T в узагальнених проти чисельних декартових', r['T'], g['T'], 1e-7, 'Дж')
    note('м1 · T узагальнена = T декартова на сторінці', 0.0, g['dT'],
         g['dT'] < 1e-12, 'Дж')
    chk('м2 · поріг ω_c = √(g/R)', r['wc'], g['wc'], 1e-9, 'рад/с')
    chk('м2 · рівновага θ₀ (корінь U′_еф) при ω = 10', r['th0'], g['th0'], 1e-4, '°')
    chk('м2 · частота малих коливань (з U″_еф)', r['fr'], g['fr'], 1e-4, 'рад/с')
    note('м2 · дрейф інтеграла Якобі за 8 с Верле', 0.0, g['hconst'], g['hconst'] < 1e-6, 'Дж')
    chk('м3 · r при ω = 2, r₀ = 0,1, t = 1 (DOP853)', r['r'], g['r'], 1e-9, 'м')
    chk('м3 · реакція N = 2mωṙ', r['N'], g['N'], 1e-9, 'Н')
    chk('м3 · енергія E у ЛСВ', r['E'], g['E'], 1e-11, 'Дж')
    chk('м3 · E₀ на старті', r['E0'], g['E0'], 1e-12, 'Дж')
    chk('м3 · інтеграл Якобі h', r['h'], g['h'], 1e-10, 'Дж')
    note('м3 · дрейф h за весь прогін', 0.0, g['hdrift'], g['hdrift'] < 1e-8, 'Дж')
    note('м3 · віртуальна робота реакції N·δr', 0.0, g['Nvirt'], g['Nvirt'] < 1e-12, 'Дж')
    chk('м4 · зсув за цикл уздовж x (в’язь, DOP853)', r['dx'], g['dx'], 1e-9, 'м')
    chk('м4 · зсув за цикл уздовж y', r['dy'], g['dy'], 1e-9, 'м')
    note('м4 · кут після циклу повертається до нуля', 0.0, g['dphi'],
         abs(g['dphi']) < 1e-12, 'рад')

# ======================================================= 00b ==============
def ref_00b():
    from scipy.integrate import quad, solve_ivp
    from scipy.optimize import brentq
    out = {}
    m = 1.0

    # --- вкладка 1: дія на справжній траєкторії береться квадратурою,
    #     а не замкненою формулою, яку показує сторінка
    T = 2.0
    x = lambda t: 0.5*G*t*(T-t)
    v = lambda t: 0.5*G*(T-2*t)
    out['S0'] = quad(lambda t: 0.5*m*v(t)**2 - m*G*x(t), 0, T, limit=200)[0]
    #     коефіцієнт при ε² — із другої різниці самої дії
    def S_eps(e, w=0.0):
        f  = lambda t: x(t) + e*math.sin(math.pi*t/T)
        fd = lambda t: v(t) + e*math.pi/T*math.cos(math.pi*t/T)
        U  = (lambda q: m*G*q) if w == 0 else (lambda q: 0.5*m*w*w*q*q)
        return quad(lambda t: 0.5*m*fd(t)**2 - U(f(t)), 0, T, limit=200)[0]
    h = 1e-3
    out['c2'] = (S_eps(h) - 2*S_eps(0.0) + S_eps(-h))/(h*h)/2
    #     зміна знака коефіцієнта для осцилятора: корінь, а не формула π/ω
    co = lambda TT: m*TT/4*(math.pi**2/TT**2 - 4.0)
    out['Tsign'] = brentq(co, 0.5, 4.0)

    # --- вкладка 2: брахістохрона
    k = 2.0/1.0
    thB = brentq(lambda th: (th-math.sin(th)) - k*(1-math.cos(th)), 0.5, 2*math.pi-1e-9)
    a = 1.0/(1-math.cos(thB))
    out['thB'], out['a'] = thB, a
    out['tcyc'] = math.sqrt(a/G)*thB
    L = math.hypot(2.0, 1.0)
    out['tline'] = math.sqrt(2*L/(G*(1.0/L)))

    # --- вкладка 3: різниця дій
    V, dx, T3 = 1.0, 2.0, 2.0
    out['dS'] = m*V*dx + 0.5*m*V*V*T3

    # --- вкладка 4: лійка і поле B
    r0 = 0.2
    out['vcirc'] = math.sqrt(G*r0)               # v² = gr·ctg 45°
    out['wcirc'] = out['vcirc']/r0
    out['w_half'] = out['wcirc']*4               # φ̇ ∝ 1/r²
    #     поле B: інтегруємо рівняння руху й дивимося на канонічний імпульс
    sol = solve_ivp(lambda t, y: [y[2], y[3], y[3], -y[2]], [0, 12.0],
                    [1.5, 0.0, 0.0, -1.0], method='DOP853',
                    rtol=1e-12, atol=1e-14, dense_output=True)
    ts = np.linspace(0, 12.0, 2000)
    Y = sol.sol(ts)
    Lz = Y[0]*Y[3] - Y[1]*Y[2]
    r2 = Y[0]**2 + Y[1]**2
    pc = Lz + 0.5*r2
    out['pcan'] = float(pc[0])
    out['pdrift'] = float(np.max(np.abs(pc - pc[0])))
    out['Lzspan'] = float(np.max(Lz) - np.min(Lz))

    # --- вкладка 5: подібність
    out['sim'] = {kk: 2.0**(1 - kk/2) for kk in (2, 1, -1)}
    return out

def page_00b():
    p = page('Theoretical-Mechanics/00b-least-action-symmetries.html', 2.6)
    o = {}
    o['S0'] = num(p, "(function(){activate('m1');M1.sys='grav';M1.T=2;M1.eps=0;"
                     "M1.nodes=[0,0,0,0,0];M1.render();return M1.S0();})()")
    o['Squad'] = num(p, "M1.S()")
    o['c2'] = num(p, "M1.c2()")
    o['Tsign'] = num(p, "(function(){M1.sys='osc';M1.w=2;return Math.PI/M1.w;})()")
    o['thB'] = num(p, "(function(){activate('m2');M2.bx=2;M2.by=1;M2.render();"
                      "return M2.thB();})()")
    o['a'] = num(p, "M2.aCyc()")
    o['tcyc'] = num(p, "M2.time('cyc')")
    o['tline'] = num(p, "M2.time('line')")
    o['dS'] = num(p, "(function(){activate('m3');M3.V=1;M3.eps=0;M3.render();"
                     "return M3.S2()-M3.S();})()")
    o['dS_e'] = num(p, "(function(){M3.eps=0.8;return M3.S2()-M3.S();})()")
    o['dSth'] = num(p, "M3.dTheory()")
    o['vcirc'] = num(p, "(function(){activate('m4');M4.sys='funnel';M4.reset();"
                        "M4.render();return M4.v0;})()")
    o['wcirc'] = num(p, "M4.wphi()")
    o['w_half'] = num(p, "M4.p0/(M4.m*0.1*0.1)")
    o['pdrift'] = num(p, """(function(){M4.sys='funnel';M4.reset();M4.r=0.3;
      M4.p0=M4.m*0.3*1.2;M4.rd=0;const p0=M4.pphi();let d=0;
      for(let i=0;i<60000;i++){const r=verlet(M4.r,M4.rd,2e-4,x=>M4.accR(x));
        M4.r=r[0];M4.rd=r[1]; d=Math.max(d,Math.abs(M4.pphi()-p0));}
      return d;})()""")
    o['pcan'] = num(p, "(function(){M4.sys='mag';M4.reset();return M4.pcan();})()")
    o['pcanDrift'] = num(p, """(function(){M4.sys='mag';M4.reset();const p0=M4.pcan();
      let d=0,s=[M4.bx,M4.by,M4.bvx,M4.bvy],t=0;
      for(let i=0;i<60000;i++){s=rk4(t,s,2e-4,(tt,y)=>[y[2],y[3],y[3],-y[2]]);t+=2e-4;
        M4.bx=s[0];M4.by=s[1];M4.bvx=s[2];M4.bvy=s[3];
        d=Math.max(d,Math.abs(M4.pcan()-p0));}
      return d;})()""")
    o['LzSpan'] = num(p, """(function(){M4.sys='mag';M4.reset();
      let lo=1e9,hi=-1e9,s=[M4.bx,M4.by,M4.bvx,M4.bvy],t=0;
      for(let i=0;i<60000;i++){s=rk4(t,s,2e-4,(tt,y)=>[y[2],y[3],y[3],-y[2]]);t+=2e-4;
        M4.bx=s[0];M4.by=s[1];M4.bvx=s[2];M4.bvy=s[3];
        const L=M4.Lz(); if(L<lo)lo=L; if(L>hi)hi=L;}
      return hi-lo;})()""")
    o['sim'] = {}
    for kk in (2, 1, -1):
        o['sim'][kk] = num(p, """(function(){activate('m5');M5.k=%d;M5.lam=2;M5.reset();
          const h=2e-4;
          while((!M5.A.per||!M5.B.per)&&M5.t<400){M5.step(M5.A,h);M5.step(M5.B,h);M5.t+=h;}
          return M5.B.per/M5.A.per;})()""" % kk)
    o['vir'] = num(p, """(function(){activate('m5');M5.k=2;M5.lam=2;M5.reset();
      const h=2e-4;
      while(M5.t<20*2*Math.PI){M5.step(M5.A,h);M5.step(M5.B,h);
        const v=Math.hypot(M5.A.v[0],M5.A.v[1]);
        M5.sumT+=0.5*v*v*h; M5.sumU+=M5.Upot(M5.A.p)*h; M5.nAvg+=h; M5.t+=h;}
      return M5.virRes();})()""")
    p.close()
    return o

def main_00b():
    r, g = ref_00b(), page_00b()
    chk('м1 · S₀ = −mg²T³/24 проти квадратури', r['S0'], g['S0'], 1e-6, 'Дж·с')
    chk('м1 · та сама дія, порахована сторінкою по кривій', r['S0'], g['Squad'], 1e-4, 'Дж·с')
    chk('м1 · коефіцієнт при ε² (друга різниця)', r['c2'], g['c2'], 1e-5, 'Дж·с/м²')
    chk('м1 · зміна знака коефіцієнта при ω = 2', r['Tsign'], g['Tsign'], 1e-6, 'с')
    chk('м2 · параметр циклоїди θ_B', r['thB'], g['thB'], 1e-6, 'рад')
    chk('м2 · параметр циклоїди a', r['a'], g['a'], 1e-6, 'м')
    chk('м2 · час спуску циклоїдою (аналітика проти квадратури)',
        r['tcyc'], g['tcyc'], 1e-3, 'с')
    chk('м2 · час спуску прямою', r['tline'], g['tline'], 1e-3, 'с')
    note('м2 · циклоїда швидша за пряму', 1.0, g['tline']/g['tcyc'],
         g['tcyc'] < g['tline'], 'раза')
    chk('м3 · S′ − S при ε = 0', r['dS'], g['dS'], 1e-9, 'Дж·с')
    chk('м3 · те саме при ε = 0,8 — не залежить від форми', r['dS'], g['dS_e'], 1e-9, 'Дж·с')
    chk('м3 · формула mVΔx + ½mV²T на сторінці', r['dS'], g['dSth'], 1e-12, 'Дж·с')
    chk('м4 · колова орбіта лійки: v = √(gr) при r = 0,2', r['vcirc'], g['vcirc'], 1e-6, 'м/с')
    chk('м4 · та сама орбіта: φ̇', r['wcirc'], g['wcirc'], 1e-6, 'рад/с')
    chk('м4 · φ̇ при вдвічі меншому r — учетверо більша', r['w_half'], g['w_half'], 1e-6, 'рад/с')
    note('м4 · дрейф p_φ у лійці за 12 с', 0.0, g['pdrift'], g['pdrift'] < 1e-8)
    chk('м4 · поле B: p_φ = ½qB(d² − R²) при d = 0,5, R = 1',
        r['pcan'], g['pcan'], 1e-9, '')
    note('м4 · поле B: дрейф канонічного p_φ за 12 с', 0.0, g['pcanDrift'],
         g['pcanDrift'] < 1e-9)
    note('м4 · поле B: механічний mr²φ̇ НЕ сталий — розмах',
         r['Lzspan'], g['LzSpan'],
         abs(g['LzSpan']-r['Lzspan']) < 1e-3 and g['LzSpan'] > 0.5)
    for kk in (2, 1, -1):
        chk('м5 · t′/t при λ = 2, k = %d' % kk, r['sim'][kk], g['sim'][kk], 2e-3)
    note('м5 · нев’язка віріалу за 20 обходів, k = 2', 0.0, g['vir'], g['vir'] < 1.0, '%')


# ======================================================= 03 ===============
def ref_03():
    """Еталон для вкладок 03. Скрізь, де сторінка бере замкнену формулу,
    еталон інтегрує рівняння руху, і навпаки."""
    out = {}

    # --- вкладка 1: період точного маятника вимірюємо прогоном, а не K(k) ---
    l = 1.0
    def period(th0):
        f = lambda t, y: [y[1], -G/l*math.sin(y[0])]
        ev = lambda t, y: y[1]            # повернення швидкості до нуля
        ev.direction = 1; ev.terminal = False
        s = solve_ivp(f, [1e-9, 20], [th0, 0.0], method='DOP853',
                      rtol=1e-12, atol=1e-14, events=ev)
        # перша подія ẏ = 0 з додатним напрямом — це півперіод
        return 2*float(s.t_events[0][0])
    out['T0'] = period(1e-4)
    out['T30'] = period(math.radians(30))
    out['T90'] = period(math.radians(90))

    # --- вкладка 2: биття й нахил на резонансі — із чисельного розв'язку ---
    w0, fm = 2*math.pi, 1.0
    def forced(gam, tend, n=40001):
        f = lambda t, y: [y[1], -w0*w0*y[0] + fm*math.cos(gam*t)]
        tt = np.linspace(0, tend, n)
        s = solve_ivp(f, [0, tend], [0.0, 0.0], method='DOP853',
                      rtol=1e-12, atol=1e-14, t_eval=tt)
        return tt, s.y[0]
    tt, x = forced(0.9*w0, 20.0)
    # нуль огинаючої — мить, коли сама величина обертається на нуль разом
    # з усіма сусідніми піками; шукаємо її як мінімум |x| у вікні [5; 15] с
    sel = (tt > 5) & (tt < 15)
    out['Tbeat'] = float(tt[sel][int(np.argmin(np.abs(x[sel])))])
    tt, x = forced(w0, 12.0)
    pk = [(tt[i], abs(x[i])) for i in range(1, len(x)-1)
          if abs(x[i]) > abs(x[i-1]) and abs(x[i]) > abs(x[i+1])]
    pk = [q for q in pk if q[1] > 1e-3]
    out['slope'] = np.polyfit([q[0] for q in pk], [q[1] for q in pk], 1)[0]

    # --- вкладка 3: частоти мод із власних чисел матриці, биття з прогону ---
    l3, m3, k3 = 0.5, 0.2, 0.5
    M = np.array([[G/l3 + k3/m3, -k3/m3], [-k3/m3, G/l3 + k3/m3]])
    ev = np.sqrt(np.sort(np.linalg.eigvalsh(M)))
    out['w1'], out['w2'] = float(ev[0]), float(ev[1])
    f3 = lambda t, y: [y[2], y[3],
                       -(G/l3)*y[0] - (k3/m3)*(y[0]-y[1]),
                       -(G/l3)*y[1] - (k3/m3)*(y[1]-y[0])]
    s = solve_ivp(f3, [0, 20], [0.06, 0.0, 0.0, 0.0], method='DOP853',
                  rtol=1e-12, atol=1e-14, t_eval=np.linspace(0, 20, 40001))
    # Лівий маятник завмирає тоді, коли дві нормальні координати стають у
    # протифазі: x₁ = (Q₁ + Q₂)/2. Фазу кожної беремо з інтегрованої
    # траєкторії, а не з формули π/Δω, — це й робить еталон незалежним.
    Q1 = s.y[0]+s.y[1]; Q2 = s.y[0]-s.y[1]
    Q1d = s.y[2]+s.y[3]; Q2d = s.y[2]-s.y[3]
    ph1 = np.unwrap(np.arctan2(-Q1d/out['w1'], Q1))
    ph2 = np.unwrap(np.arctan2(-Q2d/out['w2'], Q2))
    out['Ttrans'] = float(np.interp(math.pi, ph2-ph1, s.t))

    # --- вкладка 4: складки — зі зміни кількості додатних коренів кубіки ---
    w0n, beta, lam, f4 = 1.0, 0.5, 0.05, 0.1
    kap = 3*beta/(8*w0n); R = f4*f4/(4*w0n*w0n)
    out['kap'] = kap
    out['bmax'] = f4/(2*w0n*lam)
    out['gpeak'] = w0n + kap*out['bmax']**2
    def nroots(eps):
        c = [kap*kap, -2*kap*eps, eps*eps+lam*lam, -R]
        rr = np.roots(c)
        return sum(1 for z in rr if abs(z.imag) < 1e-9 and z.real > 0)
    es = np.linspace(0.05, 0.30, 25001)
    cnt = np.array([nroots(e) for e in es])
    idx = np.where(np.diff(cnt) != 0)[0]
    out['g1'] = w0n + float(es[idx[0]])
    out['g2'] = w0n + float(es[idx[-1]+1])

    # --- вкладка 5, Капіца: частоти з другої похідної U_eff чисельно ---
    l5, a5, O5 = 0.2, 0.01, 300.0
    out['Oc'] = brentq(lambda O: a5*a5*O*O - 2*G*l5, 1.0, 1e4)
    U = lambda f: -G*l5*math.cos(f) + a5*a5*O5*O5/4*math.sin(f)**2
    e = 1e-5
    d2top = (U(math.pi+e) - 2*U(math.pi) + U(math.pi-e))/(e*e)
    d2bot = (U(e) - 2*U(0) + U(-e))/(e*e)
    out['wtop'] = math.sqrt(d2top)/l5
    out['wbot'] = math.sqrt(d2bot)/l5
    # повна модель: повільне коливання біля вершини, тремтіння прибране
    # ковзним середнім по періоду вібрації
    h = 2e-5; n = int(2.4/h)
    f5 = lambda t, y: [y[1], -(G - a5*O5*O5*math.cos(O5*t))/l5*math.sin(y[0])]
    s = solve_ivp(f5, [0, 2.4], [math.pi+0.15, 0.0], method='DOP853',
                  rtol=1e-11, atol=1e-13, t_eval=np.linspace(0, 2.4, n))
    d = s.y[0] - math.pi
    w = max(3, int(2*math.pi/O5/h))
    sm = np.convolve(d, np.ones(w)/w, mode='same')[w:-w]
    ts = s.t[w:-w]
    zc = [i for i in range(1, len(sm)) if sm[i-1] > 0 >= sm[i]]
    # дві сусідні однонапрямлені нулі — це повний період повільного руху
    out['wtop_full'] = 2*math.pi/(ts[zc[1]]-ts[zc[0]]) if len(zc) > 1 else float('nan')

    # --- вкладка 5, параметричний: інкремент із прогону рівняння Матьє ---
    w0p, hmod = 2*math.pi, 0.1
    fm2 = lambda t, y, gam: [y[1], -w0p*w0p*(1+hmod*math.cos(gam*t))*y[0]]
    s = solve_ivp(lambda t, y: fm2(t, y, 2*w0p), [0, 30], [0.08, 0.0],
                  method='DOP853', rtol=1e-12, atol=1e-14,
                  t_eval=np.linspace(0, 30, 60001))
    a = np.abs(s.y[0]); tt = s.t
    pk = [(tt[i], a[i]) for i in range(1, len(a)-1)
          if a[i] > a[i-1] and a[i] > a[i+1] and tt[i] > 4]
    out['incr'] = float(np.polyfit([q[0] for q in pk],
                                   [math.log(q[1]) for q in pk], 1)[0])
    out['halfw'] = hmod*w0p/2
    return out


def page_03():
    p = page('Theoretical-Mechanics/03-oscillations.html', 2.6)
    o = {}
    o['T0'] = num(p, "(function(){activate('m1');M1.th0=30*DEG;M1.reset();"
                     "M1.render();return M1.T0();})()")
    o['T30'] = num(p, "M1.T()")
    o['r30'] = num(p, "M1.ratio(30*DEG)")
    o['r90'] = num(p, "M1.ratio(90*DEG)")
    o['T90'] = num(p, "M1.T0()*M1.ratio(90*DEG)")
    # дрейф енергії точного маятника за 100 періодів його власним інтегратором
    o['dE1'] = num(p, """(function(){M1.th0=30*DEG;M1.reset();
      const h=1e-4,n=Math.round(100*M1.T()/h),E0=M1.En(M1.ex);let d=0;
      for(let i=0;i<n;i++){const r=verlet(M1.ex.th,M1.ex.w,h,x=>-G/M1.l*Math.sin(x));
        M1.ex.th=r[0];M1.ex.w=r[1];
        if(i%97===0) d=Math.max(d,Math.abs(M1.En(M1.ex)-E0));}
      return d/E0;})()""")
    o['Tbeat'] = num(p, "(function(){activate('m2');M2.r=0.9;M2.reset();"
                        "M2.render();return M2.Tb();})()")
    o['A2'] = num(p, "M2.A()")
    o['slope'] = num(p, "M2.slope()")
    o['w1'] = num(p, "(function(){activate('m3');M3.k=0.5;M3.x1=0.06;M3.x2=0;"
                     "M3.reset();M3.render();return M3.w1();})()")
    o['w2'] = num(p, "M3.w2()")
    o['Tbeat3'] = num(p, "M3.Tbeat()")
    o['Ttrans'] = num(p, "M3.Ttrans()")
    o['dE3'] = num(p, """(function(){M3.reset();
      const h=1e-4,n=Math.round(100*2*Math.PI/M3.w1()/h),E0=M3.E1()+M3.E2();let d=0;
      for(let i=0;i<n;i++){const s=M3.s,a0=M3.acc(s.a,s.b);
        const na=s.a+s.va*h+0.5*a0[0]*h*h, nb=s.b+s.vb*h+0.5*a0[1]*h*h;
        const a1=M3.acc(na,nb);
        s.va+=0.5*(a0[0]+a1[0])*h; s.vb+=0.5*(a0[1]+a1[1])*h; s.a=na; s.b=nb;
        if(i%97===0) d=Math.max(d,Math.abs(M3.E1()+M3.E2()-E0));}
      return d/E0;})()""")
    o['kap'] = num(p, "(function(){activate('m4');M4.reset();M4.render();return M4.kap();})()")
    o['bmax'] = num(p, "M4.bMax()")
    o['gpeak'] = num(p, "M4.w0+M4.kap()*M4.bMax()*M4.bMax()")
    o['g1'] = num(p, "M4.w0+M4.folds().e1")
    o['g2'] = num(p, "M4.w0+M4.folds().e2")
    o['Oc'] = num(p, "(function(){activate('m5');M5.mode='kap';M5.a=0.01;M5.O=300;"
                     "M5.reset();M5.render();return M5.Oc();})()")
    o['wtop'] = num(p, "M5.wTop()")
    o['wbot'] = num(p, "M5.wBot()")
    o['halfw'] = num(p, "(function(){M5.mode='par';M5.h=0.1;M5.r=2;M5.reset();"
                        "return M5.halfW();})()")
    o['incr'] = num(p, "M5.h*M5.w0()/4")
    p.close()
    return o


def main_03():
    r, g = ref_03(), page_03()
    chk('м1 · T₀ = 2π√(l/g) проти прогону при θ₀ → 0', r['T0'], g['T0'], 1e-4, 'с')
    chk('м1 · T при θ₀ = 30° (K(k) проти прогону)', r['T30'], g['T30'], 1e-4, 'с')
    chk('м1 · T при θ₀ = 90°', r['T90'], g['T90'], 1e-4, 'с')
    chk('м1 · T/T₀ при 30°', r['T30']/r['T0'], g['r30'], 1e-4)
    chk('м1 · T/T₀ при 90°', r['T90']/r['T0'], g['r90'], 1e-4)
    note('м1 · дрейф E за 100 періодів', 0.0, g['dE1'], g['dE1'] < 1e-6)
    chk('м2 · період биття при γ = 0,9ω₀', r['Tbeat'], g['Tbeat'], 3e-3, 'с')
    chk('м2 · нахил огинаючої на резонансі', r['slope'], g['slope'], 1e-3, 'м/с')
    chk('м3 · ω₁ (власні числа проти √(g/l))', r['w1'], g['w1'], 1e-9, 'рад/с')
    chk('м3 · ω₂ (власні числа проти √(g/l + 2k/m))', r['w2'], g['w2'], 1e-9, 'рад/с')
    chk('м3 · період биття 2π/(ω₂ − ω₁)',
        2*math.pi/(r['w2']-r['w1']), g['Tbeat3'], 1e-6, 'с')
    chk('м3 · повна передача енергії (прогін проти π/Δω)',
        r['Ttrans'], g['Ttrans'], 3e-3, 'с')
    note('м3 · дрейф E₁ + E₂ за 100 періодів', 0.0, g['dE3'], g['dE3'] < 1e-6)
    chk('м4 · κ = 3β/8ω₀', r['kap'], g['kap'], 1e-12)
    chk('м4 · b_max = f/2ω₀λ', r['bmax'], g['bmax'], 1e-12)
    chk('м4 · частота вершини хребта', r['gpeak'], g['gpeak'], 1e-12)
    chk('м4 · ліва складка (кубіка проти dε/db)', r['g1'], g['g1'], 1e-3)
    chk('м4 · права складка', r['g2'], g['g2'], 1e-3)
    chk('м5 · поріг Капіци Ω_c = √(2gl)/a', r['Oc'], g['Oc'], 1e-6, 'рад/с')
    # друга похідна тут чисельна, тож допуск — її власна похибка, не нуль
    chk('м5 · частота біля вершини (друга похідна U_eff)',
        r['wtop'], g['wtop'], 1e-3, 'рад/с')
    chk('м5 · частота біля низу', r['wbot'], g['wbot'], 1e-3, 'рад/с')
    note('м5 · повна модель проти ефективної біля вершини',
         r['wtop'], r['wtop_full'],
         abs(r['wtop_full']-r['wtop'])/r['wtop'] < 0.03, 'рад/с')
    chk('м5 · півширина язика hω₀/2', r['halfw'], g['halfw'], 1e-9, 'рад/с')
    chk('м5 · інкремент у центрі зони (прогін Матьє проти hω₀/4)',
        r['incr'], g['incr'], 5e-3, 'с⁻¹')


# ======================================================= 04 ===============
def ref_04():
    """Еталон для вкладок 04: власні числа numpy, прогін рівнянь Ейлера,
    прогін рівнянь вовчка й прогін рівнянь Коріоліса — скрізь іншим
    маршрутом, ніж замкнені формули сторінки."""
    out = {}

    # --- вкладка 1: тензор прямокутника 2×1, 4 маси по 1 кг ---
    pts = [(-1, -0.5), (1, -0.5), (1, 0.5), (-1, 0.5)]
    Ixx = sum(1.0*y*y for _, y in pts)
    Iyy = sum(1.0*x*x for x, _ in pts)
    Ixy = -sum(1.0*x*y for x, y in pts)
    A = np.array([[Ixx, Ixy], [Ixy, Iyy]])
    ev, evec = np.linalg.eigh(A)
    out['Ixx'], out['Iyy'], out['Izz'] = Ixx, Iyy, Ixx+Iyy
    out['I1'], out['I2'] = float(ev[0]), float(ev[1])
    out['psi'] = math.degrees(math.atan2(evec[1, 0], evec[0, 0])) % 180

    # --- вкладка 2: комутатор двох поворотів ---
    def R(axis, a):
        c, s = math.cos(a), math.sin(a)
        if axis == 'x': return np.array([[1,0,0],[0,c,-s],[0,s,c]])
        return np.array([[c,0,s],[0,1,0],[-s,0,c]])
    def gap(t):
        C = R('y',t)@R('x',t)@np.linalg.inv(R('x',t)@R('y',t))
        return math.acos(max(-1, min(1, (np.trace(C)-1)/2)))
    out['gap90'] = gap(math.pi/2)
    out['gap01'] = gap(0.1)
    out['det'] = float(np.linalg.det(R('y',math.pi/2)@R('x',math.pi/2)))

    # --- вкладка 3: брусок, рівняння Ейлера ---
    m, a, b, c = 0.1, 0.10, 0.06, 0.02
    I = np.array([m*(b*b+c*c)/12, m*(a*a+c*c)/12, m*(a*a+b*b)/12])
    out['I'] = I.tolist()
    w = 10.0
    out['inc'] = w*math.sqrt((I[1]-I[0])*(I[2]-I[1])/(I[0]*I[2]))
    out['f1'] = w*math.sqrt((I[1]-I[0])*(I[2]-I[0])/(I[1]*I[2]))
    out['f3'] = w*math.sqrt((I[2]-I[0])*(I[2]-I[1])/(I[0]*I[1]))
    # інкремент незалежно: прогін із малим збуренням і нахил ln|ω₁| у часі
    def euler(t, y):
        return [(I[1]-I[2])*y[1]*y[2]/I[0],
                (I[2]-I[0])*y[2]*y[0]/I[1],
                (I[0]-I[1])*y[0]*y[1]/I[2]]
    # збурення беремо дуже малим, щоб лінійний режим тривав довше: на
    # хвості експоненти нахил уже псують нелінійні члени
    e = 1e-10*w
    s3 = solve_ivp(euler, [0, 3.0], [e, w, e], method='DOP853',
                   rtol=1e-13, atol=1e-22, t_eval=np.linspace(0, 3.0, 6001))
    la = np.log(np.abs(s3.y[0]))
    sel = (s3.t > 0.5) & (s3.t < 2.5)
    out['incNum'] = float(np.polyfit(s3.t[sel], la[sel], 1)[0])
    # частота навколо осі 1 — із того самого прогону, але іншого старту
    s1 = solve_ivp(euler, [0, 4.0], [w, e, e], method='DOP853',
                   rtol=1e-12, atol=1e-16, t_eval=np.linspace(0, 4.0, 8001))
    y = s1.y[1]
    zc = [s1.t[i] for i in range(1, len(y)) if y[i-1] < 0 <= y[i]]
    out['f1Num'] = 2*math.pi/(zc[1]-zc[0]) if len(zc) > 1 else float('nan')

    # --- вкладка 4: симетричний вовчок ---
    mt, lt, I1, I3, w3 = 0.1, 0.04, 8e-5, 4e-5, 200.0
    mgl = mt*G*lt
    out['Opr'] = mgl/(I3*w3)
    out['wcrit'] = math.sqrt(4*I1*mgl)/I3
    # точний корінь регулярної прецесії: φ̇(M₃ − I₁φ̇cos θ) = mgl
    th0 = math.radians(30)
    phreg = brentq(lambda p: p*(I3*w3 - I1*p*math.cos(th0)) - mgl, 0.1, 50)
    out['phreg'] = phreg
    # і прогін рівнянь вовчка з цим φ̇: θ мусить стояти
    M3 = I3*w3
    Mz = I1*phreg*math.sin(th0)**2 + M3*math.cos(th0)
    def top(t, y):
        th, thd = y
        s, cc = math.sin(th), math.cos(th)
        A2 = Mz - M3*cc
        return [thd, -A2*(M3 - Mz*cc)/(I1*I1*s**3) + mgl*s/I1]
    st = solve_ivp(top, [0, 2.0], [th0, 0.0], method='DOP853',
                   rtol=1e-12, atol=1e-14, t_eval=np.linspace(0, 2.0, 2001))
    out['thSpan'] = float(st.y[0].max() - st.y[0].min())
    phd = (Mz - M3*np.cos(st.y[0]))/(I1*np.sin(st.y[0])**2)
    out['phMean'] = float(phd.mean())

    # --- вкладка 5: маятник Фуко, прогін рівнянь Коріоліса ---
    OZ, ll = 7.292e-5, 10.0
    phi = math.radians(50.45)
    Oz = OZ*math.sin(phi)
    out['rate'] = Oz/math.pi*180*3600
    out['Tturn'] = 2*math.pi/Oz/3600
    out['Tpend'] = 2*math.pi*math.sqrt(ll/G)
    out['Tpole'] = 2*math.pi/OZ/3600
    w02 = G/ll
    def foucault(t, y):
        return [y[2], y[3], -w02*y[0] + 2*Oz*y[3], -w02*y[1] - 2*Oz*y[2]]
    T = 600.0
    sf = solve_ivp(foucault, [0, T], [1.0, 0.0, 0.0, 0.0], method='DOP853',
                   rtol=1e-12, atol=1e-14, t_eval=np.linspace(0, T, 60001))
    # кут площини беремо як напрям найбільшого розмаху: головна вісь
    # коваріаційної матриці траєкторії на останній сотні секунд
    sel = sf.t > T-100
    X = np.vstack([sf.y[0][sel], sf.y[1][sel]])
    C = X@X.T
    _, vv = np.linalg.eigh(C)
    ang = math.degrees(math.atan2(vv[1, 1], vv[0, 1]))
    ang = (ang + 90) % 180 - 90
    out['turnNum'] = -ang/((T-50)/3600)
    return out


def page_04():
    p = page('Theoretical-Mechanics/04-rigid-body-noninertial.html', 2.6)
    o = {}
    o['Ixx'] = num(p, "(function(){activate('m1');M1.pre='rect';M1.reset();"
                      "M1.render();return M1.Ixx();})()")
    o['Iyy'] = num(p, "M1.Iyy()")
    o['Izz'] = num(p, "M1.Izz()")
    o['I1'] = num(p, "M1.eig().I1")
    o['I2'] = num(p, "M1.eig().I2")
    o['psi'] = num(p, "((M1.eig().psi/DEG)%180+180)%180")
    o['ang0'] = num(p, "M1.angLo(M1.eig().psi)")
    o['gap90'] = num(p, "(function(){activate('m2');M2.th=Math.PI/2;return M2.gap();})()")
    o['gap01'] = num(p, "M2.gap(0.1)")
    o['det'] = num(p, "M2.det(M2.Rleft(2))")
    o['orth'] = num(p, "M2.orthErr(M2.Rleft(2))")
    o['I'] = [num(p, "(function(){activate('m3');M3.w0=10;M3.reset();return M3.I()[%d];})()" % i)
              for i in range(3)]
    o['inc'] = num(p, "M3.inc()")
    o['f1'] = num(p, "M3.f1()")
    o['f3'] = num(p, "M3.f3()")
    o['drift'] = num(p, """(function(){M3.axis='2';M3.w0=10;M3.reset();
      const h=2e-4,n=300000;let W=M3.W.slice();
      const E0=M3.En(W),M0=M3.M2(W);let d=0;
      for(let i=0;i<n;i++){W=rk4(0,W,h,(tt,y)=>M3.dW(y));
        if(i%997===0) d=Math.max(d,Math.abs(M3.En(W)/E0-1),Math.abs(M3.M2(W)/M0-1));}
      return d;})()""")
    o['Opr'] = num(p, "(function(){activate('m4');M4.w3=200;M4.th=30*DEG;"
                      "M4.setPre('reg');return M4.Opr();})()")
    o['wcrit'] = num(p, "M4.wcrit()")
    o['phreg'] = num(p, "M4.phReg(30*DEG)")
    o['rate'] = num(p, "(function(){activate('m5');M5.phi=50.45*DEG;M5.reset();"
                       "return M5.ratePh();})()")
    o['Tturn'] = num(p, "M5.Tturn()")
    o['Tpend'] = num(p, "M5.Tpend()")
    o['Tpole'] = num(p, "(function(){M5.phi=90*DEG;const v=M5.Tturn();"
                        "M5.phi=50.45*DEG;return v;})()")
    o['eq'] = num(p, "(function(){M5.phi=0;const v=M5.ratePh();"
                     "M5.phi=50.45*DEG;return v;})()")
    p.close()
    return o


def main_04():
    r, g = ref_04(), page_04()
    chk('м1 · I_xx прямокутника 2×1', r['Ixx'], g['Ixx'], 1e-12, 'кг·м²')
    chk('м1 · I_yy', r['Iyy'], g['Iyy'], 1e-12, 'кг·м²')
    chk('м1 · I_zz = I_xx + I_yy', r['Izz'], g['Izz'], 1e-12, 'кг·м²')
    chk('м1 · головні моменти (eigh проти формули)', r['I1'], g['I1'], 1e-10, 'кг·м²')
    chk('м1 · другий головний момент', r['I2'], g['I2'], 1e-10, 'кг·м²')
    chk('м1 · кут головної осі', r['psi'], g['psi'], 1e-6, '°')
    note('м1 · на головній осі L ∥ ω', 0.0, g['ang0'], g['ang0'] < 1e-6, '°')
    chk('м2 · розбіжність двох порядків при 90°',
        r['gap90']/DEGP, g['gap90']/DEGP, 1e-6, '°')
    chk('м2 · комутатор при θ = 0,1 рад ≈ θ²', r['gap01'], g['gap01'], 1e-4, 'рад')
    chk('м2 · det R', r['det'], g['det'], 1e-12)
    note('м2 · ‖RᵀR − E‖', 0.0, g['orth'], g['orth'] < 1e-12)
    for i in range(3):
        chk('м3 · I%d бруска' % (i+1), r['I'][i], g['I'][i], 1e-12, 'кг·м²')
    chk('м3 · інкремент навколо середньої осі', r['inc'], g['inc'], 1e-9, 'с⁻¹')
    note('м3 · той самий інкремент із прогону', r['inc'], r['incNum'],
         abs(r['incNum']-r['inc']) < 5e-3, 'с⁻¹')
    chk('м3 · частота навколо осі 1', r['f1'], g['f1'], 1e-9, 'рад/с')
    note('м3 · та сама частота з прогону', r['f1'], r['f1Num'],
         abs(r['f1Num']-r['f1']) < 5e-3, 'рад/с')
    chk('м3 · частота навколо осі 3', r['f3'], g['f3'], 1e-9, 'рад/с')
    note('м3 · дрейф E і M² за 60 с', 0.0, g['drift'], g['drift'] < 1e-6)
    chk('м4 · Ω_пр = mgl/(I₃ω₃)', r['Opr'], g['Opr'], 1e-9, 'рад/с')
    chk('м4 · точний корінь регулярної прецесії', r['phreg'], g['phreg'], 1e-6, 'рад/с')
    note('м4 · при ньому θ справді стоїть', 0.0, r['thSpan']/DEGP,
         r['thSpan'] < 1e-6, '°')
    note('м4 · середнє φ̇ прогону проти кореня', r['phreg'], r['phMean'],
         abs(r['phMean']-r['phreg']) < 1e-6, 'рад/с')
    chk('м4 · поріг стійкості вертикального вовчка', r['wcrit'], g['wcrit'], 1e-6, 'рад/с')
    chk('м5 · Ω_З·sin φ у Києві', r['rate'], g['rate'], 1e-6, '°/год')
    chk('м5 · повний оберт площини', r['Tturn'], g['Tturn'], 1e-6, 'год')
    chk('м5 · період маятника', r['Tpend'], g['Tpend'], 1e-9, 'с')
    chk('м5 · повний оберт на полюсі', r['Tpole'], g['Tpole'], 1e-6, 'год')
    note('м5 · на екваторі площина не повертається', 0.0, g['eq'],
         abs(g['eq']) < 1e-12, '°/год')
    note('м5 · те саме з прогону рівнянь Коріоліса', r['rate'], r['turnNum'],
         abs(r['turnNum']-r['rate']) < 0.05, '°/год')


# ====================================================== 05a ===============
def ref_05a():
    """Еталон для 05a: Лежандр чисельним диференціюванням, період маятника
    квадратурою, площа фазової плями — прогоном матриці Якобі потоку."""
    out = {}

    # --- вкладка 1 ---
    Lq = lambda v: 0.5*v*v
    Lr = lambda v: -math.sqrt(1-v*v)
    d = 1e-6
    v = 2.0
    out['pq'] = (Lq(v+d)-Lq(v-d))/(2*d)
    out['Hq'] = out['pq']*v - Lq(v)
    v = 0.8
    out['pr'] = (Lr(v+d)-Lr(v-d))/(2*d)
    out['Hr'] = out['pr']*v - Lr(v)
    out['Hr2'] = math.sqrt(out['pr']**2 + 1)

    # --- вкладка 2: період маятника квадратурою по координаті ---
    m, l = 1.0, 1.0
    mgl = m*G*l
    out['mgl'] = mgl
    out['T0'] = 2*math.pi*math.sqrt(l/G)
    def period(E):
        if E < mgl:                      # лібрація
            th0 = math.acos(max(-1, min(1, -E/mgl)))
            f = lambda u: 1/math.sqrt(max(1e-18, math.cos(u)-math.cos(th0)))
            # підстановка sin u/2 = sin θ₀/2 · sin ψ прибирає особливість
            k = math.sin(th0/2)
            g2 = lambda ps: 1/math.sqrt(max(1e-18, 1-k*k*math.sin(ps)**2))
            from scipy.integrate import quad
            I = quad(g2, 0, math.pi/2, limit=200)[0]
            return 4*math.sqrt(l/G)*I
        from scipy.integrate import quad
        f = lambda q: 1/math.sqrt(max(1e-18, 2*(E+mgl*math.cos(q))/(m*l*l)))
        return 2*quad(f, 0, math.pi, limit=400)[0]
    out['T14'] = period(-mgl*math.cos(1.4))
    out['Tnear'] = period(mgl*0.995)
    out['Trot'] = period(mgl*1.5)

    # --- вкладка 3: площа плями через матрицю Якобі потоку ---
    # dJ/dt = A(t)·J, A — матриця лінеаризації; det J і є множник площі
    def run(gam, T, pend):
        def rhs(t, y):
            q, p = y[0], y[1]
            J = np.array(y[2:6]).reshape(2, 2)
            aq = (-G*math.sin(q)) if pend else (-q)
            dq, dp = p, aq - 2*gam*p
            k = (-G*math.cos(q)) if pend else (-1.0)
            A = np.array([[0.0, 1.0], [k, -2*gam]])
            dJ = A@J
            return [dq, dp] + list(dJ.reshape(4))
        y0 = [0.0, 1.6, 1, 0, 0, 1]
        s = solve_ivp(rhs, [0, T], y0, method='DOP853', rtol=1e-12, atol=1e-14)
        J = np.array(s.y[2:6, -1]).reshape(2, 2)
        return float(np.linalg.det(J))
    out['detFree'] = run(0.0, 20.0, True)
    out['detFric'] = run(0.1, 10.0, True)
    out['expFric'] = math.exp(-2*0.1*10)
    return out


def page_05a():
    p = page('Theoretical-Mechanics/05a-hamilton-phase-space.html', 2.6)
    o = {}
    o['pq'] = num(p, "(function(){activate('m1');M1.sys='quad';M1.v=2;"
                     "M1.render();return M1.P(2);})()")
    o['Hq'] = num(p, "M1.H(2)")
    o['back'] = num(p, "(function(){M1.v=2;return M1.Lback();})()")
    o['Lq'] = num(p, "M1.L(2)")
    o['pr'] = num(p, "(function(){M1.sys='rel';M1.v=0.8;M1.render();return M1.P(0.8);})()")
    o['Hr'] = num(p, "M1.H(0.8)")
    o['nc'] = num(p, "(function(){M1.sys='nc';M1.v=0;M1.render();return M1.nRoots(0);})()")
    o['mgl'] = num(p, "(function(){activate('m2');M2.reset();M2.render();return M2.mgl();})()")
    o['T0'] = num(p, "M2.T0()")
    o['T14'] = num(p, "M2.period(-M2.mgl()*Math.cos(1.4))")
    o['Tnear'] = num(p, "M2.period(M2.mgl()*0.995)")
    o['Trot'] = num(p, "M2.period(M2.mgl()*1.5)")
    o['dH'] = num(p, """(function(){M2.q0=1.4;M2.p0=0;M2.reset();
      const h=2e-4,n=Math.round(20*M2.T0()/h),H0=M2.Hof(M2.q,M2.p);let d=0;
      for(let i=0;i<n;i++){const r=verlet(M2.q,M2.p,h,x=>-G*Math.sin(x));
        M2.q=r[0];M2.p=r[1];
        if(i%499===0) d=Math.max(d,Math.abs(M2.Hof(M2.q,M2.p)-H0));}
      return d;})()""")
    o['Sfree'] = num(p, """(function(){activate('m3');M3.sys='pend';M3.cq=0;M3.cp=1.6;
      M3.rad=0.3;M3.reset();
      const T=20*2*Math.PI*Math.sqrt(1/G),h=1e-3,n=Math.round(T/h);
      for(let i=0;i<n;i++){M3.step(M3.bnd,h);M3.t+=h;
        if(i%20===0) M3.densify();}
      return shoelace(M3.bnd)/M3.S0;})()""")
    o['Sfric'] = num(p, """(function(){M3.sys='fric';M3.gam=0.1;M3.cq=0;M3.cp=1.6;
      M3.rad=0.3;M3.reset();
      const h=1e-3,n=10000;
      for(let i=0;i<n;i++){M3.step(M3.bnd,h);M3.t+=h;
        if(i%20===0) M3.densify();}
      return shoelace(M3.bnd)/M3.S0;})()""")
    p.close()
    return o


def main_05a():
    r, g = ref_05a(), page_05a()
    chk('м1 · ½mv² при v = 2: p = ∂L/∂v', r['pq'], g['pq'], 1e-6)
    chk('м1 · той самий випадок: H = pv − L', r['Hq'], g['Hq'], 1e-6)
    note('м1 · подвійне перетворення вертає L', g['Lq'], g['back'],
         abs(g['back']-g['Lq']) < 1e-9)
    chk('м1 · релятивістська при v = 0,8: p', r['pr'], g['pr'], 1e-5)
    chk('м1 · та сама: H', r['Hr'], g['Hr'], 1e-5)
    note('м1 · H = √(p²c² + m²c⁴) тим самим числом', r['Hr2'], g['Hr'],
         abs(g['Hr']-r['Hr2']) < 1e-9)
    note('м1 · неопукла L: один нахил — три v', 3.0, g['nc'], g['nc'] == 3)
    chk('м2 · енергія сепаратриси mgl', r['mgl'], g['mgl'], 1e-12, 'Дж')
    chk('м2 · T₀ малих коливань', r['T0'], g['T0'], 1e-9, 'с')
    chk('м2 · період лібрації при q₀ = 1,4 (K(k) проти квадратури)',
        r['T14'], g['T14'], 1e-4, 'с')
    chk('м2 · період біля сепаратриси (E = 0,995·mgl)', r['Tnear'], g['Tnear'], 2e-3, 'с')
    chk('м2 · період ротації при E = 1,5·mgl', r['Trot'], g['Trot'], 1e-3, 'с')
    note('м2 · дрейф H за 20 періодів', 0.0, g['dH'], g['dH'] < 1e-6, 'Дж')
    note('м3 · площа плями за 20 періодів без тертя', r['detFree'], g['Sfree'],
         abs(g['Sfree']-1) < 0.01)
    chk('м3 · площа з тертям γ = 0,1 за 10 с', r['expFric'], g['Sfric'], 5e-3)
    note('м3 · та сама частка з детермінанта Якобі', r['expFric'], r['detFric'],
         abs(r['detFric']-r['expFric']) < 1e-6)


# ====================================================== 05b ===============
def ref_05b():
    """Еталон для 05b: дія як інтеграл по контуру, адіабатичний прогін
    рівнянь зі змінною довжиною, парабола безпеки й фронти дії."""
    from scipy.integrate import quad
    out = {}

    # --- вкладка 1: J як площа контуру, а не як E/ω ---
    m, w0, E = 1.0, 2.0, 2.0
    a = math.sqrt(2*E/(m*w0*w0))
    f = lambda q: math.sqrt(max(0.0, 2*m*(E - 0.5*m*w0*w0*q*q)))
    out['J'] = 2*quad(f, -a, a, limit=200)[0]/(2*math.pi)
    out['Jform'] = E/w0
    # адіабатичний маятник: прогін рівняння зі змінною довжиною
    L0, L1, TAD, th0 = 1.0, 0.5, 60.0, 0.35
    lof = lambda t: max(L1, L0 + (L1-L0)*t/TAD)
    def rhs(t, y):
        th, thd = y
        l = lof(t)
        ld = (L1-L0)/TAD if t < TAD else 0.0
        return [thd, -G/l*math.sin(th) - 2*ld/l*thd]
    sol = solve_ivp(rhs, [0, TAD], [th0, 0.0], method='DOP853',
                    rtol=1e-12, atol=1e-14, t_eval=np.linspace(0, TAD, 60001))
    th = sol.y[0]
    # амплітуда наприкінці — максимум за останні два періоди
    Tend = 2*math.pi*math.sqrt(L1/G)
    sel = sol.t > TAD - 2*Tend
    out['ampEnd'] = float(np.abs(th[sel]).max())
    out['ampTheory'] = th0*math.pow(L1/L0, -0.75)
    # J на початку й у кінці
    J0 = 0.5*m*math.sqrt(G)*math.pow(L0, 1.5)*th0**2
    J1 = 0.5*m*math.sqrt(G)*math.pow(L1, 1.5)*out['ampEnd']**2
    out['Jratio'] = J1/J0

    # --- вкладка 2: замикання при 3/2 ---
    wx, r = 1.0, 1.5
    T = 2*math.pi*2/wx
    out['Tclose'] = T
    out['closeErr'] = max(abs(math.cos(wx*T) - 1), abs(math.cos(r*wx*T) - 1))

    # --- вкладка 3: парабола безпеки й перпендикулярність фронтів ---
    v0 = 10.0
    out['hMax'] = v0*v0/(2*G)
    out['dMax'] = v0*v0/G
    S0 = lambda al, t: v0*v0*t - G*v0*math.sin(al)*t*t + G*G*t**3/3
    def tOfS(al, S):
        lo, hi = 0.0, 2*v0*math.sin(al)/G
        if S0(al, hi) < S: return None
        for _ in range(60):
            mid = (lo+hi)/2
            if S0(al, mid) < S: lo = mid
            else: hi = mid
        return (lo+hi)/2
    al = math.radians(35); t = 2*v0*math.sin(al)/G*0.5
    Sv = S0(al, t); d = 1e-4
    p1 = [v0*math.cos(al-d)*tOfS(al-d, Sv), v0*math.sin(al-d)*tOfS(al-d, Sv)
          - G*tOfS(al-d, Sv)**2/2]
    p2 = [v0*math.cos(al+d)*tOfS(al+d, Sv), v0*math.sin(al+d)*tOfS(al+d, Sv)
          - G*tOfS(al+d, Sv)**2/2]
    fr = [p2[0]-p1[0], p2[1]-p1[1]]
    v = [v0*math.cos(al), v0*math.sin(al) - G*t]
    c = (fr[0]*v[0]+fr[1]*v[1])/(math.hypot(*fr)*math.hypot(*v))
    out['perp'] = math.degrees(math.acos(min(1, abs(c))))
    return out


def page_05b():
    p = page('Theoretical-Mechanics/05b-canonical-action-angle.html', 2.6)
    o = {}
    o['J'] = num(p, "(function(){activate('m1');M1.sys='osc';M1.E=2;M1.reset();"
                    "M1.render();return M1.Jnow();})()")
    o['amp'] = num(p, """(function(){M1.sys='ad';M1.reset();
      const h=2e-4,n=Math.round(60/h);let mx=0;
      for(let i=0;i<n;i++){
        const l0=M1.l; M1.t+=h; M1.l=M1.lOf(M1.t);
        const ld=(M1.l-l0)/h;
        const a=-G/M1.l*Math.sin(M1.th)-2*ld/M1.l*M1.thd;
        M1.thd+=a*h; M1.th+=M1.thd*h;
        if(M1.t>60-2*2*Math.PI*Math.sqrt(0.5/G)) mx=Math.max(mx,Math.abs(M1.th));}
      return mx;})()""")
    o['Jdrift'] = num(p, "Math.abs(M1.Jnow()/M1.J0-1)")
    o['Tclose'] = num(p, "(function(){activate('m2');M2.r=1.5;M2.reset();"
                         "M2.render();return M2.Tclose();})()")
    o['frac'] = num(p, "(function(){const f=M2.frac(); return f?f[1]:0;})()")
    o['irr'] = num(p, "(function(){M2.r=Math.SQRT2;return M2.frac()?1:0;})()")
    o['hMax'] = num(p, "(function(){activate('m3');M3.v0=10;M3.al=45*DEG;"
                       "M3.render();return M3.hMax();})()")
    o['dMax'] = num(p, "M3.dMax()")
    o['tan45'] = num(p, "M3.tanX()")
    o['tanY45'] = num(p, "M3.tanY()")
    o['perp'] = num(p, "(function(){M3.al=35*DEG;return M3.perp();})()")
    p.close()
    return o


def main_05b():
    r, g = ref_05b(), page_05b()
    chk('м1 · J осцилятора: контурний інтеграл проти E/ω', r['J'], g['J'], 1e-6, 'Дж·с')
    note('м1 · та сама дія за формулою E/ω', r['Jform'], r['J'],
         abs(r['J']-r['Jform']) < 1e-6, 'Дж·с')
    chk('м1 · амплітуда після вкорочення l: 1 → 0,5 м',
        r['ampEnd'], g['amp'], 5e-3, 'рад')
    note('м1 · вона ж за θ₀ ∝ l^(−3/4)', r['ampTheory'], r['ampEnd'],
         abs(r['ampEnd']/r['ampTheory']-1) < 0.02, 'рад')
    note('м1 · J зберігся з точністю до 1 %', 1.0, r['Jratio'],
         abs(r['Jratio']-1) < 0.01)
    note('м1 · дрейф J на сторінці', 0.0, g['Jdrift'], g['Jdrift'] < 0.01)
    chk('м2 · період замикання при ω_y/ω_x = 3/2', r['Tclose'], g['Tclose'], 1e-9, 'с')
    note('м2 · замикання точне', 0.0, r['closeErr'], r['closeErr'] < 1e-9)
    note('м2 · знаменник нескоротного дробу 3/2', 2.0, g['frac'], g['frac'] == 2)
    note('м2 · √2 розпізнано як ірраціональне', 0.0, g['irr'], g['irr'] == 0)
    chk('м3 · найвища точка параболи безпеки', r['hMax'], g['hMax'], 1e-9, 'м')
    chk('м3 · найбільша дальність', r['dMax'], g['dMax'], 1e-9, 'м')
    note('м3 · під 45° дотик сідає рівно на землю', 0.0, g['tanY45'],
         abs(g['tanY45']) < 1e-9, 'м')
    note('м3 · і рівно на найбільшій дальності', r['dMax'], g['tan45'],
         abs(g['tan45']-r['dMax']) < 1e-9, 'м')
    chk('м3 · кут між фронтом S₀ і траєкторією', r['perp'], g['perp'], 1e-2, '°')


# ======================================================= 01 ===============
def ref_01():
    """Еталон для 01: період квадратурою scipy, задача двох тіл прогоном,
    кут між перигеліями з прогону, кеплерові сталі з інтегрування."""
    from scipy.integrate import quad
    out = {}

    # --- вкладка 1: подвійна яма ---
    m, a, b = 1.0, 1.0, 1.0
    U = lambda x: a*(x*x-b*b)**2
    out['w0'] = math.sqrt(8*a*b*b/m)
    out['T0'] = 2*math.pi/out['w0']
    out['Esep'] = a*b**4
    def period(E):
        # точки повороту правої ями
        x1 = brentq(lambda x: U(x)-E, 1e-6, b)
        x2 = brentq(lambda x: U(x)-E, b, 3.0)
        f = lambda x: 1/math.sqrt(max(1e-18, E-U(x)))
        return math.sqrt(2*m)*quad(f, x1, x2, points=[x1, x2], limit=400)[0]
    out['T045'] = period(0.45)
    out['T099'] = period(0.99*out['Esep'])

    # --- вкладка 2: двоє тіл ---
    m1, m2 = 3.0, 1.0
    out['mu'] = m1*m2/(m1+m2)
    out['rr'] = m2/m1

    # --- вкладка 3: розетка, кут між перигеліями з прогону ---
    mu, al, M, beta = 1.0, 1.0, 1.0, 0.1
    out['dphi'] = 2*math.pi/math.sqrt(1+2*mu*beta/(M*M))
    Ueff = lambda r: -al/r + beta/(r*r) + M*M/(2*mu*r*r)
    dU = lambda r: (Ueff(r+1e-7)-Ueff(r-1e-7))/2e-7
    E = -0.4
    rmin = brentq(lambda r: Ueff(r)-E, 0.3, 1.2)
    def rhs(t, y):
        r, rd, ph = y
        return [rd, -dU(r)/mu, M/(mu*r*r)]
    ev = lambda t, y: y[1]
    ev.direction = 1
    sol = solve_ivp(rhs, [1e-9, 40], [rmin, 0.0, 0.0], method='DOP853',
                    rtol=1e-12, atol=1e-14, events=ev)
    te = sol.t_events[0]
    ye = sol.y_events[0]
    out['dphiNum'] = float(ye[1][2]-ye[0][2]) if len(ye) > 1 else float('nan')

    # --- вкладка 4: Кеплер ---
    alk, mk = 1.0, 1.0
    r0, v0 = np.array([1.0, 0.0]), np.array([0.0, 0.8])
    Ek = 0.5*mk*v0@v0 - alk/np.linalg.norm(r0)
    Mk = mk*(r0[0]*v0[1]-r0[1]*v0[0])
    out['E'] = Ek; out['M'] = Mk
    out['p'] = Mk*Mk/(mk*alk)
    out['e'] = math.sqrt(1 + 2*Ek*Mk*Mk/(mk*alk*alk))
    out['a'] = alk/(2*abs(Ek))
    out['T'] = 2*math.pi*math.sqrt(mk*out['a']**3/alk)
    out['hodR'] = alk/abs(Mk)
    out['hodOff'] = out['e']*alk/abs(Mk)
    out['A'] = mk*alk*out['e']
    # |A| уздовж прогону: мусить стояти
    def kep(t, y):
        d = math.hypot(y[0], y[1])
        return [y[2], y[3], -alk*y[0]/(mk*d**3), -alk*y[1]/(mk*d**3)]
    sk = solve_ivp(kep, [0, out['T']], [1.0, 0.0, 0.0, 0.8], method='DOP853',
                   rtol=1e-13, atol=1e-15, t_eval=np.linspace(0, out['T'], 2001))
    Ax = mk*sk.y[3]*Mk - mk*alk*sk.y[0]/np.hypot(sk.y[0], sk.y[1])
    Ay = -mk*sk.y[2]*Mk - mk*alk*sk.y[1]/np.hypot(sk.y[0], sk.y[1])
    out['Adrift'] = float(np.abs(np.hypot(Ax, Ay) - out['A']).max())
    return out


def page_01():
    p = page('Theoretical-Mechanics/01-central-field.html', 2.6)
    o = {}
    o['w0'] = num(p, "(function(){activate('m1');M1.sys='well';M1.E=0.45;M1.x=1;"
                     "M1.reset();M1.render();return M1.w0();})()")
    o['T0'] = num(p, "2*Math.PI/M1.w0()")
    o['Esep'] = num(p, "M1.Esep()")
    o['T045'] = num(p, "M1.period(0.45)")
    o['T099'] = num(p, "M1.period(0.99*M1.Esep())")
    o['mu'] = num(p, "(function(){activate('m2');M2.m1=3;M2.m2=1;M2.reset();"
                     "M2.render();return M2.mu();})()")
    o['rr'] = num(p, "M2.m2/M2.m1")
    o['dphi'] = num(p, "(function(){activate('m3');M3.sys='ros';M3.beta=0.1;"
                       "M3.M=1;M3.E=-0.4;M3.reset();M3.render();"
                       "return M3.dphiTheory();})()")
    o['rmin'] = num(p, "M3.turn()[0]")
    o['rmax'] = num(p, "M3.turn()[1]")
    o['E'] = num(p, "(function(){activate('m4');M4.v=[0,0.8];M4.reset();"
                    "M4.render();return M4.En();})()")
    o['M'] = num(p, "M4.Mom()")
    o['p'] = num(p, "M4.par()")
    o['e'] = num(p, "M4.ecc()")
    o['a'] = num(p, "M4.semi()")
    o['T'] = num(p, "M4.per()")
    o['hodR'] = num(p, "M4.al/Math.abs(M4.Mom())")
    o['hodOff'] = num(p, "M4.ecc()*M4.al/Math.abs(M4.Mom())")
    o['A'] = num(p, "(function(){const A=M4.LRL(); return Math.hypot(A[0],A[1]);})()")
    o['Adrift'] = num(p, """(function(){M4.v=[0,0.8];M4.reset();
      const h=1e-4,n=Math.round(M4.per()/h),A0=M4.A0;let d=0;
      for(let i=0;i<n;i++){
        const y=rk4(0,[M4.r[0],M4.r[1],M4.v[0],M4.v[1]],h,(tt,s)=>{
          const dd=Math.hypot(s[0],s[1]);
          const aa=-M4.al/(M4.m*dd*dd*dd);
          return [s[2],s[3],aa*s[0],aa*s[1]];});
        M4.r=[y[0],y[1]];M4.v=[y[2],y[3]];
        if(i%97===0){const A=M4.LRL(); d=Math.max(d,Math.abs(Math.hypot(A[0],A[1])-A0));}}
      return d;})()""")
    p.close()
    return o


def main_01():
    r, g = ref_01(), page_01()
    chk('м1 · частота малих коливань √(8ab²/m)', r['w0'], g['w0'], 1e-6, 'рад/с')
    chk('м1 · T₀ малих коливань', r['T0'], g['T0'], 1e-6, 'с')
    chk('м1 · енергія сепаратриси ab⁴', r['Esep'], g['Esep'], 1e-12, 'Дж')
    chk('м1 · T(E) при E = 0,45 (quad проти Гауса–Чебишова)',
        r['T045'], g['T045'], 1e-4, 'с')
    # зростання біля сепаратриси логарифмічне, тож вимагаємо саме зростання,
    # а не якоїсь наперед заданої кратності
    note('м1 · T(E) при E = 0,99·E_сеп росте', r['T099'], g['T099'],
         abs(g['T099']/r['T099']-1) < 1e-3 and g['T099'] > 1.5*g['T045'], 'с')
    chk('м2 · приведена маса μ', r['mu'], g['mu'], 1e-12, 'кг')
    chk('м2 · r₁/r₂ = m₂/m₁', r['rr'], g['rr'], 1e-12)
    chk('м3 · кут між перигеліями 2π/√(1 + 2μβ/M²)',
        r['dphi']/DEGP, g['dphi']/DEGP, 1e-6, '°')
    note('м3 · той самий кут із прогону', r['dphi']/DEGP, r['dphiNum']/DEGP,
         abs(r['dphiNum']-r['dphi']) < 2e-3, '°')
    note('м3 · точки повороту 1,0 і 1,5', 1.0, g['rmin'], abs(g['rmin']-1.0) < 1e-4)
    note('м3 · друга точка повороту', 1.5, g['rmax'], abs(g['rmax']-1.5) < 1e-4)
    chk('м4 · E при v₀ = (0; 0,8)', r['E'], g['E'], 1e-12)
    chk('м4 · M', r['M'], g['M'], 1e-12)
    chk('м4 · параметр p = M²/mα', r['p'], g['p'], 1e-12)
    chk('м4 · ексцентриситет e', r['e'], g['e'], 1e-9)
    chk('м4 · велика піввісь a', r['a'], g['a'], 1e-9)
    chk('м4 · період T = 2π√(ma³/α)', r['T'], g['T'], 1e-6, 'с')
    chk('м4 · радіус годографа α/M', r['hodR'], g['hodR'], 1e-12)
    chk('м4 · зсув центра годографа eα/M', r['hodOff'], g['hodOff'], 1e-9)
    chk('м4 · |A| = mαe', r['A'], g['A'], 1e-9)
    note('м4 · дрейф |A| за оберт', 0.0, g['Adrift'], g['Adrift'] < 1e-6)
    note('м4 · те саме в еталоні', 0.0, r['Adrift'], r['Adrift'] < 1e-9)


# ======================================================= 02 ===============
def ref_02():
    """Еталон для 02: кінематика розпаду й зіткнення із замкнених формул,
    кут розсіяння — прогоном рівнянь руху, Монте-Карло — критерієм χ²."""
    out = {}
    v0, V = 1.0, 1.5
    out['thmax'] = math.degrees(math.asin(v0/V))

    mr = 2.0
    out['th1max'] = math.degrees(math.asin(1/mr))
    # сума кутів при рівних масах — для кількох χ
    out['sums'] = []
    for chd in (30, 70, 110, 150):
        ch = math.radians(chd)
        th1 = math.degrees(math.atan2(math.sin(ch), math.cos(ch)+1.0))
        th2 = math.degrees((math.pi-ch)/2)
        out['sums'].append(th1+th2)

    # Резерфорд: кут прогоном рівнянь руху з далекого старту
    al, rho = 0.5, 1.0
    def rhs(t, y):
        d = max(1e-9, math.hypot(y[0], y[1]))
        k = al/d**3
        return [y[2], y[3], k*y[0], k*y[1]]
    ev = lambda t, y: math.hypot(y[0], y[1]) - 600
    ev.terminal = True; ev.direction = 1
    sol = solve_ivp(rhs, [0, 2000], [-400.0, rho, 1.0, 0.0], method='DOP853',
                    rtol=1e-12, atol=1e-14, events=ev)
    vx, vy = sol.y[2, -1], sol.y[3, -1]
    out['chiNum'] = math.degrees(math.atan2(vy, vx))
    out['chiForm'] = math.degrees(2*math.atan(al/rho))

    a, rb = 1.0, 0.5
    out['chiBall'] = math.degrees(math.pi - 2*math.asin(rb/a))
    return out


def page_02():
    p = page('Theoretical-Mechanics/02-decay-collisions-scattering.html', 2.8)
    o = {}
    o['thmax'] = num(p, "(function(){activate('m1');M1.V=1.5;M1.reset();"
                        "M1.render();return M1.thMax()/DEG;})()")
    o['nsol'] = num(p, "(function(){M1.chi=1.2;return M1.nSol();})()")
    o['vcm'] = num(p, "M1.v0")
    o['th1max'] = num(p, "(function(){activate('m2');M2.mr=2;M2.render();"
                         "return M2.th1max()/DEG;})()")
    o['sums'] = [num(p, "(function(){M2.mr=1;return (M2.th1(%f)+M2.th2(%f))/DEG;})()"
                     % (math.radians(c), math.radians(c)))
                 for c in (30, 70, 110, 150)]
    o['chiNum'] = num(p, "(function(){activate('m3');M3.sys='rep';M3.a1=0.5;"
                         "M3.rho=1;M3.reset();M3.render();"
                         "return Math.abs(M3.probe().chi)/DEG;})()")
    o['chiForm'] = num(p, "2*Math.atan(M3.a1/M3.rho)/DEG")
    o['chiBall'] = num(p, "(function(){M3.sys='ball';M3.rho=0.5;M3.reset();"
                          "return M3.chi(0.5)/DEG;})()")
    # гістограма Монте-Карло й очікувані числа з формули — для критерію χ²
    o['mc'] = p.js("""(function(){M3.sys='rep';M3.a1=0.5;M3.wid=2.2;M3.reset();
      const M=M3.mkMC(), out=[];
      for(let i=0;i<M.NB;i++) out.push(M.h[i]);
      return JSON.stringify({h:out, N:M.N, NB:M.NB, RM:M.RM, a1:M3.a1});})()""")
    p.close()
    return o


def main_02():
    import json
    from scipy.stats import chi2 as chi2d
    r, g = ref_02(), page_02()
    chk('м1 · найбільший кут вильоту arcsin(v₀/V) при V = 1,5',
        r['thmax'], g['thmax'], 1e-6, '°')
    note('м1 · при V > v₀ одному θ відповідають дві швидкості', 2.0, g['nsol'],
         g['nsol'] == 2)
    note('м1 · |v| у СЦМ однакова для всіх напрямів', 1.0, g['vcm'],
         abs(g['vcm']-1) < 1e-12)
    chk('м2 · θ₁max при m₁/m₂ = 2', r['th1max'], g['th1max'], 1e-6, '°')
    for i, c in enumerate((30, 70, 110, 150)):
        chk('м2 · θ₁ + θ₂ при рівних масах, χ = %d°' % c,
            r['sums'][i], g['sums'][i], 1e-9, '°')
    chk('м3 · кут розсіяння: прогін проти 2·arctg(α/mv²ρ)',
        r['chiForm'], g['chiNum'], 0.1, '°')
    note('м3 · той самий прогін в еталоні', r['chiForm'], r['chiNum'],
         abs(r['chiNum']-r['chiForm']) < 0.1, '°')
    chk('м3 · тверда куля, ρ = a/2', r['chiBall'], g['chiBall'], 1e-9, '°')
    # критерій χ²: очікувані числа — точні, з ρ(χ) = α/tg(χ/2)
    d = json.loads(g['mc'])
    al, RM, N, NB = d['a1'], d['RM'], d['N'], d['NB']
    rho = lambda c: min(RM, al/math.tan(c/2)) if c > 1e-9 else RM
    chis, obs, exp = 0.0, 0, 0
    k = 0
    for i in range(NB):
        c1 = i/NB*math.pi; c2 = (i+1)/NB*math.pi
        E = N*(rho(max(c1, 1e-9))**2 - rho(c2)**2)/RM**2
        O = d['h'][i]
        if E < 5: continue
        chis += (O-E)**2/E; k += 1
        obs += O; exp += E
    lim = chi2d.ppf(0.95, max(1, k-1))
    note('м3 · Монте-Карло проти формули: χ² на %d бінах' % k, lim, chis,
         chis < lim)


DISPATCH = {'00a': main_00a, '00b': main_00b, '03': main_03, '04': main_04, '05a': main_05a, '05b': main_05b, '01': main_01, '02': main_02}

if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else '00a'
    if which not in DISPATCH:
        print('немає перевірок для «%s»; є: %s' % (which, ', '.join(sorted(DISPATCH))))
        sys.exit(2)
    DISPATCH[which]()
    report()
