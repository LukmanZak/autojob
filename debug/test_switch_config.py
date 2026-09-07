from pathlib import Path
from playwright.sync_api import sync_playwright
import sys
sys.path.insert(0,'F:/alpha')
from src.auth.google_flow_vision import switch_video_to_images, configure_image_settings
url='https://flow.google.com/project/bdb7c586-7ccb-4595-a147-604b189b1a08'; session=Path('F:/alpha/data/sessions/google_flow.json'); chrome='C:/Users/ASUS/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe'
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path=chrome); c=b.new_context(storage_state=str(session),viewport={'width':1280,'height':720},accept_downloads=True); page=c.new_page(); page.goto(url,wait_until='commit',timeout=30000); page.wait_for_timeout(15000)
 print('SWITCH',switch_video_to_images(page)); print('CONFIG',configure_image_settings(page,'16:9',4)); print('SUMMARY',page.locator("span.settings-summary").first.inner_text().strip()); b.close()
