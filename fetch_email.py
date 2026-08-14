import os
import sys
import imaplib
import email
from email.header import decode_header
from datetime import datetime, date
import re

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

# Configuration from Environment Variables (GitHub Secrets)
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")
SENDER_FILTER = os.getenv("SENDER_FILTER", "") # e.g. "digant73@gmail.com" or empty
SUBJECT_FILTER = os.getenv("SUBJECT_FILTER", "") # e.g. "Daily Stock Report" or empty

def clean_header_str(header_value):
    if not header_value:
        return ""
    decoded_list = decode_header(header_value)
    result = ""
    for decoded_string, charset in decoded_list:
        if isinstance(decoded_string, bytes):
            charset = charset or "utf-8"
            try:
                result += decoded_string.decode(charset, errors="ignore")
            except Exception:
                result += decoded_string.decode("latin-1", errors="ignore")
        else:
            result += str(decoded_string)
    return result.strip()

def format_text_to_rich_html(raw_text):
    """
    Transforms plain text / markdown email content into modern HTML component cards.
    Handles Markdown tables, section headers, breakout alerts, and URLs.
    """
    lines = raw_text.split('\n')
    formatted_html = []
    in_table = False
    table_rows = []

    def flush_table(rows):
        if not rows:
            return ""
        html = '<div class="table-container"><table class="data-table"><thead>'
        # Header row
        headers = [c.strip() for c in rows[0].split('|')[1:-1]]
        html += '<tr>' + ''.join([f'<th>{h}</th>' for h in headers]) + '</tr></thead><tbody>'
        
        # Data rows (skip index 1 if separator line like | :--- |)
        start_idx = 2 if len(rows) > 1 and ':---' in rows[1] else 1
        for row in rows[start_idx:]:
            cols = [c.strip() for c in row.split('|')[1:-1]]
            if not cols or all(c == '' for c in cols):
                continue
            html += '<tr>'
            for idx, cell in enumerate(cols):
                # Colorize positive/negative changes
                if '+' in cell and '%' in cell:
                    cell_html = f'<span class="badge-change pos">{cell}</span>'
                elif '-' in cell and '%' in cell:
                    cell_html = f'<span class="badge-change neg">{cell}</span>'
                elif 'Surge' in headers[idx] if idx < len(headers) else False:
                    cell_html = f'<span class="surge-tag">{cell}</span>'
                else:
                    cell_html = cell
                html += f'<td>{cell_html}</td>'
            html += '</tr>'
        html += '</tbody></table></div>'
        return html

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Handle Markdown Table lines
        if line.startswith('|') and line.endswith('|'):
            table_rows.append(line)
            in_table = True
            i += 1
            continue
        elif in_table:
            formatted_html.append(flush_table(table_rows))
            table_rows = []
            in_table = False

        if not line:
            i += 1
            continue

        # Handle Section Headers (e.g. 1. Major Indian Market Summary:)
        header_match = re.match(r'^(\d+\.\s*)(.*)', line)
        if header_match:
            title_text = header_match.group(2)
            icon = "📌"
            badge_class = "blue"
            if "Breakout" in title_text or "Breach Alert" in title_text:
                icon = "🚨"
                badge_class = "amber"
            elif "Market Summary" in title_text:
                icon = "📊"
                badge_class = "blue"
            elif "Circuit Check" in title_text:
                icon = "⚡"
                badge_class = "purple"
            elif "Volume Surge" in title_text:
                icon = "🔥"
                badge_class = "emerald"
            elif "Corporate Events" in title_text or "Calendar" in title_text:
                icon = "📅"
                badge_class = "indigo"

            formatted_html.append(f'<div class="section-header-card"><span class="section-icon">{icon}</span><h3>{title_text}</h3></div>')
            i += 1
            continue

        # Handle Breakout Alert Callout Banner
        if "BREAKOUT ALERT" in line or "crossed above your set Up Level" in line:
            formatted_html.append(f'<div class="breakout-alert-box"><div class="alert-icon">⚡</div><div><strong>BREAKOUT ALERT</strong><br/>{line}</div></div>')
            i += 1
            continue

        # Handle Spreadsheet Links & General URLs
        if "Spreadsheet Tracker Link:" in line or "http" in line:
            line_with_links = re.sub(
                r'\[([^\]]+)\]\((https?://[^\s\)]+)\)',
                r'<a href="\2" target="_blank" rel="noopener" class="link-btn">🔗 \1</a>',
                line
            )
            line_with_links = re.sub(
                r'(?<!href=")(https?://[^\s<]+)',
                r'<a href="\1" target="_blank" rel="noopener" class="link-url">\1</a>',
                line_with_links
            )
            formatted_html.append(f'<div class="link-card">{line_with_links}</div>')
            i += 1
            continue

        # Handle Bullet points
        if line.startswith('- ') or line.startswith('* '):
            bullet_content = line[2:]
            # Bold stock symbols or key phrases
            bullet_content = re.sub(r'\b([A-Z0-9]{3,})\b', r'<strong>\1</strong>', bullet_content)
            formatted_html.append(f'<div class="bullet-item"><span class="bullet-dot">•</span><div>{bullet_content}</div></div>')
            i += 1
            continue

        # Default paragraph
        formatted_html.append(f'<p class="text-paragraph">{line}</p>')
        i += 1

    if in_table:
        formatted_html.append(flush_table(table_rows))

    return '\n'.join(formatted_html)

def fetch_latest_daily_email():
    if not EMAIL_USER or not EMAIL_PASS:
        print("EMAIL_USER/EMAIL_PASS not set. Checking for mock email payload...")
        return None

    print(f"Connecting to IMAP server {IMAP_SERVER}:{IMAP_PORT}...")
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("INBOX")

    today_str = date.today().strftime("%d-%b-%Y")
    search_query = f'(SINCE "{today_str}")'
    if SENDER_FILTER:
        search_query += f' (FROM "{SENDER_FILTER}")'
    if SUBJECT_FILTER:
        search_query += f' (SUBJECT "{SUBJECT_FILTER}")'

    print(f"Searching IMAP with query: {search_query}")
    status, messages = mail.search(None, search_query)
    mail_ids = messages[0].split()

    if not mail_ids or mail_ids == [b'']:
        print("No email today. Searching recent messages...")
        fallback_query = "ALL"
        if SUBJECT_FILTER:
            fallback_query = f'(SUBJECT "{SUBJECT_FILTER}")'
        status, messages = mail.search(None, fallback_query)
        mail_ids = messages[0].split()

    if not mail_ids or mail_ids == [b'']:
        print("No matching email found.")
        mail.logout()
        return None

    latest_id = mail_ids[-1]
    status, msg_data = mail.fetch(latest_id, "(RFC822)")

    for response_part in msg_data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])
            subject = clean_header_str(msg["Subject"])
            from_addr = clean_header_str(msg["From"])
            date_sent = clean_header_str(msg["Date"])

            html_content = ""
            text_content = ""

            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    if "attachment" not in content_disposition:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or "utf-8"
                            decoded_str = payload.decode(charset, errors="ignore")
                            if content_type == "text/html":
                                html_content += decoded_str
                            elif content_type == "text/plain":
                                text_content += decoded_str
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or "utf-8"
                    decoded_str = payload.decode(charset, errors="ignore")
                    if msg.get_content_type() == "text/html":
                        html_content = decoded_str
                    else:
                        text_content = decoded_str

            mail.logout()

            if html_content and "<table" in html_content:
                body_formatted = html_content
            else:
                raw_text = text_content if text_content else html_content
                body_formatted = format_text_to_rich_html(raw_text)

            return {
                "subject": subject or "Daily Briefing",
                "from": from_addr or EMAIL_USER,
                "date": date_sent or datetime.now().strftime("%a, %d %b %Y %H:%M:%S"),
                "body": body_formatted,
                "fetched_at": datetime.now().strftime("%B %d, %Y - %I:%M %p IST")
            }

    mail.logout()
    return None

def generate_html_page(email_data):
    if not email_data:
        print("No email data provided.")
        return

    subject = email_data["subject"]
    from_addr = email_data["from"]
    date_sent = email_data["date"]
    body = email_data["body"]
    fetched_at = email_data["fetched_at"]

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject} - Executive Daily Report</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-page: #f8fafc;
      --bg-card: #ffffff;
      --border-color: #e2e8f0;
      --text-main: #0f172a;
      --text-muted: #64748b;
      --accent-blue: #0284c7;
      --accent-light: #e0f2fe;
      --accent-emerald: #059669;
      --accent-emerald-bg: #dcfce7;
      --accent-amber: #d97706;
      --accent-amber-bg: #fef3c7;
      --accent-red: #dc2626;
      --accent-red-bg: #fee2e2;
      --shadow-card: 0 4px 20px -2px rgba(15, 23, 42, 0.06);
    }}

    [data-theme="dark"] {{
      --bg-page: #0b1120;
      --bg-card: #1e293b;
      --border-color: #334155;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --accent-blue: #38bdf8;
      --accent-light: #0369a1;
      --accent-emerald: #34d399;
      --accent-emerald-bg: #064e3b;
      --accent-amber: #fbbf24;
      --accent-amber-bg: #78350f;
      --accent-red: #f87171;
      --accent-red-bg: #7f1d1d;
      --shadow-card: 0 4px 20px -2px rgba(0, 0, 0, 0.3);
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: var(--bg-page);
      color: var(--text-main);
      line-height: 1.6;
      padding-bottom: 60px;
      transition: background-color 0.3s ease, color 0.3s ease;
    }}

    header {{
      background-color: var(--bg-card);
      border-bottom: 1px solid var(--border-color);
      padding: 16px 28px;
      position: sticky;
      top: 0;
      z-index: 100;
      box-shadow: 0 2px 10px rgba(0,0,0,0.03);
    }}

    .header-container {{
      max-width: 1050px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}

    .logo-area {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .logo-icon {{
      width: 42px;
      height: 42px;
      background: linear-gradient(135deg, #0284c7, #0369a1);
      color: #fff;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-family: 'Outfit', sans-serif;
      font-size: 20px;
      box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3);
    }}

    .site-title {{
      font-family: 'Outfit', sans-serif;
      font-size: 20px;
      font-weight: 700;
      color: var(--text-main);
    }}

    .btn-toggle {{
      background: var(--bg-page);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 8px 16px;
      border-radius: 8px;
      cursor: pointer;
      font-size: 14px;
      font-weight: 500;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.2s;
    }}

    .btn-toggle:hover {{
      border-color: var(--accent-blue);
    }}

    main {{
      max-width: 1050px;
      margin: 32px auto;
      padding: 0 20px;
    }}

    .brief-meta-card {{
      background-color: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 18px;
      padding: 28px;
      margin-bottom: 24px;
      box-shadow: var(--shadow-card);
    }}

    .brief-tag {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background-color: var(--accent-light);
      color: var(--accent-blue);
      padding: 5px 14px;
      border-radius: 20px;
      font-size: 13px;
      font-weight: 700;
      margin-bottom: 14px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}

    .brief-subject {{
      font-family: 'Outfit', sans-serif;
      font-size: 26px;
      font-weight: 800;
      line-height: 1.3;
      margin-bottom: 16px;
      color: var(--text-main);
    }}

    .meta-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
      border-top: 1px solid var(--border-color);
      padding-top: 16px;
      font-size: 14px;
      color: var(--text-muted);
    }}

    .meta-item strong {{
      color: var(--text-main);
    }}

    .email-content-container {{
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}

    .section-header-card {{
      display: flex;
      align-items: center;
      gap: 12px;
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 14px 20px;
      margin-top: 8px;
      box-shadow: var(--shadow-card);
    }}

    .section-icon {{
      font-size: 22px;
    }}

    .section-header-card h3 {{
      font-family: 'Outfit', sans-serif;
      font-size: 18px;
      font-weight: 700;
      color: var(--text-main);
    }}

    .breakout-alert-box {{
      background: var(--accent-amber-bg);
      border: 1px solid var(--accent-amber);
      border-radius: 14px;
      padding: 18px 22px;
      display: flex;
      align-items: flex-start;
      gap: 14px;
      color: var(--text-main);
      box-shadow: 0 4px 14px rgba(217, 119, 6, 0.15);
    }}

    .alert-icon {{
      font-size: 24px;
    }}

    .bullet-item {{
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 14px 20px;
      display: flex;
      align-items: flex-start;
      gap: 12px;
      box-shadow: var(--shadow-card);
      font-size: 15px;
    }}

    .bullet-dot {{
      color: var(--accent-blue);
      font-size: 20px;
      line-height: 1;
    }}

    .text-paragraph {{
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 14px 20px;
      font-size: 15px;
      box-shadow: var(--shadow-card);
    }}

    .table-container {{
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 16px;
      padding: 16px;
      overflow-x: auto;
      box-shadow: var(--shadow-card);
    }}

    .data-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
      text-align: left;
    }}

    .data-table th {{
      background: var(--bg-page);
      color: var(--text-muted);
      font-weight: 700;
      padding: 12px 16px;
      border-bottom: 2px solid var(--border-color);
      text-transform: uppercase;
      font-size: 12px;
      letter-spacing: 0.5px;
    }}

    .data-table td {{
      padding: 14px 16px;
      border-bottom: 1px solid var(--border-color);
      color: var(--text-main);
    }}

    .data-table tr:last-child td {{
      border-bottom: none;
    }}

    .badge-change {{
      font-weight: 700;
      padding: 4px 10px;
      border-radius: 20px;
      font-size: 13px;
      display: inline-block;
    }}

    .badge-change.pos {{
      background: var(--accent-emerald-bg);
      color: var(--accent-emerald);
    }}

    .badge-change.neg {{
      background: var(--accent-red-bg);
      color: var(--accent-red);
    }}

    .surge-tag {{
      background: var(--accent-light);
      color: var(--accent-blue);
      font-weight: 700;
      padding: 4px 10px;
      border-radius: 8px;
    }}

    .link-card {{
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 16px 20px;
      box-shadow: var(--shadow-card);
    }}

    .link-btn {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: var(--accent-blue);
      color: #fff !important;
      padding: 10px 20px;
      border-radius: 10px;
      text-decoration: none;
      font-weight: 600;
      box-shadow: 0 4px 12px rgba(2, 132, 199, 0.25);
      transition: opacity 0.2s;
    }}

    .link-btn:hover {{
      opacity: 0.9;
    }}

    footer {{
      text-align: center;
      margin-top: 40px;
      color: var(--text-muted);
      font-size: 13px;
    }}
  </style>
</head>
<body>

  <header>
    <div class="header-container">
      <div class="logo-area">
        <div class="logo-icon">DB</div>
        <div class="site-title">Daily Stock Briefing</div>
      </div>
      <button class="btn-toggle" onclick="toggleTheme()">
        <span id="theme-icon">🌙</span> <span id="theme-text">Dark Mode</span>
      </button>
    </div>
  </header>

  <main>
    <div class="brief-meta-card">
      <div class="brief-tag">⚡ Automated 7:00 AM Email Report</div>
      <h1 class="brief-subject">{subject}</h1>
      <div class="meta-grid">
        <div class="meta-item"><strong>From:</strong> {from_addr}</div>
        <div class="meta-item"><strong>Received:</strong> {date_sent}</div>
        <div class="meta-item"><strong>Page Updated:</strong> {fetched_at}</div>
      </div>
    </div>

    <div class="email-content-container">
      {body}
    </div>

    <footer>
      Auto-generated from Daily 7 AM Email • Powered by GitHub Actions & Pages
    </footer>
  </main>

  <script>
    function toggleTheme() {{
      const current = document.documentElement.getAttribute('data-theme');
      const target = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', target);
      document.getElementById('theme-icon').innerText = target === 'dark' ? '☀️' : '🌙';
      document.getElementById('theme-text').innerText = target === 'dark' ? 'Light Mode' : 'Dark Mode';
      localStorage.setItem('theme', target);
    }}

    const savedTheme = localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    if (savedTheme === 'dark') {{
      document.documentElement.setAttribute('data-theme', 'dark');
      document.getElementById('theme-icon').innerText = '☀️';
      document.getElementById('theme-text').innerText = 'Light Mode';
    }}
  </script>
</body>
</html>
"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)
    print("Successfully generated index.html!")

if __name__ == "__main__":
    email_data = fetch_latest_daily_email()
    if email_data:
        generate_html_page(email_data)
    else:
        print("No email fetched from IMAP. Checking for local sample generation...")
