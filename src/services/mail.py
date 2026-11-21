import html
import logging

import resend

from src.lib.config import Settings

logger = logging.getLogger(__name__)


class InviteMailError(Exception):
    """The invite could not be handed to Resend. The message carries no key or token."""


def send_invite(settings: Settings, *, to: str, name: str, link: str) -> None:
    key = settings.resend_api_key.strip()
    if not key:
        raise InviteMailError("Resend is not configured.")
    safe_name = html.escape(name)
    safe_link = html.escape(link, quote=True)
    resend.api_key = key
    try:
        resend.Emails.send(
            {
                "from": settings.resend_from,
                "to": [to],
                "subject": "Set your Spaceship password",
                "html": (
                    f"<p>{safe_name}, you have a Spaceship desk.</p>"
                    f'<p><a href="{safe_link}">Set your password</a></p>'
                    "<p>This link works for 7 days.</p>"
                ),
            }
        )
    except Exception as exc:
        logger.warning("Invite email was not accepted: %s", type(exc).__name__)
        raise InviteMailError("Resend did not accept the invite.") from None
