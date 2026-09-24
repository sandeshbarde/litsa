"""
Fallback contact discovery and direct SMTP email verification service.
Guesses standard email patterns for domains and verifies via direct SMTP handshake.
If no domain exists, marks business contact channel as 'phone' for WhatsApp/call routing.
"""

import socket
from typing import Optional, Tuple, Dict, Any, List
from urllib.parse import urlparse
from loguru import logger


def extract_domain(website_url: Optional[str]) -> Optional[str]:
    """Extract clean root domain from website URL."""
    if not website_url:
        return None
    url = website_url.strip()
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    try:
        parsed = urlparse(url)
        host = parsed.netloc or parsed.path
        host = host.split(":")[0].lower()
        if host.startswith("www."):
            host = host[4:]
        return host if "." in host else None
    except Exception:
        return None


class EmailGuesserService:
    """Discovers and verifies email addresses via direct MX / SMTP handshake."""

    CANDIDATE_PREFIXES = ["info", "contact", "hello", "sales", "support", "office", "admin"]

    def __init__(self, timeout: float = 6.0):
        self.timeout = timeout

    def _resolve_mx(self, domain: str) -> List[str]:
        """Resolve MX hostnames for a domain using dnspython or socket fallback."""
        try:
            import dns.resolver
            answers = dns.resolver.resolve(domain, "MX", lifetime=self.timeout)
            records = sorted(answers, key=lambda r: r.preference)
            return [str(r.exchange).rstrip(".") for r in records]
        except Exception:
            # Fallback to direct domain connection
            return [domain]

    def _verify_smtp_rcpt(self, mx_host: str, candidate_email: str) -> bool:
        """Attempt direct SMTP HELO -> MAIL FROM -> RCPT TO verification."""
        sock = None
        try:
            sock = socket.create_connection((mx_host, 25), timeout=self.timeout)
            banner = sock.recv(1024).decode("utf-8", errors="ignore")
            if not banner.startswith("220"):
                return False

            # HELO
            sock.sendall(b"HELO litsa.io\r\n")
            helo_resp = sock.recv(1024).decode("utf-8", errors="ignore")
            if not helo_resp.startswith("250"):
                return False

            # MAIL FROM
            sock.sendall(b"MAIL FROM:<verify@litsa.io>\r\n")
            mail_resp = sock.recv(1024).decode("utf-8", errors="ignore")
            if not mail_resp.startswith("250"):
                return False

            # RCPT TO
            sock.sendall(f"RCPT TO:<{candidate_email}>\r\n".encode("utf-8"))
            rcpt_resp = sock.recv(1024).decode("utf-8", errors="ignore")

            # QUIT
            try:
                sock.sendall(b"QUIT\r\n")
            except Exception:
                pass

            # 250 or 251 indicates mailbox accepted
            return rcpt_resp.startswith(("250", "251"))
        except Exception as exc:
            logger.debug(f"SMTP check failed for {candidate_email} on {mx_host}: {exc}")
            return False
        finally:
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass

    def discover_contact(
        self,
        business_name: str,
        website: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> Tuple[Optional[str], str, Dict[str, Any]]:
        """
        Returns (verified_email, contact_channel, metadata).
        contact_channel is 'email' if verified email found, else 'phone'.
        """
        domain = extract_domain(website)
        
        # If no custom domain exists (e.g. NO_WEBSITE or SOCIAL_ONLY)
        if not domain:
            logger.info(f"No custom domain for '{business_name}'. Routing to phone/WhatsApp outreach channel.")
            return None, "phone", {
                "contact_channel": "phone",
                "reason": "Business has no website domain. Phone/WhatsApp channel active.",
                "has_phone": bool(phone),
            }

        mx_hosts = self._resolve_mx(domain)
        if not mx_hosts:
            return None, "phone", {
                "contact_channel": "phone",
                "reason": f"No MX records resolved for domain '{domain}'.",
            }

        primary_mx = mx_hosts[0]
        logger.info(f"Testing candidate emails for '{business_name}' on domain '{domain}' (MX: {primary_mx})...")

        for prefix in self.CANDIDATE_PREFIXES:
            candidate = f"{prefix}@{domain}"
            is_valid = self._verify_smtp_rcpt(primary_mx, candidate)
            if is_valid:
                logger.info(f"Discovered verified SMTP mailbox for '{business_name}': {candidate}")
                return candidate, "email", {
                    "contact_channel": "email",
                    "smtp_verified": True,
                    "mx_host": primary_mx,
                    "domain": domain,
                }

        logger.info(f"SMTP candidates unverified for domain '{domain}'. Falling back to phone channel.")
        return None, "phone", {
            "contact_channel": "phone",
            "reason": f"SMTP pattern verification failed for domain '{domain}'.",
            "domain": domain,
        }


email_guesser = EmailGuesserService()
