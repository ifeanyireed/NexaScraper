# Nigerian Business Multi-City, Multi-Industry Scraper

A comprehensive, production-ready Python framework for scraping Nigerian businesses across 10 industries, 36 states, and multiple data sources. Built with **Playwright**, **async processing**, and **AI-powered data cleaning**.

---

## 📋 Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Strategy Overview](#strategy-overview)
- [Data Quality](#data-quality)
- [Output Formats](#output-formats)
- [Performance Tuning](#performance-tuning)
- [Legal & Ethical Considerations](#legal--ethical-considerations)

---

## ✨ Features

### Tiered Scraping Strategy
- **Google Maps**: Physical locations, reviews, ratings (anti-bot challenge: high)
- **YellowPages NG**: Traditional business directories (anti-bot: medium)
- **Jiji**: Visual services marketplace (anti-bot: high)
- **Instagram**: Social media validation (anti-bot: high, requires auth)
- **CAC Database**: Corporate registration verification (anti-bot: low)

### 10 Core Industries
1. **Home & Maintenance** (Plumbers, Electricians, Solar Installers)
2. **Fashion & Personal Grooming** (Tailors, Hairdressers, Makeup Artists)
3. **Professional & Business Services** (Lawyers, Accountants, Developers)
4. **Education & Skill Development** (Tutors, Trainers)
5. **Events & Entertainment** (DJs, Photographers, Event Planners)
6. **Health & Wellness** (Nurses, Therapists, Gyms)
7. **Logistics & Transport** (Drivers, Dispatch Riders)
8. **Automotive Services** (Mechanics, Vulcanizers)
9. **Food & Agribusiness** (Chefs, Caterers, Farmers)
10. **Real Estate & Construction** (Agents, Architects)

### Geographic Coverage
- **36 Nigerian States**
- **Priority Cities**: Lagos, Abuja, Kano, Port Harcourt, Enugu
- **LGA-level targeting** for surgical precision

### Data Cleaning & Standardization
- ✅ Phone number standardization (→ +234 format)
- ✅ WhatsApp contact extraction (critical for Nigerian market)
- ✅ Address parsing & geocoding (lat/long)
- ✅ Ghost business detection (inactive/spam filtering)
- ✅ LGA & state extraction from raw addresses
- ✅ Duplicate detection & removal
- ✅ Record validation

### Performance Features
- ⚡ Async/await for concurrent requests
- 🔄 Automatic retry logic with exponential backoff
- ⏱️ Rate limiting to avoid IP blocks
- 🎭 Stealth headers & user-agent rotation
- 🧵 Configurable worker pool (max parallel tasks)

---

## 📁 Project Structure

```
nexascraper/
├── main_scraper.py              # Main orchestrator
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment configuration template
├── README.md                    # This file
├── scraper.log                  # Execution log
│
├── config/
│   ├── __init__.py
│   ├── industries.py            # 10 industries + finders lookup
│   └── locations.py             # Nigerian states + LGAs
│
├── utils/
│   ├── __init__.py
│   ├── data_cleaner.py          # Phone/address standardization, deduplication
│   └── query_generator.py       # Search query generation (10,000+ queries)
│
├── scrapers/
│   ├── __init__.py
│   └── base_scraper.py          # Base + implementations (GMaps, YellowPages, etc.)
│
└── data/                        # Output directory (auto-created)
    ├── businesses_*.json        # Raw results
    ├── businesses_*.csv         # Tabular format
    ├── businesses_*.xlsx        # Excel with formatting
    └── report_*.txt             # Summary report
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
cd /home/gamp/Scripts/nexascraper
pip install -r requirements.txt
```

### 2. Download Playwright Browsers

```bash
playwright install chromium
```

### 3. Run Test Mode (50 queries)

```bash
python main_scraper.py test
```

Expected output:
- Console logs with progress
- `scraper.log` file
- Results in `data/businesses_*.{json,csv,xlsx}`
- Summary report in `data/report_*.txt`

### 4. Run Full Pipeline

```bash
# Priority cities only (Lagos, Abuja, Kano, Port Harcourt, Enugu)
python main_scraper.py priority

# All 36 states (slow, 10,000+ queries)
python main_scraper.py full
```

---

## 📦 Installation

### Prerequisites
- Python 3.8+
- pip or conda
- ~50MB disk space for Playwright browsers
- ~500MB RAM (more for large batch runs)

### Step-by-Step

```bash
# 1. Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download Playwright chromium browser
playwright install chromium

# 4. Verify installation
python -c "from main_scraper import NigerianBusinessScraper; print('✓ Ready')"
```

---

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Key settings:

```ini
# Browser automation
HEADLESS_BROWSER=true           # Run without GUI
MAX_WORKERS=3                   # Concurrent tasks
TIMEOUT_SECONDS=30              # Per-page timeout

# Data cleaning
PHONE_STANDARDIZATION=true      # Normalize to +234
ADDRESS_GEOCODING=true          # Get lat/long
GHOST_BUSINESS_DETECTION=true   # Filter inactive

# Output
OUTPUT_FORMAT=csv,json,excel    # Save formats
OUTPUT_DIRECTORY=data/          # Where to save

# Proxy (for production)
USE_PROXY=false
RESIDENTIAL_PROXY_LIST=         # Comma-separated list
```

### Industry Configuration

Edit [config/industries.py](config/industries.py) to add/remove service types:

```python
"Home & Maintenance": {
    "handyman": ["Plumber", "Electrician", ...],
    "specialist": ["Solar Installer", ...],
}
```

### Location Configuration

Edit [config/locations.py](config/locations.py) to add/remove LGAs:

```python
"Lagos": {
    "lgas": ["Alimosho", "Ikeja", "Surulere", ...]
}
```

---

## 🎯 Usage

### Basic Usage

```python
import asyncio
from main_scraper import NigerianBusinessScraper

scraper = NigerianBusinessScraper()

# Run in test mode (50 queries, ~5 min)
asyncio.run(scraper.run_full_pipeline(mode='test'))
```

### Advanced Usage

```python
from utils.query_generator import SearchQueryGenerator
from utils.data_cleaner import DataCleaner

# Generate custom queries
qg = SearchQueryGenerator()
queries = qg.generate_lga_based_queries(use_priority=True)

# Clean a business record
cleaner = DataCleaner()
cleaned = cleaner.clean_business_record(raw_record)

# Validate
is_valid, errors = cleaner.validate_business_record(cleaned)
```

### Command-Line Arguments

```bash
# Test mode (quick validation)
python main_scraper.py test

# Priority cities (recommended for production)
python main_scraper.py priority

# Full 36 states (comprehensive, slow)
python main_scraper.py full
```

---

## 📊 Strategy Overview

### Phase 1: Query Generation
- Combine 10 industries with 36 states + LGAs
- Creates ~10,000+ unique search queries
- Prioritized by city relevance and service demand

### Phase 2: Search & Initial Extraction ("Breadcrumbs")
- Execute LGA-specific searches: *"Plumber in Ikeja, Lagos, Nigeria"*
- Extract basic info: business name, URL, initial contact details
- Screenshots cached for manual review

### Phase 3: Deep Dive Extraction
- Visit each business profile URL
- Extract "gold" data:
  - ✅ Verified phone numbers (tel: links)
  - ✅ WhatsApp contact (crucial in Nigeria)
  - ✅ Operating hours
  - ✅ Ratings & review count
  - ✅ Physical address

### Phase 4: Data Cleaning
- **Phone Standardization**: `0703123456` → `+2347031234567`
- **Address Parsing**: Extract LGA/State from freeform text
- **Geocoding**: Convert addresses to coordinates (lat/long)
- **Ghost Detection**: Remove spam/inactive (0 reviews, 24+ months inactive)
- **Validation**: Ensure contact info + address present

### Phase 5: Deduplication
- Remove duplicates by (name + phone) or (name + address)
- Merge data from multiple sources

### Phase 6: Output & Reporting
- Save to JSON (raw), CSV (Excel-friendly), XLSX (formatted)
- Generate summary report with metrics by state/industry/source

---

## 📈 Data Quality

### Quality Metrics

Your output will include:

```
Total Records: 5,432
│ 
├─ Records with Phone: 4,891 (90%)
├─ Records with WhatsApp: 3,245 (60%)
├─ Records with Address: 5,210 (96%)
├─ Records with Coordinates: 4,567 (84%)
│
└─ By State:
    ├─ Lagos: 2,100 records
    ├─ Abuja: 890 records
    ├─ Kano: 750 records
    └─ ...
```

### Handling Edge Cases

| Issue | Solution |
| --- | --- |
| Missing phone number | WhatsApp-only contacts accepted |
| Incomplete address | Use LGA + state for mapping |
| Duplicate entries | Merged by name + phone signature |
| Ghost businesses | Filtered if 0 reviews + 2+ years inactive |
| Inconsistent formats | Cleaned to standard format |

---

## 📤 Output Formats

### JSON
```json
[
  {
    "name": "Ikeja Plumbers",
    "finder_type": "Plumber",
    "industry": "Home & Maintenance",
    "primary_phone": "+2347031234567",
    "phones": ["+2347031234567", "+2348012345678"],
    "whatsapp": "+2347031234567",
    "address": "123 Ikeja Road, Lagos",
    "latitude": 6.5944,
    "longitude": 3.3521,
    "lga": "Ikeja",
    "state": "Lagos",
    "source": "google_maps",
    "rating": 4.8,
    "reviews_count": 156,
    "scraped_date": "2026-01-15T10:30:00"
  }
]
```

### CSV
```
name,primary_phone,whatsapp,address,lga,state,rating,source
Ikeja Plumbers,+2347031234567,+2347031234567,123 Ikeja Road,Ikeja,Lagos,4.8,google_maps
```

### Excel (.xlsx)
- Auto-formatted with:
  - Frozen header row
  - Auto-sized columns
  - Filtered state + industry columns

---

## 🚄 Performance Tuning

### Recommended Settings

| Mode | MAX_WORKERS | BATCH_SIZE | Duration | Records |
| --- | --- | --- | --- | --- |
| **test** | 2 | 5 | 5 min | 50-100 |
| **priority** | 3-4 | 10 | 2-4 hrs | 2,000-5,000 |
| **full** | 5+ | 15 | 12-24 hrs | 10,000+ |

### Performance Tips

```ini
# For fast iteration (testing)
MAX_WORKERS=2
DELAY_BETWEEN_REQUESTS_MIN=1
DELAY_BETWEEN_REQUESTS_MAX=2

# For production (avoid blocks)
MAX_WORKERS=3
DELAY_BETWEEN_REQUESTS_MIN=3
DELAY_BETWEEN_REQUESTS_MAX=8
USE_PROXY=true
```

### Memory Management

```bash
# Monitor memory usage
watch -n 1 'ps aux | grep main_scraper'

# Limit to available RAM
# On 4GB system: MAX_WORKERS=2, BATCH_SIZE=5
# On 8GB system: MAX_WORKERS=4, BATCH_SIZE=10
```

---

## ⚖️ Legal & Ethical Considerations

### ✅ Do

- Check `robots.txt` before scraping
- Respect `rate-limit` headers
- Add delays between requests
- Identify your scraper in User-Agent string
- Cache results to avoid re-scraping

### ❌ Don't

- Scrape personal data (GDPR, CCPA, Nigeria Privacy Act)
- Violate terms of service
- Use data for spam/harassment
- Resell data without permission
- Impersonate other users

### Legal Alternatives

For production enterprises, consider:

```
✅ Google Places API (Official, legal)
✅ YellowPages API (if available)
✅ CAC Open Data portal
✅ Business directory partnerships
```

### Nigeria-Specific

- **CAC Licensing**: Some scrapers may fall under Nigeria Data Protection Regulation (NDPR)
- **Telecommunications**: WhatsApp scraping needs extra caution
- **Privacy**: Avoid storing phone numbers + personal names together

---

## 🐛 Troubleshooting

### "Timeout waiting for selector"
```
Solution: Increase TIMEOUT_SECONDS or check site structure
```

### "Rate limited / IP blocked"
```
Solution: Enable proxy rotation, increase delays, use smaller batches
```

### "No results found"
```
Possible causes:
1. Site structure changed → update selectors in base_scraper.py
2. Anti-bot protection → try with headless=false for debugging
3. Query too specific → use broader terms
```

### "Memory error on full run"
```
Solution: Reduce MAX_WORKERS, run in smaller batches, or split by state
```

### "Phone numbers not standardizing"
```
Solution: Check phonenumbers library version, report format bugs
```

---

## 📝 Example Workflows

### Workflow 1: Quick Validation (5 min)
```bash
python main_scraper.py test
# ↓ Review data/report_*.txt
# ↓ Check data/businesses_*.csv
```

### Workflow 2: Priority Cities Production Run (2-4 hrs)
```bash
# Run overnight
nohup python main_scraper.py priority > scraper_output.log 2>&1 &

# Check progress next morning
tail -f scraper.log
```

### Workflow 3: Continuous Monitoring
```bash
# Run daily/weekly to catch new businesses
0 2 * * 0 cd /home/gamp/Scripts/nexascraper && python main_scraper.py priority
```

---

## 🔗 Dependencies

| Package | Version | Purpose |
| --- | --- | --- |
| `playwright` | 1.40.0 | Browser automation |
| `pandas` | 2.1.3 | Data processing |
| `requests` | 2.31.0 | HTTP requests |
| `beautifulsoup4` | 4.12.2 | HTML parsing |
| `phonenumbers` | 8.13.0 | Phone validation |
| `geopy` | 2.3.0 | Geocoding |

---

## 📞 Support & Contribution

### Common Questions

**Q: Can I include custom sources?**
A: Yes! Extend `BaseScraper` class in `scrapers/base_scraper.py`

**Q: How do I add new industries?**
A: Edit `config/industries.py` and add to `INDUSTRIES` dict

**Q: Can I filter by industry?**
A: Yes! Use pandas: `df[df['industry'] == 'Home & Maintenance']`

---

## 📄 License

[Specify your license here - MIT, Apache 2.0, etc.]

---

## Authors & Contributors

- **Data Engineering Team** - Initial framework
- **Contributions Welcome!** - PRs, issues, suggestions

---

## 🎓 Learning Resources

- Playwright docs: https://playwright.dev/python/
- Async Python: https://docs.python.org/3/library/asyncio.html
- Web scraping best practices: https://en.wikipedia.org/wiki/Web_scraping#Ethics

---

## Changelog

### v1.0.0 (2026-01-15)
- ✅ Initial release
- ✅ 10 industries, 36 states
- ✅ 5 scraper sources
- ✅ Phone/address parsing
- ✅ Async performance

---

**Happy Scraping! 🚀 For Nigerian businesses, by Nigerians.**
