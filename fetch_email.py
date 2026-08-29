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
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com").strip() or "imap.gmail.com"
raw_port = os.getenv("IMAP_PORT", "993").strip()
IMAP_PORT = int(raw_port) if raw_port.isdigit() else 993
EMAIL_USER = os.getenv("EMAIL_USER", "").strip()
EMAIL_PASS = os.getenv("EMAIL_PASS", "").strip()
SENDER_FILTER = os.getenv("SENDER_FILTER", "").strip()
SUBJECT_FILTER = os.getenv("SUBJECT_FILTER", "Daily Stock Report").strip() or "Daily Stock Report"

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

def is_target_daily_stock_email(subject_str, from_str=""):
    """
    Strict validation to ensure ONLY 'Daily Stock Report' emails are processed.
    Rejects any email that does not contain 'daily stock report' in its subject.
    """
    if not subject_str:
        return False
    
    subject_clean = " ".join(subject_str.lower().split())
    target_clean = " ".join((SUBJECT_FILTER or "daily stock report").lower().split())
    
    # Must contain "daily stock report" (or configured target filter)
    if target_clean not in subject_clean and "daily stock report" not in subject_clean:
        return False
        
    if SENDER_FILTER and SENDER_FILTER.lower() not in from_str.lower():
        return False
        
    return True

def format_text_to_rich_html(raw_text):
    """
    Transforms plain text / markdown email content into modern mobile-friendly HTML cards.
    Handles Markdown tables, section headers, breakout alerts, bullet points, and spreadsheet URLs.
    """
    lines = raw_text.split('\n')
    formatted_html = []
    nav_sections = []
    in_table = False
    table_rows = []

    def flush_table(rows):
        if not rows:
            return ""
        html = '<div class="table-container"><table class="data-table"><thead>'
        # Header row
        headers = [c.strip() for c in rows[0].split('|')[1:-1]]
        html += '<tr>' + ''.join([f'<th>{h}</th>' for h in headers]) + '</tr></thead><tbody>'
        
        # Data rows (skip separator lines like | :--- |)
        start_idx = 2 if len(rows) > 1 and ':---' in rows[1] else 1
        for row in rows[start_idx:]:
            cols = [c.strip() for c in row.split('|')[1:-1]]
            if not cols or all(c == '' for c in cols):
                continue
            html += '<tr>'
            for idx, cell in enumerate(cols):
                header_name = headers[idx] if idx < len(headers) else ""
                # Colorize positive/negative changes
                if '+' in cell and ('%' in cell or '₹' in cell or '.' in cell):
                    cell_html = f'<span class="badge-change pos">{cell}</span>'
                elif '-' in cell and ('%' in cell or '₹' in cell or '.' in cell):
                    cell_html = f'<span class="badge-change neg">{cell}</span>'
                elif 'Surge' in header_name or 'x' in cell.lower():
                    cell_html = f'<span class="surge-tag">{cell}</span>'
                elif idx == 0:
                    # Stock name in bold
                    cell_html = f'<strong>{cell}</strong>'
                else:
                    cell_html = cell
                html += f'<td data-label="{header_name}">{cell_html}</td>'
            html += '</tr>'
        html += '</tbody></table></div>'
        return html

    i = 0
    section_counter = 0
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

        # Handle Section Headers (e.g. 1. Major Indian Market Summary: or ## Section)
        header_match = re.match(r'^(?:##\s*|\d+\.\s*)(.*)', line)
        if header_match and (line.endswith(':') or line.endswith('?') or len(line) < 80):
            section_counter += 1
            title_text = header_match.group(1).rstrip(':')
            icon = "📌"
            badge_class = "blue"
            section_id = f"sec-{section_counter}"

            if "breakout" in title_text.lower() or "breach" in title_text.lower():
                icon = "🚨"
                badge_class = "amber"
                section_id = "sec-breakout"
                nav_sections.append({"id": section_id, "icon": icon, "title": "Breakouts"})
            elif "market summary" in title_text.lower() or "opening" in title_text.lower():
                icon = "📊"
                badge_class = "blue"
                section_id = "sec-market"
                nav_sections.append({"id": section_id, "icon": icon, "title": "Market Setup"})
            elif "52-week" in title_text.lower() or "high & low" in title_text.lower():
                icon = "🎯"
                badge_class = "indigo"
                section_id = "sec-52w"
                nav_sections.append({"id": section_id, "icon": icon, "title": "52W High/Low"})
            elif "circuit" in title_text.lower():
                icon = "⚡"
                badge_class = "purple"
                section_id = "sec-circuit"
                nav_sections.append({"id": section_id, "icon": icon, "title": "Circuits"})
            elif "volume surge" in title_text.lower():
                icon = "🔥"
                badge_class = "emerald"
                section_id = "sec-volume"
                nav_sections.append({"id": section_id, "icon": icon, "title": "Volume Surges"})
            elif "crossover" in title_text.lower():
                icon = "📈"
                badge_class = "blue"
                section_id = "sec-crossover"
                nav_sections.append({"id": section_id, "icon": icon, "title": "MA Crossover"})
            elif "corporate" in title_text.lower() or "announcements" in title_text.lower() or "news" in title_text.lower():
                icon = "📢"
                badge_class = "indigo"
                section_id = "sec-corporate"
                nav_sections.append({"id": section_id, "icon": icon, "title": "Corporate News"})
            elif "calendar" in title_text.lower() or "events" in title_text.lower() or "agm" in title_text.lower():
                icon = "📅"
                badge_class = "rose"
                section_id = "sec-calendar"
                nav_sections.append({"id": section_id, "icon": icon, "title": "Calendar"})
            else:
                nav_sections.append({"id": section_id, "icon": icon, "title": title_text[:14]})

            formatted_html.append(f'<div id="{section_id}" class="section-header-card {badge_class}"><span class="section-icon">{icon}</span><h3>{title_text}</h3></div>')
            i += 1
            continue

        # Handle Breakout Alert Callout Banner
        if "BREAKOUT ALERT" in line or "crossed above your set Up Level" in line:
            # Format ticker and prices
            alert_formatted = re.sub(r'(\b[A-Z0-9_]{3,}\b)', r'<strong>\1</strong>', line)
            formatted_html.append(f'<div class="breakout-alert-box"><div class="alert-icon">🚨</div><div class="alert-content"><div class="alert-tag">LEVEL BREACH / BREAKOUT</div><p>{alert_formatted}</p></div></div>')
            i += 1
            continue

        # Handle Spreadsheet Links & General URLs
        if "Spreadsheet Tracker Link:" in line or "http" in line:
            # Markdown link [Text](URL)
            line_with_links = re.sub(
                r'\[([^\]]+)\]\((https?://[^\s\)]+)\)',
                r'<a href="\2" target="_blank" rel="noopener" class="link-btn">📊 \1</a>',
                line
            )
            # Raw URLs
            line_with_links = re.sub(
                r'(?<!href=")(https?://[^\s<]+)',
                r'<a href="\1" target="_blank" rel="noopener" class="link-url">\1</a>',
                line_with_links
            )
            formatted_html.append(f'<div class="link-card">{line_with_links}</div>')
            i += 1
            continue

        # Handle Bullet points (- or *)
        if line.startswith('- ') or line.startswith('* '):
            bullet_content = line[2:].strip()
            # Convert markdown bold **word** to <strong>word</strong>
            bullet_content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', bullet_content)
            
            # Highlight stock ticker in parentheses e.g. (BOROLTD), (HAL), (GPPL)
            bullet_content = re.sub(r'\(([A-Z0-9_\.]{2,12})\)', r'(<strong class="ticker-badge">\1</strong>)', bullet_content)
            
            # Format positive / negative change chips inside bullets if present
            bullet_content = re.sub(r'(\+\d+(?:\.\d+)?%)', r'<span class="badge-change pos">\1</span>', bullet_content)
            bullet_content = re.sub(r'(-\d+(?:\.\d+)?%)', r'<span class="badge-change neg">\1</span>', bullet_content)

            # Check if this bullet is a subheader like "Stocks At / Near 52-Week Highs:"
            if bullet_content.endswith(':') and len(bullet_content) < 45:
                formatted_html.append(f'<div class="sub-section-title">✨ {bullet_content}</div>')
            else:
                formatted_html.append(f'<div class="bullet-item"><span class="bullet-dot">•</span><div class="bullet-text">{bullet_content}</div></div>')
            i += 1
            continue

        # Convert markdown bold in normal paragraphs
        p_content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
        formatted_html.append(f'<p class="text-paragraph">{p_content}</p>')
        i += 1

    if in_table:
        formatted_html.append(flush_table(table_rows))

    # Generate quick navigation pills HTML
    nav_html = ""
    if nav_sections:
        pills = []
        for nav in nav_sections:
            pills.append(f'<a href="#{nav["id"]}" class="nav-pill">{nav["icon"]} {nav["title"]}</a>')
        nav_html = f'<div class="quick-nav-bar"><div class="quick-nav-label">Quick Jump:</div><div class="quick-nav-scroll">{"".join(pills)}</div></div>'

    return nav_html + "\n" + '\n'.join(formatted_html)

def fetch_latest_daily_email():
    """
    Connects to IMAP and retrieves strictly the latest 'Daily Stock Report' email.
    If no matching email is found, returns None without modifying existing content.
    """
    if not EMAIL_USER or not EMAIL_PASS:
        print("EMAIL_USER or EMAIL_PASS environment variables are not set.")
        return None

    server_to_use = IMAP_SERVER if IMAP_SERVER and "." in IMAP_SERVER else "imap.gmail.com"
    print(f"Connecting to IMAP server {server_to_use}:{IMAP_PORT}...")
    try:
        mail = imaplib.IMAP4_SSL(server_to_use, IMAP_PORT)
    except Exception as e:
        print(f"Connection to '{server_to_use}' failed ({e}). Falling back to 'imap.gmail.com'...")
        server_to_use = "imap.gmail.com"
        mail = imaplib.IMAP4_SSL(server_to_use, IMAP_PORT)
    
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("INBOX")
    
    target_keyword = SUBJECT_FILTER or "Daily Stock Report"
    print(f"Strict search target: subject must contain '{target_keyword}'")

    # Strategy 1: Search specifically for SUBJECT "Daily Stock Report"
    candidate_ids = []
    try:
        status, messages = mail.search(None, f'SUBJECT "{target_keyword}"')
        if status == "OK" and messages[0]:
            candidate_ids = messages[0].split()
    except Exception as err:
        print(f"Direct IMAP subject search error: {err}")

    # Strategy 2: If IMAP subject search returned empty, search recent messages to check headers
    if not candidate_ids or candidate_ids == [b'']:
        print("Searching recent inbox messages for header verification...")
        try:
            status, messages = mail.search(None, "ALL")
            if status == "OK" and messages[0]:
                all_ids = messages[0].split()
                # Check the most recent 100 emails
                candidate_ids = all_ids[-100:] if len(all_ids) > 100 else all_ids
        except Exception as err:
            print(f"Error fetching recent message IDs: {err}")
            candidate_ids = []

    if not candidate_ids or candidate_ids == [b'']:
        print("No messages available in INBOX.")
        mail.logout()
        return None

    print(f"Scanning {len(candidate_ids)} candidate message(s) from newest to oldest for strict subject match...")

    # Iterate candidate IDs in reverse order (newest first)
    for msg_id in reversed(candidate_ids):
        try:
            status, header_data = mail.fetch(msg_id, "(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE)])")
            if status != "OK" or not header_data:
                continue

            header_text = ""
            for part in header_data:
                if isinstance(part, tuple):
                    header_text = part[1].decode("utf-8", errors="ignore")
                    break

            msg_headers = email.message_from_string(header_text)
            subject = clean_header_str(msg_headers.get("Subject", ""))
            from_addr = clean_header_str(msg_headers.get("From", ""))
            date_sent = clean_header_str(msg_headers.get("Date", ""))

            # Strict verification
            if not is_target_daily_stock_email(subject, from_addr):
                continue

            print(f"Found matching target email: ID {msg_id.decode()} | Subject: '{subject}' | Date: {date_sent}")

            # Fetch full RFC822 message payload
            status, full_msg_data = mail.fetch(msg_id, "(RFC822)")
            if status != "OK" or not full_msg_data:
                continue

            for response_part in full_msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
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
                        "subject": subject,
                        "from": from_addr or EMAIL_USER,
                        "date": date_sent or datetime.now().strftime("%a, %d %b %Y %H:%M:%S"),
                        "body": body_formatted,
                        "fetched_at": datetime.now().strftime("%B %d, %Y - %I:%M %p IST")
                    }

        except Exception as e:
            print(f"Error processing message {msg_id}: {e}")
            continue

    mail.logout()
    print(f"No email matching subject '{target_keyword}' found in the inbox. No changes made.")
    return None

def generate_html_page(email_data):
    if not email_data:
        print("No email data provided to generate HTML.")
        return False

    subject = email_data["subject"]
    from_addr = email_data["from"]
    date_sent = email_data["date"]
    body = email_data["body"]
    fetched_at = email_data["fetched_at"]

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <title>{subject} - Daily Stock Briefing</title>
  
  <!-- iOS & Android Web App Meta Tags -->
  <link rel="apple-touch-icon" sizes="180x180" href="apple-touch-icon.png">
  <link rel="icon" type="image/png" href="favicon.png">
  <link rel="manifest" href="site.webmanifest">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="Daily Stocks">
  <meta name="theme-color" content="#0f172a">

  <!-- Modern Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Outfit:wght@600;700;800;900&display=swap" rel="stylesheet">
  
  <style>
    :root {{
      --bg-page: #f1f5f9;
      --bg-card: #ffffff;
      --bg-card-subtle: #f8fafc;
      --border-color: #e2e8f0;
      --text-main: #0f172a;
      --text-muted: #64748b;
      --accent-blue: #0284c7;
      --accent-blue-bg: #e0f2fe;
      --accent-emerald: #059669;
      --accent-emerald-bg: #dcfce7;
      --accent-amber: #d97706;
      --accent-amber-bg: #fef3c7;
      --accent-red: #dc2626;
      --accent-red-bg: #fee2e2;
      --accent-purple: #7c3aed;
      --accent-purple-bg: #f3e8ff;
      --accent-indigo: #4f46e5;
      --accent-indigo-bg: #e0e7ff;
      --shadow-sm: 0 1px 3px rgba(0,0,0,0.05);
      --shadow-md: 0 4px 16px -2px rgba(15, 23, 42, 0.08);
      --radius-card: 16px;
    }}

    [data-theme="dark"] {{
      --bg-page: #0b1120;
      --bg-card: #1e293b;
      --bg-card-subtle: #151e2e;
      --border-color: #334155;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --accent-blue: #38bdf8;
      --accent-blue-bg: #0c4a6e;
      --accent-emerald: #34d399;
      --accent-emerald-bg: #064e3b;
      --accent-amber: #fbbf24;
      --accent-amber-bg: #78350f;
      --accent-red: #f87171;
      --accent-red-bg: #7f1d1d;
      --accent-purple: #c084fc;
      --accent-purple-bg: #581c87;
      --accent-indigo: #818cf8;
      --accent-indigo-bg: #312e81;
      --shadow-sm: 0 1px 3px rgba(0,0,0,0.2);
      --shadow-md: 0 4px 20px -2px rgba(0, 0, 0, 0.4);
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-tap-highlight-color: transparent;
    }}

    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: var(--bg-page);
      color: var(--text-main);
      line-height: 1.6;
      padding-bottom: 80px;
      transition: background-color 0.25s ease, color 0.25s ease;
      -webkit-font-smoothing: antialiased;
    }}

    header {{
      background-color: var(--bg-card);
      border-bottom: 1px solid var(--border-color);
      padding: 14px 20px;
      position: sticky;
      top: 0;
      z-index: 200;
      box-shadow: 0 2px 10px rgba(0,0,0,0.04);
      backdrop-filter: blur(8px);
    }}

    .header-container {{
      max-width: 900px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}

    .logo-area {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .logo-icon {{
      width: 38px;
      height: 38px;
      background: linear-gradient(135deg, #0284c7, #2563eb);
      color: #fff;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 900;
      font-family: 'Outfit', sans-serif;
      font-size: 18px;
      box-shadow: 0 4px 10px rgba(2, 132, 199, 0.3);
    }}

    .site-title {{
      font-family: 'Outfit', sans-serif;
      font-size: 19px;
      font-weight: 800;
      color: var(--text-main);
      letter-spacing: -0.3px;
    }}

    .header-actions {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .btn-action {{
      background: var(--bg-card-subtle);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 7px 12px;
      border-radius: 8px;
      cursor: pointer;
      font-size: 13px;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s;
    }}

    .btn-action:hover {{
      border-color: var(--accent-blue);
    }}

    main {{
      max-width: 900px;
      margin: 20px auto 0 auto;
      padding: 0 16px;
    }}

    /* Quick Jump Navigation Bar */
    .quick-nav-bar {{
      margin-bottom: 20px;
      display: flex;
      align-items: center;
      gap: 10px;
      overflow-x: auto;
      padding-bottom: 6px;
      scrollbar-width: none;
    }}
    .quick-nav-bar::-webkit-scrollbar {{
      display: none;
    }}
    .quick-nav-label {{
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-muted);
      white-space: nowrap;
    }}
    .quick-nav-scroll {{
      display: flex;
      gap: 8px;
      overflow-x: auto;
      scrollbar-width: none;
    }}
    .quick-nav-scroll::-webkit-scrollbar {{
      display: none;
    }}
    .nav-pill {{
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 13px;
      font-weight: 600;
      text-decoration: none;
      white-space: nowrap;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      box-shadow: var(--shadow-sm);
      transition: all 0.2s;
    }}
    .nav-pill:hover, .nav-pill:active {{
      background: var(--accent-blue-bg);
      color: var(--accent-blue);
      border-color: var(--accent-blue);
    }}

    /* Main Meta Brief Card */
    .brief-meta-card {{
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-card);
      padding: 22px 20px;
      margin-bottom: 20px;
      box-shadow: var(--shadow-md);
      position: relative;
      overflow: hidden;
    }}

    .brief-meta-card::before {{
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 4px;
      background: linear-gradient(90deg, #0284c7, #3b82f6, #6366f1);
    }}

    .brief-tag-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 12px;
      flex-wrap: wrap;
    }}

    .brief-tag {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background-color: var(--accent-blue-bg);
      color: var(--accent-blue);
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}

    .live-badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      font-weight: 600;
      color: var(--accent-emerald);
      background: var(--accent-emerald-bg);
      padding: 4px 10px;
      border-radius: 20px;
    }}

    .live-dot {{
      width: 7px;
      height: 7px;
      background: var(--accent-emerald);
      border-radius: 50%;
      animation: pulse 1.8s infinite;
    }}

    @keyframes pulse {{
      0% {{ transform: scale(0.95); opacity: 0.8; }}
      50% {{ transform: scale(1.3); opacity: 1; }}
      100% {{ transform: scale(0.95); opacity: 0.8; }}
    }}

    .brief-subject {{
      font-family: 'Outfit', sans-serif;
      font-size: 22px;
      font-weight: 800;
      line-height: 1.35;
      margin-bottom: 14px;
      color: var(--text-main);
      letter-spacing: -0.3px;
    }}

    .meta-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 10px;
      border-top: 1px solid var(--border-color);
      padding-top: 14px;
      font-size: 13px;
      color: var(--text-muted);
    }}

    .meta-item strong {{
      color: var(--text-main);
    }}

    /* Email Content Styling */
    .email-content-container {{
      display: flex;
      flex-direction: column;
      gap: 14px;
    }}

    .section-header-card {{
      display: flex;
      align-items: center;
      gap: 12px;
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 12px 18px;
      margin-top: 12px;
      box-shadow: var(--shadow-sm);
      scroll-margin-top: 80px;
    }}

    .section-header-card.amber {{ border-left: 4px solid var(--accent-amber); }}
    .section-header-card.blue {{ border-left: 4px solid var(--accent-blue); }}
    .section-header-card.emerald {{ border-left: 4px solid var(--accent-emerald); }}
    .section-header-card.purple {{ border-left: 4px solid var(--accent-purple); }}
    .section-header-card.indigo {{ border-left: 4px solid var(--accent-indigo); }}
    .section-header-card.rose {{ border-left: 4px solid var(--accent-red); }}

    .section-icon {{
      font-size: 22px;
      line-height: 1;
    }}

    .section-header-card h3 {{
      font-family: 'Outfit', sans-serif;
      font-size: 17px;
      font-weight: 700;
      color: var(--text-main);
    }}

    .sub-section-title {{
      font-size: 14px;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin: 8px 4px 2px 4px;
    }}

    .breakout-alert-box {{
      background: var(--accent-amber-bg);
      border: 1.5px solid var(--accent-amber);
      border-radius: 14px;
      padding: 16px 18px;
      display: flex;
      align-items: flex-start;
      gap: 12px;
      color: var(--text-main);
      box-shadow: 0 4px 14px rgba(217, 119, 6, 0.15);
    }}

    .alert-icon {{
      font-size: 24px;
      line-height: 1;
    }}

    .alert-content {{
      flex: 1;
    }}

    .alert-tag {{
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.5px;
      color: var(--accent-amber);
      margin-bottom: 4px;
    }}

    .bullet-item {{
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 12px 16px;
      display: flex;
      align-items: flex-start;
      gap: 12px;
      box-shadow: var(--shadow-sm);
      font-size: 14.5px;
      line-height: 1.55;
    }}

    .bullet-dot {{
      color: var(--accent-blue);
      font-size: 18px;
      line-height: 1.3;
    }}

    .bullet-text {{
      flex: 1;
    }}

    .ticker-badge {{
      background: var(--bg-card-subtle);
      border: 1px solid var(--border-color);
      color: var(--accent-blue);
      padding: 1px 6px;
      border-radius: 6px;
      font-family: monospace;
      font-size: 13px;
    }}

    .text-paragraph {{
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 12px 16px;
      font-size: 14.5px;
      box-shadow: var(--shadow-sm);
    }}

    /* Table Component (Mobile Responsive with Horizontal Scroll) */
    .table-container {{
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 14px;
      padding: 12px;
      overflow-x: auto;
      box-shadow: var(--shadow-md);
      -webkit-overflow-scrolling: touch;
    }}

    .data-table {{
      width: 100%;
      min-width: 600px;
      border-collapse: collapse;
      font-size: 13.5px;
      text-align: left;
    }}

    .data-table th {{
      background: var(--bg-card-subtle);
      color: var(--text-muted);
      font-weight: 700;
      padding: 10px 14px;
      border-bottom: 2px solid var(--border-color);
      text-transform: uppercase;
      font-size: 11.5px;
      letter-spacing: 0.5px;
      position: sticky;
      top: 0;
    }}

    .data-table td {{
      padding: 12px 14px;
      border-bottom: 1px solid var(--border-color);
      color: var(--text-main);
    }}

    .data-table tr:last-child td {{
      border-bottom: none;
    }}

    .data-table tr:hover td {{
      background-color: var(--bg-card-subtle);
    }}

    .badge-change {{
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 16px;
      font-size: 12.5px;
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
      background: var(--accent-blue-bg);
      color: var(--accent-blue);
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 6px;
      font-size: 12px;
      display: inline-block;
    }}

    .link-card {{
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 16px;
      box-shadow: var(--shadow-sm);
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}

    .link-btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      background: linear-gradient(135deg, #0284c7, #2563eb);
      color: #fff !important;
      padding: 12px 20px;
      border-radius: 10px;
      text-decoration: none;
      font-weight: 700;
      font-size: 14.5px;
      box-shadow: 0 4px 12px rgba(2, 132, 199, 0.25);
      transition: opacity 0.2s, transform 0.1s;
    }}

    .link-btn:hover {{
      opacity: 0.95;
      transform: translateY(-1px);
    }}

    .link-url {{
      color: var(--accent-blue);
      word-break: break-all;
      font-size: 13px;
    }}

    footer {{
      text-align: center;
      margin-top: 36px;
      color: var(--text-muted);
      font-size: 12px;
      line-height: 1.5;
    }}

    /* Mobile view tweaks */
    @media (max-width: 600px) {{
      header {{
        padding: 12px 14px;
      }}
      .site-title {{
        font-size: 17px;
      }}
      .brief-subject {{
        font-size: 19px;
      }}
      .brief-meta-card {{
        padding: 18px 14px;
      }}
      .bullet-item, .text-paragraph {{
        padding: 10px 14px;
        font-size: 14px;
      }}
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
      <div class="header-actions">
        <button class="btn-action" onclick="toggleTheme()">
          <span id="theme-icon">🌙</span> <span id="theme-text">Dark</span>
        </button>
      </div>
    </div>
  </header>

  <main>
    <div class="brief-meta-card">
      <div class="brief-tag-row">
        <div class="brief-tag">⚡ Automated 7:00 AM Stock Report</div>
        <div class="live-badge"><span class="live-dot"></span> Latest Report</div>
      </div>
      <h1 class="brief-subject">{subject}</h1>
      <div class="meta-grid">
        <div class="meta-item"><strong>From:</strong> {from_addr}</div>
        <div class="meta-item"><strong>Date:</strong> {date_sent}</div>
        <div class="meta-item"><strong>Updated:</strong> {fetched_at}</div>
      </div>
    </div>

    <div class="email-content-container">
      {body}
    </div>

    <footer>
      Auto-generated from Daily 7:00 AM Email • Strictly verified & updated via GitHub Actions
    </footer>
  </main>

  <script>
    function toggleTheme() {{
      const current = document.documentElement.getAttribute('data-theme');
      const target = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', target);
      document.getElementById('theme-icon').innerText = target === 'dark' ? '☀️' : '🌙';
      document.getElementById('theme-text').innerText = target === 'dark' ? 'Light' : 'Dark';
      localStorage.setItem('theme', target);
    }}

    const savedTheme = localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    if (savedTheme === 'dark') {{
      document.documentElement.setAttribute('data-theme', 'dark');
      document.getElementById('theme-icon').innerText = '☀️';
      document.getElementById('theme-text').innerText = 'Light';
    }}
  </script>
</body>
</html>
"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)
    print("Successfully generated index.html!")
    return True

if __name__ == "__main__":
    email_data = fetch_latest_daily_email()
    if email_data:
        generate_html_page(email_data)
    else:
        print("No new target email to process. Existing page retained.")
