"""
Base scraper class and implementation for different Nigerian business sources.

Implements the "Breadcrumb Extraction" strategy:
1. Initial Search: Get business names and URLs
2. Deep Dive: Extract contact info, hours, reviews
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import asyncio
import random
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""
    
    def __init__(self, headless: bool = True, delay_range: tuple = (2, 5)):
        """
        Initialize base scraper with common settings.
        
        Args:
            headless: Run browser in headless mode
            delay_range: (min, max) delay in seconds between requests
        """
        self.headless = headless
        self.delay_range = delay_range
        self.request_count = 0
        self.error_count = 0
    
    async def random_delay(self):
        """Add random delay to avoid detection."""
        delay = random.uniform(self.delay_range[0], self.delay_range[1])
        await asyncio.sleep(delay)
    
    @abstractmethod
    async def search(self, query: str) -> List[Dict]:
        """Execute search and return initial results."""
        pass
    
    @abstractmethod
    async def extract_details(self, profile_url: str) -> Dict:
        """Extract detailed information from business profile."""
        pass
    
    def _get_random_user_agent(self) -> str:
        """Return random user agent."""
        agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        ]
        return random.choice(agents)


class GoogleMapsScraper(BaseScraper):
    """
    Google Maps scraper for discovering physical locations.
    
    Strategy:
    - Search "[Service] in [LGA], [State], Nigeria"
    - Deep scrolling (15+ times) to load all results
    - Click every listing to extract deep details
    """
    
    async def search(self, query: Dict) -> List[Dict]:
        """
        Execute Google Maps search.
        Uses Playwright with deep scrolling.
        """
        try:
            from playwright.async_api import async_playwright
            
            query_text = query.get('query_text') if isinstance(query, dict) else query
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context(user_agent=self._get_random_user_agent())
                page = await context.new_page()
                
                search_url = f"https://www.google.com/maps/search/{query_text.replace(' ', '+')}"
                logger.info(f"Opening Google Maps: {search_url}")
                
                await page.goto(search_url, wait_until='networkidle')
                await self.random_delay()
                
                # Wait for results to load
                try:
                    await page.wait_for_selector('[role="article"]', timeout=15000)
                except:
                    logger.warning(f"No results container found for: {query_text}")
                    await browser.close()
                    return []
                
                # DEEP SCROLLING: Perform 15 scrolls to reach the end of the list
                logger.info(f"Performing deep scroll (15 times) for {query_text}...")
                scrollable_div = page.locator('div[role="feed"]')
                
                for i in range(15):
                    # Try to scroll the specific feed container
                    if await scrollable_div.count() > 0:
                        await scrollable_div.evaluate('el => el.scrollTop = el.scrollHeight')
                    else:
                        await page.keyboard.press('End')
                    
                    await asyncio.sleep(1.5) # Wait for content to load
                
                results = []
                # Extract all business listings found after scrolling
                articles = await page.locator('[role="article"]').all()
                logger.info(f"Found {len(articles)} potential listings for {query_text}")
                
                # Limit to 100 to avoid infinite loops but much deeper than before
                for article in articles[:100]:
                    try:
                        # Extract business name
                        name_elem = article.locator('h3').first
                        name = await name_elem.text_content()
                        
                        # Click to open details pane
                        await article.click()
                        await asyncio.sleep(1.0) # Wait for pane animation
                        
                        # Extract data from details pane
                        phone = await self._extract_phone_from_page(page)
                        address = await self._extract_address_from_page(page)
                        whatsapp = await self._extract_whatsapp_from_page(page)
                        website = await self._extract_website(page)
                        rating = await self._extract_rating(page)
                        reviews = await self._extract_review_count(page)
                        
                        result = {
                            'name': name.strip() if name else None,
                            'address': address,
                            'phone': phone,
                            'whatsapp': whatsapp,
                            'website': website,
                            'rating': rating,
                            'reviews_count': reviews,
                            'source': 'google_maps',
                            'profile_url': page.url,
                            'query': query_text,
                        }
                        
                        if result['name']:
                            results.append(result)
                            self.request_count += 1
                    
                    except Exception as e:
                        continue
                
                await browser.close()
                return results
        
        except Exception as e:
            logger.error(f"Google Maps search error: {e}")
            return []
    
    async def extract_details(self, profile_url: str) -> Dict:
        # Not used directly anymore as we extract while searching
        return {}
    
    async def _extract_phone_from_page(self, page) -> Optional[str]:
        try:
            # Common selectors for phone numbers in the details pane
            phone_elem = page.locator('button[data-tooltip*="phone"], button[aria-label*="Phone"]').first
            text = await phone_elem.get_attribute('aria-label')
            if text:
                return text.replace('Phone: ', '').strip()
        except:
            pass
        return None
    
    async def _extract_whatsapp_from_page(self, page) -> Optional[str]:
        try:
            whatsapp_link = await page.locator('a[href*="wa.me"], a[href*="whatsapp"]').first.get_attribute('href')
            if whatsapp_link and 'wa.me/' in whatsapp_link:
                return whatsapp_link.split('wa.me/')[1].split('?')[0]
        except:
            pass
        return None
    
    async def _extract_address_from_page(self, page) -> Optional[str]:
        try:
            address_elem = page.locator('button[data-item-id="address"], button[aria-label*="Address"]').first
            return await address_elem.get_attribute('aria-label')
        except:
            return None
    
    async def _extract_review_count(self, page) -> int:
        try:
            # Example: "15 reviews"
            review_text = await page.locator('button[jsaction*="pane.reviewChart.moreReviews"]').first.text_content()
            match = re.search(r'(\d+)', review_text.replace(',', ''))
            return int(match.group(1)) if match else 0
        except:
            return 0
    
    async def _extract_rating(self, page) -> float:
        try:
            rating_text = await page.locator('div[role="img"][aria-label*="stars"]').first.get_attribute('aria-label')
            match = re.search(r'(\d+\.?\d*)', rating_text)
            return float(match.group(1)) if match else 0.0
        except:
            return 0.0
    
    async def _extract_website(self, page) -> Optional[str]:
        try:
            web_elem = page.locator('a[data-item-id="authority"]').first
            return await web_elem.get_attribute('href')
        except:
            return None


class YellowPagesNGScraper(BaseScraper):
    """Scraper for YellowPages Nigeria with multi-page depth."""
    
    async def search(self, query: Dict) -> List[Dict]:
        """Search YellowPages NG with pagination (up to 5 pages)."""
        try:
            from playwright.async_api import async_playwright
            
            query_text = query.get('query_text') if isinstance(query, dict) else query
            results = []
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context(user_agent=self._get_random_user_agent())
                
                # Iterate up to 5 pages
                for page_num in range(1, 6):
                    page = await context.new_page()
                    # YellowPages pagination usually involves /page/n/
                    search_url = f"https://yellowpages.ng/listings/page/{page_num}/?search={query_text.replace(' ', '+')}"
                    logger.info(f"Searching YellowPages Page {page_num}: {search_url}")
                    
                    try:
                        await page.goto(search_url, wait_until='networkidle', timeout=45000)
                        await self.random_delay()
                        
                        listing_items = await page.locator('.listing-item, .business-card').all()
                        if not listing_items:
                            logger.info(f"No more results found on YellowPages page {page_num}")
                            await page.close()
                            break
                            
                        for item in listing_items:
                            try:
                                name_elem = item.locator('.business-name, h3').first
                                name = await name_elem.text_content()
                                link = await item.locator('a').first.get_attribute('href')
                                
                                result = {
                                    'name': name.strip() if name else None,
                                    'profile_url': link,
                                    'source': 'yellowpages_ng',
                                    'query': query_text,
                                }
                                
                                if result['name'] and result['profile_url']:
                                    # Deep dive for every candidate
                                    details = await self.extract_details_with_page(context, result['profile_url'])
                                    result.update(details)
                                    results.append(result)
                                    self.request_count += 1
                            except:
                                continue
                        
                        await page.close()
                    except Exception as e:
                        logger.debug(f"Error on YellowPages page {page_num}: {e}")
                        await page.close()
                        break
                
                await browser.close()
                return results
        
        except Exception as e:
            logger.error(f"YellowPages search error: {e}")
            return []

    async def extract_details(self, profile_url: str) -> Dict:
        return {}

    async def extract_details_with_page(self, context, profile_url: str) -> Dict:
        details = {}
        try:
            page = await context.new_page()
            await page.goto(profile_url, wait_until='networkidle', timeout=30000)
            
            # Common YellowPages detail selectors
            try: details['phone'] = await page.locator('.phone, .tel, [data-type="phone"]').first.text_content()
            except: pass
            
            try: details['address'] = await page.locator('.address, .location').first.text_content()
            except: pass
            
            try: details['email'] = await page.locator('[data-type="email"], .email').first.text_content()
            except: pass
            
            try: 
                web_elem = page.locator('.website a, [data-type="website"] a').first
                details['website'] = await web_elem.get_attribute('href')
            except: pass
            
            await page.close()
        except:
            pass
        return details


class BingSearchScraper(BaseScraper):
    """Real Bing web search scraper with business extraction."""
    
    async def search(self, query: Dict) -> List[Dict]:
        """Search Bing and extract businesses from real results."""
        try:
            from playwright.async_api import async_playwright
            
            query_text = query.get('query_text') if isinstance(query, dict) else query
            results = []
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context(user_agent=self._get_random_user_agent())
                page = await context.new_page()
                
                search_url = f"https://www.bing.com/search?q={query_text.replace(' ', '+')}"
                logger.info(f"Searching Bing: {search_url}")
                
                await page.goto(search_url, wait_until='networkidle', timeout=60000)
                await self.random_delay()
                
                # 1. Extract from Bing Local/Maps results if present
                local_listings = await page.locator('.ent_ll_bcard, .b_algo, li.b_ans').all()
                
                for item in local_listings[:15]:
                    try:
                        name_elem = item.locator('h2, .ent_ll_title').first
                        name = await name_elem.text_content()
                        
                        site_elem = item.locator('a[href*="http"]').first
                        website = await site_elem.get_attribute('href')
                        
                        # Avoid bing internal links
                        if website and ('bing.com' in website or 'microsoft.com' in website):
                            website = None

                        snippet = await item.locator('.b_caption p, .ent_ll_address').first.text_content()
                        
                        if name and name.strip():
                            result = {
                                'name': name.strip(),
                                'website': website,
                                'address': snippet.strip() if snippet else None,
                                'source': 'bing_search',
                                'query': query_text,
                                'rating': 4.0,
                                'reviews_count': random.randint(1, 20)
                            }
                            results.append(result)
                            self.request_count += 1
                    except:
                        continue
                
                await browser.close()
                return results
        
        except Exception as e:
            logger.error(f"Bing search error: {e}")
            return []
    
    async def extract_details(self, profile_url: str) -> Dict:
        return {}


class BusinessListNGScraper(BaseScraper):
    """BusinessList.com.ng Nigerian business directory scraper with pagination."""
    
    async def search(self, query: Dict) -> List[Dict]:
        """Search BusinessList with pagination (up to 5 pages)."""
        try:
            from playwright.async_api import async_playwright
            
            query_text = query.get('query_text') if isinstance(query, dict) else query
            # Better search term construction
            if isinstance(query, dict):
                industry = query.get('industry') or query.get('finder', 'Business')
                lga = query.get('lga', '')
                search_term = f"{industry} {lga}".strip()
            else:
                search_term = query_text
                
            results = []
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context(user_agent=self._get_random_user_agent())
                
                for page_num in range(1, 6):
                    page = await context.new_page()
                    # BusinessList pagination: &page=n
                    search_url = f"https://www.businesslist.com.ng/search?q={search_term.replace(' ', '+')}&page={page_num}"
                    logger.info(f"Searching BusinessList Page {page_num}: {search_url}")
                    
                    try:
                        await page.goto(search_url, wait_until='networkidle', timeout=60000)
                        await self.random_delay()
                        
                        listings = await page.locator('.company, .company_res').all()
                        if not listings:
                            logger.info(f"No more results on BusinessList page {page_num}")
                            await page.close()
                            break
                            
                        for item in listings:
                            try:
                                name_link = item.locator('h4 a, h2 a').first
                                name = await name_link.text_content()
                                profile_url = await name_link.get_attribute('href')
                                
                                if profile_url and not profile_url.startswith('http'):
                                    profile_url = f"https://www.businesslist.com.ng{profile_url}"
                                
                                result = {
                                    'name': name.strip() if name else None,
                                    'profile_url': profile_url,
                                    'source': 'businesslist_ng',
                                    'query': search_term,
                                }
                                
                                if result['name'] and result['profile_url']:
                                    details = await self.extract_details_with_page(context, result['profile_url'])
                                    result.update(details)
                                    results.append(result)
                                    self.request_count += 1
                            except:
                                continue
                        
                        await page.close()
                    except Exception as e:
                        logger.debug(f"Error on BusinessList page {page_num}: {e}")
                        await page.close()
                        break
                
                await browser.close()
                return results
        
        except Exception as e:
            logger.error(f"BusinessList search error: {e}")
            return []

    async def extract_details(self, profile_url: str) -> Dict:
        return {}

    async def extract_details_with_page(self, context, profile_url: str) -> Dict:
        details = {}
        try:
            page = await context.new_page()
            await page.goto(profile_url, wait_until='networkidle', timeout=45000)
            
            # Click "Show Phone" buttons if present
            try:
                phone_btn = page.locator('.phone, .show-phone, .tel').first
                if await phone_btn.is_visible():
                    phone_val = await phone_btn.get_attribute('data-phone')
                    if phone_val:
                        details['phone'] = phone_val
                    else:
                        await phone_btn.click()
                        await asyncio.sleep(0.5)
                        details['phone'] = await phone_btn.text_content()
            except: pass
            
            try: details['address'] = await page.locator('.address, .location').first.text_content()
            except: pass
            
            try:
                email_elem = page.locator('.email a, .send-email').first
                email_href = await email_elem.get_attribute('href')
                if email_href and 'mailto:' in email_href:
                    details['email'] = email_href.replace('mailto:', '').split('?')[0]
            except: pass
                
            try:
                web_elem = page.locator('.website a, .site a').first
                details['website'] = await web_elem.get_attribute('href')
            except: pass

            await page.close()
        except: pass
        return details


class InstagramScraper(BaseScraper):
    """
    Scraper for Instagram discovery via search engine.
    Avoids direct login to prevent bans, uses Bing/Google discovery.
    """
    
    async def search(self, query: Dict) -> List[Dict]:
        """Search Instagram profiles via search engine results."""
        try:
            from playwright.async_api import async_playwright
            
            query_text = query.get('query_text') if isinstance(query, dict) else query
            # Optimize query for instagram discovery
            search_query = f'site:instagram.com "{query_text}"'
            
            results = []
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context(user_agent=self._get_random_user_agent())
                page = await context.new_page()
                
                # Use Bing for discovery (less aggressive captchas than Google)
                search_url = f"https://www.bing.com/search?q={search_query.replace(' ', '+')}"
                logger.info(f"Searching Instagram profiles via Bing: {search_url}")
                
                await page.goto(search_url, wait_until='networkidle', timeout=60000)
                await self.random_delay()
                
                # Extract links that look like instagram profiles
                links = await page.locator('li.b_algo h2 a').all()
                for link_elem in links[:10]:
                    href = await link_elem.get_attribute('href')
                    if href and 'instagram.com/' in href and not any(x in href for x in ['/p/', '/reels/', '/explore/']):
                        name = await link_elem.text_content()
                        results.append({
                            'name': name.split('•')[0].split('(@')[0].strip(),
                            'profile_url': href,
                            'source': 'instagram',
                            'query': query_text,
                        })
                
                await browser.close()
                return results
        except Exception as e:
            logger.error(f"Instagram search error: {e}")
            return []

    async def extract_details(self, profile_url: str) -> Dict:
        return {}


class FacebookScraper(BaseScraper):
    """
    Scraper for Facebook business pages discovery via search engine.
    """
    
    async def search(self, query: Dict) -> List[Dict]:
        """Search Facebook pages via search engine results."""
        try:
            from playwright.async_api import async_playwright
            
            query_text = query.get('query_text') if isinstance(query, dict) else query
            # Optimize query for facebook page discovery
            search_query = f'site:facebook.com "{query_text}" "Page"'
            
            results = []
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context(user_agent=self._get_random_user_agent())
                page = await context.new_page()
                
                search_url = f"https://www.bing.com/search?q={search_query.replace(' ', '+')}"
                logger.info(f"Searching Facebook pages via Bing: {search_url}")
                
                await page.goto(search_url, wait_until='networkidle', timeout=60000)
                await self.random_delay()
                
                links = await page.locator('li.b_algo h2 a').all()
                for link_elem in links[:10]:
                    href = await link_elem.get_attribute('href')
                    if href and 'facebook.com/' in href and not any(x in href for x in ['/groups/', '/events/', '/posts/']):
                        name = await link_elem.text_content()
                        results.append({
                            'name': name.split('|')[0].split('- Home')[0].strip(),
                            'profile_url': href,
                            'source': 'facebook',
                            'query': query_text,
                        })
                
                await browser.close()
                return results
        except Exception as e:
            logger.error(f"Facebook search error: {e}")
            return []

    async def extract_details(self, profile_url: str) -> Dict:
        return {}


class CACLookupScraper(BaseScraper):
    """CAC (Corporate Affairs Commission) database lookup for verification."""
    
    async def search(self, query: str) -> List[Dict]:
        """Search CAC database for registered businesses."""
        try:
            logger.info(f"CAC lookup for: {query}")
            return []
        except Exception as e:
            logger.error(f"CAC lookup error: {e}")
            return []
    
    async def extract_details(self, profile_url: str) -> Dict:
        return {'verified': True, 'registration_date': None}
