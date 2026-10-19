# SMM Panel & Third-Party Services

## tikfollowers.com (CONFIRMED WORKING - Free)
- URL: https://tikfollowers.com/free-tools
- API: `/api/process` requires `google_token` (reCAPTCHA)
- Built on: TikApis.com reverse-engineered TikTok API
- How it works: Maintains own TikTok account pool, dispatches views server-side
- Test result: 547 → 3624 views (July 2026)
- Has Telegram: t.me/tikfollowerscom

## like.vn (Vietnamese SMM Panel - Paid)
- URL: https://like.vn/mua-view-tiktok
- API endpoint: `POST https://like.vn/api/mua-view-tiktok/order`
- Returns: `{"status":"error","message":"Người dùng không hợp lệ vui lòng thử lại"}` without auth
- CSRF token required (from meta tag)
- Services: Facebook, Instagram, TikTok, YouTube
- Description: "Hệ thống cung cấp dịch vụ tăng view tiktok uy tín"

## zefoy.com (Intermittent)
- URL: https://zefoy.com
- Views service: Often disabled ("This service is currently not working")
- CAPTCHA: Hardened against OCR (Tesseract/ddddocr/EasyOCR all fail)
- External CAPTCHA APIs: Both DOWN (plowsidecaptcha.pythonanywhere.com, platipus9999.pythonanywhere.com)
- Session: PHPSESSID cookie, expires quickly

## freer.es (DEAD)
- Status: 502 error, completely offline

## SMM Panel Architecture (How View Sellers Work)
1. **Upstream providers** maintain large pools of TikTok accounts (real or generated)
2. **SMM panels** (like.vn, bufflikes.com) resell services via web UI + API
3. **Resellers** buy in bulk from panels and resell at markup
4. **Open-source bots** (Zefoy wrappers) automate free tier from Zefoy's account pool
5. All approaches ultimately require TikTok accounts watching the video

## Key Repos for SMM
- prm4u/SMMpanel (40★) — All-in-one SMM panel, 70+ platforms
- followersmore/followersmore-smm-free (4★) — Free SMM panel
