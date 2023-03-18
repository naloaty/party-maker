from dataclasses import dataclass

from system.services.projector import Projector
from system.services.lighting import Lighting
from .resource import Resource


@dataclass
class Stage(Resource):
    display: Projector
    lighting: Lighting
