from datetime import datetime, timezone

from clone.config.model import CloneConfig


def clone_config_create(params: dict) -> CloneConfig:
    """All core config logic should be validated with Pydantic
    + unit tests. What's left here is validation we don't want to
    impose on tests (e.g. file existence)"""
    now = datetime.now(tz=timezone.utc)
    extra = {"run_timestamp": now.strftime("%Y%m%d%H%M%S")}
    config = CloneConfig(**(params | extra))
    config.validate_paths()
    return config
