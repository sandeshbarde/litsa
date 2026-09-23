"""
API Registry & Location Resolution Endpoints.
Exposes integrated API capabilities and global location lookup services.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query
from app.config import settings
from app.services.location_config import get_location_meta, get_all_preset_locations, LocationMeta

router = APIRouter(tags=["apis"])


@router.get("/apis/list")
def list_all_apis():
    """
    Returns a comprehensive catalog of all integrated APIs and system endpoints,
    including authentication status, capabilities, and usage mode.
    """
    return {
        "system": {
            "name": "Global B2B Lead Generator & Outreach Engine",
            "version": "2.0.0",
            "environment": settings.app_env,
            "free_mode": settings.free_mode,
        },
        "apis": [
            {
                "id": "serpapi_maps",
                "name": "SerpApi Google Maps Engine",
                "category": "Discovery & Maps",
                "provider": "SerpApi",
                "active": settings.has_serpapi(),
                "endpoint": "https://serpapi.com/search.json?engine=google_maps",
                "http_methods": ["GET"],
                "description": "Extracts real-time local business listings, coordinates, ratings, and web presence across 200+ countries.",
                "rate_limit": "100-50,000 queries/mo",
                "mode": "Primary Discovery Engine"
            },
            {
                "id": "serpapi_search",
                "name": "SerpApi Google Search Engine",
                "category": "Discovery & Verification",
                "provider": "SerpApi",
                "active": settings.has_serpapi(),
                "endpoint": "https://serpapi.com/search.json?engine=google",
                "http_methods": ["GET"],
                "description": "Performs deep Google organic search queries for website verification, domain discovery, and social media presence audit.",
                "rate_limit": "Included in SerpApi plan",
                "mode": "Verification & Social Audit"
            },
            {
                "id": "apify_maps",
                "name": "Apify Google Maps Scraper",
                "category": "Discovery & Maps",
                "provider": "Apify",
                "active": settings.has_apify(),
                "endpoint": "https://api.apify.com/v2/acts/compass~crawler-google-places/runs",
                "http_methods": ["POST", "GET"],
                "description": "High-volume failover crawler for bulk Google Maps business extraction.",
                "rate_limit": "$5 free credit / mo",
                "mode": "Failover Discovery Engine"
            },
            {
                "id": "snov_io",
                "name": "Snov.io Executive Email Finder",
                "category": "Executive Contact Discovery",
                "provider": "Snov.io",
                "active": bool(settings.snov_user_id and settings.snov_secret),
                "endpoint": "https://api.snov.io/v2/domain-emails-with-info",
                "http_methods": ["POST"],
                "description": "Discovers and verifies direct email addresses for CEOs, Founders, Owners, and Managing Directors.",
                "rate_limit": "50 free credits / mo",
                "mode": "Executive Contact Search"
            },
            {
                "id": "apollo_io",
                "name": "Apollo.io B2B Contact Enrichment",
                "category": "Executive Contact Discovery",
                "provider": "Apollo.io",
                "active": bool(settings.apollo_api_key),
                "endpoint": "https://api.apollo.io/v1/people/match",
                "http_methods": ["POST"],
                "description": "Enriches business records with decision maker names, job titles, LinkedIn profiles, and verified emails.",
                "rate_limit": "10k free credits / mo",
                "mode": "Contact Enrichment & Scoring"
            },
            {
                "id": "zerobounce",
                "name": "ZeroBounce Email Hygiene Shield",
                "category": "Email Verification & Hygiene",
                "provider": "ZeroBounce",
                "active": bool(settings.zerobounce_api_key),
                "endpoint": "https://api.zerobounce.net/v2/validate",
                "http_methods": ["GET"],
                "description": "Validates email deliverability in real-time before sending to eliminate bounces, spam traps, and protect sender score.",
                "rate_limit": "100 free credits / mo",
                "mode": "Domain Deliverability Shield"
            },
            {
                "id": "resend_api",
                "name": "Resend Email API",
                "category": "Cold Outreach Dispatch",
                "provider": "Resend",
                "active": bool(settings.resend_api_key),
                "endpoint": "https://api.resend.com/emails",
                "http_methods": ["POST"],
                "description": "Ultra-reliable HTTPS email delivery service with 99.8% inbox placement rate, bypassing SMTP limits.",
                "rate_limit": "3,000 free emails / mo",
                "mode": "Recommended Primary Dispatcher"
            },
            {
                "id": "gmail_smtp",
                "name": "Google Gmail SMTP Gateway",
                "category": "Cold Outreach Dispatch",
                "provider": "Google Gmail",
                "active": bool(settings.smtp_username and settings.smtp_password),
                "endpoint": "smtp.gmail.com:587",
                "http_methods": ["TLS / SMTP"],
                "description": "Direct 1-on-1 cold email dispatch via authenticated Google App Passwords.",
                "rate_limit": "500 emails / day per account",
                "mode": "SMTP Fallback Gateway"
            },
            {
                "id": "anthropic_claude",
                "name": "Anthropic Claude 3.5 Sonnet AI",
                "category": "AI Forensics & CEO Pitch",
                "provider": "Anthropic",
                "active": bool(settings.anthropic_api_key),
                "endpoint": "https://api.anthropic.com/v1/messages",
                "http_methods": ["POST"],
                "description": "Powers deep company revenue leak analysis, financial turnover estimation, and hyper-personalized CEO pitch writing.",
                "rate_limit": "Pay-per-token API",
                "mode": "Forensic AI Intelligence"
            },
            {
                "id": "google_gemini",
                "name": "Google Gemini 1.5 Pro AI",
                "category": "AI Reasoning & Quality Audit",
                "provider": "Google AI Studio",
                "active": bool(settings.has_gemini() and settings.enable_gemini),
                "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro",
                "http_methods": ["POST"],
                "description": "Analyzes website quality scores, lead qualification nuances, and local market positioning.",
                "rate_limit": "60 requests / min free",
                "mode": "AI Business Audit"
            },
            {
                "id": "global_location_engine",
                "name": "Worldwide Location Engine & Geocoder",
                "category": "Location & Locale",
                "provider": "Internal / OpenStreetMap",
                "active": True,
                "endpoint": "/location/resolve",
                "http_methods": ["GET"],
                "description": "Resolves Cities, States, Provinces, and Countries worldwide (Pune, Bombay, Maharashtra, Gujarat, Dubai, NY, UK) with automatic locale mapping.",
                "rate_limit": "Unlimited",
                "mode": "Worldwide Location Support"
            }
        ],
        "fastapi_endpoints": [
            {"path": "/health", "method": "GET", "summary": "System health and feature flags"},
            {"path": "/stats", "method": "GET", "summary": "Dashboard counts and daily API usage statistics"},
            {"path": "/jobs/start", "method": "POST", "summary": "Launch background discovery job for any city/state/country"},
            {"path": "/jobs", "method": "GET", "summary": "List running and completed search jobs"},
            {"path": "/leads", "method": "GET", "summary": "List qualified leads with city, state, country, score, and priority filters"},
            {"path": "/leads/{id}", "method": "GET", "summary": "Get full business record detail"},
            {"path": "/leads/{id}/verify", "method": "POST", "summary": "Re-run website verification and rescore lead"},
            {"path": "/leads/{id}/find-ceo", "method": "POST", "summary": "Locate CEO name, title, and verified email"},
            {"path": "/leads/{id}/generate-pitch", "method": "POST", "summary": "Generate personalized multi-step CEO outreach pitch"},
            {"path": "/leads/{id}/send-email", "method": "POST", "summary": "Dispatch email directly to CEO"},
            {"path": "/leads/{id}/website-preview", "method": "GET", "summary": "Generate live personal prototype website mockup"},
            {"path": "/leads/{id}/loophole-research", "method": "GET", "summary": "Generate forensic loophole dossier"},
            {"path": "/leads/automation/dispatch-all", "method": "POST", "summary": "100% Hands-free Autopilot CEO outreach dispatcher"},
            {"path": "/location/resolve", "method": "GET", "summary": "Resolve any city, state, or country worldwide into full metadata"},
            {"path": "/location/presets", "method": "GET", "summary": "List categorized world location presets (India, Middle East, USA, UK)"},
            {"path": "/apis/list", "method": "GET", "summary": "List all integrated APIs and internal endpoints"}
        ]
    }


@router.get("/location/resolve")
def resolve_location(q: str = Query(..., description="City, State, or Country (e.g. Pune, Bombay, Maharashtra, Gujarat, Dubai)")):
    """
    Resolve any location query (City, State, or Country) into complete metadata,
    ISO country code, Google `gl` parameter, and recommended district areas.
    """
    meta = get_location_meta(q)
    return meta.model_dump() if hasattr(meta, "model_dump") else meta.dict()


@router.get("/location/presets")
def list_location_presets():
    """
    Returns categorized world location presets for Cities, States, and Countries.
    """
    return get_all_preset_locations()
