#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Преизчислява данните на ME/index.html от всички снимки Sofia_*.json(.gz).

ME остава един самостоятелен файл — скриптът само подменя реда `const D={...};`
с прясно изчислен обект и освежава двата етикета с дати. Кола се брои за
преместена само ако същият регистрационен номер стои под друга фирма в
следващата снимка.
"""
import json, glob, gzip, re, io, collections

TARGET = 'ТАКСИМИ СОФИЯ ЕООД'
PAGE = 'ME/index.html'


def load(path):
    opener = gzip.open if path.endswith('.gz') else io.open
    with opener(path, 'rt', encoding='utf-8') as fh:
        data = json.load(fh)
    fleet = {}
    for op in data:
        name = (op.get('operatorName') or '').strip()
        for v in op.get('vehicles') or []:
            reg = (v.get('registerNumber') or '').strip().upper()
            if reg:
                fleet[reg] = {'op': name, 'model': (v.get('markAndModel') or '').strip()}
    return fleet


snaps = []
paths = {}
for path in glob.glob('Sofia_*.json') + glob.glob('Sofia_*.json.gz'):
    paths[path[:-3] if path.endswith('.gz') else path] = path  # .gz бие суровия
for path in [paths[k] for k in sorted(paths)]:
    m = re.search(r'(\d{4}-\d{2}-\d{2})', path)
    if not m:
        print('прескачам (няма ISO дата в името):', path)
        continue
    snaps.append((m.group(1), load(path)))

if len(snaps) < 2:
    raise SystemExit('ГРЕШКА: трябват поне две снимки')

series = [{'date': d, 'count': sum(1 for x in f.values() if x['op'] == TARGET)}
          for d, f in snaps]

intervals = []
for i in range(1, len(snaps)):
    (d0, a), (d1, b) = snaps[i - 1], snaps[i]
    moved = [(p, a[p]['op'], b[p]['op'], b[p]['model'])
             for p in a.keys() & b.keys() if a[p]['op'] != b[p]['op']]
    pairs = collections.Counter((x[1], x[2]) for x in moved)
    intervals.append({
        'from': d0, 'to': d1, 'moved': len(moved),
        'in': [{'plate': x[0], 'other': x[1], 'model': x[3]} for x in moved if x[2] == TARGET],
        'out': [{'plate': x[0], 'other': x[2], 'model': x[3]} for x in moved if x[1] == TARGET],
        'new': sum(1 for p in b.keys() - a.keys() if b[p]['op'] == TARGET),
        'gone': sum(1 for p in a.keys() - b.keys() if a[p]['op'] == TARGET),
        'top': [{'f': k[0], 't': k[1], 'n': n} for k, n in pairs.most_common(12)],
    })

payload = json.dumps({'target': TARGET, 'series': series, 'intervals': intervals},
                     ensure_ascii=False, separators=(',', ':'))

html = io.open(PAGE, encoding='utf-8').read()
new_html, n = re.subn(r'(?m)^const D=\{.*\};$', 'const D=' + payload + ';',
                      html, count=1)
if n != 1:
    raise SystemExit('ГРЕШКА: не намирам реда `const D={...};` в ' + PAGE)

# Двата етикета под числата носят дати — да не изостават от данните.
dm = lambda d: d[8:10] + '.' + d[5:7]
new_html = re.sub(r'(<b id="kNow">—</b><span>коли на )\d\d\.\d\d(</span>)',
                  lambda m: m.group(1) + dm(series[-1]['date']) + m.group(2),
                  new_html, count=1)
new_html = re.sub(r'(<b id="kYtd">—</b><span>от )\d\d\.\d\d(</span>)',
                  lambda m: m.group(1) + dm(series[0]['date']) + m.group(2),
                  new_html, count=1)

io.open(PAGE, 'w', encoding='utf-8').write(new_html)
print('ME обновена: %d снимки, %s – %s, парк %d коли'
      % (len(snaps), series[0]['date'], series[-1]['date'], series[-1]['count']))
