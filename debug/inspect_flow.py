from playwright.sync_api import sync_playwright
from pathlib import Path
import json, time

url='https://flow.google.com/project/e093fb3a-cb2a-4352-9063-4f1ab1112815'
session=Path('F:/alpha/data/sessions/google_flow.json')
out=Path('F:/alpha/debug/flow_dom_inspect.json')
chrome='C:/Users/ASUS/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe'
with sync_playwright() as p:
    b=p.chromium.launch(headless=True, executable_path=chrome)
    c=b.new_context(storage_state=str(session), viewport={'width':1280,'height':720}, accept_downloads=True)
    page=c.new_page()
    page.goto(url, wait_until='commit', timeout=30000)
    page.wait_for_timeout(20000)
    data=page.evaluate('''() => {
      const els=[...document.querySelectorAll('body *')];
      return els.map((e,i)=>({i,tag:e.tagName,cls:e.className?.toString().slice(0,180),aria:e.getAttribute('aria-label'),role:e.getAttribute('role'),text:(e.innerText||'').trim().slice(0,120),rect:(()=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height}})()}))
      .filter(x=>x.rect.w>0&&x.rect.h>0&&(x.aria?.toLowerCase().includes('more')||x.text==='Download'||x.text==='1K'||x.tag==='IMG'||x.tag==='VIDEO'||(x.rect.w>250&&x.rect.h>180&&x.rect.y<400)));
    }''')
    page.screenshot(path='F:/alpha/debug/flow_inspect.png', full_page=True)
    out.write_text(json.dumps(data,indent=2),encoding='utf-8')
    print('url',page.url,'count',len(data),'title',page.title())
    for x in data: print(x)
    b.close()
