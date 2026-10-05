#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Вбудовує KaTeX у файл серії: CSS зі шрифтами, JS і хелпер tex().

Сторінка має відкриватися з флешки без мережі, тож усе лежить усередині
документа. Шрифти — у base64 в самому CSS (див. tools/katex/README.md).

  python3 tools/katex-embed.py --apply basic_physics/09-*.html
"""
import sys,os,glob,re
HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.dirname(HERE)

HELPER = r"""
/* ---- формули -----------------------------------------------------------
   Рендерить KaTeX, вбудований у цей самий файл разом зі шрифтами: сторінка
   відкривається з флешки без мережі. Повертає рядок, щоб формулу можна було
   вставляти в будь-яку розмітку нарівні з текстом.

   Кольори ролей беремо з брендбука: tex('v=\\tfrac{s}{t}','k1') пофарбує всю
   формулу в колір першої системи відліку. Кирилиці KaTeX не має, тож
   українські слова лишаються звичайним HTML поруч із формулою — це збігається
   з правилом §4: формула символьна, одиниці й пояснення стоять після неї. */
function tex(f,role){
  const src=role?('\\textcolor{'+(CLR[role]||role)+'}{'+f+'}'):f;
  try{ return katex.renderToString(src,{throwOnError:false,displayMode:false,strict:false}); }
  catch(e){ return '<span class="texraw">'+f+'</span>'; }
}
/* Та сама формула, але одразу в елемент — для тих місць, що оновлюються
   щокадру: innerHTML там дешевший за перескладання всього рядка. */
function texTo(el,f,role){ const e=(typeof el==='string')?$(el):el; if(e) e.innerHTML=tex(f,role); }
"""

CSS_EXTRA = """
/* KaTeX лишає свій кегль відносним: прив'язуємо його до кеглю сторінки, щоб
   формула не випадала з рядка. Кирилиця в \\text{} піде системним шрифтом —
   у KaTeX її немає. */
.katex{font-size:1.06em; color:inherit}
.katex .mord.text{font-family:system-ui,-apple-system,"Segoe UI",sans-serif}
.formulas .katex,.kv .katex,.hint .katex{font-size:1.02em}
.texraw{font-family:Georgia,"Times New Roman",serif; font-style:italic}
"""

def embed(path,apply=False):
    s=open(path,encoding='utf-8').read()
    if 'katex.renderToString' in s: return 'уже вбудовано'
    css=open(os.path.join(HERE,'katex','katex.inline.css'),encoding='utf-8').read()
    js=open(os.path.join(HERE,'katex','katex.min.js'),encoding='utf-8').read()
    # 1. CSS — окремим блоком одразу після власних стилів
    i=s.index('</style>')+len('</style>')
    s=s[:i]+'\n<style id="katex-css">'+css+'</style>\n<style>'+CSS_EXTRA+'</style>'+s[i:]
    # 2. JS — перед власним скриптом
    j=s.index('<script>')
    s=s[:j]+'<script id="katex-js">'+js+'</script>\n'+s[j:]
    # 3. хелпер — одразу після CLR
    m=re.search(r'const CLR=\{[^}]*\};',s)
    assert m, 'не знайдено CLR'
    s=s[:m.end()]+'\n'+HELPER+s[m.end():]
    if apply: open(path,'w',encoding='utf-8').write(s)
    return 'вбудовано (+%d КБ)'%((len(css)+len(js))//1024)

if __name__=='__main__':
    ap='--apply' in sys.argv
    os.chdir(ROOT)
    files=[]
    for a in sys.argv[1:]:
        if not a.startswith('--'): files+=sorted(glob.glob(a))
    for f in files: print('%-52s %s'%(f,embed(f,ap)))
