"""Experimental segment service for the tested 20-segment Tuya strip."""
import asyncio
import base64
import struct
import voluptuous as vol
from homeassistant.exceptions import HomeAssistantError

DOMAIN = "tuya_rgbic_segments"
SEGMENT_COUNT = 20
COMMAND_DELAY = 0.15

def percent():
    return vol.All(vol.Coerce(float), vol.Range(min=0, max=100))

def hue():
    return vol.All(vol.Coerce(float), vol.Range(min=0, max=360))

SCHEMA = vol.Schema({
    vol.Required("entity_id"): str,
    vol.Required("segments"): [vol.All(vol.Coerce(int), vol.Range(min=1, max=SEGMENT_COUNT))],
    vol.Optional("hue", default=0): hue(),
    vol.Optional("saturation", default=100): percent(),
    vol.Optional("brightness", default=100): percent(),
    vol.Optional("background_hue", default=0): hue(),
    vol.Optional("background_saturation", default=0): percent(),
    vol.Optional("background_brightness", default=0): percent(),
    vol.Optional("background_temperature", default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=1000)),
    vol.Optional("background_mode", default="rgb"): vol.In(["rgb", "white"]),
    vol.Optional("preserve_background", default=False): bool,
    vol.Optional("erase", default=False): bool,
    vol.Optional("clear_others", default=False): bool,
    vol.Optional("write_mode", default="individual"): vol.In(["individual", "full_pattern"]),
})

def encode(packet):
    return base64.b64encode(packet).decode("ascii")

def encode_segment_command(segment, color, erase=False):
    if erase:
        color = (0, 0, 0)
    return encode(bytes.fromhex("00020014") + bytes([2 if erase else 1])
                  + struct.pack(">HHH", *color) + bytes([0x81, segment]))

def encode_full_pattern(segments, foreground, background, erase=False):
    selected = set(segments)
    packet = bytearray.fromhex("0003001400")
    for segment in range(1, SEGMENT_COUNT + 1):
        color = ((0, 0, 0) if erase else foreground) if segment in selected else background
        packet.extend(struct.pack(">HHH", *color))
    return encode(packet)

def encode_white_background(brightness, temperature):
    return encode(bytes.fromhex("0000001400") + struct.pack(">HH", brightness, temperature))

async def async_setup(hass, config):
    locks = {}

    async def handle(call):
        data = call.data
        matches = []
        for bucket in hass.data.get("tuya_local", {}).values():
            if not isinstance(bucket, dict):
                continue
            device = bucket.get("device")
            if device is None:
                continue
            if any(getattr(entity, "entity_id", None) == data["entity_id"]
                   for entity in getattr(device, "_children", ())):
                if not any(found is device for found in matches):
                    matches.append(device)
        if len(matches) != 1:
            raise HomeAssistantError("Gebruik een entity_id van precies één geladen Tuya Local-apparaat.")
        device = matches[0]
        segments = list(dict.fromkeys(data["segments"]))
        if not segments:
            raise HomeAssistantError("segments mag niet leeg zijn; gebruik 1 t/m 20.")
        preserve = data["preserve_background"]
        white = data["background_mode"] == "white"
        if preserve and (data["clear_others"] or data["write_mode"] != "individual"):
            raise HomeAssistantError("preserve_background vereist clear_others: false en write_mode: individual.")
        configured = set()
        for entity in getattr(device, "_children", ()):
            entity_config = getattr(entity, "_config", None)
            if entity_config is not None:
                configured.update(str(dp.id) for dp in entity_config.dps())
        required = {"103"} if preserve else {"20", "21", "103"}
        if white and not preserve:
            required.update({"22", "23"})
        missing = required - configured
        if missing:
            raise HomeAssistantError("Ontbrekende DP's: " + ", ".join(sorted(missing, key=int)))
        erase = data["erase"] or data["brightness"] == 0
        foreground = (round(data["hue"]) % 360, round(data["saturation"] * 10), round(data["brightness"] * 10))
        background = (round(data["background_hue"]) % 360, round(data["background_saturation"] * 10), round(data["background_brightness"] * 10))
        if not preserve and not white and data["write_mode"] == "full_pattern" and not data["clear_others"]:
            raise HomeAssistantError("RGB full_pattern vereist clear_others: true.")
        lock = locks.setdefault(device.unique_id, asyncio.Lock())
        async with lock:
            if preserve:
                for segment in segments:
                    await device.async_set_properties({"103": encode_segment_command(segment, foreground, erase)})
                return
            if white:
                brightness = round(data["background_brightness"] * 10)
                temperature = data["background_temperature"]
                await device.async_set_properties({"20": True, "21": "white", "22": max(10, brightness), "23": temperature})
                await asyncio.sleep(COMMAND_DELAY)
                await device.async_set_properties({"103": encode_white_background(brightness, temperature)})
                await asyncio.sleep(COMMAND_DELAY)
                for segment in segments:
                    await device.async_set_properties({"103": encode_segment_command(segment, foreground, erase)})
                    await asyncio.sleep(COMMAND_DELAY)
                return
            await device.async_set_properties({"20": True, "21": "colour"})
            await asyncio.sleep(COMMAND_DELAY)
            if data["write_mode"] == "full_pattern":
                await device.async_set_properties({"103": encode_full_pattern(segments, foreground, background, erase)})
                return
            if data["clear_others"]:
                for segment in range(1, SEGMENT_COUNT + 1):
                    if segment not in segments:
                        await device.async_set_properties({"103": encode_segment_command(segment, (0, 0, 0), True)})
                        await asyncio.sleep(COMMAND_DELAY)
            for segment in segments:
                await device.async_set_properties({"103": encode_segment_command(segment, foreground, erase)})
                await asyncio.sleep(COMMAND_DELAY)

    hass.services.async_register(DOMAIN, "set_segments", handle, schema=SCHEMA)
    return True
