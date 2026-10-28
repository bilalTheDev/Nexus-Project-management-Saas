"""Refresh-token lifecycle helpers."""

from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)


def blacklist_all_refresh_tokens(user) -> int:
    """Blacklist every outstanding refresh token for ``user``. Returns count."""
    count = 0
    for outstanding in OutstandingToken.objects.filter(user=user):
        _, created = BlacklistedToken.objects.get_or_create(token=outstanding)
        if created:
            count += 1
    return count
