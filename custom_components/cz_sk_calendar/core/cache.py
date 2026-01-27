"""Caching layer for CZ/SK Calendar."""
from __future__ import annotations

from datetime import date
from functools import lru_cache, wraps
from typing import Any, Callable, TypeVar

T = TypeVar("T")

# Global cache storage
_cache: dict[str, Any] = {}
_cache_date: date | None = None


def cached_date(func: Callable[..., T]) -> Callable[..., T]:
    """Cache decorator that invalidates when date changes.

    This decorator caches function results and automatically clears
    the cache at midnight when the date changes.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        global _cache_date
        today = date.today()

        # Clear cache if date changed
        if _cache_date != today:
            _cache.clear()
            _cache_date = today

        # Create cache key from function name and arguments
        key = f"{func.__name__}:{args}:{sorted(kwargs.items())}"

        if key not in _cache:
            _cache[key] = func(*args, **kwargs)

        return _cache[key]

    return wrapper


def clear_cache() -> None:
    """Manually clear the cache."""
    global _cache_date
    _cache.clear()
    _cache_date = None


# LRU cache for expensive calculations that don't change (e.g., Easter for a given year)
@lru_cache(maxsize=128)
def cached_easter(year: int) -> tuple[int, int, int]:
    """Cache Easter calculation by year. Returns (year, month, day)."""
    from .calculations import calculate_easter_sunday
    easter = calculate_easter_sunday(year)
    return (easter.year, easter.month, easter.day)


@lru_cache(maxsize=64)
def cached_holidays(year: int, country: str) -> tuple[tuple[str, int, int, str], ...]:
    """Cache holidays by year and country. Returns tuple of (country, month, day, name)."""
    from .data_sources import _get_holidays_raw
    holidays = _get_holidays_raw(year, country)
    return tuple((country, d.month, d.day, name) for d, name in holidays.items())


@lru_cache(maxsize=64)
def cached_vacations(school_year: int, country: str, region: str) -> tuple[tuple[str, str, str, str], ...]:
    """Cache vacations by school year, country, and region."""
    from .data_sources import _get_vacations_raw
    vacations = _get_vacations_raw(school_year, country, region)
    return tuple(
        (start.isoformat(), end.isoformat(), name, country)
        for start, end, name in vacations
    )
