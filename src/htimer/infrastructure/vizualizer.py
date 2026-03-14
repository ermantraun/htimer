from htimer.application.reports import interfaces
from htimer.application.reports.interfaces import ContentType


class ReportVizualizer(interfaces.ReportVizualizer):
    def vizualize(self, content: ContentType) -> bytes:
        return b""
