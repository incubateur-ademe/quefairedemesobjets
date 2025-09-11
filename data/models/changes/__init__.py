from .acteur_change_nothing_in_base import ChangeActeurNothingBase
from .acteur_create_as_parent import ChangeActeurCreateAsParent
from .acteur_delete_as_parent import ChangeActeurDeleteAsParent
from .acteur_keep_as_parent import ChangeActeurKeepAsParent
from .acteur_rgpd_anonymize import ChangeActeurRgpdAnonymize
from .acteur_update import ChangeActeurUpdate
from .acteur_update_parent_id import ChangeActeurUpdateParentId
from .acteur_update_revision import ChangeActeurUpdateRevision
from .acteur_verify_in_revision import ChangeActeurVerifyRevision
from .sample_model_do_nothing import SampleModelDoNothing

CHANGE_MODELS = {
    ChangeActeurCreateAsParent.name(): ChangeActeurCreateAsParent,
    ChangeActeurDeleteAsParent.name(): ChangeActeurDeleteAsParent,
    ChangeActeurKeepAsParent.name(): ChangeActeurKeepAsParent,
    ChangeActeurNothingBase.name(): ChangeActeurNothingBase,
    ChangeActeurRgpdAnonymize.name(): ChangeActeurRgpdAnonymize,
    ChangeActeurUpdateParentId.name(): ChangeActeurUpdateParentId,
    ChangeActeurUpdateRevision.name(): ChangeActeurUpdateRevision,
    ChangeActeurUpdate.name(): ChangeActeurUpdate,
    ChangeActeurVerifyRevision.name(): ChangeActeurVerifyRevision,
    SampleModelDoNothing.name(): SampleModelDoNothing,
}
