"""
Telegram Notifier for Gumroad Product Automation
Sends product files, images, videos, and status updates
to a Telegram chat for monitoring and review.

Usage:
    from telegram_notifier import notify
    notify("Product published!", link="https://duyhoivu.gumroad.com/l/xxx")
    notify("Carousel ready", photo="carousel/slide_1.jpg")
    notify("Video ready", video="output/short_video.mp4")
"""

import os
import sys
import json
import requests

# Load .env
try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "gumroad_products", ".env")
    load_dotenv(_env_path)
except Exception:
    pass

TELEGRAM_API = "https://api.telegram.org"


def _get_config():
    """Get Telegram bot token and chat ID from env."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    return token, chat_id


def _send_message(text, parse_mode="Markdown", disable_preview=True):
    """Send a text message to Telegram."""
    token, chat_id = _get_config()
    if not token or not chat_id:
        return {"ok": False, "error": "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID"}

    resp = requests.post(f"{TELEGRAM_API}/bot{token}/sendMessage", json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": disable_preview,
    })
    return resp.json()


def _send_photo(photo_path, caption=""):
    """Send a photo to Telegram."""
    token, chat_id = _get_config()
    if not token or not chat_id:
        return {"ok": False, "error": "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID"}

    if not os.path.exists(photo_path):
        return {"ok": False, "error": f"File not found: {photo_path}"}

    with open(photo_path, "rb") as f:
        resp = requests.post(f"{TELEGRAM_API}/bot{token}/sendPhoto",
            data={"chat_id": chat_id, "caption": caption, "parse_mode": "Markdown"},
            files={"photo": f})
    return resp.json()


def _send_document(doc_path, caption=""):
    """Send a file/document to Telegram."""
    token, chat_id = _get_config()
    if not token or not chat_id:
        return {"ok": False, "error": "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID"}

    if not os.path.exists(doc_path):
        return {"ok": False, "error": f"File not found: {doc_path}"}

    with open(doc_path, "rb") as f:
        resp = requests.post(f"{TELEGRAM_API}/bot{token}/sendDocument",
            data={"chat_id": chat_id, "caption": caption, "parse_mode": "Markdown"},
            files={"document": f})
    return resp.json()


def _send_video(video_path, caption=""):
    """Send a video to Telegram."""
    token, chat_id = _get_config()
    if not token or not chat_id:
        return {"ok": False, "error": "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID"}

    if not os.path.exists(video_path):
        return {"ok": False, "error": f"File not found: {video_path}"}

    with open(video_path, "rb") as f:
        resp = requests.post(f"{TELEGRAM_API}/bot{token}/sendVideo",
            data={"chat_id": chat_id, "caption": caption, "parse_mode": "Markdown"},
            files={"video": f})
    return resp.json()


def notify(message, photo=None, document=None, video=None, link=None, parse_mode="Markdown"):
    """Send a notification to Telegram.

    Args:
        message: text message (supports Markdown)
        photo: path to image file to send
        document: path to document file to send (PDF, CSV, etc.)
        video: path to video file to send
        link: optional link to append to message
        parse_mode: "Markdown" or "HTML"

    Returns:
        dict with success status
    """
    results = []

    # Build message with optional link
    full_message = message
    if link:
        full_message += f"\n\n🔗 [View on Gumroad]({link})"

    # Send text message
    if not photo and not document and not video:
        r = _send_message(full_message, parse_mode=parse_mode)
        results.append({"type": "message", "result": r})
        return {"success": r.get("ok", False), "results": results}

    # Send text message first (if has media)
    r = _send_message(full_message, parse_mode=parse_mode)
    results.append({"type": "message", "result": r})

    # Send media
    if photo:
        r = _send_photo(photo, caption=f"📸 {os.path.basename(photo)}")
        results.append({"type": "photo", "result": r})

    if document:
        r = _send_document(document, caption=f"📄 {os.path.basename(document)}")
        results.append({"type": "document", "result": r})

    if video:
        r = _send_video(video, caption=f"🎬 {os.path.basename(video)}")
        results.append({"type": "video", "result": r})

    all_ok = all(item["result"].get("ok", False) for item in results)
    return {"success": all_ok, "results": results}


def notify_product_published(title, url, files=None, covers=None, thumbnail=None):
    """Send a formatted product publication notification.

    Args:
        title: product title
        url: Gumroad product URL
        files: list of file paths to send
        covers: list of cover image paths
        thumbnail: thumbnail image path
    """
    message = f"""✅ *Product Published!*

*{title}*

🔗 {url}"""

    result = notify(message, link=url)

    # Send covers
    if covers:
        for cover_path in covers:
            if os.path.exists(cover_path):
                notify(f"🖼️ Cover: {os.path.basename(cover_path)}", photo=cover_path)

    # Send thumbnail
    if thumbnail and os.path.exists(thumbnail):
        notify(f"📷 Thumbnail", photo=thumbnail)

    # Send PDF
    if files:
        for f in files:
            if os.path.exists(f) and f.endswith(".pdf"):
                notify(f"📄 PDF: {os.path.basename(f)}", document=f)

    return result


def notify_batch_start(count, niche):
    """Notify that a batch production is starting."""
    return notify(f"""🚀 *Batch Production Started*

*Niche:* {niche}
*Products to create:* {count}
*Estimated time:* ~{count * 3} minutes

Pipeline: Content → PDF → Cover → Thumbnail → QA → Publish""")


def notify_batch_complete(results):
    """Notify that a batch production is complete."""
    passed = sum(1 for r in results if r.get("qa_pass", False))
    total = len(results)

    message = f"""✅ *Batch Production Complete!*

*Total:* {total} products
*QA Passed:* {passed}/{total}

"""
    for i, r in enumerate(results, 1):
        status = "✅" if r.get("qa_pass") else "❌"
        message += f"{status} {r.get('title', 'Unknown')}\n"
        if r.get("url"):
            message += f"   🔗 {r['url']}\n"

    return notify(message)


if __name__ == "__main__":
    # Demo: show what would be sent
    print("Telegram Notifier Demo")
    print("=" * 40)

    # Test without actual credentials
    r = notify("Test notification", link="https://example.com")
    print(f"Result (no creds): {r}")

    r = notify_product_published(
        title="N8N Automation Pack",
        url="https://duyhoivu.gumroad.com/l/xxx",
    )
    print(f"Product notify: {r}")
