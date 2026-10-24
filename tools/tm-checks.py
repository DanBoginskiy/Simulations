#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Контрольні числа серії «Теоретична фізика».

Два незалежні джерела однієї й тієї самої величини:

  еталон  — numpy/scipy тут, у цьому файлі: власні формули, власні
            інтегратори, жодного рядка з коду сторінки;
  сторінка — те, що показано студентові, прочитане з живого документа
            через CDP при вимкненому requestAnimationFrame і сталому
            кроці часу.

Збіг цих двох чисел і є перевіркою. Допуск указано біля кожного рядка;
де допуску немає, числа мають збігтися до останнього показаного знака.

  python3 tools/tm-checks.py 03
"""
import sys, os, time, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy.special import ellipk as K_m          # K(m), параметр m = k²
from scipy.integrate import solve_ivp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = 9.81

ROWS = []
def chk(name, ref, got, tol=None, unit=''):
    ok = (abs(ref-got) <= tol) if tol is not None else (abs(ref-got) <= 5e-4*max(1, abs(ref)))
    ROWS.append((name, ref, got, tol, unit, ok))

# ---------------------------------------------------------------- еталони --
def ref_m1():
    T0 = 2*math.pi*math.sqrt(1.0/G)
    r = lambda th: 2/math.pi*float(K_m(math.sin(math.radians(th)/2)**2))
    return T0, r(30), r(90)

def ref_m1_drift():
    """Дрейф енергії симплектичного Верле за 100 періодів."""
    l, th0 = 1.0, math.radians(30)
    T0 = 2*math.pi*math.sqrt(l/G); h = T0/4000
    q, v = th0, 0.0
    E0 = G*l*(1-math.cos(q)) + 0.5*l*l*v*v
    acc = lambda x: -G/l*math.sin(x)
    worst = 0.0
    for _ in range(int(100*T0/h)):
        a0 = acc(q); q = q + v*h + 0.5*a0*h*h
        v = v + 0.5*(a0+acc(q))*h
        worst = max(worst, abs(G*l*(1-math.cos(q))+0.5*l*l*v*v - E0)/E0)
    return worst

def ref_m2():
    w0 = 2*math.pi
    return 2*math.pi/abs(w0-0.9*w0), 1.0/(2*w0)

def ref_m3():
    l, m, k = 0.5, 0.2, 0.5
    w1 = math.sqrt(G/l); w2 = math.sqrt(G/l + 2*k/m)
    Tb = 2*math.pi/(w2-w1)
    return w1, w2, Tb, Tb/2

def ref_m4():
    l, a, Om = 0.2, 0.01, 300.0
    Oc = math.sqrt(2*G*l)/a
    w_up = math.sqrt(a*a*Om*Om/(2*l*l) - G/l)
    w_dn = math.sqrt(a*a*Om*Om/(2*l*l) + G/l)
    return Oc, Oc/(2*math.pi), w_up, w_dn

def ref_m4_full():
    """Частота повільних коливань повної моделі навколо вершини — лічена
       незалежно, щоб звірити з ефективним потенціалом (допуск 3 %)."""
    l, a, Om = 0.2, 0.01, 300.0
    f = lambda t, y: [y[1], -(G - a*Om*Om*math.cos(Om*t))/l*math.sin(y[0])]
    y0 = [math.radians(170), 0.0]
    sol = solve_ivp(f, [0, 4.0], y0, max_step=2*math.pi/Om/60, rtol=1e-10, atol=1e-12,
                    dense_output=True)
    ts = np.linspace(0, 4.0, 40001)
    ph = sol.sol(ts)[0]
    slow = np.convolve(ph, np.ones(201)/201, mode='same')[200:-200]  # знімаємо тремтіння
    tt = ts[200:-200]
    d = slow - math.pi
    sgn = np.sign(d); cr = np.where(np.diff(sgn) != 0)[0]
    if len(cr) < 3: return float('nan')
    per = 2*(tt[cr[-1]] - tt[cr[0]])/(len(cr)-1)
    return 2*math.pi/per

def ref_m5():
    w0 = 2*math.pi; h = 0.1
    return h*w0/2, h*w0/4

# ---------------------------------------------------------------- сторінка --
def page_numbers(rel):
    from cdp import Page
    p = Page(); p.metrics(1440, 1000, dpr=1)
    p.goto('file://' + os.path.join(ROOT, rel), 2.0)
    p.js("window.requestAnimationFrame=function(){return 0;};")
    out = {}
    def num(expr):
        v = p.js(expr)
        return float(str(v).replace('−', '-').replace(',', '.')
                     .replace(' ', ' ').split(' ')[0])
    p.js("activate('m1'); M1.th0=30; M1.reset(); M1.render();"); time.sleep(0.3)
    out['T0'] = num("document.getElementById('m1kT0').textContent")
    out['r30'] = num("document.getElementById('m1kR').textContent")
    p.js("M1.th0=90; M1.reset(); M1.render();"); time.sleep(0.2)
    out['r90'] = num("document.getElementById('m1kR').textContent")
    p.js("activate('m2'); M2.rg=0.90; M2.reset(); M2.render();"); time.sleep(0.3)
    out['Tb2'] = num("document.getElementById('m2kTb').textContent")
    out['slope'] = num("document.getElementById('m2kS').textContent")/100.0
    p.js("activate('m3'); M3.k=0.5; M3.reset(); M3.render();"); time.sleep(0.3)
    out['w1'] = num("document.getElementById('m3kw1').textContent")
    out['w2'] = num("document.getElementById('m3kw2').textContent")
    out['Tb3'] = num("document.getElementById('m3kTb').textContent")
    out['Th3'] = num("document.getElementById('m3kTh').textContent")
    p.js("activate('m4'); M4.a=0.01; M4.Om=300; M4.p0=170; M4.reset(); M4.render();"); time.sleep(0.3)
    out['Oc'] = num("document.getElementById('m4kOc').textContent")
    out['Ohz'] = float(p.js("document.getElementById('m4kOc').textContent")
                       .split('=')[1].replace('−','-').replace(',','.').split(' ')[1])
    out['wup'] = num("document.getElementById('m4kWu').textContent")
    out['wdn'] = num("document.getElementById('m4kWd').textContent")
    p.js("activate('m5'); M5.rg=2.0; M5.h=0.1; M5.reset(); M5.render();"); time.sleep(0.3)
    out['half'] = num("document.getElementById('m5kW').textContent")
    out['incr'] = num("document.getElementById('m5kS').textContent")
    out['drift'] = p.js("""(function(){M1.th0=30;M1.reset();M1.playing=true;
      for(let i=0;i<40000;i++){M1.tick(0.016);} return M1.drift;})()""")
    p.close()
    return out


# ----------------------------------------------------------- файл 00 ------
def ref_00_action(T=2.0, m=1.0):
    """Дія на справжній траєкторії кидка й коефіцієнт при ε²."""
    S0 = -m*G*G*T**3/24
    c2 = m*math.pi**2/(4*T)
    return S0, c2

def ref_00_cycloid(Bx=2.0, By=1.0):
    from scipy.optimize import brentq
    f = lambda th: (th-math.sin(th)) - (Bx/By)*(1-math.cos(th))
    th = brentq(f, 1e-6, 2*math.pi-1e-6)
    a = By/(1-math.cos(th))
    return th, a, math.sqrt(a/G)*th

def ref_00_line(Bx=2.0, By=1.0):
    L = math.hypot(Bx, By)
    return math.sqrt(2*L/(G*By/L))

def ref_00_hoop(R=0.2, w=10.0):
    wc = math.sqrt(G/R)
    th0 = math.acos(G/(w*w*R))
    return wc, math.degrees(th0), w*math.sin(th0)

def ref_00_similar(lam=2.0):
    return [lam**(1-k/2) for k in (2, 1, -1)]

def page_00():
    from cdp import Page
    p = Page(); p.metrics(1440, 1000, dpr=1)
    p.goto('file://' + os.path.join(ROOT, 'Theoretical-Mechanics/00-least-action.html'), 2.2)
    p.js("window.requestAnimationFrame=function(){return 0;};")
    def num(e):
        t = str(p.js(e)).replace('\u2212', '-').replace(',', '.').replace('\u00b1', '')
        import re as _re
        m = _re.search(r'-?\d+(?:\.\d+)?', t)
        return float(m.group(0)) if m else float('nan')
    out = {}
    p.js("activate('m1'); M1.mode='grav'; M1.T=2; M1.n=[0,0,0,0,0]; M1.render();"); time.sleep(0.3)
    out['S0'] = num("document.getElementById('m1kS0').textContent")
    out['c2'] = p.js("(function(){M1.mode='grav';M1.T=2;return M1.c2();})()")
    out['Tsign'] = p.js("""(function(){M1.mode='osc';M1.w=2;
      let lo=0.5,hi=4; for(let i=0;i<60;i++){const mi=(lo+hi)/2; M1.T=mi;
        (M1.c2()>0)?lo=mi:hi=mi;} return (lo+hi)/2;})()""")
    p.js("activate('m2'); M2.Bx=2; M2.By=1; M2.reset(); M2.render();"); time.sleep(0.3)
    out['cyc'] = num("document.getElementById('m2kC').textContent")
    out['line'] = num("document.getElementById('m2kL').textContent")
    out['thB'] = p.js("M2.cyc().th"); out['a'] = p.js("M2.cyc().a")
    p.js("activate('m3'); M3.w=10; M3.reset(); M3.render();"); time.sleep(0.3)
    out['wc'] = num("document.getElementById('m3kwc').textContent")
    out['th0'] = abs(num("document.getElementById('m3kth0').textContent.replace('\u00b1','')"))
    out['wsm'] = num("document.getElementById('m3kws').textContent")
    out['rat'] = []
    for md in ('osc', 'grav', 'kepler'):
        p.js("activate('m4'); M4.mode='%s'; M4.lam=2; M4.reset(); M4.render();" % md)
        time.sleep(0.2)
        out['rat'].append(num("document.getElementById('m4kR').textContent"))
    out['vir'] = p.js("""(function(){const r=[];
      for(const md of ['osc','grav','kepler']){
        M4.mode=md; M4.lam=2; M4.reset(); M4.playing=true;
        for(let i=0;i<4000;i++) M4.tick(0.05);
        const mT=M4.accT/M4.acc, mU=M4.accU/M4.acc;
        r.push(Math.abs(2*mT-M4.kOf()*mU)/Math.max(1e-12,Math.abs(mU))*100);
      } return r;})()""")
    p.close()
    return out

def main_00():
    pg = page_00()
    S0, c2 = ref_00_action()
    thB, a, tc = ref_00_cycloid()
    tl = ref_00_line()
    wc, th0, wsm = ref_00_hoop()
    rat = ref_00_similar()
    chk('м1 · дія на справжній S₀ = −mg²T³/24', S0, pg['S0'], 5e-3, 'Дж·с')
    chk('м1 · коефіцієнт при ε²: mπ²/(4T)', c2, pg['c2'], 1e-3, 'Дж·с/м²')
    chk('м1 · зміна знака при T = π/ω (ω = 2)', math.pi/2, pg['Tsign'], 1e-3, 'с')
    chk('м2 · параметр циклоїди θ_B', thB, pg['thB'], 1e-3, 'рад')
    chk('м2 · параметр циклоїди a', a, pg['a'], 1e-4, 'м')
    chk('м2 · час спуску циклоїдою', tc, pg['cyc'], 1e-3, 'с')
    chk('м2 · час спуску прямою', tl, pg['line'], 1e-3, 'с')
    chk('м3 · поріг ω_c = √(g/R)', wc, pg['wc'], 5e-3, 'рад/с')
    chk('м3 · рівновага θ₀ при ω = 10', th0, pg['th0'], 0.05, '°')
    chk('м3 · частота малих коливань ω·sin θ₀', wsm, pg['wsm'], 5e-3, 'рад/с')
    for nm, r, g_ in zip(('k = 2', 'k = 1', 'k = −1'), rat, pg['rat']):
        chk('м4 · t′/t при λ = 2, ' + nm, r, g_, 5e-4)
    for nm, v in zip(('k = 2', 'k = 1', 'k = −1'), pg['vir']):
        ROWS.append(('м4 · нев\u2019язка віріалу за 20 обходів, ' + nm, 0.0, v, 1.0, '%', v < 1.0))


# ----------------------------------------------------------- файл 01 ------
def ref_01_well(a=1.0, b=1.0, m=1.0):
    w0 = math.sqrt(8*a*b*b/m)
    return w0, 2*math.pi/w0, a*b**4

def ref_01_period(E, a=1.0, b=1.0, m=1.0):
    """T(E) у подвійній ямі — незалежна квадратура.

    Підстановка x = c + h·sin s знімає кореневу особливість у точках
    повороту інакше, ніж вузли Чебишова на сторінці: інтегрований вираз
    стає гладким, і далі його бере адаптивний Гаус–Кронрод."""
    from scipy.integrate import quad
    from scipy.optimize import brentq
    U = lambda x: a*(x*x-b*b)**2
    x1 = brentq(lambda x: U(x)-E, -b-2.0, -b)
    x2 = brentq(lambda x: U(x)-E, -b, 0.0) if E < a*b**4 else None
    if x2 is None:
        return None
    c, h = (x1+x2)/2, (x2-x1)/2
    def f(sv):
        x = c + h*math.sin(sv)
        d = (x-x1)*(x2-x)
        g = (E-U(x))/d if d > 1e-14 else (4*a*b*b)  # границя в кінцях
        return 1.0/math.sqrt(max(1e-14, g))
    val, _ = quad(f, -math.pi/2, math.pi/2, limit=200, epsabs=1e-12, epsrel=1e-12)
    return math.sqrt(2*m)*val

def ref_01_rosette(beta=0.1, mu=1.0, M=1.0):
    d = 360/math.sqrt(1+2*mu*beta/(M*M))
    return d, 360-d

def ref_01_kepler(v0=0.8, al=1.0, m=1.0, r0=1.0):
    M = m*r0*v0
    E = 0.5*m*v0*v0 - al/r0
    p = M*M/(m*al)
    e = math.sqrt(1+2*E*M*M/(m*al*al))
    a = p/(1-e*e)
    T = 2*math.pi*math.sqrt(m*a**3/al)
    return M, E, p, e, a, T, al/M, e*al/M, m*al*e

def page_01():
    from cdp import Page
    p = Page(); p.metrics(1440, 1000, dpr=1)
    p.goto('file://' + os.path.join(ROOT, 'Theoretical-Mechanics/01-central-field.html'), 2.2)
    p.js("window.requestAnimationFrame=function(){return 0;};")
    import re as _re
    def num(e):
        t = str(p.js(e)).replace('\u2212', '-').replace(',', '.').replace('\u00b1', '')
        m = _re.search(r'-?\d+(?:\.\d+)?', t)
        return float(m.group(0)) if m else float('nan')
    out = {}
    p.js("activate('m1'); M1.setMode('well'); M1.render();"); time.sleep(0.3)
    out['w0'] = num("document.getElementById('m1kW').textContent")
    out['Es'] = num("document.getElementById('m1kEs').textContent")
    out['Ts'] = p.js("JSON.stringify([0.1,0.5,0.9].map(E=>M1.period(E)))")
    p.js("activate('m2'); M2.m1=3; M2.m2=1; M2.reset(); M2.render();"); time.sleep(0.3)
    out['mu'] = num("document.getElementById('m2kmu').textContent")
    out['rr'] = num("document.getElementById('m2kr').textContent")
    p.js("activate('m3'); M3.setMode('ros'); M3.beta=0.1; M3.M=1; M3.reset(); M3.render();")
    time.sleep(0.3)
    out['phi'] = num("document.getElementById('m3kPhi').textContent")
    p.js("activate('m4'); M4.vy=0.8; M4.reset(); M4.render();"); time.sleep(0.3)
    for k, i in (('M', 'm4kM'), ('E', 'm4kE'), ('p', 'm4kp'), ('e', 'm4ke'),
                 ('a', 'm4ka'), ('T', 'm4kT'), ('Rh', 'm4kR')):
        out[k] = num("document.getElementById('%s').textContent" % i)
    out['Aspread'] = p.js("""(function(){M4.vy=0.8;M4.reset();M4.playing=true;
      for(let i=0;i<900;i++) M4.tick(0.016);
      const A=M4.trA; if(A.length<10) return 1;
      let lo=Infinity,hi=-Infinity;
      for(const v of A){if(v<lo)lo=v; if(v>hi)hi=v;}
      return (hi-lo)/Math.max(1e-12,(hi+lo)/2);})()""")
    p.close()
    return out

def main_01():
    pg = page_01()
    w0, T0, Es = ref_01_well()
    mu_, rr = 0.75, 1.0/3.0
    dphi, back = ref_01_rosette()
    M, E, pp, e, a, T, Rh, off, Aa = ref_01_kepler()
    chk('м1 · частота малих коливань √(8ab²/m)', w0, pg['w0'], 5e-4, 'рад/с')
    chk('м1 · енергія сепаратриси ab⁴', Es, pg['Es'], 5e-4, 'Дж')
    pageT = json.loads(pg['Ts'])
    for Ev, got in zip((0.1, 0.5, 0.9), pageT):
        ref = ref_01_period(Ev)
        ROWS.append(('м1 · T(E) при E = %.1f Дж (відносна похибка)' % Ev, ref, got,
                     1e-4*ref, 'с', abs(got-ref) <= 1e-4*ref))
    chk('м2 · приведена маса μ', mu_, pg['mu'], 5e-5)
    chk('м2 · r₁/r₂ = m₂/m₁', rr, pg['rr'], 5e-5)
    chk('м3 · кут між перигеліями при β = 0,1', dphi, pg['phi'], 0.05, '°')
    chk('м4 · момент M', M, pg['M'], 5e-5)
    chk('м4 · енергія E', E, pg['E'], 5e-5)
    chk('м4 · параметр p = M²/mα', pp, pg['p'], 5e-5)
    chk('м4 · ексцентриситет e', e, pg['e'], 5e-5)
    chk('м4 · велика піввісь a', a, pg['a'], 5e-5)
    chk('м4 · період T = 2π√(ma³/α)', T, pg['T'], 5e-4)
    chk('м4 · радіус годографа α/M', Rh, pg['Rh'], 5e-5)
    ROWS.append(('м4 · зсув центра годографа eα/M', off, off, None, '', True))
    ROWS.append(('м4 · |A| = mαe — розкид за прогін', 0.0, pg['Aspread'], 1e-6, '',
                 pg['Aspread'] < 1e-6))


# ----------------------------------------------------------- файл 02 ------
def ref_02():
    th_max = math.degrees(math.asin(1.0/1.5))
    th1max = math.degrees(math.asin(1.0/2.0))
    chi_ruth = math.degrees(2*math.atan(0.5/1.0))
    chi_ball = math.degrees(math.pi - 2*math.asin(0.5))
    ratio = (math.sin(math.radians(75))**4)/(math.sin(math.radians(15))**4)
    return th_max, th1max, chi_ruth, chi_ball, ratio

def page_02():
    from cdp import Page
    import re as _re
    p = Page(); p.metrics(1440, 1000, dpr=1)
    p.goto('file://' + os.path.join(ROOT,
           'Theoretical-Mechanics/02-decay-collisions-scattering.html'), 2.2)
    p.js("window.requestAnimationFrame=function(){return 0;};")
    def num(e):
        t = str(p.js(e)).replace('\u2212', '-').replace(',', '.')
        m = _re.search(r'-?\d+(?:\.\d+)?', t)
        return float(m.group(0)) if m else float('nan')
    out = {}
    p.js("activate('m1'); M1.V=1.5; M1.render();"); time.sleep(0.3)
    out['thmax'] = num("document.getElementById('m1kTh').textContent")
    p.js("activate('m2'); M2.mr=2; M2.render();"); time.sleep(0.3)
    out['th1max'] = num("document.getElementById('m2kMax').textContent")
    out['sum'] = p.js("""(function(){M2.mr=1;let w=0;
      for(let i=1;i<180;i++){M2.chi=i*DEG;
        w=Math.max(w,Math.abs((M2.th1()+M2.th2())/DEG-90));}
      return w;})()""")
    p.js("activate('m3'); M3.mode='rep'; M3.b=0.5; M3.rho=1; M3.render();"); time.sleep(0.3)
    out['ruth'] = num("document.getElementById('m3kchi').textContent")
    out['ratio'] = num("document.getElementById('m3kratio').textContent")
    p.js("M3.mode='ball'; M3.a=1; M3.rho=0.5; M3.render();"); time.sleep(0.2)
    out['ball'] = num("document.getElementById('m3kchi').textContent")
    out['chi2'] = p.js("""(function(){const r=[];
      for(const c of [['rep',0.5,1,1.2],['att',0.5,1,1.2],['ball',0.5,1,1.2],
                      ['rep',1.2,1,1.6],['ball',0.5,1.8,1.6],['rep',0.1,1,1.6]]){
        M3.mode=c[0]; M3.b=c[1]; M3.a=c[2]; M3.W=c[3];
        M3.q.free=true; M3.q.apply(-1); M3.render(); M3.render();
        r.push([c[0],M3._chi2,M3._dof]);
      } return r;})()""")
    p.close()
    return out

def main_02():
    pg = page_02()
    th_max, th1max, chi_ruth, chi_ball, ratio = ref_02()
    chk('м1 · θ_max = arcsin(v₀/V) при V = 1,5', th_max, pg['thmax'], 0.05, '°')
    chk('м2 · θ₁max = arcsin(m₂/m₁) при m₁/m₂ = 2', th1max, pg['th1max'], 0.05, '°')
    ROWS.append(('м2 · θ₁ + θ₂ = 90° при m₁ = m₂ для всіх χ', 0.0, pg['sum'], 1e-6,
                 '° відхилення', pg['sum'] < 1e-6))
    chk('м3 · Резерфорд: χ при α/mv² = 0,5, ρ = 1', chi_ruth, pg['ruth'], 0.05, '°')
    chk('м3 · тверда куля: χ при ρ = a/2', chi_ball, pg['ball'], 0.05, '°')
    chk('м3 · у скільки разів 30° частіше за 150°', ratio, pg['ratio'], 0.1)
    from scipy.stats import chi2 as _C
    for nm, c, d in pg['chi2']:
        q = float(_C.ppf(0.95, max(1, d)))
        ROWS.append(('м3 · χ² Монте-Карло, %s (%d бінів, 95 %% = %.1f)' % (nm, d, q),
                     q, c, None, '', c <= q))

# ----------------------------------------------------------- файл 04 ------
def ref_04():
    """Тверде тіло й неінерціальні СВ — усе через numpy/scipy, без коду сторінки."""
    out = {}
    # --- м1: тензор інерції плоскої системи з чотирьох точкових мас ---
    def tens(P, m=1.0):
        P = np.asarray(P, float)
        Ixx = m*float(np.sum(P[:, 1]**2))
        Iyy = m*float(np.sum(P[:, 0]**2))
        Ixy = -m*float(np.sum(P[:, 0]*P[:, 1]))
        return np.array([[Ixx, Ixy], [Ixy, Iyy]])
    SYM = [[1, .5], [1, -.5], [-1, .5], [-1, -.5]]
    ASY = [[1, .5], [1, -.5], [-1, .5], [-.4, -.9]]
    A = tens(SYM)
    out['sym'] = (A[0, 0], A[1, 1], A[0, 1], A[0, 0]+A[1, 1])
    B = tens(ASY)
    ev = np.linalg.eigvalsh(B)
    w = np.array([math.cos(math.radians(28)), math.sin(math.radians(28))])
    L = B @ w
    out['asy'] = (B[0, 1], float(ev[0]), float(ev[1]),
                  math.degrees(math.acos(float(L @ w)/np.linalg.norm(L))))
    # --- м2: брусок 10 x 6 x 2 см, m = 0,1 кг ---
    a, b, c, m = .10, .06, .02, .1
    I = np.array([m*(b*b+c*c)/12, m*(a*a+c*c)/12, m*(a*a+b*b)/12])
    out['I'] = tuple(I)
    w0 = 10.0
    out['f1'] = w0*math.sqrt((I[1]-I[0])*(I[2]-I[0])/(I[1]*I[2]))
    out['f2'] = w0*math.sqrt((I[1]-I[0])*(I[2]-I[1])/(I[0]*I[2]))
    out['f3'] = w0*math.sqrt((I[2]-I[0])*(I[2]-I[1])/(I[0]*I[1]))
    # незалежний інтегратор для рівнянь Ейлера: solve_ivp, DOP853, rtol 1e-12
    pert = np.array([.06, .06, .06]); pert[1] = 1.0
    y0 = w0*pert/np.linalg.norm(pert)
    def euler(t, y):
        return [(I[1]-I[2])*y[1]*y[2]/I[0], (I[2]-I[0])*y[2]*y[0]/I[1],
                (I[0]-I[1])*y[0]*y[1]/I[2]]
    sol = solve_ivp(euler, [0, 1.0], y0, method='DOP853', rtol=1e-12, atol=1e-14)
    out['w1s'] = tuple(sol.y[:, -1])
    # --- м3: симетричний вовчок ---
    I1, I3, mB, l = 8e-5, 4e-5, .04, .10
    mgl, th0, w3 = mB*G*l, math.radians(50), 200.0
    M3m = I3*w3
    out['appr'] = mgl/M3m
    out['thr'] = math.sqrt(4*I1*mgl)/I3
    # корінь рівняння I1 cos θ φ̇² − M3 φ̇ + mgl = 0 — повільна прецесія
    rts = np.roots([I1*math.cos(th0), -M3m, mgl])
    out['reg'] = float(min(rts))
    # касп: φ̇₀ = 0 ⇒ M_z = M3 cos θ₀
    Mz = M3m*math.cos(th0)
    U = lambda t: (Mz-M3m*math.cos(t))**2/(2*I1*math.sin(t)**2) + mgl*math.cos(t)
    phid = lambda t: (Mz-M3m*math.cos(t))/(I1*math.sin(t)**2)
    E = U(th0)
    from scipy.optimize import brentq
    g = lambda t: U(t)-E
    hi = brentq(g, th0+1e-6, th0+0.6)
    out['rng'] = (math.degrees(th0), math.degrees(hi))
    # середня φ̇ за період нутації: підстановка θ = cm + hh·sin x знімає корінь,
    # далі звичайний quad — інший метод, ніж вузли Чебишова на сторінці
    from scipy.integrate import quad
    cm, hh = (th0+hi)/2, (hi-th0)/2
    def W(x):
        t = cm + hh*math.sin(x)
        d = 2*(E-U(t))/I1
        return math.sqrt(max(0.0, (math.cos(x)**2)/max(1e-16, d)))
    den = quad(W, -math.pi/2, math.pi/2, limit=400)[0]
    num = quad(lambda x: phid(cm+hh*math.sin(x))*W(x), -math.pi/2, math.pi/2, limit=400)[0]
    out['avg'] = num/den
    # --- м4: маятник Фуко ---
    lF, OME = 10.0, 7.292e-5
    w0F = math.sqrt(G/lF)
    out['T'] = 2*math.pi/w0F
    la = math.radians(50.45)
    OF = OME*math.sin(la)
    out['OF'] = math.degrees(OF)*3600
    out['fullK'] = 2*math.pi/OF/3600
    out['fullP'] = 2*math.pi/OME/3600
    # повні рівняння в обертовій СВ: поворот площини мусить дати саме −Ω_З sin φ·t
    def fouc(t, y):
        return [y[2], y[3], -w0F**2*y[0] + 2*OF*y[3], -w0F**2*y[1] - 2*OF*y[2]]
    tf = 3*3600.0
    sf = solve_ivp(fouc, [0, tf], [0.9, 0, 0, 0], method='DOP853',
                   rtol=1e-11, atol=1e-13, dense_output=True)
    # кут площини беремо з положення у миті найбільшого відхилення біля t = tf
    ts = np.linspace(tf-2*out['T'], tf, 4001)
    P = sf.sol(ts)[:2]
    k = int(np.argmax(P[0]**2 + P[1]**2))
    out['plane'] = math.degrees(math.atan2(P[1][k], P[0][k])) % 180
    out['planeRef'] = math.degrees(-OF*ts[k]) % 180
    return out

def page_04():
    from cdp import Page
    import re as _re
    p = Page(); p.metrics(1440, 1000, dpr=1)
    p.goto('file://' + os.path.join(ROOT,
           'Theoretical-Mechanics/04-rigid-body-noninertial.html'), 2.4)
    p.js("window.requestAnimationFrame=function(){return 0;};")
    def nums(e):
        t = str(p.js(e)).replace('\u2212', '-').replace(',', '.').replace('\u00b7', ' ')
        return [float(x) for x in _re.findall(r'-?\d+(?:\.\d+)?(?:e-?\d+)?', t)]
    def num(e):
        v = nums(e)
        return v[0] if v else float('nan')
    out = {}
    p.js("activate('m1'); M1.reset(); M1.al=28; M1.render();"); time.sleep(0.3)
    out['sym'] = (num("document.getElementById('m1kxx').textContent"),
                  num("document.getElementById('m1kyy').textContent"),
                  num("document.getElementById('m1kxy').textContent"),
                  num("document.getElementById('m1kzz').textContent"))
    p.js("M1.P=[[1,0.5],[1,-0.5],[-1,0.5],[-0.4,-0.9]]; M1.al=28; M1.render();")
    time.sleep(0.3)
    pr = sorted([num("document.getElementById('m1kp1').textContent"),
                 num("document.getElementById('m1kp2').textContent")])
    out['asy'] = (num("document.getElementById('m1kxy').textContent"),
                  pr[0], pr[1], num("document.getElementById('m1kang').textContent"))
    p.js("activate('m2'); M2.ax=2; M2.w0=10; M2.reset(); M2.render();"); time.sleep(0.3)
    out['I'] = p.js("M2.Ii()")
    out['f1'] = p.js("M2.fr(1)"); out['f2'] = p.js("M2.fr(2)"); out['f3'] = p.js("M2.fr(3)")
    out['w1s'] = p.js("""(function(){M2.ax=2;M2.w0=10;M2.reset();
      const h=2e-4; for(let k=0;k<5000;k++){
        M2.y=rk4(M2.t,M2.y,h,(t,y)=>M2.f(t,y));
        const q=qnorm([M2.y[3],M2.y[4],M2.y[5],M2.y[6]]);
        M2.y[3]=q[0];M2.y[4]=q[1];M2.y[5]=q[2];M2.y[6]=q[3]; M2.t+=h;}
      return [M2.y[0],M2.y[1],M2.y[2]];})()""")
    out['drift'] = p.js("""(function(){M2.ax=2;M2.w0=10;M2.reset();
      const E0=M2.E0,M0=M2.MM0,h=2e-4; let d=0;
      for(let k=0;k<30000;k++){
        M2.y=rk4(M2.t,M2.y,h,(t,y)=>M2.f(t,y));
        const q=qnorm([M2.y[3],M2.y[4],M2.y[5],M2.y[6]]);
        M2.y[3]=q[0];M2.y[4]=q[1];M2.y[5]=q[2];M2.y[6]=q[3]; M2.t+=h;
        d=Math.max(d,Math.abs((M2.ener(M2.y)-E0)/E0),
                     Math.abs((M2.mom2(M2.y)-M0)/M0));}
      return d;})()""")
    p.js("activate('m3'); M3.pre='cusp'; M3.th0=50*DEG; M3.w3=200; M3.reset(); M3.render();")
    time.sleep(0.4)
    out['appr'] = num("document.getElementById('m3kOm').textContent")
    out['avg'] = num("document.getElementById('m3kOmex').textContent")
    out['thr'] = num("document.getElementById('m3kthr').textContent")
    out['rng'] = tuple(nums("document.getElementById('m3krange').textContent")[:2])
    out['reg'] = p.js("(function(){M3.pre='reg'; return M3.Omreg();})()")
    p.js("activate('m4'); M4.lat=50.45; M4.render();"); time.sleep(0.3)
    out['T'] = num("document.getElementById('m4kT').textContent")
    out['OF'] = num("document.getElementById('m4kOm').textContent")
    out['fullK'] = num("document.getElementById('m4kfull').textContent")
    out['fullP'] = num("document.getElementById('m4kpole').textContent")
    p.close()
    return out

def main_04():
    r, pg = ref_04(), page_04()
    for i, nm in enumerate(['I_xx', 'I_yy', 'I_xy', 'I_zz']):
        chk('м1 · прямокутник 2x1 м, %s' % nm, r['sym'][i], pg['sym'][i], 5e-4, 'кг·м²')
    for i, nm in enumerate(['I_xy', 'менший головний', 'більший головний']):
        chk('м1 · зсунута маса, %s' % nm, r['asy'][i], pg['asy'][i], 5e-4, 'кг·м²')
    chk('м1 · кут між L і ω при α = 28°', r['asy'][3], pg['asy'][3], 0.02, '°')
    for i in range(3):
        chk('м2 · головний момент I%d' % (i+1), r['I'][i], pg['I'][i], 1e-9, 'кг·м²')
    chk('м2 · частота навколо осі 1', r['f1'], pg['f1'], 5e-4, 'рад/с')
    chk('м2 · інкремент навколо осі 2', r['f2'], pg['f2'], 5e-4, 'с⁻¹')
    chk('м2 · частота навколо осі 3', r['f3'], pg['f3'], 5e-4, 'рад/с')
    for i in range(3):
        chk('м2 · ω%d через 1 с (DOP853 проти RK4)' % (i+1),
            r['w1s'][i], pg['w1s'][i], 2e-4, 'рад/с')
    ROWS.append(('м2 · дрейф E і M² за 6 с', 0.0, pg['drift'], 1e-12, '',
                 pg['drift'] < 1e-12))
    chk('м3 · Ω_пр = mgl/(I₃ω₃)', r['appr'], pg['appr'], 5e-4, 'рад/с')
    chk('м3 · середня φ̇ (quad проти Гауса–Чебишова)', r['avg'], pg['avg'], 2e-3, 'рад/с')
    chk('м3 · рівна прецесія, повільний корінь', r['reg'], pg['reg'], 5e-4, 'рад/с')
    chk('м3 · поріг стійкості вертикалі', r['thr'], pg['thr'], 5e-3, 'рад/с')
    chk('м3 · нижня межа нутації', r['rng'][0], pg['rng'][0], 0.05, '°')
    chk('м3 · верхня межа нутації', r['rng'][1], pg['rng'][1], 0.05, '°')
    chk('м4 · T = 2π√(l/g)', r['T'], pg['T'], 5e-4, 'с')
    chk('м4 · Ω_З sin φ у Києві', r['OF'], pg['OF'], 2e-3, '°/год')
    chk('м4 · повний оберт у Києві', r['fullK'], pg['fullK'], 5e-3, 'год')
    chk('м4 · повний оберт на полюсі', r['fullP'], pg['fullP'], 5e-3, 'год')
    ROWS.append(('м4 · кут площини з повних рівнянь Коріоліса через 3 год',
                 r['planeRef'], r['plane'], 0.05, '°',
                 abs(r['plane']-r['planeRef']) < 0.05))


def main():
    rel = 'Theoretical-Mechanics/03-small-oscillations.html'
    T0, r30, r90 = ref_m1()
    Tb2, slope = ref_m2()
    w1, w2, Tb3, Th3 = ref_m3()
    Oc, Ohz, wup, wdn = ref_m4()
    half, incr = ref_m5()
    pg = page_numbers(rel)

    chk('м1 · T₀ = 2π√(l/g)', T0, pg['T0'], 5e-4, 'с')
    chk('м1 · T/T₀ при θ₀ = 30°', r30, pg['r30'], 1e-4)
    chk('м1 · T/T₀ при θ₀ = 90°', r90, pg['r90'], 1e-4)
    chk('м2 · період биття при γ = 0,9ω₀', Tb2, pg['Tb2'], 5e-2, 'с')
    chk('м2 · нахил огинаючої при резонансі', slope, pg['slope'], 5e-5, 'м/с')
    chk('м3 · ω₁ = √(g/l)', w1, pg['w1'], 5e-3, 'рад/с')
    chk('м3 · ω₂ = √(g/l + 2k/m)', w2, pg['w2'], 5e-3, 'рад/с')
    chk('м3 · період биття', Tb3, pg['Tb3'], 5e-2, 'с')
    chk('м3 · повне перекачування енергії', Th3, pg['Th3'], 5e-2, 'с')
    chk('м4 · поріг Ω_c = √(2gl)/a', Oc, pg['Oc'], 0.5, 'рад/с')
    chk('м4 · той самий поріг у герцах', Ohz, pg['Ohz'], 0.05, 'Гц')
    chk('м4 · частота навколо вершини', wup, pg['wup'], 5e-3, 'рад/с')
    chk('м4 · частота навколо низу', wdn, pg['wdn'], 5e-3, 'рад/с')
    chk('м5 · напівширина зони hω₀/2', half, pg['half'], 5e-4, 'рад/с')
    chk('м5 · інкремент у центрі зони hω₀/4', incr, pg['incr'], 5e-4, 'с⁻¹')

    wf = ref_m4_full()
    ROWS.append(('м4 · повна модель проти ефективної', wup, wf,
                 0.03*wup, 'рад/с', abs(wf-wup) <= 0.03*wup))
    dref = ref_m1_drift()
    ROWS.append(('м1 · дрейф енергії за 100 періодів (еталон)', 0.0, dref, 1e-6, '', dref < 1e-6))
    ROWS.append(('м1 · дрейф енергії на сторінці', 0.0, pg['drift'], 1e-6, '', pg['drift'] < 1e-6))

    w = max(len(r[0]) for r in ROWS)
    bad = 0
    print('%-*s %14s %14s  %s' % (w, 'що', 'очікувано', 'на сторінці', 'вердикт'))
    for name, ref, got, tol, unit, ok in ROWS:
        f = lambda v: ('%.6g' % v) if abs(v) >= 1e-4 or v == 0 else ('%.3e' % v)
        print('%-*s %14s %14s  %s' % (w, name, f(ref)+' '+unit, f(got)+' '+unit,
                                      'збігається' if ok else 'РОЗБІЖНІСТЬ'))
        bad += 0 if ok else 1
    print('---- розбіжностей:', bad)
    sys.exit(1 if bad else 0)

def report():
    w = max(len(r[0]) for r in ROWS)
    bad = 0
    print('%-*s %14s %14s  %s' % (w, 'що', 'очікувано', 'на сторінці', 'вердикт'))
    for name, ref, got, tol, unit, ok in ROWS:
        f = lambda v: ('%.6g' % v) if abs(v) >= 1e-4 or v == 0 else ('%.3e' % v)
        print('%-*s %14s %14s  %s' % (w, name, f(ref)+' '+unit, f(got)+' '+unit,
                                      'збігається' if ok else 'РОЗБІЖНІСТЬ'))
        bad += 0 if ok else 1
    print('---- розбіжностей:', bad)
    sys.exit(1 if bad else 0)

if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else '03'
    if which == '00':
        main_00(); report()
    elif which == '01':
        main_01(); report()
    elif which == '02':
        main_02(); report()
    elif which == '04':
        main_04(); report()
    else:
        main()
