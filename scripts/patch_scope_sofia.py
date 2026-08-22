#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAXI е софийско репо. Auto-discovery четеше всеки .json в корена, затова
националният Bulgaria_13.08.2026.json се избираше за БАЗА 2 и се сравняваше
със софийски baseline — резултат: всяка кола извън София излизаше "★ НОВ".

Патчът стеснява откриването само до файлове със "Sofia"/"София" в името.
Националните файлове могат да си стоят в корена — просто се игнорират.

Идемпотентен: втори run не прави нищо.
"""
import io, sys

PATH = 'index.html'

OLD = "      .filter(f=>f.type==='file'&&/\\.json$/i.test(f.name))"
NEW = ("      // TAXI = само София. Национални файлове (Bulgaria_*.json) стоят в корена,\n"
       "      // но НЕ участват в сравнението — иначе всичко извън София става \"НОВ\".\n"
       "      .filter(f=>f.type==='file'&&/\\.json$/i.test(f.name)&&/(sofia|софия)/i.test(f.name))")

h = io.open(PATH, encoding='utf-8').read()

if '/(sofia|софия)/i.test(f.name)' in h:
    print('already applied')
    sys.exit(0)

if h.count(OLD) != 1:
    print('ANCHOR NOT FOUND (matches: %d) — index.html е променян, патчът не се прилага' % h.count(OLD))
    sys.exit(1)

h = h.replace(OLD, NEW)
io.open(PATH, 'w', encoding='utf-8').write(h)
print('patched: auto-discovery вече приема само Sofia/София файлове')
