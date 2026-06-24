"""Recompile translated CHM using hh.exe (built-in Windows HTML Help compiler)

Usage: python recompile_chm.py

This script:
1. Copies static assets (JS, CSS, Images) to the output directory
2. Generates/updates the .hhp project file
3. Attempts to compile using hh.exe (if available)
4. Falls back to instructions for HTML Help Workshop
"""

import shutil
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(r"D:\Code\WITec")
INPUT_DIR = BASE_DIR / "chm_extracted"
OUTPUT_DIR = BASE_DIR / "chm_extracted_cn"

def copy_static_assets():
    """Copy JavaScript, CSS, and images to output directory"""
    print("[1/3] Copying static assets...")
    
    # JS and CSS files
    for ext in ['.js', '.css']:
        for f in INPUT_DIR.glob(f'*{ext}'):
            shutil.copy2(f, OUTPUT_DIR / f.name)
            print(f"  Copied {f.name}")
    
    # Images directory
    images_src = INPUT_DIR / "Images"
    images_dst = OUTPUT_DIR / "Images"
    if images_src.exists():
        if images_dst.exists():
            shutil.rmtree(images_dst)
        shutil.copytree(images_src, images_dst)
        img_count = sum(1 for _ in images_dst.rglob('*') if _.is_file())
        print(f"  Copied Images/ ({img_count} files)")

def generate_hhp():
    """Generate .hhp project file"""
    print("[2/3] Generating HHP project file...")
    
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
    with open(hhp_path, 'w', encoding='utf-8') as f:
        f.write(hhp_content)
    print(f"  Created HHP with {len(html_files)} files")

def try_compile():
    """Try to compile using available tools"""
    print("[3/3] Compiling CHM...")
    
    hhp_path = OUTPUT_DIR / "WITecSuiteHelp.hhp"
    
    # Try HTML Help Workshop (hhw.exe)
    hhw_paths = [
        r"C:\Program Files (x86)\HTML Help Workshop\hhw.exe",
        r"C:\Program Files\HTML Help Workshop\hhw.exe",
    ]
    
    for hhw in hhw_paths:
        if Path(hhw).exists():
            print(f"  Using HTML Help Workshop: {hhw}")
            result = subprocess.run([hhw, str(hhp_path)], 
                                    capture_output=True, text=True, 
                                    cwd=str(OUTPUT_DIR))
            if result.returncode == 0:
                chm_path = OUTPUT_DIR / "WITecSuiteHelp_CN.chm"
                if chm_path.exists():
                    print(f"  SUCCESS! Created: {chm_path}")
                    print(f"  Size: {chm_path.stat().st_size / 1024 / 1024:.1f} MB")
                    return True
    
    print("\n  HTML Help Workshop (hhw.exe) not found.")
    print("  To compile manually:")
    print(f"  1. Install HTML Help Workshop from: C:\\Users\\15817\\Downloads\\htmlhelp.exe")
    print(f"  2. Open: {hhp_path}")
    print(f"  3. File → Compile")
    print(f"\n  Or try the command line method:")
    print(f'  & "C:\\Program Files (x86)\\HTML Help Workshop\\hhw.exe" "{hhp_path}"')
    return False

def main():
    print("=" * 60)
    print("WITec Suite CHM Recompiler")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if translations exist
    html_count = len(list(OUTPUT_DIR.glob("*.html")))
    hhc_exists = (OUTPUT_DIR / "WITecSuiteHelp.hhc").exists()
    
    if html_count == 0:
        print("\nERROR: No translated HTML files found in output directory!")
        print("Run translate_chm.py first, or wait for subagent translations to complete.")
        sys.exit(1)
    
    print(f"\nFound: {html_count} HTML files")
    print(f"HHC: {'Yes' if hhc_exists else 'No'}")
    
    copy_static_assets()
    generate_hhp()
    success = try_compile()
    
    print(f"\n{'=' * 60}")
    if success:
        print("DONE! WITecSuiteHelp_CN.chm is ready.")
    else:
        print("Ready for manual compilation.")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
