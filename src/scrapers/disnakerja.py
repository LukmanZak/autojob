import datetime, asyncio, re
from playwright.async_api import async_playwright
from src.models import JobPosting
from src.normalizer import parse_disnakerja_date, clean
from src.config import get_launch_kwargs

BASE = "https://www.disnakerja.com"

async def extract_apply_url(page, detail_url):
    """Cari link apply: email atau form via /download/?link=1"""
    try:
        article_txt = await page.locator("article").first.inner_text() if await page.locator("article").count()>0 else ""
        # 1. cari email di detail
        emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", article_txt)
        # filter email valid bukan contoh
        emails = [e for e in emails if not e.lower().endswith(('.png','.jpg'))]
        if emails:
            # pakai email pertama, cek APPLY NOW juga ada? email lebih spesifik
            # simpan email sebagai apply method
            return f"mailto:{emails[0]}", f"Email: {emails[0]}"
        # 2. cari APPLY NOW -> /download/ -> Link Apply
        apply_el = page.locator("a:has-text('APPLY NOW')")
        if await apply_el.count()>0:
            href = await apply_el.first.get_attribute('href')
            if href:
                if href.startswith('/'):
                    href = BASE + href
                # buka download page
                try:
                    await page.goto(href, wait_until="domcontentloaded", timeout=20000)
                    await page.wait_for_timeout(2500)
                    # di download page cari Link Apply -> /download/?link=1
                    html = await page.content()
                    m = re.search(r'href="([^"]*\/download\/\?link=\d+[^"]*)"', html)
                    if m:
                        link_apply = m.group(1)
                        if link_apply.startswith('/'):
                            link_apply = BASE + link_apply
                        return link_apply, "Form via download link"
                    # fallback: cari a di download page yang bukan disnakerja
                    links = page.locator("a")
                    for i in range(await links.count()):
                        ah = await links.nth(i).get_attribute('href')
                        if ah and ah.startswith('http') and 'disnakerja.com' not in ah and 'google.com' not in ah and 'gstatic' not in ah:
                            if any(k in ah.lower() for k in ['career','recruit','forms','bit.ly','job']):
                                return ah, f"Apply: {ah[:80]}"
                except Exception as e:
                    print(f"      apply extract err {e}")
                # fallback ke detail url
                return detail_url, ""
        return detail_url, ""
    except Exception as e:
        return detail_url, ""

async def scrape_latest(max_pages=3, headless=True):
    """Scrape Latest Update: homepage + /page/2/ + /page/3/, klik tiap PT, extract posisi + apply link."""
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
            for list_title, href in hrefs:
                try:
                    print(f"    -> detail {list_title[:45]}")
                    await page.goto(href, wait_until="domcontentloaded", timeout=30000)
                    await page.wait_for_timeout(2000)
                    # date
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
                    # company
                    company=""
                    try:
                        if await page.locator("h1").count()>0:
                            company = clean(await page.locator("h1").first.inner_text())[:80]
                    except: pass
                    if not company:
                        company = list_title[:80]
                    snippet=""
                    try:
                        if await page.locator("article p").count()>0:
                            snippet = clean(await page.locator("article p").first.inner_text())[:200]
                    except: pass
                    # apply url
                    apply_url, apply_note = await extract_apply_url(page, href)
                    # perlu kembali ke detail page karena extract_apply_url navigasi ke download
                    # setelah extract, kembali ke detail untuk extract posisi? sudah selesai, posisi extract sebelumnya sudah? 
                    # kita extract posisi setelah kembali
                    # jika apply_url pindah page, kembali dulu
                    try:
                        await page.goto(href, wait_until="domcontentloaded", timeout=20000)
                        await page.wait_for_timeout(1500)
                    except: pass
                    # positions
                    positions=[]
                    try:
                        strongs = page.locator("article strong")
                        cnt = await strongs.count()
                        for k in range(cnt):
                            txt = clean(await strongs.nth(k).inner_text())
                            if len(txt)<4 or len(txt)>80: continue
                            if "Perusahaan Lainnya" in txt or "Lowongan Kerja" in txt: continue
                            if re.search(r"(STAFF|ENGINEER|OFFICER|MANAGER|ANALYST|ADMIN|OPERATOR|TECHNICIAN|SUPERVISOR|SPECIALIST|CREW|TRAINEESHIP|RECRUITMENT|FGP)", txt, re.I):
                                txt_clean = re.sub(r"^\d+\.\s*", "", txt).strip()
                                if txt_clean and txt_clean not in positions:
                                    positions.append(txt_clean)
                    except: pass
                    if not positions:
                        positions = [list_title]
                    for pos in positions:
                        # url = apply_url jika ada, else detail href
                        job_url = apply_url if apply_url != href else href
                        # jika apply via email, buat job_id unik
                        jid = href.strip("/").split("/")[-1] + "_" + re.sub(r"\W+","_", pos[:20]).strip("_")
                        desc = snippet
                        if apply_note:
                            desc = f"{apply_note} | {snippet}"[:200]
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
                            url=job_url,
                            job_id=jid,
                            description_snippet=desc
                        ))
                    print(f"      + {len(positions)} posisi (date={posted}) apply={apply_url[:60] if apply_url!=href else 'detail'}")
                except Exception as e:
                    print(f"      detail err {e}")
                await asyncio.sleep(0.2)
        await browser.close()
    seen=set(); uniq=[]
    for j in jobs:
        k=j.url.lower() + "|" + j.title.lower()
        if k not in seen:
            seen.add(k); uniq.append(j)
    return uniq

async def scrape_one(keyword, max_pages=3, headless=True, fetch_detail=True):
    return await scrape_latest(max_pages=max_pages, headless=headless)

def scrape_disnakerja_sync(keywords=None, max_pages=3, headless=True):
    return __import__("asyncio").run(scrape_latest(max_pages=max_pages, headless=headless))

if __name__ == "__main__":
    import asyncio
    jobs = asyncio.run(scrape_latest(max_pages=1, headless=True))
    print(f"Got {len(jobs)} jobs")
    for j in jobs[:10]:
        print(j.posted_date, j.title[:50], "|", j.url[:80])
