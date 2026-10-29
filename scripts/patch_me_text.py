#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ME/index.html: в бележката "Сравнени са N снимки" N беше броят на интервалите,
а не на снимките (между N интервала има N+1 снимки). Идемпотентен.
"""
import io, sys

PAGE = 'ME/index.html'
OLD = 'Сравнени са ${after.length} снимки между'
NEW = 'Сравнени са ${after.length+1} снимки между'

html = io.open(PAGE, encoding='utf-8').read()
if NEW in html:
    print('вече е поправено')
elif OLD in html:
    io.open(PAGE, 'w', encoding='utf-8').write(html.replace(OLD, NEW, 1))
    print('поправено')
else:
    print('ГРЕШКА: не намирам фразата в ' + PAGE); sys.exit(1)
