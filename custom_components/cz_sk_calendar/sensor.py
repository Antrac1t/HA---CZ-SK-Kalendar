"""Sensor platform for CZ/SK School & Work Calendar."""
from __future__ import annotations

import calendar
from datetime import date, timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_COUNTRY, CONF_REGION, COUNTRY_CZ
from .entity import CZSKEntity
from .core import (
    get_all_holidays,
    get_all_vacations,
    get_holiday_name,
    get_nameday,
    get_namedays_in_week,
    get_next_holiday,
    get_next_vacation,
    get_school_year,
    get_special_day_name,
    get_next_special_day,
    get_vacation_name,
    is_holiday,
    is_school_day,
    is_vacation,
    is_workday,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the CZ/SK Calendar sensors."""
    country = config_entry.data[CONF_COUNTRY]
    region = config_entry.data[CONF_REGION]

    sensors = [
        # Boolean state sensors (kept for backwards compatibility)
        CZSKBooleanSensor(
            config_entry, "workday",
            "Pracovní den" if country == COUNTRY_CZ else "Pracovný deň",
            "mdi:briefcase",
            lambda e: is_workday(e.today, e._country),
        ),
        CZSKBooleanSensor(
            config_entry, "school_day",
            "Školní den" if country == COUNTRY_CZ else "Školský deň",
            "mdi:school",
            lambda e: is_school_day(e.today, e._country, e._region),
        ),
        CZSKBooleanSensor(
            config_entry, "holiday",
            "Svátek" if country == COUNTRY_CZ else "Sviatok",
            "mdi:party-popper",
            lambda e: is_holiday(e.today, e._country),
        ),
        CZSKBooleanSensor(
            config_entry, "vacation",
            "Prázdniny" if country == COUNTRY_CZ else "Prázdniny",
            "mdi:beach",
            lambda e: is_vacation(e.today, e._country, e._region),
        ),
        # Name sensors
        CZSKNameSensor(
            config_entry, "holiday_name",
            "Název svátku" if country == COUNTRY_CZ else "Názov sviatku",
            "mdi:calendar-star",
            lambda e: get_holiday_name(e.today, e._country),
        ),
        CZSKNameSensor(
            config_entry, "vacation_name",
            "Název prázdnin" if country == COUNTRY_CZ else "Názov prázdnin",
            "mdi:calendar-text",
            lambda e: get_vacation_name(e.today, e._country, e._region),
        ),
        CZSKNameSensor(
            config_entry, "special_day",
            "Významný den" if country == COUNTRY_CZ else "Významný deň",
            "mdi:star",
            lambda e: get_special_day_name(e.today, e._country),
        ),
        CZSKNameSensor(
            config_entry, "nameday",
            "Jmeniny" if country == COUNTRY_CZ else "Meniny",
            "mdi:cake-variant",
            lambda e: get_nameday(e.today, e._country),
        ),
        # Countdown sensors
        CZSKCountdownSensor(config_entry, country),
        # School year sensor
        CZSKSchoolYearSensor(config_entry, country, region),
        # Statistics sensors
        CZSKWorkdaysInMonthSensor(config_entry, country),
        CZSKSchoolDaysInMonthSensor(config_entry, country, region),
        CZSKVacationProgressSensor(config_entry, country, region),
    ]

    async_add_entities(sensors, True)


# ============================================================================
# Base sensor classes
# ============================================================================

class CZSKBaseSensor(CZSKEntity, SensorEntity):
    """Base class for CZ/SK Calendar sensors."""
    pass


class CZSKBooleanSensor(CZSKBaseSensor):
    """Sensor that returns True/False based on a condition."""

    def __init__(
        self,
        config_entry: ConfigEntry,
        entity_type: str,
        name: str,
        icon: str,
        value_fn,
    ) -> None:
        """Initialize the boolean sensor."""
        super().__init__(config_entry, entity_type, name, icon)
        self._value_fn = value_fn

    @property
    def native_value(self) -> bool:
        """Return the sensor value."""
        return self._value_fn(self)


class CZSKNameSensor(CZSKBaseSensor):
    """Sensor that returns a name (holiday, vacation, etc.)."""

    def __init__(
        self,
        config_entry: ConfigEntry,
        entity_type: str,
        name: str,
        icon: str,
        value_fn,
    ) -> None:
        """Initialize the name sensor."""
        super().__init__(config_entry, entity_type, name, icon)
        self._value_fn = value_fn

    @property
    def native_value(self) -> str | None:
        """Return the sensor value."""
        return self._value_fn(self)


# ============================================================================
# Specialized sensors
# ============================================================================

class CZSKCountdownSensor(CZSKBaseSensor):
    """Combined countdown sensor for holidays and vacations."""

    _attr_native_unit_of_measurement = "days"

    def __init__(self, config_entry: ConfigEntry, country: str) -> None:
        """Initialize the countdown sensor."""
        name = "Odpočet" if country == COUNTRY_CZ else "Odpočet"
        super().__init__(config_entry, "countdown", name, "mdi:timer-sand")

    @property
    def native_value(self) -> int:
        """Return days to next event (holiday or vacation)."""
        today = self.today

        # Days to next holiday
        if is_holiday(today, self._country):
            days_holiday = 0
        else:
            next_h, _ = get_next_holiday(today + timedelta(days=1), self._country)
            days_holiday = (next_h - today).days

        # Days to next vacation
        if is_vacation(today, self._country, self._region):
            days_vacation = 0
        else:
            next_v, _, _ = get_next_vacation(today, self._country, self._region)
            days_vacation = (next_v - today).days

        return min(days_holiday, days_vacation)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        attrs = super().extra_state_attributes.copy()
        today = self.today

        # Next holiday
        if is_holiday(today, self._country):
            attrs["days_to_holiday"] = 0
            attrs["holiday_name"] = get_holiday_name(today, self._country)
        else:
            next_h, name_h = get_next_holiday(today + timedelta(days=1), self._country)
            attrs["days_to_holiday"] = (next_h - today).days
            attrs["next_holiday"] = name_h
            attrs["next_holiday_date"] = next_h.isoformat()

        # Next vacation
        if is_vacation(today, self._country, self._region):
            attrs["days_to_vacation"] = 0
            attrs["vacation_name"] = get_vacation_name(today, self._country, self._region)
        else:
            next_v, name_v, end_v = get_next_vacation(today, self._country, self._region)
            attrs["days_to_vacation"] = (next_v - today).days
            attrs["next_vacation"] = name_v
            attrs["next_vacation_start"] = next_v.isoformat()
            attrs["next_vacation_end"] = end_v.isoformat()

        # Next special day
        next_s, name_s = get_next_special_day(today + timedelta(days=1), self._country)
        attrs["days_to_special_day"] = (next_s - today).days
        attrs["next_special_day"] = name_s
        attrs["next_special_day_date"] = next_s.isoformat()

        # Tomorrow's nameday
        tomorrow = today + timedelta(days=1)
        attrs["tomorrow_nameday"] = get_nameday(tomorrow, self._country)

        return attrs


class CZSKSchoolYearSensor(CZSKBaseSensor):
    """Sensor for school year information."""

    def __init__(
        self, config_entry: ConfigEntry, country: str, region: str
    ) -> None:
        """Initialize the school year sensor."""
        name = "Školní rok" if country == COUNTRY_CZ else "Školský rok"
        super().__init__(config_entry, "school_year", name, "mdi:school")

    @property
    def native_value(self) -> str:
        """Return the current school year."""
        school_year = get_school_year(self.today)
        return f"{school_year}/{school_year + 1}"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        attrs = super().extra_state_attributes.copy()
        today = self.today
        school_year = get_school_year(today)

        # School year dates
        start_day = 2 if self._country == "SK" else 1
        start_date = date(school_year, 9, start_day)
        end_date = date(school_year + 1, 6, 30)

        attrs["start_date"] = start_date.isoformat()
        attrs["end_date"] = end_date.isoformat()

        # Progress
        total_days = (end_date - start_date).days + 1
        elapsed = max(0, (today - start_date).days)
        remaining = max(0, (end_date - today).days)

        attrs["total_days"] = total_days
        attrs["elapsed_days"] = elapsed
        attrs["remaining_days"] = remaining
        attrs["progress_percent"] = round(min(100, (elapsed / total_days) * 100), 1)

        # Vacations list
        vacations = get_all_vacations(school_year, self._country, self._region)
        attrs["vacations"] = [
            {"name": name, "start": start.isoformat(), "end": end.isoformat()}
            for start, end, name in sorted(vacations, key=lambda x: x[0])
        ]

        return attrs


class CZSKWorkdaysInMonthSensor(CZSKBaseSensor):
    """Sensor for workdays in current month."""

    _attr_native_unit_of_measurement = "days"

    def __init__(self, config_entry: ConfigEntry, country: str) -> None:
        """Initialize the sensor."""
        name = "Pracovní dny v měsíci" if country == COUNTRY_CZ else "Pracovné dni v mesiaci"
        super().__init__(config_entry, "workdays_in_month", name, "mdi:calendar-month")

    @property
    def native_value(self) -> int:
        """Return remaining workdays in current month."""
        today = self.today
        _, last_day = calendar.monthrange(today.year, today.month)

        count = 0
        for day in range(today.day, last_day + 1):
            if is_workday(date(today.year, today.month, day), self._country):
                count += 1
        return count

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        attrs = super().extra_state_attributes.copy()
        today = self.today
        _, last_day = calendar.monthrange(today.year, today.month)

        total = sum(
            1 for d in range(1, last_day + 1)
            if is_workday(date(today.year, today.month, d), self._country)
        )
        elapsed = sum(
            1 for d in range(1, today.day)
            if is_workday(date(today.year, today.month, d), self._country)
        )

        attrs["total_in_month"] = total
        attrs["elapsed"] = elapsed
        attrs["month"] = today.strftime("%B")

        return attrs


class CZSKSchoolDaysInMonthSensor(CZSKBaseSensor):
    """Sensor for school days in current month."""

    _attr_native_unit_of_measurement = "days"

    def __init__(
        self, config_entry: ConfigEntry, country: str, region: str
    ) -> None:
        """Initialize the sensor."""
        name = "Školní dny v měsíci" if country == COUNTRY_CZ else "Školské dni v mesiaci"
        super().__init__(config_entry, "school_days_in_month", name, "mdi:calendar-month")

    @property
    def native_value(self) -> int:
        """Return remaining school days in current month."""
        today = self.today
        _, last_day = calendar.monthrange(today.year, today.month)

        count = 0
        for day in range(today.day, last_day + 1):
            if is_school_day(date(today.year, today.month, day), self._country, self._region):
                count += 1
        return count

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        attrs = super().extra_state_attributes.copy()
        today = self.today
        _, last_day = calendar.monthrange(today.year, today.month)

        total = sum(
            1 for d in range(1, last_day + 1)
            if is_school_day(date(today.year, today.month, d), self._country, self._region)
        )
        elapsed = sum(
            1 for d in range(1, today.day)
            if is_school_day(date(today.year, today.month, d), self._country, self._region)
        )

        attrs["total_in_month"] = total
        attrs["elapsed"] = elapsed
        attrs["month"] = today.strftime("%B")

        return attrs


class CZSKVacationProgressSensor(CZSKBaseSensor):
    """Sensor for vacation progress (when on vacation)."""

    _attr_native_unit_of_measurement = "days"

    def __init__(
        self, config_entry: ConfigEntry, country: str, region: str
    ) -> None:
        """Initialize the sensor."""
        name = "Zbývá dní prázdnin" if country == COUNTRY_CZ else "Zostáva dní prázdnin"
        super().__init__(config_entry, "vacation_remaining", name, "mdi:beach")

    @property
    def native_value(self) -> int | None:
        """Return remaining vacation days or None."""
        today = self.today
        vacation_name = get_vacation_name(today, self._country, self._region)

        if not vacation_name:
            return None

        # Find end of current vacation
        current = today
        while get_vacation_name(current, self._country, self._region) == vacation_name:
            current += timedelta(days=1)

        return (current - today).days

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        attrs = super().extra_state_attributes.copy()
        today = self.today
        vacation_name = get_vacation_name(today, self._country, self._region)

        attrs["on_vacation"] = vacation_name is not None

        if vacation_name:
            attrs["vacation_name"] = vacation_name

            # Find start
            start = today
            while get_vacation_name(start - timedelta(days=1), self._country, self._region) == vacation_name:
                start -= timedelta(days=1)

            # Find end
            end = today
            while get_vacation_name(end, self._country, self._region) == vacation_name:
                end += timedelta(days=1)
            end -= timedelta(days=1)

            total = (end - start).days + 1
            elapsed = (today - start).days

            attrs["start_date"] = start.isoformat()
            attrs["end_date"] = end.isoformat()
            attrs["total_days"] = total
            attrs["elapsed_days"] = elapsed
            attrs["progress_percent"] = round((elapsed / total) * 100, 1) if total > 0 else 0

        return attrs
