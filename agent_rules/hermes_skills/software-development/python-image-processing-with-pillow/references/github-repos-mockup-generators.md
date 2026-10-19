# GitHub Repos: Python Product Mockup Generators

Research conducted 2026-07-30. All repos use Python + Pillow for image compositing.

## Repos Found

### CTDave001/automated_mockups - 68 stars
https://github.com/CTDave001/automated_mockups
- Focus: T-shirt, hoodie, product template compositing at scale
- Architecture: mockup_generator/ package with calculator.py (detects colored placeholder boxes via scikit-image), generator.py (composites with alignment/scale modes), utils.py, cli.py
- Key pattern: Detects target color in templates, extracts bbox + rotation, composites with Alignment (9 positions) and ScaleMode (fit/fill/stretch/none)
- Dependencies: Pillow, numpy, scikit-image
- Code quality: Production-grade, dataclass-based, threaded batch processing

### kashifulhaque/product-mockup-node-python - 46 stars
https://github.com/kashifulhaque/product-mockup-node-python
- Focus: Mask-based compositing using ImageMagick + Python/Node
- Pattern: Pre-create mask of replacement area, then ImageMagick composite
- Blog: https://ifkash.hashnode.dev/imagemagick-product-mockups
- Best for: Server-side batch mockup generation with ImageMagick

### devonjhills/etsy-digital-mockup-tools - 10 stars
https://github.com/devonjhills/etsy-digital-mockup-tools
- Focus: Full Etsy automation - mockups + AI content + OAuth listing upload
- Stack: Flask, Pillow, MoviePy, Google Gemini/OpenAI for SEO
- Mockup features: Dynamic color extraction, grid layouts, transparency demos
- Best reference for: End-to-end e-commerce product pipeline

### jjshay/mockup-generator - 2 stars
https://github.com/jjshay/mockup-generator
- Focus: Artwork framing + lifestyle room-scene compositing
- Key files: mockup_generator_with_frames.py, template_based_mockup_generator.py
- Pattern: add_mat_and_frame() - white mat (8% of art width) + black frame (20-30px), composite onto room photos at normalized (x, y, width, height) positions
- Best reference for: The mat+frame compositing pattern

## Search Queries That Worked
- "product mockup python pillow" (3 results)
- "pillow mockup generator" (3 results)
- "product mockup python" (10 results)
- "3D book cover python PIL" - 0 results (gap in ecosystem)
- "ebook cover mockup generator python" - 0 results

## Key Finding
No existing repo provides a pure-Pillow 3D book cover mockup generator. The CTDave001 repo is the most sophisticated general framework but uses scikit-image. Our standalone script fills the gap with book3d/tablet/card/framed styles using only Pillow.
