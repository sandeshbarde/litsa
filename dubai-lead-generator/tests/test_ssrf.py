"""
Unit tests for SSRF protection and network safety filters.
"""

from app.utils.ssrf import validate_url_for_ssrf, is_safe_ip


def test_ssrf_blocks_private_ips():
    bad_ips = [
        "127.0.0.1",
        "10.0.0.1",
        "172.16.0.1",
        "192.168.1.1",
        "169.254.169.254",  # AWS/GCP metadata
        "::1",  # IPv6 loopback
    ]
    for ip in bad_ips:
        safe, reason = is_safe_ip(ip)
        assert safe is False, f"IP {ip} should be rejected, but passed."


def test_ssrf_blocks_private_urls():
    bad_urls = [
        "http://127.0.0.1:8000/api",
        "http://localhost:3000/dashboard",
        "http://169.254.169.254/computeMetadata/v1/",
        "http://10.200.1.5/admin",
        "http://192.168.0.1/status",
    ]
    for url in bad_urls:
        safe, reason, _ = validate_url_for_ssrf(url)
        assert safe is False, f"URL {url} should be blocked for SSRF, reason: {reason}"


def test_ssrf_allows_public_urls():
    public_urls = [
        "https://www.google.com",
        "https://example.com",
    ]
    for url in public_urls:
        safe, reason, _ = validate_url_for_ssrf(url)
        assert safe is True, f"Legitimate public URL {url} was blocked: {reason}"
