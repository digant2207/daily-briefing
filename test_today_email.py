from fetch_email import format_text_to_rich_html, generate_html_page, is_target_daily_stock_email
from datetime import datetime

# Unit tests for strict filtering
test_cases = [
    ("Daily Stock Report: Vijaya Diagnostic Breakout, High Volume Table", True),
    ("daily stock report - 29 August", True),
    ("Fwd: DAILY STOCK REPORT - Aug 29", True),
    ("Your Weekly Stock Newsletter", False),
    ("Your OTP for ICICI Bank login", False),
    ("Amazon.in order confirmation", False),
    ("Important security alert for your account", False),
    ("Stock Market News Alert", False),
    ("Daily Briefing from NYTimes", False)
]

print("Running strict subject filter verification tests...")
for subject_line, expected in test_cases:
    result = is_target_daily_stock_email(subject_line)
    status_str = "PASS" if result == expected else "FAIL"
    print(f"[{status_str}] '{subject_line}' => Expected {expected}, Got {result}")
    assert result == expected, f"Failed test for subject: {subject_line}"
print("All subject filter verification tests passed successfully!\n")

todays_email_text = """Hi Digant,
Here is your morning stock list report, 52-week high/low check, market opening setup, circuit status, volume surge table, level breach alerts, and corporate calendar update for Friday, August 29, 2026:

1. 52-Week High & Low Highlights:
- Stocks At / Near 52-Week Highs:
- Fineotex Chemical (fcl): Current ₹49.00 vs 52W High ₹51.38 (-4.6%; 13.25M shares).
- Acme Solar Holdings (acmesolar): Current ₹398.00 vs 52W High ₹411.50 (-3.3%).
- Action Construction Equipment (ace): Current ₹1,155.00 vs 52W High ₹1,196.00 (-3.4%).
- Sigma Advanced Systems (sigmaadv): Current ₹692.70 vs 52W High ₹721.50 (-4.0%).
- HEG Ltd (HEG): Current ₹720.00 vs 52W High ₹749.00 (-3.9%).
- Hindustan Aeronautics Ltd (HAL): Current ₹4,890.00 vs 52W High ₹5,149.90 (-5.0%).
- Redington Ltd (redington): Current ₹351.50 vs 52W High ₹370.80 (-5.2%).
- Vijaya Diagnostic (VIJAYA): Current ₹1,482.30 vs 52W High ₹1,573.00 (-5.8%).
- Deccan Gold Mines (512068): Current ₹232.60 vs 52W High ₹250.65 (-7.2%).
- Sadhana Nitro Chem (SADHNANIQ): Current ₹2.90 vs 52W High ₹3.32.
- Stocks At / Near 52-Week Lows:
- Shrenik Ltd (SHRENIK): Trading at 52-WEEK LOW of ₹0.28 (fresh low of ₹0.27–0.28).
- Indian Railway Finance Corp (IRFC): Current ₹85.43 vs 52W Low ₹85.00 (+0.5%).
- HDFC Bank Ltd (HDFCBANK): Current ₹724.00 vs 52W Low ₹715.10 (+1.2%).
- Filatex Fashions Ltd (FILATFASH): Current ₹0.19 vs 52W Low ₹0.14.
- Housing Development & Infra (HDIL): Current ₹1.50 vs 52W Low ₹1.45 (+3.4%).

2. Major Indian Market Summary & Opening Setup:
- Thursday Market Rebound: Indian benchmarks rebounded sharply during monthly F&O expiry: Sensex rose 286.98 points (+0.37%) to 77,656.09, and Nifty 50 gained 115.50 points (+0.48%) to 24,334.55.
- Friday Opening Cues: GIFT Nifty is trading around 24,474–24,527 (+140 to +190 points premium), indicating a strong positive opening this morning on easing crude oil prices and global tech strength.
- Key Technical Levels: Immediate support moves up to 24,250–24,300, while resistance is pegged at 24,450–24,520.

3. Price Level Breach Alert:
- VIJAYA (Vijaya Diagnostic Centre Ltd): NEW BREAKOUT ALERT! Current Price ₹1,482.30 has crossed above your set Up Level threshold of ₹1,425.00.
- Blue Jet Healthcare (BLUEJET): Current Price ₹592.00 sustains above your set threshold of ₹460.00.

4. Upper & Lower Circuit / Momentum Check:
- Borosil Ltd (BOROLTD): Heavy buying volume of 18.59M shares (+20.1x volume surge) at ₹256.40.
- Rashtriya Chemicals & Fertilizers (RCF): Surged on 18.10M volume (+12.0x volume surge) to ₹124.22.
- Sigachi Industries (SIGACHI): Rallied +10.9% to ₹33.78 on 16.06M shares (+5.51x volume surge).

5. High Volume Surge Stocks (> 2x 1-Month Avg Volume):
| Stock | Current Price (₹) | Change in Price (% / ₹) | Volume | Volume Surge Times |
| :--- | :--- | :--- | :--- | :--- |
| Sarda Energy & Minerals (SARDAEN) | ₹529.25 | +7.8% | 21,370,686 | 81.2x |
| Borosil Ltd (BOROLTD) | ₹256.40 | +0.6% | 18,593,567 | 20.1x |
| Fineotex Chemical (fcl) | ₹41.80 | -1.4% | 5,294,086 | 14.2x |
| RCF (RCF) | ₹124.22 | +4.5% | 18,100,384 | 12.0x |
| Gujarat Pipavav Port (GPPL) | ₹151.95 | +2.1% | 9,224,012 | 9.45x |
| Sigachi Industries (SIGACHI) | ₹33.78 | +10.9% | 16,061,164 | 5.51x |
| ZF Commercial Vehicles (ZFCVINDIA) | ₹2,600.00 | -1.5% | 650,642 | 5.28x |
| Jindal Poly Invest (JPOLYINVST) | ₹1,068.30 | +1.8% | 49,750 | 4.68x |
| AWL Agri Business (AWL) | ₹200.60 | +3.4% | 16,360,851 | 4.53x |
| GSFC (GSFC) | ₹158.82 | -0.3% | 3,644,998 | 4.32x |
| NCL Industries (NCLIND) | ₹174.00 | +0.8% | 260,210 | 4.11x |
| Jullundur Motor Agency (JMA) | ₹88.90 | +1.6% | 22,658 | 3.83x |
| Hindustan Copper (HINDCOPPER) | ₹531.40 | -6.4% | 44,652,248 | 3.46x |
| Edelweiss Financial (EDELWEISS) | ₹124.26 | +4.8% | 7,915,912 | 2.91x |
| IFCI Ltd (IFCI) | ₹76.55 | +1.3% | 35,636,368 | 2.47x |
| Tata Power (TATAPOWER) | ₹370.00 | -0.5% | 9,167,396 | 2.30x |
| Great Eastern Shipping (GESHIP) | ₹1,342.00 | +0.1% | 2,444,622 | 2.10x |
| Jio Financial Services (JIOFIN) | ₹255.50 | +0.7% | 43,028,580 | 2.05x |

6. Moving Average Crossover Status:
- No new Golden Cross or Death Cross transitions occurred today. (Ongoing/static crossovers are omitted per your preference).

7. Corporate Announcements & News:
- Kuantum Papers Ltd: 29th Annual General Meeting at 11:30 AM IST.
- NMDC Ltd: 68th AGM on September 28, 2026; Record Date Monday, October 5, 2026 for ₹1.00/share final dividend.
- Tata Power: Commissioned 190.5 MW FDRE project in Rajasthan.
- IRFC: Received GST show cause notice over FY23 ITC claim.
- HCL Infosystems: 40th AGM on Sept 16 to approve ₹1,500 crore promoter-group financial support.

8. Upcoming Events in Google Calendar:
- Monday, Aug 31: Indian Oil Corporation Ltd (67th AGM at 11:00 AM IST), Savita Oil Technologies Ltd (65th AGM at 11:00 AM IST).
- Wednesday, Sep 2: Deccan Gold Mines Ltd (EGM at 11:30 AM IST).
- Thursday, Sep 10: Delta Corp Ltd (35th AGM at 11:00 AM IST; Re. 0.50/share final dividend).
- Wednesday, Sep 16: HCL Infosystems Ltd (40th AGM at 11:00 AM IST).
- Monday, Sep 28: NMDC Ltd (68th AGM at 11:00 AM IST).
- Monday, Oct 5: NMDC Ltd (Record Date for Final Dividend of ₹1.00/share).

Spreadsheet Tracker Link: [Google Sheets Daily Tracker](https://docs.google.com/spreadsheets/d/1_rWhyap8gO-u8ehP1vDCiad-RwnFjGBCn2R5qiis4_A/edit)
"""

email_data = {
    "subject": "Daily Stock Report: Gap-Up Opening Setup, High Volume Surges & Corporate Updates",
    "from": "Digant Joshi <digant73@gmail.com>",
    "date": "Friday, August 29, 2026 at 7:00 AM IST",
    "body": format_text_to_rich_html(todays_email_text),
    "fetched_at": datetime.now().strftime("%B %d, %Y - %I:%M %p IST")
}

generate_html_page(email_data)
print("Successfully generated index.html with new mobile design!")
