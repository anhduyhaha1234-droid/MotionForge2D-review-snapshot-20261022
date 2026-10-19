
"""
Gumroad Product Publishing — Full E2E Template
Usage: Edit TOKEN, product details, and file paths, then run.
"""
import requests
import json
import os

TOKEN = "YOUR_GUMROAD_ACCESS_TOKEN"
BASE = "https://api.gumroad.com/v2"
PDF_PATH = "./product.pdf"
COVER_PATH = "./cover.jpg"  # Note: cover must be set via web dashboard

def presign_upload(filepath, filename, content_type):
    """3-step file upload: presign → S3 → complete"""
    file_size = os.path.getsize(filepath)
    
    # 1. Presign
    resp = requests.post(f"{BASE}/files/presign", data={
        "access_token": TOKEN,
        "filename": filename,
        "content_type": content_type,
        "file_size": str(file_size),
    })
    presign = resp.json()
    assert presign.get("success"), f"Presign failed: {presign}"
    
    # 2. Upload to S3
    with open(filepath, "rb") as f:
        data = f.read()
    s3_resp = requests.put(
        presign["parts"][0]["presigned_url"],
        data=data,
        headers={"Content-Type": content_type},
    )
    etag = s3_resp.headers.get("ETag", "")
    
    # 3. Complete (MUST be JSON body)
    complete = requests.post(f"{BASE}/files/complete", json={
        "access_token": TOKEN,
        "upload_id": presign["upload_id"],
        "key": presign["key"],
        "parts": [{"part_number": 1, "etag": etag}],
    })
    result = complete.json()
    assert result.get("success"), f"Complete failed: {result}"
    return result["file_url"]


def create_product(name, description, price=0):
    """Create a Gumroad product"""
    resp = requests.post(f"{BASE}/products", data={
        "access_token": TOKEN,
        "name": name,
        "description": description,
        "price": price,
        "currency": "usd",
        "customizable_price": price == 0,  # Pay what you want for free products
    })
    result = resp.json()
    assert result.get("success"), f"Create failed: {result}"
    return result["product"]


def attach_files(product_id, file_urls):
    """Attach uploaded files to product (JSON body required)"""
    resp = requests.put(f"{BASE}/products/{product_id}",
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
        json={
            "published": True,
            "files": [{"url": url} for url in file_urls],
        })
    return resp.json()


def main():
    # Step 1: Create product
    print("Creating product...")
    product = create_product(
        name="Your Product Title",
        description="""Your product description here.
        
What's Inside:
- Feature 1
- Feature 2
- Feature 3

Pay What You Want — download free or support with any amount!""",
        price=0,
    )
    product_id = product["id"]
    print(f"  Created: {product['short_url']} (ID: {product_id})")
    
    # Step 2: Upload PDF
    print("Uploading PDF...")
    pdf_url = presign_upload(PDF_PATH, "product.pdf", "application/pdf")
    print(f"  PDF URL: {pdf_url}")
    
    # Step 3: Attach to product
    print("Attaching files...")
    result = attach_files(product_id, [pdf_url])
    print(f"  Success: {result.get('success')}")
    
    # Step 4: Verify
    print("\nVerifying...")
    resp = requests.get(f"{BASE}/products/{product_id}", params={"access_token": TOKEN})
    p = resp.json()["product"]
    print(f"  Published: {p['published']}")
    print(f"  URL: {p['short_url']}")
    print(f"  Files: {len(p['files'])}")
    print(f"  Covers: {p['covers']} (must set via web dashboard)")
    
    print(f"\nDone! Product at: {p['short_url']}")


if __name__ == "__main__":
    main()
