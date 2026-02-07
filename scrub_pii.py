#!/usr/bin/env python3
"""
Scrub PII (Personally Identifiable Information) from the public deployment.
Run this after generate_final.py and before deploying to GitLab Pages.
"""
import re
import os
import json

PUBLIC_HTML = os.path.join('public', 'index.html')
PII_CONFIG_FILE = 'pii_config.json'

# PII patterns to scrub
PII_PATTERNS = [
    # Email addresses - replace with generic text
    {
        'pattern': r'mailto:[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'replacement': '#',
        'description': 'email links'
    },
    {
        'pattern': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'replacement': '[email removed]',
        'description': 'email addresses'
    },
    # Phone numbers (if any)
    {
        'pattern': r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
        'replacement': '[phone removed]',
        'description': 'phone numbers'
    },
]

def load_name_replacements():
    """
    Load name replacements from pii_config.json.
    Returns empty dict if file doesn't exist.
    """
    if not os.path.exists(PII_CONFIG_FILE):
        print(f"WARNING: {PII_CONFIG_FILE} not found. No name replacements will be applied.")
        print(f"         Create {PII_CONFIG_FILE} to configure name scrubbing.")
        return {}

    try:
        with open(PII_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('name_replacements', {})
    except Exception as e:
        print(f"ERROR: Failed to load {PII_CONFIG_FILE}: {e}")
        return {}

def scrub_pii_from_html(html_content, name_replacements):
    """
    Scrub PII from HTML content using regex patterns.

    Args:
        html_content: HTML string to scrub
        name_replacements: Dict of regex patterns to replacement strings
    """
    changes_made = []

    # Apply PII pattern replacements
    for pii in PII_PATTERNS:
        pattern = pii['pattern']
        replacement = pii['replacement']
        description = pii['description']

        matches = re.findall(pattern, html_content, re.IGNORECASE)
        if matches:
            changes_made.append(f"Removed {len(matches)} {description}")
            html_content = re.sub(pattern, replacement, html_content, flags=re.IGNORECASE)

    # Apply name replacements
    for name_pattern, replacement in name_replacements.items():
        matches = re.findall(name_pattern, html_content)
        if matches:
            changes_made.append(f"Replaced {len(matches)} instance(s) of '{name_pattern}' with '{replacement}'")
            html_content = re.sub(name_pattern, replacement, html_content)

    return html_content, changes_made

def main():
    print("PII Scrubber for Campaign Chronicle\n")

    if not os.path.exists(PUBLIC_HTML):
        print(f"ERROR: {PUBLIC_HTML} not found.")
        print("   Please run generate_final.py first.")
        return

    # Load name replacements from config
    print(f"Loading configuration from {PII_CONFIG_FILE}...")
    name_replacements = load_name_replacements()

    if not name_replacements:
        print("\nWARNING: No name replacements configured!")
        print("         Only email addresses and phone numbers will be scrubbed.\n")

    print(f"Reading {PUBLIC_HTML}...")

    # Method 1: Regex-based scrubbing
    with open(PUBLIC_HTML, 'r', encoding='utf-8') as f:
        original_content = f.read()

    original_size = len(original_content)

    # Apply scrubbing
    cleaned_content, changes = scrub_pii_from_html(original_content, name_replacements)

    # Write back
    with open(PUBLIC_HTML, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)

    final_size = len(cleaned_content)
    size_diff = original_size - final_size

    print(f"\nPII Scrubbing Complete!\n")

    if changes:
        print("Changes made:")
        for change in changes:
            print(f"   - {change}")
    else:
        print("   No PII found - file is clean!")

    print(f"\nStats:")
    print(f"   Original size: {original_size:,} bytes")
    print(f"   Final size:    {final_size:,} bytes")
    if size_diff > 0:
        print(f"   Removed:       {size_diff:,} bytes")

    print(f"\n{PUBLIC_HTML} is now ready for deployment!")
    print(f"\nNext steps:")
    print(f"   1. Review the cleaned file: open {PUBLIC_HTML} in a browser")
    print(f"   2. If satisfied, commit and push:")
    print(f"      git add public/")
    print(f"      git commit -m 'Update campaign content'")
    print(f"      git push origin main")

if __name__ == '__main__':
    main()
