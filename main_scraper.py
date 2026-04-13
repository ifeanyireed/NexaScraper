"""
Main Nigerian Business Scraper Orchestrator.

Manages the complete multi-city, multi-industry scraping workflow:
1. Query Generation
2. Batch Processing with Rate Limiting
3. Data Extraction & Cleaning
4. Result Storage
5. Duplicate Detection & Validation
"""

import logging
import json
import asyncio
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NigerianBusinessScraper:
    """Main orchestrator for Nigerian business scraping."""
    
    def __init__(self, output_dir: str = 'data', max_workers: int = 3):
        """
        Initialize scraper.
        
        Args:
            output_dir: Directory to save results
            max_workers: Maximum concurrent scraping tasks
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.max_workers = max_workers
        self.results = []
        self.errors = []
        
        # Import after module initialization
        from utils.query_generator import SearchQueryGenerator, QueryBatcher
        from utils.data_cleaner import DataCleaner, DataDeduplicator
        from scrapers.base_scraper import (
            GoogleMapsScraper, YellowPagesNGScraper,
            BingSearchScraper, BusinessListNGScraper
        )
        from utils.google_sheets_writer import GoogleSheetsIntegration
        
        self.query_generator = SearchQueryGenerator()
        self.query_batcher = QueryBatcher()
        self.data_cleaner = DataCleaner()
        self.deduplicator = DataDeduplicator()
        
        # Initialize Google Sheets (optional)
        try:
            self.sheets_integration = GoogleSheetsIntegration()
            logger.info("✓ Google Sheets integration enabled")
        except Exception as e:
            logger.warning(f"Google Sheets integration disabled: {e}")
            self.sheets_integration = None
        
        self.scrapers = {
            'google_maps': GoogleMapsScraper(),
            'bing_search': BingSearchScraper(),
            'businesslist_ng': BusinessListNGScraper(),
            'yellowpages_ng': YellowPagesNGScraper(),
        }
        
        logger.info("Nigerian Business Scraper initialized")
    
    async def run_full_pipeline(self, mode: str = 'priority'):
        """
        Execute complete scraping pipeline.
        
        Args:
            mode: 'priority' (priority cities), 'full' (all states), or 'test' (sample)
        """
        logger.info(f"Starting scraping pipeline in {mode} mode")
        
        try:
            # Step 1: Generate queries
            logger.info("Step 1: Generating search queries...")
            queries = self._generate_queries(mode)
            logger.info(f"Generated {len(queries)} queries")
            
            # Step 2: Batch and prioritize
            logger.info("Step 2: Batching and prioritizing queries...")
            batches = self.query_batcher.batch_queries(queries, batch_size=10)
            logger.info(f"Organized into {len(batches)} batches")
            
            # Step 3: Execute scraping
            logger.info("Step 3: Executing scraping tasks...")
            await self._execute_scraping(batches)
            
            # Step 4: Clean data
            logger.info("Step 4: Cleaning and standardizing data...")
            self._clean_results()
            
            # Step 5: Deduplicate
            logger.info("Step 5: Deduplicating results...")
            self._deduplicate_results()
            
            # Step 6: Save results
            logger.info("Step 6: Saving results...")
            self._save_results()
            
            # Step 6b: Export to Google Sheets
            if self.sheets_integration:
                logger.info("Step 6b: Exporting to Google Sheets...")
                self._export_to_sheets()
            
            # Step 7: Generate report
            logger.info("Step 7: Generating report...")
            self._generate_report()
            
            logger.info(f"Pipeline complete. Total records: {len(self.results)}")
        
        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            raise
    
    def _generate_queries(self, mode: str) -> List[Dict]:
        """Generate queries based on mode."""
        queries = []
        
        # For test mode: use structured queries with finder/industry/state/LGA
        if mode == 'test':
            platform_queries = self.query_generator.generate_platform_specific_queries()
            # Use 5 Bing queries (different services) + 5 BusinessList queries
            bing_queries = platform_queries.get('bing_search', [])[:5]
            biz_queries = platform_queries.get('businesslist_ng', [])[:5]
            queries.extend(bing_queries)
            queries.extend(biz_queries)
            logger.info(f"Test mode: Using {len(bing_queries)} Bing + {len(biz_queries)} BusinessList structured queries")
        
        # For priority/full: use all sources
        else:
            # Generate Google Maps queries (LGA-based)
            if mode == 'priority':
                gmap_queries = self.query_generator.generate_lga_based_queries(use_priority=True)
            elif mode == 'full':
                gmap_queries = self.query_generator.generate_lga_based_queries(use_priority=False)
            else:
                raise ValueError(f"Unknown mode: {mode}")
            
            # Add platform-specific queries (Bing, BusinessList)
            platform_queries = self.query_generator.generate_platform_specific_queries()
            
            queries.extend(gmap_queries)
            queries.extend(platform_queries.get('bing_search', []))
            queries.extend(platform_queries.get('businesslist_ng', []))
            
            logger.info(f"Generated {len(gmap_queries)} Google Maps, {len(platform_queries.get('bing_search', []))} Bing, {len(platform_queries.get('businesslist_ng', []))} BusinessList queries")
        
        return self.query_batcher.prioritize_queries(queries)
    
    async def _execute_scraping(self, batches: List[List[Dict]]):
        """Execute scraping with rate limiting."""
        for batch_idx, batch in enumerate(batches):
            logger.info(f"Processing batch {batch_idx + 1}/{len(batches)}")
            
            tasks = []
            for query in batch:
                source = query.get('source') or 'google_maps'
                scraper = self.scrapers.get(source)
                
                if scraper:
                    tasks.append(self._scrape_query(scraper, query))
            
            # Run with semaphore to limit concurrency
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Task error: {result}")
                    self.errors.append(str(result))
                else:
                    self.results.extend(result)
            
            # Delay between batches
            await asyncio.sleep(5)
    
    async def _scrape_query(self, scraper, query: Dict) -> List[Dict]:
        """Scrape single query and attach query metadata to results."""
        try:
            query_text = query.get('query_text', '')
            source = query.get('source', 'unknown')
            logger.info(f"Scraping [{source}]: {query_text}")
            results = await scraper.search(query)  # Pass full query dict
            if results:
                logger.info(f"  -> Got {len(results)} results from {source}")
                # Attach query metadata to results
                for result in results:
                    result['finder'] = query.get('finder') or result.get('finder')
                    result['industry'] = query.get('industry') or result.get('industry')
                    result['lga'] = query.get('lga') or result.get('lga')
                    result['state'] = query.get('state') or result.get('state')
            else:
                logger.warning(f"  -> No results from {source}")
            return results
        except Exception as e:
            logger.error(f"Scrape error for {query}: {e}", exc_info=True)
            return []
    
    def _clean_results(self):
        """Clean and standardize results."""
        cleaned_results = []
        
        logger.info(f"Starting to clean {len(self.results)} raw scraper records")
        
        for i, result in enumerate(self.results):
            try:
                cleaned = self.data_cleaner.clean_business_record(result)
                
                # Validate record
                is_valid, errors = self.data_cleaner.validate_business_record(cleaned)
                
                if not is_valid:
                    logger.info(f"Record {i} invalid ({result.get('source','?')}): {result.get('name','?')}, errors: {errors}")
                
                if is_valid:
                    # Check if ghost business
                    if not self.data_cleaner.detect_ghost_business(cleaned):
                        cleaned_results.append(cleaned)
                    else:
                        logger.debug(f"Filtered ghost business: {cleaned.get('name')}")
                else:
                    logger.debug(f"Invalid record: {cleaned.get('name')} - {errors}")
            
            except Exception as e:
                logger.error(f"Error cleaning record: {e}")
        
        self.results = cleaned_results
        logger.info(f"Cleaned to {len(self.results)} valid records")
    
    def _deduplicate_results(self):
        """Remove duplicate records."""
        before_count = len(self.results)
        self.results = self.deduplicator.deduplicate(self.results)
        
        logger.info(f"Deduplicated: {before_count} -> {len(self.results)} records")
    
    def _save_results(self):
        """Save results to multiple formats."""
        if not self.results:
            logger.warning("No results to save")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save as JSON
        json_file = self.output_dir / f"businesses_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved JSON: {json_file}")
        
        # Save as CSV
        csv_file = self.output_dir / f"businesses_{timestamp}.csv"
        df = pd.DataFrame(self.results)
        df.to_csv(csv_file, index=False, encoding='utf-8')
        logger.info(f"Saved CSV: {csv_file}")
        
        # Save as Excel (with formatting)
        try:
            excel_file = self.output_dir / f"businesses_{timestamp}.xlsx"
            df.to_excel(excel_file, index=False, sheet_name='Businesses')
            logger.info(f"Saved Excel: {excel_file}")
        except Exception as e:
            logger.warning(f"Could not save Excel: {e}")
    
    def _export_to_sheets(self):
        """Export results to Google Sheets."""
        if not self.results:
            logger.warning("No results to export to Google Sheets")
            return
        
        try:
            # Option 1: All businesses in single sheet
            self.sheets_integration.writer.write_businesses(
                self.results,
                sheet_name="Businesses"
            )
            
            # Option 2: Create grouped sheets by state (uncomment to enable)
            # self.sheets_integration.export_results(
            #     self.results,
            #     grouped=True,
            #     group_by="state"
            # )
            
            logger.info(f"✓ Successfully exported {len(self.results)} records to Google Sheets")
        
        except Exception as e:
            logger.error(f"Failed to export to Google Sheets: {e}")
    
    
    def _generate_report(self):
        """Generate summary report with service/location segmentation."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"report_{timestamp}.txt"
        
        # Calculate statistics
        states = {}
        industries = {}
        sources = {}
        service_location = {}  # NEW: Group by finder/industry + state/lga
        
        for record in self.results:
            # By state
            state = record.get('state', 'Unknown')
            states[state] = states.get(state, 0) + 1
            
            # By industry
            industry = record.get('industry', 'Unknown')
            industries[industry] = industries.get(industry, 0) + 1
            
            # By source
            source = record.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
            
            # By service + location (NEW)
            finder = record.get('finder', record.get('industry', 'Other Service'))
            lga = record.get('lga', record.get('state', 'Unknown'))
            service_loc_key = f"{finder} in {lga}, {state}".strip()
            if service_loc_key not in service_location:
                service_location[service_loc_key] = []
            service_location[service_loc_key].append(record)
        
        # Generate report
        report = f"""
NIGERIAN BUSINESS SCRAPER REPORT
Generated: {datetime.now().isoformat()}

SUMMARY
=======
Total Records: {len(self.results)}
Total Errors: {len(self.errors)}
Processing Time: [See logs]

RECORDS BY STATE
================
{self._format_dict_report(states)}

RECORDS BY INDUSTRY/SERVICE
============================
{self._format_dict_report(industries)}

RECORDS BY SOURCE
=================
{self._format_dict_report(sources)}

RECORDS BY SERVICE + LOCATION (FOR EASY MANAGEMENT)
===================================================
"""
        for service_loc, records in sorted(service_location.items()):
            report += f"\n{service_loc}: {len(records)} records\n"
            for i, rec in enumerate(records, 1):
                report += f"  {i}. {rec.get('name', 'Unknown')} | Ph: {rec.get('primary_phone', '-')} | Email: {rec.get('primary_email', '-')}\n"
        
        report += f"""

TOP 10 BUSINESSES
=================
"""
        
        for i, record in enumerate(self.results[:10], 1):
            report += f"""
{i}. {record.get('name', 'Unknown')}
   Service: {record.get('finder', record.get('industry', 'N/A'))}
   Location: {record.get('lga', 'N/A')}, {record.get('state', 'N/A')}
   Phone: {record.get('primary_phone', 'N/A')}
   WhatsApp: {record.get('whatsapp', 'N/A')}
   Email: {record.get('primary_email', 'N/A')}
   Website: {record.get('website', 'N/A')}
   Rating: {record.get('rating', 'N/A')} ({record.get('reviews_count', 0)} reviews)
   Source: {record.get('source', 'N/A')}
"""
        
        report += f"""

DATA QUALITY
============
Records with Phone: {sum(1 for r in self.results if r.get('primary_phone'))}
Records with WhatsApp: {sum(1 for r in self.results if r.get('whatsapp'))}
Records with Email: {sum(1 for r in self.results if r.get('primary_email'))}
Records with Website: {sum(1 for r in self.results if r.get('website'))}
Records with Address: {sum(1 for r in self.results if r.get('address'))}
Records with Coordinates: {sum(1 for r in self.results if r.get('latitude') and r.get('longitude'))}
Records with Service Info: {sum(1 for r in self.results if r.get('finder') or r.get('industry'))}
Records with LGA Info: {sum(1 for r in self.results if r.get('lga'))}

CONTACT METHODS BREAKDOWN
=========================
Phone Only: {sum(1 for r in self.results if r.get('primary_phone') and not r.get('primary_email') and not r.get('website'))}
Email Only: {sum(1 for r in self.results if r.get('primary_email') and not r.get('primary_phone'))}
Website Only: {sum(1 for r in self.results if r.get('website') and not r.get('primary_phone') and not r.get('primary_email'))}
Phone + Email: {sum(1 for r in self.results if r.get('primary_phone') and r.get('primary_email'))}
Complete Profile (Phone + Email + Website): {sum(1 for r in self.results if r.get('primary_phone') and r.get('primary_email') and r.get('website'))}

RECOMMENDATIONS
===============
1. Records are now organized by Service + Location for targeted outreach
2. Use LGA for precise geographical targeting
3. Service type enables bulk email templates per industry
4. Prioritize WhatsApp for initial contact
5. Verify ratings and reviews before outreach
6. Use coordinates for route optimization
7. Schedule follow-up scraping for emerging service areas
7. Integrate with CAC database for corporate verification
"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Report saved: {report_file}")
        print(report)
    
    @staticmethod
    def _format_dict_report(data: Dict[str, int]) -> str:
        """Format dictionary for report."""
        lines = []
        for key, value in sorted(data.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {key}: {value}")
        return '\n'.join(lines)


class ScraperConfig:
    """Configuration for scraper behavior."""
    
    PROXY_ROTATION = False  # Set to True with rotating proxy list
    STEALTH_MODE = True  # Use stealth plugins/headers
    HEADLESS_BROWSER = True
    MAX_RETRIES = 3
    TIMEOUT_SECONDS = 30
    DELAY_BETWEEN_REQUESTS = (2, 5)  # seconds


if __name__ == '__main__':
    import sys
    
    # Get mode from command line
    mode = sys.argv[1] if len(sys.argv) > 1 else 'test'
    
    if mode not in ['test', 'priority', 'full']:
        print(f"Invalid mode: {mode}")
        print("Usage: python main_scraper.py [test|priority|full]")
        sys.exit(1)
    
    # Run scraper
    scraper = NigerianBusinessScraper()
    asyncio.run(scraper.run_full_pipeline(mode=mode))
