"""Constants for file paths"""

from pathlib import Path

DIR_CURRENT = Path(__file__).resolve()
DIR_SQL_SCHEMAS = DIR_CURRENT.parent / "sql" / "schemas"
DIR_SQL_VALIDATIONS = DIR_CURRENT.parent / "sql" / "validations"
