# 🚀 Google Sheets Integration - Quick Start

Your scraper now exports results directly to Google Sheets in real-time! Here's how to set it up in 5 minutes.

---

## 🎯 What You Get

✅ Automatic export to Google Sheets after each scrape  
✅ Real-time cloud backup (shareable with team)  
✅ Summary statistics sheet  
✅ Auto-formatted headers  
✅ No manual file uploads needed  

---

## ⚡ 5-Minute Setup

### Step 1: Verify Your .env File

Check that your `.env` already has:

```bash
cat .env
```

Should show:
```
SHEET_ID=1-NEyYpgKMJX8_ABtyiLnxU-Fl6-v_gkcYd_ou1esOa4
GOOGLE_APPLICATION_CREDENTIALS=./secure_keys/my-service-account.json
```

If missing, add them.

### Step 2: Verify Service Account JSON

Your JSON should be at: `./secure_keys/my-service-account.json`

If you need to get it:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Follow steps in `GOOGLE_SHEETS_SETUP.md`

### Step 3: Update Requirements

```bash
pip install -r requirements.txt
# This installs: gspread, google-auth, google-auth-oauthlib
```

### Step 4: Test Connection

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

### Step 5: Run Scraper

```bash
python main_scraper.py test
```

**Done!** 🎉 Results appear in Google Sheet automatically

---

## 📊 What Gets Exported

### Sheet 1: "Businesses"

All scraped records:
```
name | primary_phone | whatsapp | address | lga | state | rating | source
Ikeja Plumbers | +2347031234567 | +2347031234567 | 123 Ikeja Rd | Ikeja | Lagos | 4.8 | google_maps
```

### Sheet 2: "Summary"

Statistics:
```
Metric | Value
Total Records | 1,234
Records with Phone | 1,100
Records with WhatsApp | 856
Unique States | 5
```

---

## 🔧 Common Tasks

### Task 1: Check If It's Working

```bash
# Run scraper and watch for this message in logs:
tail -f scraper.log | grep "Google Sheets"

# Output should show:
# "Successfully exported X records to Google Sheets"
```

### Task 2: Share Results with Team

1. Open your Google Sheet
2. Click "Share" (top right)
3. Add team member emails
4. Give "Viewer" permission (to prevent edits)

### Task 3: Export by State (Optional)

Edit `main_scraper.py` around line 194, uncomment:

```python
# Grouped export - creates separate sheet per state
self.sheets_integration.export_results(
    self.results,
    grouped=True,
    group_by="state"
)
```

Now sheets will be: "Lagos", "Abuja", "Kano", etc.

### Task 4: Check Logs

```bash
# See all Google Sheets activity
grep "Google Sheets\|Successfully exported" scraper.log

# See errors
grep "ERROR" scraper.log | grep -i "sheets"
```

---

## 🐛 Troubleshooting

### Problem: "Permission denied" Error

**Solution**: Share Google Sheet with service account email

```bash
# Get the service account email:
cat ./secure_keys/my-service-account.json | grep client_email
```

Then:
1. Open your Google Sheet
2. Click Share
3. Paste the email
4. Click Share

### Problem: "FileNotFoundError: my-service-account.json"

**Solution**: Create the secure_keys folder and place JSON file

```bash
mkdir -p ./secure_keys
# Move or copy your JSON file here
mv ~/Downloads/my-service-account.json ./secure_keys/
```

### Problem: "ModuleNotFoundError: gspread"

**Solution**: Install required packages

```bash
pip install -r requirements.txt
```

### Problem: No Data Appearing in Sheet

**Solution**: Check the scraper log

```bash
tail -50 scraper.log
# Look for "Successfully exported" message
# If you see errors, Google Sheets integration is disabled
```

---

## 📈 How It Works

```python
# This happens automatically:

1. scraper.py runs and generates queries
2. Scrapes websites (Google Maps, YellowPages, etc)
3. Cleans data (phone standardization, etc)
4. Deduplicates records
5. Exports to Google Sheets ← YOU'RE HERE
   - Writes to "Businesses" sheet
   - Creates "Summary" sheet
   - Auto-formats headers
6. Also saves locally (JSON/CSV/Excel)
```

---

## ✅ Verification Checklist

- [ ] `.env` has SHEET_ID and GOOGLE_APPLICATION_CREDENTIALS
- [ ] `./secure_keys/my-service-account.json` exists
- [ ] Ran `pip install -r requirements.txt`
- [ ] Ran `python test_google_sheets.py` - all checks pass
- [ ] Google Sheet is shared with service account email
- [ ] Ran `python main_scraper.py test` - data appears in sheet
- [ ] Checked `scraper.log` for "Successfully exported" message

---

## 🔒 Security Notes

✅ Service account (not personal account - secure)  
✅ JSON key in `secure_keys/` (hidden from git)  
✅ Minimal permissions ("Editor" only for needed sheet)  

**Don't**:
- Share the JSON file
- Commit it to git
- Use personal Google account

---

## 📚 Full Documentation

For detailed setup:
- See `GOOGLE_SHEETS_SETUP.md` (complete guide)
- See `GOOGLE_SHEETS_INTEGRATION.md` (technical details)

For scraper options:
- See `README.md` (full scraper documentation)

---

## 💡 Pro Tips

### Tip 1: Monitor Progress
```bash
# Watch scraper and Google Sheets activity in real-time
watch -n 5 "tail scraper.log | grep 'Google Sheets\|records\|completed'"
```

### Tip 2: Schedule Daily Runs
```bash
# Add to crontab
0 2 * * * cd /home/gamp/Scripts/nexascraper && python main_scraper.py priority
```

### Tip 3: Create Dashboard
1. Export to Google Sheets
2. Use Google Sheets formulas for summaries
3. Add charts/graphs
4. Share dashboard link with stakeholders

### Tip 4: Filter by Industry
In Google Sheet, select data and use "Data" → "Create a filter"

---

## 🆘 Still Not Working?

1. **Run diagnostics**:
   ```bash
   python test_google_sheets.py
   ```

2. **Check permissions**:
   - Google Sheet shared with service account? ✓
   - Service account has "Editor" access? ✓

3. **Check logs**:
   ```bash
   tail -100 scraper.log
   ```

4. **Try manual export**:
   ```bash
   python -c "
   from utils.google_sheets_writer import GoogleSheetsIntegration
   gs = GoogleSheetsIntegration()
   test_data = [{'name': 'Test', 'phone': '+2347031234567'}]
   gs.writer.write_businesses(test_data)
   print('✓ Manual export successful')
   "
   ```

---

## 🎯 Next Steps

1. ✅ Run the test: `python test_google_sheets.py`
2. ✅ Run the scraper: `python main_scraper.py test`
3. ✅ Check Google Sheet for data
4. ✅ Share with team
5. ✅ Schedule regular runs (cron)

---

**Ready! Your data is now in the cloud. 🌐**

Questions? Check the full docs or contact support.
