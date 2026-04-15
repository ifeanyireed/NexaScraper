"""
Search Query Generator for Nigerian Business Scraper.

Generates multi-permutation search queries combining:
- 10 core industries
- Nigerian states/LGAs
- Search modifiers for nuanced results
"""

from typing import List, Dict, Tuple
from itertools import product
import logging

logger = logging.getLogger(__name__)


class SearchQueryGenerator:
    """Generates targeted search queries for different platforms."""
    
    def __init__(self):
        from config.industries import INDUSTRIES, SCRAPER_SOURCES
        from config.locations import NIGERIAN_LOCATIONS, PRIORITY_CITIES, SEARCH_MODIFIERS
        
        self.industries = INDUSTRIES
        self.sources = SCRAPER_SOURCES
        self.locations = NIGERIAN_LOCATIONS
        self.priority_cities = PRIORITY_CITIES
        self.search_modifiers = SEARCH_MODIFIERS
    
    def get_all_finders(self) -> List[str]:
        """Extract all individual service types from industries."""
        finders = []
        for industry, categories in self.industries.items():
            for category, services in categories.items():
                finders.extend(services)
        return list(set(finders))  # Deduplicate
    
    def get_all_locations(self) -> List[Tuple[str, str]]:
        """
        Get all (state, lga) tuples from Nigerian locations.
        
        Returns: List of (state, lga) tuples
        """
        locations = []
        for state, data in self.locations.items():
            for lga in data['lgas']:
                locations.append((state, lga))
        return locations
    
    def get_priority_locations(self) -> List[Tuple[str, str]]:
        """Get LGAs from priority cities only."""
        locations = []
        for state in self.priority_cities:
            if state in self.locations:
                for lga in self.locations[state]['lgas'][:5]:  # Top 5 LGAs per priority city
                    locations.append((state, lga))
        return locations
    
    def generate_lga_based_queries(self, use_priority: bool = True) -> List[Dict]:
        """
        Generate LGA-specific queries for maximum granularity.
        
        Format: "[Service Keyword] in [LGA], [State], Nigeria"
        Example: "Solar Installer in Ikeja, Lagos, Nigeria"
        """
        queries = []
        
        finders = self.get_all_finders()
        locations = self.get_priority_locations() if use_priority else self.get_all_locations()
        
        for finder, (state, lga) in product(finders, locations):
            query = {
                'query_text': f"{finder} in {lga}, {state}, Nigeria",
                'finder': finder,
                'lga': lga,
                'state': state,
                'query_type': 'lga_based',
                'source': None,  # Will be assigned per source
            }
            queries.append(query)
        
        logger.info(f"Generated {len(queries)} LGA-based queries")
        return queries
    
    def generate_city_based_queries(self) -> List[Dict]:
        """
        Generate city-level queries for broader coverage.
        
        Format: "[Service Keyword] [City], Nigeria"
        Example: "Plumber Lagos, Nigeria"
        """
        queries = []
        finders = self.get_all_finders()
        
        for finder, city in product(finders, self.priority_cities):
            query = {
                'query_text': f"{finder} {city}, Nigeria",
                'finder': finder,
                'city': city,
                'query_type': 'city_based',
                'source': None,
            }
            queries.append(query)
        
        logger.info(f"Generated {len(queries)} city-based queries")
        return queries
    
    def generate_platform_specific_queries(self, use_priority: bool = True) -> Dict[str, List[Dict]]:
        """
        Generate platform-specific queries optimized for each scraper source.
        """
        platform_queries = {}
        
        # Get locations based on priority flag
        locations = self.get_priority_locations() if use_priority else self.get_all_locations()
        
        # Google Maps queries
        gmaps_queries = self.generate_lga_based_queries(use_priority=use_priority)
        platform_queries['google_maps'] = gmaps_queries
        
        # Bing Search queries (web results with emails/websites)
        bing_queries = []
        
        # Limit finders for platform specific to keep it manageable if not in priority mode
        max_finders = 20 if use_priority else 50
        
        finders_sample = self.get_all_finders()[:max_finders]
        
        for finder in finders_sample:
            for state, lga in locations:
                query = {
                    'query_text': f"{finder} in {lga}, {state} Nigeria contact",
                    'finder': finder,
                    'lga': lga,
                    'state': state,
                    'query_type': 'web_search',
                    'source': 'bing_search',
                }
                bing_queries.append(query)
        platform_queries['bing_search'] = bing_queries
        
        # Facebook queries
        facebook_queries = []
        for finder in finders_sample:
            for state, lga in locations:
                query = {
                    'query_text': f"{finder} in {lga}, {state} Nigeria",
                    'finder': finder,
                    'lga': lga,
                    'state': state,
                    'query_type': 'social_discovery',
                    'source': 'facebook',
                }
                facebook_queries.append(query)
        platform_queries['facebook'] = facebook_queries

        # Instagram queries
        instagram_queries = []
        for finder in finders_sample:
            for state, lga in locations:
                query = {
                    'query_text': f"{finder} in {lga}, {state} Nigeria",
                    'finder': finder,
                    'lga': lga,
                    'state': state,
                    'query_type': 'social_discovery',
                    'source': 'instagram',
                }
                instagram_queries.append(query)
        platform_queries['instagram'] = instagram_queries
        
        # BusinessList.com.ng queries (Nigerian directory)
        businesslist_queries = []
        max_industries = 5 if use_priority else 15
        for industry in list(self.industries.keys())[:max_industries]:
            for state, lga in locations:
                query = {
                    'query_text': f"{industry} in {lga}, {state}",
                    'industry': industry,
                    'lga': lga,
                    'state': state,
                    'query_type': 'directory_search',
                    'source': 'businesslist_ng',
                }
                businesslist_queries.append(query)
        platform_queries['businesslist_ng'] = businesslist_queries
        
        # YellowPages NG queries
        yellowpages_queries = []
        for industry in list(self.industries.keys())[:max_industries]:
            for state, lga in locations:
                query = {
                    'query_text': f"{industry} in {lga}, {state}",
                    'industry': industry,
                    'lga': lga,
                    'state': state,
                    'query_type': 'industry_lga',
                    'source': 'yellowpages_ng',
                }
                yellowpages_queries.append(query)
        platform_queries['yellowpages_ng'] = yellowpages_queries
        
        return platform_queries
    
    def generate_instagram_hashtag_queries(self) -> List[Dict]:
        """
        Generate Instagram hashtag queries for visual service finders.
        """
        hashtag_queries = []
        
        visual_services = {
            'makeup': ['makeupng', 'makeupartistnigeria', 'nigerianmakeupartist'],
            'tailor': ['tailornigeria', 'customtailoring', 'bespoquetailor'],
            'photographer': ['nigerianphotographer', 'weddingphotographer', 'portraitphotography'],
            'videographer': ['videographernigeria', 'weddingvideography'],
            'dj': ['djnigeria', 'nightlifedj'],
            'event_planner': ['eventplannerlagos', 'nigerianweddingplanner'],
            'jewelry': ['jewelerynigeria', 'customjewelry'],
            'fashion': ['fashiondesignernigeria', 'designernigeria', 'clothesnigeria'],
        }
        
        for service, hashtags in hashtag_services.items():
            for hashtag in hashtags:
                query = {
                    'query_text': f"#{hashtag}",
                    'service': service,
                    'query_type': 'instagram_hashtag',
                    'source': 'instagram',
                }
                hashtag_queries.append(query)
        
        return hashtag_queries
    
    def generate_cac_verification_queries(self) -> List[Dict]:
        """
        Generate CAC (Corporate Affairs Commission) database queries
        for verifying professional/corporate service providers.
        """
        cac_queries = []
        
        corporate_finders = [
            'Lawyer', 'Accountant', 'Tax Consultant', 'Business Consultant',
            'Architect', 'Estate Agent', 'Web Developer'
        ]
        
        for state in self.priority_cities:
            for finder in corporate_finders:
                query = {
                    'query_text': f"{finder} {state}",
                    'finder': finder,
                    'state': state,
                    'query_type': 'cac_verification',
                    'source': 'cac',
                }
                cac_queries.append(query)
        
        return cac_queries
    
    def generate_mixed_queries_with_contacts(self) -> List[Dict]:
        """
        Generate queries specifically targeting contact information.
        Adds contact keywords like "WhatsApp", "phone", "call".
        """
        mixed_queries = []
        base_queries = self.generate_lga_based_queries(use_priority=True)[:100]  # Sample
        
        contact_keywords = ['WhatsApp', 'phone', 'contact', 'call', 'number']
        
        for base_query in base_queries:
            # Original query
            mixed_queries.append(base_query)
            
            # With contact keyword
            for keyword in contact_keywords:
                contact_query = base_query.copy()
                contact_query['query_text'] = f"{base_query['query_text']} {keyword}"
                contact_query['contact_focused'] = True
                mixed_queries.append(contact_query)
        
        return mixed_queries
    
    def estimate_total_queries(self) -> Dict[str, int]:
        """Estimate total queries for all strategies."""
        return {
            'lga_based': len(self.get_all_finders()) * len(self.get_priority_locations()),
            'city_based': len(self.get_all_finders()) * len(self.priority_cities),
            'bing_search': 50 * len(self.priority_cities),  # Top 50 finders per city
            'businesslist': len(self.industries) * len(self.priority_cities),
            'platform_specific': len(self.industries) * len(self.priority_cities),
            'instagram_hashtags': 50,  # Approximate
            'cac_queries': len(self.priority_cities) * 7,  # ~7 corporate finders
        }


class QueryBatcher:
    """Batch queries for efficient parallel processing."""
    
    @staticmethod
    def batch_queries(queries: List[Dict], batch_size: int = 10) -> List[List[Dict]]:
        """Split queries into manageable batches."""
        batches = []
        for i in range(0, len(queries), batch_size):
            batches.append(queries[i:i + batch_size])
        return batches
    
    @staticmethod
    def prioritize_queries(queries: List[Dict]) -> List[Dict]:
        """
        Prioritize queries by:
        1. Priority cities first
        2. High-demand services first
        3. LGA-based before city-based
        """
        from config.locations import PRIORITY_CITIES
        
        priority_order = {
            'lga_based': 1,
            'city_based': 2,
            'industry_state': 3,
            'instagram_hashtag': 4,
            'cac_verification': 5,
        }
        
        # Sort by query type priority
        queries.sort(key=lambda q: priority_order.get(q.get('query_type'), 999))
        
        # Secondary sort: priority cities first
        queries.sort(key=lambda q: (
            0 if q.get('state') in PRIORITY_CITIES else 1,
            q.get('query_text', '')
        ))
        
        return queries
