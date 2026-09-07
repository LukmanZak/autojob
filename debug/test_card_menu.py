from playwright.sync_api import sync_playwright
from pathlib import Path
import json
url='https://flow.google.com/project/e093fb3a-cb2a-4352-9063-4f1ab1112815'
session=Path('F:/alpha/data/sessions/google_flow.json')
chrome='C:/Users/ASUS/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe'
with sync_playwright() as p:
 b=p.chromium.launch(headless=True, executable_path=chrome)
 c=b.new_context(storage_state=str(session),viewport={'width':1280,'height':720},accept_downloads=True)
 page=c.new_page(); page.goto(url,wait_until='commit',timeout=30000); page.wait_for_timeout(15000)
 cards=page.locator('flow-grid-tile-container').filter(has=page.locator('flow-image-tile'))
 print('cards',cards.count())
 for i in range(min(cards.count(),2)):
  card=cards.nth(i); img=card.locator('img.image'); more=card.locator("button[aria-label='More options']")
  print('card',i,'img',img.count(),'more',more.count(),'box',card.bounding_box(),more.bounding_box())
  img.hover(force=True); page.wait_for_timeout(300); more.click(force=True); page.wait_for_timeout(500)
  vals=page.locator('mat-menu-container, .mat-mdc-menu-panel, [role=menu], [role=menuitem], span.label, mat-icon').evaluate_all("els=>els.map(e=>({tag:e.tagName,role:e.getAttribute('role'),text:(e.innerText||'').trim(),cls:e.className?.toString().slice(0,100)})).filter(x=>x.text||x.role)")
  print('menu',vals[-30:])
  page.keyboard.press('Escape'); page.wait_for_timeout(300)
 b.close()
