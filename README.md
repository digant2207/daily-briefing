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

## ⏰ Schedule Details (Simple Once-A-Day Morning Update)

- **Morning Scan Window**: Runs every 15 minutes between **06:30 AM and 01:00 PM IST** (plus 1:30 PM and 3:30 PM IST checks).
- **Once-A-Day Update**: As soon as today's morning email arrives, the page updates once. Subsequent checks recognize that today's report is already published and automatically skip to prevent duplicate commits.
- **Manual Trigger**: Go to **Actions** -> **Fetch Daily Briefing Email & Update GitHub Page** -> **Run workflow** anytime. You can also toggle `Force overwrite index.html` if you want to regenerate the page.

---

## 🌐 Connect with Cron-Job.org (Guaranteed 100% On-Time Execution)

GitHub's built-in cron schedule can experience queuing delays or enter sleep mode if a repo is inactive. To trigger your daily update **on the exact minute with 0 delay**, connect a free cron trigger from [cron-job.org](https://cron-job.org/):

### Step 1: Create a GitHub Personal Access Token (PAT)
1. Go to your GitHub profile -> **Settings** -> **Developer Settings** -> **Personal access tokens** -> **Tokens (classic)** (or [click here](https://github.com/settings/tokens)).
2. Click **Generate new token (classic)**.
3. Name it: `CronJob Daily Brief Trigger`.
4. Select scope: Check ✅ **`repo`** (Full control of private repositories) or **`workflow`**.
5. Click **Generate token** and copy the token value (e.g. `ghp_xxxxxxxxxxxxxxxxxxxx`).

### Step 2: Set up a Cron Job on Cron-Job.org
1. Create a free account at [cron-job.org](https://cron-job.org/) and log in.
2. Click **CREATE CRONJOB** / **Cronjobs** -> **Create**.
3. Fill in the following settings:
   - **Title**: `Daily Stock Briefing Update`
   - **URL**: `https://api.github.com/repos/digant2207/daily-briefing/dispatches`
   - **Execution Schedule**: Set your desired time (e.g. Every 15 minutes between 7:00 AM and 10:00 AM IST, or every day at 7:05 AM, 7:15 AM, 7:30 AM IST).
   - **Request Method**: `POST`
   - **HTTP Headers**: Add the following 4 headers:
     1. `Accept`: `application/vnd.github+json`
     2. `Authorization`: `Bearer ghp_YOUR_COPIED_GITHUB_TOKEN` *(replace with your actual token)*
     3. `User-Agent`: `CronJob-DailyBrief`
     4. `X-GitHub-Api-Version`: `2022-11-28`
   - **Request Body**:
     ```json
     {"event_type": "cron_trigger"}
     ```
4. Click **Create** / **Save**.

### Test Your Webhook via Terminal (cURL)
You can test the trigger anytime from your terminal:
```bash
curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer YOUR_GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/digant2207/daily-briefing/dispatches \
  -d '{"event_type":"cron_trigger"}'
```
This instantly starts the GitHub Action to fetch your email and refresh the page within 30 seconds!

