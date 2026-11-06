/* engine/integrators.js — чисельні інтегратори з фіксованим кроком.

   rk4 і verlet — дослівно з Theoretical-Mechanics/ (8 файлів, один варіант),
   сигнатури ті самі, щоб міграція тих файлів нічого не змінила:
     rk4(t, y, h, f)       → новий y;     f(t, y) повертає dy/dt (масив);
     verlet(q, v, h, acc)  → [q1, v1];    acc(q) — прискорення (скаляр).
   Решта — для систем із кількома координатами і для тестів:
     euler(t, y, h, f)           явний Ейлер — НЕ зберігає енергію;
     eulerCromer(q, v, h, acc)   напівнеявний (симплектичний) Ейлер;
     verletN / eulerCromerN      те саме для масивів координат;
     advance(…)                  розбиває кадр dt на підкроки ≤ hMax, щоб
                                 результат не залежав від частоти кадрів.
   Тести і допуски: tests/unit/integrators.test.js, tests/TOLERANCES.md. */

export function rk4(t,y,h,f){
  const k1=f(t,y);
  const k2=f(t+h/2,y.map((v,i)=>v+h/2*k1[i]));
  const k3=f(t+h/2,y.map((v,i)=>v+h/2*k2[i]));
  const k4=f(t+h,  y.map((v,i)=>v+h*k3[i]));
  return y.map((v,i)=>v+h/6*(k1[i]+2*k2[i]+2*k3[i]+k4[i]));
}

/* Швидкісний Верле: q₁ = q + v·h + a₀h²/2, v₁ = v + (a₀ + a₁)·h/2.
   Симплектичний і оборотний у часі: енергія коливається біля сталого
   значення з амплітудою ~h², але не дрейфує. */
export function verlet(q,v,h,acc){
  const a0=acc(q);
  const q1=q+v*h+0.5*a0*h*h;
  return [q1, v+0.5*(a0+acc(q1))*h];
}

/* Явний Ейлер: похідну беруть на початку кроку. Для коливань кожен крок
   множить енергію на (1 + ω²h²) — вона росте експоненційно. */
export function euler(t,y,h,f){
  const k=f(t,y);
  return y.map((v,i)=>v+h*k[i]);
}

/* Ейлер–Кромер (симплектичний Ейлер): спершу швидкість, потім координата
   вже з новою швидкістю. Перший порядок точності, але енергія обмежена. */
export function eulerCromer(q,v,h,acc){
  const v1=v+h*acc(q);
  return [q+h*v1, v1];
}

export function verletN(q,v,h,acc){
  const a0=acc(q);
  const q1=q.map((x,i)=>x+v[i]*h+0.5*a0[i]*h*h);
  const a1=acc(q1);
  return [q1, v.map((x,i)=>x+0.5*(a0[i]+a1[i])*h)];
}

export function eulerCromerN(q,v,h,acc){
  const a=acc(q);
  const v1=v.map((x,i)=>x+h*a[i]);
  return [q.map((x,i)=>x+h*v1[i]), v1];
}

/* Пройти інтервал dt підкроками не довшими за hMax: step(t, y, h, f) — будь-який
   інтегратор із сигнатурою rk4/euler. Повертає [t, y] у кінці інтервалу. */
export function advance(t,y,dt,hMax,f,step=rk4){
  let rem=dt;
  while(rem>1e-12){const h=Math.min(hMax,rem); y=step(t,y,h,f); t+=h; rem-=h;}
  return [t,y];
}
