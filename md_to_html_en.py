import os
import sys
import re

def get_script_dir():
    """Returns the absolute path to the directory where the script is located."""
    return os.path.dirname(os.path.abspath(__file__))

def find_md_files(directory):
    """Finds all files with the .md extension in the given directory."""
    try:
        files = [f for f in os.listdir(directory) if f.lower().endswith('.md')]
        return sorted(files)
    except Exception as e:
        print(f"Error reading folder: {e}")
        return []

def escape_html(text):
    """Escapes HTML special characters in plain text."""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    return text

def make_slug(text):
    """Turns heading text into an anchor (id) for navigation."""
    slug = re.sub(r'[^\w\s-]', '', text, flags=re.UNICODE).strip().lower()
    slug = re.sub(r'[\s_]+', '-', slug)
    return slug or 'section'

def process_inline(text):
    """
    Applies inline Markdown formatting.
    Uses placeholders so that already generated tags are not escaped.
    """
    text = escape_html(text)

    protected = {}
    counter = [0]

    def protect(html_str):
        key = f"\x00PH{counter[0]}\x00"
        protected[key] = html_str
        counter[0] += 1
        return key

    # 1. Inline code: `code`
    def repl_code(m):
        return protect(f'<code>{m.group(1)}</code>')
    text = re.sub(r'`([^`]+)`', repl_code, text)

    # 2. Images: ![alt](url)
    def repl_img(m):
        return protect(f'<img src="{m.group(2)}" alt="{m.group(1)}">')
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', repl_img, text)

    # 3. Links: [text](url)
    def repl_link(m):
        return protect(f'<a href="{m.group(2)}">{m.group(1)}</a>')
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', repl_link, text)

    # 4. Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)

    # 5. Italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'<em>\1</em>', text)

    # 6. Strikethrough
    text = re.sub(r'~~(.+?)~~', r'<del>\1</del>', text)

    for key, value in protected.items():
        text = text.replace(key, value)

    return text

def normalize_source(md_text):
    """Strips BOM, normalizes line endings and removes an outer ```markdown wrapper."""
    md_text = md_text.lstrip('\ufeff')
    md_text = md_text.replace('\r\n', '\n').replace('\r', '\n')

    # If the whole document was accidentally wrapped in an outer code block, unwrap it
    probe = md_text.strip().split('\n')
    if probe and probe[0].strip().lower() in ('```markdown', '```md'):
        if len(probe) > 1 and probe[-1].strip() == '```':
            md_text = '\n'.join(probe[1:-1])
    return md_text

def convert_md_to_html(md_text):
    """Converts Markdown to HTML, handling both block and inline elements."""
    md_text = normalize_source(md_text)
    lines = md_text.split('\n')
    html = []

    # === First pass: collect headings for anchors and the table of contents ===
    heading_ids = []      # heading ids in order of appearance
    headings_info = []    # (level, text, id)
    text_to_id = {}       # normalized text -> id
    used_ids = {}
    scan_in_code = False
    for raw in lines:
        s = raw.strip()
        if s.startswith('```'):
            scan_in_code = not scan_in_code
            continue
        if scan_in_code:
            continue
        hm = re.match(r'^(#{1,6})\s+(.*)', s)
        if hm:
            base = make_slug(hm.group(2))
            slug = base
            if slug in used_ids:
                used_ids[slug] += 1
                slug = f"{slug}-{used_ids[slug]}"
            else:
                used_ids[slug] = 1
            heading_ids.append(slug)
            headings_info.append((len(hm.group(1)), hm.group(2), slug))
            text_to_id.setdefault(base, slug)

    heading_index = 0
    toc_mode = False   # skip the original contents block (we replace it with our own)

    def render_li(text):
        """List item: if the text matches a heading, turn it into an anchor link."""
        key = make_slug(text)
        if key in text_to_id:
            return f'<li><a href="#{text_to_id[key]}">{process_inline(text)}</a></li>'
        return f'<li>{process_inline(text)}</li>'

    # Open block states
    in_code_block = False
    code_buffer = []

    in_ul = False
    in_ol = False
    in_blockquote = False
    in_table = False

    def close_list():
        nonlocal in_ul, in_ol
        if in_ul:
            html.append('</ul>')
            in_ul = False
        if in_ol:
            html.append('</ol>')
            in_ol = False

    def close_blockquote():
        nonlocal in_blockquote
        if in_blockquote:
            html.append('</blockquote>')
            in_blockquote = False

    def close_table():
        nonlocal in_table
        if in_table:
            html.append('</tbody></table>')
            in_table = False

    def close_all():
        close_list()
        close_blockquote()
        close_table()

    for line in lines:
        # === Code block (``` ... ```) ===
        if line.strip().startswith('```'):
            if in_code_block:
                code_content = escape_html('\n'.join(code_buffer))
                html.append(f'<pre><code>{code_content}</code></pre>')
                code_buffer = []
                in_code_block = False
            else:
                close_all()
                in_code_block = True
            continue

        if in_code_block:
            code_buffer.append(line)
            continue

        stripped = line.strip()

        # === Skip the original contents: it was replaced by the auto-generated list ===
        if toc_mode:
            if re.match(r'^#{1,6}\s+', stripped) or re.match(r'^[-*_]{3,}$', stripped):
                toc_mode = False
            else:
                continue

        # === Empty line ===
        if not stripped:
            close_all()
            continue

        # === Horizontal rule ===
        if re.match(r'^[-*_]{3,}$', stripped):
            close_all()
            html.append('<hr>')
            continue

        # === Headings ===
        m = re.match(r'^(#{1,6})\s+(.*)', stripped)
        if m:
            close_all()
            level = len(m.group(1))
            content = process_inline(m.group(2))
            hid = heading_ids[heading_index]
            heading_index += 1
            html.append(f'<h{level} id="{hid}">{content}</h{level}>')

            # If this is the "Contents" section, build the clickable list ourselves
            base_slug = make_slug(m.group(2))
            if any(w in base_slug for w in ('содержание', 'оглавление', 'contents')):
                html.append('<ul class="toc">')
                for lvl, txt, tid in headings_info:
                    if lvl == 2 and tid != hid:
                        html.append(f'<li><a href="#{tid}">{process_inline(txt)}</a></li>')
                html.append('</ul>')
                toc_mode = True
            continue

        # === Blockquote ===
        if stripped.startswith('>'):
            close_list()
            close_table()
            content = stripped[1:].strip()
            if not in_blockquote:
                html.append('<blockquote>')
                in_blockquote = True
            html.append(f'<p>{process_inline(content)}</p>')
            continue
        else:
            close_blockquote()

        # === Table ===
        is_table_row = '|' in stripped
        is_table_separator = bool(re.match(r'^[\s|:\-]+$', stripped))

        if is_table_row and not is_table_separator:
            cells = [c.strip() for c in stripped.split('|')]
            if cells and cells[0] == '':
                cells = cells[1:]
            if cells and cells[-1] == '':
                cells = cells[:-1]

            if not in_table:
                html.append('<table><thead><tr>')
                for cell in cells:
                    html.append(f'<th>{process_inline(cell)}</th>')
                html.append('</tr></thead><tbody>')
                in_table = True
            else:
                html.append('<tr>')
                for cell in cells:
                    html.append(f'<td>{process_inline(cell)}</td>')
                html.append('</tr>')
            continue
        elif is_table_separator and in_table:
            continue
        else:
            close_table()

        # === Ordered list ===
        m = re.match(r'^\d+\.\s+(.*)', stripped)
        if m:
            close_blockquote()
            close_table()
            if in_ul:
                html.append('</ul>')
                in_ul = False
            if not in_ol:
                html.append('<ol>')
                in_ol = True
            html.append(render_li(m.group(1)))
            continue

        # === Unordered list ===
        m = re.match(r'^[-*]\s+(.*)', stripped)
        if m:
            close_blockquote()
            close_table()
            if in_ol:
                html.append('</ol>')
                in_ol = False
            if not in_ul:
                html.append('<ul>')
                in_ul = True
            html.append(render_li(m.group(1)))
            continue

        # === Regular paragraph ===
        close_list()
        close_blockquote()
        close_table()
        html.append(f'<p>{process_inline(stripped)}</p>')

    if in_code_block:
        code_content = escape_html('\n'.join(code_buffer))
        html.append(f'<pre><code>{code_content}</code></pre>')
    close_all()

    return '\n'.join(html)

def generate_html(body_content):
    """Generates the final HTML document with embedded CSS styles."""
    css = """
        body {
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.7;
            color: #2c3e50;
            background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
            margin: 0;
            padding: 40px 20px;
        }
        .container {
            max-width: 860px;
            margin: 0 auto;
            background: #ffffff;
            padding: 50px 60px;
            border-radius: 14px;
            box-shadow: 0 15px 40px rgba(0,0,0,0.08);
        }
        h1, h2, h3 {
            color: #1a202c;
            margin-top: 1.6em;
            margin-bottom: 0.6em;
            font-weight: 700;
            line-height: 1.3;
        }
        h1 {
            font-size: 2.3em;
            border-bottom: 3px solid #3498db;
            padding-bottom: 0.4em;
        }
        h2 {
            font-size: 1.7em;
            border-bottom: 1px solid #ecf0f1;
            padding-bottom: 0.3em;
        }
        h3 { font-size: 1.3em; color: #34495e; }
        p {
            margin-bottom: 1.1em;
            font-size: 1.05em;
        }
        a {
            color: #3498db;
            text-decoration: none;
            border-bottom: 1px dotted #3498db;
            transition: all 0.2s;
        }
        a:hover {
            color: #2980b9;
            border-bottom-style: solid;
        }
        strong { color: #1a202c; font-weight: 700; }
        em { color: #555; font-style: italic; }
        del { color: #95a5a6; }
        ul, ol {
            margin-bottom: 1.3em;
            padding-left: 26px;
        }
        li {
            margin-bottom: 0.5em;
            padding-left: 4px;
        }
        code {
            background-color: #f1f3f5;
            padding: 2px 7px;
            border-radius: 4px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.9em;
            color: #e74c3c;
        }
        pre {
            background-color: #282c34;
            color: #abb2bf;
            padding: 18px 22px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 1.5em 0;
            box-shadow: inset 0 0 0 1px rgba(255,255,255,0.05);
        }
        pre code {
            background: none;
            color: inherit;
            padding: 0;
            font-size: 0.92em;
            line-height: 1.5;
        }
        blockquote {
            border-left: 4px solid #3498db;
            margin: 1.5em 0;
            padding: 0.6em 1.2em;
            background-color: #f8f9fa;
            color: #555;
            font-style: italic;
            border-radius: 0 6px 6px 0;
        }
        blockquote p { margin: 0; }
        hr {
            border: none;
            border-top: 1px solid #ecf0f1;
            margin: 2.2em 0;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 1.5em 0;
            font-size: 0.98em;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            border-radius: 6px;
            overflow: hidden;
        }
        th, td {
            border: 1px solid #e1e4e8;
            padding: 11px 14px;
            text-align: left;
        }
        th {
            background-color: #f6f8fa;
            font-weight: 600;
            color: #24292e;
        }
        tr:nth-child(even) td {
            background-color: #fafbfc;
        }
        img {
            max-width: 100%;
            height: auto;
            border-radius: 6px;
            margin: 1em 0;
            display: block;
        }
    """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document</title>
    <style>{css}</style>
</head>
<body>
    <div class="container">
        {body_content}
    </div>
</body>
</html>"""

def main():
    print("=== Simple MD to HTML Converter ===")

    script_dir = get_script_dir()
    md_files = find_md_files(script_dir)

    if not md_files:
        print("No .md files found in this folder")
        input("Press Enter to exit...")
        sys.exit(0)

    print("\nAvailable files:")
    for i, filename in enumerate(md_files, 1):
        print(f"  {i}. {filename}")

    selected_file = None
    while True:
        try:
            choice = input("\nEnter the number of the file to convert: ")
            index = int(choice) - 1
            if 0 <= index < len(md_files):
                selected_file = md_files[index]
                break
            else:
                print("Error: number out of range. Please try again.")
        except ValueError:
            print("Error: please enter a valid number.")
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            sys.exit(0)

    file_path = os.path.join(script_dir, selected_file)
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            md_content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

    print("Converting...")

    html_body = convert_md_to_html(md_content)
    full_html = generate_html(html_body)

    output_filename = os.path.splitext(selected_file)[0] + '.html'
    output_path = os.path.join(script_dir, output_filename)

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_html)
        print(f"\nDone! File saved as: {output_filename}")
    except Exception as e:
        print(f"Error saving file: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

    # === DIAGNOSTICS: shows immediately whether navigation works ===
    anchors = len(re.findall(r'<h[1-6] id="', html_body))
    links = html_body.count('href="#')
    print("\n--- DIAGNOSTICS ---")
    print(f"Reading file:           {file_path}")
    print(f"Headings with anchors:  {anchors}")
    print(f"Navigation links:       {links}")
    if anchors == 0:
        print("PROBLEM: the .md file has no headings like '# Text' or '## Text'.")
    elif links == 0:
        print("PROBLEM: anchors exist, but no 'Contents' section was found.")
    else:
        print("Navigation generated correctly.")
    print(f"Open this file:         {output_path}")
    print("-------------------")

    input("\nPress Enter to exit...")

if __name__ == '__main__':
    main()
