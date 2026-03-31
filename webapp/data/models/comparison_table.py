from abc import ABC
from typing import Literal

from pydantic import BaseModel, ConfigDict


class StimulusControllerConfig(BaseModel):
    """Configuration for a Stimulus controller attached to an HTML element."""

    model_config = ConfigDict(frozen=True)

    controller: str
    values: dict[str, str] = {}
    actions: list[str] = []


class CellLink(BaseModel):
    """A hyperlink rendered inside a column header."""

    model_config = ConfigDict(frozen=True)

    label: str
    url: str


class Cell(BaseModel):
    """A single table cell (<td>)."""

    model_config = ConfigDict(frozen=True)

    links: list[CellLink] = []


class CellField(Cell):
    """
    One field within a cell (cells may contain multiple fields for grouped fields).
    """

    model_config = ConfigDict(frozen=True)

    field_name: str
    display_html: str = ""
    editable: bool = False
    stimulus: StimulusControllerConfig | None = None
    error: str | None = None


class BaseCellContent(Cell, ABC):
    model_config = ConfigDict(frozen=True)

    column_key: str
    cell_type: str


class CellHtmlContent(BaseCellContent):
    """A single table cell (<td>) with html content."""

    html_content: str = ""
    cell_type: Literal["html"] = "html"


class CellFieldsContent(BaseCellContent):
    """A single table cell (<td>) with CellField (one by item of group_fields)."""

    model_config = ConfigDict(frozen=True)

    cell_type: Literal["display", "action", "editable"]
    fields: list[CellField] = []
    enabled: bool = True
    disabled_icon: str = "🚫"
    action_icon: str = ""
    stimulus: StimulusControllerConfig | None = None


class ColumnHeader(BaseModel):
    """Describes one column of the comparison table."""

    model_config = ConfigDict(frozen=True)

    key: str
    label: str = ""
    css_classes: str = ""
    links: list[CellLink] = []
    subtitle: str | None = None
    header_action: StimulusControllerConfig | None = None


class TableRow(BaseModel):
    """One row representing a field group."""

    model_config = ConfigDict(frozen=True)

    label: str
    cells: list[CellFieldsContent | CellHtmlContent]


class ComparisonTable(BaseModel):
    """A fully described, domain-agnostic comparison table."""

    model_config = ConfigDict(frozen=True)

    columns: list[ColumnHeader]
    rows: list[TableRow]
