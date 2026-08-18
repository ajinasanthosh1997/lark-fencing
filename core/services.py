import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from rest_framework.exceptions import APIException


class RecaptchaVerificationUnavailable(APIException):
    status_code = 503
    default_detail = "reCAPTCHA verification is temporarily unavailable."
    default_code = "recaptcha_unavailable"


def verify_recaptcha(token, remote_ip=None):
    """Verify a browser-generated reCAPTCHA token with Google's siteverify API."""
    secret_key = settings.RECAPTCHA_SECRET_KEY
    if not secret_key:
        raise RecaptchaVerificationUnavailable(
            "Contact form is unavailable because reCAPTCHA is not configured."
        )

    payload = {"secret": secret_key, "response": token}
    if remote_ip:
        payload["remoteip"] = remote_ip

    request = Request(
        settings.RECAPTCHA_VERIFY_URL,
        data=urlencode(payload).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=settings.RECAPTCHA_TIMEOUT) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RecaptchaVerificationUnavailable() from exc

    return result.get("success") is True
