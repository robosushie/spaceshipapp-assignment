import html
import logging

import resend

from src.lib.config import Settings

logger = logging.getLogger(__name__)


class MailError(Exception):
    """Resend did not take the message. The error carries no key or token."""


def _send(settings: Settings, *, to: str, subject: str, html_body: str) -> None:
    key = settings.resend_api_key.strip()
    if not key:
        raise MailError("Resend is not configured.")
    resend.api_key = key
    try:
        resend.Emails.send(
            {
                "from": settings.resend_from,
                "to": [to],
                "subject": subject,
                "html": html_body,
            }
        )
    except Exception as exc:
        logger.warning("Email was not accepted: %s", type(exc).__name__)
        raise MailError("Resend did not accept the message.") from None


def send_invite(settings: Settings, *, to: str, name: str, link: str) -> None:
    safe_name = html.escape(name)
    safe_link = html.escape(link, quote=True)
    _send(
        settings,
        to=to,
        subject="Set your Spaceship password",
        html_body=(
            f"<p>{safe_name}, you have a Spaceship desk.</p>"
            f'<p><a href="{safe_link}">Set your password</a></p>'
            "<p>This link works for 7 days.</p>"
        ),
    )


def send_reset(settings: Settings, *, to: str, name: str, link: str) -> None:
    safe_name = html.escape(name)
    safe_link = html.escape(link, quote=True)
    _send(
        settings,
        to=to,
        subject="Reset your Spaceship password",
        html_body=(
            f"<p>{safe_name}, reset your Spaceship password.</p>"
            f'<p><a href="{safe_link}">Choose a new password</a></p>'
            "<p>This link works for 1 hour.</p>"
        ),
    )
