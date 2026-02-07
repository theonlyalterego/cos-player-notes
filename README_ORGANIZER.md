# Content Organizer - Workflow Guide

This tool allows you to organize your emails and notes in a specific order for your players to read.

## 📋 Workflow Overview

1. **Process Emails** - Extract and clean emails from mbox
2. **Organize Content** - Use drag-and-drop interface to arrange content
3. **Generate Deployment** - Create final combined HTML file
4. **Deploy to GitLab** - Push and let CI/CD handle deployment

## 🚀 Step-by-Step Guide

### Step 1: Process Your Emails

First, run the email processor to extract and clean your emails:

```bash
pip install beautifulsoup4
python clean_emails.py
```

This creates:
- `cleaned_emails/` directory with individual HTML files
- `cleaned_emails/images/` with all extracted images
- De-duplicated content (no quoted replies)
- Chronologically ordered messages

### Step 2: Organize Content

Start the local organizer server:

```bash
python organize_server.py
```

Then open `organize_interface.html` in your browser (usually at `http://localhost:8000/organize_interface.html`).

The interface has three panels:

1. **📚 Available Content** (left)
   - Shows all email threads and player_notes.html
   - Drag items from here...

2. **📋 Ordered List** (middle)
   - Drop items here in the order you want
   - Drag to reorder within this list
   - Items are numbered automatically

3. **👁️ Preview** (right)
   - Click any item to preview its content
   - Review before finalizing

**Actions:**
- Drag items from Available → Ordered List
- Rearrange items within Ordered List
- Click items to preview
- **Click "🚫 Exclude" to mark as DM-only** (won't appear in player deployment)
- Click "👁️ Include" to unmark excluded items
- Click "💾 Save Order" when done

Excluded items are marked with "DM ONLY" badge and appear dimmed. They're saved in your order but won't be included in the final player-facing site.

The order is saved to `content_order.json`.

### Step 3: Generate Final Deployment

Once you've saved your order, generate the final combined HTML:

```bash
python generate_final.py
```

This creates:
- `public/index.html` - Single combined file with all content in order
- `public/images/` - All images copied over
- Table of contents with jump links
- Section numbers matching your organized order

**Preview locally:**
```bash
cd public
python -m http.server 8080
# Open http://localhost:8080
```

### Step 4: Deploy to GitLab Pages

Commit and push your changes (including `content_order.json`):

```bash
git add content_order.json player_notes.html
git commit -m "Updated content organization"
git push
```

GitLab CI will automatically:
1. Run `clean_emails.py` to process the mbox
2. Run `generate_final.py` using your saved order
3. Deploy the `public/` directory to GitLab Pages

Your site will be live at `https://yourusername.gitlab.io/yourproject/`

## 📁 File Structure

```
.
├── clean_emails.py           # Email processor (extracts from mbox)
├── organize_server.py         # Local server for organizer interface
├── organize_interface.html    # Drag-and-drop UI
├── generate_final.py          # Creates final combined deployment
├── content_order.json         # Your saved order (commit this!)
├── player_notes.html          # Your custom notes (if exists)
├── cleaned_emails/            # Intermediate files (gitignored)
│   ├── *.html
│   └── images/
└── public/                    # Final deployment (generated)
    ├── index.html
    └── images/
```

## 🔄 Making Changes

### Reorder Content

1. Run `python organize_server.py`
2. Open `organize_interface.html`
3. Rearrange items
4. Save order
5. Run `python generate_final.py` to regenerate
6. Commit `content_order.json`

### Add New Content

1. Add new emails to mbox file OR create new HTML files
2. Run `python clean_emails.py` to process
3. Run organizer to include new items
4. Save and regenerate

### Update Player Notes

1. Edit `player_notes.html` directly
2. Run `python generate_final.py` to regenerate
3. Commit changes

## 🎨 Customization

### Styling

Edit the `<style>` section in:
- `generate_final.py` (lines ~30-80) - Final deployment styles
- `organize_interface.html` - Organizer interface styles
- `clean_emails.py` (lines ~157-187) - Individual email page styles

### Content Structure

The final HTML includes:
- Hero header with campaign title
- Table of contents with section numbers
- Content sections in your specified order
- Each section is a linkable anchor

### Section Formatting

Individual emails are wrapped in Bootstrap cards with:
- Date headers
- Cleaned content (no quotes)
- Responsive images
- All links open in new tabs

## 🛠️ Troubleshooting

**"No items in Available Content"**
- Make sure you ran `clean_emails.py` first
- Check that `cleaned_emails/` directory exists with HTML files

**"Failed to save order"**
- Make sure `organize_server.py` is running
- Check console for error messages

**Images not showing in preview**
- Images load from `cleaned_emails/images/`
- Make sure the server can access this directory

**Generated site has broken images**
- Run `generate_final.py` again - it copies images to `public/`
- Images use relative paths: `images/filename.jpg`

**GitLab deployment has no content**
- Make sure `content_order.json` is committed to the repo
- Check GitLab CI logs for errors
- Verify mbox file path in `clean_emails.py` MBOX_FILE variable

## 💡 Tips

1. **Save Often** - The organizer auto-saves when you click Save Order
2. **Preview Everything** - Click each item to verify content looks good
3. **Test Locally** - Always run `generate_final.py` and preview before deploying
4. **Commit Order File** - Don't forget to commit `content_order.json`!
5. **Incremental Updates** - You can reorganize anytime, just regenerate and push

## 🔒 DM-Only Content (Exclude Feature)

Some emails contain DM notes or spoilers that shouldn't be visible to players. Use the **Exclude** feature to mark these:

1. In the organizer, click **"🚫 Exclude"** on any item
2. The item is marked with a "DM ONLY" badge and appears dimmed
3. The item stays in your ordered list (so you can track it)
4. When you run `generate_final.py`, excluded items are skipped
5. Players will never see excluded content in the deployment

**Use cases:**
- DM planning emails
- Spoiler-heavy discussions
- Behind-the-scenes campaign notes
- Future plot hooks not yet revealed

The excluded status is saved in `content_order.json` and preserved across sessions.

## 🎯 What Gets Deployed

**Players will see:**
- Single combined HTML page
- All content in your specified order (except excluded items)
- Table of contents for navigation
- Section numbers
- All images properly loaded
- Clean, professional formatting

**Players will NOT see:**
- Individual email files
- Quoted reply text
- Email clutter (scripts, styles, etc.)
- **Excluded (DM-only) content**
- Any files not in your ordered list
- The organizer interface (that's just for you!)

## 🔐 Security Note

The organizer server (`organize_server.py`) is **only for local use**. Don't expose it to the internet. It's meant to run on localhost while you organize content.
