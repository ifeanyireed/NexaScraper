"""
Google Sheets integration for Nigerian Business Scraper.

Handles writing scraped business data directly to Google Sheets
using service account authentication.
"""

import logging
import os
import json
from typing import List, Dict, Optional
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)


class GoogleSheetsWriter:
    """Write scraper results to Google Sheets."""
    
    SCOPE = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    def __init__(self, sheet_id: str, credentials_path: str):
        """
        Initialize Google Sheets writer.
        
        Args:
            sheet_id: Google Sheet ID (from URL)
            credentials_path: Path to service account JSON file
        """
        self.sheet_id = sheet_id
        self.credentials_path = Path(credentials_path)
        self.client = None
        self.sheet = None
        
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Sheets API."""
        try:
            if not self.credentials_path.exists():
                raise FileNotFoundError(f"Service account file not found: {self.credentials_path}")
            
            creds = Credentials.from_service_account_file(
                str(self.credentials_path),
                scopes=self.SCOPE
            )
            
            self.client = gspread.authorize(creds)
            self.sheet = self.client.open_by_key(self.sheet_id)
            
            logger.info(f"✓ Authenticated with Google Sheets: {self.sheet.title}")
        
        except Exception as e:
            logger.error(f"Google Sheets authentication failed: {e}")
            raise
    
    def create_worksheet(self, sheet_name: str) -> gspread.Worksheet:
        """
        Create or get existing worksheet.
        
        Args:
            sheet_name: Name of worksheet (tab)
            
        Returns:
            Worksheet object
        """
        try:
            # Try to get existing worksheet
            worksheet = self.sheet.worksheet(sheet_name)
            logger.info(f"Using existing worksheet: {sheet_name}")
            return worksheet
        
        except gspread.exceptions.WorksheetNotFound:
            # Create new worksheet
            worksheet = self.sheet.add_worksheet(title=sheet_name, rows=1, cols=1)
            logger.info(f"Created new worksheet: {sheet_name}")
            return worksheet
    
    def write_businesses(self, records: List[Dict], sheet_name: str = "Businesses"):
        """
        Write business records to Google Sheet.
        
        Args:
            records: List of cleaned business records
            sheet_name: Name of worksheet to write to
        """
        if not records:
            logger.warning("No records to write")
            return
        
        try:
            worksheet = self.create_worksheet(sheet_name)
            
            # Get headers from first record
            headers = list(records[0].keys())
            
            # Prepare data: headers + all records
            data = [headers]
            for record in records:
                row = [str(record.get(key, '')) for key in headers]
                data.append(row)
            
            logger.info(f"Writing {len(records)} records to '{sheet_name}'...")
            
            # Clear existing content
            worksheet.clear()
            
            # Write headers + data in batches (API limit: 1M cells)
            batch_size = 1000
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                
                # Determine range
                end_row = i + len(batch)
                end_col = len(headers)
                
                range_label = f"A{i+1}:{self._col_letter(end_col)}{end_row}"
                
                worksheet.update(batch, range_label, raw=False)
                logger.info(f"  Wrote rows {i+1}-{end_row}")
            
            # Format header row
            self._format_header_row(worksheet, len(headers))
            
            logger.info(f"✓ Successfully wrote {len(records)} records to Google Sheets")
        
        except Exception as e:
            logger.error(f"Error writing to Google Sheets: {e}", exc_info=True)
            raise
    
    def write_summary_stats(self, stats: Dict, sheet_name: str = "Summary"):
        """
        Write summary statistics to a separate sheet.
        
        Args:
            stats: Dictionary of statistics
            sheet_name: Name of statistics worksheet
        """
        try:
            worksheet = self.create_worksheet(sheet_name)
            worksheet.clear()
            
            data = [["Metric", "Value"]]
            for key, value in stats.items():
                data.append([str(key), str(value)])
            
            worksheet.update(data)
            self._format_header_row(worksheet, 2)
            
            logger.info(f"✓ Wrote summary stats to '{sheet_name}'")
        
        except Exception as e:
            logger.error(f"Error writing stats: {e}")
    
    def write_grouped_data(self, records: List[Dict], group_by: str = "state"):
        """
        Write business data grouped by field (e.g., by state).
        Creates separate worksheets for each group.
        
        Args:
            records: List of business records
            group_by: Field to group by (state, industry, source)
        """
        # Group records
        grouped = {}
        for record in records:
            key = record.get(group_by, 'Unknown')
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(record)
        
        logger.info(f"Writing {len(grouped)} groups grouped by '{group_by}'...")
        
        for group_name, group_records in grouped.items():
            # Sanitize sheet name (32 char limit, no special chars)
            safe_name = str(group_name)[:30].replace('/', '_').replace('\\', '_')
            
            try:
                self.write_businesses(group_records, sheet_name=safe_name)
            except Exception as e:
                logger.error(f"Error writing group '{group_name}': {e}")
    
    def append_businesses(self, records: List[Dict], sheet_name: str = "Businesses"):
        """
        Append business records to existing sheet (don't overwrite).
        
        Args:
            records: List of new business records
            sheet_name: Name of worksheet to append to
        """
        if not records:
            logger.warning("No records to append")
            return
        
        try:
            worksheet = self.create_worksheet(sheet_name)
            
            # Get existing data to avoid duplicates
            existing = worksheet.get_all_values()
            existing_set = {tuple(row) for row in existing[1:]} if len(existing) > 1 else set()
            
            # Filter new records
            headers = existing[0] if existing else list(records[0].keys())
            
            new_rows = []
            for record in records:
                row = tuple(str(record.get(key, '')) for key in headers)
                if row not in existing_set:
                    new_rows.append(list(row))
            
            if new_rows:
                worksheet.append_rows(new_rows)
                logger.info(f"✓ Appended {len(new_rows)} new records to '{sheet_name}'")
            else:
                logger.info(f"No new records to append (all exist)")
        
        except Exception as e:
            logger.error(f"Error appending to Google Sheets: {e}")
            raise
    
    def _format_header_row(self, worksheet: gspread.Worksheet, num_cols: int):
        """Format header row with bold + background color."""
        try:
            # Make header row bold and set background
            header_format = {
                "textFormat": {"bold": True},
                "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2},
                "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}}
            }
            
            # Format header cells
            worksheet.format(f"A1:{self._col_letter(num_cols)}1", header_format)
            
            # Auto-resize columns (approximately)
            worksheet.update_title(worksheet.title)  # Refresh
        
        except Exception as e:
            logger.debug(f"Could not format header: {e}")
    
    @staticmethod
    def _col_letter(col_num: int) -> str:
        """Convert column number to letter (1 -> A, 27 -> AA)."""
        result = ""
        while col_num > 0:
            col_num -= 1
            result = chr(65 + (col_num % 26)) + result
            col_num //= 26
        return result


class GoogleSheetsIntegration:
    """High-level integration for scraper."""
    
    def __init__(self):
        """Initialize from environment variables."""
        sheet_id = os.getenv('SHEET_ID')
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', './secure_keys/my-service-account.json')
        
        if not sheet_id:
            raise ValueError("SHEET_ID not set in .env")
        
        self.writer = GoogleSheetsWriter(sheet_id, creds_path)
    
    def export_results(self, results: List[Dict], grouped: bool = False, group_by: str = "state"):
        """
        Export scraper results to Google Sheets.
        
        Args:
            results: List of scraped business records
            grouped: Whether to create separate sheets per group
            group_by: Field to group by if grouped=True
        """
        if not results:
            logger.warning("No results to export")
            return
        
        if grouped:
            self.writer.write_grouped_data(results, group_by=group_by)
        else:
            self.writer.write_businesses(results, sheet_name="Businesses")
        
        # Generate and write summary
        stats = self._generate_stats(results)
        self.writer.write_summary_stats(stats)
    
    @staticmethod
    def _generate_stats(records: List[Dict]) -> Dict:
        """Generate summary statistics."""
        stats = {
            "Total Records": len(records),
            "Records with Phone": sum(1 for r in records if r.get('primary_phone')),
            "Records with WhatsApp": sum(1 for r in records if r.get('whatsapp')),
            "Records with Email": sum(1 for r in records if r.get('primary_email')),
            "Records with Website": sum(1 for r in records if r.get('website')),
            "Records with Address": sum(1 for r in records if r.get('address')),
            "Records with Coordinates": sum(1 for r in records if r.get('latitude') and r.get('longitude')),
            "Unique States": len(set(r.get('state') for r in records if r.get('state'))),
            "Unique Industries": len(set(r.get('industry') for r in records if r.get('industry'))),
            "Average Rating": f"{sum(float(r.get('rating', 0)) for r in records) / max(1, len(records)):.2f}",
        }
        return stats
