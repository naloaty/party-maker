from dataclasses import dataclass

from system.services.projector import VlcProjector
from system.services.lighting import Lighting
from .resource import Resource


@dataclass
class Stage(Resource):
    display: VlcProjector
    lighting: Lighting
