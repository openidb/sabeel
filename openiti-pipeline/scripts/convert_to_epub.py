#!/usr/bin/env python3
"""
OpenITI to EPUB Converter
Converts OpenITI mARkdown texts to EPUB format for Kavita
"""

import os
import sys
import subprocess
import re
import json
from pathlib import Path

try:
    import oitei
except ImportError:
    print("Error: oitei library not found. Please install: pip install oitei")
    sys.exit(1)

# Load Arabic metadata mapping
def load_arabic_metadata():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    metadata_file = os.path.join(script_dir, 'arabic_metadata.json')
    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

ARABIC_METADATA = load_arabic_metadata()


def extract_metadata_from_filename(filename):
    """
    Extract metadata from OpenITI filename.
    Format: DeathDate.AuthorName.BookTitle.SourceID-lang
    """
    basename = os.path.basename(filename)
    # Remove extension if present
    basename = re.sub(r'\.(mARkdown|completed|inProgress)$', '', basename)

    parts = basename.split('.')
    if len(parts) < 3:
        return None

    # Extract death year (first 4 digits)
    death_year = parts[0][:4] if parts[0][:4].isdigit() else "Unknown"

    # Author name (remove death year prefix)
    author_name = parts[0][4:] if len(parts[0]) > 4 else "Unknown"
    # Convert camelCase to readable name
    author_name = re.sub(r'([a-z])([A-Z])', r'\1 \2', author_name)

    # Book title
    book_title = parts[1] if len(parts) > 1 else "Unknown"
    # Convert camelCase to readable title
    book_title = re.sub(r'([a-z])([A-Z])', r'\1 \2', book_title)

    # Source ID (e.g., Shamela0001349-ara1)
    source_id = parts[2] if len(parts) > 2 else "Unknown"

    # Extract Shamela ID if present
    shamela_match = re.search(r'(Shamela|Sham19Y)(\d+)', source_id)
    shamela_id = shamela_match.group(2) if shamela_match else ""

    # Check if we have Arabic metadata for this file
    if basename in ARABIC_METADATA:
        arabic_data = ARABIC_METADATA[basename]
        author_name = arabic_data.get('author', author_name)
        book_title = arabic_data.get('title', book_title)

    return {
        'death_year': death_year,
        'author': author_name,
        'title': book_title,
        'source_id': source_id,
        'shamela_id': shamela_id,
        'basename': basename
    }


def convert_markdown_to_tei(markdown_file):
    """
    Convert OpenITI mARkdown to TEI XML using oitei
    """
    print(f"  Reading mARkdown file...")

    try:
        with open(markdown_file, 'r', encoding='utf-8') as f:
            markdown_text = f.read()
    except Exception as e:
        print(f"  Error reading file: {e}")
        return None

    print(f"  Converting to TEI XML...")
    try:
        tei_obj = oitei.convert(markdown_text)
        tei_string = tei_obj.tostring()
        return tei_string
    except Exception as e:
        print(f"  Error converting to TEI: {e}")
        return None


def create_metadata_xml(metadata, output_file):
    """
    Create EPUB metadata XML file for Pandoc
    """
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
  <dc:title>{metadata['title']}</dc:title>
  <dc:creator>{metadata['author']}</dc:creator>
  <dc:language>ar</dc:language>
  <dc:date>{metadata['death_year']} AH</dc:date>
  <dc:source>Shamela {metadata['shamela_id']}</dc:source>
  <dc:publisher>OpenITI</dc:publisher>
</metadata>
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(xml_content)


def convert_tei_to_html(tei_content, metadata):
    """
    Convert TEI XML content to properly structured HTML with chapters
    """
    import re
    import xml.etree.ElementTree as ET

    try:
        # Parse TEI XML
        root = ET.fromstring(tei_content)
        ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

        # Find body element
        body = root.find('.//tei:text/tei:body', ns)
        if body is None:
            # Fallback to simple extraction
            return convert_tei_to_html_simple(tei_content, metadata)

        # Extract div sections (chapters)
        divs = body.findall('.//tei:div', ns)

        chapters_html = []
        chapter_num = 0

        for div in divs:
            # Get chapter heading
            head = div.find('.//tei:head', ns)
            if head is not None and head.text and head.text.strip():
                chapter_num += 1
                heading_text = head.text.strip()

                # Get all paragraphs in this div
                paragraphs = []
                for p in div.findall('.//tei:p', ns):
                    # Use itertext() to get all text content properly
                    para_text = ' '.join(p.itertext()).strip()

                    # Clean up the text - remove all extra whitespace and leading/trailing spaces
                    para_text = ' '.join(para_text.split())  # Normalize whitespace
                    para_text = para_text.strip()  # Remove any leading/trailing whitespace

                    # Remove any leading non-breaking spaces or unusual whitespace characters
                    para_text = re.sub(r'^[\s\u00A0\u2000-\u200F\u202F\u205F\u3000]+', '', para_text)
                    para_text = re.sub(r'[\s\u00A0\u2000-\u200F\u202F\u205F\u3000]+$', '', para_text)

                    # Skip empty paragraphs and metadata markers
                    if para_text and not para_text.startswith('PageV') and not para_text.startswith('Milestone'):
                        # Don't add RTL mark - let CSS handle RTL direction
                        paragraphs.append(f'<p>{para_text}</p>')

                # Create chapter section with proper heading
                if paragraphs:
                    # Don't add RTL mark - let CSS handle it
                    chapter_html = f'''
<section epub:type="chapter" class="chapter">
    <h2>{heading_text}</h2>
    {''.join(paragraphs)}
</section>
'''
                    chapters_html.append(chapter_html)

        # If no chapters found, use simple conversion
        if not chapters_html:
            return convert_tei_to_html_simple(tei_content, metadata)

        # Build complete HTML with proper structure
        html = f'''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>{metadata['title']}</title>
</head>
<body>
    <section epub:type="titlepage" class="titlepage">
        <h1>{metadata['title']}</h1>
        <p><strong>المؤلف:</strong> {metadata['author']} (ت. {metadata['death_year']} هـ)</p>
        <p><strong>المصدر:</strong> شاملة {metadata['shamela_id']}</p>
        <hr/>
    </section>
    {''.join(chapters_html)}
</body>
</html>'''

        return html

    except Exception as e:
        print(f"  Warning: XML parsing failed ({e}), using simple conversion")
        return convert_tei_to_html_simple(tei_content, metadata)


def convert_tei_to_html_simple(tei_content, metadata):
    """
    Simple fallback conversion for TEI to HTML
    """
    import re

    # Extract text content between <body> tags
    body_match = re.search(r'<body[^>]*>(.*?)</body>', tei_content, re.DOTALL)
    if not body_match:
        return None

    body_content = body_match.group(1)

    # Convert basic TEI elements to HTML
    body_content = re.sub(r'<div[^>]*>', '<div>', body_content)
    body_content = re.sub(r'<head>(.*?)</head>', r'<h2 class="chapter">\1</h2>', body_content)
    body_content = re.sub(r'<lb\s*/>', ' ', body_content)  # Line breaks to spaces
    body_content = re.sub(r'<pb[^>]*>', '', body_content)  # Remove page breaks
    body_content = re.sub(r'<([a-z]+)[^>]*>', r'<\1>', body_content)

    # Build complete HTML
    html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{metadata['title']}</title>
</head>
<body>
    <h1>{metadata['title']}</h1>
    <p><strong>المؤلف:</strong> {metadata['author']} (ت. {metadata['death_year']} هـ)</p>
    <hr/>
    {body_content}
</body>
</html>"""

    return html


def convert_tei_to_epub(tei_file, epub_file, metadata, css_file):
    """
    Convert TEI XML to EPUB using Pandoc (via HTML intermediate)
    """
    print(f"  Converting TEI to EPUB...")

    # Read TEI content
    with open(tei_file, 'r', encoding='utf-8') as f:
        tei_content = f.read()

    # Convert to HTML
    html_content = convert_tei_to_html(tei_content, metadata)
    if not html_content:
        print(f"  ✗ Could not extract content from TEI")
        return False

    # Save HTML file
    html_file = tei_file.replace('.xml', '.html')
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # Create metadata file
    metadata_file = tei_file.replace('.xml', '-metadata.xml')
    create_metadata_xml(metadata, metadata_file)

    # Build Pandoc command (HTML to EPUB)
    # Use --epub-chapter-level=2 to split at h2 headings (our chapters)
    cmd = [
        'pandoc',
        html_file,
        '-f', 'html',
        '-t', 'epub3',
        '--epub-metadata=' + metadata_file,
        '--css=' + css_file,
        '--epub-chapter-level=2',  # Split chapters at h2 level
        '--metadata', f'title={metadata["title"]}',
        '--metadata', f'author={metadata["author"]}',
        '--metadata', 'lang=ar',
        '--metadata', 'dir=rtl',
        '-o', epub_file
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"  ✓ EPUB created successfully")
        # Clean up intermediate files
        os.remove(metadata_file)
        os.remove(html_file)
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Pandoc error: {e.stderr}")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def convert_single_file(markdown_file, output_dir, css_file):
    """
    Convert a single OpenITI mARkdown file to EPUB
    """
    print(f"\nProcessing: {os.path.basename(markdown_file)}")

    # Extract metadata
    metadata = extract_metadata_from_filename(markdown_file)
    if not metadata:
        print(f"  ✗ Could not extract metadata from filename")
        return False

    print(f"  Author: {metadata['author']}")
    print(f"  Title: {metadata['title']}")
    print(f"  Death Year: {metadata['death_year']} AH")
    print(f"  Source: {metadata['source_id']}")

    # Create output filenames
    base_name = metadata['basename']
    tei_file = os.path.join(output_dir, f"{base_name}.xml")
    epub_file = os.path.join(output_dir, f"{base_name}.epub")

    # Step 1: Convert to TEI
    tei_content = convert_markdown_to_tei(markdown_file)
    if not tei_content:
        return False

    # Save TEI file
    with open(tei_file, 'w', encoding='utf-8') as f:
        f.write(tei_content)
    print(f"  ✓ TEI XML saved: {os.path.basename(tei_file)}")

    # Step 2: Convert to EPUB
    success = convert_tei_to_epub(tei_file, epub_file, metadata, css_file)

    if success:
        # Check file size
        size_mb = os.path.getsize(epub_file) / (1024 * 1024)
        print(f"  File size: {size_mb:.2f} MB")

        # Optionally remove intermediate TEI file
        # os.remove(tei_file)

    return success


def main():
    if len(sys.argv) < 2:
        print("Usage: python convert_to_epub.py <markdown_file> [output_dir]")
        print("   or: python convert_to_epub.py --batch <file_list> [output_dir]")
        sys.exit(1)

    # Determine script directory for CSS file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    css_file = os.path.join(script_dir, 'arabic-rtl.css')

    if not os.path.exists(css_file):
        print(f"Error: CSS file not found: {css_file}")
        sys.exit(1)

    # Batch mode
    if sys.argv[1] == '--batch':
        if len(sys.argv) < 3:
            print("Error: --batch requires a file list")
            sys.exit(1)

        file_list = sys.argv[2]
        output_dir = sys.argv[3] if len(sys.argv) > 3 else '../output'
        os.makedirs(output_dir, exist_ok=True)

        with open(file_list, 'r') as f:
            files = [line.strip() for line in f if line.strip()]

        print(f"Processing {len(files)} files...")
        successful = 0
        failed = 0

        for markdown_file in files:
            if not os.path.exists(markdown_file):
                print(f"\n✗ File not found: {markdown_file}")
                failed += 1
                continue

            if convert_single_file(markdown_file, output_dir, css_file):
                successful += 1
            else:
                failed += 1

        print(f"\n{'='*60}")
        print(f"Batch Conversion Summary:")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Output directory: {output_dir}")
        print(f"{'='*60}")

    # Single file mode
    else:
        markdown_file = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else '../output'
        os.makedirs(output_dir, exist_ok=True)

        if not os.path.exists(markdown_file):
            print(f"Error: File not found: {markdown_file}")
            sys.exit(1)

        success = convert_single_file(markdown_file, output_dir, css_file)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
