"""Поправя фалшивата дата 1.01.2000 в TAXI.

parseValidTo() връщаше new Date(2000,0,1) на четири места — при липсваща
стойност, при неразпознат формат и при година под 1900. После isActive()
сравняваше тази дата с днешната, тя естествено излизаше в миналото, и
интерфейсът показваше "ИЗТЕКЪЛ НА 1.01.2000 г." за коли, чийто лиценз
изобщо не е прекратен. В самия регистър тези оператори нямат terminationDate
— полето просто липсва.

Липсата на дата и изтеклият лиценз са различни неща и не бива да изглеждат
еднакво: първото значи "не знаем", второто значи "проверено и невалидно".

Поправката:
  · parseValidTo връща null при липсваща или негодна стойност
  · isActive/isExpiringSoon се пазят от null — липсваща дата не е "активен"
  · сравненията e.validTo > x.validTo се пазят от null
  · formatDate вече показва "—", което покрива и този случай
"""
import io, re

src = io.open('index.html', encoding='utf-8').read()
count = 0

def rep(old, new):
    global src, count
    c = src.count(old)
    assert c == 1, 'MARKER x%d: %r' % (c, old[:70])
    src = src.replace(old, new); count += 1

rep("""function parseValidTo(value){
  if(!value) return new Date(2000,0,1,0,0,0,0);
  if(typeof value==='string'){
    const m=value.match(/^(\\d{4})-(\\d{2})-(\\d{2})/);
    if(m){
      const y=+m[1];
      if(y<1900) return new Date(2000,0,1,0,0,0,0); // guard bad dates (e.g. year 13)
      return new Date(y,+m[2]-1,+m[3],23,59,59,999);
    }
  }
  const dt=new Date(value);
  if(isNaN(dt.getTime())) return new Date(2000,0,1,0,0,0,0);
  const y=dt.getFullYear();
  if(y<1900) return new Date(2000,0,1,0,0,0,0);
  return new Date(y,dt.getMonth(),dt.getDate(),23,59,59,999);
}""",
"""/* Липсваща дата и изтекъл лиценз са различни неща. Преди тук се връщаше
   1.01.2000, което после излизаше като "ИЗТЕКЪЛ НА 1.01.2000 г." за коли,
   чийто лиценз изобщо не е прекратен — в регистъра полето просто липсва.
   Сега липсата е null и се показва като "—". */
function parseValidTo(value){
  if(!value) return null;
  if(typeof value==='string'){
    const m=value.match(/^(\\d{4})-(\\d{2})-(\\d{2})/);
    if(m){
      const y=+m[1];
      if(y<1900) return null;              // негодна дата (напр. година 13)
      return new Date(y,+m[2]-1,+m[3],23,59,59,999);
    }
  }
  const dt=new Date(value);
  if(isNaN(dt.getTime())) return null;
  const y=dt.getFullYear();
  if(y<1900) return null;
  return new Date(y,dt.getMonth(),dt.getDate(),23,59,59,999);
}
/* По-късната от две дати, като null се смята за "няма". */
function laterDate(a,b){
  if(!a) return b || null;
  if(!b) return a;
  return a>b ? a : b;
}""")

rep("""function isActive(validTo){ return validTo>=todayStart; }
function isExpiringSoon(validTo){ return validTo>=todayStart&&validTo<=in30; }""",
"""/* Без дата не значи "активен" — значи "неизвестно". И в двата случая
   колата не бива да се брои за валидна, но и не бива да се показва
   като изтекла. */
function isActive(validTo){ return !!validTo && validTo>=todayStart; }
function isExpiringSoon(validTo){ return !!validTo && validTo>=todayStart&&validTo<=in30; }
function isExpired(validTo){ return !!validTo && validTo<todayStart; }""")

# сравненията, които биха се счупили при null
src = src.replace("if(!hist.slot1||e.validTo>hist.slot1.validTo)",
                  "if(!hist.slot1||(e.validTo&&laterDate(e.validTo,hist.slot1.validTo)===e.validTo))")
src = src.replace("if(!hist.slot2||e.validTo>hist.slot2.validTo)",
                  "if(!hist.slot2||(e.validTo&&laterDate(e.validTo,hist.slot2.validTo)===e.validTo))")
src = src.replace("if(e.validTo>ex.validTo) ex.validTo=e.validTo;",
                  "ex.validTo=laterDate(e.validTo,ex.validTo);")
count += 1

io.open('index.html', 'w', encoding='utf-8').write(src)
print('PATCHED %d blocks OK' % count)
