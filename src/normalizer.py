import re, datetime

def parse_disnakerja_date(raw: str) -> str:
    raw=raw.strip().lower()
    today=datetime.date.today()
    # handle "2 days ago", "5 hours ago", "2025-09-01"
    m=re.search(r"(\d+)\s+days? ago", raw)
    if m:
        d=today-datetime.timedelta(days=int(m.group(1)))
        return d.isoformat()
    m=re.search(r"(\d+)\s+hours? ago", raw)
    if m:
        return today.isoformat()
    m=re.search(r"(\d{4}-\d{2}-\d{2})", raw)
    if m:
        return m.group(1)
    # try dd month yyyy
    for fmt in ["%d %B %Y","%B %d, %Y","%d %b %Y"]:
        try:
            return datetime.datetime.strptime(raw, fmt).date().isoformat()
        except: pass
    return today.isoformat()

def clean(s):
    return re.sub(r"\s+"," ", s).strip()
