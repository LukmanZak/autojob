import datetime, asyncio, re
from playwright.async_api import async_playwright
from src.models import JobPosting
from src.normalizer import parse_disnakerja_date, clean
from src.config import get_launch_kwargs

BASE = "https://www.disnakerja.com"
# OPSI B: Disnakerja scrape Latest Update langsung, tidak pakai keyword AI

async def scrape_latest(max_pages=3, headless=True):
    """Scrape Disnakerja Latest Update: homepage + /page/2/ + /page/3/, klik tiap PT."""
    jobs=[]
    async with async_playwright() as p:
        browser = await p.chromium.launch(**get_launch_kwargs(headless))
        ctx = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36")
        page = await ctx.new_page()
        for pg in range(1, max_pages+1):
            url = f"{BASE}/" if pg==1 else f"{BASE}/page/{pg}/"
            print(f"[disnakerja] goto {url}")
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2500)
            except Exception as e:
                print(f"goto fail {e}")
                continue
            links = page.locator("article h2 a")
            n = await links.count()
            print(f"  h2 links={n}")
            hrefs=[]
            for i in range(n):
                try:
                    href = await links.nth(i).get_attribute("href")
                    title = clean(await links.nth(i).inner_text())
                    if href and title and len(title)>=3:
                        hrefs.append((title, href))
                except: pass
            print(f"  collected {len(hrefs)} PT links")
            # klik tiap PT - detail di bawah Latest Update
            for list_title, href in hrefs:
                try:
                    print(f"    -> detail {list_title[:50]}")
                    await page.goto(href, wait_until="domcontentloaded", timeout=30000)
                    await page.wait_for_timeout(2000)
                    # Last Update date
                    date_raw=""
                    try:
                        txt_full = await page.locator("article").first.inner_text() if await page.locator("article").count()>0 else ""
                        m = re.search(r"Last Update:\s*\n?\s*(.+)", txt_full)
                        if m:
                            date_raw = m.group(1).split("\n")[0].strip()
                        if not date_raw and await page.locator("time").count()>0:
                            date_raw = await page.locator("time").first.inner_text()
                    except: pass
                    posted = parse_disnakerja_date(date_raw) if date_raw else datetime.date.today().isoformat()
                    # company dari h1
                    company=""
                    try:
                        if await page.locator("h1").count()>0:
                            company = clean(await page.locator("h1").first.inner_text())[:80]
                    except: pass
                    if not company:
                        company = list_title[:80]
                    # snippet
                    snippet=""
                    try:
                        if await page.locator("article p").count()>0:
                            snippet = clean(await page.locator("article p").first.inner_text())[:200]
                    except: pass
                    # extract posisi di bawah Latest Update: ambil semua strong yang terlihat seperti job title
                    positions=[]
                    try:
                        strongs = page.locator("article strong")
                        cnt = await strongs.count()
                        for k in range(cnt):
                            txt = clean(await strongs.nth(k).inner_text())
                            # filter
                            if len(txt)<4 or len(txt)>80: continue
                            if txt in ["DESIGNER & ENGINEER", "Perusahaan Lainnya:", "Lowongan Kerja PT Indonesia Epson Industry", "Lowongan Kerja PT"]: continue
                            if "Perusahaan Lainnya" in txt or "Lowongan Kerja" in txt: continue
                            # pattern: biasanya "1. EMC TESTING ENGINEER" atau "ENGINEERING STAFF"
                            # minimal 2 kata dan huruf besar dominan atau ada STAFF/ENGINEER/OFFICER/MANAGER
                            if re.search(r"(STAFF|ENGINEER|OFFICER|MANAGER|ANALYST|ADMIN|OPERATOR|TECHNICIAN|SUPERVISOR|SPECIALIST)", txt, re.I):
                                # bersihkan numbering "1. "
                                txt_clean = re.sub(r"^\d+\.\s*", "", txt).strip()
                                if txt_clean and txt_clean not in positions:
                                    positions.append(txt_clean)
                    except: pass
                    # fallback: jika tidak ada posisi terdeteksi, pakai title PT sebagai 1 job
                    if not positions:
                        positions = [list_title]
                    for pos in positions:
                        jobs.append(JobPosting(
                            source="disnakerja",
                            keyword="Latest Update",
                            posted_date=posted,
                            scraped_at=datetime.datetime.now().isoformat(),
                            title=pos[:120],
                            company=company,
                            location="Indonesia",
                            country="Indonesia",
                            salary="",
                            url=href,
                            job_id=href.strip("/").split("/")[-1] + "_" + re.sub(r"\W+","_", pos[:20]).strip("_"),
                            description_snippet=snippet
                        ))
                    print(f"      + {len(positions)} posisi (date={posted}) -> {[x[:30] for x in positions[:3]]}")
                except Exception as e:
                    print(f"      detail err {e}")
                await asyncio.sleep(0.3)
            # lanjut next page loop akan goto url baru
        await browser.close()
    seen=set(); uniq=[]
    for j in jobs:
        k=j.url.lower() + "|" + j.title.lower()
        if k not in seen:
            seen.add(k); uniq.append(j)
    return uniq

# compatibility untuk main.py lama (keyword search)
async def scrape_one(keyword, max_pages=3, headless=True, fetch_detail=True):
    return await scrape_latest(max_pages=max_pages, headless=headless)

def scrape_disnakerja_sync(keywords=None, max_pages=3, headless=True):
    # OPSI B: abaikan keywords, langsung latest
    return __import__("asyncio").run(scrape_latest(max_pages=max_pages, headless=headless))

if __name__ == "__main__":
    import asyncio
    jobs = asyncio.run(scrape_latest(max_pages=2, headless=True))
    print(f"Got {len(jobs)} jobs")
    for j in jobs[:15]:
        print(j.posted_date, j.title[:60], "|", j.company[:30])
