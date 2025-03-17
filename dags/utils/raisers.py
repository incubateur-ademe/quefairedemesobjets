"""Utilities to raise exceptions:
- raise on one line w/ a proper exception, not using assert
   (see https://google.github.io/styleguide/pyguide.html#244-decision)
- reduce code duplication & improve improve consistency
- integrate extra logging if we want to
"""


def raise_if(cond: bool, msg: str):
    """Raise an exception if a condition is met."""
    if cond:
        raise ValueError(msg)
