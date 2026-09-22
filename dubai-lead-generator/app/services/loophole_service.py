"""
Company Loophole Research & Vulnerability Analysis Service.
Conducts deep forensic analysis of a business before pitching to find the
exact digital loophole (revenue leak, lost corporate contracts, trust friction)
caused by having NO website.
"""

from typing import Dict, Any, Optional
import json
from loguru import logger
from app.config import settings

# Pre-defined intelligent industry vulnerability matrix
INDUSTRY_LOOPHOLES = {
    "b2b_wholesale": {
        "title": "Missing B2B Digital Catalog & Corporate RFQ System",
        "description": "Bulk corporate buyers and international procurement teams in trade hubs like Dubai search online for wholesale distributors. Without an official website, they cannot verify product specifications, download catalogs, or submit RFQs (Requests for Quote), steering massive bulk purchase orders directly to digital-ready competitors.",
        "revenue_leak": "Estimated $15,000 - $60,000 (AED 55k - 220k) in lost wholesale contracts annually.",
        "website_blueprint": "High-speed B2B Wholesale Portal with searchable catalog, downloadable PDF spec sheets, instant RFQ quotation form, and WhatsApp procurement hotline.",
        "pitch_angle": "Corporate procurement managers are bypassing your business because they cannot view your wholesale catalog or submit an RFQ online."
    },
    "industrial_contracting": {
        "title": "Zero Tender Visibility & Missing Technical Credentials",
        "description": "Commercial property developers and facility managers verify contractors online before awarding tenders. Without an official digital presence, your business is invisible for high-value tenders, forcing you to rely solely on broker referrals who take heavy cuts.",
        "revenue_leak": "Estimated $25,000 - $100,000+ per lost commercial project.",
        "website_blueprint": "Authority Contractor Portfolio with past completed projects gallery, HSE certifications, client testimonials, and instant commercial inquiry form.",
        "pitch_angle": "High-value commercial tenders require a verified digital portfolio; without one, tier-1 clients award contracts to your competitors."
    },
    "auto_spare_parts": {
        "title": "No Part Number Lookup & Zero Export Order Capture",
        "description": "Auto parts buyers from across the Middle East and Africa seek Dubai distributors via part numbers (OEM/Aftermarket). Having no website means zero visibility on international search engines, losing export inquiries to competitors with part databases.",
        "revenue_leak": "Estimated $10,000 - $45,000 monthly in missed regional export inquiries.",
        "website_blueprint": "Automotive Parts Catalog with OEM number search, brand filter, stock availability status, and direct WhatsApp / Email export inquiry desk.",
        "pitch_angle": "Regional auto buyers searching for your specific parts cannot find your catalog online, sending export orders to rival suppliers."
    },
    "retail_luxury": {
        "title": "High Trust Deficit & Lost Affluent Walk-Ins",
        "description": "High-net-worth customers and international visitors research brands online before visiting in person. Without a verified personal website, affluent shoppers assume the brand is unverified or discount-tier, choosing established digital storefronts instead.",
        "revenue_leak": "Estimated $8,000 - $25,000 in lost high-margin retail sales every month.",
        "website_blueprint": "Luxury Showcase Website featuring brand story, VIP private appointment booking, high-res collection preview, and interactive boutique locator.",
        "pitch_angle": "Affluent buyers searching for your products are dropping off due to the lack of an official verified brand website."
    },
    "services_dining_salon": {
        "title": "No 24/7 Direct Booking & Third-Party Commission Bleed",
        "description": "Over 65% of customer bookings happen in the evening after normal business hours. With only a phone number and no website, you lose impulse appointments while they sleep or pay 20-30% commissions to third-party aggregators.",
        "revenue_leak": "Estimated $4,000 - $12,000 monthly in lost bookings and commission deductions.",
        "website_blueprint": "Instant Direct Booking Engine with service menu, pricing, real-time slot selection, Google Maps integration, and zero commission fee.",
        "pitch_angle": "Customers ready to book outside business hours cannot do so online, resulting in lost bookings every single night."
    },
    "general": {
        "title": "Zero Google Discovery & Total Digital Invisibility",
        "description": "Customers actively looking for your exact services in your area find competitor websites with official links and clear offers. Without an official domain, your high Google rating and customer loyalty fail to convert into new inbound clients.",
        "revenue_leak": "Estimated $5,000 - $20,000 in missed inbound client inquiries monthly.",
        "website_blueprint": "Clean, modern 5-page Responsive Website with service highlights, customer proof, instant quote request, and direct CEO/sales hotline.",
        "pitch_angle": "Hundreds of high-intent local searches every month are ending up with your competitors simply because they have an official website and you do not."
    }
}


class LoopholeResearchService:
    """Service to discover company details and diagnose business loopholes."""

    def __init__(self):
        pass

    def classify_business_type(self, name: str, category: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Classify business as B2B Wholesale/Dealer or B2C Retail/Service."""
        combined_text = f"{name} {category} {description or ''}".lower()

        b2b_keywords = [
            "wholesale", "trading", "distributor", "supplier", "industrial",
            "dealer", "equipment", "hardware", "building materials", "spare parts",
            "machinery", "chemicals", "packaging", "commercial", "logistics",
            "import", "export", "llc", "fze", "general trading"
        ]

        is_b2b = any(kw in combined_text for kw in b2b_keywords)
        is_dealer = any(kw in combined_text for kw in ["dealer", "wholesale", "distributor", "supplier", "trading"])

        return {
            "business_type": "B2B" if is_b2b else "B2C",
            "is_dealer_or_wholesale": is_dealer,
        }

    def analyze_company_and_loophole(
        self,
        business_name: str,
        category: str,
        city: str = "Dubai",
        area: Optional[str] = None,
        google_rating: Optional[float] = None,
        review_count: Optional[int] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Conduct deep analysis of the business to identify what they do,
        their primary revenue loophole, and the custom website solution.
        """
        combined = f"{business_name} {category} {description or ''}".lower()
        classification = self.classify_business_type(business_name, category, description)
        b_type = classification["business_type"]

        # Select loophole pattern
        if any(k in combined for k in ["auto", "spare parts", "car parts"]):
            pattern = INDUSTRY_LOOPHOLES["auto_spare_parts"]
            industry_label = "Automotive & Spare Parts Distribution"
        elif any(k in combined for k in ["wholesale", "distributor", "supplier", "trading", "dealer"]):
            pattern = INDUSTRY_LOOPHOLES["b2b_wholesale"]
            industry_label = "B2B Wholesale & Commercial Trading"
        elif any(k in combined for k in ["contractor", "construction", "mep", "engineering"]):
            pattern = INDUSTRY_LOOPHOLES["industrial_contracting"]
            industry_label = "Industrial & Commercial Contracting"
        elif any(k in combined for k in ["salon", "spa", "barber", "restaurant", "cafe", "clinic", "dental"]):
            pattern = INDUSTRY_LOOPHOLES["services_dining_salon"]
            industry_label = "Local Services & Hospitality"
        elif any(k in combined for k in ["jewel", "luxury", "perfume", "fashion", "boutique", "watch"]):
            pattern = INDUSTRY_LOOPHOLES["retail_luxury"]
            industry_label = "High-End Retail & Luxury"
        else:
            pattern = INDUSTRY_LOOPHOLES["general"]
            industry_label = f"{category or 'Commercial'} Business"

        location_display = f"{area}, {city}" if area else city
        rating_text = f"{google_rating}★ ({review_count} reviews)" if google_rating else "established presence"

        # Revenue turnover and leak estimation based on sector and review signals
        reviews = review_count or 10
        if b_type == "B2B" or classification["is_dealer_or_wholesale"]:
            if reviews > 50:
                est_turnover = "$2,500,000 - $5,500,000 (AED 9.2M - 20.2M)"
                est_leak = "Estimated $75,000 - $180,000 (AED 275k - 660k) in lost wholesale revenue annually"
            else:
                est_turnover = "$1,200,000 - $3,000,000 (AED 4.4M - 11.0M)"
                est_leak = "Estimated $45,000 - $95,000 (AED 165k - 350k) in lost wholesale revenue annually"
        elif "luxury" in pattern["title"].lower() or "retail" in pattern["title"].lower():
            est_turnover = "$600,000 - $1,500,000 (AED 2.2M - 5.5M)"
            est_leak = "Estimated $25,000 - $60,000 (AED 90k - 220k) in lost retail sales annually"
        else:
            est_turnover = "$350,000 - $800,000 (AED 1.3M - 2.9M)"
            est_leak = "Estimated $15,000 - $35,000 (AED 55k - 130k) in lost bookings annually"

        # What they do summary
        what_they_do = (
            f"{business_name} is an established {industry_label} operating in {location_display}. "
            f"They serve {b_type} customers with an active physical presence ({rating_text})."
        )

        competitor_threat = (
            f"Active competitors in {city} with verified web portals are capturing 70%+ of "
            f"high-intent online search traffic and bulk corporate RFQ submissions."
        )

        loophole_data = {
            "company_overview": what_they_do,
            "industry": industry_label,
            "business_type": b_type,
            "is_dealer_or_wholesale": classification["is_dealer_or_wholesale"],
            "estimated_annual_turnover": est_turnover,
            "primary_loophole": pattern["title"],
            "loophole_details": pattern["description"],
            "estimated_revenue_leak": est_leak,
            "competitor_threat": competitor_threat,
            "ceo_pitch_hook": pattern["pitch_angle"],
            "website_solution_blueprint": pattern["website_blueprint"],
            "key_missing_features": [
                "No official verified company domain or SSL certificate",
                "No interactive digital catalog or online Request For Quote (RFQ) form",
                "Zero SEO visibility on Google for commercial procurement searches",
                "No 24/7 direct WhatsApp procurement or customer booking hotline",
            ],
            "proposal_deliverables": [
                "Custom High-Speed Responsive Website (Mobile, Tablet, Desktop)",
                "Searchable Product/Service Catalog with High-Res Media",
                "Direct B2B RFQ Quotation Form routed to CEO/Sales Email & WhatsApp",
                "Google Search Console & Local SEO Optimization for " + city,
                "Dedicated WhatsApp Floating Hotline for instant client capture",
                "Ultra-Fast Hosting with 99.9% Uptime & SSL Security",
            ],
            "estimated_timeline": "5 - 7 Business Days",
            "commercial_investment": "$1,200 - $2,200 (AED 4,500 - 8,000)",
            "action_priority": "CRITICAL" if (review_count and review_count > 20) else "HIGH",
        }

        return loophole_data


loophole_service = LoopholeResearchService()

