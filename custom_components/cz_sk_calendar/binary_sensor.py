"""Binary sensor platform for CZ/SK School & Work Calendar."""
from __future__ import annotations

from datetime import date, timedelta
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_change

from .const import (
    CONF_COUNTRY,
    CONF_REGION,
    CZ_REGIONS,
    DOMAIN,
    SK_REGIONS,
    COUNTRY_CZ,
)
from .holidays import is_holiday, get_holiday_name
from .vacations import is_school_day, is_vacation, get_vacation_name
from .special_days import is_special_day, get_special_day_name

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the CZ/SK Calendar binary sensors."""
    country = config_entry.data[CONF_COUNTRY]
    region = config_entry.data[CONF_REGION]

    sensors = [
        CZSKWorkdayBinarySensor(config_entry, country, region),
        CZSKSchoolDayBinarySensor(config_entry, country, region),
        CZSKHolidayBinarySensor(config_entry, country, region),
        CZSKVacationBinarySensor(config_entry, country, region),
        CZSKWeekendBinarySensor(config_entry, country, region),
        CZSKSpecialDayBinarySensor(config_entry, country, region),
    ]

    async_add_entities(sensors, True)


class CZSKBaseBinarySensor(BinarySensorEntity):
    """Base class for CZ/SK Calendar binary sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        config_entry: ConfigEntry,
        country: str,
        region: str,
        sensor_type: str,
        name: str,
        icon_on: str,
        icon_off: str,
    ) -> None:
        """Initialize the binary sensor."""
        self._config_entry = config_entry
        self._country = country
        self._region = region
        self._sensor_type = sensor_type
        self._icon_on = icon_on
        self._icon_off = icon_off

        region_name = (
            CZ_REGIONS.get(region, region)
            if country == COUNTRY_CZ
            else SK_REGIONS.get(region, region)
        )

        self._attr_unique_id = f"{config_entry.entry_id}_binary_{sensor_type}"
        self._attr_name = name
        self._attr_extra_state_attributes = {
            "country": country,
            "region": region,
            "region_name": region_name,
        }

    @property
    def icon(self) -> str:
        """Return the icon based on state."""
        return self._icon_on if self.is_on else self._icon_off

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
        self.async_on_remove(
            async_track_time_change(
                self.hass, self._async_update_at_midnight, hour=0, minute=0, second=0
            )
        )

    @callback
    def _async_update_at_midnight(self, now=None) -> None:
        """Update the sensor at midnight."""
        self.async_schedule_update_ha_state(True)


class CZSKWorkdayBinarySensor(CZSKBaseBinarySensor):
    """Binary sensor for workday detection."""

    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY

    def __init__(
        self, config_entry: ConfigEntry, country: str, region: str
    ) -> None:
        """Initialize the workday binary sensor."""
        name = "Pracovní den" if country == COUNTRY_CZ else "Pracovný deň"
        super().__init__(
            config_entry, country, region, "workday", name,
            "mdi:briefcase", "mdi:briefcase-off"
        )

    @property
    def is_on(self) -> bool:
        """Return True if today is a workday."""
        today = date.today()
        # Weekend check
        if today.weekday() >= 5:
            return False
        # Holiday check
        if is_holiday(today, self._country):
            return False
        return True

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        today = date.today()
        tomorrow = today + timedelta(days=1)
        attrs = dict(self._attr_extra_state_attributes)

        # Tomorrow check
        tomorrow_is_workday = tomorrow.weekday() < 5 and not is_holiday(tomorrow, self._country)
        attrs["tomorrow"] = tomorrow_is_workday

        # Holiday name if today is holiday
        holiday = get_holiday_name(today, self._country)
        if holiday:
            attrs["holiday_name"] = holiday

        return attrs


class CZSKSchoolDayBinarySensor(CZSKBaseBinarySensor):
    """Binary sensor for school day detection."""

    def __init__(
        self, config_entry: ConfigEntry, country: str, region: str
    ) -> None:
        """Initialize the school day binary sensor."""
        name = "Školní den" if country == COUNTRY_CZ else "Školský deň"
        super().__init__(
            config_entry, country, region, "school_day", name,
            "mdi:school", "mdi:school-outline"
        )

    @property
    def is_on(self) -> bool:
        """Return True if today is a school day."""
        return is_school_day(date.today(), self._country, self._region)

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        today = date.today()
        tomorrow = today + timedelta(days=1)
        attrs = dict(self._attr_extra_state_attributes)
        attrs["tomorrow"] = is_school_day(tomorrow, self._country, self._region)

        # Reason if not school day
        if not self.is_on:
            if today.weekday() >= 5:
                attrs["reason"] = "weekend"
            elif is_holiday(today, self._country):
                attrs["reason"] = "holiday"
                attrs["holiday_name"] = get_holiday_name(today, self._country)
            elif is_vacation(today, self._country, self._region):
                attrs["reason"] = "vacation"
                attrs["vacation_name"] = get_vacation_name(today, self._country, self._region)

        return attrs


class CZSKHolidayBinarySensor(CZSKBaseBinarySensor):
    """Binary sensor for holiday detection."""

    def __init__(
        self, config_entry: ConfigEntry, country: str, region: str
    ) -> None:
        """Initialize the holiday binary sensor."""
        name = "Svátek" if country == COUNTRY_CZ else "Sviatok"
        super().__init__(
            config_entry, country, region, "holiday", name,
            "mdi:party-popper", "mdi:calendar-blank"
        )

    @property
    def is_on(self) -> bool:
        """Return True if today is a holiday."""
        return is_holiday(date.today(), self._country)

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        today = date.today()
        attrs = dict(self._attr_extra_state_attributes)

        holiday = get_holiday_name(today, self._country)
        if holiday:
            attrs["name"] = holiday

        return attrs


class CZSKVacationBinarySensor(CZSKBaseBinarySensor):
    """Binary sensor for vacation detection."""

    def __init__(
        self, config_entry: ConfigEntry, country: str, region: str
    ) -> None:
        """Initialize the vacation binary sensor."""
        name = "Prázdniny" if country == COUNTRY_CZ else "Prázdniny"
        super().__init__(
            config_entry, country, region, "vacation", name,
            "mdi:beach", "mdi:calendar-blank"
        )

    @property
    def is_on(self) -> bool:
        """Return True if today is during vacation."""
        return is_vacation(date.today(), self._country, self._region)

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        today = date.today()
        attrs = dict(self._attr_extra_state_attributes)

        vacation = get_vacation_name(today, self._country, self._region)
        if vacation:
            attrs["name"] = vacation

        return attrs


class CZSKWeekendBinarySensor(CZSKBaseBinarySensor):
    """Binary sensor for weekend detection."""

    def __init__(
        self, config_entry: ConfigEntry, country: str, region: str
    ) -> None:
        """Initialize the weekend binary sensor."""
        name = "Víkend" if country == COUNTRY_CZ else "Víkend"
        super().__init__(
            config_entry, country, region, "weekend", name,
            "mdi:weather-sunny", "mdi:briefcase"
        )

    @property
    def is_on(self) -> bool:
        """Return True if today is weekend."""
        return date.today().weekday() >= 5

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        today = date.today()
        attrs = dict(self._attr_extra_state_attributes)
        attrs["day_of_week"] = today.strftime("%A")
        attrs["day_number"] = today.weekday()
        return attrs


class CZSKSpecialDayBinarySensor(CZSKBaseBinarySensor):
    """Binary sensor for special day detection."""

    def __init__(
        self, config_entry: ConfigEntry, country: str, region: str
    ) -> None:
        """Initialize the special day binary sensor."""
        name = "Významný den" if country == COUNTRY_CZ else "Významný deň"
        super().__init__(
            config_entry, country, region, "special_day", name,
            "mdi:star", "mdi:star-outline"
        )

    @property
    def is_on(self) -> bool:
        """Return True if today is a special day."""
        return is_special_day(date.today(), self._country)

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        today = date.today()
        attrs = dict(self._attr_extra_state_attributes)

        special = get_special_day_name(today, self._country)
        if special:
            attrs["name"] = special

        return attrs
