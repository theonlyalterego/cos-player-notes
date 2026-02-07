#!/usr/bin/env python3
"""
Simple server for organizing email threads and notes.
Provides API endpoints for loading content, saving order, and serving previews.
"""
import os
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import mimetypes

OUTPUT_DIR = 'cleaned_emails'
ORDER_FILE = 'content_order.json'
MESSAGE_EXCLUSIONS_FILE = 'message_exclusions.json'

class OrganizerHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # API: Get list of all content items
        if path == '/api/items':
            self.send_json(self.get_items())

        # API: Get saved order
        elif path == '/api/order':
            self.send_json(self.get_saved_order())

        # API: Preview content with message exclusions
        elif path.startswith('/api/preview-with-controls'):
            query = parse_qs(parsed_path.query)
            filename = query.get('file', [''])[0]
            self.send_preview_with_controls(filename)

        # API: Preview content (regular)
        elif path.startswith('/api/preview'):
            query = parse_qs(parsed_path.query)
            filename = query.get('file', [''])[0]
            self.send_preview(filename)

        # API: Get message exclusions
        elif path == '/api/message-exclusions':
            self.send_json(self.get_message_exclusions())

        # API: Get parsed messages from a file
        elif path.startswith('/api/messages'):
            query = parse_qs(parsed_path.query)
            filename = query.get('file', [''])[0]
            self.send_json(self.get_messages_from_file(filename))

        # Serve static files
        else:
            super().do_GET()

    def do_POST(self):
        parsed_path = urlparse(self.path)

        # API: Save order
        if parsed_path.path == '/api/save-order':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            order_data = json.loads(post_data.decode('utf-8'))

            with open(ORDER_FILE, 'w', encoding='utf-8') as f:
                json.dump(order_data, f, indent=2)

            self.send_json({'success': True, 'message': 'Order saved successfully'})

        # API: Save message exclusions
        elif parsed_path.path == '/api/save-message-exclusions':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            exclusions_data = json.loads(post_data.decode('utf-8'))

            with open(MESSAGE_EXCLUSIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(exclusions_data, f, indent=2)

            self.send_json({'success': True, 'message': 'Message exclusions saved'})

        else:
            self.send_error(404)

    def get_items(self):
        """Get list of all HTML files in cleaned_emails directory"""
        items = []

        if os.path.exists(OUTPUT_DIR):
            for filename in os.listdir(OUTPUT_DIR):
                if filename.endswith('.html') and filename != 'index.html':
                    filepath = os.path.join(OUTPUT_DIR, filename)
                    date = self.extract_date_from_file(filepath)
                    items.append({
                        'filename': filename,
                        'title': filename.replace('.html', '').replace('_', ' '),
                        'type': 'email',
                        'size': os.path.getsize(filepath),
                        'date': date
                    })

        # Add individual player notes if file exists
        if os.path.exists('player_notes.html'):
            notes = self.parse_player_notes()
            items.extend(notes)

        return sorted(items, key=lambda x: x['title'])

    def parse_player_notes(self):
        """Parse player_notes.html into individual note items"""
        from bs4 import BeautifulSoup

        try:
            with open('player_notes.html', 'r', encoding='utf-8') as f:
                content = f.read()

            soup = BeautifulSoup(content, 'html.parser')
            notes = []

            # Find all note cards
            note_divs = soup.find_all('div', class_='note')

            for idx, note_div in enumerate(note_divs):
                # Extract title from h5
                header = note_div.find('div', class_='card-header')
                title_elem = header.find('h5') if header else None
                title = title_elem.get_text(strip=True) if title_elem else f'Note {idx + 1}'

                # Get the note ID
                content_div = note_div.find('div', class_='note-content')
                note_id = content_div.get('id') if content_div else f'note-{idx}'

                notes.append({
                    'filename': f'player_notes.html#{note_id}',
                    'title': f'📝 {title}',
                    'type': 'note',
                    'size': len(str(note_div)),
                    'date': None,
                    'note_id': note_id
                })

            return notes
        except Exception as e:
            print(f"Error parsing player notes: {e}")
            return []

    def extract_date_from_file(self, filepath):
        """Extract the earliest date from an HTML file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                # Look for dates in card headers (format: <small>date</small>)
                import re
                dates = re.findall(r'<small>([^<]+)</small>', content)
                if dates:
                    return dates[0]  # Return the first (oldest) date
        except:
            pass
        return None

    def get_saved_order(self):
        """Load saved order from JSON file"""
        if os.path.exists(ORDER_FILE):
            with open(ORDER_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'items': []}

    def send_preview(self, filename):
        """Send HTML content for preview"""
        # Security: prevent path traversal
        filename = os.path.basename(filename)

        # Check in cleaned_emails first
        filepath = os.path.join(OUTPUT_DIR, filename)
        if not os.path.exists(filepath):
            # Check in root directory
            filepath = filename

        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        else:
            self.send_error(404, f'File not found: {filename}')

    def send_preview_with_controls(self, filename):
        """Send HTML content with message exclusion controls injected"""
        from bs4 import BeautifulSoup

        # Check if this is a player note reference
        note_id = None
        actual_filename = filename
        if '#' in filename:
            actual_filename, note_id = filename.split('#', 1)

        # Security: prevent path traversal
        actual_filename = os.path.basename(actual_filename)

        # Check in cleaned_emails first
        filepath = os.path.join(OUTPUT_DIR, actual_filename)
        if not os.path.exists(filepath):
            filepath = actual_filename

        if not os.path.exists(filepath):
            self.send_error(404, f'File not found: {actual_filename}')
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            soup = BeautifulSoup(content, 'html.parser')

            # If this is a player note, extract just that note
            if note_id and actual_filename == 'player_notes.html':
                note_div = soup.find('div', id=note_id)
                if note_div:
                    # Get the parent note card
                    note_card = note_div.find_parent('div', class_='note')
                    if note_card:
                        # Create a new minimal HTML with just this note
                        new_soup = BeautifulSoup(f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Player Note</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ margin: 20px; background: #f5f5f5; }}
        .note {{ margin-bottom: 20px; }}
    </style>
</head>
<body class="container">
    {str(note_card)}
</body>
</html>''', 'html.parser')
                        # Expand the note content to be visible
                        content_div = new_soup.find('div', id=note_id)
                        if content_div:
                            content_div['style'] = 'display: block;'
                        modified_content = str(new_soup)
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html; charset=utf-8')
                        self.end_headers()
                        self.wfile.write(modified_content.encode('utf-8'))
                        return

            # Load current exclusions
            exclusions = self.get_message_exclusions().get('exclusions', [])
            excluded_dates = [e['date'] for e in exclusions if e['filename'] == filename]

            # Find all message cards and inject exclude buttons
            cards = soup.find_all('div', class_='card')
            for idx, card in enumerate(cards):
                header = card.find('div', class_='card-header')
                if header:
                    date_elem = header.find('small')
                    if date_elem:
                        message_date = date_elem.get_text(strip=True)
                        is_excluded = message_date in excluded_dates

                        # Create exclude button
                        button_html = f'''
                        <button class="message-exclude-btn {'excluded' if is_excluded else ''}"
                                data-filename="{filename}"
                                data-date="{message_date}"
                                onclick="toggleMessageExclusion(this)"
                                style="float: right; margin-left: 10px; padding: 0.2rem 0.5rem; font-size: 0.75rem; border-radius: 3px; cursor: pointer; transition: all 0.2s; {'background: #dc3545; color: white; border: 1px solid #dc3545;' if is_excluded else 'background: transparent; color: #666; border: 1px solid #ccc;'}">
                            {'✓ Excluded' if is_excluded else '🚫 Exclude'}
                        </button>
                        '''
                        button_tag = BeautifulSoup(button_html, 'html.parser')
                        header.append(button_tag)

                        # Add excluded styling if needed
                        if is_excluded:
                            card['style'] = 'opacity: 0.5; border-color: #dc3545; background: #f8d7da;'

            # Inject JavaScript for handling exclusions
            script = soup.new_tag('script')
            script.string = '''
                function toggleMessageExclusion(button) {
                    const filename = button.dataset.filename;
                    const date = button.dataset.date;
                    const isExcluded = button.classList.contains('excluded');

                    // Send message to parent window
                    window.parent.postMessage({
                        type: 'toggleMessageExclusion',
                        filename: filename,
                        date: date,
                        excluded: !isExcluded
                    }, '*');

                    // Update button appearance
                    const card = button.closest('.card');
                    if (!isExcluded) {
                        button.classList.add('excluded');
                        button.textContent = '✓ Excluded';
                        button.style.background = '#dc3545';
                        button.style.color = 'white';
                        button.style.borderColor = '#dc3545';
                        if (card) {
                            card.style.opacity = '0.5';
                            card.style.borderColor = '#dc3545';
                            card.style.background = '#f8d7da';
                        }
                    } else {
                        button.classList.remove('excluded');
                        button.textContent = '🚫 Exclude';
                        button.style.background = 'transparent';
                        button.style.color = '#666';
                        button.style.borderColor = '#ccc';
                        if (card) {
                            card.style.opacity = '1';
                            card.style.borderColor = '';
                            card.style.background = '';
                        }
                    }
                }

                // Add hover effects
                document.addEventListener('DOMContentLoaded', function() {
                    const buttons = document.querySelectorAll('.message-exclude-btn');
                    buttons.forEach(btn => {
                        btn.addEventListener('mouseenter', function() {
                            if (!this.classList.contains('excluded')) {
                                this.style.background = '#f0f0f0';
                            }
                        });
                        btn.addEventListener('mouseleave', function() {
                            if (!this.classList.contains('excluded')) {
                                this.style.background = 'transparent';
                            }
                        });
                    });
                });
            '''
            soup.body.append(script)

            modified_content = str(soup)
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(modified_content.encode('utf-8'))

        except Exception as e:
            self.send_error(500, f'Error processing file: {str(e)}')

    def get_message_exclusions(self):
        """Load message exclusions from JSON file"""
        if os.path.exists(MESSAGE_EXCLUSIONS_FILE):
            with open(MESSAGE_EXCLUSIONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'exclusions': []}

    def get_messages_from_file(self, filename):
        """Parse individual messages from an HTML file"""
        from bs4 import BeautifulSoup

        # Security: prevent path traversal
        filename = os.path.basename(filename)

        # Check in cleaned_emails first
        filepath = os.path.join(OUTPUT_DIR, filename)
        if not os.path.exists(filepath):
            filepath = filename

        if not os.path.exists(filepath):
            return {'messages': []}

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            soup = BeautifulSoup(content, 'html.parser')
            messages = []

            # Find all message cards
            cards = soup.find_all('div', class_='card')
            for idx, card in enumerate(cards):
                # Extract date from card header
                header = card.find('div', class_='card-header')
                date_elem = header.find('small') if header else None
                date = date_elem.get_text(strip=True) if date_elem else None

                # Extract body preview (first 200 chars)
                body = card.find('div', class_='card-body')
                body_text = body.get_text(strip=True)[:200] + '...' if body and len(body.get_text(strip=True)) > 200 else body.get_text(strip=True) if body else ''

                messages.append({
                    'index': idx,
                    'date': date,
                    'preview': body_text,
                    'filename': filename
                })

            return {'messages': messages}
        except Exception as e:
            return {'messages': [], 'error': str(e)}

    def send_json(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, OrganizerHandler)
    print(f'Content Organizer running at http://localhost:{port}/')
    print(f'Open organize_interface.html in your browser')
    print('Press Ctrl+C to stop')
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
