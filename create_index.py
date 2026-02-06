import os
import re
from pathlib import Path

OUTPUT_DIR = 'cleaned_emails'

# Get all HTML files
html_files = sorted([f for f in os.listdir(OUTPUT_DIR) if f.endswith('.html')])

# Create index.html
with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
    f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Curse of Strahd - Campaign Journal</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            padding: 2rem 0;
        }
        .container {
            max-width: 900px;
        }
        .hero {
            text-align: center;
            padding: 3rem 0;
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
        .thread-list {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 2rem;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        }
        .thread-item {
            padding: 1rem;
            margin: 0.5rem 0;
            border-left: 4px solid #6c757d;
            background: #f8f9fa;
            border-radius: 5px;
            transition: all 0.3s ease;
        }
        .thread-item:hover {
            border-left-color: #dc3545;
            background: #fff;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            transform: translateX(5px);
        }
        .thread-item a {
            text-decoration: none;
            color: #212529;
            font-weight: 500;
            font-size: 1.1rem;
        }
        .thread-item a:hover {
            color: #dc3545;
        }
        .footer {
            text-align: center;
            color: #fff;
            opacity: 0.7;
            margin-top: 3rem;
            padding: 1rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>🏰 Curse of Strahd</h1>
            <p>Campaign Journal & Email Archive</p>
        </div>

        <div class="thread-list">
            <h2 class="mb-4">📜 Story Threads</h2>
''')

    # Add links to each thread
    for filename in html_files:
        # Convert filename back to readable title
        title = filename.replace('.html', '').replace('_', ' ')
        f.write(f'''            <div class="thread-item">
                <a href="{filename}">{title}</a>
            </div>
''')

    f.write('''        </div>

        <div class="footer">
            <p>Generated from email archives</p>
        </div>
    </div>
</body>
</html>
''')

print(f"Created index.html with {len(html_files)} thread links")
