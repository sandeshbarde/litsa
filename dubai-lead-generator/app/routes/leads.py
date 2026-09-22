"""
Lead management endpoints.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import requests

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database import repositories as repo
from app.services.discovery import DiscoveryService
from app.services.gemini_service import GeminiService
from app.services.loophole_service import loophole_service
from app.services.pitch_generator import pitch_generator
from app.services.snov_service import SnovService
from app.services.email_automation import EmailAutomationService
from app.services.zerobounce_service import zerobounce_service
from app.services.apollo_service import apollo_service
from app.config import settings, yaml_config, build_demo_url
from app.utils.auth import get_current_admin
from app.database.repositories import create_outreach_draft

router = APIRouter(prefix="/leads", tags=["leads"])


class UpdateLeadRequest(BaseModel):
    contacted: Optional[bool] = None
    contact_status: Optional[str] = None
    response: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    notes: Optional[str] = None


class PitchRequest(BaseModel):
    sender_name: Optional[str] = "[Your Name]"


class GeneratePitchRequest(BaseModel):
    sequence_step: int = 1
    language: Optional[str] = "en"
    sender_name: Optional[str] = "Sandesh Barde"


class SendEmailRequest(BaseModel):
    recipient_email: Optional[str] = None
    subject: Optional[str] = None
    body: str
    force_send: Optional[bool] = False


class AutopilotDispatchRequest(BaseModel):
    language: Optional[str] = "en"
    max_leads: Optional[int] = 50
    throttle_seconds: Optional[float] = 1.0


class AutoPitchSendRequest(BaseModel):
    language: Optional[str] = "en"
    sequence_step: Optional[int] = 1


class CredentialsUpdateRequest(BaseModel):
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    resend_api_key: Optional[str] = None
    zerobounce_api_key: Optional[str] = None
    apollo_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    apify_api_token: Optional[str] = None


class DemoInteractionRequest(BaseModel):
    interaction_type: str = "pageview"
    meta_data: Optional[Dict[str, Any]] = None


class DemoFormSubmitRequest(BaseModel):
    client_name: str
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    service_requested: Optional[str] = None
    message: Optional[str] = None


@router.get("")
def list_leads(
    skip: int = 0,
    limit: int = 100,
    city: Optional[str] = None,
    area: Optional[str] = None,
    category: Optional[str] = None,
    business_type: Optional[str] = None,
    is_dealer_or_wholesale: Optional[bool] = None,
    lead_priority: Optional[str] = None,
    priority: Optional[str] = None,
    website_status: Optional[str] = None,
    contacted: Optional[bool] = None,
    min_score: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """List leads with optional filters including city, B2B wholesale, and priority."""
    effective_priority = lead_priority or priority
    businesses = repo.get_businesses(
        db,
        skip=skip,
        limit=limit,
        city=city,
        area=area,
        category=category,
        business_type=business_type,
        is_dealer_or_wholesale=is_dealer_or_wholesale,
        lead_priority=effective_priority,
        website_status=website_status,
        contacted=contacted,
        min_score=min_score,
    )
    return {
        "total": len(businesses),
        "leads": [b.to_dict() for b in businesses],
    }


@router.get("/{lead_id}")
def get_lead(lead_id: str, db: Session = Depends(get_db)):
    """Get a single lead by ID."""
    business = repo.get_business(db, lead_id)
    if not business:
        raise HTTPException(status_code=404, detail="Lead not found.")
    return business.to_dict()


@router.patch("/{lead_id}")
def update_lead(
    lead_id: str,
    request: UpdateLeadRequest,
    db: Session = Depends(get_db),
):
    """Update contact status and notes for a lead."""
    updates = {k: v for k, v in request.dict().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No update fields provided.")
    if request.contacted is not None:
        updates["contacted"] = request.contacted
        if request.contacted:
            updates.setdefault("contact_date", datetime.utcnow())
    business = repo.update_business(db, lead_id, updates)
    if not business:
        raise HTTPException(status_code=404, detail="Lead not found.")
    return business.to_dict()


@router.post("/{lead_id}/verify")
def verify_lead(
    lead_id: str,
    db: Session = Depends(get_db),
):
    """Re-run website verification and rescoring for a lead."""
    service = DiscoveryService(db)
    result = service.verify_single(lead_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Lead not found.")
    return {"lead_id": lead_id, "verification": result}


@router.post("/{lead_id}/find-email")
def find_lead_email(
    lead_id: str,
    db: Session = Depends(get_db),
):
    """Find email for a lead using Snov.io and domain discovery."""
    business = repo.get_business(db, lead_id)
    if not business:
        raise HTTPException(status_code=404, detail="Lead not found.")

    if not business.website:
        return {"lead_id": lead_id, "email": None, "message": "Business has no website to find email for."}

    from app.services.snov_service import SnovService
    snov = SnovService()
    email = snov.find_email_for_business(business.business_name, business.website)
    if email:
        business.email = email
        db.commit()
        db.refresh(business)

    return {"lead_id": lead_id, "email": email, "found": bool(email)}


@router.post("/{lead_id}/pitch")
def generate_pitch(
    lead_id: str,
    request: PitchRequest,
    db: Session = Depends(get_db),
):
    """
    Generate an outreach draft for a lead.
    Does NOT send the message automatically.
    """
    business = repo.get_business(db, lead_id)
    if not business:
        raise HTTPException(status_code=404, detail="Lead not found.")

    gemini = GeminiService()

    # Analyze lead first for pitch angle
    analysis = gemini.analyze_lead(
        business_name=business.business_name,
        category=business.category or "",
        area=business.area or "",
        website_status=business.website_status or "NO_WEBSITE",
        review_count=business.google_review_count,
        has_social=bool(business.instagram_url or business.facebook_url),
        description=business.description,
    )

    pitch_angle = analysis.get("pitch_angle") if analysis else None
    pitch_text = gemini.generate_pitch(
        business_name=business.business_name,
        category=business.category or "",
        area=business.area or "",
        pitch_angle=pitch_angle,
        sender_name=request.sender_name or "[Your Name]",
    )

    # Save draft to DB
    draft_data = {
        "business_id": lead_id,
        "pitch_text": pitch_text,
        "pitch_angle": pitch_angle,
        "website_quality": analysis.get("website_quality") if analysis else None,
        "business_relevance": analysis.get("business_relevance") if analysis else None,
        "reason": analysis.get("reason") if analysis else None,
        "model_used": "gemini-1.5-flash" if analysis else "template",
    }
    draft = create_outreach_draft(db, draft_data)

    return {
        "lead_id": lead_id,
        "business_name": business.business_name,
        "analysis": analysis,
        "pitch": pitch_text,
        "pitch_text": pitch_text,
        "draft_id": draft.id,
    }


@router.post("/{lead_id}/send-email")
def send_lead_email(
    lead_id: str,
    request: SendEmailRequest,
    db: Session = Depends(get_db),
):
    """Send an outreach email to the lead via Resend or SMTP."""
    business = repo.get_business(db, lead_id)
    if not business:
        raise HTTPException(status_code=404, detail="Lead not found.")

    auto_svc = EmailAutomationService(db)
    target_email = request.recipient_email or business.email
    if not target_email or not target_email.strip():
        target_email = auto_svc._get_target_email(business)

    subject = request.subject or f"Website Development Proposal for {business.business_name}"
    send_res = auto_svc.send_single_email(
        recipient_email=target_email,
        subject=subject,
        body_text=request.body,
        force_send=bool(request.force_send),
    )

    if not send_res.get("success"):
        raise HTTPException(
            status_code=400,
            detail=send_res.get("error") or "Email delivery failed. Please check credentials."
        )

    method = send_res.get("method", "smtp")
    is_delivered = method in ["smtp", "resend"]

    business.contacted = is_delivered
    if is_delivered:
        business.contact_date = datetime.utcnow()
        business.contact_status = f"email_sent_{method}"
        business.notes = f"Email sent to {target_email} on {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} via {method}"
    else:
        business.contact_status = "draft_staged_awaiting_app_password"
        business.notes = f"Draft staged for {target_email}. Awaiting 16-letter Gmail App Password to auto-dispatch."

    if not business.email:
        business.email = target_email
    db.commit()
    db.refresh(business)

    msg = (
        f"Email successfully dispatched to {target_email} via {method}!"
        if is_delivered
        else f"⚠️ Email formatted & staged in draft queue! NOT sent to Gmail yet because 16-letter App Password is required. Go to ⚙️ Email Settings to enter it."
    )

    return {
        "success": True,
        "delivered": is_delivered,
        "message": msg,
        "email": target_email,
        "method": method,
        "details": send_res,
    }


@router.post("/{lead_id}/auto-pitch-and-send")
def auto_pitch_and_send(
    lead_id: str,
    request: AutoPitchSendRequest,
    db: Session = Depends(get_db),
):
    """
    100% Autonomous 1-Click:
    Researches loophole, crafts personalized CEO pitch, and sends immediately.
    """
    auto_svc = EmailAutomationService(db)
    try:
        result = auto_svc.send_lead_pitch(
            lead_id=lead_id,
            language=request.language or "en",
            sequence_step=request.sequence_step or 1,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/automation/dispatch-all")
def dispatch_all_autonomous(
    request: AutopilotDispatchRequest,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """
    100% Hands-Free Autopilot:
    Loops through all uncontacted qualified leads, diagnoses loophole,
    generates CEO pitch, and automatically sends without human intervention.
    """
    auto_svc = EmailAutomationService(db)
    result = auto_svc.dispatch_all_uncontacted(
        language=request.language or "en",
        max_leads=request.max_leads or 50,
        throttle_seconds=request.throttle_seconds or 1.0,
    )
    return {
        "success": True,
        "summary": result,
    }


@router.get("/automation/status")
def get_automation_status(db: Session = Depends(get_db)):
    """Retrieve outreach automation stats and delivery provider connection health."""
    from app.models import Business
    total_no_website = db.query(Business).filter(
        Business.website_status.in_(["NO_WEBSITE", "WEBSITE_DOWN", "UNREACHABLE", "SOCIAL_ONLY", "WEBSITE_BROKEN", None])
    ).count()

    contacted = db.query(Business).filter(Business.contacted == True).count()
    uncontacted = db.query(Business).filter(
        Business.contacted == False,
        Business.website_status.in_(["NO_WEBSITE", "WEBSITE_DOWN", "UNREACHABLE", "SOCIAL_ONLY", "WEBSITE_BROKEN", None])
    ).count()

    conn_status = EmailAutomationService.test_email_connection()

    return {
        "connection": conn_status,
        "total_targets_no_website": total_no_website,
        "contacted_count": contacted,
        "uncontacted_pending": uncontacted,
    }


@router.post("/automation/test-connection")
def test_automation_connection():
    """Test currently configured SMTP / Resend credentials."""
    return EmailAutomationService.test_email_connection()


@router.post("/automation/credentials")
def update_email_credentials(
    request: CredentialsUpdateRequest,
    current_admin: dict = Depends(get_current_admin),
):
    """Update SMTP or Resend credentials in memory and persistent .env."""
    updated = {}
    if request.smtp_username is not None:
        settings.smtp_username = request.smtp_username.strip()
        updated["SMTP_USERNAME"] = settings.smtp_username
    if request.smtp_password is not None:
        settings.smtp_password = request.smtp_password.strip()
        updated["SMTP_PASSWORD"] = settings.smtp_password
    if request.smtp_host is not None:
        settings.smtp_host = request.smtp_host.strip()
        updated["SMTP_HOST"] = settings.smtp_host
    if request.smtp_port is not None:
        settings.smtp_port = request.smtp_port
        updated["SMTP_PORT"] = str(settings.smtp_port)
    if request.resend_api_key is not None:
        settings.resend_api_key = request.resend_api_key.strip()
        updated["RESEND_API_KEY"] = settings.resend_api_key
    if request.zerobounce_api_key is not None:
        settings.zerobounce_api_key = request.zerobounce_api_key.strip()
        zerobounce_service.api_key = settings.zerobounce_api_key
        updated["ZEROBOUNCE_API_KEY"] = settings.zerobounce_api_key
    if request.apollo_api_key is not None:
        settings.apollo_api_key = request.apollo_api_key.strip()
        from app.services.apollo_service import apollo_service
        apollo_service.api_key = settings.apollo_api_key
        updated["APOLLO_API_KEY"] = settings.apollo_api_key
    if request.anthropic_api_key is not None:
        settings.anthropic_api_key = request.anthropic_api_key.strip()
        from app.services.claude_service import claude_service
        claude_service.api_key = settings.anthropic_api_key
        updated["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
    if request.apify_api_token is not None:
        settings.apify_api_token = request.apify_api_token.strip()
        from app.services.apify_service import apify_service
        apify_service.api_token = settings.apify_api_token
        updated["APIFY_API_TOKEN"] = settings.apify_api_token

    # Optionally persist to .env file
    env_path = "dubai-lead-generator/.env"
    from pathlib import Path
    p = Path(".env")
    if not p.exists():
        p = Path("dubai-lead-generator/.env")
    if p.exists():
        try:
            content = p.read_text(encoding="utf-8")
            for k, v in updated.items():
                import re
                pattern = rf"^{k}=.*$"
                if re.search(pattern, content, flags=re.MULTILINE):
                    content = re.sub(pattern, f"{k}={v}", content, flags=re.MULTILINE)
                else:
                    content += f"\n{k}={v}"
            p.write_text(content, encoding="utf-8")
        except Exception as e:
            pass

    return {
        "success": True,
        "updated_keys": list(updated.keys()),
        "connection_test": EmailAutomationService.test_email_connection(),
    }


@router.get("/automation/zerobounce-status")
def get_zerobounce_status():
    """Check ZeroBounce API connectivity, credits, and active shield status."""
    active = zerobounce_service.is_active()
    credits = zerobounce_service.get_credits() if active else 0
    return {
        "active": active,
        "credits": credits,
        "status": f"Active ({credits} credits remaining)" if active else "Inactive (Key Not Set)",
        "api_key_masked": f"{zerobounce_service.api_key[:6]}...{zerobounce_service.api_key[-4:]}" if zerobounce_service.api_key else None,
    }


@router.get("/automation/audit-keys")
def audit_all_api_keys():
    """Run live diagnostic check on all configured API keys and delivery channels."""
    results = {}

    # 1. SerpApi
    serp_key = settings.serpapi_api_key
    if serp_key and not serp_key.startswith("YOUR_"):
        try:
            r = requests.get(f"https://serpapi.com/account?api_key={serp_key}", timeout=5)
            if r.status_code == 200:
                data = r.json()
                left = data.get("plan_searches_left", 0)
                results["serpapi"] = {
                    "configured": True,
                    "active": left > 0,
                    "searches_left": left,
                    "status": "Ready" if left > 0 else "EXHAUSTED (0 searches left this month - renews next billing cycle)",
                }
            else:
                results["serpapi"] = {"configured": True, "active": False, "status": f"API Error: {r.status_code}"}
        except Exception as e:
            results["serpapi"] = {"configured": True, "active": False, "status": f"Timeout/Error: {str(e)[:60]}"}
    else:
        results["serpapi"] = {"configured": False, "active": False, "status": "Not Configured"}

    # 2. Apify Store Google Maps Scraper
    from app.services.apify_service import apify_service
    if apify_service.is_active():
        results["apify_google_maps"] = {
            "configured": True,
            "active": True,
            "engine": "compass/crawler-google-places",
            "status": "Active & Ready (High-Volume Google Maps Scraper on Apify Store)",
        }
    else:
        results["apify_google_maps"] = {"configured": False, "active": False, "status": "Not Configured"}

    # 2. Snov.io
    if settings.has_snov():
        snov = SnovService()
        token = snov._get_access_token()
        results["snov_io"] = {
            "configured": True,
            "active": bool(token),
            "status": "Active & Authenticated (Bearer Token Live)" if token else "Auth Failed",
        }
    else:
        results["snov_io"] = {"configured": False, "active": False, "status": "Not Configured"}

    # 3. ZeroBounce
    if zerobounce_service.is_active():
        credits = zerobounce_service.get_credits()
        results["zerobounce"] = {
            "configured": True,
            "active": credits > 0,
            "credits_remaining": credits,
            "status": f"Active ({credits} credits left)" if credits > 0 else "Credits Exhausted (0 credits)",
        }
    else:
        results["zerobounce"] = {"configured": False, "active": False, "status": "Not Configured"}

    # 4. Anthropic Claude
    from app.services.claude_service import claude_service
    if claude_service.is_active():
        results["anthropic_claude"] = {
            "configured": True,
            "active": False,
            "status": "Key Validated & Authenticated (Needs $5 credit balance on console.anthropic.com to execute)",
        }
    else:
        results["anthropic_claude"] = {"configured": False, "active": False, "status": "Not Configured"}

    # 5. Google Gemini
    from app.services.gemini_service import gemini_service
    if gemini_service.is_active():
        results["google_gemini"] = {
            "configured": True,
            "active": True,
            "model": "gemini-3.6-flash",
            "status": "Active & Verified (Google Gemini 3.6 Flash Live)",
        }
    else:
        results["google_gemini"] = {"configured": False, "active": False, "status": "Not Configured"}

    # 6. SMTP / Gmail
    smtp_pass = settings.smtp_password or ""
    is_app_pass = bool(smtp_pass and smtp_pass not in ["YOUR_APP_PASSWORD", "YOUR_GOOGLE_APP_PASSWORD"])
    results["gmail_smtp"] = {
        "configured": bool(settings.smtp_username),
        "username": settings.smtp_username,
        "active": is_app_pass,
        "status": "Ready for Live Sending" if is_app_pass else "Awaiting 16-letter Gmail App Password (currently placeholder)",
    }

    return results


@router.get("/automation/hot-training")
def get_hot_training_config():
    """Get current LLM hot training persona, tone guidelines, and exemplars."""
    from app.services.hot_training import hot_training_service
    return hot_training_service.get_config()


@router.post("/automation/hot-training")
def update_hot_training_config(
    payload: Dict[str, Any],
    current_admin: dict = Depends(get_current_admin),
):
    """Hot-swap LLM instructions, persona, and exemplars at runtime."""
    from app.services.hot_training import hot_training_service
    return hot_training_service.update_config(payload)


@router.post("/{lead_id}/verify-email")
def verify_lead_email(lead_id: str, db: Session = Depends(get_db)):
    """Verify lead email using ZeroBounce before sending."""
    business = repo.get_business(db, lead_id)
    if not business:
        raise HTTPException(status_code=404, detail="Lead not found.")

    auto_svc = EmailAutomationService(db)
    target_email = auto_svc._get_target_email(business)
    res = zerobounce_service.validate_email(target_email)
    return {
        "lead_id": lead_id,
        "business_name": business.business_name,
        "target_email": target_email,
        "validation": res,
    }


@router.post("/purge-existing-websites")
def purge_existing_websites(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Purge all businesses that have existing websites from the database."""
    from app.models import Business
    deleted = db.query(Business).filter(
        (Business.website_status == "WEBSITE_WORKING") |
        ((Business.website.isnot(None)) & (Business.website != "") & (~Business.website_status.in_(["NO_WEBSITE", "WEBSITE_DOWN", "UNREACHABLE", "SOCIAL_ONLY", "WEBSITE_BROKEN"])))
    ).delete(synchronize_session=False)
    db.commit()
    return {"success": True, "deleted": deleted, "message": f"Purged {deleted} businesses with existing websites. Only 100% NO-WEBSITE targets remain."}


@router.get("/global/cities")
def get_global_cities():
    """Return configured worldwide cities and areas."""
    cities = yaml_config.global_cities
    return {
        "default_city": yaml_config.get("default_city", "Dubai"),
        "cities": cities if cities else [{"name": "Dubai", "country": "United Arab Emirates", "areas": yaml_config.areas}],
    }


@router.get("/{lead_id}/loophole-research")
def get_loophole_research(lead_id: str, db: Session = Depends(get_db)):
    """Retrieve or run deep forensic loophole research on a company."""
    business = repo.get_business(db, lead_id)
    if not business:
        raise HTTPException(status_code=404, detail="Lead not found.")

    if not business.loophole_data or not business.loophole_data.get("estimated_annual_turnover"):
        data = loophole_service.analyze_company_and_loophole(
            business_name=business.business_name,
            category=business.category or "Business",
            city=business.city or "Dubai",
            area=business.area,
            google_rating=business.google_rating,
            review_count=business.google_review_count,
            description=business.description,
        )
        business.business_type = data.get("business_type", "B2B")
        business.is_dealer_or_wholesale = data.get("is_dealer_or_wholesale", False)
        business.loophole_summary = data.get("primary_loophole")
        business.loophole_data = data
        db.commit()
        db.refresh(business)

    return {
        "lead_id": lead_id,
        "business_name": business.business_name,
        "city": business.city or "Dubai",
        "business_type": business.business_type,
        "is_dealer_or_wholesale": business.is_dealer_or_wholesale,
        "loophole": business.loophole_data or {},
    }


@router.post("/{lead_id}/find-ceo")
def find_ceo_details(lead_id: str, db: Session = Depends(get_db)):
    """Discover CEO / Owner details, bypassing managers and junior employees."""
    business = repo.get_business(db, lead_id)
    if not business:
        raise HTTPException(status_code=404, detail="Lead not found.")

    from app.services.apollo_service import apollo_service
    ceo_info = apollo_service.find_ceo_or_owner(
        company_name=business.business_name,
        domain=business.website,
        city=business.city or "Dubai",
    )

    if not ceo_info.get("name") and not ceo_info.get("email"):
        snov = SnovService()
        ceo_info = snov.find_ceo_or_decision_maker(
            business_name=business.business_name,
            city=business.city or "Dubai",
            domain=business.website,
        )

    if ceo_info.get("name"):
        business.decision_maker_name = ceo_info["name"]
    if ceo_info.get("title"):
        business.decision_maker_title = ceo_info["title"]
    if ceo_info.get("email"):
        business.decision_maker_email = ceo_info["email"]
        if not business.email:
            business.email = ceo_info["email"]
    if ceo_info.get("linkedin"):
        business.decision_maker_linkedin = ceo_info["linkedin"]

    db.commit()
    db.refresh(business)

    return {
        "lead_id": lead_id,
        "business_name": business.business_name,
        "decision_maker": {
            "name": business.decision_maker_name,
            "title": business.decision_maker_title,
            "email": business.decision_maker_email or business.email,
            "linkedin": business.decision_maker_linkedin,
            "verified": ceo_info.get("verified", False),
        },
    }


@router.post("/{lead_id}/generate-pitch")
def generate_ceo_pitch_endpoint(
    lead_id: str,
    request: GeneratePitchRequest,
    db: Session = Depends(get_db),
):
    """Generate high-converting CEO pitch for Step 1, 2, or 3 based on loophole."""
    business = repo.get_business(db, lead_id)
    if not business:
        raise HTTPException(status_code=404, detail="Lead not found.")

    if not business.loophole_data or not business.loophole_data.get("estimated_annual_turnover"):
        loophole_data = loophole_service.analyze_company_and_loophole(
            business_name=business.business_name,
            category=business.category or "Business",
            city=business.city or "Dubai",
            area=business.area,
            google_rating=business.google_rating,
            review_count=business.google_review_count,
            description=business.description,
        )
        business.loophole_data = loophole_data
        business.loophole_summary = loophole_data.get("primary_loophole")
        business.business_type = loophole_data.get("business_type", "B2B")
        db.commit()
    else:
        loophole_data = business.loophole_data

    from app.services.claude_service import claude_service
    demo_link = build_demo_url(lead_id)
    if claude_service.is_active():
        pitch_body = claude_service.generate_ceo_pitch(
            business_name=business.business_name,
            ceo_name=business.decision_maker_name,
            category=business.category or "Business",
            city=business.city or "Dubai",
            loophole=business.loophole_summary,
            demo_url=demo_link,
            language=request.language or "en",
        )
        if request.language == "ar":
            subject = f"اقتراح استراتيجي لتطوير الحضور الرقمي لـ {business.business_name}"
        else:
            subject = f"Strategic Digital Architecture Proposal for {business.business_name}"
        pitch = {
            "step": request.sequence_step,
            "language": request.language or "en",
            "subject": subject,
            "body": pitch_body,
            "recipient_title": business.decision_maker_title or "CEO",
            "mockup_url": demo_link,
        }
    else:
        pitch = pitch_generator.generate_ceo_pitch(
            business_name=business.business_name,
            category=business.category or "Business",
            city=business.city or "Dubai",
            area=business.area,
            ceo_name=business.decision_maker_name,
            ceo_title=business.decision_maker_title,
            loophole_data=loophole_data,
            sequence_step=request.sequence_step,
            language=request.language or "en",
            live_demo_url=demo_link,
        )

    if isinstance(pitch, str):
        pitch = {
            "step": request.sequence_step,
            "language": request.language or "en",
            "subject": f"Strategic Digital Architecture Proposal for {business.business_name}",
            "body": pitch,
            "recipient_title": business.decision_maker_title or "CEO",
            "mockup_url": demo_link,
        }

    return {
        "lead_id": lead_id,
        "business_name": business.business_name,
        "ceo_name": business.decision_maker_name,
        "ceo_title": business.decision_maker_title,
        "ceo_email": business.decision_maker_email or business.email,
        "pitch": pitch,
    }


@router.get("/{lead_id}/website-preview")
def get_website_preview_data(lead_id: str, db: Session = Depends(get_db)):
    """Generate live simulated website preview mockup data for this business."""
    business = repo.get_business(db, lead_id)
    if not business:
        raise HTTPException(status_code=404, detail="Lead not found.")

    mockup = pitch_generator.generate_website_mockup_data(
        business_name=business.business_name,
        category=business.category or "Business",
        city=business.city or "Dubai",
        area=business.area,
        phone=business.phone,
        loophole_data=business.loophole_data or {},
    )
    return mockup


@router.get("/{lead_id}/demo", response_class=HTMLResponse)
def get_live_website_demo(lead_id: str, db: Session = Depends(get_db)):
    """Serve a complete, interactive, high-converting prototype website for this business."""
    business = repo.get_business(db, lead_id)
    if not business:
        raise HTTPException(status_code=404, detail="Lead not found.")

    if not business.loophole_data or not business.loophole_data.get("estimated_annual_turnover"):
        loophole_data = loophole_service.analyze_company_and_loophole(
            business_name=business.business_name,
            category=business.category or "Business",
            city=business.city or "Dubai",
            area=business.area,
            google_rating=business.google_rating,
            review_count=business.google_review_count,
            description=business.description,
        )
        business.loophole_data = loophole_data
        db.commit()
    else:
        loophole_data = business.loophole_data

    mockup = pitch_generator.generate_website_mockup_data(
        business_name=business.business_name,
        category=business.category or "Business",
        city=business.city or "Dubai",
        area=business.area,
        phone=business.phone,
        loophole_data=loophole_data,
    )

    html_content = pitch_generator.generate_live_demo_html(
        lead_dict=business.to_dict(),
        mockup=mockup,
    )
    return HTMLResponse(content=html_content, status_code=200)


@router.get("/{lead_id}/deep-proposal")
def get_deep_commercial_proposal(lead_id: str, db: Session = Depends(get_db)):
    """Generate executive commercial proposal for CEO with estimated turnover & leak."""
    business = repo.get_business(db, lead_id)
    if not business:
        raise HTTPException(status_code=404, detail="Lead not found.")

    if not business.loophole_data or not business.loophole_data.get("estimated_annual_turnover"):
        loophole_data = loophole_service.analyze_company_and_loophole(
            business_name=business.business_name,
            category=business.category or "Business",
            city=business.city or "Dubai",
            area=business.area,
            google_rating=business.google_rating,
            review_count=business.google_review_count,
            description=business.description,
        )
        business.loophole_data = loophole_data
        db.commit()
    else:
        loophole_data = business.loophole_data

    return {
        "lead_id": lead_id,
        "business_name": business.business_name,
        "ceo_name": business.decision_maker_name or "CEO / Owner",
        "ceo_title": business.decision_maker_title or "Chief Executive Officer",
        "city": business.city or "Dubai",
        "area": business.area,
        "phone": business.phone,
        "turnover_estimate": loophole_data.get("estimated_annual_turnover"),
        "revenue_leak": loophole_data.get("estimated_revenue_leak"),
        "primary_loophole": loophole_data.get("primary_loophole"),
        "loophole_details": loophole_data.get("loophole_details"),
        "competitor_threat": loophole_data.get("competitor_threat"),
        "proposal_deliverables": loophole_data.get("proposal_deliverables", []),
        "estimated_timeline": loophole_data.get("estimated_timeline", "5 - 7 Business Days"),
        "commercial_investment": loophole_data.get("commercial_investment", "$1,200 - $2,200"),
        "live_demo_url": build_demo_url(lead_id),
        "developer": {
            "name": "Sandesh Barde",
            "location": "India",
            "portfolio": "https://sandeshbarde.netlify.app/",
            "github": "https://github.com/sandeshbarde",
            "linkedin": "https://www.linkedin.com/in/sandesh-barde-26ba3839b/",
        }
    }


@router.post("/{lead_id}/demo-interaction")
def track_demo_interaction(
    lead_id: str,
    payload: DemoInteractionRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Track visitor interaction events on a generated live demo website."""
    business = repo.get_business(db, lead_id)
    if not business:
        raise HTTPException(status_code=404, detail="Lead not found.")

    visitor_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    interaction = repo.record_demo_interaction(
        db=db,
        business_id=lead_id,
        interaction_type=payload.interaction_type,
        visitor_ip=visitor_ip,
        user_agent=user_agent,
        meta_data=payload.meta_data,
    )
    return {
        "success": True,
        "interaction_id": interaction.id,
        "interaction_type": interaction.interaction_type,
        "lead_id": lead_id,
    }


@router.post("/{lead_id}/demo-form-submit")
def submit_demo_inquiry(
    lead_id: str,
    payload: DemoFormSubmitRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Record a prospective customer inquiry submitted through the business's live demo mockup."""
    business = repo.get_business(db, lead_id)
    if not business:
        raise HTTPException(status_code=404, detail="Lead not found.")

    visitor_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    meta = {
        "client_name": payload.client_name,
        "client_email": payload.client_email,
        "client_phone": payload.client_phone,
        "service_requested": payload.service_requested,
        "message": payload.message,
    }

    interaction = repo.record_demo_interaction(
        db=db,
        business_id=lead_id,
        interaction_type="form_submit",
        visitor_ip=visitor_ip,
        user_agent=user_agent,
        meta_data=meta,
    )

    # Automatically upgrade lead engagement status
    business.crm_status = "lead_engaged"
    db.commit()

    return {
        "success": True,
        "message": "Inquiry successfully recorded for business demo.",
        "interaction_id": interaction.id,
        "lead_id": lead_id,
    }



