#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Два падащи списъка за избор на БАЗА 1 и БАЗА 2 измежду свалените снимки.

Досега сравнението беше заковано: най-старата срещу най-новата. Списъкът
вече го има от auto-discovery, така че само го показваме.
Важно: при смяна се презареждат и двете бази, в ред 1 после 2 — флаговете
НОВ / ТРЪГНАЛ / МИГРАЦИЯ се смятат чак в края на парсването на БАЗА 2 и
иначе биха останали от предишната двойка. Патчът е идемпотентен.
"""
import io, sys

PAGE = 'index.html'
MARK = 'function fillBasePickers'

CSS_OLD = "    .file-lbl input{display:none}"
CSS_NEW = """    .file-lbl input{display:none}
    .base-pick{font-size:11px;font-weight:900;color:var(--muted);padding:3px 7px;background:var(--line);border-radius:4px;display:inline-flex;align-items:center;gap:5px;white-space:nowrap}
    .base-pick select{background:var(--panel);color:var(--text);border:1px solid var(--accent);border-radius:3px;font-size:11px;font-weight:700;padding:2px 4px;max-width:120px}"""

HTML_OLD = '        <button id="resetBtn" onclick="location.reload()">RESET</button>'
HTML_NEW = """        <label class="base-pick">1<select id="sel1" onchange="pickBases()"></select></label>
        <label class="base-pick">2<select id="sel2" onchange="pickBases()"></select></label>
        <button id="resetBtn" onclick="location.reload()">RESET</button>"""

JS_OLD = "(async()=>{\n  let base=window.location.href.replace(/\\/[^\\/]*$/,'/');"
JS_NEW = """/* ================================================
   ИЗБОР НА БАЗИ измежду свалените снимки
================================================ */
let DATED=[], BASE_URL='';

function fillBasePickers(cur1,cur2){
  [['sel1',cur1],['sel2',cur2]].forEach(function(pair){
    const s=document.getElementById(pair[0]);
    if(!s) return;
    s.innerHTML='';
    DATED.forEach(function(f){          // DATED е сортиран най-нов отгоре
      const o=document.createElement('option');
      o.value=f.name;
      o.textContent=(extractDateFromFilename(f.name)||f.name).replace(' г.','');
      if(f.name===pair[1]) o.selected=true;
      s.appendChild(o);
    });
  });
}

async function pickBases(){
  const n1=document.getElementById('sel1').value;
  const n2=document.getElementById('sel2').value;
  if(!n1||!n2) return;
  if(n1===n2){ alert('Избери две различни снимки.'); return; }
  document.body.style.cursor='progress';
  await autoFetch(BASE_URL+n1,1);       // редът има значение: 1, после 2
  const ok=await autoFetch(BASE_URL+n2,2);
  document.body.style.cursor='';
  if(ok) setMode('active');
}

(async()=>{
  let base=window.location.href.replace(/\\/[^\\/]*$/,'/');"""

BOOT_OLD = """    if(dated.length>=2){
      const oldest=dated[dated.length-1]; // earliest available (e.g. March) — long baseline
      const newest=dated[0];              // most recent — current snapshot
      await autoFetch(base+oldest.name,1);"""
BOOT_NEW = """    DATED=dated; BASE_URL=base;
    if(dated.length>=2){
      const oldest=dated[dated.length-1]; // earliest available (e.g. March) — long baseline
      const newest=dated[0];              // most recent — current snapshot
      fillBasePickers(oldest.name,newest.name);
      await autoFetch(base+oldest.name,1);"""

h = io.open(PAGE, encoding='utf-8').read()

if MARK in h:
    print('вече е патчнато — нищо за правене')
    sys.exit(0)

for old, new in [(CSS_OLD, CSS_NEW), (HTML_OLD, HTML_NEW), (JS_OLD, JS_NEW), (BOOT_OLD, BOOT_NEW)]:
    if old not in h:
        print('ГРЕШКА: не намирам блока:\n' + old)
        sys.exit(1)
    h = h.replace(old, new, 1)

io.open(PAGE, 'w', encoding='utf-8').write(h)
print('патчнато: два падащи списъка за избор на бази')
