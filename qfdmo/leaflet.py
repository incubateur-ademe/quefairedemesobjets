import json
import logging
from json.decoder import JSONDecodeError
from typing import List, TypedDict

logger = logging.getLogger(__name__)


class PointDict(TypedDict):
    lat: float
    lng: float


class LeafletBbox(TypedDict):
    center: PointDict
    southWest: PointDict
    northEast: PointDict


def center_from_leaflet_bbox(custom_bbox_as_string: str) -> List[float]:
    try:
        custom_bbox: LeafletBbox = json.loads(custom_bbox_as_string)
        # Handle center
        return [custom_bbox["center"]["lng"], custom_bbox["center"]["lat"]]
    except (JSONDecodeError, KeyError):
        # TODO : gérer l'erreur
        return ["", ""]


def sanitize_leaflet_bbox(custom_bbox_as_string: str) -> List[float] | None:
    try:
        custom_bbox: LeafletBbox = json.loads(custom_bbox_as_string)
        # Handle center
        return [
            custom_bbox["southWest"]["lng"],
            custom_bbox["southWest"]["lat"],
            custom_bbox["northEast"]["lng"],
            custom_bbox["northEast"]["lat"],
        ]
    except (KeyError, JSONDecodeError):
        logger.error("An error occured while sanitizing a leaflet bbox. It was ignored")
        # TODO : gérer l'erreur
        return []


def compile_leaflet_bbox(bbox) -> str:
    xmin, ymin, xmax, ymax = bbox
    return json.dumps(
        {
            "southWest": {
                "lng": xmin,
                "lat": ymin,
            },
            "northEast": {"lng": xmax, "lat": ymax},
        }
    )
