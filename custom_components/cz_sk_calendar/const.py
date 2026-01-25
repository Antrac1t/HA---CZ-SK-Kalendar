"""Constants for CZ/SK School & Work Calendar integration."""
from typing import Final

DOMAIN: Final = "cz_sk_calendar"
CONF_COUNTRY: Final = "country"
CONF_REGION: Final = "region"

# Countries
COUNTRY_CZ: Final = "CZ"
COUNTRY_SK: Final = "SK"

# Czech regions for spring vacation
CZ_REGIONS: Final = {
    "praha": "Praha",
    "stredocesky": "Středočeský kraj",
    "jihocesky": "Jihočeský kraj",
    "plzensky": "Plzeňský kraj",
    "karlovarsky": "Karlovarský kraj",
    "ustecky": "Ústecký kraj",
    "liberecky": "Liberecký kraj",
    "kralovehradecky": "Královéhradecký kraj",
    "pardubicky": "Pardubický kraj",
    "vysocina": "Kraj Vysočina",
    "jihomoravsky": "Jihomoravský kraj",
    "olomoucky": "Olomoucký kraj",
    "zlinsky": "Zlínský kraj",
    "moravskoslezsky": "Moravskoslezský kraj",
}

# Slovak regions for spring vacation
SK_REGIONS: Final = {
    "bratislavsky": "Bratislavský kraj",
    "trnavsky": "Trnavský kraj",
    "nitriansky": "Nitriansky kraj",
    "trenciansky": "Trenčiansky kraj",
    "zilinsky": "Žilinský kraj",
    "banskobystricky": "Banskobystrický kraj",
    "presovsky": "Prešovský kraj",
    "kosicky": "Košický kraj",
}

# Slovak region groups for spring vacation rotation
SK_REGION_GROUPS: Final = {
    "west": ["bratislavsky", "trnavsky", "nitriansky"],
    "central": ["trenciansky", "zilinsky", "banskobystricky"],
    "east": ["presovsky", "kosicky"],
}

# Sensor types
SENSOR_TYPES: Final = {
    "workday": {
        "name": "Workday",
        "icon": "mdi:briefcase",
    },
    "school_day": {
        "name": "School Day",
        "icon": "mdi:school",
    },
    "holiday": {
        "name": "Holiday",
        "icon": "mdi:party-popper",
    },
    "vacation": {
        "name": "Vacation",
        "icon": "mdi:beach",
    },
    "vacation_name": {
        "name": "Vacation Name",
        "icon": "mdi:calendar-text",
    },
    "holiday_name": {
        "name": "Holiday Name",
        "icon": "mdi:calendar-star",
    },
    "next_vacation": {
        "name": "Next Vacation",
        "icon": "mdi:calendar-arrow-right",
    },
    "next_holiday": {
        "name": "Next Holiday",
        "icon": "mdi:calendar-arrow-right",
    },
    "days_to_vacation": {
        "name": "Days to Vacation",
        "icon": "mdi:counter",
    },
    "days_to_holiday": {
        "name": "Days to Holiday",
        "icon": "mdi:counter",
    },
}

# Calendar entity
CALENDAR_NAME: Final = "CZ/SK Calendar"
