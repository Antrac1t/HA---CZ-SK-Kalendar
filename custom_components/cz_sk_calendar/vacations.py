"""School vacation calculation for Czech Republic and Slovakia."""
from datetime import date, timedelta
from typing import Optional

from .const import (
    COUNTRY_CZ,
    COUNTRY_SK,
    CZ_REGIONS,
    SK_REGION_GROUPS,
)
from .holidays import calculate_easter_sunday


def get_school_year(check_date: date) -> int:
    """Get the school year for a given date.

    School year starts in September. Returns the year when school year started.
    E.g., for date 2024-02-15, returns 2023 (school year 2023/2024).
    """
    if check_date.month >= 9:
        return check_date.year
    return check_date.year - 1


def get_summer_vacation(year: int, country: str) -> tuple[date, date, str]:
    """Get summer vacation dates.

    Summer vacation is July 1 to August 31 in both countries.
    Year parameter is the year when school year ENDS (vacation year).
    """
    if country == COUNTRY_CZ:
        name = "Letní prázdniny"
    else:
        name = "Letné prázdniny"
    return date(year, 7, 1), date(year, 8, 31), name


def get_autumn_vacation_cz(year: int) -> tuple[date, date, str]:
    """Get autumn vacation dates for Czech Republic.

    Autumn vacation is Thursday and Friday in the week containing October 29.
    Year is the calendar year.
    """
    # Find October 29
    oct_29 = date(year, 10, 29)
    # Find the Thursday of that week
    days_since_thursday = (oct_29.weekday() - 3) % 7
    thursday = oct_29 - timedelta(days=days_since_thursday)
    friday = thursday + timedelta(days=1)
    return thursday, friday, "Podzimní prázdniny"


def get_autumn_vacation_sk(year: int) -> tuple[date, date, str]:
    """Get autumn vacation dates for Slovakia.

    Autumn vacation is October 30 and 31.
    """
    return date(year, 10, 30), date(year, 10, 31), "Jesenné prázdniny"


def get_christmas_vacation(school_year: int, country: str) -> tuple[date, date, str]:
    """Get Christmas vacation dates.

    Christmas vacation typically runs from December 23 to January 2-5.
    school_year is when the school year started (e.g., 2023 for 2023/2024).
    """
    # Start is December 23
    start = date(school_year, 12, 23)
    # End is typically January 2-5 of next year, depends on day of week
    # Usually ends on the Sunday before school starts (first Monday of January after Jan 2)

    jan_2 = date(school_year + 1, 1, 2)
    # Find the first workday after Jan 1 that is at least Jan 2
    # Typically school resumes on first workday of January (after Jan 1)
    # Christmas vacation ends on the Sunday before

    # Simplified: vacation ends on January 2 or the following Sunday if Jan 2 is mid-week
    # Most commonly ends around January 2-5

    # Find next Monday after January 2
    days_until_monday = (7 - jan_2.weekday()) % 7
    if days_until_monday == 0 and jan_2.weekday() != 0:
        days_until_monday = 7
    first_monday = jan_2 + timedelta(days=days_until_monday)
    if first_monday.day == 2:
        first_monday = jan_2

    # End is day before first school day, or January 2 minimum
    end = first_monday - timedelta(days=1)
    if end < jan_2:
        end = jan_2

    if country == COUNTRY_CZ:
        name = "Vánoční prázdniny"
    else:
        name = "Vianočné prázdniny"

    return start, end, name


def get_semester_vacation_cz(school_year: int) -> tuple[date, date, str]:
    """Get semester (half-term) vacation for Czech Republic.

    One day - Friday after the end of first semester (end of January/beginning of February).
    Semester ends on January 31, so vacation is first Friday of February.
    """
    # Find first Friday of February
    feb_1 = date(school_year + 1, 2, 1)
    days_until_friday = (4 - feb_1.weekday()) % 7
    first_friday = feb_1 + timedelta(days=days_until_friday)
    return first_friday, first_friday, "Pololetní prázdniny"


def get_semester_vacation_sk(school_year: int) -> tuple[date, date, str]:
    """Get semester (half-term) vacation for Slovakia.

    Monday after end of first semester - typically first Monday of February.
    """
    feb_1 = date(school_year + 1, 2, 1)
    days_until_monday = (7 - feb_1.weekday()) % 7
    if days_until_monday == 0 and feb_1.weekday() != 0:
        days_until_monday = 7
    first_monday = feb_1 + timedelta(days=days_until_monday)
    if feb_1.weekday() == 0:
        first_monday = feb_1
    return first_monday, first_monday, "Polročné prázdniny"


# Czech spring vacation groups - regions rotate through these groups
CZ_SPRING_GROUPS = [
    # Group 1
    ["praha", "stredocesky", "kralovehradecky", "pardubicky"],
    # Group 2
    ["jihocesky", "plzensky", "vysocina", "karlovarsky"],
    # Group 3
    ["ustecky", "liberecky", "jihomoravsky", "olomoucky"],
    # Group 4
    ["zlinsky", "moravskoslezsky"],
]


def get_spring_vacation_cz(school_year: int, region: str) -> tuple[date, date, str]:
    """Get spring vacation dates for Czech Republic.

    Spring vacation is one week, and the timing depends on the region.
    Regions are divided into groups that rotate each year.
    Vacation period is typically late February to mid-March.
    """
    # Find which group this region belongs to
    group_index = 0
    for i, group in enumerate(CZ_SPRING_GROUPS):
        if region in group:
            group_index = i
            break

    # Base date calculation - spring vacation starts around week 8-11 of the year
    # The rotation shifts each year
    # We use a reference year and calculate offset

    # Reference: In 2024, group 0 has vacation starting Feb 5
    reference_year = 2024
    year_offset = school_year - reference_year

    # Each group is offset by 1 week
    # The entire schedule shifts by 1 position each year
    effective_group = (group_index - year_offset) % 4

    # Base start dates for each slot (week of February/March)
    # Slot 0: first week of February (around Feb 5)
    # Slot 1: second week (around Feb 12)
    # Slot 2: third week (around Feb 19)
    # Slot 3: fourth week (around Feb 26)

    # Find the Monday of the week
    feb_1 = date(school_year + 1, 2, 1)
    # Find first Monday of February
    days_until_monday = (7 - feb_1.weekday()) % 7
    if feb_1.weekday() == 0:
        days_until_monday = 0
    first_monday = feb_1 + timedelta(days=days_until_monday)

    # Add weeks based on effective group
    start = first_monday + timedelta(weeks=effective_group)
    end = start + timedelta(days=4)  # Monday to Friday

    return start, end, "Jarní prázdniny"


def get_spring_vacation_sk(school_year: int, region: str) -> tuple[date, date, str]:
    """Get spring vacation dates for Slovakia.

    Spring vacation is one week (Monday to Friday).
    Regions are divided into 3 groups (west, central, east) that rotate.
    """
    # Find which group this region belongs to
    group_name = None
    for name, regions in SK_REGION_GROUPS.items():
        if region in regions:
            group_name = name
            break

    if group_name is None:
        group_name = "west"  # Default

    # Group order for rotation
    group_order = ["west", "central", "east"]
    group_index = group_order.index(group_name)

    # Reference year for rotation calculation
    reference_year = 2024
    year_offset = school_year - reference_year

    # Calculate effective slot (0, 1, or 2)
    effective_slot = (group_index - year_offset) % 3

    # Spring vacation in SK is typically in February/March
    # Slot 0: around Feb 19
    # Slot 1: around Feb 26
    # Slot 2: around Mar 4

    feb_1 = date(school_year + 1, 2, 1)
    # Find third Monday of February as base
    days_until_monday = (7 - feb_1.weekday()) % 7
    if feb_1.weekday() == 0:
        days_until_monday = 0
    first_monday = feb_1 + timedelta(days=days_until_monday)
    third_monday = first_monday + timedelta(weeks=2)

    # Add weeks based on effective slot
    start = third_monday + timedelta(weeks=effective_slot)
    end = start + timedelta(days=4)  # Monday to Friday

    return start, end, "Jarné prázdniny"


def get_easter_vacation_sk(year: int) -> tuple[date, date, str]:
    """Get Easter vacation dates for Slovakia.

    Easter vacation is Thursday before Easter to Tuesday after Easter.
    """
    easter = calculate_easter_sunday(year)
    # Thursday before Easter (Maundy Thursday)
    start = easter - timedelta(days=3)
    # Tuesday after Easter
    end = easter + timedelta(days=2)
    return start, end, "Veľkonočné prázdniny"


def get_easter_vacation_cz(year: int) -> tuple[date, date, str]:
    """Get Easter vacation dates for Czech Republic.

    Easter vacation is Maundy Thursday to Easter Monday (4 days).
    """
    easter = calculate_easter_sunday(year)
    # Maundy Thursday
    start = easter - timedelta(days=3)
    # Easter Monday
    end = easter + timedelta(days=1)
    return start, end, "Velikonoční prázdniny"


def get_all_vacations(
    school_year: int, country: str, region: str
) -> list[tuple[date, date, str]]:
    """Get all school vacations for a school year.

    school_year is when the school year starts (e.g., 2023 for 2023/2024).
    """
    vacations = []

    # Autumn vacation (in the starting year of school year)
    if country == COUNTRY_CZ:
        vacations.append(get_autumn_vacation_cz(school_year))
    else:
        vacations.append(get_autumn_vacation_sk(school_year))

    # Christmas vacation
    vacations.append(get_christmas_vacation(school_year, country))

    # Semester vacation
    if country == COUNTRY_CZ:
        vacations.append(get_semester_vacation_cz(school_year))
    else:
        vacations.append(get_semester_vacation_sk(school_year))

    # Spring vacation
    if country == COUNTRY_CZ:
        vacations.append(get_spring_vacation_cz(school_year, region))
    else:
        vacations.append(get_spring_vacation_sk(school_year, region))

    # Easter vacation (in the ending year of school year)
    if country == COUNTRY_CZ:
        vacations.append(get_easter_vacation_cz(school_year + 1))
    else:
        vacations.append(get_easter_vacation_sk(school_year + 1))

    # Summer vacation (in the ending year of school year)
    vacations.append(get_summer_vacation(school_year + 1, country))

    return vacations


def is_vacation(check_date: date, country: str, region: str) -> bool:
    """Check if a date is during school vacation."""
    school_year = get_school_year(check_date)

    # Check current school year vacations
    vacations = get_all_vacations(school_year, country, region)
    for start, end, _ in vacations:
        if start <= check_date <= end:
            return True

    # Also check previous school year (for summer vacation edge case)
    if check_date.month <= 8:
        prev_vacations = get_all_vacations(school_year - 1, country, region)
        for start, end, _ in prev_vacations:
            if start <= check_date <= end:
                return True

    return False


def get_vacation_name(check_date: date, country: str, region: str) -> Optional[str]:
    """Get the name of the vacation for a given date, or None if not on vacation."""
    school_year = get_school_year(check_date)

    # Check current school year vacations
    vacations = get_all_vacations(school_year, country, region)
    for start, end, name in vacations:
        if start <= check_date <= end:
            return name

    # Also check previous school year
    if check_date.month <= 8:
        prev_vacations = get_all_vacations(school_year - 1, country, region)
        for start, end, name in prev_vacations:
            if start <= check_date <= end:
                return name

    return None


def get_next_vacation(
    from_date: date, country: str, region: str
) -> tuple[date, str, date]:
    """Get the next vacation from a given date.

    Returns (start_date, vacation_name, end_date).
    """
    school_year = get_school_year(from_date)

    # Collect vacations from current and next school year
    all_vacations = []
    all_vacations.extend(get_all_vacations(school_year, country, region))
    all_vacations.extend(get_all_vacations(school_year + 1, country, region))

    # Sort by start date
    all_vacations.sort(key=lambda x: x[0])

    # Find next vacation that starts after from_date
    for start, end, name in all_vacations:
        if start > from_date:
            return start, name, end

    # Fallback - shouldn't happen
    return from_date, "Unknown", from_date


def is_school_day(check_date: date, country: str, region: str) -> bool:
    """Check if a date is a school day.

    A school day is a weekday that is not a holiday and not during vacation.
    """
    # Weekend check
    if check_date.weekday() >= 5:
        return False

    # Vacation check
    if is_vacation(check_date, country, region):
        return False

    # Holiday check (importing here to avoid circular imports)
    from .holidays import is_holiday

    if is_holiday(check_date, country):
        return False

    return True
