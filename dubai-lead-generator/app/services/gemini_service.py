"""
Gemini AI service for lead classification and high-converting CEO pitch generation.
Uses Google Gemini 3.6 Flash via REST API with hot-training exemplar integration.
Active when ENABLE_GEMINI=true and GEMINI_API_KEY is set.
"""

import json
from typing import Optional, Dict, Any
import requests
from loguru import logger

from app.config import settings


class GeminiService:
    """Uses Gemini 3.6 Flash to classify leads and generate personalized outreach drafts."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    MODEL = "gemini-3.6-flash"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or settings.gemini_api_key or "").strip()

    def is_active(self) -> bool:
        """Check if Gemini API key is validly configured."""
        key = self.api_key or settings.gemini_api_key or ""
        return bool(key and not key.startswith("YOUR_") and len(key) > 20)

    def _call_gemini(self, prompt: str, timeout: int = 15) -> Optional[str]:
        """Execute text generation request against Gemini 3.6 Flash."""
        key = self.api_key or settings.gemini_api_key or ""
        if not key or key.startswith("YOUR_"):
            return None

        url = f"{self.BASE_URL}/{self.MODEL}:generateContent?key={key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 450,
            }
        }

        try:
            resp = requests.post(url, json=payload, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
            else:
                logger.error(f"Gemini API returned status {resp.status_code}: {resp.text[:200]}")
                return None
        except Exception as exc:
            logger.error(f"Gemini request failed: {exc}")
            return None

    def analyze_lead(
        self,
        business_name: str,
        category: str,
        area: str,
        website_status: str,
        review_count: Optional[int] = None,
        has_social: bool = False,
        description: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Classify a business lead and provide loophole analysis.
        Returns structured output dict or None if unavailable.
        """
        if not self.is_active():
            return None

        prompt = (
            f"You are a B2B commercial web strategist.\n"
            f"Analyze this business that currently has NO website:\n\n"
            f"Business Name: {business_name}\n"
            f"Category: {category}\n"
            f"Area / City: {area}\n"
            f"Website Status: {website_status}\n"
            f"Google Reviews: {review_count or 'Limited'}\n"
            f"Description: {description or 'Commercial enterprise'}\n\n"
            f"Respond with valid JSON only in this exact structure:\n"
            f"{{\n"
            f'  "website_quality": "missing",\n'
            f'  "business_relevance": "high",\n'
            f'  "primary_loophole": "One sentence describing their digital vulnerability",\n'
            f'  "reason": "One sentence explanation of why they lose deals without a website",\n'
            f'  "pitch_angle": "Best value proposition for the CEO"\n'
            f"}}\n"
            f"Respond with valid JSON only, no markdown, no extra text."
        )

        text = self._call_gemini(prompt)
        if not text:
            return None

        try:
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text.strip())
        except Exception as exc:
            logger.warning(f"Failed to parse Gemini JSON output: {exc}")
            return None

    def generate_pitch(
        self,
        business_name: str,
        category: str,
        area: str,
        pitch_angle: Optional[str] = None,
        sender_name: str = "Sandesh Barde",
    ) -> str:
        """
        Generate a personalized, high-converting outreach draft using Gemini 3.6 Flash.
        Includes Hot Training exemplars and Sandesh Barde credentials.
        """
        if not self.is_active():
            return self._default_pitch(business_name, sender_name)

        try:
            from app.services.hot_training import hot_training_service
            hot_prefix = hot_training_service.build_hot_prompt_prefix()
        except Exception:
            hot_prefix = ""

        angle_hint = pitch_angle or "losing high-ticket B2B procurement inquiries to competitors with digital quotation portals"
        prompt = (
            f"{hot_prefix}\n\n"
            f"Write a concise, high-converting B2B cold email from Web Architect Sandesh Barde reaching out to the CEO of {business_name}.\n\n"
            f"Business: {business_name}\n"
            f"Industry: {category}\n"
            f"Location: {area}\n"
            f"Identified Loophole: {angle_hint}\n"
            f"Sender: {sender_name} (Full-Stack Web Architect, India)\n\n"
            f"Requirements:\n"
            f"- Under 120 words\n"
            f"- Authoritative, ROI-focused tone directly addressing the CEO/Owner\n"
            f"- Highlight that a private live working prototype website has been built for them\n"
            f"- Include portfolio: https://sandeshbarde.netlify.app/\n"
            f"- Include GitHub: https://github.com/sandeshbarde\n"
            f"- Include LinkedIn: https://www.linkedin.com/in/sandesh-barde-26ba3839b/\n"
            f"- End with Best regards, {sender_name}\n"
            f"- Return ONLY the email body text without subject line."
        )

        pitch = self._call_gemini(prompt)
        if pitch and len(pitch) > 40:
            return pitch

        return self._default_pitch(business_name, sender_name)

    @staticmethod
    def _default_pitch(business_name: str, sender_name: str = "Sandesh Barde") -> str:
        """Fallback pitch template when Gemini is unavailable."""
        return (
            f"Dear Leadership at {business_name},\n\n"
            f"While auditing commercial suppliers in your region, we noticed that {business_name} operates without an official digital procurement portal. "
            f"Competitors in your industry are capturing high-margin inquiries that should be converting directly to your desk.\n\n"
            f"We took the initiative to build a private, live interactive prototype showing your catalog, direct quotation RFQ engine, and B2B hotline:\n"
            f"👉 Live Concept: https://sandeshbarde.netlify.app/\n\n"
            f"Let's schedule a 5-minute call this week to review it.\n\n"
            f"Best regards,\n"
            f"{sender_name}\n"
            f"Full-Stack Web Architect (India)\n"
            f"Portfolio: https://sandeshbarde.netlify.app/\n"
            f"GitHub: https://github.com/sandeshbarde\n"
            f"LinkedIn: https://www.linkedin.com/in/sandesh-barde-26ba3839b/"
        )


gemini_service = GeminiService()
