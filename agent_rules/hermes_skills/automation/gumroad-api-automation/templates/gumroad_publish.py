
"""
Gumroad Product Publishing — Full E2E Template
Edit TOKEN, product details, and file paths, then run.
"""
import requests
import json
import os

TOKEN = "YOUR_GUMROAD_ACCESS_TOKEN"
BASE = "https://api.gumroad.com/v2"
PDF_PATH = "./product.pdf"

def presign_upload(filepath, filename, content_type):
    """3-step file upload: presign → S3 → complete"""
    file_size = os.path.getsize(filepath)
    resp = requests.post(f"{BASE}/files/presign", data={
        "access_token": TOKEN,
        "filename": filename,
        "content_type": content_type,
        "file_size": str(file_size),
    })
    presign = resp.json()
    assert presign.get("success"), f"Presign failed: {presign}"
    with open(filepath, "rb") as f:
        data = f.read()
    s3_resp = requests.put(
        presign["parts"][0]["presigned_url"],
        data=data,
        headers={"Content-Type": content_type},
    )
    etag = s3_resp.headers.get("ETag", "")
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
    resp = requests.post(f"{BASE}/products", data={
        "access_token": TOKEN,
        "name": name,
        "description": description,
        "price": price,
        "currency": "usd",
        "customizable_price": price == 0,
    })
    result = resp.json()
    assert result.get("success"), f"Create failed: {result}"
    return result["product"]

def attach_files(product_id, file_urls):
    resp = requests.put(f"{BASE}/products/{product_id}",
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
        json={"published": True, "files": [{"url": url} for url in file_urls]})
    return resp.json()

def main():
    print("Creating product...")
    product = create_product(
        name="Your Product Title",
        description="Your description here. Pay What You Want!",
        price=0,
    )
    product_id = product["id"]
    print(f"  Created: {product['short_url']} (ID: {product_id})")
    print("Uploading PDF...")
    pdf_url = presign_upload(PDF_PATH, "product.pdf", "application/pdf")
    print(f"  PDF URL: {pdf_url}")
    print("Attaching files...")
    result = attach_files(product_id, [pdf_url])
    print(f"  Success: {result.get('success')}")
    print(f"\nDone! Product at: {product['short_url']}")
    print("NOTE: Cover image must be set via web dashboard (API limitation)")

if __name__ == "__main__":
    main()
