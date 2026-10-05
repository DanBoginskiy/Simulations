#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Кеглі серії — в одному місці.

Було: розмір тексту прописано в кожному правилі окремо, тридцять з гаком
чисел від 10,5 до 21 px, та ще й по-різному перевизначено у двох медіазапитах.
Стало: сім змінних у :root, а медіазапит міняє самі змінні, а не правила.
Нижня межа — 13 px: дрібніше студент перестає читати підпис і пропускає його.

  python3 tools/typography.py basic_physics/09-*.html          # проба
  python3 tools/typography.py --apply physics_tasks/*.html
"""
import re,sys,glob,os

VARS = """  /* Кеглі. Правити розмір тексту всієї сторінки треба тут, а не в правилах:
     13 px — нижня межа, дрібніше підпис перестають читати. */
  --fs-base:16px;    /* основний текст, підписи величин, умова, підказка */
  --fs-sm:14.5px;    /* другорядне: кнопки, пояснення, підписи графіків */
  --fs-xs:13px;      /* найменше дозволене: бейджі, легенди, службові позначки */
  --fs-h1:22px;      /* заголовок сторінки */
  --fs-h3:15px;      /* заголовок панелі */
  --fs-tab:15px;     /* вкладка */
  --fs-fx:21px;      /* конструктор формули */
"""

# роль за селектором; перше збіжне правило виграє
ROLE = [
 (r'^\.fx$|^\.fx\b',                                  '--fs-fx'),
 (r'^h1$',                                            '--fs-h1'),
 (r'^h1 small$',                                      '--fs-sm'),
 (r'^\.tabs button$',                                 '--fs-tab'),
 (r'^\.panel h3$|^\.side \.panel>h3::after$',          '--fs-h3'),
 (r'^\.badge$|^\.legend\.sm$|^\.legend,\.legend\.sm$|'
  r'^table\.read th$|^\.hint \.lv$|^\.keyrow \.klab$|'
  r'^details\.condbox>summary::before$',               '--fs-xs'),
 (r'^html,body$|^\.caption$|^\.kv$|^\.sl>span$|^\.sl output$|'
  r'^table\.read$|^\.coords$|^\.cond$|^\.hint$|^\.rothint$|'
  r'^\.verdict$|^\.ibtn$',                             '--fs-base'),
 (r'.',                                               '--fs-sm'),
]

def role(sel):
    s=sel.strip()
    for pat,v in ROLE:
        if re.search(pat,s): return v
    return '--fs-sm'

def rewrite_block(css,inside_media):
    """Повертає (новий css, скільки правил змінено)."""
    out=[]; i=0; n=0
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}',css):
        sel,body=m.group(1),m.group(2)
        out.append(css[i:m.start()])
        v=role(sel)
        nb,k=sub_sizes(body,v,inside_media)
        n+=k
        out.append(sel+'{'+nb+'}')
        i=m.end()
    out.append(css[i:])
    return ''.join(out),n

def sub_sizes(body,v,inside_media):
    k=[0]
    def f1(m):
        k[0]+=1; return 'font-size:var(%s)'%v
    nb=re.sub(r'font-size:\s*[\d.]+px',f1,body)
    # скорочення font: 600 13px/1 sans — міняємо лише розмір
    def f2(m):
        k[0]+=1; return m.group(1)+'var(%s)'%v+m.group(3)
    nb=re.sub(r'(font:\s*(?:[^;{}]*?\s)?)([\d.]+px)(\s*(?:/|[A-Za-z"]))',f2,nb)
    return nb,k[0]

def patch(path,apply=False):
    s=open(path,encoding='utf-8').read()
    if '--fs-base' in s: return 'уже зроблено'
    a=s.index('<style>'); b=s.index('</style>')
    css=s[a+7:b]
    # 1. змінні в :root
    m=re.search(r':root\{',css)
    assert m, 'немає :root'
    css=css[:m.end()]+'\n'+VARS+css[m.end():]
    # 2. правила поза медіазапитами
    parts=re.split(r'(@media[^{]*\{)',css)
    res=[]; depth=0; total=0
    for p in parts:
        if p.startswith('@media'):
            res.append(p); depth=1; continue
        if depth:
            # усередині медіазапиту: правила, що ЗМЕНШУЮТЬ кегль, прибираємо —
            # їхню роботу тепер робить перевизначення змінних
            body,k=strip_media(p); res.append(body); total+=k; depth=0
        else:
            body,k=rewrite_block(p,False); res.append(body); total+=k
    css=''.join(res)
    # 3. медіазапити міняють самі змінні
    css=css.replace('@media (max-width:760px){',
      '@media (max-width:760px){\n  /* На вузькому екрані зменшуємо не правила, а змінні */\n'
      '  :root{--fs-base:15.5px; --fs-h1:20px; --fs-tab:14.5px; --fs-sm:14px}\n',1)
    css=css.replace('@media (max-width:480px){',
      '@media (max-width:480px){\n  :root{--fs-base:15px; --fs-sm:14px; --fs-fx:19px}\n',1)
    s=s[:a+7]+css+s[b:]
    if apply: open(path,'w',encoding='utf-8').write(s)
    return 'правил змінено: %d'%total

def strip_media(body):
    """У медіазапиті лишаємо тільки ті розміри, що БІЛЬШІ за базові."""
    k=[0]
    def f(m):
        sel,inner=m.group(1),m.group(2)
        def g(mm):
            val=float(mm.group(1))
            if val>=16: return mm.group(0)      # навмисне збільшення — лишаємо
            k[0]+=1; return ''
        inner2=re.sub(r'font-size:\s*([\d.]+)px;?',g,inner)
        inner2=re.sub(r'(font:\s*(?:[^;{}]*?\s)?)([\d.]+)px(\s*(?:/|[A-Za-z"]))',
                      lambda mm:(mm.group(0) if float(mm.group(2))>=16
                                 else (k.__setitem__(0,k[0]+1) or (mm.group(1)+'var(--fs-base)'+mm.group(3)))),inner2)
        inner2=re.sub(r';\s*;',';',inner2).strip().strip(';')
        return '' if not inner2 else sel+'{'+inner2+'}'
    out=re.sub(r'([^{}]+)\{([^{}]*)\}',f,body)
    return out,k[0]

if __name__=='__main__':
    ap='--apply' in sys.argv
    files=[]
    for a in sys.argv[1:]:
        if not a.startswith('--'): files+=sorted(glob.glob(a))
    for f in files: print('%-52s %s'%(f,patch(f,ap)))
