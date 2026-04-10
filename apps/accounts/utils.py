import re
from uuid import uuid4

from apps.accounts.models import User


def generate_unique_username(email: str) -> str:
    """
    Derive a unique username from the local part of an email address.

    Strategy:
      1. Extract everything before '@'.
      2. Strip characters not allowed in AbstractUser.username (keep a-z, A-Z, 0-9, . + - _).
      3. Try the base value; if taken, append an incrementing counter (john, john1, john2, …).
      4. After 100 collisions, append a short UUID hex fragment as a guaranteed fallback.
    """
    local = email.split("@")[0]
    base = re.sub(r"[^\w.+\-]", "_", local)[:150] or "user"

    if not User.objects.filter(username=base).exists():
        return base

    for counter in range(1, 101):
        candidate = f"{base}{counter}"
        if not User.objects.filter(username=candidate).exists():
            return candidate

    return f"{base}{uuid4().hex[:8]}"
