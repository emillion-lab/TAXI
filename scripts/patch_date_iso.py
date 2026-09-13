#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Дати от имена на файлове: ISO се разпознава ПРЪВ.

Старият ред пробваше D.M.Y преди ISO. За 'Sofia_2026-09-01.json' регексът
захапваше '26-09-01' и връщаше 26.9.2001, а за '...08-29' -> 26.8.2029.
Заради тези фалшиви години auto-discovery сортираше 29.08 като най-нов
файл, а 01.09 падаше най-отдолу. Патчът е идемпотентен.
"""
import io, sys

OLD = """  const m1=fname.match(/(\\d{1,2})[._-](\\d{1,2})[._-](\\d{4}|\\d{2})/);
  if(m1){
    let y=m1[3];
    if(y.length===2) y='20'+y; // assume 2000s
    return `${+m1[1]}.${+m1[2]}.${y} г.`;
  }
  const m2=fname.match(/(\\d{4})[._-](\\d{1,2})[._-](\\d{1,2})/);
  if(m2) return `${+m2[3]}.${+m2[2]}.${m2[1]} г.`;
"""

NEW = """  // ISO ПЪРВО: 'Sofia_2026-09-01.json'. Ако D.M.Y върви пръв, той захапва
  // '26-09-01' и връща 26.9.2001 — оттам и грешното сортиране на базите.
  const iso=fname.match(/(\\d{4})[._-](\\d{1,2})[._-](\\d{1,2})(?!\\d)/);
  if(iso) return `${+iso[3]}.${+iso[2]}.${iso[1]} г.`;
  const m1=fname.match(/(\\d{1,2})[._-](\\d{1,2})[._-](\\d{4}|\\d{2})(?!\\d)/);
  if(m1){
    let y=m1[3];
    if(y.length===2) y='20'+y; // assume 2000s
    return `${+m1[1]}.${+m1[2]}.${y} г.`;
  }
"""

h = io.open('index.html', encoding='utf-8').read()

if 'ISO ПЪРВО' in h:
    print('вече е патчнато — нищо за правене')
    sys.exit(0)

if OLD not in h:
    print('ГРЕШКА: не намирам очаквания блок в extractDateFromFilename')
    sys.exit(1)

io.open('index.html', 'w', encoding='utf-8').write(h.replace(OLD, NEW, 1))
print('патчнато: extractDateFromFilename чете ISO пръв')
