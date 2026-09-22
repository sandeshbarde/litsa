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

    def get_daily_email_limit(self) -> int:
        """Calculate maximum allowed email sends for today according to warmup mode."""
        if not getattr(settings, "warmup_mode", True):
            return getattr(settings, "max_emails_per_day", 50)

        start_str = getattr(settings, "warmup_start_date", None)
        start_date = None
        if start_str:
            try:
                start_date = datetime.strptime(start_str.strip(), "%Y-%m-%d").date()
            except Exception:
                pass

        if not start_date:
            first_log = self.db.query(EmailLog.sent_at).order_by(EmailLog.sent_at.asc()).first()
            if first_log and first_log[0]:
                start_date = first_log[0].date()
            else:
                start_date = datetime.utcnow().date()

        days = max(0, (datetime.utcnow().date() - start_date).days)
        warmup_capacity = min(10 + days * 3, 50)
        max_configured = getattr(settings, "max_emails_per_day", 50)
        return min(warmup_capacity, max_configured)

    def get_emails_sent_today_count(self) -> int:
        """Count emails sent today across all channels."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return self.db.query(EmailLog).filter(
            EmailLog.sent_at >= today_start,
            EmailLog.status.in_(["SENT", "ACCEPTED", "DELIVERED"])
        ).count()

    def check_resend_domain_status(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """Check SPF/DKIM authentication status via Resend API."""
        resend_key = getattr(settings, "resend_api_key", "")
        if not resend_key or not resend_key.startswith("re_"):
            return {
                "verified": False,
                "status": "unconfigured",
                "message": "Resend API key not configured."
            }

        target_domain = domain
        if not target_domain:
            from_addr = getattr(settings, "email_from_address", "")
            if "@" in from_addr:
                target_domain = from_addr.split("@")[-1].strip().lower()
            else:
                target_domain = "resend.dev"

        try:
            resp = requests.get(
                "https://api.resend.com/domains",
                headers={"Authorization": f"Bearer {resend_key}"},
                timeout=8,
            )
            if resp.status_code == 200:
                domains_data = resp.json().get("data", [])
                for d in domains_data:
                    d_name = d.get("name", "").lower()
                    if d_name == target_domain or target_domain == "resend.dev":
                        d_status = (d.get("status") or "").lower()
                        is_verified = (d_status == "verified" or target_domain == "resend.dev")
                        if not is_verified:
                            logger.warning(f"Resend domain warning: Domain '{target_domain}' status is '{d_status}'. High-volume sending blocked.")
                        return {
                            "verified": is_verified,
                            "status": d_status or "verified",
                            "domain": target_domain,
                            "details": d,
                        }
                logger.warning(f"Resend domain warning: Domain '{target_domain}' not found in registered Resend domains. High-volume sending blocked.")
                return {
                    "verified": False,
                    "status": "not_found",
                    "domain": target_domain,
                    "message": f"Domain '{target_domain}' not registered in Resend account.",
                }
            else:
                logger.warning(f"Resend domain API returned HTTP {resp.status_code}: {resp.text}")
                return {"verified": False, "status": "error", "domain": target_domain, "message": resp.text}
        except Exception as exc:
            logger.error(f"Failed to check Resend domain status: {exc}")
            return {"verified": False, "status": "exception", "domain": target_domain, "error": str(exc)}

    def send_single_email(
        self,
        recipient_email: str,
        subject: str,
        body_text: str,
        force_send: bool = False,
    ) -> Dict[str, Any]:
        """
        Deliver email via Resend API (Primary Channel) with Gmail SMTP as Emergency Fallback.
        Enforces Warmup / Daily Email Limit and pre-send ZeroBounce hygiene check.
        """
        if not recipient_email or "@" not in recipient_email:
            return {
                "success": False,
                "method": "validation",
                "error": "No valid email address found for this lead. Pitch them directly via 1-Click WhatsApp!"
            }

        recipient_email = recipient_email.strip()
        domain = recipient_email.split("@")[-1].strip().lower()

        # Warmup / Daily Quota Check
        sent_today = self.get_emails_sent_today_count()
        daily_limit = self.get_daily_email_limit()
        if sent_today >= daily_limit and not force_send:
            logger.warning(f"Warmup / Daily limit reached: {sent_today}/{daily_limit} emails sent today.")
            return {
                "success": False,
                "method": "warmup_limit",
                "error": f"Daily email limit reached ({sent_today}/{daily_limit} sent today under warmup mode). Sending paused to protect domain reputation.",
            }

        # 0. Suppression List Check (Compliance & Opt-out safety)
        if is_email_suppressed(self.db, recipient_email):
            logger.warning(f"Suppression shield: Recipient '{recipient_email}' is opted out or suppressed.")
            return {
                "success": False,
                "method": "suppressed",
                "error": f"Recipient '{recipient_email}' is on the suppression list (unsubscribed or previous bounce). Delivery blocked.",
            }

        # Pre-flight DNS Existence Check
        import socket
        try:
            socket.getaddrinfo(domain, 25)
        except Exception:
            logger.warning(f"DNS Guard: Domain '{domain}' does not exist on the internet (NXDOMAIN). Delivery blocked.")
            return {
                "success": False,
                "method": "dns_guard",
                "error": f"The domain '{domain}' does not exist on the internet (NXDOMAIN). Delivery was blocked to protect sender reputation.",
            }

        # ZeroBounce email hygiene check
        if zerobounce_service.is_active() and not force_send:
            zb_result = zerobounce_service.validate_email(recipient_email, allow_catch_all=True)
            status_reason = (zb_result.get("status") or "").upper()
            sub_status = zb_result.get("sub_status", "")
            if status_reason in ["INVALID", "SPAMTRAP", "ABUSE", "DO_NOT_MAIL"]:
                logger.warning(f"ZeroBounce blocked email to {recipient_email}: {status_reason} ({sub_status})")
                return {
                    "success": False,
                    "method": "zerobounce_shield",
                    "error": f"ZeroBounce Hygiene Shield: Blocked '{recipient_email}' (Status: {status_reason}, {sub_status}). This address is confirmed invalid or toxic.",
                    "zerobounce": zb_result,
                }
            else:
                logger.info(f"ZeroBounce hygiene passed for {recipient_email}: status={status_reason} ({sub_status})")

        # Safe Test Mode
        target_to = recipient_email
        if settings.provider_test_mode:
            test_addr = settings.test_recipient_email or "test-lead@example.com"
            logger.info(f"PROVIDER_TEST_MODE active: Redirecting email from '{recipient_email}' to test mailbox '{test_addr}'")
            target_to = test_addr

        from_header = f"{settings.email_from_name or DEVELOPER_NAME} <{settings.email_from_address or 'onboarding@resend.dev'}>"

        # PRIMARY CHANNEL: Resend API (HTTP)
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
                    logger.info(f"Email sent via Resend API (Primary Channel) to {recipient_email} (Msg ID: {msg_id})")
                    return {"success": True, "method": "resend", "id": msg_id}
                else:
                    logger.warning(f"Resend Primary Channel error ({resp.status_code}): {resp.text}. Falling back to emergency SMTP...")
            except Exception as e:
                logger.warning(f"Resend Primary Channel exception: {e}. Falling back to emergency SMTP...")

        # EMERGENCY FALLBACK: Standard SMTP (Gmail App Password)
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
                logger.info(f"Email sent via Emergency SMTP Fallback to {recipient_email}")
                return {"success": True, "method": "smtp_fallback"}
            except smtplib.SMTPAuthenticationError as auth_err:
                err_msg = (
                    "Emergency SMTP Fallback Failed: Gmail Authentication Error. Google requires a 16-character App Password. "
                    "Visit https://myaccount.google.com/apppasswords"
                )
                logger.error(f"SMTP Auth error to {recipient_email}: {err_msg}")
                return {"success": False, "method": "smtp_fallback", "error": err_msg}
            except Exception as e:
                logger.error(f"Emergency SMTP Fallback failed to {recipient_email}: {e}")
                return {"success": False, "method": "smtp_fallback", "error": str(e)}

        # Method 3: Credentials Required
        logger.info(f"Email queued for {recipient_email} (awaiting Resend API Key / SMTP App Password)")
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

        # Domain authentication check for high-volume sends
        domain_check = self.check_resend_domain_status()
        if not domain_check.get("verified", True) and len(leads) > 5:
            logger.warning(f"Resend sender domain '{domain_check.get('domain')}' is unverified. High-volume dispatch capped to 5 leads.")
            leads = leads[:5]

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

    def process_drip_followups(self, max_leads: int = 50) -> Dict[str, Any]:
        """
        Processes multi-step drip sequence follow-ups (Day 0: Pitch, Day 3: Soft, Day 7: Insight, Day 14: Final).
        Pauses automatically if lead replied, unsubscribed, or bounced.
        """
        now = datetime.utcnow()
        leads = self.db.query(Business).filter(
            Business.contacted == True,
            Business.contact_status.not_in(["replied", "unsubscribed", "bounced", "suppressed"]),
            Business.crm_status.not_in(["REPLIED", "UNSUBSCRIBED", "BOUNCED", "SUPPRESSED"]),
            Business.sequence_stage.not_in(["FINISHED", "REPLIED_PAUSED"]),
            (Business.next_action_due <= now) | (Business.next_action_due.is_(None))
        ).limit(max_leads).all()

        processed_count = 0
        skipped_count = 0
        results = []

        for biz in leads:
            recipient_email = self._get_target_email(biz)
            if not recipient_email or is_email_suppressed(self.db, recipient_email):
                skipped_count += 1
                continue

            current_stage = biz.sequence_stage or "STEP1_SENT"
            next_step = 2
            next_delay_days = 4
            if current_stage == "STEP1_SENT":
                next_step = 2
                next_delay_days = 4
            elif current_stage == "STEP2_SENT":
                next_step = 3
                next_delay_days = 7
            elif current_stage == "STEP3_SENT":
                next_step = 4
                next_delay_days = 0

            pitch_data = pitch_generator.generate_ceo_pitch(
                business_name=biz.business_name,
                category=biz.category or "Business",
                city=biz.city or "Dubai",
                area=biz.area,
                ceo_name=biz.decision_maker_name,
                ceo_title=biz.decision_maker_title,
                loophole_data=biz.loophole_data or {},
                sequence_step=next_step,
                language="en",
                live_demo_url=build_demo_url(biz.id),
            )

            send_res = self.send_single_email(
                recipient_email=recipient_email,
                subject=pitch_data["subject"],
                body_text=pitch_data["body"],
            )

            if send_res.get("success"):
                biz.sequence_stage = f"STEP{next_step}_SENT" if next_step < 4 else "FINISHED"
                biz.contact_status = f"step{next_step}_sent"
                if next_step < 4:
                    biz.next_action_due = now + timedelta(days=next_delay_days)
                else:
                    biz.next_action_due = None

                create_email_log(self.db, {
                    "business_id": biz.id,
                    "recipient_email": recipient_email,
                    "subject": pitch_data["subject"],
                    "provider": send_res.get("method", "resend"),
                    "provider_message_id": send_res.get("id"),
                    "status": "ACCEPTED",
                    "sent_at": now,
                })
                self.db.commit()
                processed_count += 1
                results.append({"business_id": biz.id, "step": next_step, "status": "sent"})
            else:
                results.append({"business_id": biz.id, "step": next_step, "status": "failed", "error": send_res.get("error")})

        return {"processed": processed_count, "skipped": skipped_count, "results": results}
