#!/usr/bin/env python3
"""Национален scraper за публичния регистър на taxireg.infosys.bg.

ДИАГНОСТИЧНА ВЕРСИЯ: винаги пише debug.txt с резолвнатите env стойности
и резултата от първата страница, преди каквото и да е разклонение по
test_only. Правя това, защото няма пряк достъп до Actions логовете оттук —
debug.txt е единственият начин да видя какво реално се случва вътре.
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
    last_raw = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read().decode('utf-8')
                last_raw = raw[:500]
                data = json.loads(raw)
            return (data.get('rows', data) if isinstance(data, dict) else data), url, last_raw, None
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
            last_err = e
            wait = attempt * 3
            time.sleep(wait)
    return None, url, last_raw, str(last_err)


def scrape(q, step, delay, max_pages, debug_lines):
    all_rows = []
    start = 1
    page = 0
    while True:
        end = start + step - 1
        records, url, raw_sample, err = fetch_page(q, start, end)
        if page == 0:
            debug_lines.append(f'първа заявка URL: {url}')
            debug_lines.append(f'първи 500 символа отговор: {raw_sample!r}')
            debug_lines.append(f'грешка (ако има): {err!r}')
        if err and records is None:
            debug_lines.append(f'СПРЯХ на страница {page+1} заради грешка: {err}')
            break
        if not records:
            debug_lines.append(f'Няма повече данни след {len(all_rows)} записа — край на страница {page+1}.')
            break
        all_rows.extend(records)
        page += 1
        start += step
        if max_pages and page >= max_pages:
            debug_lines.append(f'спрях на max_pages={max_pages} (тестов режим)')
            break
        time.sleep(delay)
    return all_rows


def main():
    debug_lines = []
    q = os.environ.get('SCRAPE_Q', '')
    step_raw = os.environ.get('SCRAPE_STEP', '200')
    delay_raw = os.environ.get('SCRAPE_DELAY', '0.4')
    test_only_raw = os.environ.get('TEST_ONLY', 'true')

    debug_lines.append(f'RAW ENV: TEST_ONLY={test_only_raw!r} SCRAPE_Q={q!r} SCRAPE_STEP={step_raw!r} SCRAPE_DELAY={delay_raw!r}')

    step = int(step_raw)
    delay = float(delay_raw)
    test_only = test_only_raw.strip().lower() == 'true'
    max_pages = 3 if test_only else None

    label = 'Bulgaria' if not q.strip() else q.strip()
    debug_lines.append(f'резолвнато: test_only={test_only}, label={label}, step={step}, delay={delay}, max_pages={max_pages}')

    rows = scrape(q, step, delay, max_pages, debug_lines)
    debug_lines.append(f'общо събрани записи: {len(rows)}')

    # винаги пиша debug.txt, независимо от режима
    with open('debug.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(debug_lines) + '\n')

    if test_only:
        debug_lines.append('--- ТЕСТОВ РЕЖИМ: не записвам основния файл ---')
        with open('debug.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(debug_lines) + '\n')
        sys.exit(0)

    if len(rows) < 500:
        debug_lines.append('ПОДОЗРИТЕЛНО МАЛКО за национален обхват — не записвам основния файл')
        with open('debug.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(debug_lines) + '\n')
        sys.exit(0)  # не failure - искам debug.txt да се commit-не за диагностика

    today = datetime.date.today()
    fname = f'{label}_{today.day:02d}.{today.month:02d}.{today.year}.json'
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False)
    size_mb = os.path.getsize(fname) / (1024 * 1024)
    debug_lines.append(f'записан {fname}: {size_mb:.1f} MB')

    with open('debug.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(debug_lines) + '\n')
    with open('registry-pull-report.txt', 'w', encoding='utf-8') as f:
        f.write(f'{fname}: {len(rows)} записа, {size_mb:.1f} MB, {today.isoformat()}\n')


if __name__ == '__main__':
    main()
