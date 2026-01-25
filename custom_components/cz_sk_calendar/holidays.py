"""Holiday calculation for Czech Republic and Slovakia."""
from datetime import date, timedelta
from typing import Optional

from .const import COUNTRY_CZ, COUNTRY_SK


def calculate_easter_sunday(year: int) -> date:
    """Calculate Easter Sunday using the Anonymous Gregorian algorithm (Computus).

    This algorithm calculates Easter Sunday for any year in the Gregorian calendar.
    Easter falls on the first Sunday after the first full moon on or after March 21.
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


def get_easter_holidays(year: int, country: str) -> dict[date, str]:
    """Get Easter-related holidays for a given year and country."""
    easter = calculate_easter_sunday(year)
    holidays = {}

    # Good Friday (Velký pátek / Veľký piatok) - 2 days before Easter
    good_friday = easter - timedelta(days=2)
    if country == COUNTRY_CZ:
        holidays[good_friday] = "Velký pátek"
    else:
        holidays[good_friday] = "Veľký piatok"

    # Easter Monday (Velikonoční pondělí / Veľkonočný pondelok) - 1 day after Easter
    easter_monday = easter + timedelta(days=1)
    if country == COUNTRY_CZ:
        holidays[easter_monday] = "Velikonoční pondělí"
    else:
        holidays[easter_monday] = "Veľkonočný pondelok"

    return holidays


def get_fixed_holidays_cz(year: int) -> dict[date, str]:
    """Get fixed holidays for Czech Republic."""
    return {
        date(year, 1, 1): "Nový rok / Den obnovy samostatného českého státu",
        date(year, 5, 1): "Svátek práce",
        date(year, 5, 8): "Den vítězství",
        date(year, 7, 5): "Den slovanských věrozvěstů Cyrila a Metoděje",
        date(year, 7, 6): "Den upálení mistra Jana Husa",
        date(year, 9, 28): "Den české státnosti",
        date(year, 10, 28): "Den vzniku samostatného československého státu",
        date(year, 11, 17): "Den boje za svobodu a demokracii",
        date(year, 12, 24): "Štědrý den",
        date(year, 12, 25): "1. svátek vánoční",
        date(year, 12, 26): "2. svátek vánoční",
    }


def get_fixed_holidays_sk(year: int) -> dict[date, str]:
    """Get fixed holidays for Slovakia."""
    return {
        date(year, 1, 1): "Deň vzniku Slovenskej republiky",
        date(year, 1, 6): "Zjavenie Pána (Traja králi)",
        date(year, 5, 1): "Sviatok práce",
        date(year, 5, 8): "Deň víťazstva nad fašizmom",
        date(year, 7, 5): "Sviatok svätého Cyrila a Metoda",
        date(year, 8, 29): "Výročie SNP",
        date(year, 9, 1): "Deň Ústavy Slovenskej republiky",
        date(year, 9, 15): "Sedembolestná Panna Mária",
        date(year, 11, 1): "Sviatok všetkých svätých",
        date(year, 11, 17): "Deň boja za slobodu a demokraciu",
        date(year, 12, 24): "Štedrý deň",
        date(year, 12, 25): "Prvý sviatok vianočný",
        date(year, 12, 26): "Druhý sviatok vianočný",
    }


def get_all_holidays(year: int, country: str) -> dict[date, str]:
    """Get all holidays for a given year and country."""
    if country == COUNTRY_CZ:
        holidays = get_fixed_holidays_cz(year)
    else:
        holidays = get_fixed_holidays_sk(year)

    # Add Easter holidays
    holidays.update(get_easter_holidays(year, country))

    return holidays


def is_holiday(check_date: date, country: str) -> bool:
    """Check if a date is a holiday."""
    holidays = get_all_holidays(check_date.year, country)
    return check_date in holidays


def get_holiday_name(check_date: date, country: str) -> Optional[str]:
    """Get the name of the holiday for a given date, or None if not a holiday."""
    holidays = get_all_holidays(check_date.year, country)
    return holidays.get(check_date)


def get_next_holiday(from_date: date, country: str) -> tuple[date, str]:
    """Get the next holiday from a given date."""
    current_date = from_date
    # Check up to 2 years ahead
    end_date = from_date + timedelta(days=730)

    while current_date <= end_date:
        holidays = get_all_holidays(current_date.year, country)
        if current_date in holidays:
            return current_date, holidays[current_date]
        current_date += timedelta(days=1)

    # Fallback - shouldn't happen with valid data
    return from_date, "Unknown"


def is_workday(check_date: date, country: str) -> bool:
    """Check if a date is a workday (not weekend and not holiday)."""
    # Weekend check (Saturday = 5, Sunday = 6)
    if check_date.weekday() >= 5:
        return False

    # Holiday check
    if is_holiday(check_date, country):
        return False

    return True
