import pprint
from logging import Filter


def log_pretty(dictionnary, sort_dicts=False):
    pretty_printer = pprint.PrettyPrinter(indent=2, sort_dicts=sort_dicts)
    """Beautifully log dict with line breaks and indentation in the console

    This can be used in a logger.info(log_pretty(some_dict))

    """
    return f"{pretty_printer.pformat(dictionnary)}\n"


class SkipStaticFilter(Filter):
    """Logging filter to skip logging of staticfiles"""

    def filter(self, record):
        return "GET /static/" not in record.getMessage()
