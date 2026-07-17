"""Single shared Limiter instance. Must be imported everywhere rate limiting
is needed — creating separate Limiter() instances per module means each one
tracks its own counters and the global default_limits never actually apply."""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])
