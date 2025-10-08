"""Configuration model for the clone DAG"""

import re
from pathlib import Path
from typing import Literal

from pydantic import AnyUrl, BaseModel, computed_field

DIR_CURRENT = Path(__file__).resolve()
DIR_SQL_CREATION = DIR_CURRENT.parent / "sql" / "creation"
DIR_SQL_VALIDATION = DIR_CURRENT.parent / "sql" / "validation"

PREFIX_ALL = "clone"
SUFFIX_VIEW_IN_USE = "in_use"


class CloneConfig(BaseModel):
    dry_run: bool
    table_kind: str
    data_endpoint: AnyUrl
    clone_method: Literal["download_to_disk_first", "stream_directly"] = (
        "stream_directly"
    )
    file_downloaded: str | None = None
    file_unpacked: str | None = None
    delimiter: str = ","
    run_timestamp: str
    convert_downloaded_file_to_utf8: bool = False

    @computed_field
    @property
    def table_schema_file_path(self) -> Path:
        return DIR_SQL_CREATION / "tables" / f"create_table_{self.table_kind}.sql"

    @computed_field
    @property
    def table_name(self) -> str:
        return f"{PREFIX_ALL}_{self.table_kind}_{self.run_timestamp}"

    @computed_field
    @property
    def table_name_pattern(self) -> re.Pattern:
        """Pattern to help us remove old tables"""
        return re.compile(f"^{PREFIX_ALL}_{self.table_kind}_\\d{{14}}$")

    @computed_field
    @property
    def view_schema_file_path(self) -> Path:
        """Pattern to help us remove old views"""
        return (
            DIR_SQL_CREATION
            / "views"
            / f"create_view_{self.table_kind}_{SUFFIX_VIEW_IN_USE}.sql"
        )

    @computed_field
    @property
    def view_name(self) -> str:
        return f"{PREFIX_ALL}_{self.table_kind}_{SUFFIX_VIEW_IN_USE}"

    def validate_paths(self) -> None:
        # Making this optional so it doesn't become a bottleneck in the tests
        if not self.table_schema_file_path.exists():
            raise FileNotFoundError(f"{self.table_schema_file_path=} pas trouvé")
        if not self.view_schema_file_path.exists():
            raise FileNotFoundError(f"{self.view_schema_file_path=} pas trouvé")
