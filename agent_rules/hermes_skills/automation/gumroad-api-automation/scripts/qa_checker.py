
"""
QA Checker for Gumroad Digital Products
Validates PDF files, images, and product data before publishing.

Usage:
    from qa_checker import check_product
    results = check_product(pdf_path="product.pdf", cover_path="cover.jpg",
                            thumbnail_path="thumb.jpg", title="My Product")
    print(results)
"""

import os
import json

# === Image validation ===

def check_image(path, expected_width=None, expected_height=None,
                min_width=None, min_height=None, max_size_mb=10,
                allowed_formats=("JPEG", "PNG", "WEBP")):
    """
    Validate an image file.
    
    Returns:
        dict with: path, valid (bool), errors (list), info (dict)
    """
    from PIL import Image
    
    errors = []
    info = {}
    
    if not os.path.exists(path):
        return {"path": path, "valid": False, "errors": ["File not found"], "info": {}}
    
    try:
        img = Image.open(path)
        info["format"] = img.format
        info["mode"] = img.mode
        info["width"] = img.width
        info["height"] = img.height
        info["size_bytes"] = os.path.getsize(path)
        info["size_mb"] = round(info["size_bytes"] / 1024 / 1024, 2)
    except Exception as e:
        return {"path": path, "valid": False, "errors": [f"Cannot open: {e}"], "info": {}}
    
    # Format check
    if img.format not in allowed_formats:
        errors.append(f"Format {img.format} not in allowed: {allowed_formats}")
    
    # Size check
    if info["size_mb"] > max_size_mb:
        errors.append(f"File too large: {info['size_mb']}MB > {max_size_mb}MB")
    
    # Dimension checks
    if expected_width and img.width != expected_width:
        errors.append(f"Width {img.width} != expected {expected_width}")
    if expected_height and img.height != expected_height:
        errors.append(f"Height {img.height} != expected {expected_height}")
    if min_width and img.width < min_width:
        errors.append(f"Width {img.width} < minimum {min_width}")
    if min_height and img.height < min_height:
        errors.append(f"Height {img.height} < minimum {min_height}")
    
    # Aspect ratio info
    info["aspect_ratio"] = round(img.width / img.height, 2)
    
    return {"path": path, "valid": len(errors) == 0, "errors": errors, "info": info}


def check_cover(path):
    """Check Gumroad cover image (1280x720 recommended)."""
    return check_image(path, min_width=1200, min_height=600, max_size_mb=5,
                       allowed_formats=("JPEG", "PNG", "WEBP"))


def check_thumbnail(path):
    """Check Gumroad thumbnail (600x600 recommended)."""
    return check_image(path, min_width=500, min_height=500, max_size_mb=3,
                       allowed_formats=("JPEG", "PNG", "WEBP"))


# === PDF validation ===

def check_pdf(path, min_pages=1, max_size_mb=50, min_size_kb=10):
    """
    Validate a PDF file.
    
    Returns:
        dict with: path, valid (bool), errors (list), info (dict)
    """
    errors = []
    info = {}
    
    if not os.path.exists(path):
        return {"path": path, "valid": False, "errors": ["File not found"], "info": {}}
    
    info["size_bytes"] = os.path.getsize(path)
    info["size_kb"] = round(info["size_bytes"] / 1024, 1)
    info["size_mb"] = round(info["size_bytes"] / 1024 / 1024, 2)
    
    # Size checks
    if info["size_mb"] > max_size_mb:
        errors.append(f"PDF too large: {info['size_mb']}MB > {max_size_mb}MB")
    if info["size_kb"] < min_size_kb:
        errors.append(f"PDF too small: {info['size_kb']}KB < {min_size_kb}KB (possibly empty)")
    
    # Check PDF header
    try:
        with open(path, "rb") as f:
            header = f.read(8)
            if not header.startswith(b"%PDF"):
                errors.append("Not a valid PDF file (missing %PDF header)")
            else:
                info["pdf_version"] = header.decode("ascii", errors="ignore").strip()
    except Exception as e:
        errors.append(f"Cannot read file: {e}")
    
    # Try to count pages with reportlab/pikepdf if available
    try:
        import pikepdf
        with pikepdf.open(path) as pdf:
            info["pages"] = len(pdf.pages)
            if info["pages"] < min_pages:
                errors.append(f"Only {info['pages']} pages, expected >= {min_pages}")
    except ImportError:
        # Try PyPDF2
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(path)
            info["pages"] = len(reader.pages)
            if info["pages"] < min_pages:
                errors.append(f"Only {info['pages']} pages, expected >= {min_pages}")
        except ImportError:
            info["pages"] = "unknown (no PDF reader library installed)"
    except Exception as e:
        info["pages"] = f"error: {e}"
    
    return {"path": path, "valid": len(errors) == 0, "errors": errors, "info": info}


# === Product data validation ===

def check_product_data(title, description, price, prompts=None):
    """
    Validate product metadata.
    
    Returns:
        dict with: valid (bool), errors (list), warnings (list)
    """
    errors = []
    warnings = []
    
    if not title or len(title.strip()) < 5:
        errors.append("Title too short (min 5 chars)")
    if len(title or "") > 200:
        errors.append("Title too long (max 200 chars)")
    
    if not description or len(description.strip()) < 50:
        errors.append("Description too short (min 50 chars)")
    if len(description or "") > 5000:
        warnings.append("Description very long, may be truncated")
    
    if price is not None and price < 0:
        errors.append(f"Price cannot be negative: {price}")
    
    if prompts:
        if len(prompts) < 5:
            warnings.append(f"Only {len(prompts)} prompts, consider adding more")
        for i, p in enumerate(prompts):
            if not p.get("prompt"):
                errors.append(f"Prompt #{i+1} has empty 'prompt' field")
            if not p.get("category"):
                warnings.append(f"Prompt #{i+1} missing 'category'")
    
    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


# === Full product check ===

def check_product(pdf_path=None, cover_path=None, thumbnail_path=None,
                   title=None, description=None, price=None, prompts=None):
    """
    Run all checks on a complete product.
    
    Returns:
        dict with overall valid status, and detailed results for each component.
    """
    results = {
        "overall_valid": True,
        "checks": {},
        "summary": {"passed": 0, "failed": 0, "warnings": 0},
    }
    
    # PDF check
    if pdf_path:
        r = check_pdf(pdf_path)
        results["checks"]["pdf"] = r
        if r["valid"]:
            results["summary"]["passed"] += 1
        else:
            results["summary"]["failed"] += 1
            results["overall_valid"] = False
    
    # Cover check
    if cover_path:
        r = check_cover(cover_path)
        results["checks"]["cover"] = r
        if r["valid"]:
            results["summary"]["passed"] += 1
        else:
            results["summary"]["failed"] += 1
            results["overall_valid"] = False
    
    # Thumbnail check
    if thumbnail_path:
        r = check_thumbnail(thumbnail_path)
        results["checks"]["thumbnail"] = r
        if r["valid"]:
            results["summary"]["passed"] += 1
        else:
            results["summary"]["failed"] += 1
            results["overall_valid"] = False
    
    # Product data check
    if title or description or price is not None:
        r = check_product_data(title, description, price, prompts)
        results["checks"]["product_data"] = r
        if r["valid"]:
            results["summary"]["passed"] += 1
        else:
            results["summary"]["failed"] += 1
            results["overall_valid"] = False
        results["summary"]["warnings"] += len(r.get("warnings", []))
    
    return results


def print_report(results):
    """Print a human-readable QA report."""
    status = "PASS" if results["overall_valid"] else "FAIL"
    print(f"\n{'='*50}")
    print(f"  QA REPORT: {status}")
    print(f"  Passed: {results['summary']['passed']} | Failed: {results['summary']['failed']} | Warnings: {results['summary']['warnings']}")
    print(f"{'='*50}")
    
    for name, check in results["checks"].items():
        icon = "PASS" if check["valid"] else "FAIL"
        print(f"\n  [{icon}] {name.upper()}")
        
        if check.get("info"):
            for k, v in check["info"].items():
                print(f"      {k}: {v}")
        
        for err in check.get("errors", []):
            print(f"      ERROR: {err}")
        
        for warn in check.get("warnings", []):
            print(f"      WARN: {warn}")
    
    print(f"\n{'='*50}\n")


if __name__ == "__main__":
    # Quick test
    import tempfile
    
    # Create test files
    from PIL import Image
    
    tmp = tempfile.mkdtemp()
    
    # Test cover (correct size)
    img = Image.new("RGB", (1280, 720), (30, 30, 60))
    cover_path = os.path.join(tmp, "cover.jpg")
    img.save(cover_path)
    
    # Test thumbnail (correct size)
    img2 = Image.new("RGB", (600, 600), (30, 30, 60))
    thumb_path = os.path.join(tmp, "thumb.jpg")
    img2.save(thumb_path)
    
    # Test PDF
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    
    pdf_path = os.path.join(tmp, "test.pdf")
    doc = SimpleDocTemplate(pdf_path)
    doc.build([Paragraph("Test", getSampleStyleSheet()["Normal"])])
    
    # Run checks
    results = check_product(
        pdf_path=pdf_path,
        cover_path=cover_path,
        thumbnail_path=thumb_path,
        title="Test Product - Veo 3 Prompts",
        description="This is a test product description with enough characters to pass validation checks.",
        price=0,
        prompts=[{"title": "P1", "prompt": "Test prompt", "category": "Test"}] * 10,
    )
    print_report(results)
    
    # Cleanup
    import shutil
    shutil.rmtree(tmp)
