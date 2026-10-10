# Tuya RGBIC Segments

Experimentele Home Assistant-service voor onze geteste Tuya RGBIC-strip met 20 segmenten.
Geen algemene ondersteuning voor alle Tuya RGBIC-strips.

## Vereisten

- Een werkend apparaat in [make-all/tuya-local](https://github.com/make-all/tuya-local).
- Het passende deviceprofiel moet de benodigde DP's bevatten.
- DP 103 voor segmentcommando's; DP 20/21 voor de normale route; DP 22/23 voor wit.
- Gebruikt interne Tuya Local-attributen; toekomstige updates kunnen compatibiliteit breken.

## Installatie

1. Kopieer `custom_components/tuya_rgbic_segments` naar dezelfde map onder je Home Assistant-configuratiemap.
2. Voeg aan `configuration.yaml` toe (als dit nog niet bestaat):

```yaml
tuya_rgbic_segments:
```

3. Herstart Home Assistant.
4. Gebruik `tuya_rgbic_segments.set_segments` bij Ontwikkelaarstools → Acties.

Geen HACS-installatie of configuratiewizard inbegrepen.

## Gekozen segmenten groen, achtergrond ongemoeid

De strip moet vooraf aanstaan met de gewenste achtergrond.

```yaml
action: tuya_rgbic_segments.set_segments
data:
  entity_id: light.keuken_keuken_strip
  segments: [3, 4]
  hue: 120
  saturation: 100
  brightness: 100
  preserve_background: true
```

## Alleen gekozen segmenten uit

```yaml
action: tuya_rgbic_segments.set_segments
data:
  entity_id: light.keuken_keuken_strip
  segments: [3, 4]
  erase: true
  preserve_background: true
```

## Eenmalig warmwit met groene segmenten instellen

```yaml
action: tuya_rgbic_segments.set_segments
data:
  entity_id: light.keuken_keuken_strip
  segments: [3, 4]
  hue: 120
  saturation: 100
  brightness: 100
  background_mode: white
  background_brightness: 70
  background_temperature: 0
```

Deze witroute schrijft eerst de hele strip wit, daarna de gekozen segmenten.
Gebruik deze route niet herhaaldelijk om te knipperen; gebruik daarvoor preserve_background.
De gemeten temperatuurschaal is 0 = warm, 1000 = koud; dit zijn geen kelvinwaarden.

## Beperkingen

- `preserve_background: true` stuurt alleen DP 103, zonder extra pauze tussen segmenten.
- Segmenten worden nog afzonderlijk en opeenvolgend verstuurd, niet in één groepscommando.
- Achtergrondbehoud door de firmware en betrouwbare verwerking zonder pauze moeten lokaal worden getest.
- `preserve_background` kan niet samen met `clear_others: true` of `full_pattern`.
- RGB `full_pattern` vereist `clear_others: true`, overschrijft alle segmenten en schakelt naar colour.
- RGB full_pattern behoudt geen echte witte achtergrond; die route gaf op onze strip een paarse achtergrond.
- In de individuele RGB-route wist clear_others de niet-geselecteerde segmenten; RGB-achtergrondvelden worden daar niet gebruikt.
- Niet getest op andere apparaten; witte achtergrondhelderheid 0 is niet bevestigd.
- Geen device-YAML, local key, device ID of andere credentials inbegrepen.

## Bestanden

- `__init__.py`: service en pakketopbouw.
- `manifest.json`: integratiegegevens en afhankelijkheid van Tuya Local.
- `services.yaml`: velden voor de service-interface.

De pakketopbouw komt uit de besproken lokale tests. Dit is geen officiële Tuya Local-uitbreiding.
