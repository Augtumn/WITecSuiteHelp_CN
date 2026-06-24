"""Convert translated CHM to PDF

Requirements:
    pip install weasyprint beautifulsoup4
    
    or (better quality, faster):
    Download wkhtmltopdf from https://wkhtmltopdf.org/downloads.html
    pip install pdfkit

Usage:
    python chm_to_pdf.py              # Auto-detect best available tool
    python chm_to_pdf.py --weasyprint # Force weasyprint
    python chm_to_pdf.py --wkhtml     # Force wkhtmltopdf
"""

import re
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
WORK_DIR = BASE_DIR / "chm_extracted_cn"
HHC_PATH = WORK_DIR / "WITecSuiteHelp.hhc"
OUTPUT_PDF = BASE_DIR / "WITecSuiteHelp_CN.pdf"


def parse_hhc():
    """Parse HHC file to get ordered page list"""
    content = HHC_PATH.read_text(encoding="gb2312")

    # Extract all Local values in order (these define the page sequence)
    pages = re.findall(r'<param name="Local" value="([^"]+)"', content)
    return pages


def build_combined_html(pages, output_path):
    """Build a single combined HTML with TOC navigation"""
    print(f"Building combined HTML from {len(pages)} pages...")

    css = """
    <style>
        body { font-family: 'Microsoft YaHei', 'SimSun', sans-serif; font-size: 11pt; line-height: 1.6; }
        h1 { font-size: 16pt; color: #151f6d; border-bottom: 2px solid #ea7600; padding-bottom: 4px; margin-top: 30px; }
        h2 { font-size: 14pt; color: #151f6d; }
        img { max-width: 100%; height: auto; }
        .page-break { page-break-after: always; }
        .toc { margin: 20px 0; }
        .toc a { color: #0000ff; text-decoration: none; }
        .toc ul { list-style: none; padding-left: 0; }
        .toc li { margin: 4px 0; }
        pre, code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-size: 9pt; }
        table { border-collapse: collapse; margin: 10px 0; }
        td, th { border: 1px solid #808080; padding: 4px 8px; }
    </style>
    """

    html_parts = [
        '<!DOCTYPE html><html><head><meta charset="UTF-8">',
        '<title>WITec Suite 帮助</title>',
        css,
        '</head><body>',
        '<h1>WITec Suite 帮助</h1>',
        '<p>翻译：<a href="https://www.deepseek.com/">DeepSeek</a> &amp; <a href="https://github.com/Augtumn">Augtumn</a></p>',
        '<p>原始版权归 WITec GmbH 所有</p>',
        '<hr>',
    ]

    # Build TOC
    html_parts.append('<div class="toc"><h2>目录</h2>')
    # Parse HHC structure for nested TOC
    hhc_content = HHC_PATH.read_text(encoding="gb2312")
    toc_entries = re.findall(
        r'<param name="Name" value="([^"]+)".*?<param name="Local" value="([^"]+)"',
        hhc_content, re.DOTALL
    )
    seen = set()
    for name, local in toc_entries:
        if local not in seen and local in pages:
            seen.add(local)
            html_parts.append(f'<a href="#{local}">{name}</a><br>')
    html_parts.append('</div><hr>')

    # Embed each page
    for i, page in enumerate(pages):
        f = WORK_DIR / page
        if not f.exists():
            continue

        try:
            page_content = f.read_text(encoding="utf-8")
        except Exception:
            continue

        # Extract only body content (strip header/footer/nav)
        body_match = re.search(
            r'<div id="FHScroll">(.*?)</div>\s*</body>',
            page_content, re.DOTALL
        )
        if body_match:
            body = body_match.group(1)
        else:
            # Fallback: extract just the body
            bm = re.search(r'<body[^>]*>(.*?)</body>', page_content, re.DOTALL)
            body = bm.group(1) if bm else page_content

        # Fix image paths (relative to work dir)
        body = body.replace('src="Images/', f'src="{WORK_DIR.as_posix()}/Images/')

        # Fix internal links: href="OtherPage.html" → href="#OtherPage.html"
        def rewrite_link(m):
            href = m.group(1)
            if href.startswith(('http://', 'https://', 'mailto:', '#')):
                return m.group(0)  # External link, leave as-is
            if '.html' in href:
                return f'href="#{href}"'
            return m.group(0)

        body = re.sub(r'href="([^"]+)"', rewrite_link, body)

        html_parts.append(f'<div id="{page}">')
        html_parts.append(body)
        html_parts.append('</div>')
        html_parts.append('<div class="page-break"></div>')

        if (i + 1) % 50 == 0:
            print(f"  {i + 1}/{len(pages)} pages processed...")

    html_parts.append('</body></html>')

    combined = '\n'.join(html_parts)
    output_path.write_text(combined, encoding="utf-8")
    print(f"  Combined HTML: {output_path} ({len(combined):,} chars)")


def convert_weasyprint(html_path, pdf_path):
    """Convert using weasyprint (pure Python, needs GTK on Windows)"""
    print("Converting with weasyprint...")
    try:
        from weasyprint import HTML
        HTML(filename=str(html_path)).write_pdf(str(pdf_path))
        print(f"  PDF created: {pdf_path} ({pdf_path.stat().st_size / 1024 / 1024:.1f} MB)")
    except ImportError:
        raise
    except OSError as e:
        if "libgobject" in str(e) or "cannot load library" in str(e):
            print("\n  WeasyPrint needs GTK libraries on Windows.")
            print("  Recommend: open _combined.html in browser → Ctrl+P → Save as PDF")
            print("  Or install wkhtmltopdf and run: python chm_to_pdf.py --wkhtml")
            sys.exit(1)
        raise


def convert_wkhtmltopdf(html_path, pdf_path):
    """Convert using wkhtmltopdf (best quality)"""
    print("Converting with wkhtmltopdf...")

    # Find wkhtmltopdf
    wk_paths = [
        r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe",
        r"C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe",
    ]
    wk = None
    for p in wk_paths:
        if Path(p).exists():
            wk = p
            break

    if not wk:
        # Try PATH
        try:
            subprocess.run(["wkhtmltopdf", "--version"], capture_output=True)
            wk = "wkhtmltopdf"
        except FileNotFoundError:
            pass

    if not wk:
        print("  wkhtmltopdf not found.")
        print("  Download: https://wkhtmltopdf.org/downloads.html")
        return False

    subprocess.run([
        wk,
        "--enable-local-file-access",
        "--page-size", "A4",
        "--margin-top", "15mm",
        "--margin-bottom", "15mm",
        "--margin-left", "15mm",
        "--margin-right", "15mm",
        "--encoding", "UTF-8",
        str(html_path),
        str(pdf_path),
    ], check=True)
    print(f"  PDF created: {pdf_path} ({pdf_path.stat().st_size / 1024 / 1024:.1f} MB)")
    return True


def main():
    force = sys.argv[1] if len(sys.argv) > 1 else ""

    print("=" * 60)
    print("WITec Suite CHM → PDF Converter")
    print("=" * 60)

    if not HHC_PATH.exists():
        print(f"\nERROR: {HHC_PATH} not found")
        print("Run translation first, then try again.")
        sys.exit(1)

    pages = parse_hhc()
    print(f"\nPages to convert: {len(pages)}")

    # Build combined HTML
    combined_html = BASE_DIR / "chm_extracted_cn" / "_combined.html"
    build_combined_html(pages, combined_html)

    # Convert to PDF
    if force == "--wkhtml":
        convert_wkhtmltopdf(combined_html, OUTPUT_PDF)
    elif force == "--weasyprint":
        convert_weasyprint(combined_html, OUTPUT_PDF)
    else:
        # Try wkhtmltopdf first, fallback to weasyprint
        try:
            ok = convert_wkhtmltopdf(combined_html, OUTPUT_PDF)
            if not ok:
                raise RuntimeError("wkhtmltopdf not available")
        except Exception:
            print("\n  wkhtmltopdf failed or not found. Trying weasyprint...")
            try:
                convert_weasyprint(combined_html, OUTPUT_PDF)
            except ImportError:
                print("\n  ERROR: Neither wkhtmltopdf nor weasyprint available.")
                print("  Install one of:")
                print("    pip install weasyprint")
                print("    OR download wkhtmltopdf from https://wkhtmltopdf.org/downloads.html")
                sys.exit(1)

    # Cleanup
    combined_html.unlink(missing_ok=True)

    print(f"\n{'=' * 60}")
    print(f"PDF: {OUTPUT_PDF}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
