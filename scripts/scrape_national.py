#!/usr/bin/env python3
"""Национален scraper за публичния регистър на taxireg.infosys.bg.

Портиран от 007taxiDown.html (браузърен инструмент с cors-anywhere прокси).
GitHub Actions runner-ите имат директен мрежов достъп — прокси не е нужен,
CORS е браузърно ограничение и не важи тук.

q='' (празно поле) връща цяла България вместо филтър по град — потвърдено
от Емил. Схемата на записите е същата като досегашните Sofia_*.json файлове
(build_registry_index.py в FISHTAXI очаква точно този формат).
"""
import json
import os
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
import datetime


API = 'https://taxireg.infosys.bg/TaxiReg/api/custom/publicregister/query'
UA = 'Mozilla/5.0 (compatible; fishtaxi-registry-sync/1.0)'


def fetch_page(q, row_begin, row_end, retries=4):
    url = f'{API}?rowBegin={row_begin}&rowEnd={row_end}&q={urllib.parse.quote(q)}&sort=createdAt&order=desc'
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json'})
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read().decode('utf-8'))
            return data.get('rows', data) if isinstance(data, dict) else data
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
            last_err = e
            wait = attempt * 3
            print(f'  грешка на страница {row_begin}-{row_end} (опит {attempt}/{retries}): {e} — чакам {wait}s')
            time.sleep(wait)
    raise RuntimeError(f'страница {row_begin}-{row_end} се провали след {retries} опита: {last_err}')


def scrape(q, step, delay, max_pages=None):
    all_rows = []
    start = 1
    page = 0
    while True:
        end = start + step - 1
        records = fetch_page(q, start, end)
        if not records:
            print(f'Няма повече данни след {len(all_rows)} записа — край.')
            break
        all_rows.extend(records)
        page += 1
        print(f'страница {page}: {start}-{end} | общо: {len(all_rows)}')
        start += step
        if max_pages and page >= max_pages:
            print(f'спрях на max_pages={max_pages} (тестов режим)')
            break
        time.sleep(delay)
    return all_rows


def main():
    q = os.environ.get('SCRAPE_Q', '')  # празно = цяла България
    step = int(os.environ.get('SCRAPE_STEP', '200'))
    delay = float(os.environ.get('SCRAPE_DELAY', '0.4'))
    test_only = os.environ.get('TEST_ONLY', 'true').lower() == 'true'
    max_pages = 3 if test_only else None

    label = 'Bulgaria' if not q.strip() else q.strip()
    print(f'старт: q={q!r} ({label}), step={step}, delay={delay}s, test_only={test_only}')

    rows = scrape(q, step, delay, max_pages)
    print(f'общо събрани записи: {len(rows)}')

    if test_only:
        print('--- ТЕСТОВ РЕЖИМ: не записвам файл, само показвам мостра ---')
        if rows:
            sample = rows[0]
            print('пример за оператор:', json.dumps(sample, ensure_ascii=False)[:800])
            print('ключове:', list(sample.keys()) if isinstance(sample, dict) else type(sample))
        sys.exit(0)

    if len(rows) < 500:
        print('ПОДОЗРИТЕЛНО МАЛКО за национален обхват — не записвам')
        sys.exit(1)

    today = datetime.date.today()
    fname = f'{label}_{today.day:02d}.{today.month:02d}.{today.year}.json'
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False)
    size_mb = os.path.getsize(fname) / (1024 * 1024)
    print(f'записан {fname}: {size_mb:.1f} MB')

    if size_mb > 90:
        print('ВНИМАНИЕ: файлът е над 90 MB — риск от GitHub-ов лимит от 100 MB. '
              'Ще трябва Git LFS или разделяне по региони.')

    with open('registry-pull-report.txt', 'w', encoding='utf-8') as f:
        f.write(f'{fname}: {len(rows)} записа, {size_mb:.1f} MB, {today.isoformat()}\n')


if __name__ == '__main__':
    main()
