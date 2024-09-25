from typing import TypedDict, List
import json


class PointDict(TypedDict):
    lat: float
    lng: float


class LeafletBbox(TypedDict):
    center: List[str]
    southWest: PointDict
    northEast: PointDict


def sanitize_leaflet_bbox(custom_bbox_as_string: str) -> List[float] | None:
    custom_bbox: LeafletBbox = json.loads(custom_bbox_as_string)

    try:
        # Handle center
        return [
            custom_bbox["southWest"]["lng"],
            custom_bbox["southWest"]["lat"],
            custom_bbox["northEast"]["lng"],
            custom_bbox["northEast"]["lat"],
        ]
    except KeyError as exception:
        # TODO : gérer l'erreur
        print(f"Uh oh {exception=}")
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
