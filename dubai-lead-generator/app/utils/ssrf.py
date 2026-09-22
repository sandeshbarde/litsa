"""
SSRF (Server-Side Request Forgery) protection utility.
Validates URLs and resolves destination IPs before network dispatch.
Re-evaluates every HTTP redirect destination to prevent SSRF through redirect chains.
"""

import socket
import ipaddress
from urllib.parse import urlparse
from typing import Tuple, Optional
import requests
from loguru import logger


# Cloud metadata IP and common cloud internal hosts
BLOCKED_IPS = {
    "169.254.169.254",  # AWS/GCP/Azure metadata
    "fd00:ec2::254",    # AWS IPv6 metadata
    "100.100.100.200",  # Alibaba metadata
}

BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "instance-data",
    "kubernetes.default",
    "docker.internal",
}


def is_safe_ip(ip_str: str) -> Tuple[bool, str]:
    """
    Checks whether an IP address is publicly routable and safe to query.
    Blocks private, loopback, link-local, multicast, and reserved addresses.
    """
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False, f"Invalid IP address format: {ip_str}"

    if ip_str in BLOCKED_IPS:
        return False, f"Access to cloud metadata IP ({ip_str}) is prohibited."

    if ip.is_loopback:
        return False, f"Loopback address ({ip_str}) is prohibited."

    if ip.is_private:
        return False, f"Private network address ({ip_str}) is prohibited."

    if ip.is_link_local:
        return False, f"Link-local address ({ip_str}) is prohibited."

    if ip.is_multicast:
        return False, f"Multicast address ({ip_str}) is prohibited."

    if ip.is_reserved:
        return False, f"Reserved address ({ip_str}) is prohibited."

    return True, "IP is safe"


def validate_url_for_ssrf(url: str) -> Tuple[bool, str, Optional[str]]:
    """
    Validates a URL against SSRF rules:
    1. Only http and https protocols allowed.
    2. Hostname must not be in blocked local/cloud hostnames.
    3. Resolves DNS to IP and validates IP safety.
    Returns: (is_safe, error_reason, resolved_ip)
    """
    if not url or not isinstance(url, str):
        return False, "Empty or invalid URL provided", None

    try:
        parsed = urlparse(url)
    except Exception as exc:
        return False, f"Malformed URL: {exc}", None

    if parsed.scheme.lower() not in ["http", "https"]:
        return False, f"Unsupported scheme '{parsed.scheme}'. Only HTTP/HTTPS allowed.", None

    hostname = parsed.hostname
    if not hostname:
        return False, "URL does not contain a valid hostname.", None

    hostname_clean = hostname.strip().lower()
    if hostname_clean in BLOCKED_HOSTNAMES or hostname_clean.endswith(".local") or hostname_clean.endswith(".internal"):
        return False, f"Hostname '{hostname_clean}' is prohibited by SSRF security policy.", None

    # Resolve IP address
    port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
    try:
        addr_info = socket.getaddrinfo(hostname_clean, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror as exc:
        return False, f"DNS resolution failed for '{hostname_clean}': {exc}", None
    except Exception as exc:
        return False, f"Socket error resolving '{hostname_clean}': {exc}", None

    if not addr_info:
        return False, f"No DNS records found for '{hostname_clean}'.", None

    # Check all resolved IP addresses
    resolved_ip = None
    for entry in addr_info:
        ip_addr = entry[4][0]
        resolved_ip = ip_addr
        safe, reason = is_safe_ip(ip_addr)
        if not safe:
            return False, f"SSRF Protection blocked request to '{hostname_clean}' -> {reason}", ip_addr

    return True, "URL is safe", resolved_ip


def safe_request(
    method: str,
    url: str,
    session: Optional[requests.Session] = None,
    timeout: int = 10,
    max_redirects: int = 4,
    verify_ssl: bool = True,
    headers: Optional[dict] = None,
) -> Tuple[bool, Optional[requests.Response], str]:
    """
    Executes an HTTP request while strictly enforcing SSRF checks on initial URL
    and every subsequent redirect hop.
    Returns: (success, response, error_message)
    """
    sess = session or requests.Session()
    current_url = url
    redirect_hops = 0

    req_headers = headers or {"User-Agent": "Mozilla/5.0 (compatible; LitsaLeadBot/2.0)"}

    while redirect_hops <= max_redirects:
        is_safe, reason, _ = validate_url_for_ssrf(current_url)
        if not is_safe:
            return False, None, reason

        try:
            resp = sess.request(
                method=method,
                url=current_url,
                timeout=timeout,
                allow_redirects=False,
                verify=verify_ssl,
                headers=req_headers,
            )
        except requests.exceptions.SSLError as ssl_err:
            return False, None, f"SSL verification error: {ssl_err}"
        except requests.exceptions.Timeout:
            return False, None, f"Connection timed out ({timeout}s)"
        except requests.exceptions.RequestException as req_err:
            return False, None, f"Request failed: {req_err}"

        # If redirect, extract location and loop with SSRF check
        if resp.is_redirect and "Location" in resp.headers:
            redirect_hops += 1
            redirect_target = resp.headers["Location"]
            # Handle relative redirects
            current_url = requests.compat.urljoin(current_url, redirect_target)
            continue

        return True, resp, "Success"

    return False, None, f"Exceeded maximum redirects ({max_redirects})"
