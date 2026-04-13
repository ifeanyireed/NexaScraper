# Nigerian Industries Configuration
# Maps industry categories to specific "Finders" (service types)

INDUSTRIES = {
    "Home & Maintenance": {
        "handyman": ["Plumber", "Electrician", "Carpenter", "Painter", "Tiler", "Welder"],
        "specialist": ["Solar Installer", "Generator Repairer", "AC Technician", "Borehole Driller", "Inverter Repairer"],
        "sanitation": ["Home Cleaner", "Fumigator", "Pest Control", "Waste Disposal", "Water Tank Cleaner"]
    },
    "Fashion & Personal Grooming": {
        "style": ["Tailor", "Hairdresser", "Braider", "Barber", "Makeup Artist", "Manicurist", "Nail Tech"],
        "wardrobe": ["Laundry", "Dry Cleaner", "Personal Shopper", "Cobbler", "Shoe Repair"]
    },
    "Professional & Business Services": {
        "tech": ["Web Developer", "App Developer", "UI/UX Designer", "SEO Expert", "Cybersecurity Consultant"],
        "corporate": ["Lawyer", "Accountant", "Tax Consultant", "Business Consultant", "Grant Writer"],
        "content": ["Copywriter", "Social Media Manager", "Graphic Designer", "Video Editor", "Translator"]
    },
    "Education & Skill Development": {
        "academic": ["Home Tutor", "Music Instructor", "Language Teacher", "Exam Prep Tutor"],
        "vocational": ["Driving School", "Tech Skill Trainer", "Fashion School"]
    },
    "Events & Entertainment": {
        "planning": ["Event Planner", "Decorator", "Souvenir Vendor", "Ushering Agency"],
        "talent": ["DJ", "MC", "Photographer", "Videographer", "Drone Pilot", "Live Band", "Musician"]
    },
    "Health & Wellness": {
        "medical": ["Private Nurse", "Physiotherapist", "Dentist", "Optician", "Pharmacy"],
        "wellness": ["Gym Instructor", "Yoga Teacher", "Nutritionist", "Massage Therapist"]
    },
    "Logistics & Transport": {
        "transport": ["Professional Driver", "Towing Van", "Car Rental", "Bus Hire"],
        "delivery": ["Dispatch Rider", "Logistics", "Errand Runner", "Moving Service", "Relocation"]
    },
    "Automotive Services": {
        "repair": ["Car Mechanic", "Vulcanizer", "Panel Beater", "Auto Electrician"],
        "care": ["Mobile Car Wash", "Car Tracker Installer", "CCTV Installer", "Security Installer"]
    },
    "Food & Agribusiness": {
        "culinary": ["Private Chef", "Caterer", "Cake Baker", "Bulk Food Supplier"],
        "agro": ["Farm Manager", "Agro-Processor", "Veterinary Doctor", "Pet Groomer"]
    },
    "Real Estate & Construction": {
        "property": ["Estate Agent", "Facility Manager", "Surveyor", "Quantity Surveyor"],
        "building": ["Architect", "Bricklayer", "Aluminum Fitter", "POP Ceiling Installer"]
    }
}

# Tier-based sources for different scraping strategies
SCRAPER_SOURCES = {
    "google_maps": {
        "name": "Google Maps",
        "priority": 1,
        "difficulty": "high",
        "description": "Physical locations, reviews, high-frequency finders"
    },
    "bing_search": {
        "name": "Bing Search",
        "priority": 2,
        "difficulty": "medium",
        "description": "Web search results with business websites and emails"
    },
    "businesslist_ng": {
        "name": "BusinessList.com.ng",
        "priority": 3,
        "difficulty": "medium",
        "description": "Nigerian business directory with contact info"
    },
    "yellowpages_ng": {
        "name": "YellowPages NG",
        "priority": 4,
        "difficulty": "medium",
        "description": "Traditional business listings and registered SMEs"
    },
    "jiji": {
        "name": "Jiji Nigeria",
        "priority": 5,
        "difficulty": "high",
        "description": "Visual services (Makeup, Tailoring, etc.)"
    },
    "instagram": {
        "name": "Instagram",
        "priority": 6,
        "difficulty": "high",
        "description": "Visual services and social presence"
    },
    "cac": {
        "name": "CAC / NG-Check",
        "priority": 7,
        "difficulty": "low",
        "description": "Professional/Corporate verification"
    }
}
