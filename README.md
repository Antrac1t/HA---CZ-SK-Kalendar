# CZ/SK School & Work Calendar pro Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/joshuaaaaa/HA---CZ-SK-Kalendar)](https://github.com/joshuaaaaa/HA---CZ-SK-Kalendar/releases)

Dynamický kalendář a senzory školních a pracovních dnů pro **Českou republiku** a **Slovensko**.

## Funkce

### Automatické rozpoznání
- **Pracovní dny** - detekce, zda je dnes pracovní den (není víkend ani svátek)
- **Školní dny** - detekce, zda mají děti školu (není víkend, svátek ani prázdniny)
- **Státní svátky** - včetně automatického výpočtu pohyblivých svátků (Velikonoce)
- **Školní prázdniny** - všechny typy prázdnin s regionálním dělením

### Podporované prázdniny
| Prázdniny | Česká republika | Slovensko |
|-----------|-----------------|-----------|
| Letní | 1.7. - 31.8. | 1.7. - 31.8. |
| Podzimní | čtvrtek a pátek v týdnu s 29.10. | 30.10. - 31.10. |
| Vánoční | 23.12. - 2.1. | 23.12. - 7.1. |
| Pololetní | pátek po konci 1. pololetí | pondělí po konci 1. pololetí |
| Jarní | podle regionu (rotace) | podle regionu (západ/střed/východ) |
| Velikonoční | čtvrtek - pondělí | čtvrtek - úterý |

### Regionální podpora jarních prázdnin

#### Česká republika (14 krajů)
Praha, Středočeský, Jihočeský, Plzeňský, Karlovarský, Ústecký, Liberecký, Královéhradecký, Pardubický, Vysočina, Jihomoravský, Olomoucký, Zlínský, Moravskoslezský

#### Slovensko (8 krajů)
- **Západ**: Bratislavský, Trnavský, Nitriansky
- **Střed**: Trenčiansky, Žilinský, Banskobystrický
- **Východ**: Prešovský, Košický

## Instalace

### HACS (doporučeno)

1. Otevřete HACS v Home Assistant
2. Klikněte na "Integrations"
3. Klikněte na tři tečky vpravo nahoře → "Custom repositories"
4. Přidejte URL: `https://github.com/joshuaaaaa/HA---CZ-SK-Kalendar`
5. Vyberte kategorii "Integration"
6. Klikněte "Add"
7. Vyhledejte "CZ/SK Calendar" a nainstalujte
8. Restartujte Home Assistant

### Ruční instalace

1. Stáhněte složku `custom_components/cz_sk_calendar`
2. Zkopírujte ji do `<config>/custom_components/`
3. Restartujte Home Assistant

## Konfigurace

1. Přejděte do Nastavení → Zařízení a služby
2. Klikněte "Přidat integraci"
3. Vyhledejte "CZ/SK School & Work Calendar"
4. Vyberte zemi (Česká republika / Slovensko)
5. Vyberte váš region

## Vytvořené entity

### Senzory (binary_sensor pattern)

| Senzor | Popis | Hodnota |
|--------|-------|---------|
| `sensor.workday` | Je dnes pracovní den? | `True` / `False` |
| `sensor.school_day` | Je dnes školní den? | `True` / `False` |
| `sensor.holiday` | Je dnes svátek? | `True` / `False` |
| `sensor.vacation` | Jsou dnes prázdniny? | `True` / `False` |
| `sensor.holiday_name` | Název dnešního svátku | text nebo `None` |
| `sensor.vacation_name` | Název aktuálních prázdnin | text nebo `None` |
| `sensor.next_holiday` | Název příštího svátku | text |
| `sensor.next_vacation` | Název příštích prázdnin | text |
| `sensor.days_to_holiday` | Dní do příštího svátku | číslo |
| `sensor.days_to_vacation` | Dní do příštích prázdnin | číslo |

### Kalendáře

| Kalendář | Popis |
|----------|-------|
| `calendar.svatky` | Pouze státní svátky |
| `calendar.skolni_prazdniny` | Pouze školní prázdniny |
| `calendar.svatky_a_prazdniny` | Kombinovaný kalendář |

## Příklady automatizací

### Budík pouze ve školní dny
```yaml
automation:
  - alias: "Školní budík"
    trigger:
      - platform: time
        at: "06:30:00"
    condition:
      - condition: state
        entity_id: sensor.cz_sk_calendar_school_day
        state: "True"
    action:
      - service: media_player.play_media
        target:
          entity_id: media_player.bedroom
        data:
          media_content_id: "alarm.mp3"
          media_content_type: "music"
```

### Oznámení o blížících se prázdninách
```yaml
automation:
  - alias: "Oznámení o prázdninách"
    trigger:
      - platform: numeric_state
        entity_id: sensor.cz_sk_calendar_days_to_vacation
        below: 8
    action:
      - service: notify.mobile_app
        data:
          title: "Prázdniny se blíží!"
          message: >
            Za {{ states('sensor.cz_sk_calendar_days_to_vacation') }} dní začínají
            {{ state_attr('sensor.cz_sk_calendar_next_vacation', 'friendly_name') }}
```

### Jiný režim topení o prázdninách
```yaml
automation:
  - alias: "Prázdninový režim topení"
    trigger:
      - platform: state
        entity_id: sensor.cz_sk_calendar_vacation
        to: "True"
    action:
      - service: climate.set_preset_mode
        target:
          entity_id: climate.thermostat
        data:
          preset_mode: "away"
```

## Pohyblivé svátky

Integrace automaticky vypočítává datum Velikonoc pomocí algoritmu Computus (Anonymní Gregoriánský algoritmus), který je platný pro libovolný rok gregoriánského kalendáře.

Od data Velikonoční neděle se odvozují:
- **Velký pátek** (CZ/SK) - 2 dny před Velikonoční nedělí
- **Velikonoční pondělí** (CZ/SK) - 1 den po Velikonoční neděli

## Podpora

Máte-li problémy nebo návrhy na vylepšení, vytvořte [issue na GitHubu](https://github.com/joshuaaaaa/HA---CZ-SK-Kalendar/issues).

## Licence

MIT License - viz soubor [LICENSE](LICENSE)
