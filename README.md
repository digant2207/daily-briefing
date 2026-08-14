# Automated Daily Briefing Email to GitHub Pages 🚀

This repository automatically logs into your email inbox daily at **7:30 AM IST (02:00 UTC)**, fetches your **7:00 AM daily briefing email**, extracts its HTML content, and publishes it live as a clean, responsive web page hosted on **GitHub Pages**.

---

## 📋 What is Included

1. **`fetch_email.py`**: Python script that securely connects via IMAP, parses the latest daily email, and builds `index.html`.
2. **`.github/workflows/fetch_daily_email.yml`**: GitHub Actions workflow running on a daily schedule (`cron: '0 2 * * *'`) and manual trigger.
3. **`index.html`**: Responsive, theme-aware web page template (Light/Dark mode toggle, executive header, formatted email content container).

---

## 🔑 Setup Instructions (3 Simple Steps)

### Step 1: Set up GitHub Repository Secrets
Go to your GitHub Repository -> **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**.

Add the following Secrets:

| Secret Name | Value | Example |
| :--- | :--- | :--- |
| `EMAIL_USER` | Your full email address | `yourname@gmail.com` |
| `EMAIL_PASS` | App Password (not your main password) | `abcd efgh ijkl mnop` |
| `IMAP_SERVER` | Your email provider's IMAP host | `imap.gmail.com` (Gmail) or `outlook.office365.com` (Outlook) |
| `IMAP_PORT` | IMAP SSL Port (Optional) | `993` (default) |
| `SENDER_FILTER` | (Optional) Specific sender email to target | `briefing@domain.com` |
| `SUBJECT_FILTER` | (Optional) Subject line phrase to target | `Daily Brief` |

> 💡 **For Gmail users**: Generate an App Password via [Google Account -> Security -> 2-Step Verification -> App Passwords](https://myaccount.google.com/apppasswords).

---

### Step 2: Enable GitHub Pages
1. Go to your repository **Settings** -> **Pages**.
2. Under **Build and deployment** -> **Source**, select **Deploy from a branch**.
3. Choose `main` branch and `/ (root)` directory.
4. Click **Save**.

---

### Step 3: Test & Run Workflow
1. Go to the **Actions** tab in your GitHub repository (`https://github.com/digant2207/daily-briefing`).
2. Select **Fetch Daily Briefing Email & Update GitHub Page** on the left.
3. Click **Run workflow** -> **Run workflow**.
4. Once completed, your GitHub Pages site will be live at:
   `https://digant2207.github.io/daily-briefing/`

---

## ⏰ Schedule Details
- **Email Received**: 7:00 AM IST daily.
- **Workflow Runs**: 7:30 AM IST (02:00 UTC) daily.
