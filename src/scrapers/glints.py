import datetime, asyncio
from playwright.async_api import async_playwright
from src.models import JobPosting
from src.normalizer import clean
from src.config import get_launch_kwargs, DEBUG_DIR, ensure_dirs

SEARCHES = [
    ("AI Engineer", "https://glints.com/id/lowongan-kerja?keywords=AI%20Engineer&sortBy=LATEST"),
    ("Machine Learning Engineer", "https://glints.com/id/lowongan-kerja?keywords=Machine%20Learning%20Engineer&sortBy=LATEST"),
]

async def scrape_all(headless=True):
    all_jobs=[]
    async with async_playwright() as p:
        launch_kwargs = get_launch_kwargs(headless)

        browser = await p.chromium.launch(**launch_kwargs)
        for kw, url in SEARCHES:
            try:
                ctx = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36", locale="id-ID")
                page = await ctx.new_page()
                print(f"[glints] goto {url}")
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(5000)
                title = await page.title()
                print(f"  title: {title[:150]}")
                if "Firewall" in title or "Just a moment" in title:
                    print("  blocked, waiting 8s")
                    await page.wait_for_timeout(8000)
                links = page.locator("a[href*='/opportunities/jobs/']")
                cnt = await links.count()
                print(f"  total job links={cnt}")
                if cnt==0:
                    html = await page.content()
                    ensure_dirs()
                    with open(DEBUG_DIR / f"glints_{kw.replace(' ','_')}.html","w",encoding="utf-8") as f:
                        f.write(html[:20000])
                else:
                    for i in range(min(cnt, 15)):
                        a = links.nth(i)
                        try:
                            href = await a.get_attribute("href")
                            if href and href.startswith("/"):
                                href = "https://glints.com" + href
                            txt = clean(await a.inner_text())
                            parts = [p.strip() for p in txt.split("\n") if p.strip()]
                            title_txt = parts[0] if parts else txt[:80]
                            company = parts[1] if len(parts)>1 else ""
                            loc = parts[2] if len(parts)>2 else "Indonesia"
                            posted = datetime.date.today().isoformat()
                            all_jobs.append(JobPosting(source="glints", keyword=kw, posted_date=posted, scraped_at=datetime.datetime.now().isoformat(), title=title_txt[:120], company=company[:80], location=loc[:80], country="Indonesia", salary="", url=href or url, job_id=href.split("/")[-1].split("?")[0] if href else str(i), description_snippet=""))
                        except Exception as e:
                            print(f"    link {i} err {e}")
                await ctx.close()
            except Exception as e:
                print(f"[glints:{kw}] exception {e}")
                import traceback; traceback.print_exc()
                try: await ctx.close()
                except: pass
            await asyncio.sleep(1)
        await browser.close()
    return all_jobs

def scrape_glints_sync(headless=True):
    return __import__("asyncio").run(scrape_all(headless=headless))

if __name__=="__main__":
    import asyncio
    jobs=asyncio.run(scrape_all(headless=True))
    print(f"TOTAL {len(jobs)}")
    for j in jobs[:5]:
        print(j.title, j.url)
