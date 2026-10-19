# Zefoy CAPTCHA OCR Test Results (2026-07-23)

## Test Environment
- Chrome 150.0.7871.181 + Selenium + ChromeDriver
- Tesseract OCR at `C:\Program Files\Tesseract-OCR\tesseract.exe`
- ddddocr 1.6.1 (specialized CAPTCHA OCR engine)
- easyocr 1.7.2
- Python 3.11, Windows 10

## CAPTCHA Characteristics
- 278×129 pixel PNG images
- Served from PHP endpoint: `https://zefoy.com/<hash>.php?_CAPTCHA=<token>`
- New image on each page refresh
- Contains distorted lowercase word (appears to be dictionary words)
- Has colored noise/lines overlaying text
- Characters have scaling distortion and variable spacing

## OCR Engines Tested (18+ CAPTCHA attempts over ~8 minutes)

### ddddocr (specialized CAPTCHA model)
- Original image: returned garbage like "回" (Chinese character), "u9h"
- Cropped (8% margin): "half" (possibly correct on one image, but never confirmed)
- Denoised: similar garbage
- **Accuracy: ~0%** (no confirmed correct answers)

### Tesseract OCR (multiple preprocessing methods)
Tried: raw, grayscale, Otsu threshold, adaptive threshold, inverted, morphological open/close,
cropped (8%/15% margins), scaled 2x/3x (INTER_CUBIC), with whitelist a-zA-Z0-9

Results across all attempts:
| CAPTCHA # | Best Guess | Other Guesses | Correct? |
|-----------|-----------|---------------|----------|
| 1 | "sunlight" | "Lsunlight", "pees", "passo" | ❌ |
| 2 | "begun" | | ❌ |
| 3 | "after" | "often", "biter" | ❌ |
| 4 | "action" | "Cteton", "Ctetien" | ❌ |
| 5 | "badot" | | ❌ |
| 6 | "pen"/"Lopen" | | ❌ |
| 7 | "smooth" | "emoothe", "amoethe" | ❌ |
| 8 | "Fighting" | "fighting" | ❌ |

- **Best preprocessing**: Cropped (8% margin) + inverted + Otsu + 3x scale + PSM 7
- **Accuracy: ~0%** (no confirmed correct answers)

### easyocr
- Result: "h a / f" with 56% confidence
- **Accuracy: ~0%**

### External APIs
- `plowsidecaptcha.pythonanywhere.com/captcha` → "Coming Soon" page (DEAD)
- `platipus9999.pythonanywhere.com/` → "Coming Soon" page (DEAD)

## Key Findings

1. **Zefoy CAPTCHA is hardened against open-source OCR** — ALL tested engines fail
2. **Cropping borders helps OCR quality** — removing ~8% margin from each side eliminates border noise
3. **ddddocr performs worse than Tesseract** on Zefoy CAPTCHAs — it's designed for Chinese captchas with different characteristics
4. **Tesseract produces plausible English words** ("sunlight", "after", "fighting") but they're wrong — the CAPTCHA text is too distorted
5. **No preprocessing technique bridges the gap** — the distortion is too severe for classical image processing

## Selenium Element Screenshot Caching Bug

**CRITICAL FINDING**: When taking screenshots of CAPTCHA image elements via Selenium's `element.screenshot_as_png`, the images can be cached:
- Same element reference + same CAPTCHA URL = identical bytes every time (e.g., 12539 bytes)
- Even after the CAPTCHA has changed (different _CAPTCHA= token in URL)
- The element screenshot returns the STALE cached image, not the current one

**Workaround**: Use JavaScript to extract the image:
```python
# Get image src via JS
img_src = driver.execute_script("""
    var img = document.querySelector('form img');
    return img ? img.src : null;
""")
# If base64 data URL, decode directly
# If URL, fetch via JS fetch() API and get base64
# Then decode the base64 to get fresh image bytes
```

**Fallback**: Take full page screenshot + crop to captcha element coordinates:
```python
pos = driver.execute_script("""
    var img = document.querySelector('form img');
    var rect = img.getBoundingClientRect();
    return {x: rect.x, y: rect.y, w: rect.width, h: rect.height};
""")
# Scale by (screenshot_width / window_innerWidth)
```

## Sneezedip/Tiktok-Booster Repo Analysis

- **Requires Python 3.12+** (hard check in code, exits on 3.11)
- Uses basic `pytesseract.image_to_string(Image.open('Captcha/captcha.png')).strip()` — NO preprocessing
- Has interactive prompts (history selection, video URL input) — not headless-friendly
- Downloads bundled Tesseract to `./Tesseract/` directory
- Has Discord webhook integration, ad blocker extension, heartbeat system
- Would face identical CAPTCHA accuracy issues even if it ran

## Conclusion

Zefoy CAPTCHA solving via open-source OCR is not viable (0% success rate). Options:
1. Custom-trained neural network specifically for Zefoy's CAPTCHA distortion
2. Paid CAPTCHA-solving service (2captcha, anticaptcha) — if they support this type
3. Manual CAPTCHA solving (defeats automation)
