"""
Gumroad Digital Product PDF Generator v2
Dark mode template with:
  - Clickable Table of Contents (anchor links to sections)
  - Category badges (e.g. [TIKTOK], [REELS], [B2B]) on prompt cards
  - Code syntax highlight boxes, flexbox layouts, professional typography
Uses Playwright HTML→PDF for best quality.

Usage:
    from pdf_template import generate_prompt_pack_pdf
    generate_prompt_pack_pdf(prompts, "output.pdf", title="My Prompt Pack")
"""

import os
import re
import unicodedata


# === Badge mapping: category keyword → badge label + color ===
BADGE_MAP = {
    "tiktok":       ("TIKTOK",  "#ff0050"),
    "short":        ("SHORT",   "#ff0050"),
    "reels":        ("REELS",   "#c13584"),
    "instagram":    ("REELS",   "#c13584"),
    "shorts":       ("SHORTS",  "#ff0000"),
    "youtube":      ("YOUTUBE", "#ff0000"),
    "fashion":      ("FASHION", "#e91e63"),
    "tech":         ("TECH",    "#00bcd4"),
    "education":    ("EDU",     "#4caf50"),
    "copywriting":  ("B2B",     "#ff9800"),
    "marketing":    ("B2B",     "#ff9800"),
    "funnel":       ("B2B",     "#ff9800"),
    "business":     ("B2B",     "#ff9800"),
    "client":       ("B2B",     "#ff9800"),
    "portrait":     ("PHOTO",   "#9c27b0"),
    "product":      ("PHOTO",   "#9c27b0"),
    "architecture": ("PHOTO",   "#9c27b0"),
    "landscape":    ("PHOTO",   "#9c27b0"),
    "cinematic":    ("CINEMA",  "#2196f3"),
    "film":         ("CINEMA",  "#2196f3"),
    "abstract":     ("ART",     "#607d8b"),
    "artistic":     ("ART",     "#607d8b"),
    "midjourney":   ("MIDJOURNEY", "#00e5ff"),
    "flux":         ("FLUX",    "#76ff03"),
    "chatgpt":      ("CHATGPT", "#10a37f"),
    "claude":       ("CLAUDE",  "#d97706"),
    "automation":   ("AUTO",    "#009688"),
    "solopreneur":  ("BIZ",     "#3f51b5"),
    "viral":        ("VIRAL",   "#e53935"),
    "hook":         ("HOOK",    "#e53935"),
    "script":       ("SCRIPT",  "#7b1fa2"),
    "content":      ("CONTENT", "#00897b"),
    "funnel":       ("FUNNEL",  "#f57c00"),
    "creator":      ("CREATOR", "#ab47bc"),
}


def _slugify(text):
    """Convert text to URL-safe slug."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[-\s]+", "-", text).strip("-")
    return text


def _get_badge(category):
    """Get badge label and color for a category."""
    cat_lower = category.lower()
    for keyword, (label, color) in BADGE_MAP.items():
        if keyword in cat_lower:
            return label, color
    return None, None


def generate_html(prompts, title="AI Prompt Pack", subtitle="The Ultimate Collection",
                  author="AI Prompt Studio", version="1.0", accent_color="#6c63ff",
                  dark_mode=True):
    """Generate a professional HTML document for PDF conversion.
    Includes clickable TOC and category badges."""

    categories = {}
    for p in prompts:
        cat = p.get("category", "General")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(p)

    # --- Build prompt cards HTML ---
    cards_html = ""
    for cat_name, items in categories.items():
        section_id = f"section-{_slugify(cat_name)}"
        badge_label, badge_color = _get_badge(cat_name)
        badge_html = ""
        if badge_label:
            badge_html = f'<span class="badge" style="background:{badge_color}">{badge_label}</span>'

        cards_html += f'<h2 class="category-title" id="{section_id}">{badge_html} {cat_name}</h2>\n'
        cards_html += '<div class="divider"></div>\n'
        for i, item in enumerate(items, 1):
            title_text = item.get("title", f"Prompt {i}")
            prompt_text = item.get("prompt", "")
            tip = item.get("tip", "")
            variables = item.get("variables", [])

            var_html = ""
            if variables:
                var_html = '<div class="variables"><strong>Variables:</strong> '
                var_html += ", ".join(f'<code>[{v}]</code>' for v in variables)
                var_html += "</div>"

            tip_html = f'<div class="tip">{tip}</div>' if tip else ""

            cards_html += f'''
            <div class="prompt-card">
                <div class="prompt-title">{title_text}</div>
                <div class="prompt-box">{prompt_text}</div>
                {var_html}
                {tip_html}
            </div>
            '''

    # --- Build TOC HTML (clickable links) ---
    toc_items = ""
    for i, (cat_name, items) in enumerate(categories.items(), 1):
        section_id = f"section-{_slugify(cat_name)}"
        badge_label, badge_color = _get_badge(cat_name)
        badge_html = ""
        if badge_label:
            badge_html = f' <span class="badge badge-sm" style="background:{badge_color}">{badge_label}</span>'
        toc_items += f'<li><a href="#{section_id}" class="toc-link">{i}. {cat_name}{badge_html} <span class="toc-count">({len(items)} prompts)</span></a></li>\n'

    # --- Dark mode colors ---
    bg = "#0f172a" if dark_mode else "#ffffff"
    text = "#e2e8f0" if dark_mode else "#333333"
    card_bg = "#1e293b" if dark_mode else "#f8f8ff"
    code_bg = "#0f172a" if dark_mode else "#f0f0ff"
    border = "#334155" if dark_mode else "#e0e0e0"
    link_color = accent_color

    html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@page {{
    size: A4;
    margin: 20mm 18mm;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    background: {bg};
    color: {text};
    font-size: 10pt;
    line-height: 1.5;
}}

/* === COVER === */
.cover {{
    page-break-after: always;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    min-height: 90vh;
    text-align: center;
}}
.cover h1 {{
    font-size: 28pt;
    color: #ffffff;
    margin-bottom: 8px;
    letter-spacing: 2px;
}}
.cover .subtitle {{
    font-size: 14pt;
    color: {accent_color};
    margin-bottom: 20px;
}}
.cover .meta {{
    font-size: 9pt;
    color: #888;
}}
.divider {{
    height: 2px;
    background: {accent_color};
    margin: 8px 0 16px 0;
    opacity: 0.5;
}}

/* === CLICKABLE TOC === */
.toc {{
    page-break-after: always;
}}
.toc h2 {{
    font-size: 18pt;
    color: {accent_color};
    margin-bottom: 16px;
}}
.toc ul {{
    list-style: none;
    padding: 0;
}}
.toc li {{
    padding: 6px 0;
    font-size: 11pt;
}}
.toc-link {{
    color: {text};
    text-decoration: none;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 8px;
    border-radius: 4px;
    transition: background 0.2s;
}}
.toc-link:hover {{
    background: {card_bg};
}}
.toc-count {{
    color: #888;
    font-size: 9pt;
}}

/* === BADGES === */
.badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 7pt;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: 1px;
    text-transform: uppercase;
    vertical-align: middle;
}}
.badge-sm {{
    padding: 1px 6px;
    font-size: 6.5pt;
}}

/* === CATEGORY SECTIONS === */
.category-title {{
    font-size: 16pt;
    color: {accent_color};
    margin-top: 24px;
    margin-bottom: 4px;
    page-break-after: avoid;
    scroll-margin-top: 20mm;
}}

/* === PROMPT CARDS === */
.prompt-card {{
    background: {card_bg};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 12px;
    page-break-inside: avoid;
}}
.prompt-title {{
    font-size: 11pt;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 6px;
}}
.prompt-box {{
    background: {code_bg};
    border-left: 3px solid {accent_color};
    padding: 10px 12px;
    font-family: "Cascadia Code", "Fira Code", "Consolas", monospace;
    font-size: 8.5pt;
    line-height: 1.4;
    border-radius: 4px;
    white-space: pre-wrap;
    word-break: break-word;
    color: #c8d6e5;
}}
.variables {{
    margin-top: 6px;
    font-size: 8.5pt;
    color: #aaa;
}}
.variables code {{
    background: {code_bg};
    padding: 1px 4px;
    border-radius: 3px;
    color: {accent_color};
    font-family: "Cascadia Code", monospace;
}}
.tip {{
    margin-top: 6px;
    font-size: 8.5pt;
    color: #999;
    font-style: italic;
}}

/* === FOOTER === */
.footer {{
    text-align: center;
    font-size: 8pt;
    color: #666;
    margin-top: 40px;
}}

/* === PRINT OVERRIDES === */
@media print {{
    .toc-link {{
        color: {text} !important;
        text-decoration: none !important;
    }}
}}
</style>
</head>
<body>

<!-- COVER PAGE -->
<div class="cover">
    <h1>{title}</h1>
    <div class="subtitle">{subtitle}</div>
    <div class="divider" style="width:60%"></div>
    <div class="meta">{len(prompts)} Expert-Crafted Prompts</div>
    <div class="meta">Version {version} | {author}</div>
</div>

<!-- CLICKABLE TABLE OF CONTENTS -->
<div class="toc">
    <h2>Table of Contents</h2>
    <ul>
    {toc_items}
    </ul>
    <div class="tip" style="margin-top:20px;">
        <strong>How to Use:</strong> Each prompt is ready to copy-paste.
        Modify [VARIABLES] to customize for your needs.
        Click any section above to jump directly to it.
    </div>
</div>

<!-- PROMPT SECTIONS -->
{cards_html}

<!-- FOOTER -->
<div class="footer">
    <p>Thank you! If this helped you, a 5-star review helps others find it.</p>
</div>

</body>
</html>'''
    return html


def generate_pdf_playwright(html_content, output_path):
    """Convert HTML to PDF using Playwright (best quality)."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html_content, wait_until="networkidle")
        page.pdf(path=output_path, format="A4", margin={
            "top": "20mm", "bottom": "20mm", "left": "18mm", "right": "18mm"
        })
        browser.close()


def generate_pdf_reportlab(prompts, output_path, title="AI Prompt Pack",
                           subtitle="The Ultimate Collection", accent_color="#6c63ff"):
    """Fallback: Generate PDF using ReportLab (no HTML/CSS support)."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            topMargin=25*mm, bottomMargin=20*mm,
                            leftMargin=20*mm, rightMargin=20*mm)
    styles = getSampleStyleSheet()

    title_s = ParagraphStyle('T', parent=styles['Title'], fontSize=28,
        textColor=colors.HexColor('#1a1a2e'), alignment=TA_CENTER)
    sub_s = ParagraphStyle('S', parent=styles['Normal'], fontSize=14,
        textColor=colors.HexColor(accent_color), alignment=TA_CENTER)
    cat_s = ParagraphStyle('C', parent=styles['Heading1'], fontSize=18,
        textColor=colors.HexColor(accent_color))
    ptitle_s = ParagraphStyle('PT', parent=styles['Normal'], fontSize=11,
        textColor=colors.HexColor('#1a1a2e'), fontName='Helvetica-Bold')
    pbox_s = ParagraphStyle('PB', parent=styles['Normal'], fontSize=9.5,
        fontName='Courier', backColor=colors.HexColor('#f5f5ff'),
        borderPadding=3*mm, leading=13)
    tip_s = ParagraphStyle('TI', parent=styles['Normal'], fontSize=9,
        textColor=colors.HexColor('#666'), fontName='Helvetica-Oblique')

    story = []
    story.append(Spacer(1, 40*mm))
    story.append(Paragraph(title, title_s))
    story.append(Paragraph(subtitle, sub_s))
    story.append(Spacer(1, 20*mm))
    story.append(PageBreak())

    categories = {}
    for p in prompts:
        cat = p.get("category", "General")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(p)

    for cat_name, items in categories.items():
        badge_label, _ = _get_badge(cat_name)
        badge_prefix = f"[{badge_label}] " if badge_label else ""
        story.append(Paragraph(f"{badge_prefix}{cat_name}", cat_s))
        story.append(HRFlowable(width="100%", thickness=1, spaceAfter=4*mm))
        for item in items:
            story.append(Paragraph(f"<b>{item.get('title', 'Prompt')}</b>", ptitle_s))
            story.append(Paragraph(item.get("prompt", ""), pbox_s))
            if item.get("tip"):
                story.append(Paragraph(item["tip"], tip_s))
            story.append(Spacer(1, 2*mm))
        story.append(PageBreak())

    doc.build(story)


def generate_prompt_pack_pdf(prompts, output_path, title="AI Prompt Pack",
                              subtitle="The Ultimate Collection", author="AI Prompt Studio",
                              version="1.0", dark_mode=True, accent_color="#6c63ff"):
    """
    Main entry point. Generates a professional PDF from prompt data.

    Features:
      - Clickable Table of Contents with anchor links
      - Category badges (e.g. [TIKTOK], [REELS], [B2B]) on section headings
      - Dark mode with code-style prompt boxes
      - Professional A4 typography

    Args:
        prompts: list of dicts with keys: title, prompt, category, tip, variables
        output_path: where to save the PDF
        title: product title
        subtitle: subtitle text
        author: author name
        version: version string
        dark_mode: use dark background (requires Playwright)
        accent_color: hex color for accents

    Returns:
        dict with: path, size, method (playwright/reportlab)
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    html = generate_html(prompts, title=title, subtitle=subtitle, author=author,
                         version=version, accent_color=accent_color, dark_mode=dark_mode)

    method = "reportlab"
    try:
        generate_pdf_playwright(html, output_path)
        method = "playwright"
    except Exception:
        generate_pdf_reportlab(prompts, output_path, title=title, subtitle=subtitle,
                              accent_color=accent_color)
        method = "reportlab"

    size = os.path.getsize(output_path)
    return {"path": output_path, "size": size, "method": method}


if __name__ == "__main__":
    # Quick test
    test_prompts = [
        {"title": "Epic Drone Shot", "prompt": "Cinematic aerial drone descending through clouds...",
         "category": "Cinematic", "tip": "Add camera movement", "variables": ["CITY", "TIME"]},
        {"title": "TikTok Hook", "prompt": "Stop scrolling! This one trick...",
         "category": "TikTok Short Form", "tip": "Pattern interrupt", "variables": ["TOPIC"]},
        {"title": "B2B Email", "prompt": "Subject line that gets 40% open rate...",
         "category": "Copywriting & Sales", "tip": "Use curiosity gap", "variables": ["PRODUCT"]},
    ]
    result = generate_prompt_pack_pdf(test_prompts, "test_output.pdf")
    print(f"Generated: {result}")
