#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Панелът се научава да чете `.json.gz`.

Разопаковането е по магическите байтове 1f 8b, а не по разширението: ако
някой сървър сам свали Content-Encoding, буферът вече е чист JSON и кодът
не се задавя. Патчът е идемпотентен.
"""
import io, sys

PAGE = 'index.html'
MARK = 'async function bufToJson'

HELPER = """/* Чете .json и .json.gz. Разпознава gzip по магическите байтове 1f 8b —
   ако сървърът вече е разопаковал (Content-Encoding), буферът е чист JSON. */
async function bufToJson(buf){
  const u8=new Uint8Array(buf);
  if(u8.length>1&&u8[0]===0x1f&&u8[1]===0x8b){
    if(typeof DecompressionStream==='undefined')
      throw new Error('Браузърът не поддържа DecompressionStream');
    const s=new Blob([u8]).stream().pipeThrough(new DecompressionStream('gzip'));
    return JSON.parse(await new Response(s).text());
  }
  return JSON.parse(new TextDecoder('utf-8').decode(u8));
}

async function autoFetch(url,slot){"""

EDITS = [
    ('async function autoFetch(url,slot){', HELPER),
    ('    const json=JSON.parse(await res.text());',
     '    const json=await bufToJson(await res.arrayBuffer());'),
    ('  const json=JSON.parse(await file.text());',
     '  const json=await bufToJson(await file.arrayBuffer());'),
    ("      .filter(f=>f.type==='file'&&/\\.json$/i.test(f.name)&&/(sofia|софия)/i.test(f.name))",
     "      .filter(f=>f.type==='file'&&/\\.json(\\.gz)?$/i.test(f.name)&&/(sofia|софия)/i.test(f.name))"),
    ('<input type="file" id="file1" accept=".json">',
     '<input type="file" id="file1" accept=".json,.gz">'),
    ('<input type="file" id="file2" accept=".json">',
     '<input type="file" id="file2" accept=".json,.gz">'),
]

h = io.open(PAGE, encoding='utf-8').read()

if MARK in h:
    print('вече е патчнато — нищо за правене')
    sys.exit(0)

for old, new in EDITS:
    if old not in h:
        print('ГРЕШКА: не намирам блока:\n' + old)
        sys.exit(1)
    h = h.replace(old, new, 1)

io.open(PAGE, 'w', encoding='utf-8').write(h)
print('патчнато: панелът чете .json.gz')
