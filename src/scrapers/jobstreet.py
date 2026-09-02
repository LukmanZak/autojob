import datetime, re, asyncio
from playwright.async_api import async_playwright
from src.models import JobPosting
from src.normalizer import clean
from src.config import get_launch_kwargs, DEBUG_DIR, ensure_dirs

# Tetap pakai id.jobstreet.com, location ganti via ?where=
SEARCH_CONFIGS = [
    ("Malaysia-AI", "https://id.jobstreet.com/id/ai-engineer-jobs?where=Malaysia", "Malaysia"),
    ("Malaysia-ML", "https://id.jobstreet.com/id/machine-learning-engineer-jobs?where=Malaysia", "Malaysia"),
    ("Singapore-ML", "https://id.jobstreet.com/id/machine-learning-engineer-jobs?where=Singapore", "Singapore"),
    ("Australia-ML", "https://id.jobstreet.com/id/machine-learning-engineer-jobs?where=Australia", "Australia"),
    ("Singapore-AI", "https://id.jobstreet.com/id/ai-engineer-jobs?where=Singapore", "Singapore"),
]

async def scrape_one_config(keyword_label, url, country_hint, headless=True):
    jobs=[]
    async with async_playwright() as p:
        launch_kwargs = get_launch_kwargs(headless)
        browser = await p.chromium.launch(**launch_kwargs)
        ctx = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36", locale="id-ID")
        page = await ctx.new_page()
        try:
            print(f"[jobstreet:{country_hint}] goto {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(6000)
            title = await page.title()
            print(f"  title: {title[:120]} -> {page.url[:80]}")
            if "Just a moment" in title or "Checking" in title or "Tunggu sebentar" in title:
                print("  cloudflare/cek sebentar, waiting 8s")
                await page.wait_for_timeout(8000)
                title = await page.title()
                print(f"  title2: {title[:120]}")
            selectors = ["[data-automation='jobCard']", "article", "div[data-testid='job-card']", "a[data-automation='jobTitle']"]
            found=False
            for sel in selectors:
                c = await page.locator(sel).count()
                print(f"  sel {sel} count={c}")
                if c>0:
                    found=True
                    break
            if not found:
                html = await page.content()
                print(f"  no cards, html len {len(html)}")
                ensure_dirs()
                with open(DEBUG_DIR / f"jobstreet_{country_hint}.html","w",encoding="utf-8") as f:
                    f.write(html)
            else:
                cards = page.locator("[data-automation='jobCard']")
                cnt = await cards.count()
                if cnt==0:
                    cards = page.locator("a[data-automation='jobTitle']")
                    cnt = await cards.count()
                    for i in range(min(cnt, 15)):
                        a = cards.nth(i)
                        try:
                            title_txt = clean(await a.inner_text())
                            href = await a.get_attribute("href")
                            if href and href.startswith("/"):
                                href = "https://id.jobstreet.com" + href
                            loc=""
                            try:
                                loc_el = page.locator("[data-automation='jobLocation']").nth(i)
                                if await loc_el.count()>0:
                                    loc = clean(await loc_el.inner_text())
                            except: pass
                            if "india" in loc.lower() or "india" in title_txt.lower():
                                print(f"    skip india {title_txt}")
                                continue
                            jobs.append(JobPosting(
                                source="jobstreet",
                                keyword=keyword_label,
                                posted_date=datetime.date.today().isoformat(),
                                scraped_at=datetime.datetime.now().isoformat(),
                                title=title_txt,
                                company="",
                                location=loc or country_hint,
                                country=country_hint,
                                salary="",
                                url=href or url,
                                job_id=href.split("/")[-1].split("?")[0].split("#")[0] if href else str(i),
                                description_snippet=""
                            ))
                        except Exception as e:
                            print(f"    title parse err {e}")
                else:
                    for i in range(min(cnt, 15)):
                        c = cards.nth(i)
                        try:
                            t_el = c.locator("[data-automation='jobTitle']").first
                            title_txt = clean(await t_el.inner_text()) if await t_el.count()>0 else clean(await c.inner_text())[:80]
                            href = await t_el.get_attribute("href") if await t_el.count()>0 else ""
                            if href and href.startswith("/"):
                                href = "https://id.jobstreet.com" + href
                            comp=""
                            comp_el = c.locator("[data-automation='jobCompany']").first
                            if await comp_el.count()>0:
                                comp = clean(await comp_el.inner_text())
                            loc=""
                            loc_el = c.locator("[data-automation='jobLocation']").first
                            if await loc_el.count()>0:
                                loc = clean(await loc_el.inner_text())
                            date_raw=""
                            date_el = c.locator("[data-automation='jobListingDate']").first
                            if await date_el.count()>0:
                                date_raw = await date_el.inner_text()
                            posted = datetime.date.today().isoformat()
                            if "hour" in date_raw.lower() or "today" in date_raw.lower():
                                posted = datetime.date.today().isoformat()
                            elif "day" in date_raw.lower():
                                m=re.search(r"(\d+)", date_raw)
                                if m:
                                    posted=(datetime.date.today()-datetime.timedelta(days=int(m.group(1)))).isoformat()
                            if "india" in loc.lower() or "india" in comp.lower():
                                continue
                            jobs.append(JobPosting(source="jobstreet", keyword=keyword_label, posted_date=posted, scraped_at=datetime.datetime.now().isoformat(), title=title_txt, company=comp, location=loc or country_hint, country=country_hint, salary="", url=href or url, job_id=href.split("/")[-1].split("?")[0].split("#")[0] if href else str(i), description_snippet=""))
                        except Exception as e:
                            print(f"    card {i} err {e}")
        except Exception as e:
            print(f"[jobstreet:{country_hint}] exception {e}")
            import traceback; traceback.print_exc()
        finally:
            await browser.close()
    return jobs

async def scrape_all(headless=True):
    all_jobs=[]
    for label, url, country in SEARCH_CONFIGS:
        jobs = await scrape_one_config(label, url, country, headless=headless)
        print(f"  -> {label} got {len(jobs)}")
        all_jobs.extend(jobs)
        await asyncio.sleep(1)
    filtered = [j for j in all_jobs if "india" not in j.country.lower() and "india" not in j.location.lower()]
    return filtered

def scrape_jobstreet_sync(headless=True):
    return __import__("asyncio").run(scrape_all(headless=headless))

if __name__=="__main__":
    import asyncio
    jobs=asyncio.run(scrape_all(headless=True))
    print(f"TOTAL {len(jobs)}")
    for j in jobs[:5]:
        print(j.country, j.title, j.url)
