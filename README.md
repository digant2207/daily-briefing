# Automated Daily Stock Report to Mobile-Friendly GitHub Page 🚀

This repository automatically logs into your Gmail inbox every morning, strictly fetches your **"Daily Stock Report"** email, formats it into an executive mobile-first dashboard, and publishes it live to **GitHub Pages**.

---

## 📋 Features & Architecture

1. **Strict Filter Verification**: `fetch_email.py` strictly checks incoming email headers for `"Daily Stock Report"`. It will never read or overwrite pages with unrelated inbox emails (e.g. OTPs, newsletters, personal emails).
2. **Multi-Interval Morning Cron Schedule**: Runs automatically at **7:00 AM, 7:15 AM, 7:30 AM, 7:45 AM, 8:00 AM, 8:15 AM, 8:30 AM, 9:00 AM, 9:30 AM, and 10:00 AM IST** to catch both on-time and late-arriving emails.
3. **Mobile-First Reading UI**:
   - **Quick-Jump Pills**: Instantly jump to `🎯 52W High/Low`, `📊 Market Setup`, `🚨 Breakouts`, `⚡ Circuits`, `🔥 Volume Surges`, `📈 MA Crossover`, and `📅 Calendar`.
   - **Modern Data Tables**: Touch-friendly horizontal scrolling table with color-coded positive/negative change chips and volume surge tags.
   - **Breakout Alert Callouts**: Glowing alert cards for level breaches.
   - **Dark / Light Theme Toggle**: Automatically follows system preference with instant one-tap toggle.
   - **PWA & iOS Web App Support**: Can be added directly to your mobile home screen.

---

## 🔑 GitHub Repository Secrets Configuration

Go to your GitHub Repository -> **Settings** -> **Secrets and variables** -> **Actions** -> **Repository secrets**:

| Secret Name | Value | Description |
| :--- | :--- | :--- |
| `EMAIL_USER` | Your full Gmail address | e.g. `yourname@gmail.com` |
| `EMAIL_PASS` | Gmail App Password (16 chars) | e.g. `abcd efgh ijkl mnop` |
| `IMAP_SERVER` | `imap.gmail.com` | IMAP server (defaults to `imap.gmail.com`) |
| `IMAP_PORT` | `993` | IMAP SSL port (defaults to `993`) |
| `SUBJECT_FILTER` | `Daily Stock Report` | Target subject phrase (defaults to `Daily Stock Report`) |
| `SENDER_FILTER` | *(Optional)* | Filter by sender email if desired |

> 💡 **For Gmail App Passwords**: Generate a 16-character App Password via [Google Account -> Security -> 2-Step Verification -> App Passwords](https://myaccount.google.com/apppasswords).

---

## ⏰ Schedule Details

- **Email Expected**: ~7:00 AM IST (or slightly later).
- **Automated Workflow Checks**: Every 15-30 mins between 7:00 AM IST and 10:00 AM IST.
- **Manual Trigger**: Go to **Actions** -> **Fetch Daily Briefing Email & Update GitHub Page** -> **Run workflow** anytime.
