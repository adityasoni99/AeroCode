"""Regression test for paypal_webhook_signature — FAIL on bugged code, PASS on patched code."""
import pytest
from src.webhook import verify_webhook, PayPalWebhookVerificationError


def test_verify_webhook_with_modern_transmission_headers():
    """Modern PayPal webhook calls include transmission signature, time, and cert-url."""
    headers = {
        "PAYPAL-TRANSMISSION-ID": "69438960-fae9-11ef-9351-69234b35ef21",
        "PAYPAL-TRANSMISSION-TIME": "2026-10-31T05:00:00Z",
        "PAYPAL-TRANSMISSION-SIG": "MEQCIGsV123984124981723==",
        "PAYPAL-CERT-URL": "https://api.paypal.com/v1/notifications/certs/CERT-12345",
        "PAYPAL-AUTH-ALGO": "SHA256withRSA",
    }
    raw_body = '{"event_type": "PAYMENT.CAPTURE.COMPLETED", "summary": "Payment completed"}'
    webhook_id = "WH-CONFIGURED-ID"

    # Must verify successfully without raising PayPalWebhookVerificationError
    verified = verify_webhook(headers, raw_body, webhook_id)
    assert verified is True
