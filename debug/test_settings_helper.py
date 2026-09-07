from pathlib import Path
from playwright.sync_api import sync_playwright
import sys
sys.path.insert(0,'F:/alpha')
from src.auth.google_flow_vision import configure_image_settings
url='https://flow.google.com/project/6171ac54-e8a2-4e4b-8baa-183cb600d7ed'; session=Path('F:/alpha/data/sessions/google_flow.json'); chrome='C:/Users/ASUS/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe'
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path=chrome); c=b.new_context(storage_state=str(session),viewport={'width':1280,'height':720},accept_downloads=True); page=c.new_page(); page.goto(url,wait_until='commit',timeout=30000); page.wait_for_timeout(15000)
 try:
  print('TEST_1',configure_image_settings(page,'1:1',4)); print('SUMMARY_1',page.locator("span.settings-summary").first.inner_text().strip())
  print('TEST_2',configure_image_settings(page,'16:9',2)); print('SUMMARY_2',page.locator("span.settings-summary").first.inner_text().strip())
 finally:
  b.close()
