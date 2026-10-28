#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ME/index.html: подменя твърдо вписания текст за комисионните (остарял —
говореше за "свежо теглене след 13.09") с бележка, изчислена от данните.
Идемпотентен: ако старият блок го няма, не прави нищо.
"""
import io, re

PAGE = 'ME/index.html'

NEW = r"""const moves=after.reduce((a,i)=>a+i.moved,0);
const inN=after.reduce((a,i)=>a+i.in.length,0), outN=after.reduce((a,i)=>a+i.out.length,0);
const newN=after.reduce((a,i)=>a+i.new,0), goneN=after.reduce((a,i)=>a+i.gone,0);
document.getElementById('commNote').innerHTML = after.length
 ? `<b>След комисионните от 26.08</b> (снимки ${full(after[0].from)} – ${full(last.date)}): `
  +`само <b>${moves}</b> коли в цяла София са сменили фирма, от тях ${inN} към и ${outN} от ТАКСИМИ `
  +`(нето ${net>0?'+':''}${net}). Паркът на ТАКСИМИ се променя основно от нови регистрации: `
  +`${newN} нови срещу ${goneN} излезли от регистъра.`
 : 'Още няма снимка след комисионните от 26.08.';
"""

html = io.open(PAGE, encoding='utf-8').read()
pat = re.compile(r"const straddle=.*?свежо теглене след 13\.09\.`;\n", re.S)
if not pat.search(html):
    print('нищо за промяна (старият блок го няма)')
    raise SystemExit(0)
html = pat.sub(lambda m: NEW, html, count=1)
io.open(PAGE, 'w', encoding='utf-8').write(html)
print('commNote обновена')
