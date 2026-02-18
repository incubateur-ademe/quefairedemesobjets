import sys
from pathlib import Path

# Add Django path to sys.path
_django_root = Path(__file__).resolve().parent.parent
if _django_root not in sys.path:
    sys.path.insert(0, str(_django_root))

keepalive_kwargs = {
    "keepalives": 1,  # enable keepalive
    "keepalives_idle": 60,  # idle time before sending keepalive
    "keepalives_interval": 60,  # interval between keepalive packets
    "keepalives_count": 5,  # number of keepalive packets to send before closing
}
