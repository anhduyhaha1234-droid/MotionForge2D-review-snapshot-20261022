"""
Zefoy.com service availability checker.
Solves captcha with Tesseract OCR, checks all 8 Zefoy services, reports status.

Usage: python zefoy-check-services.py [VIDEO_URL]
Default video URL is a placeholder — pass your own as argument.

Requirements:
    pip install selenium pytesseract pillow webdriver-manager
    winget install UB-Mannheim.TesseractOCR  (Windows)
"""
import sys, time, re, base64, io, json
import pytesseract
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

VIDEO_URL = sys.argv[1] if len(sys.argv) > 1 else "https://www.tiktok.com/@tadgaming0798/video/7547761978786319624"
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

SERVICES = ["Followers", "Hearts", "Comments Hearts", "Views", "Shares", "Favorites", "Live Stream", "Repost"]

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-notifications")
options.add_argument("--window-size=1280,800")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
options.add_experimental_option("prefs", {"profile.default_content_setting_values.notifications": 2})
options.add_experimental_option("excludeSwitches", ["enable-automation"])

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def dismiss():
    try: driver.switch_to.alert.dismiss()
    except: pass

def solve_captcha():
    for _ in range(6):
        time.sleep(2)
        try:
            cap = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "captcha-img")))
            time.sleep(3)
            dismiss()
            src = cap.get_attribute("src")
            if not src or len(src) < 50:
                driver.refresh(); time.sleep(3); continue
            b64 = driver.execute_script(
                "var c=document.createElement('canvas'),i=arguments[0];"
                "c.width=i.naturalWidth||i.width;c.height=i.naturalHeight||i.height;"
                "c.getContext('2d').drawImage(i,0,0);return c.toDataURL('image/png').split(',')[1]", cap)
            img = Image.open(io.BytesIO(base64.b64decode(b64))).convert("L")
            img = img.point(lambda x: 0 if x < 128 else 255).resize((img.width*3, img.height*3), Image.LANCZOS)
            text = re.sub(r"[^a-z]", "", pytesseract.image_to_string(
                img, config="--psm 7 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyz").strip().lower())
            if not text or len(text) < 3:
                driver.refresh(); time.sleep(3); continue
            print(f"[*] OCR: '{text}'")
            el = driver.find_element(By.CSS_SELECTOR, "input[name='captchalogin']")
            el.clear(); el.send_keys(text)
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            time.sleep(4); dismiss()
            if "Enter Video URL" in driver.page_source:
                return True
            driver.refresh(); time.sleep(3)
        except:
            driver.refresh(); time.sleep(3)
    return False

def submit_service(action, video_url, key):
    return driver.execute_script("""
        var xhr=new XMLHttpRequest();
        xhr.open('POST','/'+arguments[2],false);
        xhr.setRequestHeader('Content-Type','application/x-www-form-urlencoded');
        xhr.send(arguments[1]+'='+encodeURIComponent(arguments[0]));
        try{var t=xhr.responseText.split('').reverse().join('');
            return atob(decodeURIComponent(t)).substring(0,500);}
        catch(e){return 'RAW:'+xhr.responseText.substring(0,100);}
    """, video_url, key, action)

try:
    print(f"[*] Loading zefoy.com...")
    driver.get("https://zefoy.com/")
    time.sleep(3)
    dismiss()
    if "Just a moment" in driver.page_source:
        time.sleep(15); dismiss()

    if "Enter Video URL" not in driver.page_source:
        print("[*] Solving captcha...")
        if not solve_captcha():
            print("[-] Captcha failed"); sys.exit(1)
    print("[+] Session active")

    form_actions = re.findall(r'<form action="([^"]+)">', driver.page_source)
    video_key = re.findall(r'name="([^"]+)"[^>]*placeholder="Enter Video URL"', driver.page_source)[0]

    print(f"\n{'='*50}")
    print(f"Zefoy Service Status (video: {VIDEO_URL[:60]}...)")
    print(f"{'='*50}")
    for idx, action in enumerate(form_actions):
        name = SERVICES[idx] if idx < len(SERVICES) else f"Service {idx}"
        decoded = submit_service(action, VIDEO_URL, video_key)
        if "not working" in decoded.lower():
            status = "NOT WORKING"
        elif "success" in decoded.lower() or "sent" in decoded.lower():
            status = "WORKING (success)"
        elif "please wait" in decoded.lower() or "countdown" in decoded.lower():
            m = re.search(r"(\d+)\s*seconds?", decoded)
            status = f"WORKING (cooldown {m.group(1)}s)" if m else "WORKING (cooldown)"
        elif "search" in decoded.lower() or "Enter Video" in decoded:
            status = "READY"
        else:
            status = f"UNKNOWN: {decoded[:60]}"
        print(f"  {name:20s} -> {status}")
    print(f"{'='*50}")

finally:
    driver.quit()
