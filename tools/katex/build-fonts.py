# -*- coding: utf-8 -*-
"""Збирає самодостатній блок KaTeX: CSS із шрифтами в base64 + JS.
Шрифти вріжемо під ті гліфи, що справді трапляються у формулах серії:
кирилиці KaTeX не має зовсім, тож українські слова у формули не заходять —
вони лишаються звичайним HTML поруч."""
import re,os,base64,subprocess,sys

KEEP={'KaTeX_Main-Regular','KaTeX_Main-Bold','KaTeX_Main-Italic',
      'KaTeX_Math-Italic','KaTeX_Size1-Regular','KaTeX_Size2-Regular',
      'KaTeX_Size3-Regular','KaTeX_Size4-Regular'}
WHOLE={'KaTeX_Size1-Regular','KaTeX_Size2-Regular','KaTeX_Size3-Regular','KaTeX_Size4-Regular'}

GREEK=''.join(chr(c) for c in list(range(0x391,0x3AA))+list(range(0x3B1,0x3CA)))
MATH='−×·÷±∓≈≠≤≥≪≫√∞∝∑∫∂∇⇒→←↔°′″⊙⊗∥⊥∈∘⟨⟩…·'
ASCII=''.join(chr(c) for c in range(0x20,0x7F))
SUBSET=ASCII+GREEK+MATH+'ϑϕϖϱς∆'

def subset(src,dst):
    subprocess.run([sys.executable,'-m','fontTools.subset',src,
        '--text='+SUBSET,'--flavor=woff2','--output-file='+dst,
        '--layout-features=*','--no-hinting','--desubroutinize'],check=True,
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

css=open('katex.min.css',encoding='utf-8').read()
os.makedirs('sub',exist_ok=True)
used=set(re.findall(r'fonts/(KaTeX_[A-Za-z0-9-]+)\.woff2',css))
tot=0
for name in sorted(used):
    if name not in KEEP: continue
    src='fonts/%s.woff2'%name; dst='sub/%s.woff2'%name
    if name in WHOLE: open(dst,'wb').write(open(src,'rb').read())
    else: subset(src,dst)
    tot+=os.path.getsize(dst)
    print('%-28s %6d → %6d'%(name,os.path.getsize(src),os.path.getsize(dst)))
print('шрифтів лишилося %d, разом %d Б'%(len([n for n in used if n in KEEP]),tot))

# у CSS лишаємо тільки @font-face для залишених шрифтів, решту — геть
def facerepl(m):
    block=m.group(0)
    nm=re.search(r'fonts/(KaTeX_[A-Za-z0-9-]+)\.(woff2|woff|ttf)',block)
    if not nm or nm.group(1) not in KEEP: return ''
    name=nm.group(1)
    b64=base64.b64encode(open('sub/%s.woff2'%name,'rb').read()).decode()
    block=re.sub(r'src:[^;}]+','src:url(data:font/woff2;base64,%s) format("woff2")'%b64,block)
    return block
css2=re.sub(r'@font-face\{[^}]*\}',facerepl,css)
open('katex.inline.css','w',encoding='utf-8').write(css2)
print('CSS із шрифтами: %d Б'%len(css2.encode()))
print('JS: %d Б'%os.path.getsize('katex.min.js'))
