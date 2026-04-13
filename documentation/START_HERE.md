# 🚀 START HERE - Google Sheets Integration Ready!

Your Nigerian Business Scraper is now **fully integrated with Google Sheets** for automatic cloud export.

---

## ✅ What's Done

**Google Sheets integration is complete and ready to use.** Your scraper will now automatically export all scraped data to a Google Sheet with:

- ✅ All business records (name, phone, WhatsApp, address, location, rating, source)
- ✅ Summary statistics (total records, data quality metrics)
- ✅ Auto-formatted headers
- ✅ Real-time cloud backup (shareable with team)

---

## 🎯 3-Step Setup

### Step 1: Check Your .env File

Open `/home/gamp/Scripts/nexascraper/.env` and verify it has:

```
SHEET_ID=1-NEyYpgKMJX8_ABtyiLnxU-Fl6-v_gkcYd_ou1esOa4
GOOGLE_APPLICATION_CREDENTIALS=./secure_keys/my-service-account.json
```

If these aren't set, see `GOOGLE_SHEETS_SETUP.md` for full instructions.

### Step 2: Install Packages

```bash
cd /home/gamp/Scripts/nexascraper
pip install -r requirements.txt
```

This adds gspread + Google authentication libraries.

### Step 3: Run Scraper (Data Auto-Exports!)

```bash
python main_scraper.py test
```

**That's it!** Check your Google Sheet - data appears automatically.

---

## 📊 What Gets Exported

### Sheet 1: "Businesses" 
All scraped records with:
- Business name
- Phone number (standardized to +234 format)
- WhatsApp contact
- Address
- LGA & State
- Rating
- Review count
- Source (Google Maps, YellowPages, etc)

### Sheet 2: "Summary"
Statistics including:
- Total records scraped
- Records with phone numbers
- Records with WhatsApp
- Coverage by state/industry
- Data quality metrics

---

## 🧪 Test Before Full Run

Verify everything works:

```bash
python test_google_sheets.py
```

Should show:
```
✓ PASS - Environment Variables
✓ PASS - Credentials File
✓ PASS - Python Packages
✓ PASS - Google Sheets Connection
```

---

## 📚 Documentation

| Document | Read This For |
| --- | --- |
| **QUICK_START_SHEETS.md** | 5-minute quick reference |
| **GOOGLE_SHEETS_SETUP.md** | Complete setup + troubleshooting |
| **GOOGLE_SHEETS_INTEGRATION.md** | Technical details & advanced usage |
| **README.md** | Full scraper documentation |

---

## ⚡ Common Commands

```bash
# Test with 50 queries (5 min)
python main_scraper.py test

# Priority cities only (2-4 hours)
python main_scraper.py priority

# All 36 states (12-24 hours)
python main_scraper.py full

# Check logs
tail -f scraper.log

# Verify Google Sheets connection
python test_google_sheets.py
```

---

## 🔒 Your Data is Secure

- Service account (not personal Google account)
- Credentials in `secure_keys/` folder (not committed to git)
- OAuth 2.0 authentication
- Minimal permissions ("Editor" for one sheet only)

---

## 🎉 You're Ready!

Everything is set up. Just run:

```bash
python main_scraper.py test
```

Results appear in your Google Sheet automatically.

**Questions?** See `QUICK_START_SHEETS.md` or `GOOGLE_SHEETS_SETUP.md`

---

**Happy scraping! Your data is in the cloud. 🌐**
