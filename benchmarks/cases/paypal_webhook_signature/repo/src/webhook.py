"""PayPal Webhook Handler (Bugged Version)."""
import hashlib
from typing import Dict, Any


class PayPalWebhookVerificationError(Exception):
    """Raised when incoming PayPal webhook fails verification."""
    pass


def parse_webhook_event(raw_body: str) -> Dict[str, Any]:
    """Parse incoming webhook event payload."""
    import json
    return json.loads(raw_body)


def verify_webhook(headers: Dict[str, str], raw_body: str, webhook_id: str) -> bool:
    """Verify PayPal webhook notification signature.

    BUG: Legacy implementation only checks PAYPAL-AUTH-ALGO and fails to
    validate required modern transmission headers:
    PAYPAL-TRANSMISSION-SIG, PAYPAL-TRANSMISSION-TIME, PAYPAL-CERT-URL.
    """
    normalized_headers = {k.upper(): v for k, v in headers.items()}

    # Bug: Checks legacy header only and fails when modern transmission headers are sent
    if "PAYPAL-AUTH-ALGO" not in normalized_headers:
        raise PayPalWebhookVerificationError(
            "Missing required PayPal transmission headers: PAYPAL-TRANSMISSION-SIG, PAYPAL-CERT-URL, PAYPAL-TRANSMISSION-TIME"
        )

    return True
