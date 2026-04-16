"""
Main Nigerian Business Scraper Orchestrator.

Manages the complete multi-city, multi-industry scraping workflow:
1. Query Generation
2. Segment-based Processing (one service/lga per time)
3. Data Extraction & Cleaning
4. Sequential Google Sheets Writing
5. Duplicate Detection & Validation
"""

import logging
import json
import asyncio
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set
import sys
import os
from collections import defaultdict
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
        self.seen_signatures: Set[tuple] = set()  # Track duplicates across segments
        
        # Import after module initialization
        from utils.query_generator import SearchQueryGenerator, QueryBatcher
        from utils.data_cleaner import DataCleaner, DataDeduplicator
        from scrapers.base_scraper import (
            GoogleMapsScraper, YellowPagesNGScraper,
            BingSearchScraper, BusinessListNGScraper,
            InstagramScraper, FacebookScraper
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
            'instagram': InstagramScraper(),
            'facebook': FacebookScraper(),
        }
        
        logger.info("Nigerian Business Scraper initialized")
    
    async def run_full_pipeline(self, mode: str = 'priority', states: Optional[List[str]] = None):
        """
        Execute complete scraping pipeline in segments.
        
        Args:
            mode: 'priority', 'full', or 'test'
            states: Optional list of states to filter by
        """
        logger.info(f"Starting segment-based scraping pipeline in {mode} mode")
        if states:
            logger.info(f"Filtering for states: {', '.join(states)}")
        
        try:
            # Step 1: Generate queries
            logger.info("Step 1: Generating search queries...")
            queries = self._generate_queries(mode)
            
            # Filter by state if requested
            if states:
                queries = [q for q in queries if q.get('state') in states]
            
            logger.info(f"Generated {len(queries)} total queries after filtering")
            
            # Step 2: Group queries into segments (service/location)
            logger.info("Step 2: Grouping queries into segments...")
            segments = self._group_queries_by_segment(queries)
            logger.info(f"Organized into {len(segments)} segments")
            
            # Step 3: Process segments sequentially
            logger.info("Step 3: Processing segments sequentially...")
            processed_count = 0
            total_segments = len(segments)
            
            for i, (segment_key, segment_queries) in enumerate(segments.items(), 1):
                service, location = segment_key
                logger.info(f"--- Segment {i}/{total_segments} ({i/total_segments*100:.1f}%): {service} in {location} ---")
                
                try:
                    # A. Scrape queries in this segment
                    segment_results = await self._execute_segment_scraping(segment_queries)
                    
                    if not segment_results:
                        logger.info(f"No results for segment: {service} in {location}")
                        continue
                    
                    # B. Clean segment data
                    cleaned_segment = self._clean_segment_results(segment_results)
                    
                    # C. Deduplicate within segment and against global seen list
                    new_records = self._deduplicate_segment(cleaned_segment)
                    
                    if new_records:
                        logger.info(f"Found {len(new_records)} new unique records in this segment")
                        
                        # D. Add to main results
                        self.results.extend(new_records)
                        
                        # E. Write sequentially to Google Sheets
                        if self.sheets_integration:
                            self._append_to_sheets(new_records)
                        
                        # F. Save local incremental backup
                        self._save_incremental_backup()
                    
                    processed_count += 1
                    
                except Exception as segment_error:
                    logger.error(f"Error processing segment {segment_key}: {segment_error}")
                    continue

                # Small delay between segments to respect rate limits
                await asyncio.sleep(2)
            
            # Step 4: Final save of all results
            logger.info("Step 4: Saving final compiled results...")
            self._save_results()
            
            # Final Google Sheets Export (with summary stats)
            if self.sheets_integration:
                try:
                    logger.info("Exporting final results and summary to Google Sheets...")
                    self.sheets_integration.export_results(self.results)
                except Exception as e:
                    logger.warning(f"Final Google Sheets export failed: {e}")
            
            # Step 5: Generate report
            logger.info("Step 5: Generating final report...")
            self._generate_report()
            
            logger.info(f"Pipeline complete. Total unique records: {len(self.results)}")
        
        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            raise

    def _save_incremental_backup(self):
        """Save a temporary backup of results found so far."""
        if len(self.results) % 50 == 0: # Every 50 new records
            try:
                temp_file = self.output_dir / "latest_backup.csv"
                df = pd.DataFrame(self.results)
                df.to_csv(temp_file, index=False)
                logger.info(f"Incremental backup saved: {len(self.results)} records")
            except Exception as e:
                logger.warning(f"Backup failed: {e}")

    def _group_queries_by_segment(self, queries: List[Dict]) -> Dict[tuple, List[Dict]]:
        """Group queries by (service, LGA) tuple."""
        segments = defaultdict(list)
        for q in queries:
            service = q.get('finder') or q.get('industry') or 'Unknown Service'
            # Strictly use LGA for segmentation as requested
            lga = q.get('lga') or 'Unknown LGA'
            segments[(service, lga)].append(q)
        return segments

    async def _execute_segment_scraping(self, segment_queries: List[Dict]) -> List[Dict]:
        """Execute all queries for a single segment."""
        tasks = []
        for query in segment_queries:
            source = query.get('source') or 'google_maps'
            scraper = self.scrapers.get(source)
            if scraper:
                tasks.append(self._scrape_query(scraper, query))
        
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
        
        combined_results = []
        for res in results_lists:
            if isinstance(res, Exception):
                logger.error(f"Segment task error: {res}")
                self.errors.append(str(res))
            elif res:
                combined_results.extend(res)
        return combined_results

    def _clean_segment_results(self, raw_results: List[Dict]) -> List[Dict]:
        """Clean results from a single segment."""
        cleaned_results = []
        for res in raw_results:
            try:
                cleaned = self.data_cleaner.clean_business_record(res)
                is_valid, _ = self.data_cleaner.validate_business_record(cleaned)
                if is_valid and not self.data_cleaner.detect_ghost_business(cleaned):
                    cleaned_results.append(cleaned)
            except Exception as e:
                logger.error(f"Error cleaning record in segment: {e}")
        return cleaned_results

    def _deduplicate_segment(self, cleaned_results: List[Dict]) -> List[Dict]:
        """Deduplicate results within segment and against already seen businesses."""
        new_records = []
        for record in cleaned_results:
            # Create signature: (name.lower, primary_phone or address)
            name = record.get('name', '').lower().strip()
            contact = record.get('primary_phone') or record.get('address', '')
            signature = (name, contact)
            
            if signature not in self.seen_signatures:
                self.seen_signatures.add(signature)
                new_records.append(record)
        return new_records

    def _append_to_sheets(self, records: List[Dict]):
        """Append records to Google Sheets sequentially."""
        try:
            self.sheets_integration.writer.append_businesses(
                records,
                sheet_name="Businesses"
            )
            logger.info(f"✓ Appended {len(records)} records to Google Sheets")
        except Exception as e:
            logger.error(f"Failed to append to Google Sheets: {e}")

    def _generate_queries(self, mode: str) -> List[Dict]:
        """Generate queries based on mode."""
        queries = []
        
        # For test mode: use a small sample from ALL sources for verification
        if mode == 'test':
            logger.info("Test mode: Sampling all enabled sources for verification...")
            platform_queries = self.query_generator.generate_platform_specific_queries(use_priority=True)
            
            # Take 2 samples from every available source
            for source, source_queries in platform_queries.items():
                if source_queries:
                    sample = source_queries[:2]
                    for q in sample:
                        q['source'] = source # Ensure source is set
                    queries.extend(sample)
                    logger.info(f"  + Added 2 sample queries for source: {source}")
            
            logger.info(f"Test mode initialized with {len(queries)} sample queries across all platforms")
        
        # For priority/full: use all sources
        else:
            # Generate Google Maps queries (LGA-based)
            if mode == 'priority':
                gmap_queries = self.query_generator.generate_lga_based_queries(use_priority=True)
            elif mode == 'full':
                gmap_queries = self.query_generator.generate_lga_based_queries(use_priority=False)
            else:
                raise ValueError(f"Unknown mode: {mode}")
            
            # Add platform-specific queries (Bing, BusinessList, Social, etc.)
            platform_queries = self.query_generator.generate_platform_specific_queries(use_priority=(mode == 'priority'))
            
            queries.extend(gmap_queries)
            for source, source_queries in platform_queries.items():
                if source != 'google_maps': # Already added gmap LGA queries
                    queries.extend(source_queries)
            
            logger.info(f"Generated {len(queries)} total multi-platform queries")
        
        return self.query_batcher.prioritize_queries(queries)
    
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


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Nigerian Business Scraper')
    parser.add_argument('mode', choices=['test', 'priority', 'full'], help='Scraping mode')
    parser.add_argument('--states', nargs='+', help='Specific states to scrape (e.g., Lagos "Oyo State")')
    parser.add_argument('--max-workers', type=int, default=3, help='Max concurrent scrapers')
    
    args = parser.parse_args()
    
    # Run scraper
    scraper = NigerianBusinessScraper(max_workers=args.max_workers)
    
    try:
        asyncio.run(scraper.run_full_pipeline(mode=args.mode, states=args.states))
    except KeyboardInterrupt:
        print("\nScraper stopped by user. Final results saved to incremental backups.")
    except Exception as e:
        print(f"\nScraper failed: {e}")
