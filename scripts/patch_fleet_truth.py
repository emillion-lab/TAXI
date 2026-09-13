#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
`vehicles` става източникът на истината за това коя фирма държи колата.

Установено по данните (снимка 13.09.2026):
  * `vehicles` е текущият парк — 8754 номера, само 1 дубликат за целия файл.
  * `taxiLicensesVehiclesDrivers` е лицензна история и съдържа и заминали коли:
    1387 номера стоят само там и ВСИЧКИТЕ са с изтекъл лиценз.
  * Старият код четеше само историята и излизаше, без да погледне `vehicles`.
    Резултат: 376 коли под грешна фирма (ТАКСИ-С-ЕКСПРЕС падаше от 461 на 51,
    РАДИО СВ печелеше 300 чужди), ИЗТЕКЛИ 2840 вместо 1267, МИГРАЦИЯ 132
    вместо 109.
  * За номерата под няколко фирми „последният по validTo" познава текущата
    фирма в 628 от 629 случая; „първият по ред във файла" — в 41%.
  * 21 оператора имат история без `vehicles` (43 номера). Проверени: нито
    един с валиден лиценз днес, 34 не се срещат никъде другаде. История са.

Отделно се маркира СТАРИЯТ ПЛАСТ: 1540 коли, които стоят в `vehicles`, но
нямат нито един лицензен запис под своята фирма. 94% са вписани на 08.01.2021
при първоначалното зареждане на базата, 85% са коли отпреди 2010, 96% са без
данни за собственост. Те не са „изтекли" — лиценз изобщо не им е вписван —
и затова не влизат в ОБЩО, а имат свой бутон.

Патчът е идемпотентен.
"""
import io, sys

PAGE = 'index.html'
MARK = 'legacyRegs'

SHAPE_A_OLD = """  // Shape A: taxiLicensesVehiclesDrivers (full history)
  const vList=item.taxiLicensesVehiclesDrivers;
  if(Array.isArray(vList)&&vList.length>0){
    vList.forEach(vData=>{
      const v=vData.taxiLicenseVehicle||{};
      const reg=normReg(v.registerNumber||v.regNumber||'');
      if(!reg) return;
      const model=(v.markAndModel||v.model||'—').toString().trim()||'—';
      const lic=vData.taxiLicense||{};
      const validTo=parseValidTo(lic.validTo||lic.validToDate||vData.validTo);
      const driverObj=vData.taxiLicenseDriver||{};
      const hasOwnDriver=!!(driverObj.driverName||'').trim();
      const driverName=(hasOwnDriver?driverObj.driverName:'ТИТУЛЯР').toString().trim();
      // Find matching driver entry in driverList for UVLTA info
      const specificDriver=hasOwnDriver
        ? (driverList.find(d=>d.name===driverName)||{name:driverName, uvltaNumber:'', uvltaEndDate:null, contractDate:null, forOwnAccount:false})
        : false;
      const ownership=(v.ownership||'').toLowerCase();
      const firstRegDate=parseDate(v.firstRegistrationDate);
      const licVF=parseDate(lic.validFrom);
      const licVT=parseValidTo(lic.validTo||lic.validToDate);
      processVehicle(reg, model, validTo, driverName, ownership, firstRegDate, lic.licenseNumber||'', licVF, licVT, specificDriver);
    });
    return out;
  }
"""

SHAPE_A_NEW = """  // Shape A: `vehicles` казва коя фирма държи колата ДНЕС;
  // taxiLicensesVehiclesDrivers дава лиценза, срока и шофьора към нея.
  // Лицензни редове за номера, които ги няма в `vehicles`, са история на
  // заминали коли и се пропускат — иначе колата се брои на старата фирма.
  const vList=item.taxiLicensesVehiclesDrivers;
  const fleet=item.vehicles;
  if(Array.isArray(vList)&&vList.length>0&&Array.isArray(fleet)&&fleet.length>0){
    const licByReg=new Map();
    vList.forEach(vData=>{
      const reg=normReg((vData.taxiLicenseVehicle||{}).registerNumber||(vData.taxiLicenseVehicle||{}).regNumber||'');
      if(!reg) return;
      if(!licByReg.has(reg)) licByReg.set(reg,[]);
      licByReg.get(reg).push(vData);
    });

    fleet.forEach(fv=>{
      const reg=normReg(fv.registerNumber||fv.regNumber||'');
      if(!reg) return;
      const fleetModel=(fv.markAndModel||'—').toString().trim()||'—';
      const fleetOwn=(fv.ownership||'').toLowerCase();
      const fleetFirst=parseDate(fv.firstRegistrationDate);
      const rows=licByReg.get(reg);

      if(!rows||!rows.length){
        // СТАР ПЛАСТ: кола без нито един лицензен запис под своята фирма
        legacyRegs.add(reg);
        processVehicle(reg, fleetModel, null, 'ТИТУЛЯР', fleetOwn, fleetFirst, '', null, null);
        return;
      }

      rows.forEach(vData=>{
        const v=vData.taxiLicenseVehicle||{};
        const model=(v.markAndModel||v.model||fleetModel).toString().trim()||fleetModel;
        const lic=vData.taxiLicense||{};
        const validTo=parseValidTo(lic.validTo||lic.validToDate||vData.validTo);
        const driverObj=vData.taxiLicenseDriver||{};
        const hasOwnDriver=!!(driverObj.driverName||'').trim();
        const driverName=(hasOwnDriver?driverObj.driverName:'ТИТУЛЯР').toString().trim();
        const specificDriver=hasOwnDriver
          ? (driverList.find(d=>d.name===driverName)||{name:driverName, uvltaNumber:'', uvltaEndDate:null, contractDate:null, forOwnAccount:false})
          : false;
        const ownership=(v.ownership||fleetOwn||'').toLowerCase();
        const firstRegDate=parseDate(v.firstRegistrationDate)||fleetFirst;
        const licVF=parseDate(lic.validFrom);
        const licVT=parseValidTo(lic.validTo||lic.validToDate);
        processVehicle(reg, model, validTo, driverName, ownership, firstRegDate, lic.licenseNumber||'', licVF, licVT, specificDriver);
      });
    });
    return out;
  }
"""

STATE_OLD = "let slot2SeenRegs=new Set(); // regs already refreshed during the current \u0411\u0410\u0417\u0410 2 parse"
STATE_NEW = ("let slot2SeenRegs=new Set(); // regs already refreshed during the current \u0411\u0410\u0417\u0410 2 parse\n"
             "let legacyRegs=new Set();    // \u0421\u0422\u0410\u0420 \u041f\u041b\u0410\u0421\u0422 \u2014 \u043a\u043e\u043b\u0438 \u0431\u0435\u0437 \u043d\u0438\u0442\u043e \u0435\u0434\u0438\u043d \u043b\u0438\u0446\u0435\u043d\u0437\u0435\u043d \u0437\u0430\u043f\u0438\u0441 \u043f\u043e\u0434 \u0441\u0432\u043e\u044f\u0442\u0430 \u0444\u0438\u0440\u043c\u0430")

CLEAR_OLD = "  loadingSlot=slot;\n  slot2SeenRegs.clear();"
CLEAR_NEW = "  loadingSlot=slot;\n  slot2SeenRegs.clear();\n  legacyRegs.clear();"

FLAG_OLD = """    } else {
      raw.forEach(car=>{ car.isNew=false; car.isMigrated=false; });
    }
  }
"""
FLAG_NEW = """    } else {
      raw.forEach(car=>{ car.isNew=false; car.isMigrated=false; });
    }
    raw.forEach((car,reg)=>{ car.isLegacy=legacyRegs.has(reg); });
  }
"""

APPLY_OLD = """  const all=Array.from(raw.values());          // current fleet (\u0411\u0410\u0417\u0410 2 only)
  const goneAll=Array.from(goneCars.values()); // departed since \u0411\u0410\u0417\u0410 1 (reference only)
"""
APPLY_NEW = """  // \u0421\u0442\u0430\u0440\u0438\u044f\u0442 \u043f\u043b\u0430\u0441\u0442 \u0441\u0442\u043e\u0438 \u043d\u0430\u0441\u0442\u0440\u0430\u043d\u0438: \u0442\u0435\u0437\u0438 \u043a\u043e\u043b\u0438 \u043d\u044f\u043c\u0430\u0442 \u043b\u0438\u0446\u0435\u043d\u0437\u0435\u043d \u0437\u0430\u043f\u0438\u0441, \u0437\u0430\u0442\u043e\u0432\u0430
  // \u043d\u0435 \u043c\u043e\u0433\u0430\u0442 \u0434\u0430 \u0431\u044a\u0434\u0430\u0442 \u043d\u0438\u0442\u043e \u0432\u0430\u043b\u0438\u0434\u043d\u0438, \u043d\u0438\u0442\u043e \u0438\u0437\u0442\u0435\u043a\u043b\u0438 \u2014 \u0438 \u043d\u0435 \u0432\u043b\u0438\u0437\u0430\u0442 \u0432 \u041e\u0411\u0429\u041e.
  const everything=Array.from(raw.values());
  const all=everything.filter(c=>!c.isLegacy);  // current fleet (\u0411\u0410\u0417\u0410 2 only)
  const oldAll=everything.filter(c=>c.isLegacy);
  const goneAll=Array.from(goneCars.values()); // departed since \u0411\u0410\u0417\u0410 1 (reference only)
"""

SALL_OLD = "  document.getElementById('sAll').textContent  =raw.size;"
SALL_NEW = ("  document.getElementById('sAll').textContent  =all.length;\n"
            "  const oldEl=document.getElementById('sOld');\n"
            "  if(oldEl) oldEl.textContent=oldAll.length;")

SRC_OLD = "  const sourceList=(fMode==='gone')?goneAll:all;"
SRC_NEW = "  const sourceList=(fMode==='gone')?goneAll:(fMode==='old')?oldAll:all;"

MODE_OLD = "    if(fMode==='gone')      return true; // already the gone-only list"
MODE_NEW = ("    if(fMode==='gone')      return true; // already the gone-only list\n"
            "    if(fMode==='old')       return true; // already the legacy-only list")

DEN_OLD = """  const denom=(fMode==='gone')?goneAll.length
             :(fMode==='migration')?migAll
             :(fMode==='new')?newAll
             :raw.size;"""
DEN_NEW = """  const denom=(fMode==='gone')?goneAll.length
             :(fMode==='old')?oldAll.length
             :(fMode==='migration')?migAll
             :(fMode==='new')?newAll
             :all.length;"""

IDS_OLD = "  const ids={all:'fAll',active:'fAct',expired:'fExp',soon:'fSoon',new:'fNew',gone:'fGone',migration:'fMig'};"
IDS_NEW = "  const ids={all:'fAll',active:'fAct',expired:'fExp',soon:'fSoon',new:'fNew',gone:'fGone',migration:'fMig',old:'fOld'};"

HTML_OLD = """    <div class="stat-item" id="fMig"><span class="stat-val" id="sMig" style="color:var(--blue)">0</span><span class="stat-lbl" style="color:var(--blue)" data-bg="\u21c4 \u041c\u0418\u0413\u0420\u0410\u0426\u0418\u042f" data-en="\u21c4 MIGRATED">\u21c4 \u041c\u0418\u0413\u0420\u0410\u0426\u0418\u042f</span></div>"""
HTML_NEW = """    <div class="stat-item" id="fMig"><span class="stat-val" id="sMig" style="color:var(--blue)">0</span><span class="stat-lbl" style="color:var(--blue)" data-bg="\u21c4 \u041c\u0418\u0413\u0420\u0410\u0426\u0418\u042f" data-en="\u21c4 MIGRATED">\u21c4 \u041c\u0418\u0413\u0420\u0410\u0426\u0418\u042f</span></div>
    <div class="stat-item" id="fOld"><span class="stat-val" id="sOld" style="color:var(--muted)">0</span><span class="stat-lbl" style="color:var(--muted)" data-bg="\u231b \u0421\u0422\u0410\u0420 \u041f\u041b\u0410\u0421\u0422" data-en="\u231b LEGACY">\u231b \u0421\u0422\u0410\u0420 \u041f\u041b\u0410\u0421\u0422</span></div>"""

# --- предпазване от липсваща дата ---
# Колите от стария пласт нямат validTo. На три места кодът викаше
# c.validTo.toLocaleDateString() без проверка и щеше да гръмне при рендиране.
CSS_TAG_OLD = "    .v-err{background:rgba(239,68,68,0.15);color:var(--red);border:1px solid var(--red)}"
CSS_TAG_NEW = ("    .v-err{background:rgba(239,68,68,0.15);color:var(--red);border:1px solid var(--red)}\n"
               "    .v-old{background:rgba(148,163,184,0.15);color:var(--muted);border:1px solid var(--muted)}")

CARD1_OLD = """          const tagClass=act?(soon?'v-warn':'v-ok'):'v-err';
          const tagText=act?(soon?t.expSoon:t.valid):t.expired_on;"""
CARD1_NEW = """          const tagClass=!c.validTo?'v-old':(act?(soon?'v-warn':'v-ok'):'v-err');
          const tagText=!c.validTo?(lang==='bg'?'\u0411\u0415\u0417 \u041b\u0418\u0426\u0415\u041d\u0417':'NO LICENCE'):(act?(soon?t.expSoon:t.valid):t.expired_on);"""

CARD2_OLD = """    const tagClass=act?(soon?'v-warn':'v-ok'):'v-err';
    const tagText=act?(soon?t.expSoon:t.valid):t.expired_on;"""
CARD2_NEW = """    const tagClass=!c.validTo?'v-old':(act?(soon?'v-warn':'v-ok'):'v-err');
    const tagText=!c.validTo?(lang==='bg'?'\u0411\u0415\u0417 \u041b\u0418\u0426\u0415\u041d\u0417':'NO LICENCE'):(act?(soon?t.expSoon:t.valid):t.expired_on);"""

DATE1_OLD = """<div class="v-tag ${tagClass}" style="font-size:9px;">${tagText} ${c.validTo.toLocaleDateString('bg-BG')}</div>"""
DATE1_NEW = """<div class="v-tag ${tagClass}" style="font-size:9px;">${tagText} ${c.validTo?c.validTo.toLocaleDateString('bg-BG'):''}</div>"""

DATE2_OLD = """      <div class="v-tag ${tagClass}">${tagText} ${c.validTo.toLocaleDateString('bg-BG')}</div>"""
DATE2_NEW = """      <div class="v-tag ${tagClass}">${tagText} ${c.validTo?c.validTo.toLocaleDateString('bg-BG'):''}</div>"""

ST_OLD = """  const statusText=act?(soon?t.expSoon:t.valid):t.expired_on;
  statusEl.textContent=statusText+' '+c.validTo.toLocaleDateString('bg-BG');
  statusEl.style.color=act?(soon?'var(--highlight)':'var(--accent)'):'var(--red)';"""
ST_NEW = """  const statusText=!c.validTo?(lang==='bg'?'\u0411\u0415\u0417 \u041b\u0418\u0426\u0415\u041d\u0417\u0415\u041d \u0417\u0410\u041f\u0418\u0421':'NO LICENCE ON RECORD')
                   :(act?(soon?t.expSoon:t.valid):t.expired_on);
  statusEl.textContent=c.validTo?(statusText+' '+c.validTo.toLocaleDateString('bg-BG')):statusText;
  statusEl.style.color=!c.validTo?'var(--muted)':(act?(soon?'var(--highlight)':'var(--accent)'):'var(--red)');"""


# Shape B се стига само от оператори без лицензна история (29 фирми, 181 коли).
# Те са същият стар пласт: 96% вписани на 08.01.2021, 90% коли отпреди 2010.
# Без това те оставаха в живия слой с празна дата и се броят за „изтекли".
SHAPEB_OLD = """      const ownership=(v.ownership||vData.ownership||'').toLowerCase();
      const firstRegDate=parseDate(v.firstRegistrationDate||vData.firstRegistrationDate);
      processVehicle(reg, model, validTo, driverName, ownership, firstRegDate, '', null, null);"""
SHAPEB_NEW = """      const ownership=(v.ownership||vData.ownership||'').toLowerCase();
      const firstRegDate=parseDate(v.firstRegistrationDate||vData.firstRegistrationDate);
      if(!validTo) legacyRegs.add(reg);
      processVehicle(reg, model, validTo, driverName, ownership, firstRegDate, '', null, null);"""

LISTEN_OLD = "document.getElementById('fMig').addEventListener('click',()=>{if(base1Loaded)setMode('migration');});"
LISTEN_NEW = ("document.getElementById('fMig').addEventListener('click',()=>{if(base1Loaded)setMode('migration');});\n"
              "document.getElementById('fOld').addEventListener('click',()=>setMode('old'));")

h = io.open(PAGE, encoding='utf-8').read()

if MARK in h:
    print('\u0432\u0435\u0447\u0435 \u0435 \u043f\u0430\u0442\u0447\u043d\u0430\u0442\u043e \u2014 \u043d\u0438\u0449\u043e \u0437\u0430 \u043f\u0440\u0430\u0432\u0435\u043d\u0435')
    sys.exit(0)

edits = [(SHAPE_A_OLD, SHAPE_A_NEW), (STATE_OLD, STATE_NEW), (CLEAR_OLD, CLEAR_NEW),
         (FLAG_OLD, FLAG_NEW), (APPLY_OLD, APPLY_NEW), (SALL_OLD, SALL_NEW),
         (SRC_OLD, SRC_NEW), (MODE_OLD, MODE_NEW), (DEN_OLD, DEN_NEW),
         (IDS_OLD, IDS_NEW), (HTML_OLD, HTML_NEW), (LISTEN_OLD, LISTEN_NEW),
         (CSS_TAG_OLD, CSS_TAG_NEW), (CARD1_OLD, CARD1_NEW), (CARD2_OLD, CARD2_NEW),
         (DATE1_OLD, DATE1_NEW), (DATE2_OLD, DATE2_NEW), (ST_OLD, ST_NEW),
         (SHAPEB_OLD, SHAPEB_NEW)]

for i, (old, new) in enumerate(edits, 1):
    if old not in h:
        print('\u0413\u0420\u0415\u0428\u041a\u0410 \u043d\u0430 \u0431\u043b\u043e\u043a %d:\n%s' % (i, old[:200]))
        sys.exit(1)
    h = h.replace(old, new, 1)

io.open(PAGE, 'w', encoding='utf-8').write(h)
print('\u043f\u0430\u0442\u0447\u043d\u0430\u0442\u043e: vehicles \u0435 \u0438\u0441\u0442\u0438\u043d\u0430\u0442\u0430, \u0441\u0442\u0430\u0440\u0438\u044f\u0442 \u043f\u043b\u0430\u0441\u0442 \u0435 \u043e\u0442\u0434\u0435\u043b\u0435\u043d')
