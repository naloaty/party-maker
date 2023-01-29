from dataclasses import dataclass
from enum import Enum
from typing import Optional

from PyP100 import PyL530


@dataclass
class Light:
    class Type(Enum):
        COLOR = 0,
        TEMP = 1

    type: Type
    brightness: int
    hue: Optional[int] = None
    saturation: Optional[int] = None
    temperature: Optional[int] = None


class Lighting:
    _bulb: PyL530

    def __init__(self, ip: str, login: str, password: str):
        self._bulb = PyL530.L530(ip, login, password)
        self._bulb.handshake()
        self._bulb.login()

    def set(self, light: Light):
        if light.type is Light.Type.TEMP:
            self._bulb.setColorTemp(light.temperature)
        elif light.type is Light.Type.COLOR:
            self._bulb.setColor(light.hue, light.saturation)
        self._bulb.setBrightness(light.brightness)

    def state(self):
        info = self._bulb.getDeviceInfo()["result"]

        if "hue" in info:
            return Light(
                type=Light.Type.COLOR,
                hue=info["hue"],
                saturation=info["saturation"],
                brightness=info["brightness"]
            )
        else:
            return Light(
                type=Light.Type.TEMP,
                temperature=info["color_temp"],
                brightness=info["brightness"]
            )