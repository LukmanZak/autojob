import asyncio, datetime, re, csv, pathlib, sys
from playwright.async_api import async_playwright

# Stealth import (optional)
try:
    from playwright_stealth import stealth_async
    HAS_STEALTH = True
except ImportError:
    HAS_STEALTH = False
    print("[warn] playwright-stealth not available, falling back to plain")

from src.config import get_launch_kwargs, DEBUG_DIR, ensure_dirs, DATA_DIR
from src.models import JobPosting
from src.normalizer import clean
from src.csv_writer import write_csv, deduplicate

SEARCH_CONFIGS = [
    ("Malaysia-AI", "https://id.jobstreet.com/id/ai-engineer-jobs?where=Malaysia", "Malaysia"),
    ("Malaysia-ML", "https://id.jobstreet.com/id/machine-learning-engineer-jobs?where=Malaysia", "Malaysia"),
    ("Singapore-ML", "https://id.jobstreet.com/id/machine-learning-engineer-jobs?where=Singapore", "Singapore"),
    ("Australia-ML", "https://id.jobstreet.com/id/machine-learning-engineer-jobs?where=Australia", "Australia"),
    ("Singapore-AI", "https://id.jobstreet.com/id/ai-engineer-jobs?where=Singapore", "Singapore"),
]

async def scrape_one(page, label, url, country_hint):
    jobs=[]
    try:
        print(f"[jobstreet:{label}] goto {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(6000)
        title = await page.title()
        print(f"  title: {title[:120]} -> {page.url[:120]}")
        if "Just a moment" in title or "Checking" in title or "Tunggu sebentar" in title or "Firewall" in title:
            print("  Cloudflare detected, waiting 8s")
            await page.wait_for_timeout(8000)
            title = await page.title()
            print(f"  title2: {title[:120]}")
            if "Just a moment" in title or "Checking" in title:
                print(f"  FAIL Cloudflare block for {label}")
                return [], f"Cloudflare block: {title[:80]}"
        # selectors check
        selectors = ["[data-automation='jobCard']", "article", "a[data-automation='jobTitle']"]
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
            with open(DEBUG_DIR / f"jobstreet_{label}.html","w",encoding="utf-8") as f:
                f.write(html)
            return [], "no cards found"
        # try jobCard path
        cards = page.locator("[data-automation='jobCard']")
        cnt = await cards.count()
        if cnt==0:
            # fallback to title links
            cards = page.locator("a[data-automation='jobTitle']")
            cnt = await cards.count()
            print(f"  fallback title links cnt={cnt}")
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
                        continue
                    jobs.append(JobPosting(
                        source="jobstreet", keyword=label,
                        posted_date=datetime.date.today().isoformat(),
                        scraped_at=datetime.datetime.now().isoformat(),
                        title=title_txt, company="", location=loc or country_hint,
                        country=country_hint, salary="", url=href or url,
                        job_id=href.split("/")[-1].split("?")[0].split("#")[0] if href else str(i),
                        description_snippet=""
                    ))
                except Exception as e:
                    print(f"    title parse err {e}")
        else:
            print(f"  jobCard cnt={cnt}")
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
                    if "day" in date_raw.lower():
                        m=re.search(r"(\d+)", date_raw)
                        if m:
                            posted=(datetime.date.today()-datetime.timedelta(days=int(m.group(1)))).isoformat()
                    if "india" in loc.lower() or "india" in comp.lower():
                        continue
                    jobs.append(JobPosting(source="jobstreet", keyword=label, posted_date=posted, scraped_at=datetime.datetime.now().isoformat(), title=title_txt, company=comp, location=loc or country_hint, country=country_hint, salary="", url=href or url, job_id=href.split("/")[-1].split("?")[0].split("#")[0] if href else str(i), description_snippet=""))
                except Exception as e:
                    print(f"    card {i} err {e}")
        return jobs, None
    except Exception as e:
        import traceback; traceback.print_exc()
        return [], str(e)

async def main():
    ensure_dirs()
    all_jobs=[]
    errors={}
    async with async_playwright() as p:
        launch_kwargs = get_launch_kwargs(headless=True)
        print(f"launch_kwargs: {launch_kwargs}")
        browser = await p.chromium.launch(**launch_kwargs)
        ctx = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36", locale="id-ID")
        page = await ctx.new_page()
        if HAS_STEALTH:
            try:
                await stealth_async(page)
                print("[stealth] applied")
            except Exception as e:
                print(f"[stealth] fail {e}")
        for label, url, country in SEARCH_CONFIGS:
            jobs, err = await scrape_one(page, label, url, country)
            print(f"  -> {label} got {len(jobs)} err={err}")
            if err:
                errors[label]=err
            all_jobs.extend(jobs)
            await asyncio.sleep(2)
        await browser.close()

    # dedup + sort
    filtered = [j for j in all_jobs if "india" not in j.country.lower() and "india" not in j.location.lower()]
    print(f"raw {len(all_jobs)} filtered india {len(filtered)}")
    # deduplicate by url base
    seen=set()
    uniq=[]
    for j in filtered:
        key=j.url.split("?")[0].lower()
        if key not in seen:
            seen.add(key)
            uniq.append(j)
    print(f"after dedup {len(uniq)}")
    # fix job_id stripping query/fragment
    for j in uniq:
        j.job_id = j.url.split("/")[-1].split("?")[0].split("#")[0] if j.url else j.job_id
    sorted_jobs = sorted(uniq, key=lambda j: (j.posted_date, j.scraped_at), reverse=True)

    # write to dated csv and overwrite jobs.csv jobstreet-only? We'll write to data/jobs_jobstreet_today.csv and also update jobs.csv with only jobstreet
    out_path = DATA_DIR / "jobs_jobstreet_today.csv"
    write_csv(sorted_jobs, out_path)
    print(f"saved {len(sorted_jobs)} to {out_path}")

    # also print summary per keyword
    from collections import Counter
    c = Counter([j.keyword for j in sorted_jobs])
    print("per keyword:", dict(c))
    print("per country:", Counter([j.country for j in sorted_jobs]))

    # summary for report
    print("\n===REPORT===")
    for label, url, country in SEARCH_CONFIGS:
        print(f"{url}")
    print(f"TOTAL {len(sorted_jobs)}")
    for j in sorted_jobs[:5]:
        print(f"  {j.keyword} | {j.title[:60]} | {j.location} | {j.url.split('?')[0]}")
    if errors:
        print("ERRORS:", errors)

    return sorted_jobs, errors

if __name__=="__main__":
    asyncio.run(main())
