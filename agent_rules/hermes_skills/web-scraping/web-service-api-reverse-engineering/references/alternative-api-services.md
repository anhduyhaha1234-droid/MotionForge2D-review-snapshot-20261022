# Alternative API Services (tested 2026-07-23)

## DATA APIs (read-only — cannot inflate views/likes)

| Service | URL | What it does | Price | Notes |
|---------|-----|-------------|-------|-------|
| tikapi.com / tikapi.io | tikapi.com | Unofficial TikTok API with OAuth. Read videos, live streams, posts. | Paid | Legitimate data API, NOT for manipulation |
| tikhub.io | tikhub.io | 1000+ endpoints across TikTok, Instagram, YouTube, etc. | $0.001/request, free credit on signup | Social media DATA infrastructure. Can read video data but cannot inflate views |
| tiktokapi.com | tiktokapi.com | Domain for sale | N/A | Not operational |

**Key distinction:** DATA APIs let you READ TikTok data (video info, user profiles, comments). MANIPULATION APIs let you WRITE/INFLATE metrics (views, likes, follows). tikapis.com is the only known MANIPULATION API provider; all others are read-only.

## Standard SMM Panel API Format

Most SMM panels worldwide (bulkfollows.com, smmraja.com, and many child panels) use the **same industry-standard API**:

```
POST /api/v2
Content-Type: application/json

{
  "key": "YOUR_API_KEY",
  "action": "add",           // or "services", "status", "balance"
  "service": 1234,            // service ID from /api/v2?action=services
  "link": "https://tiktok.com/@user/video/123...",
  "quantity": 1000
}
```

**Common actions:**
- `services` — List all available services with IDs and prices
- `add` — Create an order
- `status` — Check order status
- `balance` — Check account balance

**This format works on:** bulkfollows.com, smmraja.com, and most panels using the SMMFollows/ChildPanel platform. Each panel has different service IDs and prices, but the API shape is identical.

**To find the API:** Navigate to the panel's `/api` or `/api/v2` page. If it returns `{"error":"Invalid API key"}` without auth, the API exists and uses this format.

## Other SMM Panels (alive, tested 2026-07-23)
- bulkfollows.com — Prices from $0.001/1K, standard /api/v2 format
- smmraja.com — "Best & Cheapest SMM Reseller Panel Since 2014"
