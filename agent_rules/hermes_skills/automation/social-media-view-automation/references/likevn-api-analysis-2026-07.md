# like.vn SMM Panel — API Analysis (2026-07-23)

## Overview
- URL: https://like.vn
- Vietnamese SMM panel for Facebook, Instagram, TikTok, YouTube
- Description: "Hệ thống cung cấp dịch vụ tăng view tiktok uy tín"
- Meta: SMM panel Vietnam

## API Endpoints Found

### Order Endpoint
```
POST https://like.vn/api/mua-view-tiktok/order
```
- Requires: CSRF token (from `<meta name="csrf-token">`), authentication
- Response without auth: `{"status":"error","message":"Người dùng không hợp lệ vui lòng thử lại"}`

### Service List
```
GET https://like.vn/mua-view-tiktok/list
```
- Returns HTML with service configurations
- Uses gridjs for table rendering

## Technical Stack
- Frontend: jQuery, AdminLTE, Bootstrap, Summernote, Daterangepicker
- CSRF protection: Yes (meta tag)
- API token: Empty (requires login)
- Widget: what-on.com/service-v2.js
- Google Analytics: G-PVY0H7ZJP0, AW-11455244301

## How like.vn Likely Works
1. User registers and deposits money
2. User submits TikTok video URL + selects service/quantity
3. like.vn dispatches orders to upstream providers
4. Upstream providers use account pools or emulator farms
5. Views are delivered incrementally (drip-feed)

## Related Services (Vietnamese SMM Market)
- bufflikes.com
- socpanel.com
- Various Telegram bots for SMM

## Next Steps to Automate
1. Register account on like.vn
2. Get API key/token after login
3. Use CSRF token + session cookie to POST orders
4. Can potentially automate bulk orders
