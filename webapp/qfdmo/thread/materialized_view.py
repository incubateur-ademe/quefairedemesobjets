import threading

from django.core.management import call_command


class RefreshMateriazedViewThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        call_command("refresh_materialized_view")
