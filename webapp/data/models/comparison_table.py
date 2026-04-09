from abc import ABC
from typing import ClassVar

from pydantic import BaseModel, ConfigDict


class LinkInCell(BaseModel):
    """A hyperlink rendered inside a column header or a cell."""

    model_config = ConfigDict(frozen=True)

    label: str
    url: str


class FieldInCell(BaseModel):
    """
    One field rendered inside a cell,
    cells may contain multiple fields for grouped fields.
    """

    model_config = ConfigDict(frozen=True)

    links: list[LinkInCell] = []
    field_name: str
    display_html: str = ""
    editable: bool = False
    # Stimulus values for cell-edit controller
    suggestion_modele: str | None = None
    update_url: str | None = None
    replace_text: str | None = None
    fields_groups: str | None = None
    identifiant_unique: str | None = None
    error: str | None = None


class BaseCellContent(BaseModel, ABC):
    model_config = ConfigDict(frozen=True)

    links: list[LinkInCell] = []
    column_key: str
    template_name: ClassVar[str]


class CellHtmlContent(BaseCellContent):
    """A single table cell (<td>) with html content."""

    template_name: ClassVar[str] = "data/_partials/cells/html.html"
    html_content: str = ""


class BaseCellWithFields(BaseCellContent, ABC):
    """Base for cells that contain a list of FieldInCell."""

    fields: list[FieldInCell] = []


class CellDisplayContent(BaseCellWithFields):
    """A read-only cell displaying field values."""

    template_name: ClassVar[str] = "data/_partials/cells/display.html"


class CellEditableContent(BaseCellWithFields):
    """An editable cell where each field can be modified in-place."""

    template_name: ClassVar[str] = "data/_partials/cells/editable.html"


class CellActionContent(BaseCellContent):
    """A cell with a clickable action icon (report-update controller)."""

    template_name: ClassVar[str] = "data/_partials/cells/action.html"
    enabled: bool = True
    disabled_icon: str = "🚫"
    action_icon: str = ""
    # Stimulus values for report-update controller
    stimulus_fields: str | None = None
    stimulus_suggestion_modele: str | None = None
    stimulus_update_url: str | None = None
    stimulus_target_values: str | None = None
    stimulus_fields_groups: str | None = None


class ColumnHeader(BaseModel):
    """Describes one column header of the comparison table."""

    model_config = ConfigDict(frozen=True)

    key: str
    label: str = ""
    links: list[LinkInCell] = []
    subtitle: str | None = None
    header_action: dict | None = None


class TableRow(BaseModel):
    """One row representing a field group."""

    model_config = ConfigDict(frozen=True)

    cells: list[
        CellHtmlContent | CellDisplayContent | CellEditableContent | CellActionContent
    ]


class ComparisonTable(BaseModel):
    """A fully described, domain-agnostic comparison table."""

    model_config = ConfigDict(frozen=True)

    columns: list[ColumnHeader]
    rows: list[TableRow]
