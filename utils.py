# utils.py
from datetime import datetime, timedelta
from telegram import ChatPermissions

def parse_duration(duration):
    if not duration:
        return None
    try:
        value = int(duration[:-1])
        unit = duration[-1].lower()
        if unit == "m":
            return datetime.now() + timedelta(minutes=value)
        elif unit == "h":
            return datetime.now() + timedelta(hours=value)
        elif unit == "d":
            return datetime.now() + timedelta(days=value)
        elif unit == "w":
            return datetime.now() + timedelta(weeks=value)
        elif unit == "y":
            return datetime.now() + timedelta(days=value * 365)
    except (ValueError, IndexError):
        return None
    return None

def mute_permissions():
    return ChatPermissions(
        can_send_messages=False,
        can_send_media_messages=False,
        can_send_polls=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False,
        can_change_info=False,
        can_invite_users=False,
        can_pin_messages=False
    )
