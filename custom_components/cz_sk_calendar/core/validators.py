"""Validators for CZ/SK Calendar."""
from __future__ import annotations

from ..const import COUNTRY_CZ, COUNTRY_SK, CZ_REGIONS, SK_REGIONS


class ValidationError(Exception):
    """Validation error for CZ/SK Calendar."""
    pass


def validate_country(country: str) -> str:
    """Validate country code.

    Args:
        country: Country code (CZ or SK)

    Returns:
        Validated country code

    Raises:
        ValidationError: If country is not valid
    """
    if country not in (COUNTRY_CZ, COUNTRY_SK):
        raise ValidationError(
            f"Invalid country '{country}'. Must be '{COUNTRY_CZ}' or '{COUNTRY_SK}'."
        )
    return country


def validate_region(region: str, country: str) -> str:
    """Validate region for a given country.

    Args:
        region: Region code
        country: Country code (CZ or SK)

    Returns:
        Validated region code

    Raises:
        ValidationError: If region is not valid for the country
    """
    validate_country(country)

    regions = CZ_REGIONS if country == COUNTRY_CZ else SK_REGIONS

    if region not in regions:
        valid_regions = ", ".join(regions.keys())
        raise ValidationError(
            f"Invalid region '{region}' for country '{country}'. "
            f"Valid regions: {valid_regions}"
        )
    return region


def validate_date_range(start_year: int, end_year: int) -> tuple[int, int]:
    """Validate date range for calculations.

    Args:
        start_year: Start year
        end_year: End year

    Returns:
        Validated (start_year, end_year) tuple

    Raises:
        ValidationError: If range is invalid
    """
    if start_year > end_year:
        raise ValidationError(
            f"Start year ({start_year}) cannot be greater than end year ({end_year})."
        )

    if start_year < 1900 or end_year > 2100:
        raise ValidationError(
            "Year must be between 1900 and 2100."
        )

    return start_year, end_year


def get_region_name(region: str, country: str) -> str:
    """Get human-readable region name.

    Args:
        region: Region code
        country: Country code

    Returns:
        Human-readable region name
    """
    regions = CZ_REGIONS if country == COUNTRY_CZ else SK_REGIONS
    return regions.get(region, region)
