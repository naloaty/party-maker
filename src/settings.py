from system.lighting import Light

# TP-Link Tapo L530E
bulb_settings = {
    "ip": "",
    "login": "",
    "password": "",
}

default_light = Light(
    type=Light.Type.TEMP, temperature=3620, brightness=100)
