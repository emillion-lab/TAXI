#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Старите прототипи (index2..5, index-fetch) не се поддържат: нищо не сочи към тях,
зареждат несъществуващи Sofia.json/Sofia2.json и предхождат поправките на
главния панел (ISO датите, Shape A, .gz). Не ги трия — слагам ясен банер,
за да не бъдат взети за актуален калкулатор. Идемпотентен.
"""
import io, re, sys

FILES = ['index2.html', 'index3.html', 'index4.html', 'index5.html', 'index-fetch.html']
BANNER = ('<div data-legacy-banner style="background:#7c2d12;color:#fff;padding:10px 14px;'
          'font:700 14px/1.4 system-ui,sans-serif;text-align:center">'
          'ОСТАРЯЛА ВЕРСИЯ — не се поддържа и може да дава грешни числа. '
          'Ползвай <a href="./" style="color:#fde68a">главния панел</a>.</div>')

bad = 0
for f in FILES:
    try:
        html = io.open(f, encoding='utf-8').read()
    except FileNotFoundError:
        print(f, ': няма такъв файл'); continue
    if 'data-legacy-banner' in html:
        print(f, ': банерът вече е сложен'); continue
    new, n = re.subn(r'(<body[^>]*>)', lambda m: m.group(1) + '\n' + BANNER, html, count=1)
    if n != 1:
        print(f, ': ГРЕШКА — няма <body>'); bad += 1; continue
    io.open(f, 'w', encoding='utf-8').write(new)
    print(f, ': банер добавен')
sys.exit(1 if bad else 0)
