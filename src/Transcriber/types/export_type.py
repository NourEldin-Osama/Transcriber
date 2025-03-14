from enum import Enum


class ExportType(Enum):
    ALL = "all"
    TXT = "txt"
    SRT = "srt"
    VTT = "vtt"
    DOCX = "docx"
    # PDF = "pdf"

    def __str__(self):
        return self.value
