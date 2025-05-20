# Shorthands to make writing tests shorter and more explicit

from data.models.changes import (
    ChangeActeurCreateAsParent,
    ChangeActeurDeleteAsParent,
    ChangeActeurKeepAsParent,
    ChangeActeurUpdateParentId,
    ChangeActeurVerifyRevision,
)

CHANGE_KEEP = ChangeActeurKeepAsParent.name()
CHANGE_CREATE = ChangeActeurCreateAsParent.name()
CHANGE_DELETE = ChangeActeurDeleteAsParent.name()
CHANGE_POINT = ChangeActeurUpdateParentId.name()
CHANGE_NOTHING = ChangeActeurVerifyRevision.name()
