#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Подрежда избора на бази: всеки падащ списък застава до своя бутон.

Два проблема, които се видяха на телефон:
1) Списъците се пренареждаха на нов ред и „1" се озоваваше до БАЗА 2.
   Сега всяка двойка бутон + списък е на свой ред.
2) Датите се изписваха 1.9.2026 и 29.8.2026 — без водеща нула подредбата
   изглежда разбъркана, макар че е правилна. Сега са 01.09.2026.
Патчът е идемпотентен.
"""
import io, sys

PAGE = 'index.html'
MARK = 'class="io-row"'

CSS_OLD = """    .io-zone{display:flex;gap:6px;align-items:center;flex-wrap:wrap}"""
CSS_NEW = """    .io-zone{display:flex;flex-direction:column;gap:5px;align-items:flex-end}
    .io-row{display:flex;gap:6px;align-items:center}"""

PICK_OLD = """    .base-pick{font-size:11px;font-weight:900;color:var(--muted);padding:3px 7px;background:var(--line);border-radius:4px;display:inline-flex;align-items:center;gap:5px;white-space:nowrap}
    .base-pick select{background:var(--panel);color:var(--text);border:1px solid var(--accent);border-radius:3px;font-size:11px;font-weight:700;padding:2px 4px;max-width:120px}"""
PICK_NEW = """    .base-sel{background:var(--panel);color:var(--text);border:1px solid var(--accent);border-radius:4px;font-size:11px;font-weight:700;padding:4px 6px;font-variant-numeric:tabular-nums}"""

HTML_OLD = """        <label class="file-lbl" id="l1">📂 <span id="lbl1txt">БАЗА 1</span><input type="file" id="file1" accept=".json,.gz"></label>
        <label class="file-lbl" id="l2">📂 <span id="lbl2txt">БАЗА 2</span><input type="file" id="file2" accept=".json,.gz"></label>
        <label class="base-pick">1<select id="sel1" onchange="pickBases()"></select></label>
        <label class="base-pick">2<select id="sel2" onchange="pickBases()"></select></label>"""
HTML_NEW = """        <div class="io-row">
          <label class="file-lbl" id="l1">📂 <span id="lbl1txt">БАЗА 1</span><input type="file" id="file1" accept=".json,.gz"></label>
          <select id="sel1" class="base-sel" onchange="pickBases()"></select>
        </div>
        <div class="io-row">
          <label class="file-lbl" id="l2">📂 <span id="lbl2txt">БАЗА 2</span><input type="file" id="file2" accept=".json,.gz"></label>
          <select id="sel2" class="base-sel" onchange="pickBases()"></select>
        </div>"""

JS_OLD = """      o.textContent=(extractDateFromFilename(f.name)||f.name).replace(' г.','');"""
JS_NEW = """      const dt=new Date(f.ts), pad=function(n){return n<10?'0'+n:''+n;};
      o.textContent=pad(dt.getDate())+'.'+pad(dt.getMonth()+1)+'.'+dt.getFullYear();"""

h = io.open(PAGE, encoding='utf-8').read()

if MARK in h:
    print('вече е патчнато — нищо за правене')
    sys.exit(0)

for old, new in [(CSS_OLD, CSS_NEW), (PICK_OLD, PICK_NEW), (HTML_OLD, HTML_NEW), (JS_OLD, JS_NEW)]:
    if old not in h:
        print('ГРЕШКА: не намирам блока:\n' + old)
        sys.exit(1)
    h = h.replace(old, new, 1)

io.open(PAGE, 'w', encoding='utf-8').write(h)
print('патчнато: списъците са до бутоните си, датите с водеща нула')
