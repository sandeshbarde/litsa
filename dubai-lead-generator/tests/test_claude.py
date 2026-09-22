"""
Unit tests for Anthropic Claude AI Service.
"""

from app.services.claude_service import ClaudeService


def test_claude_service_unconfigured():
    svc = ClaudeService(api_key="")
    assert svc.is_active() is False


def test_claude_service_masked_key_rejected():
    # If the user provides a key with dots '...' from a screenshot, it shouldn't crash or be marked active
    svc = ClaudeService(api_key="sk-ant-api03-XTd...RQAA")
    assert svc.is_active() is False


def test_claude_service_valid_key_pattern():
    svc = ClaudeService(api_key="sk-ant-api03-realfullkeystring1234567890abcdefghijklmnopqrstuvwxyz")
    assert svc.is_active() is True


def test_claude_fallback_pitch_generation():
    svc = ClaudeService(api_key="")
    pitch = svc.generate_ceo_pitch(
        business_name="Al Futtaim Wholesale",
        ceo_name="Ahmed Al Futtaim",
        category="Wholesale Metals",
        city="Dubai",
        loophole="Missing digital RFQ procurement workflow",
        demo_url="http://127.0.0.1:8000/demo/lead_123",
        language="en",
    )
    assert "Sandesh Barde" in pitch
    assert "https://sandeshbarde.netlify.app/" in pitch
    assert "https://github.com/sandeshbarde" in pitch
    assert "https://www.linkedin.com/in/sandesh-barde-26ba3839b/" in pitch
    assert "Al Futtaim Wholesale" in pitch
