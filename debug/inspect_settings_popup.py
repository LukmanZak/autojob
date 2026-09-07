from playwright.sync_api import sync_playwright
from pathlib import Path
import json
url='https://flow.google.com/project/6171ac54-e8a2-4e4b-8baa-183cb600d7ed'; session=Path('F:/alpha/data/sessions/google_flow.json'); chrome='C:/Users/ASUS/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe'
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path=chrome); c=b.new_context(storage_state=str(session),viewport={'width':1280,'height':720},accept_downloads=True); page=c.new_page(); page.goto(url,wait_until='commit',timeout=30000); page.wait_for_timeout(15000)
 s=page.locator("button[aria-label='Settings trigger']"); print('settings',s.count(),s.inner_text())
 s.click(force=True); page.wait_for_timeout(500)
 vals=page.evaluate('''() => [...document.querySelectorAll('button,[role=button],[role=radio],[role=menuitem],span,label')].map((e,i)=>{const r=e.getBoundingClientRect();return {i,tag:e.tagName,txt:(e.innerText||'').trim().replace(/\\s+/g,' ').slice(0,180),aria:e.getAttribute('aria-label'),role:e.getAttribute('role'),checked:e.getAttribute('aria-checked'),cls:e.className?.toString().slice(0,140),x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)}}).filter(x=>x.w>0&&x.h>0&&((x.y>350)||(x.txt.match(/16:9|1:1|9:16|4:3|x[234]/i))))''')
 print(json.dumps(vals,indent=2)); page.screenshot(path='F:/alpha/debug/settings_popup.png'); b.close()
