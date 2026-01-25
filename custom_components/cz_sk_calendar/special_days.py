"""Special days calculation for Czech Republic and Slovakia."""
from datetime import date, timedelta
from typing import Optional

from .const import COUNTRY_CZ, COUNTRY_SK


def get_nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> date:
    """Get the nth occurrence of a weekday in a month.

    weekday: 0=Monday, 6=Sunday
    n: 1=first, 2=second, etc. Use -1 for last.
    """
    if n > 0:
        # Find first occurrence
        first_day = date(year, month, 1)
        days_until = (weekday - first_day.weekday()) % 7
        first_occurrence = first_day + timedelta(days=days_until)
        return first_occurrence + timedelta(weeks=n - 1)
    else:
        # Find last occurrence
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)
        last_day = next_month - timedelta(days=1)
        days_since = (last_day.weekday() - weekday) % 7
        return last_day - timedelta(days=days_since)


def get_special_days_cz(year: int) -> dict[date, str]:
    """Get special days for Czech Republic."""
    special_days = {
        # Fixed dates
        date(year, 1, 6): "Tři králové",
        date(year, 2, 14): "Valentýn",
        date(year, 3, 8): "Mezinárodní den žen",
        date(year, 3, 28): "Den učitelů",
        date(year, 4, 1): "Apríl",
        date(year, 4, 7): "Světový den zdraví",
        date(year, 4, 22): "Den Země",
        date(year, 5, 5): "Květen - osvobození Prahy",
        date(year, 6, 1): "Mezinárodní den dětí",
        date(year, 6, 21): "Letní slunovrat",
        date(year, 9, 1): "Začátek školního roku",
        date(year, 9, 21): "Mezinárodní den míru",
        date(year, 9, 28): "Den české státnosti",
        date(year, 10, 5): "Světový den učitelů",
        date(year, 10, 31): "Halloween",
        date(year, 11, 2): "Dušičky",
        date(year, 11, 11): "Den válečných veteránů",
        date(year, 12, 5): "Mikuláš (předvečer)",
        date(year, 12, 6): "Mikuláš",
        date(year, 12, 21): "Zimní slunovrat",
        date(year, 12, 31): "Silvestr",
    }

    # Mother's Day - second Sunday of May
    mothers_day = get_nth_weekday_of_month(year, 5, 6, 2)  # 6 = Sunday
    special_days[mothers_day] = "Den matek"

    # Father's Day - third Sunday of June
    fathers_day = get_nth_weekday_of_month(year, 6, 6, 3)
    special_days[fathers_day] = "Den otců"

    # Grandparents' Day - first Sunday of October (in CZ)
    grandparents_day = get_nth_weekday_of_month(year, 10, 6, 1)
    special_days[grandparents_day] = "Den prarodičů"

    return special_days


def get_special_days_sk(year: int) -> dict[date, str]:
    """Get special days for Slovakia."""
    special_days = {
        # Fixed dates
        date(year, 1, 6): "Traja králi",
        date(year, 2, 14): "Valentín",
        date(year, 3, 8): "Medzinárodný deň žien",
        date(year, 3, 28): "Deň učiteľov",
        date(year, 4, 1): "Apríl",
        date(year, 4, 7): "Svetový deň zdravia",
        date(year, 4, 22): "Deň Zeme",
        date(year, 6, 1): "Medzinárodný deň detí",
        date(year, 6, 21): "Letný slnovrat",
        date(year, 9, 1): "Začiatok školského roka",  # Note: SK school year starts Sep 2
        date(year, 9, 2): "Začiatok školského roka",
        date(year, 9, 21): "Medzinárodný deň mieru",
        date(year, 10, 5): "Svetový deň učiteľov",
        date(year, 10, 31): "Halloween",
        date(year, 11, 2): "Pamiatka zosnulých",
        date(year, 11, 11): "Deň veteránov",
        date(year, 12, 5): "Mikuláš (predvečer)",
        date(year, 12, 6): "Mikuláš",
        date(year, 12, 21): "Zimný slnovrat",
        date(year, 12, 31): "Silvester",
    }

    # Mother's Day - second Sunday of May
    mothers_day = get_nth_weekday_of_month(year, 5, 6, 2)
    special_days[mothers_day] = "Deň matiek"

    # Father's Day - third Sunday of June
    fathers_day = get_nth_weekday_of_month(year, 6, 6, 3)
    special_days[fathers_day] = "Deň otcov"

    # Grandparents' Day
    grandparents_day = get_nth_weekday_of_month(year, 10, 6, 1)
    special_days[grandparents_day] = "Deň starých rodičov"

    return special_days


def get_all_special_days(year: int, country: str) -> dict[date, str]:
    """Get all special days for a given year and country."""
    if country == COUNTRY_CZ:
        return get_special_days_cz(year)
    else:
        return get_special_days_sk(year)


def is_special_day(check_date: date, country: str) -> bool:
    """Check if a date is a special day."""
    special_days = get_all_special_days(check_date.year, country)
    return check_date in special_days


def get_special_day_name(check_date: date, country: str) -> Optional[str]:
    """Get the name of the special day for a given date, or None."""
    special_days = get_all_special_days(check_date.year, country)
    return special_days.get(check_date)


def get_next_special_day(from_date: date, country: str) -> tuple[date, str]:
    """Get the next special day from a given date."""
    current_date = from_date
    end_date = from_date + timedelta(days=400)  # Check up to ~13 months ahead

    while current_date <= end_date:
        special_days = get_all_special_days(current_date.year, country)
        if current_date in special_days:
            return current_date, special_days[current_date]
        current_date += timedelta(days=1)

    return from_date, "Unknown"


def get_special_days_in_month(year: int, month: int, country: str) -> dict[date, str]:
    """Get all special days in a specific month."""
    all_days = get_all_special_days(year, country)
    return {d: name for d, name in all_days.items() if d.month == month}
