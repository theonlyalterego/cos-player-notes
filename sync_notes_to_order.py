import json
import os
from bs4 import BeautifulSoup

# CONFIGURATION
PLAYER_NOTES_HTML = 'player_notes.html'
CONTENT_ORDER_JSON = 'content_order.json'

def extract_notes_from_html(html_file):
    """Extract all note IDs and titles from player_notes.html"""
    if not os.path.exists(html_file):
        print(f"Error: {html_file} not found")
        return []

    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    notes = []
    for card in soup.find_all('div', class_='note'):
        # Extract note ID from the card-body
        card_body = card.find('div', class_='card-body')
        if card_body and card_body.get('id'):
            note_id = card_body.get('id')

            # Extract title from card-header
            card_header = card.find('div', class_='card-header')
            if card_header:
                h5 = card_header.find('h5')
                title = h5.get_text(strip=True) if h5 else "Untitled"

                notes.append({
                    'note_id': note_id,
                    'title': title
                })

    return notes

def sync_notes_to_content_order():
    """Add any new notes to content_order.json"""
    # Extract all notes from player_notes.html
    html_notes = extract_notes_from_html(PLAYER_NOTES_HTML)
    if not html_notes:
        print("No notes found in player_notes.html")
        return

    print(f"Found {len(html_notes)} notes in {PLAYER_NOTES_HTML}")

    # Load existing content_order.json
    if not os.path.exists(CONTENT_ORDER_JSON):
        print(f"Error: {CONTENT_ORDER_JSON} not found")
        return

    with open(CONTENT_ORDER_JSON, 'r', encoding='utf-8') as f:
        content_order = json.load(f)

    # Get existing note IDs
    existing_note_ids = set()
    for item in content_order['items']:
        if item.get('type') == 'note' and item.get('note_id'):
            existing_note_ids.add(item['note_id'])

    print(f"Found {len(existing_note_ids)} notes already in {CONTENT_ORDER_JSON}")

    # Find new notes
    new_notes = []
    for note in html_notes:
        if note['note_id'] not in existing_note_ids:
            new_notes.append(note)

    if not new_notes:
        print("✓ All notes are already in content_order.json - no changes needed")
        return

    print(f"\nFound {len(new_notes)} new note(s) to add:")

    # Append new notes to content_order
    for note in new_notes:
        new_entry = {
            "filename": f"player_notes.html#{note['note_id']}",
            "title": f"📝 {note['title']}",
            "type": "note",
            "size": 0,  # Size will be updated if needed
            "date": None,
            "note_id": note['note_id'],
            "excluded": False
        }
        content_order['items'].append(new_entry)
        print(f"  + {note['title']} ({note['note_id']})")

    # Write updated content_order.json
    with open(CONTENT_ORDER_JSON, 'w', encoding='utf-8') as f:
        json.dump(content_order, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Successfully added {len(new_notes)} new note(s) to {CONTENT_ORDER_JSON}")
    print(f"  New notes appended at the end - run your organizer to reorder if needed")

if __name__ == "__main__":
    sync_notes_to_content_order()
