#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1) scripts/build_me.py: смяната на фирма се хваща и когато колата липсва в
   междинна снимка (регистърът отразява смяната със закъснение). Досега такава
   кола се броеше като "излязла" + "нова" и смяната се губеше.
2) ME/index.html: по-подробна бележка за комисионните, изчислена от данните,
   и белег "след пропуск" до колите, хванати по този начин.
Идемпотентен: втори пуск не променя нищо.
"""
import io, re

BUILD = 'scripts/build_me.py'
PAGE = 'ME/index.html'

# ---------------- 1) build_me.py ----------------
NEW_LOOP = r"""intervals = []
from datetime import date
GAP_DAYS = 60              # колко време колата може да липсва, а смяната пак да се брои
last = dict(snaps[0][1])   # последно познат оператор за всеки номер
seen = set(last)           # номера, виждани в кое да е по-ранно състояние
last_seen = {p: snaps[0][0] for p in last}   # дата на последното виждане
for i in range(1, len(snaps)):
    (d0, a), (d1, b) = snaps[i - 1], snaps[i]
    # смяна = номерът е под друга фирма от последния път, когато е виждан —
    # дори да е липсвал в междинна снимка (последният флаг = "след пропуск")
    def gap_ok(p):   # липсвала е в предишната снимка, но не твърде отдавна
        return (date.fromisoformat(d1) - date.fromisoformat(last_seen[p])).days <= GAP_DAYS
    moved = [(p, last[p]['op'], b[p]['op'], b[p]['model'], p not in a)
             for p in b if p in last and last[p]['op'] != b[p]['op'] and (p in a or gap_ok(p))]
    pairs = collections.Counter((x[1], x[2]) for x in moved)
    intervals.append({
        'from': d0, 'to': d1, 'moved': len(moved),
        'gap': sum(1 for x in moved if x[4]),
        'in': [{'plate': x[0], 'other': x[1], 'model': x[3], 'gap': x[4]} for x in moved if x[2] == TARGET],
        'out': [{'plate': x[0], 'other': x[2], 'model': x[3], 'gap': x[4]} for x in moved if x[1] == TARGET],
        'new': sum(1 for p in b.keys() - a.keys() if b[p]['op'] == TARGET and p not in seen),
        'gone': sum(1 for p in a.keys() - b.keys() if a[p]['op'] == TARGET),
        'top': [{'f': k[0], 't': k[1], 'n': n} for k, n in pairs.most_common(12)],
    })
    seen |= set(b)
    last.update(b)
    for p in b: last_seen[p] = d1
"""

bs = io.open(BUILD, encoding='utf-8').read()
if "'gap': sum(1 for x in moved if x[4])" in bs:
    print('build_me.py: вече е patch-нат')
else:
    pat = re.compile(r"intervals = \[\]\nfor i in range\(1, len\(snaps\)\):.*?\n\n(?=payload = )", re.S)
    if not pat.search(bs):
        raise SystemExit('ГРЕШКА: не намирам цикъла за intervals в ' + BUILD)
    bs = pat.sub(lambda m: NEW_LOOP + '\n', bs, count=1)
    io.open(BUILD, 'w', encoding='utf-8').write(bs)
    print('build_me.py: patch-нат')

# ---------------- 2) ME/index.html ----------------
NOTE = r"""const days=(Date.parse(last.date)-Date.parse(after[0].from))/864e5;
const moves=after.reduce((a,i)=>a+i.moved,0);
const gapN=after.reduce((a,i)=>a+(i.gap||0),0);
const inN=after.reduce((a,i)=>a+i.in.length,0), outN=after.reduce((a,i)=>a+i.out.length,0);
const newN=after.reduce((a,i)=>a+i.new,0), goneN=after.reduce((a,i)=>a+i.gone,0);
const sg=n=>(n>0?'+':'')+n;
const short=s=>s.replace(/ +(ЕООД|ООД|АД|ЕТ)$/,'');
const before=IV.filter(i=>i.to<=COMM);
const bDays=before.length?(Date.parse(before[before.length-1].to)-Date.parse(before[0].from))/864e5:0;
const rBefore=bDays?before.reduce((a,i)=>a+i.moved,0)/bDays*30:null;
const rAfter=moves/days*30;
const cmp=rBefore===null?'':(rAfter<rBefore*0.75?'по-нисък от':rAfter>rBefore*1.25?'по-висок от':'близък до')
  +' този преди 26.08 (около '+Math.round(rBefore)+' на месец)';
const cp={};
after.forEach(i=>{
  i.in.forEach(m=>{(cp[m.other]=cp[m.other]||{i:0,o:0}).i++;});
  i.out.forEach(m=>{(cp[m.other]=cp[m.other]||{i:0,o:0}).o++;});
});
const cpTop=Object.entries(cp).sort((x,y)=>(y[1].i+y[1].o)-(x[1].i+x[1].o)).slice(0,3);
const flows={};
after.forEach(i=>i.top.forEach(p=>{const k=short(p.f)+' → '+short(p.t);flows[k]=(flows[k]||0)+p.n;}));
const flowTop=Object.entries(flows).sort((x,y)=>y[1]-x[1]).slice(0,3);
const startCnt=(S.find(p=>p.date===after[0].from)||first).count, dFleet=last.count-startCnt;
const P=t=>'<p style="margin:0 0 9px">'+t+'</p>';
document.getElementById('commNote').innerHTML = !after.length
 ? 'Още няма снимка след комисионните от 26.08.'
 : P(`<b>Какво се случи след комисионните от 26.08?</b> Сравнени са ${after.length} снимки между ${full(after[0].from)} и ${full(last.date)} (${Math.round(days)} дни). `
    +`В цяла София само <b>${moves}</b> коли са сменили фирма — около ${Math.round(rAfter)} на месец, темп ${cmp}. `
    +(rBefore!==null&&rAfter>rBefore*1.25?`Движението е по-интензивно от преди — виж посоките по-долу.`:`Масов преход на коли между фирми не се вижда.`))
  +P(`<b>ТАКСИМИ:</b> получила е ${inN} коли от други фирми и е дала ${outN} (нето ${sg(net)}). `
    +(cpTop.length?`Най-често обменът е с ${cpTop.map(([n,v])=>short(n)+' ('+v.i+' дошли, '+v.o+' отишли)').join(', ')}.`:''))
  +(flowTop.length?P(`<b>Най-чести посоки в целия пазар:</b> ${flowTop.map(([k,n])=>k+' — '+n).join('; ')}.`):'')
  +P(`<b>Откъде идва ръстът:</b> паркът на ТАКСИМИ се е променил с ${sg(dFleet)} (${startCnt} → ${last.count}), а смените между фирми дават само нето ${sg(net)}. `
    +`Основно е от нови регистрации (${newN} коли, невиждани в нито една предишна снимка) срещу отписвания (${goneN} коли са изчезнали от регистъра); малка част са коли, върнали се в регистъра под същата фирма.`)
  +P(`<b>Как да се чете:</b> регистърът отразява смяната на фирма със закъснение — колата може да изчезне от старата фирма в една снимка и да се появи в новата чак в следваща. `
    +`Такива случаи също се броят като смяна (${gapN} от ${moves}), ако колата липсва най-много 60 дни, и са белязани „след пропуск“ — затова няколко от тях може да са станали малко преди 26.08. `
    +`Кола, която просто е изчезнала, е отписана, а не прехвърлена. Снимките са през около две седмици, затова смяна и връщане между две снимки не се виждат. `
    +`Регистърът показва фирмата, не шофьора — шофьор, който сменя фирмата си с едно и също возило, не се вижда.`);
"""

html = io.open(PAGE, encoding='utf-8').read()
changed = False

# бележката: от първото `const moves=` до края на присвояването на commNote
if 'const gapN=' in html:
    print('ME: бележката вече е подробна')
else:
    pat = re.compile(r"const moves=after\.reduce.*?document\.getElementById\('commNote'\)\.innerHTML.*?;\n(?=\n/\* ---- периоди)", re.S)
    if not pat.search(html):
        raise SystemExit('ГРЕШКА: не намирам блока на commNote в ' + PAGE)
    html = pat.sub(lambda m: NOTE, html, count=1)
    changed = True

# белег "след пропуск" до колата
OLD_ROW = "${m.model||''}</span></span></div>`"
NEW_ROW = "${m.model||''}${m.gap?' · появила се след пропуск в регистъра':''}</span></span></div>`"
if NEW_ROW in html:
    print('ME: белегът за пропуск вече е добавен')
elif OLD_ROW in html:
    html = html.replace(OLD_ROW, NEW_ROW, 1)
    changed = True
else:
    raise SystemExit('ГРЕШКА: не намирам реда row() в ' + PAGE)

if changed:
    io.open(PAGE, 'w', encoding='utf-8').write(html)
    print('ME: patch-нат')
