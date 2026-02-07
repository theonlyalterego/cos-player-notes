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

        # Add player_notes.html if it exists
        if os.path.exists('player_notes.html'):
            items.append({
                'filename': 'player_notes.html',
                'title': 'Player Notes',
                'type': 'notes',
                'size': os.path.getsize('player_notes.html'),
                'date': None
            })

        return sorted(items, key=lambda x: x['title'])

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
