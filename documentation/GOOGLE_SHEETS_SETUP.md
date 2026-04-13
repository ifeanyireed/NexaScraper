# Google Sheets Integration Setup Guide

This guide helps you connect the Nigerian Business Scraper to export results directly to Google Sheets in real-time.

---

## 🔧 Prerequisites

- Google Cloud Project with Sheets API enabled
- Service Account with appropriate permissions
- Google Sheet prepared to receive data

---

## Step-by-Step Setup

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project: **New Project** → Name it (e.g., "Nigerian Business Scraper")
3. Wait for project to initialize

### 2. Enable Google Sheets API

1. In Cloud Console, go to **APIs & Services** → **Library**
2. Search for "Google Sheets API"
3. Click on it and press **ENABLE**
4. Do the same for "Google Drive API"

### 3. Create Service Account

1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **Service Account**
3. Fill in:
   - **Service account name**: `nigerian-business-scraper`
   - **Service account ID**: (auto-filled)
   - Click **CREATE AND CONTINUE**
4. Grant role: 
   - Select **Editor** (or custom "Sheets Editor" role)
   - Click **CONTINUE**
5. Click **CREATE KEY** → **JSON** → **Create**
   - A JSON file will download automatically

### 4. Prepare Service Account Key

```bash
# Create secure folder
mkdir -p /home/gamp/Scripts/nexascraper/secure_keys

# Move downloaded JSON file to secure folder
mv ~/Downloads/my-service-account.json /home/gamp/Scripts/nexascraper/secure_keys/

# Restrict permissions
chmod 600 /home/gamp/Scripts/nexascraper/secure_keys/my-service-account.json
```

### 5. Create Google Sheet

1. Go to [Google Sheets](https://sheets.google.com/)
2. Click **+ Blank** to create new sheet
3. Name it (e.g., "Nigerian Businesses")
4. Note the Sheet ID from URL:
   ```
   https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit
   ```

### 6. Share Sheet with Service Account

1. Copy the service account email from the JSON file
   ```bash
   cat /home/gamp/Scripts/nexascraper/secure_keys/my-service-account.json | grep "client_email"
   ```
2. In your Google Sheet, click **Share** button
3. Paste the service account email
4. Give **Editor** permissions
5. Click **Share**

### 7. Configure Environment Variables

Update `.env` file:

```bash
# Get Sheet ID from Google Sheet URL
SHEET_ID=1-NEyYpgKMJX8_ABtyiLnxU-Fl6-v_gkcYd_ou1esOa4

# Path to service account JSON
GOOGLE_APPLICATION_CREDENTIALS=./secure_keys/my-service-account.json
```

### 8. Install Google Packages

```bash
pip install -r requirements.txt
# This includes: gspread, google-auth, google-auth-oauthlib
```

### 9. Test Connection

```bash
python -c "
from utils.google_sheets_writer import GoogleSheetsIntegration
gs = GoogleSheetsIntegration()
print('✓ Google Sheets connected!')
"
```

---

## 📊 Usage

### Automatic Export (in scraper pipeline)

The scraper will automatically export to Google Sheets after scraping:

```bash
python main_scraper.py priority
```

Results will be written to a sheet named "Businesses" with:
- Headers in bold with dark background
- All business records with contact info
- Automatic formatting

### Manual Export

```python
from utils.google_sheets_writer import GoogleSheetsIntegration

integration = GoogleSheetsIntegration()

# Export all records
integration.export_results(records)

# Export grouped by state
integration.export_results(records, grouped=True, group_by="state")

# Append new records (don't overwrite)
integration.writer.append_businesses(new_records)
```

### Create Grouped Sheets

Edit `main_scraper.py` to uncomment grouped export:

```python
# Enable this for separate sheets per state
self.sheets_integration.export_results(
    self.results,
    grouped=True,
    group_by="state"
)
```

---

## 📈 Output Features

### Auto-Formatted Sheets

- ✅ **Bold headers** with dark background
- ✅ **Individual sheets per state** (optional)
- ✅ **Summary statistics** sheet with counts
- ✅ **Auto-resized columns** for readability

### Data Structure

Headers automatically added:
```
name | primary_phone | whatsapp | address | lga | state | rating | reviews_count | source | ...
```

Example data:
```
Ikeja Plumbers | +2347031234567 | +2347031234567 | 123 Ikeja Rd | Ikeja | Lagos | 4.8 | 156 | google_maps
```

---

## 🔒 Security Best Practices

### Do ✅

- Keep `secure_keys/` folder in `.gitignore`
- Use restricted service account (minimum permissions)
- Rotate keys periodically
- Use `chmod 600` on JSON file (read-only)
- Never commit JSON file to git

### Don't ❌

- Share JSON file with others
- Commit to public repositories
- Give service account Admin permissions
- Use personal Google account credentials

### .gitignore

Ensure `.gitignore` contains:

```
secure_keys/
*.json
.env
```

---

## 🐛 Troubleshooting

### "FileNotFoundError: Service account file not found"

```bash
# Check path
ls -la ./secure_keys/my-service-account.json

# If not found, update GOOGLE_APPLICATION_CREDENTIALS in .env
```

### "Permission denied" on Google Sheet

```
Solution:
1. Copy service account email from JSON
2. Share Google Sheet with that email
3. Give "Editor" permission
```

### "The caller does not have permission to access the file"

```
Solution:
1. Check service account email is invited to Sheet
2. Verify in Google Drive the file is shared
3. Try creating a new credential file
```

### API Quota Exceeded

```
Solution:
- Google Sheets API has rate limits (~300 requests/min)
- Adjust batch_size in google_sheets_writer.py
- Wait before re-running
```

### "gspread not found"

```bash
pip install gspread google-auth-oauthlib
```

---

## 📝 Advanced Usage

### Custom Sheet Organization

```python
# Create separate sheets per industry
for industry in industries:
    industry_records = [r for r in records if r['industry'] == industry]
    writer.write_businesses(industry_records, sheet_name=industry)
```

### Append Instead of Overwrite

```python
# Add new records to existing sheet
writer.append_businesses(new_records)
```

### Summary Sheet

```python
stats = {
    "Total Businesses": len(records),
    "States Covered": 36,
    "Data Quality Score": 94.5
}
writer.write_summary_stats(stats)
```

---

## 📊 API Limits & Performance

| Metric | Limit | Notes |
| --- | --- | --- |
| Cells per request | ~1,000,000 | Scraper batches at 1,000 |
| Requests per minute | 300 | Usually not a limit for scraper |
| Sheet size | Unlimited | But very large sheets slow down |
| Worksheets per file | ~400 | More than enough for states |

---

## 🔄 Continuous Integration

### Schedule Regular Exports

```bash
# Crontab: Daily export at 2 AM
0 2 * * * cd /home/gamp/Scripts/nexascraper && python main_scraper.py priority
```

### Monitor Scraper Job

```bash
# Check recent logs
tail -100 scraper.log | grep "Google Sheets"
```

---

## ✅ Testing Checklist

- [ ] Created Google Cloud Project
- [ ] Enabled Sheets & Drive APIs
- [ ] Created Service Account
- [ ] Downloaded JSON key file
- [ ] Placed JSON in `secure_keys/`
- [ ] Created Google Sheet
- [ ] Shared sheet with service account email
- [ ] Updated SHEET_ID in `.env`
- [ ] Updated GOOGLE_APPLICATION_CREDENTIALS path in `.env`
- [ ] Ran test: `python -c "from utils.google_sheets_writer import GoogleSheetsIntegration; GoogleSheetsIntegration()"`
- [ ] Ran scraper: `python main_scraper.py test`
- [ ] Check Google Sheet for "Businesses" tab with data

---

## 📞 Support

For issues:
1. Check `scraper.log` for errors
2. Verify service account has Sheet access
3. Confirm API is enabled in Cloud Console
4. Try re-generating service account key

---

**Ready to scrape! 🚀**
