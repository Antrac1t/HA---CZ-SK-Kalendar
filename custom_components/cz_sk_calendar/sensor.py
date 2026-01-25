"""Sensor platform for CZ/SK School & Work Calendar."""
from __future__ import annotations

from datetime import date, timedelta
import logging
from typing import Any
import calendar

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_change

from .const import (
    CONF_COUNTRY,
    CONF_REGION,
    CZ_REGIONS,
    DOMAIN,
    SENSOR_TYPES,
    SK_REGIONS,
    COUNTRY_CZ,
)
from .holidays import (
    get_all_holidays,
    get_holiday_name,
    get_next_holiday,
    is_holiday,
    is_workday,
)
from .vacations import (
    get_all_vacations,
    get_next_vacation,
    get_school_year,
    get_vacation_name,
    is_school_day,
    is_vacation,
)
from .namedays import get_nameday, get_next_nameday, get_namedays_in_week
from .special_days import get_special_day_name, get_next_special_day

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the CZ/SK Calendar sensors."""
    country = config_entry.data[CONF_COUNTRY]
    region = config_entry.data[CONF_REGION]

    sensors = [
        CZSKWorkdaySensor(config_entry, country, region),
        CZSKSchoolDaySensor(config_entry, country, region),
        CZSKHolidaySensor(config_entry, country, region),
        CZSKVacationSensor(config_entry, country, region),
        CZSKHolidayNameSensor(config_entry, country, region),
        CZSKVacationNameSensor(config_entry, country, region),
        CZSKNextHolidaySensor(config_entry, country, region),
        CZSKNextVacationSensor(config_entry, country, region),
        CZSKDaysToHolidaySensor(config_entry, country, region),
        CZSKDaysToVacationSensor(config_entry, country, region),
        # New sensors
        CZSKSchoolYearSensor(config_entry, country, region),
        CZSKNamedaySensor(config_entry, country, region),
        CZSKSpecialDaySensor(config_entry, country, region),
        CZSKWorkdaysInMonthSensor(config_entry, country, region),
        CZSKSchoolDaysInMonthSensor(config_entry, country, region),
        CZSKVacationDaysRemainingSensor(config_entry, country, region),
        CZSKWorkdaysToWeekendSensor(config_entry, country, region),
        CZSKSchoolDaysToVacationSensor(config_entry, country, region),
    ]

    async_add_entities(sensors, True)


class CZSKBaseSensor(SensorEntity):
    """Base class for CZ/SK Calendar sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        config_entry: ConfigEntry,
        country: str,
        region: str,
        sensor_type: str,
    ) -> None:
        """Initialize the sensor."""
        self._config_entry = config_entry
        self._country = country
        self._region = region
        self._sensor_type = sensor_type

        region_name = (
            CZ_REGIONS.get(region, region)
            if country == COUNTRY_CZ
            else SK_REGIONS.get(region, region)
        )

        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_type}"
        self._attr_name = SENSOR_TYPES[sensor_type]["name"]
        self._attr_icon = SENSOR_TYPES[sensor_type]["icon"]
        self._attr_extra_state_attributes = {
            "country": country,
            "region": region,
            "region_name": region_name,
        }

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": f"CZ/SK Calendar ({self._config_entry.title})",
            "manufacturer": "CZ/SK Calendar",
            "model": f"{self._country} Calendar",
        }

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""
        # Update at midnight
        self.async_on_remove(
            async_track_time_change(
                self.hass, self._async_update_at_midnight, hour=0, minute=0, second=0
            )
        )

    @callback
    def _async_update_at_midnight(self, now=None) -> None:
        """Update the sensor at midnight."""
        self.async_schedule_update_ha_state(True)


class CZSKWorkdaySensor(CZSKBaseSensor):
    """Sensor for workday detection."""

    def __init__(
        self, config_entry: ConfigEntry, country: str, region: str
    ) -> None:
        """Initialize the workday sensor."""
        super().__init__(config_entry, country, region, "workday")

    @property
    def native_value(self) -> bool:
        """Return True if today is a workday."""
        return is_workday(date.today(), self._country)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        today = date.today()
        tomorrow = today + timedelta(days=1)
        attrs = super().extra_state_attributes.copy()
        attrs["tomorrow_is_workday"] = is_workday(tomorrow, self._country)
        return attrs


class CZSKSchoolDaySensor(CZSKBaseSensor):
    """Sensor for school day detection."""

    def __init__(
        self, config_entry: ConfigEntry, country: str, region: str
    ) -> None:
        """Initialize the school day sensor."""
        super().__init__(config_entry, country, region, "school_day")

    @property
    def native_value(self) -> bool:
        """Return True if today is a school day."""
        return is_school_day(date.today(), self._country, self._region)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        today = date.today()
        tomorrow = today + timedelta(days=1)
        attrs = super().extra_state_attributes.copy()
        attrs["tomorrow_is_school_day"] = is_school_day(
            tomorrow, self._country, self._region
        )
        return attrs


class CZSKHolidaySensor(CZSKBaseSensor):
    """Sensor for holiday detection."""

    def __init__(
        self, config_entry: ConfigEntry, country: str, region: str
    ) -> None:
        """Initialize the holiday sensor."""
        super().__init__(config_entry, country, region, "holiday")

    @property
    def native_value(self) -> bool:
        """Return True if today is a holiday."""
        return is_holiday(date.today(), self._country)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        today = date.today()
        attrs = super().extra_state_attributes.copy()
        attrs["holiday_name"] = get_holiday_name(today, self._country)

        # List all holidays for current year
        holidays = get_all_holidays(today.year, self._country)
        attrs["holidays_this_year"] = {
            d.isoformat(): name for d, name in sorted(holidays.items())
        }
        return attrs


class CZSKVacationSensor(CZSKBaseSensor):
    """Sensor for vacation detection."""

    def __init__(
        self, config_entry: ConfigEntry, country: str, region: str
    ) -> None:
        """Initialize the vacation sensor."""
        super().__init__(config_entry, country, region, "vacation")

    @property
    def native_value(self) -> bool:
        """Return True if today is during vacation."""
        return is_vacation(date.today(), self._country, self._region)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        today = date.today()
        attrs = super().extra_state_attributes.copy()
        attrs["vacation_name"] = get_vacation_name(today, self._country, self._region)
        return attrs


class CZSKHolidayNameSensor(CZSKBaseSensor):
    """Sensor for current holiday name."""

    def __init__(
        self, config_entry: ConfigEntry, country: str, region: str
    ) -> None:
        """Initialize the holiday name sensor."""
        super().__init__(config_entry, country, region, "holiday_name")

    @property
    def native_value(self) -> str | None:
        """Return the name of today's holiday, or None."""
        return get_holiday_name(date.today(), self._country)


class CZSKVacationNameSensor(CZSKBaseSensor):
    """Sensor for current vacation name."""

    def __init__(
        self, config_entry: ConfigEntry, country: str, region: str
    ) -> None:
        """Initialize the vacation name sensor."""
        super().__init__(config_entry, country, region, "vacation_name")

    @property
    def native_value(self) -> str | None:
        """Return the name of current vacation, or None."""
        return get_vacation_name(date.today(), self._country, self._region)


class CZSKNextHolidaySensor(CZSKBaseSensor):
    """Sensor for next holiday."""

    def __init__(
        self, config_entry: ConfigEntry, country: str, region: str
    ) -> None:
        """Initialize the next holiday sensor."""
        super().__init__(config_entry, country, region, "next_holiday")

    @property
    def native_value(self) -> str:
        """Return the name of the next holiday."""
        today = date.today()
        next_date, name = get_next_holiday(today + timedelta(days=1), self._country)
        return name

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        today = date.today()
        next_date, name = get_next_holiday(today + timedelta(days=1), self._country)
        attrs = super().extra_state_attributes.copy()
        attrs["date"] = next_date.isoformat()
        attrs["days_until"] = (next_date - today).days
        return attrs


class CZSKNextVacationSensor(CZSKBaseSensor):
    """Sensor for next vacation."""

    def __init__(
        self, config_entry: ConfigEntry, country: str, region: str
    ) -> None:
        """Initialize the next vacation sensor."""
        super().__init__(config_entry, country, region, "next_vacation")

    @property
    def native_value(self) -> str:
        """Return the name of the next vacation."""
        today = date.today()
        # If currently on vacation, get the next one after today
        if is_vacation(today, self._country, self._region):
            start, name, end = get_next_vacation(
                today + timedelta(days=1), self._country, self._region
            )
        else:
            start, name, end = get_next_vacation(today, self._country, self._region)
        return name

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        today = date.today()
        if is_vacation(today, self._country, self._region):
            start, name, end = get_next_vacation(
                today + timedelta(days=1), self._country, self._region
            )
        else:
            start, name, end = get_next_vacation(today, self._country, self._region)
        attrs = super().extra_state_attributes.copy()
        attrs["start_date"] = start.isoformat()
        attrs["end_date"] = end.isoformat()
        attrs["days_until"] = (start - today).days
        attrs["duration_days"] = (end - start).days + 1
        return attrs


class CZSKDaysToHolidaySensor(CZSKBaseSensor):
    """Sensor for days until next holiday."""

    def __init__(
        self, config_entry: ConfigEntry, country: str, region: str
    ) -> None:
        """Initialize the days to holiday sensor."""
        super().__init__(config_entry, country, region, "days_to_holiday")

    @property
    def native_value(self) -> int:
        """Return days until next holiday."""
        today = date.today()
        if is_holiday(today, self._country):
            return 0
        next_date, _ = get_next_holiday(today + timedelta(days=1), self._country)
        return (next_date - today).days

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return "days"


class CZSKDaysToVacationSensor(CZSKBaseSensor):
    """Sensor for days until next vacation."""

    def __init__(
        self, config_entry: ConfigEntry, country: str, region: str
    ) -> None:
        """Initialize the days to vacation sensor."""
        super().__init__(config_entry, country, region, "days_to_vacation")

    @property
    def native_value(self) -> int:
        """Return days until next vacation."""
        today = date.today()
        if is_vacation(today, self._country, self._region):
            return 0
        start, _, _ = get_next_vacation(today, self._country, self._region)
        return (start - today).days

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return "days"


class CZSKSchoolYearSensor(SensorEntity):
    """Sensor for school year information."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:school"

    def __init__(
        self, config_entry: ConfigEntry, country: str, region: str
    ) -> None:
        """Initialize the school year sensor."""
        self._config_entry = config_entry
        self._country = country
        self._region = region

        region_name = (
            CZ_REGIONS.get(region, region)
            if country == COUNTRY_CZ
            else SK_REGIONS.get(region, region)
        )

        self._attr_unique_id = f"{config_entry.entry_id}_school_year"
        self._attr_name = "Školní rok" if country == COUNTRY_CZ else "Školský rok"
        self._attr_extra_state_attributes = {
            "country": country,
            "region": region,
            "region_name": region_name,
        }

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": f"CZ/SK Calendar ({self._config_entry.title})",
            "manufacturer": "CZ/SK Calendar",
            "model": f"{self._country} Calendar",
        }

    @property
    def native_value(self) -> str:
        """Return the current school year."""
        school_year = get_school_year(date.today())
        return f"{school_year}/{school_year + 1}"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        today = date.today()
        school_year = get_school_year(today)
        attrs = dict(self._attr_extra_state_attributes)

        # School year start and end
        # CZ: September 1 - June 30
        # SK: September 2 - June 30
        start_day = 2 if self._country == "SK" else 1
        start_date = date(school_year, 9, start_day)
        end_date = date(school_year + 1, 6, 30)

        attrs["start_date"] = start_date.isoformat()
        attrs["end_date"] = end_date.isoformat()
        attrs["start_year"] = school_year
        attrs["end_year"] = school_year + 1

        # Days in school year
        total_days = (end_date - start_date).days + 1
        elapsed_days = (today - start_date).days
        remaining_days = (end_date - today).days

        attrs["total_days"] = total_days
        attrs["elapsed_days"] = max(0, elapsed_days)
        attrs["remaining_days"] = max(0, remaining_days)

        # Progress percentage
        if total_days > 0 and elapsed_days >= 0:
            progress = min(100, (elapsed_days / total_days) * 100)
            attrs["progress_percent"] = round(progress, 1)
        else:
            attrs["progress_percent"] = 0

        # Get all vacations for this school year
        vacations = get_all_vacations(school_year, self._country, self._region)
        attrs["vacations"] = [
            {"name": name, "start": start.isoformat(), "end": end.isoformat()}
            for start, end, name in sorted(vacations, key=lambda x: x[0])
        ]

        return attrs

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""
        self.async_on_remove(
            async_track_time_change(
                self.hass, self._async_update_at_midnight, hour=0, minute=0, second=0
            )
        )

    @callback
    def _async_update_at_midnight(self, now=None) -> None:
        """Update the sensor at midnight."""
        self.async_schedule_update_ha_state(True)


class CZSKNamedaySensor(SensorEntity):
    """Sensor for today's name day."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:cake-variant"

    def __init__(
        self, config_entry: ConfigEntry, country: str, region: str
    ) -> None:
        """Initialize the name day sensor."""
        self._config_entry = config_entry
        self._country = country
        self._region = region

        self._attr_unique_id = f"{config_entry.entry_id}_nameday"
        self._attr_name = "Jmeniny" if country == COUNTRY_CZ else "Meniny"

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": f"CZ/SK Calendar ({self._config_entry.title})",
            "manufacturer": "CZ/SK Calendar",
            "model": f"{self._country} Calendar",
        }

    @property
    def native_value(self) -> str | None:
        """Return today's name day."""
        return get_nameday(date.today(), self._country)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        today = date.today()
        tomorrow = today + timedelta(days=1)
        attrs = {}

        # Tomorrow's name day
        attrs["tomorrow"] = get_nameday(tomorrow, self._country)

        # This week's name days
        week_namedays = get_namedays_in_week(today, self._country)
        attrs["this_week"] = {
            d.isoformat(): name for d, name in sorted(week_namedays.items())
        }

        return attrs

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""
        self.async_on_remove(
            async_track_time_change(
                self.hass, self._async_update_at_midnight, hour=0, minute=0, second=0
            )
        )

    @callback
    def _async_update_at_midnight(self, now=None) -> None:
        """Update the sensor at midnight."""
        self.async_schedule_update_ha_state(True)


class CZSKSpecialDaySensor(SensorEntity):
    """Sensor for today's special day."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:star"

    def __init__(
        self, config_entry: ConfigEntry, country: str, region: str
    ) -> None:
        """Initialize the special day sensor."""
        self._config_entry = config_entry
        self._country = country
        self._region = region

        self._attr_unique_id = f"{config_entry.entry_id}_special_day"
        self._attr_name = "Významný den" if country == COUNTRY_CZ else "Významný deň"

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": f"CZ/SK Calendar ({self._config_entry.title})",
            "manufacturer": "CZ/SK Calendar",
            "model": f"{self._country} Calendar",
        }

    @property
    def native_value(self) -> str | None:
        """Return today's special day name."""
        return get_special_day_name(date.today(), self._country)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        today = date.today()
        attrs = {}

        # Next special day
        next_date, next_name = get_next_special_day(today + timedelta(days=1), self._country)
        attrs["next_special_day"] = next_name
        attrs["next_special_day_date"] = next_date.isoformat()
        attrs["days_to_next"] = (next_date - today).days

        return attrs

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""
        self.async_on_remove(
            async_track_time_change(
                self.hass, self._async_update_at_midnight, hour=0, minute=0, second=0
            )
        )

    @callback
    def _async_update_at_midnight(self, now=None) -> None:
        """Update the sensor at midnight."""
        self.async_schedule_update_ha_state(True)


class CZSKWorkdaysInMonthSensor(SensorEntity):
    """Sensor for workdays remaining in current month."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:calendar-month"
    _attr_native_unit_of_measurement = "days"

    def __init__(
        self, config_entry: ConfigEntry, country: str, region: str
    ) -> None:
        """Initialize the workdays in month sensor."""
        self._config_entry = config_entry
        self._country = country
        self._region = region

        self._attr_unique_id = f"{config_entry.entry_id}_workdays_in_month"
        self._attr_name = "Pracovní dny v měsíci" if country == COUNTRY_CZ else "Pracovné dni v mesiaci"

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": f"CZ/SK Calendar ({self._config_entry.title})",
            "manufacturer": "CZ/SK Calendar",
            "model": f"{self._country} Calendar",
        }

    @property
    def native_value(self) -> int:
        """Return remaining workdays in current month."""
        today = date.today()
        _, last_day = calendar.monthrange(today.year, today.month)

        remaining = 0
        for day in range(today.day, last_day + 1):
            check_date = date(today.year, today.month, day)
            if is_workday(check_date, self._country):
                remaining += 1

        return remaining

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        today = date.today()
        _, last_day = calendar.monthrange(today.year, today.month)

        total_workdays = 0
        elapsed_workdays = 0
        for day in range(1, last_day + 1):
            check_date = date(today.year, today.month, day)
            if is_workday(check_date, self._country):
                total_workdays += 1
                if day < today.day:
                    elapsed_workdays += 1

        return {
            "total_workdays_in_month": total_workdays,
            "elapsed_workdays": elapsed_workdays,
            "month": today.strftime("%B"),
            "year": today.year,
        }

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""
        self.async_on_remove(
            async_track_time_change(
                self.hass, self._async_update_at_midnight, hour=0, minute=0, second=0
            )
        )

    @callback
    def _async_update_at_midnight(self, now=None) -> None:
        """Update the sensor at midnight."""
        self.async_schedule_update_ha_state(True)


class CZSKSchoolDaysInMonthSensor(SensorEntity):
    """Sensor for school days remaining in current month."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:calendar-month"
    _attr_native_unit_of_measurement = "days"

    def __init__(
        self, config_entry: ConfigEntry, country: str, region: str
    ) -> None:
        """Initialize the school days in month sensor."""
        self._config_entry = config_entry
        self._country = country
        self._region = region

        self._attr_unique_id = f"{config_entry.entry_id}_school_days_in_month"
        self._attr_name = "Školní dny v měsíci" if country == COUNTRY_CZ else "Školské dni v mesiaci"

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": f"CZ/SK Calendar ({self._config_entry.title})",
            "manufacturer": "CZ/SK Calendar",
            "model": f"{self._country} Calendar",
        }

    @property
    def native_value(self) -> int:
        """Return remaining school days in current month."""
        today = date.today()
        _, last_day = calendar.monthrange(today.year, today.month)

        remaining = 0
        for day in range(today.day, last_day + 1):
            check_date = date(today.year, today.month, day)
            if is_school_day(check_date, self._country, self._region):
                remaining += 1

        return remaining

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        today = date.today()
        _, last_day = calendar.monthrange(today.year, today.month)

        total_school_days = 0
        elapsed_school_days = 0
        for day in range(1, last_day + 1):
            check_date = date(today.year, today.month, day)
            if is_school_day(check_date, self._country, self._region):
                total_school_days += 1
                if day < today.day:
                    elapsed_school_days += 1

        return {
            "total_school_days_in_month": total_school_days,
            "elapsed_school_days": elapsed_school_days,
            "month": today.strftime("%B"),
            "year": today.year,
        }

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""
        self.async_on_remove(
            async_track_time_change(
                self.hass, self._async_update_at_midnight, hour=0, minute=0, second=0
            )
        )

    @callback
    def _async_update_at_midnight(self, now=None) -> None:
        """Update the sensor at midnight."""
        self.async_schedule_update_ha_state(True)


class CZSKVacationDaysRemainingSensor(SensorEntity):
    """Sensor for vacation days remaining (if on vacation)."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:beach"
    _attr_native_unit_of_measurement = "days"

    def __init__(
        self, config_entry: ConfigEntry, country: str, region: str
    ) -> None:
        """Initialize the vacation days remaining sensor."""
        self._config_entry = config_entry
        self._country = country
        self._region = region

        self._attr_unique_id = f"{config_entry.entry_id}_vacation_days_remaining"
        self._attr_name = "Zbývá dní prázdnin" if country == COUNTRY_CZ else "Zostáva dní prázdnin"

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": f"CZ/SK Calendar ({self._config_entry.title})",
            "manufacturer": "CZ/SK Calendar",
            "model": f"{self._country} Calendar",
        }

    @property
    def native_value(self) -> int | None:
        """Return remaining vacation days or None if not on vacation."""
        today = date.today()
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
        today = date.today()
        vacation_name = get_vacation_name(today, self._country, self._region)

        if not vacation_name:
            return {"on_vacation": False}

        # Find start and end of current vacation
        start = today
        while get_vacation_name(start - timedelta(days=1), self._country, self._region) == vacation_name:
            start -= timedelta(days=1)

        end = today
        while get_vacation_name(end, self._country, self._region) == vacation_name:
            end += timedelta(days=1)
        end -= timedelta(days=1)

        total_days = (end - start).days + 1
        elapsed_days = (today - start).days

        return {
            "on_vacation": True,
            "vacation_name": vacation_name,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "total_days": total_days,
            "elapsed_days": elapsed_days,
            "progress_percent": round((elapsed_days / total_days) * 100, 1) if total_days > 0 else 0,
        }

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""
        self.async_on_remove(
            async_track_time_change(
                self.hass, self._async_update_at_midnight, hour=0, minute=0, second=0
            )
        )

    @callback
    def _async_update_at_midnight(self, now=None) -> None:
        """Update the sensor at midnight."""
        self.async_schedule_update_ha_state(True)


class CZSKWorkdaysToWeekendSensor(SensorEntity):
    """Sensor for workdays until weekend."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:calendar-weekend"
    _attr_native_unit_of_measurement = "days"

    def __init__(
        self, config_entry: ConfigEntry, country: str, region: str
    ) -> None:
        """Initialize the workdays to weekend sensor."""
        self._config_entry = config_entry
        self._country = country
        self._region = region

        self._attr_unique_id = f"{config_entry.entry_id}_workdays_to_weekend"
        self._attr_name = "Pracovní dny do víkendu" if country == COUNTRY_CZ else "Pracovné dni do víkendu"

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": f"CZ/SK Calendar ({self._config_entry.title})",
            "manufacturer": "CZ/SK Calendar",
            "model": f"{self._country} Calendar",
        }

    @property
    def native_value(self) -> int:
        """Return workdays until weekend (Saturday)."""
        today = date.today()

        # If it's weekend, return 0
        if today.weekday() >= 5:
            return 0

        # Count workdays until Saturday
        count = 0
        current = today
        while current.weekday() < 5:  # While not Saturday
            if is_workday(current, self._country):
                count += 1
            current += timedelta(days=1)

        return count

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        today = date.today()

        # Find next Saturday
        days_to_saturday = (5 - today.weekday()) % 7
        if days_to_saturday == 0 and today.weekday() != 5:
            days_to_saturday = 7
        next_saturday = today + timedelta(days=days_to_saturday)

        return {
            "next_weekend": next_saturday.isoformat(),
            "is_weekend": today.weekday() >= 5,
            "day_of_week": today.strftime("%A"),
        }

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""
        self.async_on_remove(
            async_track_time_change(
                self.hass, self._async_update_at_midnight, hour=0, minute=0, second=0
            )
        )

    @callback
    def _async_update_at_midnight(self, now=None) -> None:
        """Update the sensor at midnight."""
        self.async_schedule_update_ha_state(True)


class CZSKSchoolDaysToVacationSensor(SensorEntity):
    """Sensor for school days until next vacation."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:school"
    _attr_native_unit_of_measurement = "days"

    def __init__(
        self, config_entry: ConfigEntry, country: str, region: str
    ) -> None:
        """Initialize the school days to vacation sensor."""
        self._config_entry = config_entry
        self._country = country
        self._region = region

        self._attr_unique_id = f"{config_entry.entry_id}_school_days_to_vacation"
        self._attr_name = "Školní dny do prázdnin" if country == COUNTRY_CZ else "Školské dni do prázdnin"

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": f"CZ/SK Calendar ({self._config_entry.title})",
            "manufacturer": "CZ/SK Calendar",
            "model": f"{self._country} Calendar",
        }

    @property
    def native_value(self) -> int:
        """Return school days until next vacation."""
        today = date.today()

        # If on vacation, return 0
        if is_vacation(today, self._country, self._region):
            return 0

        # Get next vacation start
        start, name, _ = get_next_vacation(today, self._country, self._region)

        # Count school days until vacation
        count = 0
        current = today
        while current < start:
            if is_school_day(current, self._country, self._region):
                count += 1
            current += timedelta(days=1)

        return count

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        today = date.today()

        if is_vacation(today, self._country, self._region):
            return {"on_vacation": True}

        start, name, end = get_next_vacation(today, self._country, self._region)

        return {
            "on_vacation": False,
            "next_vacation": name,
            "next_vacation_start": start.isoformat(),
            "next_vacation_end": end.isoformat(),
        }

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""
        self.async_on_remove(
            async_track_time_change(
                self.hass, self._async_update_at_midnight, hour=0, minute=0, second=0
            )
        )

    @callback
    def _async_update_at_midnight(self, now=None) -> None:
        """Update the sensor at midnight."""
        self.async_schedule_update_ha_state(True)
