"""Sensor platform for CZ/SK School & Work Calendar."""
from __future__ import annotations

from datetime import date, timedelta
import logging
from typing import Any

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
    get_next_vacation,
    get_vacation_name,
    is_school_day,
    is_vacation,
)

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
