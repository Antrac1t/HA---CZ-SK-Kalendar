"""Core calculations for CZ/SK Calendar."""
from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache

from ..const import COUNTRY_CZ, COUNTRY_SK, SK_REGION_GROUPS


@lru_cache(maxsize=128)
def calculate_easter_sunday(year: int) -> date:
    """Calculate Easter Sunday using the Anonymous Gregorian algorithm (Computus).

    This algorithm calculates Easter Sunday for any year in the Gregorian calendar.
    Easter falls on the first Sunday after the first full moon on or after March 21.

    Args:
        year: The year to calculate Easter for

    Returns:
        Date of Easter Sunday
    """
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def get_nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> date:
    """Get the nth occurrence of a weekday in a month.

    Args:
        year: Year
        month: Month (1-12)
        weekday: Day of week (0=Monday, 6=Sunday)
        n: Occurrence (1=first, 2=second, etc. Use -1 for last)

    Returns:
        Date of the nth weekday
    """
    if n > 0:
        first_day = date(year, month, 1)
        days_until = (weekday - first_day.weekday()) % 7
        first_occurrence = first_day + timedelta(days=days_until)
        return first_occurrence + timedelta(weeks=n - 1)
    else:
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)
        last_day = next_month - timedelta(days=1)
        days_since = (last_day.weekday() - weekday) % 7
        return last_day - timedelta(days=days_since)


def get_school_year(check_date: date) -> int:
    """Get the school year for a given date.

    School year starts in September. Returns the year when school year started.

    Args:
        check_date: Date to check

    Returns:
        Year when school year started (e.g., 2023 for school year 2023/2024)
    """
    if check_date.month >= 9:
        return check_date.year
    return check_date.year - 1


def is_weekend(check_date: date) -> bool:
    """Check if date is a weekend (Saturday or Sunday).

    Args:
        check_date: Date to check

    Returns:
        True if weekend
    """
    return check_date.weekday() >= 5


def is_holiday(check_date: date, country: str) -> bool:
    """Check if a date is a public holiday.

    Args:
        check_date: Date to check
        country: Country code (CZ or SK)

    Returns:
        True if the date is a public holiday
    """
    from .data_sources import get_all_holidays
    holidays = get_all_holidays(check_date.year, country)
    return check_date in holidays


def is_workday(check_date: date, country: str) -> bool:
    """Check if a date is a workday (not weekend and not holiday).

    Args:
        check_date: Date to check
        country: Country code (CZ or SK)

    Returns:
        True if the date is a workday
    """
    if is_weekend(check_date):
        return False
    return not is_holiday(check_date, country)


def is_vacation(check_date: date, country: str, region: str) -> bool:
    """Check if a date is during school vacation.

    Args:
        check_date: Date to check
        country: Country code (CZ or SK)
        region: Region code

    Returns:
        True if the date is during vacation
    """
    from .data_sources import get_all_vacations

    school_year = get_school_year(check_date)

    # Check current school year vacations
    for start, end, _ in get_all_vacations(school_year, country, region):
        if start <= check_date <= end:
            return True

    # Also check previous school year (for summer vacation edge case)
    if check_date.month <= 8:
        for start, end, _ in get_all_vacations(school_year - 1, country, region):
            if start <= check_date <= end:
                return True

    return False


def is_school_day(check_date: date, country: str, region: str) -> bool:
    """Check if a date is a school day.

    A school day is a weekday that is not a holiday and not during vacation.

    Args:
        check_date: Date to check
        country: Country code (CZ or SK)
        region: Region code

    Returns:
        True if the date is a school day
    """
    if is_weekend(check_date):
        return False
    if is_holiday(check_date, country):
        return False
    if is_vacation(check_date, country, region):
        return False
    return True


# ============================================================================
# Vacation date calculations
# ============================================================================

def calc_summer_vacation(year: int, country: str) -> tuple[date, date, str]:
    """Calculate summer vacation dates (July 1 - August 31)."""
    name = "Letní prázdniny" if country == COUNTRY_CZ else "Letné prázdniny"
    return date(year, 7, 1), date(year, 8, 31), name


def calc_autumn_vacation(year: int, country: str) -> tuple[date, date, str]:
    """Calculate autumn vacation dates."""
    if country == COUNTRY_CZ:
        # Thursday and Friday in week containing October 29
        oct_29 = date(year, 10, 29)
        days_since_thursday = (oct_29.weekday() - 3) % 7
        thursday = oct_29 - timedelta(days=days_since_thursday)
        friday = thursday + timedelta(days=1)
        return thursday, friday, "Podzimní prázdniny"
    else:
        return date(year, 10, 30), date(year, 10, 31), "Jesenné prázdniny"


def calc_christmas_vacation(school_year: int, country: str) -> tuple[date, date, str]:
    """Calculate Christmas vacation dates (Dec 23 - ~Jan 2-5)."""
    start = date(school_year, 12, 23)

    jan_2 = date(school_year + 1, 1, 2)
    days_until_monday = (7 - jan_2.weekday()) % 7
    if days_until_monday == 0 and jan_2.weekday() != 0:
        days_until_monday = 7
    first_monday = jan_2 + timedelta(days=days_until_monday)
    if first_monday.day == 2:
        first_monday = jan_2

    end = first_monday - timedelta(days=1)
    if end < jan_2:
        end = jan_2

    name = "Vánoční prázdniny" if country == COUNTRY_CZ else "Vianočné prázdniny"
    return start, end, name


def calc_semester_vacation(school_year: int, country: str) -> tuple[date, date, str]:
    """Calculate semester (half-term) vacation."""
    feb_1 = date(school_year + 1, 2, 1)

    if country == COUNTRY_CZ:
        days_until_friday = (4 - feb_1.weekday()) % 7
        first_friday = feb_1 + timedelta(days=days_until_friday)
        return first_friday, first_friday, "Pololetní prázdniny"
    else:
        days_until_monday = (7 - feb_1.weekday()) % 7
        if feb_1.weekday() == 0:
            first_monday = feb_1
        else:
            if days_until_monday == 0:
                days_until_monday = 7
            first_monday = feb_1 + timedelta(days=days_until_monday)
        return first_monday, first_monday, "Polročné prázdniny"


# Czech spring vacation groups - regions rotate through these groups
CZ_SPRING_GROUPS = [
    ["praha", "stredocesky", "kralovehradecky", "pardubicky"],
    ["jihocesky", "plzensky", "vysocina", "karlovarsky"],
    ["ustecky", "liberecky", "jihomoravsky", "olomoucky"],
    ["zlinsky", "moravskoslezsky"],
]


def calc_spring_vacation(school_year: int, country: str, region: str) -> tuple[date, date, str]:
    """Calculate spring vacation dates (varies by region)."""
    if country == COUNTRY_CZ:
        # Find which group this region belongs to
        group_index = 0
        for i, group in enumerate(CZ_SPRING_GROUPS):
            if region in group:
                group_index = i
                break

        reference_year = 2024
        year_offset = school_year - reference_year
        effective_group = (group_index - year_offset) % 4

        feb_1 = date(school_year + 1, 2, 1)
        days_until_monday = (7 - feb_1.weekday()) % 7
        if feb_1.weekday() == 0:
            days_until_monday = 0
        first_monday = feb_1 + timedelta(days=days_until_monday)

        start = first_monday + timedelta(weeks=effective_group)
        end = start + timedelta(days=4)
        return start, end, "Jarní prázdniny"
    else:
        # Slovak spring vacation
        group_name = "west"
        for name, regions in SK_REGION_GROUPS.items():
            if region in regions:
                group_name = name
                break

        group_order = ["west", "central", "east"]
        group_index = group_order.index(group_name)

        reference_year = 2024
        year_offset = school_year - reference_year
        effective_slot = (group_index - year_offset) % 3

        feb_1 = date(school_year + 1, 2, 1)
        days_until_monday = (7 - feb_1.weekday()) % 7
        if feb_1.weekday() == 0:
            days_until_monday = 0
        first_monday = feb_1 + timedelta(days=days_until_monday)
        third_monday = first_monday + timedelta(weeks=2)

        start = third_monday + timedelta(weeks=effective_slot)
        end = start + timedelta(days=4)
        return start, end, "Jarné prázdniny"


def calc_easter_vacation(year: int, country: str) -> tuple[date, date, str]:
    """Calculate Easter vacation dates."""
    easter = calculate_easter_sunday(year)

    if country == COUNTRY_CZ:
        start = easter - timedelta(days=3)  # Maundy Thursday
        end = easter + timedelta(days=1)    # Easter Monday
        return start, end, "Velikonoční prázdniny"
    else:
        start = easter - timedelta(days=3)  # Thursday before Easter
        end = easter + timedelta(days=2)    # Tuesday after Easter
        return start, end, "Veľkonočné prázdniny"


def count_workdays_in_range(start_date: date, end_date: date, country: str) -> int:
    """Count workdays in a date range.

    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        country: Country code

    Returns:
        Number of workdays in the range
    """
    count = 0
    current = start_date
    while current <= end_date:
        if is_workday(current, country):
            count += 1
        current += timedelta(days=1)
    return count


def count_school_days_in_range(
    start_date: date, end_date: date, country: str, region: str
) -> int:
    """Count school days in a date range.

    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        country: Country code
        region: Region code

    Returns:
        Number of school days in the range
    """
    count = 0
    current = start_date
    while current <= end_date:
        if is_school_day(current, country, region):
            count += 1
        current += timedelta(days=1)
    return count
