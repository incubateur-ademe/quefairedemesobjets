from logging import Filter


class SkipStaticFilter(Filter):
    """Logging filter to skip logging of staticfiles"""

    def filter(self, record):
        return "GET /static/" not in record.getMessage()
