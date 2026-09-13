#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Еднократна конверсия: снимките на регистъра стават .json.gz.

Причината е GitHub Pages, не git — Pages сервира разопакованото дърво и
таванът му е 1 GB. Една снимка пада от ~19 MB на ~1.3 MB. Печели се и
мобилният трафик, защото панелът тегли две бази при всяко отваряне.
Скриптът е идемпотентен: вече конвертирани файлове се прескачат.
"""
import glob, gzip, os, shutil

done = 0
for path in sorted(glob.glob('Sofia_*.json') + glob.glob('Bulgaria_*.json')):
    out = path + '.gz'
    if os.path.exists(out):
        print('вече има', out, '— махам само оригинала')
        os.remove(path)
        done += 1
        continue
    with open(path, 'rb') as src, gzip.GzipFile(out, 'wb', compresslevel=9, mtime=0) as dst:
        shutil.copyfileobj(src, dst)
    before, after = os.path.getsize(path), os.path.getsize(out)
    os.remove(path)
    print('%s: %.1f MB -> %.1f MB' % (path, before / 1048576.0, after / 1048576.0))
    done += 1

print('конвертирани:', done) if done else print('няма какво да се конвертира')
