#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
index.html: списъкът със снимки идва първо от манифест snapshots.json (същият
сайт), после от GitHub API. Резервните имена във файла (Sofia_24.03.2026.json,
taxi_data_Sofia29.08.2026.json) вече не съществуват — при отказ на API панелът
оставаше празен без съобщение. Сега при пълен провал има ясно съобщение.
Идемпотентен.
"""
import io, sys

PAGE = 'index.html'
html = io.open(PAGE, encoding='utf-8').read()
if 'async function listFiles' in html:
    print('вече е patch-нат'); sys.exit(0)

FUNC = """/* Списък със снимките: първо манифестът snapshots.json от същия сайт (без
   лимит на заявките), после GitHub API (неудостоверените заявки към него са
   ограничени на час за IP адрес). Манифестът се обновява от registry-pull. */
async function listFiles(base){
  try{
    const r=await fetch(base+'snapshots.json?v='+Date.now());
    if(r.ok){
      const names=await r.json();
      if(Array.isArray(names)&&names.length) return names.map(n=>({type:'file',name:String(n)}));
    }
  }catch(e){ console.warn('[manifest]',e.message); }
  const apiRes=await fetch('https://api.github.com/repos/emillion-lab/TAXI/contents/');
  if(!apiRes.ok) throw new Error('GitHub API '+apiRes.status);
  return await apiRes.json();
}

"""
ANCHOR = "(async()=>{\n  let base=window.location.href"
OLD_API = """    const apiRes=await fetch('https://api.github.com/repos/emillion-lab/TAXI/contents/');
    if(!apiRes.ok) throw new Error('GitHub API '+apiRes.status);
    const files=await apiRes.json();
"""
NEW_API = "    const files=await listFiles(base);\n"
OLD_FB = """  // Fallback if GitHub API is unreachable/rate-limited
  await autoFetch(base+'Sofia_24.03.2026.json',1);
  const ok=await autoFetch(base+'taxi_data_Sofia29.08.2026.json',2);
  if(ok) setMode('active');
"""
NEW_FB = """  // И манифестът, и GitHub API са недостъпни — стари имена на файлове вече няма.
  alert('Не мога да заредя снимките на регистъра. Опитай пак след малко или качи два файла ръчно (БАЗА 1 и БАЗА 2).');
"""
for name, old in (('anchor', ANCHOR), ('api', OLD_API), ('fallback', OLD_FB)):
    if html.count(old) != 1:
        print('ГРЕШКА: не намирам точно веднъж блока', name); sys.exit(1)
html = html.replace(ANCHOR, FUNC + ANCHOR, 1).replace(OLD_API, NEW_API, 1).replace(OLD_FB, NEW_FB, 1)
io.open(PAGE, 'w', encoding='utf-8').write(html)
print('patch-нат')
