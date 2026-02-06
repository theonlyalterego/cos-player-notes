import mailbox
import os
import re
import hashlib
import base64
from bs4 import BeautifulSoup

# CONFIGURATION
MBOX_FILE = './emails/takeout-20260206T185416Z-3-001/Takeout/Mail/RPG-Curse of Strahd.mbox'
OUTPUT_DIR = 'cleaned_emails'
IMAGES_DIR = os.path.join(OUTPUT_DIR, 'images')

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

def save_image(image_data, content_id, filename_hint=None):
    """Save image data and return the relative path"""
    # Create a unique filename based on content ID or hash
    if content_id:
        # Strip < and > from content-id
        clean_cid = re.sub(r'[<>]', '', content_id)
        base_name = re.sub(r'[^\w.-]', '_', clean_cid)
    elif filename_hint:
        base_name = re.sub(r'[^\w.-]', '_', filename_hint)
    else:
        # Use hash of image data as fallback
        img_hash = hashlib.md5(image_data).hexdigest()[:12]
        base_name = f"image_{img_hash}"

    # Ensure proper extension
    if not any(base_name.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
        base_name += '.jpg'

    img_path = os.path.join(IMAGES_DIR, base_name)

    # Save if not already exists
    if not os.path.exists(img_path):
        with open(img_path, 'wb') as f:
            f.write(image_data)

    # Return relative path from HTML file perspective
    return f'images/{base_name}'

def extract_images_and_html(message):
    """Extract HTML body and save all image attachments, returning HTML with updated image paths"""
    html_body = None
    image_map = {}  # Maps content-id to file path

    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get('Content-Disposition', ''))

            # Get HTML body
            if content_type == 'text/html' and 'attachment' not in content_disposition:
                html_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')

            # Extract images
            elif content_type.startswith('image/'):
                content_id = part.get('Content-Id')
                filename = part.get_filename()
                image_data = part.get_payload(decode=True)

                if image_data:
                    img_path = save_image(image_data, content_id, filename)
                    if content_id:
                        image_map[content_id.strip('<>')] = img_path
                    if filename:
                        # Also map by filename for non-cid references
                        image_map[filename] = img_path
    else:
        # Not multipart - just get the body
        html_body = message.get_payload(decode=True).decode('utf-8', errors='ignore')

    return html_body, image_map

def clean_html(html_content, image_map):
    """Clean HTML and update image references to use local paths"""
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, 'html.parser')

    # Nuke the typical Gmail clutter
    for tag in soup(['style', 'script', 'meta', 'link', 'title']):
        tag.decompose()

    # Update image sources
    for img in soup.find_all('img'):
        src = img.get('src', '')

        # Handle cid: references (inline images)
        if src.startswith('cid:'):
            cid = src[4:]  # Remove 'cid:' prefix
            if cid in image_map:
                img['src'] = image_map[cid]

        # Handle data URIs - extract and save them
        elif src.startswith('data:image/'):
            try:
                # Parse data URI: data:image/png;base64,iVBORw0KG...
                _, data = src.split(',', 1)
                image_data = base64.b64decode(data)
                img_path = save_image(image_data, None)
                img['src'] = img_path
            except Exception as e:
                print(f"Failed to process data URI: {e}")

        # Handle potential filename references
        elif src in image_map:
            img['src'] = image_map[src]

    # Standardize links to open in new tabs
    for a in soup.find_all('a', href=True):
        a['target'] = "_blank"
        a['rel'] = "noopener noreferrer"

    # Return cleaned HTML (keep structure, not just text)
    return str(soup)

threads = {}

for message in mailbox.mbox(MBOX_FILE):
    subject = str(message['subject'] or "Untitled Journal Entry")
    clean_subj = re.sub(r'^(Re|Fwd|FW):\s+', '', subject, flags=re.IGNORECASE).strip()

    # Extract HTML and images
    html_body, image_map = extract_images_and_html(message)

    # Store thread info
    if clean_subj not in threads:
        threads[clean_subj] = []

    threads[clean_subj].append({
        'date': message['date'],
        'body': clean_html(html_body, image_map)
    })

# Write out the files as complete HTML documents
for subject, messages in threads.items():
    safe_filename = re.sub(r'[^\w\s-]', '', subject).strip().replace(' ', '_') + '.html'

    with open(os.path.join(OUTPUT_DIR, safe_filename), 'w', encoding='utf-8') as f:
        # Write complete HTML document
        f.write(f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject} - Curse of Strahd</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            padding: 2rem 0;
        }}
        .container {{
            max-width: 900px;
        }}
        .story-thread {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 2rem;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        }}
        .back-link {{
            color: #fff;
            text-decoration: none;
            margin-bottom: 1rem;
            display: inline-block;
        }}
        .back-link:hover {{
            color: #dc3545;
        }}
        img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            margin: 1rem 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <a href="index.html" class="back-link">← Back to Archives</a>
        <section class="story-thread">
            <h1 class="display-6 mb-4">{subject}</h1>
''')

        for msg in messages:
            f.write(f'''
            <div class="card shadow-sm mb-4 border-secondary">
                <div class="card-header bg-dark text-light d-flex justify-content-between">
                    <span>Journal Entry</span>
                    <small>{msg['date']}</small>
                </div>
                <div class="card-body bg-light">
                    {msg['body']}
                </div>
            </div>
''')

        f.write('''        </section>
    </div>
</body>
</html>
''')

print(f"Successfully processed {len(threads)} lore threads.")