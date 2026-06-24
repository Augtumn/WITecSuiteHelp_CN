"""Recompile translated CHM from chm_extracted_cn/ workspace

Usage:
    python recompile_chm.py            # Full recompile
    python recompile_chm.py --quick    # Skip encoding fix (if already applied)

Requirements:
    - Python 3.x (no extra packages needed)
    - Microsoft HTML Help Workshop (hhc.exe)
      Download: https://archive.org/details/html-help-workshop-1.32
      Default install path: C:\Program Files (x86)\HTML Help Workshop\hhc.exe

Workflow:
    1. Add <meta charset="UTF-8"> to all HTML files  
    2. Convert HHC/HHK to GB2312 (required by CHM compiler for zh-CN)
    3. Copy static assets (JS, CSS, Images) from original extraction
    4. Generate/update .hhp project file
    5. Compile with hhc.exe
"""

import shutil
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "chm_extracted"        # Original decompiled source
OUTPUT_DIR = BASE_DIR / "chm_extracted_cn"     # Translated workspace


def fix_html_encoding():
    """Add UTF-8 charset declaration to all HTML files"""
    print("[1/5] Fixing HTML encoding...")
    fixed = 0
    for f in OUTPUT_DIR.glob("*.html"):
        content = f.read_text(encoding="utf-8")
        if 'charset' not in content:
            old = '<meta http-equiv="Content-Style-Type"'
            new = '<meta charset="UTF-8">\n' + old
            content = content.replace(old, new)
            f.write_text(content, encoding="utf-8")
            fixed += 1
    print(f"  Added <meta charset='UTF-8'> to {fixed} files")


def fix_hhc_hhk_encoding():
    """Convert HHC and HHK to GB2312 (required by CHM compiler)"""
    print("[2/5] Fixing HHC/HHK encoding (UTF-8 -> GB2312)...")
    for fname in ["WITecSuiteHelp.hhc", "WITecSuiteHelp.hhk"]:
        f = OUTPUT_DIR / fname
        if not f.exists():
            print(f"  WARNING: {fname} not found, skipping")
            continue
        content = f.read_text(encoding="utf-8")
        # Remove UTF-8 charset (ignored by compiler, misleading)
        content = content.replace('<meta charset="UTF-8">\n', '')
        try:
            f.write_text(content, encoding="gb2312")
            print(f"  Converted {fname} to GB2312")
        except UnicodeEncodeError:
            f.write_text(content, encoding="gbk")
            print(f"  Converted {fname} to GBK (fallback)")


def copy_static_assets():
    """Copy JS, CSS, and Images from original extraction"""
    print("[3/5] Copying static assets...")
    if not INPUT_DIR.exists():
        print("  WARNING: chm_extracted/ not found.")
        print("  Run: hh -decompile chm_extracted WITecSuiteHelp.chm")
        return

    for ext in ['.js', '.css']:
        for f in INPUT_DIR.glob(f'*{ext}'):
            shutil.copy2(f, OUTPUT_DIR / f.name)

    images_src = INPUT_DIR / "Images"
    images_dst = OUTPUT_DIR / "Images"
    if images_src.exists():
        if images_dst.exists():
            shutil.rmtree(images_dst)
        shutil.copytree(images_src, images_dst)
    print("  Done")


def generate_hhp():
    """Generate .hhp project file with all HTML files listed"""
    print("[4/5] Generating HHP project file...")
    html_files = sorted(OUTPUT_DIR.glob("*.html"))
    file_lines = "\n".join(f.name for f in html_files)

    hhp_content = f"""[OPTIONS]
Compatibility=1.1 or later
Compiled file=WITecSuiteHelp_CN.chm
Contents file=WITecSuiteHelp.hhc
Index file=WITecSuiteHelp.hhk
Default topic=WelcomeToTheWITecSuite.html
Display compile progress=Yes
Language=0x804 中文(简体，中国)
Title=WITec Suite 帮助

[FILES]
{file_lines}
FHFlyoverPopupStyle.css
FHNonscroll.js
FHUtilities.js
FHFlyoverPopups.js

[INFOTYPES]
"""
    hhp_path = OUTPUT_DIR / "WITecSuiteHelp.hhp"
    hhp_path.write_text(hhp_content, encoding="utf-8")
    print(f"  {len(html_files)} HTML files listed")


def compile_chm():
    """Compile using hhc.exe (command-line HTML Help Compiler)"""
    print("[5/5] Compiling CHM...")

    hhp_path = OUTPUT_DIR / "WITecSuiteHelp.hhp"

    # Try hhc.exe first (command-line, most reliable)
    hhc_paths = [
        r"C:\Program Files (x86)\HTML Help Workshop\hhc.exe",
        r"C:\Program Files\HTML Help Workshop\hhc.exe",
    ]

    for hhc in hhc_paths:
        if Path(hhc).exists():
            print(f"  Compiler: {hhc}")
            result = subprocess.run(
                [hhc, str(hhp_path)],
                capture_output=True, text=True,
                cwd=str(OUTPUT_DIR),
            )
            # hhc.exe prints to stdout; check for output file
            chm_path = OUTPUT_DIR / "WITecSuiteHelp_CN.chm"
            if chm_path.exists():
                size_mb = chm_path.stat().st_size / (1024 * 1024)
                print(f"  SUCCESS: {chm_path.name} ({size_mb:.1f} MB)")

                # Copy to project root for convenience
                root_chm = BASE_DIR / "WITecSuiteHelp_CN.chm"
                shutil.copy2(chm_path, root_chm)
                print(f"  Copied to project root: {root_chm}")
                return True
            else:
                print(f"  Compilation may have failed. Output:")
                # Print last few lines of stderr
                lines = result.stderr.strip().split('\n')
                for line in lines[-5:]:
                    print(f"    {line}")
                return False

    # hhc.exe not found
    print("\n  ERROR: HTML Help Workshop not found.")
    print("  Download: https://archive.org/details/html-help-workshop-1.32")
    print("  Expected at: C:\\Program Files (x86)\\HTML Help Workshop\\hhc.exe")
    print(f"\n  After installation, run:")
    print(f'  & "C:\\Program Files (x86)\\HTML Help Workshop\\hhc.exe" "{hhp_path}"')
    return False


def main():
    quick = "--quick" in sys.argv

    print("=" * 60)
    print("WITec Suite CHM Recompiler")
    if quick:
        print("(Quick mode — skip encoding fix)")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    html_count = len(list(OUTPUT_DIR.glob("*.html")))
    if html_count == 0:
        print("\nERROR: No HTML files in chm_extracted_cn/")
        print("Run translate_chm.py first.")
        sys.exit(1)

    print(f"\nFound: {html_count} HTML files in chm_extracted_cn/")

    if not quick:
        fix_html_encoding()
        fix_hhc_hhk_encoding()
    else:
        print("[skip] Encoding fix")

    copy_static_assets()
    generate_hhp()
    success = compile_chm()

    print(f"\n{'=' * 60}")
    print("DONE" if success else "FAILED — see instructions above")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
