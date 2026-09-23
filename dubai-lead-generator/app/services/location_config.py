"""
Global Location Configuration and Locale Registry.
Supports searching business leads in Cities, States/Provinces, and Countries worldwide.
Dynamically maps inputs like Pune, Bombay/Mumbai, Maharashtra, Gujarat, India, UAE, USA, UK, etc.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class LocationMeta(BaseModel):
    city: str
    state: Optional[str] = None
    country: str
    country_code: str  # ISO 3166-1 alpha-2 (e.g. IN, AE, US, GB, DE)
    google_gl: str     # Lowercase country code for Google Search / Maps API (e.g. in, ae, us, uk, de)
    default_language: str = "en"
    timezone: str = "UTC"
    default_phone_prefix: str = ""
    location_type: str = "city"  # "city", "state", "country", "custom"
    suggested_areas: List[str] = Field(default_factory=list)


# Comprehensive worldwide location registry (Cities, States, Countries)
LOCATION_REGISTRY: Dict[str, LocationMeta] = {
    # -------------------------------------------------------------
    # INDIA - CITIES
    # -------------------------------------------------------------
    "pune": LocationMeta(
        city="Pune",
        state="Maharashtra",
        country="India",
        country_code="IN",
        google_gl="in",
        default_language="en",
        timezone="Asia/Kolkata",
        default_phone_prefix="+91",
        location_type="city",
        suggested_areas=["Baner", "Kothrud", "Hinjewadi", "Viman Nagar", "Hadapsar", "Chinchwad", "Shivajinagar", "Wakad", "Pimpri", "Kondhwa"]
    ),
    "mumbai": LocationMeta(
        city="Mumbai",
        state="Maharashtra",
        country="India",
        country_code="IN",
        google_gl="in",
        default_language="en",
        timezone="Asia/Kolkata",
        default_phone_prefix="+91",
        location_type="city",
        suggested_areas=["Andheri", "Bandra", "Lower Parel", "BKC", "Thane", "Navi Mumbai", "Worli", "Juhu", "Malad", "Borivali", "Powai"]
    ),
    "bombay": LocationMeta(
        city="Mumbai",
        state="Maharashtra",
        country="India",
        country_code="IN",
        google_gl="in",
        default_language="en",
        timezone="Asia/Kolkata",
        default_phone_prefix="+91",
        location_type="city",
        suggested_areas=["Andheri", "Bandra", "Lower Parel", "BKC", "Thane", "Navi Mumbai", "Worli", "Juhu", "Malad", "Borivali", "Powai"]
    ),
    "delhi": LocationMeta(
        city="Delhi",
        state="Delhi NCR",
        country="India",
        country_code="IN",
        google_gl="in",
        default_language="en",
        timezone="Asia/Kolkata",
        default_phone_prefix="+91",
        location_type="city",
        suggested_areas=["Connaught Place", "South Extension", "Nehru Place", "Dwarka", "Okhla Industrial", "Karol Bagh", "Lajpat Nagar"]
    ),
    "bengaluru": LocationMeta(
        city="Bengaluru",
        state="Karnataka",
        country="India",
        country_code="IN",
        google_gl="in",
        default_language="en",
        timezone="Asia/Kolkata",
        default_phone_prefix="+91",
        location_type="city",
        suggested_areas=["Koramangala", "Indiranagar", "HSR Layout", "Whitefield", "Electronic City", "Jayanagar", "Marathahalli"]
    ),
    "bangalore": LocationMeta(
        city="Bengaluru",
        state="Karnataka",
        country="India",
        country_code="IN",
        google_gl="in",
        default_language="en",
        timezone="Asia/Kolkata",
        default_phone_prefix="+91",
        location_type="city",
        suggested_areas=["Koramangala", "Indiranagar", "HSR Layout", "Whitefield", "Electronic City", "Jayanagar", "Marathahalli"]
    ),
    "hyderabad": LocationMeta(
        city="Hyderabad",
        state="Telangana",
        country="India",
        country_code="IN",
        google_gl="in",
        default_language="en",
        timezone="Asia/Kolkata",
        default_phone_prefix="+91",
        location_type="city",
        suggested_areas=["HITECH City", "Banjara Hills", "Jubilee Hills", "Gachibowli", "Madhapur", "Secunderabad", "Kukatpally"]
    ),
    "ahmedabad": LocationMeta(
        city="Ahmedabad",
        state="Gujarat",
        country="India",
        country_code="IN",
        google_gl="in",
        default_language="en",
        timezone="Asia/Kolkata",
        default_phone_prefix="+91",
        location_type="city",
        suggested_areas=["SG Highway", "Navrangpura", "Bodakdev", "Prahlad Nagar", "Maninagar", "Gota", "Changodar Industrial"]
    ),
    "surat": LocationMeta(
        city="Surat",
        state="Gujarat",
        country="India",
        country_code="IN",
        google_gl="in",
        default_language="en",
        timezone="Asia/Kolkata",
        default_phone_prefix="+91",
        location_type="city",
        suggested_areas=["Ring Road Textile", "Vesu", "Adajan", "Varachha Diamond Market", "Katargam", "Sachin GIDC"]
    ),
    "jaipur": LocationMeta(
        city="Jaipur",
        state="Rajasthan",
        country="India",
        country_code="IN",
        google_gl="in",
        default_language="en",
        timezone="Asia/Kolkata",
        default_phone_prefix="+91",
        location_type="city",
        suggested_areas=["Malviya Nagar", "C Scheme", "Vaishali Nagar", "Mansarovar", "Sitapura Industrial Area", "Raja Park"]
    ),
    "kolkata": LocationMeta(
        city="Kolkata",
        state="West Bengal",
        country="India",
        country_code="IN",
        google_gl="in",
        default_language="en",
        timezone="Asia/Kolkata",
        default_phone_prefix="+91",
        location_type="city",
        suggested_areas=["Salt Lake Sector V", "Park Street", "New Town", "Bhowanipore", "Howrah Industrial", "Alipore"]
    ),
    "chennai": LocationMeta(
        city="Chennai",
        state="Tamil Nadu",
        country="India",
        country_code="IN",
        google_gl="in",
        default_language="en",
        timezone="Asia/Kolkata",
        default_phone_prefix="+91",
        location_type="city",
        suggested_areas=["T Nagar", "OMR IT Corridor", "Anna Nagar", "Velachery", "Guindy Industrial", "Adyar", "Ambattur"]
    ),

    # -------------------------------------------------------------
    # INDIA - STATES
    # -------------------------------------------------------------
    "maharashtra": LocationMeta(
        city="Maharashtra",
        state="Maharashtra",
        country="India",
        country_code="IN",
        google_gl="in",
        default_language="en",
        timezone="Asia/Kolkata",
        default_phone_prefix="+91",
        location_type="state",
        suggested_areas=["Mumbai", "Pune", "Nagpur", "Nashik", "Thane", "Aurangabad", "Solapur", "Kolhapur", "Navi Mumbai", "Sangli"]
    ),
    "gujarat": LocationMeta(
        city="Gujarat",
        state="Gujarat",
        country="India",
        country_code="IN",
        google_gl="in",
        default_language="en",
        timezone="Asia/Kolkata",
        default_phone_prefix="+91",
        location_type="state",
        suggested_areas=["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar", "Jamnagar", "Gandhinagar", "Anand", "Morbi", "Vapi"]
    ),
    "karnataka": LocationMeta(
        city="Karnataka",
        state="Karnataka",
        country="India",
        country_code="IN",
        google_gl="in",
        default_language="en",
        timezone="Asia/Kolkata",
        default_phone_prefix="+91",
        location_type="state",
        suggested_areas=["Bengaluru", "Mysore", "Hubli-Dharwad", "Mangalore", "Belgaum", "Gulbarga", "Davangere", "Bellary"]
    ),
    "telangana": LocationMeta(
        city="Telangana",
        state="Telangana",
        country="India",
        country_code="IN",
        google_gl="in",
        default_language="en",
        timezone="Asia/Kolkata",
        default_phone_prefix="+91",
        location_type="state",
        suggested_areas=["Hyderabad", "Warangal", "Nizamabad", "Karimnagar", "Khammam", "Ramagundam"]
    ),
    "tamil nadu": LocationMeta(
        city="Tamil Nadu",
        state="Tamil Nadu",
        country="India",
        country_code="IN",
        google_gl="in",
        default_language="en",
        timezone="Asia/Kolkata",
        default_phone_prefix="+91",
        location_type="state",
        suggested_areas=["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem", "Tirupur", "Erode", "Vellore"]
    ),

    # -------------------------------------------------------------
    # INDIA - COUNTRY
    # -------------------------------------------------------------
    "india": LocationMeta(
        city="India",
        state="",
        country="India",
        country_code="IN",
        google_gl="in",
        default_language="en",
        timezone="Asia/Kolkata",
        default_phone_prefix="+91",
        location_type="country",
        suggested_areas=["Mumbai, Maharashtra", "Pune, Maharashtra", "Delhi NCR", "Bangalore, Karnataka", "Hyderabad, Telangana", "Ahmedabad, Gujarat", "Surat, Gujarat", "Chennai, Tamil Nadu"]
    ),

    # -------------------------------------------------------------
    # MIDDLE EAST & UAE
    # -------------------------------------------------------------
    "dubai": LocationMeta(
        city="Dubai",
        state="Dubai",
        country="United Arab Emirates",
        country_code="AE",
        google_gl="ae",
        default_language="en",
        timezone="Asia/Dubai",
        default_phone_prefix="+971",
        location_type="city",
        suggested_areas=["Al Quoz Industrial", "Ras Al Khor Industrial", "Deira Wholesale", "Business Bay", "JAFZA", "Dubai Marina", "DIFC", "Downtown Dubai"]
    ),
    "abu dhabi": LocationMeta(
        city="Abu Dhabi",
        state="Abu Dhabi",
        country="United Arab Emirates",
        country_code="AE",
        google_gl="ae",
        default_language="en",
        timezone="Asia/Dubai",
        default_phone_prefix="+971",
        location_type="city",
        suggested_areas=["Mussafah Industrial", "Khalidiya", "Al Reem Island", "Hamdan Street", "ICAD", "Al Maryah Island"]
    ),
    "sharjah": LocationMeta(
        city="Sharjah",
        state="Sharjah",
        country="United Arab Emirates",
        country_code="AE",
        google_gl="ae",
        default_language="en",
        timezone="Asia/Dubai",
        default_phone_prefix="+971",
        location_type="city",
        suggested_areas=["Industrial Area 1-17", "SAIF Zone", "Al Majaz", "Al Nahda", "Al Rolla"]
    ),
    "riyadh": LocationMeta(
        city="Riyadh",
        state="Riyadh Region",
        country="Saudi Arabia",
        country_code="SA",
        google_gl="sa",
        default_language="ar",
        timezone="Asia/Riyadh",
        default_phone_prefix="+966",
        location_type="city",
        suggested_areas=["Olaya Financial District", "Al Malaz", "Al Sulaimaniyah", "King Abdullah Financial District", "Second Industrial City"]
    ),
    "doha": LocationMeta(
        city="Doha",
        state="Doha",
        country="Qatar",
        country_code="QA",
        google_gl="qa",
        default_language="ar",
        timezone="Asia/Qatar",
        default_phone_prefix="+974",
        location_type="city",
        suggested_areas=["West Bay Financial", "Industrial Area", "Al Sadd", "The Pearl", "Lusail City"]
    ),
    "united arab emirates": LocationMeta(
        city="United Arab Emirates",
        state="",
        country="United Arab Emirates",
        country_code="AE",
        google_gl="ae",
        default_language="en",
        timezone="Asia/Dubai",
        default_phone_prefix="+971",
        location_type="country",
        suggested_areas=["Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Ras Al Khaimah", "Fujairah"]
    ),
    "uae": LocationMeta(
        city="United Arab Emirates",
        state="",
        country="United Arab Emirates",
        country_code="AE",
        google_gl="ae",
        default_language="en",
        timezone="Asia/Dubai",
        default_phone_prefix="+971",
        location_type="country",
        suggested_areas=["Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Ras Al Khaimah", "Fujairah"]
    ),

    # -------------------------------------------------------------
    # UNITED KINGDOM
    # -------------------------------------------------------------
    "london": LocationMeta(
        city="London",
        state="Greater London",
        country="United Kingdom",
        country_code="GB",
        google_gl="uk",
        default_language="en",
        timezone="Europe/London",
        default_phone_prefix="+44",
        location_type="city",
        suggested_areas=["City of London", "Canary Wharf", "Shoreditch Tech City", "Westminster", "Kensington", "Camden", "Mayfair"]
    ),
    "manchester": LocationMeta(
        city="Manchester",
        state="Greater Manchester",
        country="United Kingdom",
        country_code="GB",
        google_gl="uk",
        default_language="en",
        timezone="Europe/London",
        default_phone_prefix="+44",
        location_type="city",
        suggested_areas=["Spinningfields", "MediaCityUK", "Northern Quarter", "Trafford Park", "Didsbury"]
    ),
    "united kingdom": LocationMeta(
        city="United Kingdom",
        state="",
        country="United Kingdom",
        country_code="GB",
        google_gl="uk",
        default_language="en",
        timezone="Europe/London",
        default_phone_prefix="+44",
        location_type="country",
        suggested_areas=["London", "Manchester", "Birmingham", "Edinburgh", "Glasgow", "Leeds", "Liverpool", "Bristol"]
    ),
    "uk": LocationMeta(
        city="United Kingdom",
        state="",
        country="United Kingdom",
        country_code="GB",
        google_gl="uk",
        default_language="en",
        timezone="Europe/London",
        default_phone_prefix="+44",
        location_type="country",
        suggested_areas=["London", "Manchester", "Birmingham", "Edinburgh", "Glasgow", "Leeds", "Liverpool", "Bristol"]
    ),

    # -------------------------------------------------------------
    # UNITED STATES
    # -------------------------------------------------------------
    "new york": LocationMeta(
        city="New York",
        state="New York",
        country="United States",
        country_code="US",
        google_gl="us",
        default_language="en",
        timezone="America/New_York",
        default_phone_prefix="+1",
        location_type="city",
        suggested_areas=["Manhattan", "Brooklyn", "Queens", "Wall Street", "Silicon Alley", "Midtown", "SoHo"]
    ),
    "chicago": LocationMeta(
        city="Chicago",
        state="Illinois",
        country="United States",
        country_code="US",
        google_gl="us",
        default_language="en",
        timezone="America/Chicago",
        default_phone_prefix="+1",
        location_type="city",
        suggested_areas=["The Loop", "West Loop", "River North", "Lincoln Park", "O'Hare Corridor"]
    ),
    "los angeles": LocationMeta(
        city="Los Angeles",
        state="California",
        country="United States",
        country_code="US",
        google_gl="us",
        default_language="en",
        timezone="America/Los_Angeles",
        default_phone_prefix="+1",
        location_type="city",
        suggested_areas=["Downtown LA", "Silicon Beach", "Santa Monica", "Beverly Hills", "Irvine", "Century City"]
    ),
    "california": LocationMeta(
        city="California",
        state="California",
        country="United States",
        country_code="US",
        google_gl="us",
        default_language="en",
        timezone="America/Los_Angeles",
        default_phone_prefix="+1",
        location_type="state",
        suggested_areas=["Los Angeles", "San Francisco", "San Jose / Silicon Valley", "San Diego", "Sacramento", "Orange County"]
    ),
    "texas": LocationMeta(
        city="Texas",
        state="Texas",
        country="United States",
        country_code="US",
        google_gl="us",
        default_language="en",
        timezone="America/Chicago",
        default_phone_prefix="+1",
        location_type="state",
        suggested_areas=["Houston", "Dallas", "Austin", "San Antonio", "Fort Worth", "Plano"]
    ),
    "united states": LocationMeta(
        city="United States",
        state="",
        country="United States",
        country_code="US",
        google_gl="us",
        default_language="en",
        timezone="America/New_York",
        default_phone_prefix="+1",
        location_type="country",
        suggested_areas=["New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Austin, TX", "Miami, FL", "Seattle, WA"]
    ),
    "usa": LocationMeta(
        city="United States",
        state="",
        country="United States",
        country_code="US",
        google_gl="us",
        default_language="en",
        timezone="America/New_York",
        default_phone_prefix="+1",
        location_type="country",
        suggested_areas=["New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Austin, TX", "Miami, FL", "Seattle, WA"]
    ),

    # -------------------------------------------------------------
    # CANADA, AUSTRALIA, GERMANY, FRANCE, JAPAN, SINGAPORE
    # -------------------------------------------------------------
    "toronto": LocationMeta(
        city="Toronto",
        state="Ontario",
        country="Canada",
        country_code="CA",
        google_gl="ca",
        default_language="en",
        timezone="America/Toronto",
        default_phone_prefix="+1",
        location_type="city",
        suggested_areas=["Downtown Toronto", "Financial District", "Mississauga", "Markham", "Yorkville"]
    ),
    "sydney": LocationMeta(
        city="Sydney",
        state="New South Wales",
        country="Australia",
        country_code="AU",
        google_gl="au",
        default_language="en",
        timezone="Australia/Sydney",
        default_phone_prefix="+61",
        location_type="city",
        suggested_areas=["Sydney CBD", "North Sydney", "Parramatta", "Surry Hills", "Barangaroo"]
    ),
    "tokyo": LocationMeta(
        city="Tokyo",
        state="Tokyo Metropolis",
        country="Japan",
        country_code="JP",
        google_gl="jp",
        default_language="ja",
        timezone="Asia/Tokyo",
        default_phone_prefix="+81",
        location_type="city",
        suggested_areas=["Shinjuku", "Shibuya", "Ginza", "Chiyoda", "Minato", "Marunouchi", "Roppongi"]
    ),
    "singapore": LocationMeta(
        city="Singapore",
        state="Singapore",
        country="Singapore",
        country_code="SG",
        google_gl="sg",
        default_language="en",
        timezone="Asia/Singapore",
        default_phone_prefix="+65",
        location_type="country",
        suggested_areas=["Marina Bay Financial", "Raffles Place", "Orchard", "Jurong Industrial", "Changi Business Park"]
    ),
    "berlin": LocationMeta(
        city="Berlin",
        state="Berlin",
        country="Germany",
        country_code="DE",
        google_gl="de",
        default_language="de",
        timezone="Europe/Berlin",
        default_phone_prefix="+49",
        location_type="city",
        suggested_areas=["Mitte", "Kreuzberg", "Charlottenburg", "Prenzlauer Berg", "Pottsdamer Platz"]
    ),
    "paris": LocationMeta(
        city="Paris",
        state="Île-de-France",
        country="France",
        country_code="FR",
        google_gl="fr",
        default_language="fr",
        timezone="Europe/Paris",
        default_phone_prefix="+33",
        location_type="city",
        suggested_areas=["La Défense", "Le Marais", "Champs-Élysées", "Opéra", "Bourse"]
    ),
}


# Recognized Country Name to ISO & GL mappings for dynamic dynamic resolution
COUNTRY_MAP = {
    "india": ("IN", "in", "India", "+91", "Asia/Kolkata"),
    "united arab emirates": ("AE", "ae", "United Arab Emirates", "+971", "Asia/Dubai"),
    "uae": ("AE", "ae", "United Arab Emirates", "+971", "Asia/Dubai"),
    "saudi arabia": ("SA", "sa", "Saudi Arabia", "+966", "Asia/Riyadh"),
    "qatar": ("QA", "qa", "Qatar", "+974", "Asia/Qatar"),
    "united kingdom": ("GB", "uk", "United Kingdom", "+44", "Europe/London"),
    "uk": ("GB", "uk", "United Kingdom", "+44", "Europe/London"),
    "united states": ("US", "us", "United States", "+1", "America/New_York"),
    "usa": ("US", "us", "United States", "+1", "America/New_York"),
    "canada": ("CA", "ca", "Canada", "+1", "America/Toronto"),
    "australia": ("AU", "au", "Australia", "+61", "Australia/Sydney"),
    "germany": ("DE", "de", "Germany", "+49", "Europe/Berlin"),
    "france": ("FR", "fr", "France", "+33", "Europe/Paris"),
    "japan": ("JP", "jp", "Japan", "+81", "Asia/Tokyo"),
    "singapore": ("SG", "sg", "Singapore", "+65", "Asia/Singapore"),
}


def get_location_meta(location_name: str, fallback_country: Optional[str] = None) -> LocationMeta:
    """
    Intelligently resolve location metadata for ANY city, state, or country worldwide.
    Handles Pune, Bombay/Mumbai, Maharashtra, Gujarat, India, UAE, USA, UK, etc.
    Never forces default Dubai/AE on non-Dubai locations!
    """
    if not location_name or not location_name.strip():
        return LOCATION_REGISTRY["dubai"]

    clean_raw = location_name.strip()
    clean_key = clean_raw.lower()

    # 1. Direct registry lookup
    if clean_key in LOCATION_REGISTRY:
        return LOCATION_REGISTRY[clean_key]

    # 2. Check if key is a known country in COUNTRY_MAP
    if clean_key in COUNTRY_MAP:
        iso, gl, country_name, prefix, tz = COUNTRY_MAP[clean_key]
        return LocationMeta(
            city=country_name,
            state="",
            country=country_name,
            country_code=iso,
            google_gl=gl,
            default_language="en",
            timezone=tz,
            default_phone_prefix=prefix,
            location_type="country",
            suggested_areas=[f"Major cities in {country_name}"]
        )

    # 3. Partial substring search in LOCATION_REGISTRY
    for k, meta in LOCATION_REGISTRY.items():
        if k in clean_key or clean_key in k:
            return meta

    # 4. Intelligent dynamic token parsing for custom queries (e.g. "Pune, Maharashtra", "Gujarat, India", "Paris, France")
    detected_country = fallback_country or ""
    detected_iso = "IN"
    detected_gl = "in"
    phone_prefix = ""
    timezone = "UTC"

    # Search for country tokens inside clean_key
    for country_token, (iso, gl, cname, prefix, tz) in COUNTRY_MAP.items():
        if country_token in clean_key or (fallback_country and country_token in fallback_country.lower()):
            detected_country = cname
            detected_iso = iso
            detected_gl = gl
            phone_prefix = prefix
            timezone = tz
            break

    # If no country detected, check for common Indian state/city keywords
    indian_keywords = ["pune", "mumbai", "bombay", "delhi", "bangalore", "bengaluru", "hyderabad", "ahmedabad", "surat", "maharashtra", "gujarat", "karnataka", "telangana", "tamil nadu", "rajasthan", "punjab", "haryana", "noida", "gurgaon"]
    if not detected_country:
        if any(k in clean_key for k in indian_keywords):
            detected_country = "India"
            detected_iso = "IN"
            detected_gl = "in"
            phone_prefix = "+91"
            timezone = "Asia/Kolkata"
        elif any(k in clean_key for k in ["dubai", "abu dhabi", "sharjah", "uae"]):
            detected_country = "United Arab Emirates"
            detected_iso = "AE"
            detected_gl = "ae"
            phone_prefix = "+971"
            timezone = "Asia/Dubai"
        elif any(k in clean_key for k in ["london", "manchester", "uk"]):
            detected_country = "United Kingdom"
            detected_iso = "GB"
            detected_gl = "uk"
            phone_prefix = "+44"
            timezone = "Europe/London"
        elif any(k in clean_key for k in ["new york", "chicago", "los angeles", "california", "texas", "usa"]):
            detected_country = "United States"
            detected_iso = "US"
            detected_gl = "us"
            phone_prefix = "+1"
            timezone = "America/New_York"
        else:
            detected_country = fallback_country or "Global"
            detected_iso = "US"
            detected_gl = "us"

    return LocationMeta(
        city=clean_raw.title(),
        state=clean_raw.title(),
        country=detected_country,
        country_code=detected_iso,
        google_gl=detected_gl,
        default_language="en",
        timezone=timezone,
        default_phone_prefix=phone_prefix,
        location_type="custom",
        suggested_areas=[clean_raw.title()]
    )


def get_all_preset_locations() -> Dict[str, List[Dict[str, Any]]]:
    """Returns world location presets grouped by region for the frontend UI."""
    return {
        "India": [
            {"name": "Pune", "type": "city", "state": "Maharashtra", "flag": "🇮🇳"},
            {"name": "Mumbai", "type": "city", "state": "Maharashtra", "flag": "🇮🇳"},
            {"name": "Maharashtra", "type": "state", "state": "Maharashtra", "flag": "🇮🇳"},
            {"name": "Gujarat", "type": "state", "state": "Gujarat", "flag": "🇮🇳"},
            {"name": "Delhi", "type": "city", "state": "Delhi NCR", "flag": "🇮🇳"},
            {"name": "Bengaluru", "type": "city", "state": "Karnataka", "flag": "🇮🇳"},
            {"name": "Hyderabad", "type": "city", "state": "Telangana", "flag": "🇮🇳"},
            {"name": "Ahmedabad", "type": "city", "state": "Gujarat", "flag": "🇮🇳"},
            {"name": "Surat", "type": "city", "state": "Gujarat", "flag": "🇮🇳"},
            {"name": "India", "type": "country", "state": "", "flag": "🇮🇳"},
        ],
        "Middle East": [
            {"name": "Dubai", "type": "city", "state": "Dubai", "flag": "🇦🇪"},
            {"name": "Abu Dhabi", "type": "city", "state": "Abu Dhabi", "flag": "🇦🇪"},
            {"name": "Sharjah", "type": "city", "state": "Sharjah", "flag": "🇦🇪"},
            {"name": "Riyadh", "type": "city", "state": "Riyadh", "flag": "🇸🇦"},
            {"name": "Doha", "type": "city", "state": "Doha", "flag": "🇶🇦"},
            {"name": "United Arab Emirates", "type": "country", "state": "", "flag": "🇦🇪"},
        ],
        "North America": [
            {"name": "New York", "type": "city", "state": "New York", "flag": "🇺🇸"},
            {"name": "Los Angeles", "type": "city", "state": "California", "flag": "🇺🇸"},
            {"name": "Chicago", "type": "city", "state": "Illinois", "flag": "🇺🇸"},
            {"name": "California", "type": "state", "state": "California", "flag": "🇺🇸"},
            {"name": "Texas", "type": "state", "state": "Texas", "flag": "🇺🇸"},
            {"name": "Toronto", "type": "city", "state": "Ontario", "flag": "🇨🇦"},
            {"name": "United States", "type": "country", "state": "", "flag": "🇺🇸"},
        ],
        "Europe & UK": [
            {"name": "London", "type": "city", "state": "Greater London", "flag": "🇬🇧"},
            {"name": "Manchester", "type": "city", "state": "Greater Manchester", "flag": "🇬🇧"},
            {"name": "Berlin", "type": "city", "state": "Berlin", "flag": "🇩🇪"},
            {"name": "Paris", "type": "city", "state": "Île-de-France", "flag": "🇫🇷"},
            {"name": "United Kingdom", "type": "country", "state": "", "flag": "🇬🇧"},
        ],
        "Asia & Pacific": [
            {"name": "Tokyo", "type": "city", "state": "Tokyo", "flag": "🇯🇵"},
            {"name": "Singapore", "type": "country", "state": "", "flag": "🇸🇬"},
            {"name": "Sydney", "type": "city", "state": "New South Wales", "flag": "🇦🇺"},
        ]
    }
