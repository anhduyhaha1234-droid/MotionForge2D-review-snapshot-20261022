"""
Gumroad Full Product Publish Pipeline v2
End-to-end: generate PDF → create images → QA check → upload to Gumroad.

New in v2:
  - Auto-generates SEO permalink from product title
  - Calls PUT /v2/products/{id}/enable to force Live status
  - Verifies permalink and published status in final check

Usage:
    from gumroad_publish import publish_product
    result = publish_product(
        token="your_gumroad_token",
        title="Veo 3 Video Prompts",
        subtitle="40 Expert-Crafted Prompts",
        description="Are you struggling...",
        prompts=prompt_list,  # list of dicts
        price=0,  # cents, 0 = pay what you want
    )
    print(result["product_url"])
    print(result["permalink"])  # e.g. "veo-3-video-prompts"
"""

import os
import sys
import re
import json
import time
import tempfile
import unicodedata
import requests

# Add scripts dir to path for imports
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from pdf_template import generate_prompt_pack_pdf
from mockup_generator import create_card_from_text, create_thumbnail
from qa_checker import check_product, print_report

BASE = "https://api.gumroad.com/v2"


# === Permalink generation ===

def slugify(text):
    """Convert product title to SEO-friendly permalink slug.

    Examples:
        "ChatGPT Solopreneur Pack" → "chatgpt-solopreneur-pack"
        "Veo 3 Video Prompts!" → "veo-3-video-prompts"
        "Midjourney v6 & Flux.1 Photorealistic" → "midjourney-v6-flux1-photorealistic"
    """
    # Normalize unicode (remove accents)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    # Lowercase
    text = text.lower()
    # Replace & with nothing
    text = text.replace("&", "")
    # Replace dots in version numbers with nothing (v6 → v6, 3.0 → 30)
    text = text.replace(".", "")
    # Replace spaces and special chars with hyphens
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    # Trim leading/trailing hyphens
    text = text.strip("-")
    # Collapse multiple hyphens
    text = re.sub(r"-{2,}", "-", text)
    return text


# === File upload helpers ===

def _presign_upload(token, filepath, filename, content_type):
    """Presign → S3 → Complete. Returns file_url."""
    file_size = os.path.getsize(filepath)

    resp = requests.post(f"{BASE}/files/presign", data={
        "access_token": token,
        "filename": filename,
        "content_type": content_type,
        "file_size": str(file_size),
    })
    presign = resp.json()
    if not presign.get("success"):
        raise Exception(f"Presign failed: {presign}")

    with open(filepath, "rb") as f:
        data = f.read()

    s3 = requests.put(presign["parts"][0]["presigned_url"],
                      data=data, headers={"Content-Type": content_type})
    etag = s3.headers.get("ETag", "")

    complete = requests.post(f"{BASE}/files/complete", json={
        "access_token": token,
        "upload_id": presign["upload_id"],
        "key": presign["key"],
        "parts": [{"part_number": 1, "etag": etag}],
    }).json()

    if not complete.get("success"):
        raise Exception(f"Complete failed: {complete}")

    return complete.get("file_url", presign["file_url"])


def _upload_cover_image(token, product_id, image_path):
    """Upload cover/thumbnail via Rails Active Storage signed_blob_id."""
    import hashlib
    import base64

    session = requests.Session()
    # Get XSRF token
    session.get("https://duyhoivu.gumroad.com/l/ewshm")
    xsrf = session.cookies.get("XSRF-TOKEN", "")

    with open(image_path, "rb") as f:
        data = f.read()
    checksum = base64.b64encode(hashlib.md5(data).digest()).decode()

    direct = session.post(
        "https://app.gumroad.com/rails/active_storage/direct_uploads",
        headers={"X-CSRF-Token": xsrf, "Content-Type": "application/json",
                 "Accept": "application/json"},
        json={"blob": {
            "filename": os.path.basename(image_path),
            "content_type": "image/jpeg",
            "byte_size": len(data),
            "checksum": checksum,
        }}
    ).json()

    signed_id = direct["signed_id"]
    requests.put(direct["direct_upload"]["url"], data=data,
                 headers=direct["direct_upload"]["headers"])

    return signed_id


def _enable_product(token, product_id):
    """Force product to Live status via PUT /v2/products/{id}/enable.

    The Gumroad API sometimes sets published:true but the product stays
    in Draft. Calling /enable forces it to Live.
    """
    resp = requests.put(
        f"{BASE}/products/{product_id}/enable",
        data={"access_token": token}
    ).json()
    return resp


def _force_publish(token, product_id):
    """Multiple attempts to ensure product is published and live."""
    # Attempt 1: PUT with published: true
    for attempt in range(3):
        resp = requests.put(
            f"{BASE}/products/{product_id}",
            data={"access_token": token, "published": "true"}
        ).json()
        if resp.get("success") and resp.get("product", {}).get("published"):
            break
        time.sleep(1)

    # Attempt 2: Call /enable endpoint
    time.sleep(1)
    enable_resp = _enable_product(token, product_id)

    # Attempt 3: Final PUT with published: true again
    time.sleep(1)
    requests.put(
        f"{BASE}/products/{product_id}",
        data={"access_token": token, "published": "true"}
    )

    return enable_resp


# === Main publish pipeline ===

def publish_product(token, title, subtitle, description, prompts,
                    price=0, currency="usd", customizable_price=True,
                    permalink=None, output_dir=None,
                    cover_bg_colors=((15, 10, 40), (5, 5, 20)),
                    accent_color=(108, 99, 255), author="AI Prompt Studio",
                    version="1.0", run_qa=True, dry_run=False):
    """
    Full pipeline: generate assets → QA check → publish to Gumroad.

    v2 features:
      - Auto-generates permalink from title (or accepts custom)
      - Calls /enable endpoint to force Live status
      - Verifies permalink and published in final check

    Args:
        token: Gumroad access token
        title: product title
        subtitle: short subtitle
        description: full product description
        prompts: list of dicts with keys: title, prompt, category, tip, variables
        price: price in cents (0 = free/pay-what-you-want)
        currency: currency code
        customizable_price: enable pay-what-you-want
        permalink: custom permalink slug (auto-generated from title if None)
        output_dir: where to save generated files (default: temp dir)
        cover_bg_colors: gradient colors for images
        accent_color: RGB tuple for accent
        author: author name
        version: version string
        run_qa: run QA checks before publishing
        dry_run: if True, generate files but don't upload

    Returns:
        dict with: product_id, product_url, permalink, files, qa_results
    """
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="gumroad_")
    os.makedirs(output_dir, exist_ok=True)

    # Auto-generate permalink if not provided
    if permalink is None:
        permalink = slugify(title)

    result = {
        "output_dir": output_dir,
        "files": {},
        "qa_results": None,
        "product_id": None,
        "product_url": None,
        "permalink": permalink,
        "published": False,
        "steps": [],
    }

    # === Step 1: Generate PDF ===
    print("[1/7] Generating PDF...")
    pdf_path = os.path.join(output_dir, "product.pdf")
    pdf_result = generate_prompt_pack_pdf(
        prompts, pdf_path, title=title, subtitle=subtitle,
        author=author, version=version, dark_mode=True,
        accent_color=f"#{accent_color[0]:02x}{accent_color[1]:02x}{accent_color[2]:02x}"
    )
    result["files"]["pdf"] = pdf_path
    result["steps"].append({"step": "generate_pdf", "status": "ok", **pdf_result})
    print(f"  PDF: {pdf_result['size']} bytes ({pdf_result['method']})")

    # === Step 2: Generate Cover ===
    print("[2/7] Generating cover image...")
    cover_path = os.path.join(output_dir, "cover.jpg")
    cover_result = create_card_from_text(
        cover_path, title=title, subtitle=subtitle,
        badge_text=f"{len(prompts)} PROMPTS",
        width=1280, height=720, bg_colors=cover_bg_colors, accent_color=accent_color
    )
    result["files"]["cover"] = cover_path
    result["steps"].append({"step": "generate_cover", "status": "ok", **cover_result})
    print(f"  Cover: {cover_result['dimensions']}")

    # === Step 3: Generate Thumbnail ===
    print("[3/7] Generating thumbnail...")
    thumb_path = os.path.join(output_dir, "thumbnail.jpg")
    thumb_result = create_thumbnail(
        cover_path, thumb_path, size=600,
        badge_text=f"{len(prompts)} PROMPTS",
        bg_colors=cover_bg_colors, accent_color=accent_color
    )
    result["files"]["thumbnail"] = thumb_path
    result["steps"].append({"step": "generate_thumbnail", "status": "ok", **thumb_result})
    print(f"  Thumbnail: {thumb_result['dimensions']}")

    # === Step 4: QA Check ===
    if run_qa:
        print("[4/7] Running QA checks...")
        qa = check_product(
            pdf_path=pdf_path, cover_path=cover_path,
            thumbnail_path=thumb_path, title=title,
            description=description, price=price, prompts=prompts
        )
        result["qa_results"] = qa
        print_report(qa)
        if not qa["overall_valid"]:
            print("  WARNING: QA failed! Proceeding anyway...")
            result["steps"].append({"step": "qa_check", "status": "FAIL"})
        else:
            result["steps"].append({"step": "qa_check", "status": "PASS"})
    else:
        print("[4/7] QA check skipped")
        result["steps"].append({"step": "qa_check", "status": "skipped"})

    if dry_run:
        print("[5/7] DRY RUN — skipping upload")
        print(f"\nFiles generated in: {output_dir}")
        for k, v in result["files"].items():
            print(f"  {k}: {v}")
        result["steps"].append({"step": "upload", "status": "dry_run"})
        return result

    # === Step 5: Create Product on Gumroad (with permalink) ===
    print(f"[5/7] Creating product on Gumroad (permalink: {permalink})...")
    create_data = {
        "access_token": token,
        "name": title,
        "description": description,
        "price": price,
        "currency": currency,
        "customizable_price": customizable_price,
        "published": "true",
        "permalink": permalink,
    }

    create_resp = requests.post(f"{BASE}/products", data=create_data).json()

    if not create_resp.get("success"):
        raise Exception(f"Product creation failed: {create_resp}")

    product_id = create_resp["product"]["id"]
    product_url = create_resp["product"]["short_url"]
    api_permalink = create_resp["product"].get("permalink", permalink)
    result["product_id"] = product_id
    result["product_url"] = product_url
    result["permalink"] = api_permalink
    print(f"  Product: {product_url}")
    print(f"  Permalink: {api_permalink}")

    # Upload PDF
    print("  Uploading PDF...")
    file_url = _presign_upload(token, pdf_path, "product.pdf", "application/pdf")

    # Attach file + publish
    requests.put(f"{BASE}/products/{product_id}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"published": True, "files": [{"url": file_url}]})
    print("  PDF attached")

    # === Step 6: Force publish + Enable ===
    print("[6/7] Forcing product to Live status...")
    enable_resp = _force_publish(token, product_id)
    print(f"  Enable response: {enable_resp.get('success', 'unknown')}")

    # === Step 7: Upload Cover & Thumbnail ===
    print("[7/7] Uploading cover & thumbnail...")
    try:
        cover_blob_id = _upload_cover_image(token, product_id, cover_path)
        r = requests.post(f"{BASE}/products/{product_id}/covers",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"signed_blob_id": cover_blob_id})
        print(f"  Cover: {r.json().get('success', False)}")

        thumb_blob_id = _upload_cover_image(token, product_id, thumb_path)
        r = requests.post(f"{BASE}/products/{product_id}/thumbnail",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"signed_blob_id": thumb_blob_id})
        print(f"  Thumbnail: {r.json().get('success', False)}")
    except Exception as e:
        print(f"  Cover/thumbnail upload error: {e}")

    result["steps"].append({"step": "upload", "status": "ok"})

    # === Final verification ===
    print("\n=== VERIFICATION ===")
    time.sleep(2)
    final = requests.get(f"{BASE}/products/{product_id}",
                         params={"access_token": token}).json().get("product", {})
    is_published = final.get("published", False)
    final_permalink = final.get("permalink", "")
    result["published"] = is_published

    print(f"  Published: {is_published}")
    print(f"  Permalink: {final_permalink}")
    print(f"  URL: {final.get('short_url')}")
    print(f"  Files: {len(final.get('files', []))}")
    print(f"  Covers: {len(final.get('covers', []))}")
    print(f"  Thumbnail: {final.get('thumbnail_url') is not None}")

    if not is_published:
        print("  WARNING: Product not yet live. May need manual publish via dashboard.")

    return result


if __name__ == "__main__":
    # Quick test with dry_run
    test_prompts = [
        {"title": "Epic Drone Shot", "prompt": "Cinematic aerial drone descending through clouds to reveal [CITY] at golden hour.",
         "category": "Cinematic", "tip": "Add camera movement details", "variables": ["CITY"]},
        {"title": "TikTok Hook", "prompt": "Stop scrolling! This one trick about [TOPIC] changed everything...",
         "category": "TikTok Short Form", "tip": "Use pattern interrupt", "variables": ["TOPIC"]},
    ]

    # Test slugify
    print("Slugify tests:")
    print(f"  'ChatGPT Solopreneur Pack' → '{slugify('ChatGPT Solopreneur Pack')}'")
    print(f"  'Veo 3 Video Prompts!' → '{slugify('Veo 3 Video Prompts!')}'")
    print(f"  'Midjourney v6 & Flux.1' → '{slugify('Midjourney v6 & Flux.1')}'")
    print()

    result = publish_product(
        token="DUMMY",
        title="Test Product",
        subtitle="Test Subtitle",
        description="This is a test product description with enough characters to pass validation. It needs to be at least 50 characters long.",
        prompts=test_prompts,
        dry_run=True,
    )
    print(f"\nResult: {json.dumps({k: v for k, v in result.items() if k != 'files'}, indent=2)}")
