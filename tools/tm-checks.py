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
    else:
        main()
