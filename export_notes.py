import os
import xml.etree.ElementTree as ET

def extract_notes_to_html(xml_file, output_html):
    """
    Extracts notes from the given XML file and writes them to an HTML file.

    Args:
        xml_file (str): Path to the XML file.
        output_html (str): Path to the output HTML file.
    """
    try:
        # Parse the XML file
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Debugging: Print the structure of the XML file
        print("Root tag:", root.tag)
        print("Child tags under root:", [child.tag for child in root])

        # Find the <notes> section directly under <root>
        notes_section = root.find("notes")
        if notes_section is None:
            print("No <notes> section found in the XML file.")
            return

        def get_recursive_text(element):
            """Recursively extract text from an XML element and its children."""
            text = (element.text or "").strip()
            for child in element:
                text += get_recursive_text(child)
            text += (element.tail or "").strip()
            return text

        # Extract individual notes from nested <id-*> tags, skipping locked notes
        # Ensure notes are processed in the order they appear in the XML file
        notes = []
        for note in notes_section:
            # Skip notes that are locked
            locked = note.find("locked")
            if locked is not None:
                continue
            is_public = note.find("public")
            if is_public is None:
                continue

            note_title = note.find("name").text if note.find("name") is not None else "Untitled"
            note_content_element = note.find("text")
            # Preserve the semi-HTML content in the <text> sections
            note_content = ET.tostring(note_content_element, encoding='unicode', method='html') if note_content_element is not None else ""
            notes.append((note_title, note_content))

        # Generate HTML content with Bootstrap for better styling
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Player Notes</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
            <style>
                body { margin: 20px; }
                .note { margin-bottom: 20px; }
                .note-title { cursor: pointer; }
                .note-content { display: none; margin-top: 10px; }
            </style>
            <script>
                function toggleContent(id) {
                    const content = document.getElementById(id);
                    if (content.style.display === "none") {
                        content.style.display = "block";
                    } else {
                        content.style.display = "none";
                    }
                }
            </script>
        </head>
        <body class="container">
            <h1 class="text-center my-4">Player Notes</h1>
        """

        for idx, (title, content) in enumerate(notes):
            html_content += f"""
            <div class='note card'>
                <div class='card-header note-title' onclick=\"toggleContent('note-{idx}')\">
                    <h5 class='mb-0'>{title}</h5>
                </div>
                <div class='card-body note-content' id='note-{idx}'>
                    {content}
                </div>
            </div>
            """

        html_content += """
        </body>
        </html>
        """

        # Write to the output HTML file
        with open(output_html, "w", encoding="utf-8") as html_file:
            html_file.write(html_content)

        print(f"Notes successfully exported to {output_html}")

    except ET.ParseError:
        print("Error: Failed to parse the XML file. Please check the file for errors.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Define the input XML file and output HTML file
    xml_file = "db.xml"  # Update this path if the XML file is located elsewhere
    output_html = "player_notes.html"

    # Check if the XML file exists
    if not os.path.exists(xml_file):
        print(f"Error: The file '{xml_file}' does not exist.")
    else:
        # Run the extraction
        extract_notes_to_html(xml_file, output_html)