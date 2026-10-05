#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Знімок сцени модуля: tools/shot.py <файл> <модуль> <вихід.png> [ширина]"""
import sys,os,time
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from cdp import Page
rel,mod,out=sys.argv[1],sys.argv[2],sys.argv[3]
W=int(sys.argv[4]) if len(sys.argv)>4 else 1440
H=int(sys.argv[5]) if len(sys.argv)>5 else (900 if W>600 else 1100)
p=Page(); p.metrics(W,H,dpr=2,mobile=(W<700))
p.goto('file://'+os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),rel),1.8)
p.js("activate('%s')"%mod); time.sleep(0.8)
p.js("""(function(){const el=document.getElementById('%s');if(!el)return;
  const r=el.getBoundingClientRect(); scrollTo(0,Math.max(0,r.top+scrollY-10));})()"""%mod)
time.sleep(0.4); p.shot(out); print(out); p.close()
