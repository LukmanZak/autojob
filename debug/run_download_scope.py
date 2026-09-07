from pathlib import Path
from playwright.sync_api import sync_playwright
import sys
sys.path.insert(0,'F:/alpha')
from src.auth.google_flow_vision import download_results
url='https://flow.google.com/project/e093fb3a-cb2a-4352-9063-4f1ab1112815'
chrome='C:/Users/ASUS/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe'
session=Path('F:/alpha/data/sessions/google_flow.json')
out=Path('F:/alpha/result image'); folder=Path('F:/alpha/debug/download_scope_test')
folder.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path=chrome)
 c=b.new_context(storage_state=str(session),viewport={'width':1280,'height':720},accept_downloads=True)
 page=c.new_page(); page.goto(url,wait_until='commit',timeout=30000); page.wait_for_timeout(15000)
 result=download_results(page,out,folder)
 print('RESULT',result)
 print('FILES',[(x.name,x.stat().st_size) for x in out.glob('result_*_1K.png')])
 b.close()
