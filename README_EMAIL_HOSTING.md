# Email to GitLab Pages Deployment

This setup converts your mbox email archive into a static website hosted on GitLab Pages, **with full image support**.

## What's Included

- **[clean_emails.py](clean_emails.py)** - Main script that:
  - Extracts emails from mbox format
  - Saves all image attachments to `images/` directory
  - Converts inline images (`cid:` references) to local paths
  - Extracts base64-encoded data URI images
  - Generates styled HTML pages with preserved images

- **[create_index.py](create_index.py)** - Generates a homepage listing all email threads

- **[.gitlab-ci.yml](.gitlab-ci.yml)** - GitLab CI configuration for automatic deployment

## How It Works

### Image Handling
The script handles three types of images in emails:

1. **Inline attachments** - Images with `Content-Id` headers referenced as `cid:xyz`
2. **Data URIs** - Base64-encoded images embedded directly in HTML (`data:image/png;base64,...`)
3. **Regular attachments** - Image files attached to emails

All images are:
- Extracted and saved to `cleaned_emails/images/`
- Given unique filenames based on their Content-ID or hash
- Referenced in HTML with relative paths (`images/filename.jpg`)

### Local Testing

Run locally to test:

```bash
# Install dependencies
pip install beautifulsoup4

# Process emails (creates cleaned_emails/ directory)
python clean_emails.py

# Generate index page
python create_index.py

# View locally
cd cleaned_emails
python -m http.server 8000
# Then open http://localhost:8000 in your browser
```

### GitLab Pages Deployment

1. **Push to GitLab** - Push this repo to GitLab
2. **Automatic Build** - GitLab CI will automatically:
   - Run `clean_emails.py` to process emails and extract images
   - Run `create_index.py` to create the index
   - Move output to `public/` directory
   - Deploy to GitLab Pages
3. **Access Your Site** - Visit `https://yourusername.gitlab.io/yourproject`

### GitLab Pages Configuration

No additional configuration needed! The `.gitlab-ci.yml` handles everything:
- Installs Python dependencies
- Runs the conversion scripts
- Deploys the `public/` directory as a static site
- All images are included in the deployment

### File Structure After Processing

```
cleaned_emails/
├── index.html              # Homepage with thread list
├── images/                 # All extracted images
│   ├── image_abc123.jpg
│   ├── logo_xyz789.png
│   └── ...
├── Thread_Name_1.html      # Individual thread pages
├── Thread_Name_2.html
└── ...
```

### Customization

**Styling**: Edit the CSS in [clean_emails.py](clean_emails.py) (lines 145-165) or [create_index.py](create_index.py)

**Output Location**: Change `OUTPUT_DIR` and `IMAGES_DIR` variables in [clean_emails.py](clean_emails.py)

**Email Source**: Update `MBOX_FILE` path in [clean_emails.py](clean_emails.py)

## Features

✅ Full image support (inline, attachments, data URIs)
✅ Responsive Bootstrap design
✅ Dark theme with gothic styling
✅ Email threading by subject
✅ Automatic index generation
✅ One-click GitLab Pages deployment
✅ All links open in new tabs
✅ Clean, clutter-free HTML

## Requirements

- Python 3.6+
- beautifulsoup4
- GitLab account (for hosting)

## Notes

- Images are stored separately and referenced via relative paths
- Works perfectly with GitLab Pages static hosting
- All image paths are relative, so the site works locally and on GitLab Pages
- Data URI images are automatically converted to files for better performance
