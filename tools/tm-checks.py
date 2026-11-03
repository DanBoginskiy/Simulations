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

DISPATCH = {'00a': main_00a}

if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else '00a'
    if which not in DISPATCH:
        print('немає перевірок для «%s»; є: %s' % (which, ', '.join(sorted(DISPATCH))))
        sys.exit(2)
    DISPATCH[which]()
    report()
