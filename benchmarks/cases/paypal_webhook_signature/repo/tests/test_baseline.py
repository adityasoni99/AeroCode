"""Baseline tests for paypal_webhook_signature — DO NOT MODIFY (Git Guard protected)."""
from src.webhook import parse_webhook_event


def test_parse_webhook_event_payload():
    """Baseline: parse_webhook_event successfully parses valid JSON payload."""
    payload = '{"event_type": "PAYMENT.CAPTURE.COMPLETED", "id": "WH-12345"}'
    data = parse_webhook_event(payload)
    assert data["event_type"] == "PAYMENT.CAPTURE.COMPLETED"
    assert data["id"] == "WH-12345"
