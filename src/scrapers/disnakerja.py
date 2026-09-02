import datetime, re, asyncio
from playwright.async_api import async_playwright
from src.models import JobPosting
from src.normalizer import parse_disnakerja_date, clean

CHROME_PATH = r"C:/Users/ASUS/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe"
BASE = "https://www.disnakerja.com"

KEYWORDS = ["AI Engineer", "Machine Learning Engineer", "Machine Learning"]

async def scrape_one(keyword, max_pages=3, headless=True):
    jobs=[]
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, executable_path=CHROME_PATH, args=["--no-sandbox","--disable-blink-features=AutomationControlled"])
        ctx = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36")
        page = await ctx.new_page()
        for pg in range(1, max_pages+1):
            url = f"{BASE}/?s={keyword.replace(' ', '+')}" + (f"&paged={pg}" if pg>1 else "")
            print(f"[disnakerja] goto {url}")
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2500)
            except Exception as e:
                print(f"goto fail {e}")
                continue
            # detect no results
            content = await page.content()
            # parse via locators
            articles = page.locator("article, .post, h2 a")
            count = await articles.count()
            print(f"  found locators count={count}")
            # better: query all h2 a inside search results
            links = page.locator("h2 a, h2.entry-title a, article h2 a")
            n = await links.count()
            print(f"  h2 links={n}")
            for i in range(n):
                try:
                    a = links.nth(i)
                    title = clean(await a.inner_text())
                    href = await a.get_attribute("href")
                    if not href or not title or len(title)<5:
                        continue
                    # filter relevance: must contain AI/Machine Learning or Engineer? keep all then filter later? keep if contains keyword fragment
                    # We'll keep all, orchestrator will not filter disnakerja strictly
                    # find card container for date
                    # try closest article's time
                    card = a.locator("xpath=ancestor::article[1]")
                    date_raw=""
                    try:
                        time_el = card.locator("time, .entry-meta, .post-date")
                        if await time_el.count()>0:
                            date_raw = await time_el.first.inner_text()
                    except: pass
                    if not date_raw:
                        # try sibling
                        date_raw = "" 
                    posted = parse_disnakerja_date(date_raw) if date_raw else datetime.date.today().isoformat()
                    # company: try to extract after "-" or just title
                    company = ""
                    if " - " in title:
                        company = title.split(" - ")[-1]
                    snippet=""
                    try:
                        p_el = card.locator("p")
                        if await p_el.count()>0:
                            snippet = clean(await p_el.first.inner_text())[:200]
                    except: pass
                    jobs.append(JobPosting(
                        source="disnakerja",
                        keyword=keyword,
                        posted_date=posted,
                        scraped_at=datetime.datetime.now().isoformat(),
                        title=title,
                        company=company,
                        location="Indonesia",
                        country="Indonesia",
                        salary="",
                        url=href,
                        job_id=href.strip("/").split("/")[-1],
                        description_snippet=snippet
                    ))
                except Exception as e:
                    print(f"    parse i={i} err {e}")
            # check if pagination exists for next page
            has_next = await page.locator("a.next, .next.page-numbers").count()
            if has_next==0 and pg>=1:
                # heuristic: if n==0 break
                if n==0:
                    break
        await browser.close()
    # dedup inside
    seen=set()
    uniq=[]
    for j in jobs:
        k=j.url.lower()
        if k not in seen:
            seen.add(k); uniq.append(j)
    return uniq

def scrape_disnakerja_sync(keywords=None, max_pages=3, headless=True):
    if keywords is None:
        keywords=KEYWORDS
    all_jobs=[]
    for kw in keywords:
        jobs= __import__("asyncio").run(scrape_one(kw, max_pages=max_pages, headless=headless))
        all_jobs.extend(jobs)
    return all_jobs

if __name__ == "__main__":
    import asyncio
    jobs = asyncio.run(scrape_one("AI Engineer", max_pages=2, headless=True))
    print(f"Got {len(jobs)} jobs")
    for j in jobs[:5]:
        print(j.posted_date, j.title, j.url)
