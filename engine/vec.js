/* engine/vec.js — тривимірні вектори як масиви [x,y,z].

   Тексти — дослівно з Analytic-Geometry/ (15 файлів, один варіант). Чистий
   модуль без DOM: його імпортують і тести (момент імпульсу в задачі Кеплера). */
export const v3add=(a,b)=>[a[0]+b[0],a[1]+b[1],a[2]+b[2]];

export const v3sub=(a,b)=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]];

export const v3mul=(a,k)=>[a[0]*k,a[1]*k,a[2]*k];

export const v3dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];

export const v3cross=(a,b)=>[a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];

export const v3len=a=>Math.hypot(a[0],a[1],a[2]);

export function v3norm(a){const L=v3len(a); return L<1e-12?[0,0,0]:v3mul(a,1/L);}

/* z-компонента векторного добутку двох плоских векторів: момент імпульсу
   L = x·vy − y·vx для руху в площині. */
export const cross2=(a,b)=>a[0]*b[1]-a[1]*b[0];
