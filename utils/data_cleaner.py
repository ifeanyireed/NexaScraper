"""
Data cleaning and standardization utilities for Nigerian business data.
Handles phone numbers, addresses, and removes "ghost" businesses.
"""

import re
import phonenumbers
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class EmailExtractor:
    """Extracts and validates Nigerian business email addresses."""
    
    # Common Nigerian business email domains
    NIGERIAN_DOMAINS = [
        'gmail.com', 'yahoo.com', 'hotmail.com',
        'businesslist.com.ng', 'mail.com',
        'outlook.com', 'aol.com', 'rediffmail.com',
    ]
    
    # Email patterns
    EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email format and filter out placeholders."""
        if not email:
            return False
        
        email = email.strip().lower()
        
        # Check basic format
        if not re.match(EmailExtractor.EMAIL_PATTERN, email):
            return False
        
        # Check for common fake/placeholder patterns
        fake_patterns = [
            r'test@', r'demo@', r'noreply@', r'no-reply@',
            r'spam@', r'fake@', r'xxx@', r'example@',
            r'email@', r'businessname@', r'yourdomain@',
            r'domain@', r'yoursite@', r'info@business\.ng',
            r'info@business\.com', r'user@', r'admin@site\.com'
        ]
        
        for pattern in fake_patterns:
            if re.search(pattern, email):
                return False
        
        # Filter out emails that look too generic (e.g., info@company.com where name is unknown)
        if email.split('@')[0] in ['info', 'contact', 'support', 'sales', 'hello', 'mail'] and len(email.split('@')[1].split('.')[0]) < 3:
            return False

        return True
    
    @staticmethod
    def extract_all_from_text(text: str) -> List[str]:
        """Extract all valid emails from text."""
        if not text:
            return []
        
        emails = []
        matches = re.findall(EmailExtractor.EMAIL_PATTERN, text)
        
        for email in matches:
            if EmailExtractor.is_valid_email(email):
                email_lower = email.strip().lower()
                if email_lower not in emails:
                    emails.append(email_lower)
        
        return emails
    
    @staticmethod
    def is_business_email(email: str) -> bool:
        """Check if email appears to be business-related (not personal)."""
        if not email:
            return False
        
        email_lower = email.lower()
        
        # Personal email patterns (usually spam)
        personal_patterns = [
            r'^[0-9]+@',  # Starts with numbers
            r'^user[0-9]*@',  # user123@
            r'^test[0-9]*@',  # test@
            r'^admin[0-9]*@',  # admin@
        ]
        
        for pattern in personal_patterns:
            if re.search(pattern, email_lower):
                return False
        
        # Business patterns (good indicators)
        business_patterns = [
            r'info@', r'contact@', r'business@', r'support@',
            r'hello@', r'sales@', r'office@', r'mail@',
        ]
        
        for pattern in business_patterns:
            if re.search(pattern, email_lower):
                return True
        
        return True  # Default to business if not personal


class PhoneNumberStandardizer:
    """Standardizes Nigerian phone numbers to +234 format."""
    
    # Common Nigerian phone prefixes
    TELECOM_PROVIDERS = {
        "MTN": ["0703", "0704", "0706", "0707", "0708", "0709"],
        "Airtel": ["0802", "0808", "0812", "0813", "0818"],
        "Glo": ["0805", "0807", "0811", "0815", "0816"],
        "9Mobile": ["0809", "0817", "0818"],
    }
    
    @staticmethod
    def standardize(phone: str) -> Optional[str]:
        """
        Convert Nigerian phone number to +234 format.
        
        Examples:
            "0703 123 4567" -> "+2347031234567"
            "+234 703 123 4567" -> "+2347031234567"
            "703 123 4567" -> "+2347031234567"
        """
        if not phone:
            return None
            
        # Clean non-digit characters
        cleaned = re.sub(r'\D', '', phone)
        
        # Handle different input formats
        if cleaned.startswith('234'):
            # Already has country code
            cleaned = cleaned[2:]  # Remove country code to normalize
        
        if not cleaned.startswith('0'):
            # Assume it's missing the leading 0
            if len(cleaned) == 10:
                cleaned = '0' + cleaned
            elif len(cleaned) == 11:
                pass  # Already correct
            else:
                return None
        
        # Validate length (Nigerian: +234XXXXXXXXXXX = 13 characters)
        if len(cleaned) != 11:
            return None
        
        # Convert to +234 format
        return f"+234{cleaned[1:]}"
    
    @staticmethod
    def is_valid_nigerian(phone: str) -> bool:
        """Validate if phone number is a valid Nigerian number."""
        try:
            standardized = PhoneNumberStandardizer.standardize(phone)
            if not standardized:
                return False
            
            # Use phonenumbers library for validation
            parsed = phonenumbers.parse(standardized, None)
            return phonenumbers.is_valid_number(parsed)
        except Exception as e:
            logger.debug(f"Phone validation error: {e}")
            return False
    
    @staticmethod
    def extract_all_from_text(text: str) -> List[str]:
        """Extract and standardize all phone numbers from text."""
        if not text:
            return []
        
        # Patterns for Nigerian phone numbers
        patterns = [
            r'(?:\+234|0)[789][01]\d{8}',  # Standard 11-digit or +234
            r'(?:\+234|0)[789][01]\d\s\d{3}\s\d{4}',  # 0803 123 4567
            r'(?:\+234|0)[789][01]\d-\d{3}-\d{4}',  # 0803-123-4567
            r'[789][01]\d{8}',  # 10-digit (missing leading zero)
        ]
        
        phones = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                standardized = PhoneNumberStandardizer.standardize(match)
                if standardized and standardized not in phones:
                    phones.append(standardized)
        
        return phones


class AddressStandardizer:
    """Standardizes Nigerian addresses."""
    
    # Common address abbreviations
    ABBREVIATIONS = {
        "St": "Street",
        "Ave": "Avenue",
        "Rd": "Road",
        "Blvd": "Boulevard",
        "Apt": "Apartment",
        "Bldg": "Building",
        "Pt": "Plot",
        "No": "Number",
        "Nr": "Near",
    }
    
    @staticmethod
    def standardize(address: str) -> Optional[str]:
        """
        Standardize Nigerian address format.
        Expands abbreviations and removes common noise.
        """
        if not address:
            return None
        
        # Clean whitespace
        address = ' '.join(address.split())
        
        # Expand abbreviations
        for abbr, full in AddressStandardizer.ABBREVIATIONS.items():
            address = re.sub(rf'\b{abbr}\b', full, address, flags=re.IGNORECASE)
        
        # Capitalize properly
        address = ' '.join(word.capitalize() for word in address.split())
        
        return address.strip()
    
    @staticmethod
    def extract_lga_state(address: str) -> Optional[Tuple[str, str]]:
        """
        Extract LGA and State from address.
        
        Returns: (LGA, State) or None
        """
        from config.locations import NIGERIAN_LOCATIONS
        
        if not address:
            return None
        
        address_upper = address.upper()
        
        for state, data in NIGERIAN_LOCATIONS.items():
            state_upper = state.upper()
            if state_upper in address_upper:
                # Try to find specific LGA
                for lga in data['lgas']:
                    if lga.upper() in address_upper:
                        return (lga, state)
                # Return state with None LGA if only state found
                return (None, state)
        
        return None
    
    @staticmethod
    def geocode_address(address: str) -> Optional[Tuple[float, float]]:
        """
        Geocode address to latitude/longitude.
        Uses geopy Nominatim (free, no API key needed).
        
        Returns: (latitude, longitude) or None
        """
        try:
            from geopy.geocoders import Nominatim
            geolocator = Nominatim(user_agent="nigerian_business_scraper")
            
            # Add Nigeria to query for better results
            query = f"{address}, Nigeria"
            location = geolocator.geocode(query, timeout=10)
            
            if location:
                return (location.latitude, location.longitude)
        except Exception as e:
            logger.debug(f"Geocoding error for {address}: {e}")
        
        return None


class DataCleaner:
    """Main data cleaner for business records."""
    
    @staticmethod
    def clean_business_record(record: Dict) -> Dict:
        """
        Clean and standardize a single business record.
        
        Input: Raw scraped business data
        Output: Standardized business data
        """
        cleaned = {}
        
        # Basic info
        cleaned['name'] = record.get('name', '').strip()
        cleaned['industry'] = record.get('industry', '')
        cleaned['finder_type'] = record.get('finder_type', '')
        
        # Combine all text for aggressive contact extraction
        all_text = " ".join([
            str(record.get('address', '') or ''),
            str(record.get('description', '') or ''),
            str(record.get('snippet', '') or ''),
            str(record.get('bio', '') or ''),
            str(record.get('about', '') or '')
        ])
        
        # Address
        original_address = record.get('address', '')
        cleaned['address'] = AddressStandardizer.standardize(original_address)
        
        # Extract LGA and State
        lga_state = AddressStandardizer.extract_lga_state(cleaned['address'] or original_address)
        if lga_state:
            cleaned['lga'], cleaned['state'] = lga_state
        else:
            cleaned['lga'] = record.get('lga')
            cleaned['state'] = record.get('state')
        
        # Geocode
        if cleaned['address']:
            coords = AddressStandardizer.geocode_address(cleaned['address'])
            if coords:
                cleaned['latitude'], cleaned['longitude'] = coords
        
        # Phone numbers - Scan primary field + all text
        phones = []
        if 'phone' in record and record['phone']:
            if isinstance(record['phone'], list):
                for p in record['phone']:
                    std = PhoneNumberStandardizer.standardize(str(p))
                    if std: phones.append(std)
            else:
                phones.extend(PhoneNumberStandardizer.extract_all_from_text(str(record['phone'])))
        
        # Fallback: Extract from all text fields
        phones.extend(PhoneNumberStandardizer.extract_all_from_text(all_text))
        
        cleaned['phones'] = list(set(phones))  # Remove duplicates
        cleaned['primary_phone'] = cleaned['phones'][0] if cleaned['phones'] else None
        
        # WhatsApp
        cleaned['whatsapp'] = record.get('whatsapp')
        if not cleaned['whatsapp'] and cleaned['primary_phone']:
            cleaned['whatsapp_possible'] = True
        
        # Emails - Scan primary fields + all text
        emails = []
        
        # 1. Check primary list/string
        for key in ['emails', 'email']:
            val = record.get(key)
            if val:
                if isinstance(val, list):
                    emails.extend([e.lower() for e in val if EmailExtractor.is_valid_email(str(e))])
                else:
                    emails.extend(EmailExtractor.extract_all_from_text(str(val)))
        
        # 2. Extract from all text fields
        emails.extend(EmailExtractor.extract_all_from_text(all_text))
        
        cleaned['emails'] = list(set(emails))  # Remove duplicates
        cleaned['primary_email'] = next(
            (e for e in cleaned['emails'] if EmailExtractor.is_business_email(e)),
            cleaned['emails'][0] if cleaned['emails'] else None
        )
        
        # Website URLs
        cleaned['website'] = record.get('website')
        if cleaned['website'] and not cleaned['website'].startswith('http'):
            cleaned['website'] = 'https://' + cleaned['website']
        
        # Review/Activity metrics for ghost business detection
        cleaned['reviews_count'] = record.get('reviews_count', 0)
        cleaned['rating'] = record.get('rating', 0)
        cleaned['last_activity'] = record.get('last_activity')
        
        # Metadata
        cleaned['source'] = record.get('source', 'unknown')
        cleaned['scraped_date'] = datetime.now().isoformat()
        cleaned['profile_url'] = record.get('profile_url')
        
        return cleaned
    
    @staticmethod
    def detect_ghost_business(record: Dict, days_threshold: int = 730) -> bool:
        """
        Detect if a business is "ghost" (inactive/fake).
        
        Criteria:
        - No reviews in 24 months
        - No activity timestamp
        - Zero reviews and zero rating
        - Generic/spam name patterns
        """
        # Zero engagement
        if record.get('reviews_count', 0) == 0 and record.get('rating', 0) == 0:
            return True
        
        # Check last activity
        last_activity = record.get('last_activity')
        if last_activity:
            try:
                last_date = datetime.fromisoformat(last_activity)
                if datetime.now() - last_date > timedelta(days=days_threshold):
                    return True
            except:
                pass
        
        # Generic/spam name patterns
        spam_patterns = [
            r'test', r'demo', r'sample', r'xxx', r'placeholder',
            r'[0-9]{2,}', r'aaa|bbb|ccc',  # Repetitive
        ]
        name = record.get('name', '').lower()
        for pattern in spam_patterns:
            if re.search(pattern, name):
                return True
        
        return False
    
    @staticmethod
    def validate_business_record(record: Dict) -> Tuple[bool, List[str]]:
        """
        Validate a business record for completeness.
        
        Returns: (is_valid, list_of_errors)
        """
        errors = []
        
        if not record.get('name'):
            errors.append("Missing business name")
        
        # Must have at least one contact method: phone, WhatsApp, or email
        has_phone = bool(record.get('primary_phone'))
        has_whatsapp = bool(record.get('whatsapp'))
        has_email = bool(record.get('primary_email'))
        
        if not (has_phone or has_whatsapp or has_email):
            errors.append("No contact information (phone, WhatsApp, or email)")
        
        if not record.get('state'):
            errors.append("Missing state/location")
        
        # If there are phones, at least one should be valid Nigerian format (if email exists, pass anyway)
        if record.get('phones'):
            valid_phones = [p for p in record.get('phones', []) 
                           if PhoneNumberStandardizer.is_valid_nigerian(p)]
            if not valid_phones and not has_email:
                errors.append("No valid Nigerian phone numbers or email")
        
        return (len(errors) == 0, errors)


class DataDeduplicator:
    """Remove duplicate business records."""
    
    @staticmethod
    def deduplicate(records: List[Dict]) -> List[Dict]:
        """
        Remove duplicate records based on business name + phone or name + address.
        """
        seen = set()
        deduplicated = []
        
        for record in records:
            # Create signature from name + primary phone
            signature = (record.get('name', '').lower().strip(),
                        record.get('primary_phone', '') or record.get('address', ''))
            
            if signature not in seen:
                seen.add(signature)
                deduplicated.append(record)
        
        return deduplicated
