
import asyncio
import logging
from scrapers.base_scraper import GoogleMapsScraper

logging.basicConfig(level=logging.INFO)

async def test_gmaps():
    scraper = GoogleMapsScraper()
    # Set headless to True to run in this environment
    scraper.headless = True
    
    query = {
        'query_text': 'Plumber in Ikeja, Lagos, Nigeria',
        'finder': 'Plumber',
        'lga': 'Ikeja',
        'state': 'Lagos'
    }
    
    print(f"Searching for: {query['query_text']}")
    results = await scraper.search(query)
    
    print(f"Found {len(results)} results")
    for r in results[:3]:
        print(f"- {r['name']} ({r.get('phone', 'No phone')})")

if __name__ == "__main__":
    asyncio.run(test_gmaps())
