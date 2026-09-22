"""
Autonomous Email Outreach & Follow-Up Automation Engine.
Enables 100% hands-free, automated dispatch of CEO pitches and drip follow-ups.
Supports both SMTP and Resend API for high-deliverability sending.
"""

import time
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
import requests
from loguru import logger
from sqlalchemy.orm import Session

from app.config import settings, build_demo_url
from app.models import Business, OutreachDraft, EmailLog, Suppression
from app.database.repositories import is_email_suppressed, create_email_log
from app.services.loophole_service import loophole_service
from app.services.pitch_generator import pitch_generator, DEVELOPER_NAME, DEVELOPER_LOCATION, PORTFOLIO_URL, GITHUB_URL, LINKEDIN_URL
from app.services.zerobounce_service import zerobounce_service


class EmailAutomationService:
    """Handles automated background sending, queue processing, and drip follow-ups."""

    def __init__(self, db: Session):
        self.db = db

    def _get_target_email(self, business: Business) -> Optional[str]:
        """Determine recipient email address for business. Never invents fake non-existent domains."""
        if business.decision_maker_email and business.decision_maker_email.strip():
            return business.decision_maker_email.strip()
        if business.email and business.email.strip():
            # Discard any previously synthesized fake domains
            email_clean = business.email.strip()
            if not email_clean.endswith(".ae") or ("@" in email_clean and len(email_clean.split("@")[0]) < 35):
                return email_clean
        return None

    @staticmethod
    def test_email_connection() -> Dict[str, Any]:
        """Test active email delivery channel (Resend API or SMTP) and return clear diagnostic status."""
        zb_active = zerobounce_service.is_active()
        zb_credits = zerobounce_service.get_credits() if zb_active else 0
        zb_info = {
            "active": zb_active,
            "credits": zb_credits,
            "status": f"Active ({zb_credits} credits available)" if zb_active else "Inactive (Key Not Set)",
        }

        resend_key = getattr(settings, "resend_api_key", "")
        if resend_key and resend_key.startswith("re_"):
            try:
                resp = requests.get("https://api.resend.com/api-keys", headers={"Authorization": f"Bearer {resend_key}"}, timeout=6)
                if resp.status_code == 200:
                    return {
                        "active": True,
                        "provider": "Resend API",
                        "status": "Connected & Ready",
                        "details": "High-deliverability HTTPS API verified.",
                        "zerobounce": zb_info,
                    }
                else:
                    return {
                        "active": False,
                        "provider": "Resend API",
                        "status": f"Invalid API Key ({resp.status_code})",
                        "details": resp.text,
                        "zerobounce": zb_info,
                    }
            except Exception as e:
                return {"active": False, "provider": "Resend API", "status": "Connection Error", "error": str(e), "zerobounce": zb_info}

        smtp_user = settings.smtp_username
        smtp_pass = settings.smtp_password
        if smtp_user and smtp_pass and smtp_user != "YOUR_EMAIL" and smtp_pass not in ["YOUR_APP_PASSWORD", "YOUR_GOOGLE_APP_PASSWORD"]:
            try:
                host = settings.smtp_host or "smtp.gmail.com"
                port = settings.smtp_port or 587
                server = smtplib.SMTP(host, port, timeout=10)
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.quit()
                return {
                    "active": True,
                    "provider": f"SMTP ({smtp_user})",
                    "status": "Connected & Ready",
                    "details": f"Authenticated with {host}:{port}",
                    "zerobounce": zb_info,
                }
            except smtplib.SMTPAuthenticationError as auth_err:
                return {
                    "active": False,
                    "provider": f"SMTP ({smtp_user})",
                    "status": "Authentication Failed (Bad Credentials)",
                    "error": (
                        "Google blocked this login. Gmail requires a 16-character 'App Password' "
                        "(not your regular account password). Go to https://myaccount.google.com/apppasswords "
                        "to create one, or use a Resend API key."
                    ),
                    "zerobounce": zb_info,
                }
            except Exception as e:
                return {"active": False, "provider": "SMTP", "status": "Connection Error", "error": str(e), "zerobounce": zb_info}

        return {
            "active": False,
            "provider": "None",
            "status": "Awaiting Credentials",
            "details": "Configure Google App Password or Resend API key to start live email sending.",
            "zerobounce": zb_info,
        }

    def send_single_email(
        self,
        recipient_email: str,
        subject: str,
        body_text: str,
        force_send: bool = False,
    ) -> Dict[str, Any]:
        """
        Deliver email via Resend API (preferred) or SMTP.
        Includes automated pre-send ZeroBounce hygiene check.
        """
        if not recipient_email or "@" not in recipient_email:
            return {
                "success": False,
                "method": "validation",
                "error": "No valid email address found for this lead. Pitch them directly via 1-Click WhatsApp!"
            }

        recipient_email = recipient_email.strip()
        domain = recipient_email.split("@")[-1].strip().lower()

        # 0. Suppression List Check (Compliance & Opt-out safety)
        if is_email_suppressed(self.db, recipient_email):
            logger.warning(f"Suppression shield: Recipient '{recipient_email}' is opted out or suppressed.")
            return {
                "success": False,
                "method": "suppressed",
                "error": f"Recipient '{recipient_email}' is on the suppression list (unsubscribed or previous bounce). Delivery blocked.",
            }

        # Pre-flight DNS Existence Check: Block non-existent domains BEFORE SMTP to avoid Google Mailer-Daemon NXDOMAIN bounce
        import socket
        try:
            socket.getaddrinfo(domain, 25)
        except Exception:
            logger.warning(f"DNS Guard: Domain '{domain}' does not exist on the internet (NXDOMAIN). Delivery blocked to protect Gmail reputation.")
            return {
                "success": False,
                "method": "dns_guard",
                "error": f"The domain '{domain}' does not exist on the internet (NXDOMAIN). Delivery was blocked to protect your Gmail reputation. Please pitch this business via 1-Click WhatsApp or Phone instead!",
            }

        # ZeroBounce email hygiene check (if configured and not force_send)
        if zerobounce_service.is_active() and not force_send:
            zb_result = zerobounce_service.validate_email(recipient_email, allow_catch_all=True)
            status_reason = (zb_result.get("status") or "").upper()
            sub_status = zb_result.get("sub_status", "")
            # Only block confirmed toxic or invalid emails (never UNKNOWN or CATCH_ALL or 0 credits):
            if status_reason in ["INVALID", "SPAMTRAP", "ABUSE", "DO_NOT_MAIL"]:
                logger.warning(f"ZeroBounce blocked email to {recipient_email}: {status_reason} ({sub_status})")
                return {
                    "success": False,
                    "method": "zerobounce_shield",
                    "error": f"ZeroBounce Hygiene Shield: Blocked '{recipient_email}' (Status: {status_reason}, {sub_status}). This address is confirmed invalid or toxic. Skipped to preserve sender reputation.",
                    "zerobounce": zb_result,
                }
            else:
                logger.info(f"ZeroBounce hygiene passed for {recipient_email}: status={status_reason} ({sub_status})")

        # Safe Test Mode: Redirect recipient to test mailbox if test mode active
        target_to = recipient_email
        if settings.provider_test_mode:
            test_addr = settings.test_recipient_email or "test-lead@example.com"
            logger.info(f"PROVIDER_TEST_MODE active: Redirecting email from '{recipient_email}' to test mailbox '{test_addr}'")
            target_to = test_addr

        from_header = f"{settings.email_from_name or DEVELOPER_NAME} <{settings.email_from_address or 'onboarding@resend.dev'}>"

        # Method 1: Resend API (HTTP, no SMTP blocks, 99.8% deliverability)
        resend_key = getattr(settings, "resend_api_key", "")
        if resend_key and resend_key.startswith("re_"):
            try:
                headers = {
                    "Authorization": f"Bearer {resend_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "from": from_header,
                    "to": [target_to],
                    "subject": subject,
                    "text": body_text,
                    "reply_to": settings.reply_to or None,
                }
                resp = requests.post("https://api.resend.com/emails", headers=headers, json=payload, timeout=10)
                if resp.status_code in [200, 201]:
                    msg_id = resp.json().get("id")
                    logger.info(f"Email sent via Resend to {recipient_email} (Msg ID: {msg_id})")
                    return {"success": True, "method": "resend", "id": msg_id}
                else:
                    logger.warning(f"Resend error: {resp.text}")
                    return {"success": False, "method": "resend", "error": resp.text}
            except Exception as e:
                logger.error(f"Resend exception: {e}")
                return {"success": False, "method": "resend", "error": str(e)}

        # Method 2: Standard SMTP (e.g. Gmail with App Password)
        smtp_user = settings.smtp_username
        smtp_pass = settings.smtp_password
        if smtp_user and smtp_pass and smtp_user != "YOUR_EMAIL" and smtp_pass not in ["YOUR_APP_PASSWORD", "YOUR_GOOGLE_APP_PASSWORD"]:
            try:
                msg = MIMEMultipart()
                msg["From"] = f"{settings.email_from_name or DEVELOPER_NAME} <{smtp_user}>"
                msg["To"] = target_to
                msg["Subject"] = subject
                if settings.reply_to:
                    msg["Reply-To"] = settings.reply_to
                msg.attach(MIMEText(body_text, "plain", "utf-8"))

                host = settings.smtp_host or "smtp.gmail.com"
                port = settings.smtp_port or 587
                server = smtplib.SMTP(host, port, timeout=15)
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, target_to, msg.as_string())
                server.quit()
                logger.info(f"Email sent via SMTP to {recipient_email}")
                return {"success": True, "method": "smtp"}
            except smtplib.SMTPAuthenticationError as auth_err:
                err_msg = (
                    "Gmail Authentication Failed. Google requires a 16-character App Password, "
                    "not your standard Gmail account password. Visit https://myaccount.google.com/apppasswords"
                )
                logger.error(f"SMTP Auth error to {recipient_email}: {err_msg}")
                return {"success": False, "method": "smtp", "error": err_msg}
            except Exception as e:
                logger.error(f"SMTP send failed to {recipient_email}: {e}")
                return {"success": False, "method": "smtp", "error": str(e)}

        # Method 3: Credentials Required (Accurate non-fake staging state)
        logger.info(f"Email queued for {recipient_email} (awaiting SMTP App Password / Resend Key)")
        return {
            "success": False,
            "method": "credentials_required",
            "status": "QUEUED",
            "message": "Email drafted and formatted in campaign queue. Ready to auto-send when credentials configured."
        }

    def dispatch_all_uncontacted(
        self,
        language: str = "en",
        max_leads: int = 50,
        throttle_seconds: float = 1.0,
    ) -> Dict[str, Any]:
        """
        100% Autonomous Outreach:
        Loops through all qualified uncontacted leads, analyzes their loophole,
        generates CEO pitch in chosen language, and sends automatically.
        """
        # Fetch target leads with NO website that haven't been contacted yet
        query = self.db.query(Business).filter(
            Business.contacted == False,
            Business.website_status.in_(["NO_WEBSITE", "WEBSITE_DOWN", "UNREACHABLE", "SOCIAL_ONLY", "WEBSITE_BROKEN", None])
        ).order_by(Business.lead_score.desc()).limit(max_leads)

        leads = query.all()
        logger.info(f"Autonomous Email Dispatcher started for {len(leads)} leads...")

        dispatched_count = 0
        failed_count = 0
        results = []

        for biz in leads:
            try:
                # 1. Ensure loophole data is present
                if not biz.loophole_data:
                    loophole_info = loophole_service.analyze_company_and_loophole(
                        business_name=biz.business_name,
                        category=biz.category or "Business",
                        city=biz.city or "Dubai",
                        area=biz.area,
                        google_rating=biz.google_rating,
                        review_count=biz.google_review_count,
                        description=biz.description,
                    )
                    biz.loophole_data = loophole_info
                    biz.loophole_summary = loophole_info.get("primary_loophole")
                    biz.business_type = loophole_info.get("business_type", "B2B")
                    biz.is_dealer_or_wholesale = loophole_info.get("is_dealer_or_wholesale", False)

                # 2. Determine target email
                recipient_email = self._get_target_email(biz)
                if not recipient_email:
                    logger.info(f"Skipping email for '{biz.business_name}': No verified email on file. Ready for WhatsApp pitch.")
                    continue

                # 3. Generate the Best Pitch for the CEO
                pitch_data = pitch_generator.generate_ceo_pitch(
                    business_name=biz.business_name,
                    category=biz.category or "Business",
                    city=biz.city or "Dubai",
                    area=biz.area,
                    ceo_name=biz.decision_maker_name,
                    ceo_title=biz.decision_maker_title,
                    loophole_data=biz.loophole_data or {},
                    sequence_step=1,
                    language=language,
                    live_demo_url=build_demo_url(biz.id),
                )

                # 4. Dispatch Email
                send_res = self.send_single_email(
                    recipient_email=recipient_email,
                    subject=pitch_data["subject"],
                    body_text=pitch_data["body"],
                )

                # 5. Record outreach draft and update lead state
                draft = OutreachDraft(
                    business_id=biz.id,
                    pitch_text=pitch_data["body"],
                    pitch_angle=biz.loophole_summary,
                    model_used=f"pitch_generator_{language}",
                )
                self.db.add(draft)

                is_success = send_res.get("success", False)
                method = send_res.get("method", "credentials_required")
                provider_msg_id = send_res.get("id")

                if is_success and method in ["resend", "smtp"]:
                    biz.contacted = True
                    biz.contact_date = datetime.utcnow()
                    biz.contact_status = f"auto_sent_{method}"
                    biz.sequence_stage = "STEP1_SENT"
                    biz.crm_status = "SENT"
                    biz.next_action_due = datetime.utcnow() + timedelta(days=3)
                    dispatched_count += 1
                    status_text = "SENT"

                    # Audit trail log
                    create_email_log(self.db, {
                        "business_id": biz.id,
                        "recipient_email": recipient_email,
                        "subject": pitch_data["subject"],
                        "provider": method,
                        "provider_message_id": provider_msg_id,
                        "status": "ACCEPTED",
                        "sent_at": datetime.utcnow(),
                    })
                elif method == "suppressed":
                    biz.crm_status = "SUPPRESSED"
                    biz.contact_status = "suppressed"
                    status_text = "SUPPRESSED"
                elif method == "credentials_required":
                    biz.contact_status = "queued_pending_credentials"
                    biz.sequence_stage = "QUEUED"
                    status_text = "QUEUED"
                elif method == "zerobounce_shield":
                    failed_count += 1
                    biz.contact_status = "shield_blocked_invalid"
                    status_text = "SHIELD_BLOCKED"
                else:
                    failed_count += 1
                    biz.contact_status = "failed_auth"
                    status_text = "FAILED"

                if not biz.email:
                    biz.email = recipient_email

                self.db.commit()

                results.append({
                    "business_id": biz.id,
                    "business_name": biz.business_name,
                    "recipient_email": recipient_email,
                    "ceo_name": biz.decision_maker_name or "CEO / Owner",
                    "subject": pitch_data["subject"],
                    "status": status_text,
                    "method": method,
                    "error": send_res.get("error"),
                    "message": send_res.get("message"),
                })

                # Safe throttle to avoid email rate-limits
                time.sleep(throttle_seconds)

            except Exception as exc:
                failed_count += 1
                logger.error(f"Failed auto-dispatch for {biz.business_name}: {exc}")
                self.db.rollback()

        return {
            "total_processed": len(leads),
            "dispatched": dispatched_count,
            "failed": failed_count,
            "results": results,
        }

    def send_lead_pitch(
        self,
        lead_id: str,
        language: str = "en",
        sequence_step: int = 1,
    ) -> Dict[str, Any]:
        """
        1-Click autonomous pitch & send for an individual lead:
        Researches loophole, crafts personalized CEO pitch, and dispatches immediately.
        """
        biz = self.db.query(Business).filter(Business.id == lead_id).first()
        if not biz:
            raise ValueError(f"Lead {lead_id} not found.")

        # 1. Forensic loophole analysis if missing
        if not biz.loophole_data:
            loophole_info = loophole_service.analyze_company_and_loophole(
                business_name=biz.business_name,
                category=biz.category or "Business",
                city=biz.city or "Dubai",
                area=biz.area,
                google_rating=biz.google_rating,
                review_count=biz.google_review_count,
                description=biz.description,
            )
            biz.loophole_data = loophole_info
            biz.loophole_summary = loophole_info.get("primary_loophole")
            biz.business_type = loophole_info.get("business_type", "B2B")
            biz.is_dealer_or_wholesale = loophole_info.get("is_dealer_or_wholesale", False)

        # 2. Target email
        recipient_email = self._get_target_email(biz)

        # 3. CEO pitch generation
        pitch_data = pitch_generator.generate_ceo_pitch(
            business_name=biz.business_name,
            category=biz.category or "Business",
            city=biz.city or "Dubai",
            area=biz.area,
            ceo_name=biz.decision_maker_name,
            ceo_title=biz.decision_maker_title,
            loophole_data=biz.loophole_data or {},
            sequence_step=sequence_step,
            language=language,
            live_demo_url=build_demo_url(lead_id),
        )

        # 4. Dispatch email
        send_res = self.send_single_email(
            recipient_email=recipient_email,
            subject=pitch_data["subject"],
            body_text=pitch_data["body"],
        )

        # 5. Save draft and update lead state
        draft = OutreachDraft(
            business_id=biz.id,
            pitch_text=pitch_data["body"],
            pitch_angle=biz.loophole_summary,
            model_used=f"pitch_generator_{language}",
        )
        self.db.add(draft)

        method = send_res.get("method", "smtp")
        if send_res.get("success"):
            if method in ["resend", "smtp"]:
                biz.contacted = True
                biz.contact_date = datetime.utcnow()
                biz.contact_status = f"auto_sent_{method}"
                biz.sequence_stage = f"STEP{sequence_step}_SENT"
                biz.next_action_due = datetime.utcnow() + timedelta(days=3)
            else:
                biz.contact_status = "staged_ready"
                biz.sequence_stage = "STAGED_READY"
        else:
            biz.contact_status = "failed_send"

        if not biz.email:
            biz.email = recipient_email

        self.db.commit()

        return {
            "success": send_res.get("success", False),
            "lead_id": biz.id,
            "business_name": biz.business_name,
            "recipient_email": recipient_email,
            "ceo_name": biz.decision_maker_name or "CEO / Owner",
            "subject": pitch_data["subject"],
            "method": method,
            "status": biz.contact_status,
            "error": send_res.get("error"),
            "message": send_res.get("message") or f"Successfully dispatched to {recipient_email}",
        }
