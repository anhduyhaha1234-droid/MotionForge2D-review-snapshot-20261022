# SMMStone API Documentation (2026-07 Verified)

## API Endpoint

```
POST https://smmstone.com/api/v2
Content-Type: application/x-www-form-urlencoded
```

## Authentication

API key required — get from smmstone.com dashboard after registration.

## Actions

| Action | Parameters | Description |
|--------|-----------|-------------|
| `services` | `key` | List all services with IDs, prices, min/max |
| `add` | `key, service, link, quantity, runs, interval` | Place an order |
| `status` | `key, order` | Check single order status |
| `status` | `key, orders` | Check multiple orders (comma-separated, max 100) |
| `balance` | `key` | Get account balance |
| `refill` | `key, order` | Create refill request |
| `refill_status` | `key, refill` | Check refill status |
| `cancel` | `key, orders` | Cancel orders |

## TikTok View Services

| ID | Service | Price/1K | Max Order | Speed |
|----|---------|----------|-----------|-------|
| **842** | TikTok Video Views [Non-Drop] [Refill 30D] | **$0.04** | 10M | 38 min |
| 11749 | TikTok Views [Cheapest] [No Refill] | $0.08 | 100M | 5.5 hrs |
| 11750 | TikTok Views [Cheapest] [Refill 30D] | $0.08 | 100M | 4.8 hrs |
| 719 | TikTok Video Views [Instant] [10M/D] | $0.09 | 100M | 15 min |
| 5964 | TikTok Video Views | $0.11 | 4M | 10 min |
| 5818 | TikTok Views [Cheapest] [FAST] | $0.12 | 100M | 7 hrs |

## Cost Calculation

- Service #842: 20M views = $800 (2 orders × 10M max each)
- Service #842: 100K views = $4

## API Usage Examples

```python
import requests

API_URL = "https://smmstone.com/api/v2"
API_KEY = "***"  # Get from dashboard

# List TikTok view services
r = requests.post(API_URL, data={"key": API_KEY, "action": "services"})
services = [s for s in r.json() if "tiktok" in s["name"].lower() and "view" in s["name"].lower()]

# Order 10M views (service 842)
r = requests.post(API_URL, data={
    "key": API_KEY,
    "action": "add",
    "service": 842,
    "link": "https://tiktok.com/@user/video/123",
    "quantity": 10000000
})
order_id = r.json()["order"]

# Check status
r = requests.post(API_URL, data={
    "key": API_KEY,
    "action": "status",
    "order": order_id
})
print(r.json())  # {"charge": "400.00", "start_count": "...", "status": "In progress", ...}

# Check balance
r = requests.post(API_URL, data={"key": API_KEY, "action": "balance"})
print(r.json())  # {"balance": "100.00", "currency": "USD"}
```

## Geo-Targeting

**SMMStone does NOT support proxy or geo-targeting.** Views come from their global bot network, not from specific countries. Vietnamese views are NOT available through SMMStone.

For Vietnamese views specifically, alternatives:
- **Like.vn** — established Vietnamese SMM (8+ years, 283K members)
- **Traodoisub.com** — Vietnamese coin-exchange platform

## Limitations

- Max 10M per order for service #842 (need 2 orders for 20M)
- Views are GLOBAL (not geo-targeted)
- No proxy support — views come from SMMStone's infrastructure
- Refill guarantee is 30 days only

## Recommendation

**Service #842 ($0.04/1K) is the best value** for mass TikTok views when geo-targeting is not required. Full API support with order tracking. Register at smmstone.com to get API key.
