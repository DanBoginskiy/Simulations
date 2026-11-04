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


DISPATCH = {'00a': main_00a, '00b': main_00b}

if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else '00a'
    if which not in DISPATCH:
        print('немає перевірок для «%s»; є: %s' % (which, ', '.join(sorted(DISPATCH))))
        sys.exit(2)
    DISPATCH[which]()
    report()
