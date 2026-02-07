#!/usr/bin/env python3
"""
Generate final deployment from saved content order.
Creates a single combined HTML file with all content in the specified order.
"""
import os
import json
import shutil
from pathlib import Path
from bs4 import BeautifulSoup

OUTPUT_DIR = 'cleaned_emails'
ORDER_FILE = 'content_order.json'
MESSAGE_EXCLUSIONS_FILE = 'message_exclusions.json'
FINAL_OUTPUT_DIR = 'public'
FINAL_HTML = os.path.join(FINAL_OUTPUT_DIR, 'index.html')

def load_order():
    """Load the saved content order"""
    if not os.path.exists(ORDER_FILE):
        print(f"Error: {ORDER_FILE} not found. Please organize content first.")
        return None

    with open(ORDER_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('items', [])

def load_message_exclusions():
    """Load message-level exclusions"""
    if not os.path.exists(MESSAGE_EXCLUSIONS_FILE):
        return []

    with open(MESSAGE_EXCLUSIONS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('exclusions', [])

def extract_player_note(filepath, note_id, title):
    """Extract a specific note from player_notes.html"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')

    # Find the note by ID
    note_content = soup.find('div', id=note_id)
    if note_content:
        # Get the parent card to include the header
        note_card = note_content.find_parent('div', class_='note')
        if note_card:
            # Remove the onclick and styling that's for the collapsible interface
            header = note_card.find('div', class_='card-header')
            if header:
                if header.has_attr('onclick'):
                    del header['onclick']
                header['class'] = ['card-header', 'bg-info', 'text-white']

            # Make content visible (remove display:none)
            if note_content.has_attr('style'):
                del note_content['style']
            note_content['class'] = ['card-body']

            return title, str(note_card)

    return title, f'<p>Note not found: {note_id}</p>'

def extract_body_content(filepath, message_exclusions, filename):
    """Extract the main content from an HTML file, filtering out excluded messages"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')

    # Get list of excluded dates for this file
    excluded_dates = [e['date'] for e in message_exclusions if e['filename'] == filename]

    # Try to find the main content section
    main_content = soup.find('section', class_='story-thread')
    if main_content:
        # Get the title
        title_elem = main_content.find('h1')
        title = title_elem.get_text() if title_elem else 'Untitled'

        # Remove the title from content (we'll add it back in our format)
        if title_elem:
            title_elem.decompose()

        # Filter out excluded messages
        cards = main_content.find_all('div', class_='card')
        removed_count = 0
        for card in cards:
            # Check if this message's date is in the exclusion list
            header = card.find('div', class_='card-header')
            if header:
                date_elem = header.find('small')
                if date_elem:
                    message_date = date_elem.get_text(strip=True)
                    if message_date in excluded_dates:
                        card.decompose()
                        removed_count += 1

        if removed_count > 0:
            print(f"  Excluded {removed_count} message(s) from '{title}'")

        return title, str(main_content)

    # Fallback: get body content
    body = soup.find('body')
    if body:
        return os.path.basename(filepath).replace('.html', '').replace('_', ' '), str(body)

    return 'Untitled', content

def generate_combined_html(ordered_items):
    """Generate a single HTML file with all content in order"""
    os.makedirs(FINAL_OUTPUT_DIR, exist_ok=True)

    # Load message exclusions
    message_exclusions = load_message_exclusions()
    if message_exclusions:
        print(f"Loaded {len(message_exclusions)} message-level exclusion(s)")

    # Filter out excluded items (DM only)
    excluded_count = sum(1 for item in ordered_items if item.get('excluded', False))
    ordered_items = [item for item in ordered_items if not item.get('excluded', False)]

    if excluded_count > 0:
        print(f"Excluding {excluded_count} DM-only thread(s) from player deployment")

    # Copy images directory
    source_images = os.path.join(OUTPUT_DIR, 'images')
    dest_images = os.path.join(FINAL_OUTPUT_DIR, 'images')
    if os.path.exists(source_images):
        if os.path.exists(dest_images):
            shutil.rmtree(dest_images)
        shutil.copytree(source_images, dest_images)
        print(f"Copied {len(os.listdir(source_images))} images to {dest_images}")

    # Start building the combined HTML
    html_parts = []

    # Header
    html_parts.append('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Curse of Strahd - Campaign Chronicle</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            padding: 2rem 0;
        }
        .container {
            max-width: 1000px;
        }
        .hero {
            text-align: center;
            padding: 3rem 0 2rem;
            color: #fff;
        }
        .hero h1 {
            font-size: 3.5rem;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.7);
            margin-bottom: 1rem;
        }
        .hero p {
            font-size: 1.2rem;
            opacity: 0.9;
        }
        .content-section {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        }
        .section-title {
            color: #1a1a2e;
            border-bottom: 3px solid #dc3545;
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
        }
        .story-thread {
            margin-bottom: 2rem;
        }
        .card {
            margin-bottom: 1.5rem;
        }
        img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            margin: 1rem 0;
        }
        .toc {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        }
        .toc h2 {
            color: #1a1a2e;
            margin-bottom: 1rem;
        }
        .toc ul {
            list-style: none;
            padding-left: 0;
        }
        .toc li {
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(0,0,0,0.1);
        }
        .toc a {
            color: #dc3545;
            text-decoration: none;
            font-weight: 500;
        }
        .toc a:hover {
            color: #c82333;
            text-decoration: underline;
        }
        .section-number {
            display: inline-block;
            background: #dc3545;
            color: white;
            padding: 0.2rem 0.6rem;
            border-radius: 4px;
            font-size: 0.85rem;
            font-weight: bold;
            margin-right: 0.5rem;
        }
        .footer {
            text-align: center;
            color: #fff;
            opacity: 0.7;
            padding: 2rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>🏰 Curse of Strahd</h1>
            <p>Campaign Chronicle</p>
        </div>

        <div class="toc">
            <h2>📜 Table of Contents</h2>
            <ul>
''')

    # Generate TOC and collect content
    content_sections = []
    for idx, item in enumerate(ordered_items, 1):
        filename = item['filename']
        title = item['title']

        # Add to TOC
        section_id = f"section-{idx}"
        html_parts.append(f'                <li><a href="#{section_id}"><span class="section-number">{idx}</span>{title}</a></li>\n')

        # Get content
        # Check if this is an individual player note
        if filename.startswith('player_notes.html#'):
            actual_file, note_id = filename.split('#', 1)
            filepath = actual_file
            if os.path.exists(filepath):
                content_title, content_body = extract_player_note(filepath, note_id, title)
                content_sections.append({
                    'id': section_id,
                    'number': idx,
                    'title': content_title,
                    'body': content_body,
                    'type': item['type']
                })
            else:
                print(f"Warning: File not found: {filepath}")
        elif filename == 'player_notes.html':
            # Legacy: handle old single player_notes item
            filepath = filename
            if os.path.exists(filepath):
                content_title, content_body = extract_body_content(filepath, message_exclusions, filename)
                content_sections.append({
                    'id': section_id,
                    'number': idx,
                    'title': content_title,
                    'body': content_body,
                    'type': item['type']
                })
            else:
                print(f"Warning: File not found: {filepath}")
        else:
            # Regular email thread
            filepath = os.path.join(OUTPUT_DIR, filename)
            if os.path.exists(filepath):
                content_title, content_body = extract_body_content(filepath, message_exclusions, filename)
                content_sections.append({
                    'id': section_id,
                    'number': idx,
                    'title': content_title,
                    'body': content_body,
                    'type': item['type']
                })
            else:
                print(f"Warning: File not found: {filepath}")

    # Close TOC
    html_parts.append('''            </ul>
        </div>

''')

    # Add all content sections
    for section in content_sections:
        html_parts.append(f'''        <div class="content-section" id="{section['id']}">
            <h2 class="section-title">
                <span class="section-number">{section['number']}</span>
                {section['title']}
            </h2>
            {section['body']}
        </div>

''')

    # Footer
    html_parts.append('''        <div class="footer">
            <p>Campaign Chronicle • Generated from Email Archives</p>
        </div>
    </div>
</body>
</html>
''')

    # Write the final file
    with open(FINAL_HTML, 'w', encoding='utf-8') as f:
        f.write(''.join(html_parts))

    print(f"\n✓ Generated {FINAL_HTML}")
    print(f"✓ Combined {len(content_sections)} content sections")
    print(f"\nDeployment ready in '{FINAL_OUTPUT_DIR}' directory!")
    print(f"To preview: cd {FINAL_OUTPUT_DIR} && python -m http.server 8080")

def main():
    print("Generating final deployment...\n")

    # Load the saved order
    ordered_items = load_order()
    if not ordered_items:
        print("No ordered items found. Please use the organizer interface first.")
        return

    print(f"Loaded order with {len(ordered_items)} items")

    # Generate the combined HTML
    generate_combined_html(ordered_items)

if __name__ == '__main__':
    main()
