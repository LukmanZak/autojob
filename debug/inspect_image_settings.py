from playwright.sync_api import sync_playwright
from pathlib import Path
import json
url='https://flow.google.com/project/6171ac54-e8a2-4e4b-8baa-183cb600d7ed'
session=Path('F:/alpha/data/sessions/google_flow.json'); chrome='C:/Users/ASUS/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe'
with sync_playwright() as p:
 b=p.chromium.launch(headless=True, executable_path=chrome)
 c=b.new_context(storage_state=str(session),viewport={'width':1280,'height':720},accept_downloads=True)
 page=c.new_page(); page.goto(url,wait_until='commit',timeout=30000); page.wait_for_timeout(15000)
 data=page.evaluate('''() => [...document.querySelectorAll('button,[role=button],[role=radio],[role=menuitem],span.settings-summary,span.toggle-text')].map((e,i)=>{const r=e.getBoundingClientRect();return {i,tag:e.tagName,txt:(e.innerText||'').trim().replace(/\\s+/g,' ').slice(0,160),aria:e.getAttribute('aria-label'),role:e.getAttribute('role'),checked:e.getAttribute('aria-checked'),cls:e.className?.toString().slice(0,120),x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),hidden:!!(r.width===0||r.height===0)}}).filter(x=>!x.hidden && x.y>500)''')
 print('URL',page.url,'COUNT',len(data)); print(json.dumps(data,indent=2))
 page.screenshot(path='F:/alpha/debug/settings_before_click.png')
 b.close()
