"""
Claude (Anthropic) AI service for executive forensic analysis and CEO pitch generation.
Supports Claude 3.5 Sonnet / Claude 3 Haiku.
Active when ANTHROPIC_API_KEY is configured.
"""

import json
from typing import Optional, Dict, Any
from loguru import logger

from app.config import settings


class ClaudeService:
    """Uses Anthropic Claude to conduct company loophole analysis and write tailored CEO pitches."""

    def __init__(self, api_key: Optional[str] = None):
        if api_key is not None:
            self.api_key = api_key.strip()
            self._explicit_key = True
        else:
            self.api_key = (getattr(settings, "anthropic_api_key", None) or "").strip()
            self._explicit_key = False
        self._client = None
        self._initialized = False

    def is_active(self) -> bool:
        key = self.api_key or ""
        return bool(key and key.strip() and not key.startswith("YOUR_") and "..." not in key)

    def _get_client(self):
        if not self._initialized:
            self._initialized = True
            key = self.api_key if self._explicit_key else (self.api_key or getattr(settings, "anthropic_api_key", None) or "")
            if key and not key.startswith("YOUR_") and "..." not in key:
                try:
                    import anthropic
                    self._client = anthropic.Anthropic(api_key=key.strip())
                    logger.info("Claude Anthropic client initialized successfully.")
                except Exception as exc:
                    logger.error(f"Failed to initialize Anthropic client: {exc}")
                    self._client = None
        return self._client

    def analyze_lead(
        self,
        business_name: str,
        category: str,
        city: str = "Dubai",
        website_status: str = "missing",
        review_count: Optional[int] = None,
        description: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Conduct deep forensic analysis on why this business is losing revenue without a website.
        Returns structured JSON with loophole, estimated revenue loss, and recommended strategy.
        """
        client = self._get_client()
        if not client:
            return None

        prompt = (
            f"You are an elite B2B Commercial Analyst specializing in SMEs and wholesale businesses in {city}.\n"
            f"Analyze this business that currently has NO official website:\n\n"
            f"Business: {business_name}\n"
            f"Industry: {category}\n"
            f"City / Location: {city}\n"
            f"Google Reviews: {review_count or 'Limited'}\n"
            f"Notes: {description or 'B2B/Wholesale trading entity'}\n\n"
            f"Respond ONLY with valid JSON in this exact structure:\n"
            f"{{\n"
            f'  "website_quality": "missing",\n'
            f'  "business_relevance": "high",\n'
            f'  "primary_loophole": "Clear commercial bottleneck (e.g. Missing digital procurement RFQ catalog)",\n'
            f'  "estimated_revenue_leak": "$25,000 - $80,000 annually",\n'
            f'  "reason": "Concise summary of their competitive risk",\n'
            f'  "pitch_angle": "Direct value proposition to pitch the CEO / Founder"\n'
            f"}}"
        )

        try:
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            text = message.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text)
        except Exception as exc:
            logger.error(f"Claude analyze_lead failed for {business_name}: {exc}")
            return None

    def generate_ceo_pitch(
        self,
        business_name: str,
        ceo_name: Optional[str] = None,
        category: str = "Wholesale & Trade",
        city: str = "Dubai",
        loophole: Optional[str] = None,
        demo_url: Optional[str] = None,
        language: str = "en",
    ) -> str:
        """
        Generate a hyper-personalized, high-converting cold email tailored directly to the CEO/Owner.
        Embeds developer credentials and live demo prototype link.
        """
        client = self._get_client()
        salutation = f"Dear {ceo_name}," if ceo_name and ceo_name != "CEO / Owner" else f"Dear {business_name} Leadership,"
        loophole_str = loophole or "losing direct procurement RFQ inquiries to digital-first competitors"
        demo_line = f"Live Interactive Prototype Prepared For You: {demo_url}" if demo_url else ""

        if not client:
            return (
                f"{salutation}\n\n"
                f"While reviewing commercial suppliers in {city}, our audit noticed that {business_name} operates without an official digital procurement portal. "
                f"Competitors in your category ({category}) are currently capturing search RFQ volumes that should be converting directly to your desk.\n\n"
                f"We took the initiative to build a private, live interactive prototype showing how your product catalog, direct quotation engine, and B2B ordering hotline would function:\n"
                f"👉 {demo_url or 'https://sandeshbarde.netlify.app/'}\n\n"
                f"Let's schedule a 5-minute preview call this week.\n\n"
                f"Best regards,\n"
                f"Sandesh Barde\n"
                f"Full-Stack Web Architect (India)\n"
                f"Portfolio: https://sandeshbarde.netlify.app/\n"
                f"GitHub: https://github.com/sandeshbarde\n"
                f"LinkedIn: https://www.linkedin.com/in/sandesh-barde-26ba3839b/"
            )

        from app.services.hot_training import hot_training_service
        hot_prefix = hot_training_service.build_hot_prompt_prefix()

        prompt = (
            f"{hot_prefix}\n\n"
            f"You are drafting a high-stakes, respectful, professional B2B cold email to a CEO/Owner.\n"
            f"Target: {business_name} ({category} in {city})\n"
            f"CEO / Decision Maker: {ceo_name or 'Managing Director'}\n"
            f"Identified Loophole: {loophole_str}\n"
            f"Live Demo Website Link: {demo_url or ''}\n"
            f"Language: {language} (en=English, ar=Arabic, hi=Hindi)\n"
            f"Developer Credentials to embed at the end:\n"
            f"- Name: Sandesh Barde (Full-Stack Web Architect based in India)\n"
            f"- Portfolio: https://sandeshbarde.netlify.app/\n"
            f"- GitHub: https://github.com/sandeshbarde\n"
            f"- LinkedIn: https://www.linkedin.com/in/sandesh-barde-26ba3839b/\n\n"
            f"Rules:\n"
            f"1. Target only the CEO/Owner directly. Do NOT talk to managers or junior staff.\n"
            f"2. Point out the exact commercial loophole: {loophole_str}.\n"
            f"3. Highlight that we built a working prototype specifically for {business_name}.\n"
            f"4. Keep it crisp, authoritative, under 130 words.\n"
            f"5. End with Sandesh Barde's credentials exactly as provided.\n"
            f"Return only the email body text without subject line."
        )

        try:
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=350,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text.strip()
        except Exception as exc:
            if "credit balance is too low" in str(exc).lower():
                logger.warning("Anthropic Claude API key is authenticated, but account credit balance is too low. Please top up at console.anthropic.com/settings/billing. Falling back gracefully.")
            else:
                logger.error(f"Claude generate_ceo_pitch failed for {business_name}: {exc}")

            if settings.has_gemini():
                try:
                    from app.services.gemini_service import GeminiService
                    gemini = GeminiService()
                    gem_pitch = gemini.generate_pitch(
                        business_name=business_name,
                        category=category,
                        area=city,
                        pitch_angle=loophole,
                        sender_name="Sandesh Barde",
                    )
                    if gem_pitch and len(gem_pitch) > 40 and business_name in gem_pitch:
                        return (
                            f"{gem_pitch}\n\n"
                            f"👉 Live Prototype Demo: {demo_url or 'https://sandeshbarde.netlify.app/'}\n\n"
                            f"Best regards,\n"
                            f"Sandesh Barde\n"
                            f"Full-Stack Web Architect (India)\n"
                            f"Portfolio: https://sandeshbarde.netlify.app/\n"
                            f"GitHub: https://github.com/sandeshbarde\n"
                            f"LinkedIn: https://www.linkedin.com/in/sandesh-barde-26ba3839b/"
                        )
                except Exception:
                    pass

            return (
                f"{salutation}\n\n"
                f"While reviewing commercial suppliers in {city}, our audit noticed that {business_name} operates without an official digital procurement portal. "
                f"Competitors in your category ({category}) are currently capturing search RFQ volumes that should be converting directly to your desk.\n\n"
                f"We took the initiative to build a private, live interactive prototype showing how your product catalog, direct quotation engine, and B2B ordering hotline would function:\n"
                f"👉 {demo_url or 'https://sandeshbarde.netlify.app/'}\n\n"
                f"Best regards,\n"
                f"Sandesh Barde\n"
                f"Full-Stack Web Architect (India)\n"
                f"Portfolio: https://sandeshbarde.netlify.app/\n"
                f"GitHub: https://github.com/sandeshbarde\n"
                f"LinkedIn: https://www.linkedin.com/in/sandesh-barde-26ba3839b/"
            )


claude_service = ClaudeService()
