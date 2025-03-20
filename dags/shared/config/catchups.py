"""To make explicit that for now none of our DAGS work
on versionned data and there is no reason to use catchups."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CATCHUPS:
    AWLAYS_FALSE: bool = False
