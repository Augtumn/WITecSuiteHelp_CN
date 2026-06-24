#!/usr/bin/env python3
"""
WITec Suite CHM Help File Translator
Translates all HTML, HHC, and HHK files from English to Chinese
Uses OpenAI-compatible API with domain glossary for consistent terminology

Usage:
    pip install beautifulsoup4 openai tqdm
    set OPENAI_API_KEY=sk-...    (or any compatible API key)
    set OPENAI_BASE_URL=...       (optional, for non-OpenAI endpoints)
    python translate_chm.py

Output: chm_extracted_cn/ directory with all translated files
"""

import os
import json
import re
import time
import sys
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag, Comment

# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(r"D:\Code\WITec")
INPUT_DIR = BASE_DIR / "chm_extracted"
OUTPUT_DIR = BASE_DIR / "chm_extracted_cn"
GLOSSARY_PATH = BASE_DIR / "glossary.json"
PROGRESS_PATH = BASE_DIR / "translation_progress.json"

# API Configuration (set via environment variables)
API_KEY = os.environ.get("OPENAI_API_KEY", "")
API_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL = os.environ.get("TRANSLATION_MODEL", "gpt-4o-mini")

# Batch settings
BATCH_SIZE = 5  # Files per batch
RETRY_COUNT = 3
DELAY_BETWEEN_BATCHES = 1  # seconds

# ============================================================
# HTML TEXT NODES TO TRANSLATE
# ============================================================

# HTML tags whose text content SHOULD be translated
TRANSLATABLE_TAGS = {
    'p', 'li', 'td', 'th', 'span', 'div', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'b', 'strong', 'i', 'em', 'u', 'small', 'big', 'font', 'label', 'option',
    'caption', 'legend', 'dt', 'dd', 'pre', 'code', 'blockquote', 'cite', 'q',
    'sub', 'sup', 'br', 'summary', 'details'
}

# Tags whose text content should NOT be translated
SKIP_TAGS = {'script', 'style', 'noscript', 'map', 'area', 'param', 'object', 'meta'}

# HTML attributes that contain translatable text
TRANSLATABLE_ATTRS = {
    'img': ['alt', 'title'],
    'a': ['title'],
    'area': ['alt', 'title'],
    'input': ['placeholder', 'title', 'value'],
    'table': ['summary'],
    'abbr': ['title'],
    'acronym': ['title'],
}

# ============================================================
# LOAD GLOSSARY
# ============================================================

def load_glossary():
    """Load the WITec terminology glossary"""
    with open(GLOSSARY_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['glossary']

# ============================================================
# AI TRANSLATION CLIENT
# ============================================================

class TranslationClient:
    """OpenAI-compatible translation API client with glossary awareness"""

    def __init__(self, glossary: dict):
        self.glossary = glossary
        self.glossary_text = self._format_glossary()

        # Lazy import to avoid dependency if not translating
        from openai import OpenAI
        self.client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)

    def _format_glossary(self) -> str:
        """Format glossary as a reference text for the AI"""
        lines = []
        for en, zh in sorted(self.glossary.items()):
            lines.append(f"  {en} → {zh}")
        return '\n'.join(lines)

    def translate_text(self, english_text: str, context_title: str = "") -> str:
        """Translate a single text string using the LLM"""
        if not english_text or not english_text.strip():
            return english_text

        # Skip pure numbers, special chars only
        if re.match(r'^[\d\s\.\,\-\+\/\*\(\)\[\]\{\}\#\@\!\?\:\;\|\&\^\%\$\€\£\¥]+$', english_text.strip()):
            return english_text

        # Skip if already mostly CJK
        cjk_count = sum(1 for c in english_text if '\u4e00' <= c <= '\u9fff')
        if cjk_count > len(english_text) * 0.5:
            return english_text

        system_prompt = f"""You are a professional translator specializing in scientific instrumentation documentation. 
Translate English to Simplified Chinese (zh-CN).

CRITICAL RULES:
1. Use the EXACT Chinese terms from the glossary below - DO NOT invent new translations
2. Preserve ALL HTML tags, placeholders like {{0}}, and technical symbols exactly as-is
3. Keep numbers, units, file paths, code snippets, and product names (WITec, TrueSurface, etc.) unchanged
4. Maintain the original tone: technical, instructional, professional
5. For mathematical/scientific content, keep formulas and variable names unchanged
6. If a term is NOT in the glossary, use the most technically accurate Chinese equivalent
7. Return ONLY the Chinese translation - no explanations, no prefixes, no quotes

GLOSSARY (EN → ZH):
{self.glossary_text}"""

        for attempt in range(RETRY_COUNT):
            try:
                response = self.client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Translate this text from WITec Suite documentation (context: {context_title}):\n\n{english_text}"}
                    ],
                    temperature=0.1,
                    max_tokens=4000,
                )
                result = response.choices[0].message.content.strip()
                return result
            except Exception as e:
                if attempt < RETRY_COUNT - 1:
                    wait = (attempt + 1) * 5
                    print(f"  API error (attempt {attempt+1}/{RETRY_COUNT}): {e}, waiting {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"  FAILED after {RETRY_COUNT} attempts: {english_text[:80]}...")
                    return english_text
        return english_text

    def translate_batch(self, texts: list, context: str = "") -> list:
        """Translate multiple texts sequentially"""
        results = []
        for text in texts:
            results.append(self.translate_text(text, context))
        return results

# ============================================================
# HTML FILE TRANSLATOR
# ============================================================

class HTMLTranslator:
    """Translates FastHelp-generated HTML files while preserving structure"""

    def __init__(self, glossary: dict):
        self.glossary = glossary
        self.stats = {"files": 0, "texts": 0, "api_calls": 0, "errors": 0}

    def collect_translatable_texts(self, soup: BeautifulSoup) -> list:
        """Collect all translatable text nodes from an HTML soup, preserving order"""
        texts = []

        # 1. Title tag
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            texts.append(('title', title_tag.string.strip()))

        # 2. Meta keywords
        for meta in soup.find_all('meta', attrs={'name': 'keywords'}):
            if meta.get('content', '').strip():
                texts.append(('meta_keywords', meta['content'].strip()))

        # 3. Body text content
        body = soup.find('body')
        if body:
            for element in body.descendants:
                if isinstance(element, Comment):
                    continue
                if isinstance(element, NavigableString) and not isinstance(element.parent, Tag):
                    continue
                if isinstance(element, NavigableString) and element.parent.name not in SKIP_TAGS:
                    text = element.strip()
                    if text and len(text) > 0:
                        # Only translate meaningful text (>1 char and contains letters)
                        if re.search(r'[a-zA-Z]', text) and len(text) > 1:
                            texts.append(('body_text', text))

        return texts

    def translate_html_file(self, filepath: Path, client: TranslationClient) -> str:
        """Translate a single HTML file, return translated HTML string"""
        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, 'html.parser')
        page_title = ""
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            page_title = title_tag.string.strip()

        # --- Translate TITLE ---
        if title_tag and title_tag.string:
            title_text = title_tag.string.strip()
            if re.search(r'[a-zA-Z]', title_text):
                translated = client.translate_text(title_text, page_title)
                title_tag.string = translated

        # --- Translate meta keywords ---
        for meta in soup.find_all('meta', attrs={'name': 'keywords'}):
            kw_text = meta.get('content', '').strip()
            if kw_text and re.search(r'[a-zA-Z]', kw_text):
                translated = client.translate_text(kw_text, page_title)
                meta['content'] = translated

        # --- Translate BODY text ---
        body = soup.find('body')
        if body:
            self._translate_element_text(body, client, page_title)

        self.stats["files"] += 1
        return str(soup)

    def _translate_element_text(self, element, client: TranslationClient, page_title: str):
        """Recursively translate text nodes within an element"""
        for child in list(element.children):
            if isinstance(child, Comment):
                continue

            if isinstance(child, NavigableString):
                parent_name = child.parent.name if child.parent else None
                if parent_name in SKIP_TAGS:
                    continue

                text = str(child)
                stripped = text.strip()
                if stripped and re.search(r'[a-zA-Z]', stripped) and len(stripped) > 1:
                    # Don't translate if it looks like a file path, URL, or code
                    if not self._is_technical_string(stripped):
                        translated = client.translate_text(stripped, page_title)
                        child.replace_with(translated)
                        self.stats["texts"] += 1

            elif isinstance(child, Tag):
                # Skip script/style/noscript etc
                if child.name not in SKIP_TAGS:
                    # Translate translatable attributes
                    if child.name in TRANSLATABLE_ATTRS:
                        for attr_name in TRANSLATABLE_ATTRS[child.name]:
                            attr_value = child.get(attr_name, '')
                            if attr_value and re.search(r'[a-zA-Z]', attr_value.strip()):
                                translated = client.translate_text(attr_value.strip(), page_title)
                                child[attr_name] = translated

                    # Recurse into children (except special cases)
                    self._translate_element_text(child, client, page_title)

    def _is_technical_string(self, text: str) -> bool:
        """Check if a string is technical (file path, code, etc.) and should NOT be translated"""
        # File paths
        if re.match(r'^[A-Za-z]:[\\\/]', text):
            return True
        # URLs
        if re.match(r'^https?://', text):
            return True
        # Pure numbers with units
        if re.match(r'^[\d\.\s\-]+[A-Za-z%°]+$', text.strip()):
            return True
        # HTML comments
        if text.strip().startswith('<!--'):
            return True
        # Code-like
        if re.match(r'^[\{\}\[\]\(\)\;\:\<\>\=\.\,\+\-\*\/\&\|\!\#\@\$\%\^\_\~]+$', text.strip()):
            return True
        return False

# ============================================================
# HHC / HHK TRANSLATOR
# ============================================================

def translate_hhc_hhk(filepath: Path, glossary: dict, client: TranslationClient):
    """Translate HHC (TOC) or HHK (Index) file - only translate Name values"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    def translate_name(match):
        name_value = match.group(1)
        # Check glossary first
        if name_value in glossary:
            zh = glossary[name_value]
            return f'<param name="Name" value="{zh}"'
        # Translate via API
        if re.search(r'[a-zA-Z]', name_value):
            translated = client.translate_text(name_value, f"TOC Index: {name_value}")
            return f'<param name="Name" value="{translated}"'
        return match.group(0)

    translated = re.sub(
        r'<param name="Name" value="([^"]+)"',
        translate_name,
        content
    )
    return translated

# ============================================================
# MAIN TRANSLATION PIPELINE
# ============================================================

def load_progress():
    """Load translation progress to support resumption"""
    if PROGRESS_PATH.exists():
        with open(PROGRESS_PATH, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()

def save_progress(completed_files: set):
    """Save translation progress"""
    with open(PROGRESS_PATH, 'w', encoding='utf-8') as f:
        json.dump(list(completed_files), f, ensure_ascii=False)

def main():
    print("=" * 60)
    print("WITec Suite CHM Help File Translator")
    print("=" * 60)

    # Check API key
    if not API_KEY:
        print("\nERROR: OPENAI_API_KEY environment variable not set!")
        print("Set it with: set OPENAI_API_KEY=sk-...")
        print("Or for other providers: set OPENAI_BASE_URL=...")
        sys.exit(1)

    # Load glossary
    print(f"\n[1/4] Loading glossary...")
    glossary = load_glossary()
    print(f"  Loaded {len(glossary)} terminology entries")

    # Initialize client
    print(f"\n[2/4] Initializing translation client...")
    print(f"  Model: {MODEL}")
    print(f"  API: {API_BASE_URL}")
    client = TranslationClient(glossary)

    # Setup output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    completed = load_progress()
    html_translator = HTMLTranslator(glossary)

    # Collect all files to translate
    html_files = sorted(INPUT_DIR.glob("*.html"))
    hhc_file = INPUT_DIR / "WITecSuiteHelp.hhc"
    hhk_file = INPUT_DIR / "WITecSuiteHelp.hhk"

    print(f"\n[3/4] Translating files...")
    print(f"  HTML files: {len(html_files)}")
    print(f"  Already completed: {len(completed)}")
    if completed:
        print(f"  Remaining: {len(html_files) - len(set(str(f.name) for f in html_files) & completed)}")

    # --- Translate HTML files ---
    for i, html_path in enumerate(html_files):
        rel_name = html_path.name
        if rel_name in completed:
            continue

        print(f"  [{i+1}/{len(html_files)}] {rel_name} ...", end=" ", flush=True)

        try:
            translated_html = html_translator.translate_html_file(html_path, client)
            output_path = OUTPUT_DIR / rel_name
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(translated_html)
            completed.add(rel_name)
            print("OK")
        except Exception as e:
            print(f"ERROR: {e}")
            html_translator.stats["errors"] += 1

        # Save progress periodically
        if (i + 1) % 10 == 0:
            save_progress(completed)

        # Small delay to avoid rate limits
        if (i + 1) % BATCH_SIZE == 0:
            time.sleep(DELAY_BETWEEN_BATCHES)

    save_progress(completed)

    # --- Translate HHC ---
    print(f"\n  Translating TOC (HHC)...", end=" ", flush=True)
    try:
        translated_hhc = translate_hhc_hhk(hhc_file, glossary, client)
        output_hhc = OUTPUT_DIR / "WITecSuiteHelp.hhc"
        with open(output_hhc, 'w', encoding='utf-8') as f:
            f.write(translated_hhc)
        print("OK")
    except Exception as e:
        print(f"ERROR: {e}")

    # --- Translate HHK ---
    print(f"  Translating Index (HHK)...", end=" ", flush=True)
    try:
        translated_hhk = translate_hhc_hhk(hhk_file, glossary, client)
        output_hhk = OUTPUT_DIR / "WITecSuiteHelp.hhk"
        with open(output_hhk, 'w', encoding='utf-8') as f:
            f.write(translated_hhk)
        print("OK")
    except Exception as e:
        print(f"ERROR: {e}")

    # --- Copy static assets ---
    print(f"\n[4/4] Copying static assets...")
    import shutil
    for item in INPUT_DIR.iterdir():
        if item.is_file() and item.suffix.lower() in ['.js', '.css', '.png', '.gif', '.bmp']:
            shutil.copy2(item, OUTPUT_DIR / item.name)
    # Copy images directory
    images_src = INPUT_DIR / "Images"
    images_dst = OUTPUT_DIR / "Images"
    if images_src.exists():
        if images_dst.exists():
            shutil.rmtree(images_dst)
        shutil.copytree(images_src, images_dst)
        print(f"  Copied Images/ directory")

    # --- Report ---
    print(f"\n{'=' * 60}")
    print(f"TRANSLATION COMPLETE")
    print(f"{'=' * 60}")
    print(f"  HTML files translated: {html_translator.stats['files']}")
    print(f"  Text segments translated: {html_translator.stats['texts']}")
    print(f"  Errors: {html_translator.stats['errors']}")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"\nNext step: recompile CHM using HTML Help Workshop")
    print(f"  hhw.exe {OUTPUT_DIR / 'WITecSuiteHelp.hhp'}")

if __name__ == "__main__":
    main()
