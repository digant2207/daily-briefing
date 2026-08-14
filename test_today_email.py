from fetch_email import format_text_to_rich_html, generate_html_page
from datetime import datetime

todays_email_text = """Hi Digant,
Here is your daily stock list report, market summary, circuit status, volume surge table, level breach alert, and corporate calendar update for Friday, August 14, 2026:

1. Major Indian Market Summary:
- GIFT Nifty indicates a flat-to-positive start near 24,467 (+0.29%) this morning.
- In Thursday's session (August 13), Indian equities ended rangebound with Nifty closing at 24,395 (-40 points) and Sensex up 113 points at 78,080.
- Investor focus today is on major Q1 earnings releases (including NMDC, Borosil, NMDC Steel) and global macroeconomic trends ahead of the weekend.

2. Price Level Breach Alert:
- VIJAYA (Vijaya Diagnostic Centre Ltd): NEW BREAKOUT ALERT! Current Price ₹1,497.90 has crossed above your set Up Level threshold of ₹1,425.00.

3. Upper & Lower Circuit Check:
- E2E Networks Ltd (e2e): Trading near session high at ₹640.50 (+5.0% Upper Circuit) on strong AI GPU cloud infrastructure demand.
- No other tracked stock hit upper or lower circuit limits in yesterday's session.

4. High Volume Surge Stocks (> 2x 1-Month Avg Volume):
| Stock | Current Price (₹) | Change in Price (% / ₹) | Volume | Volume Surge Times |
| :--- | :--- | :--- | :--- | :--- |
| Sarda Energy & Minerals (SARDAEN) | ₹529.25 | +7.8% | 21,370,686 | 81.2x |
| Fineotex Chemical (fcl) | ₹41.80 | -1.4% | 5,294,086 | 14.2x |
| Gujarat Pipavav Port (GPPL) | ₹151.95 | +2.1% | 9,224,012 | 9.45x |
| Jindal Poly Invest (JPOLYINVST) | ₹1,068.30 | +1.8% | 49,750 | 4.68x |
| Jullundur Motor Agency (jma) | ₹88.90 | +1.6% | 22,658 | 3.83x |
| Edelweiss Financial (EDELWEISS) | ₹124.26 | +4.8% | 7,915,912 | 2.91x |
| IFCI Ltd (IFCI) | ₹76.55 | +1.3% | 35,636,368 | 2.47x |
| Jio Financial Services (JIOFIN) | ₹255.50 | +0.7% | 43,028,580 | 2.05x |

5. Moving Average Crossover Status:
- No new Golden Cross or Death Cross transitions occurred today. (Ongoing/static crossovers are omitted per your preference).

6. Corporate Events Scheduled Today (Friday, August 14, 2026):
- Borosil Ltd: Q1 FY27 Board Meeting (Results approval).
- NMDC Ltd & NMDC Steel Ltd: Q1 FY27 Board Meetings (Results approval).
- Ather Energy Ltd: Extraordinary General Meeting (EGM) at 11:30 AM IST (Approval for ₹1,200 Cr preferential issue).
- DCW Ltd: Q1 FY27 Earnings Call at 2:00 PM IST.
- Kuantum Papers Ltd: Q1 FY27 Earnings Call at 3:00 PM IST.

7. Upcoming Events in Google Calendar:
- Wednesday, Aug 19: Ather Energy Ltd (13th AGM at 11:00 AM IST).
- Monday, Aug 31: Indian Oil Corporation Ltd (67th AGM at 11:00 AM IST), Savita Oil Technologies Ltd (65th AGM at 11:00 AM IST).
- Wednesday, Sep 2: Deccan Gold Mines Ltd (EGM at 11:30 AM IST).
- Wednesday, Sep 16: HCL Infosystems Ltd (40th AGM at 11:00 AM IST).

Spreadsheet Tracker Link: [Google Sheets Daily Tracker](https://docs.google.com/spreadsheets/d/1_rWhyap8gO-u8ehP1vDCiad-RwnFjGBCn2R5qiis4_A/edit)
"""

email_data = {
    "subject": "Daily Stock Report: Vijaya Diagnostic Breakout, High Volume Table & Today's Earnings Calls",
    "from": "Digant Joshi <digant73@gmail.com>",
    "date": "Friday, August 14, 2026 at 7:00 AM IST",
    "body": format_text_to_rich_html(todays_email_text),
    "fetched_at": datetime.now().strftime("%B %d, %Y - %I:%M %p IST")
}

generate_html_page(email_data)
print("Successfully generated index.html for today's email!")
