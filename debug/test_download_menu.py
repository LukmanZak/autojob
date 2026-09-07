from playwright.sync_api import sync_playwright
from pathlib import Path
url='https://flow.google.com/project/e093fb3a-cb2a-4352-9063-4f1ab1112815'; session=Path('F:/alpha/data/sessions/google_flow.json'); chrome='C:/Users/ASUS/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe'
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path=chrome); c=b.new_context(storage_state=str(session),viewport={'width':1280,'height':720},accept_downloads=True); page=c.new_page(); page.goto(url,wait_until='commit',timeout=30000); page.wait_for_timeout(15000)
 card=page.locator('flow-grid-tile-container').filter(has=page.locator('flow-image-tile')).first; card.locator('img.image').hover(force=True); page.wait_for_timeout(500); card.locator("button[aria-label='More options']").click(force=True); page.wait_for_timeout(500)
 dl=page.locator("button[role='menuitem']").filter(has_text='Download').last; print('dl',dl.count(),dl.is_visible(),dl.inner_text()); dl.click(force=True); page.wait_for_timeout(700)
 vals=page.locator("button,[role='menuitem'],span.label").evaluate_all("els=>els.map(e=>({t:(e.innerText||'').trim(),r:e.getAttribute('role'),v:!!(e.offsetWidth||e.offsetHeight)})).filter(x=>x.v&&(x.t==='1K'||x.t.includes('1K')||x.t.includes('2K')))")
 print('sizes',vals); page.screenshot(path='F:/alpha/debug/after_download_menu.png'); b.close()
