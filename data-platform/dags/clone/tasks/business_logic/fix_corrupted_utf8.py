"""Safe UTF-8 fix on a CSV file before PostgreSQL import."""

import logging
import re
import shlex
from pathlib import Path

from utils.cmd import cmd_run

logger = logging.getLogger(__name__)

# Literal s/pattern/replacement/ expression (optional trailing g).
SED_SUBSTITUTION_RE = re.compile(
    r"^s/"
    r"(?P<pattern>(?:[^/\\]|\\.|\\x[0-9a-fA-F]{2})+)"
    r"/"
    r"(?P<replacement>(?:[^/\\]|\\.|\\x[0-9a-fA-F]{2})+)"
    r"/"
    r"(?P<flags>g)?$"
)

FORBIDDEN_CHARACTERS = set("\n\r;|`&<>()${}'")


class UnsafeSedSubstitutionError(ValueError):
    """Raised when a sed substitution expression is rejected."""


def validate_sed_substitutions(sed_substitutions: list[str]) -> None:
    """Validate one or more sed-like s/pattern/replacement/ expressions."""
    for sed_substitution in sed_substitutions:
        if any(char in sed_substitution for char in FORBIDDEN_CHARACTERS):
            raise UnsafeSedSubstitutionError(
                "L'expression contient des caractères interdits"
            )

        match = SED_SUBSTITUTION_RE.fullmatch(sed_substitution)
        if match is None:
            raise UnsafeSedSubstitutionError(
                "Format attendu : s/motif/remplacement/ "
                "(remplacement littéral, pas regex)"
            )


def fix_corrupted_utf8_file(
    file_path: Path,
    sed_substitutions: list[str],
) -> None:
    """Apply validated sed substitutions on a file via the sed shell command."""
    substitutions = [item.strip() for item in sed_substitutions if item.strip()]
    if not substitutions:
        return

    validate_sed_substitutions(substitutions)

    for sed_substitution in substitutions:

        cmd_run(
            f"sed -i {shlex.quote(sed_substitution)} {shlex.quote(str(file_path))}",
            dry_run=False,
        )

    logger.info(
        "Correction UTF-8 appliquée sur %s",
        file_path,
    )
