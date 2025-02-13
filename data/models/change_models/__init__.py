from .acteur_change_nothing_in_base import ChangeActeurNothingBase
from .acteur_change_nothing_in_revision import ChangeActeurNothingRevision
from .acteur_create_as_parent import ChangeActeurCreateAsParent
from .acteur_delete_as_parent import ChangeActeurDeleteAsParent
from .acteur_keep_as_parent import ChangeActeurKeepAsParent
from .acteur_update_parent_id import ChangeActeurUpdateParentId
from .sample_model_do_nothing import SampleModelDoNothing

CHANGE_MODELS = {
    ChangeActeurCreateAsParent.name(): ChangeActeurCreateAsParent,
    ChangeActeurDeleteAsParent.name(): ChangeActeurDeleteAsParent,
    ChangeActeurUpdateParentId.name(): ChangeActeurUpdateParentId,
    ChangeActeurNothingRevision.name(): ChangeActeurNothingRevision,
    ChangeActeurNothingBase.name(): ChangeActeurNothingBase,
    ChangeActeurKeepAsParent.name(): ChangeActeurKeepAsParent,
    SampleModelDoNothing.name(): SampleModelDoNothing,
}
