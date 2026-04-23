from PySide6.QtCore import QDate

# -------------------------
# SSB price endpoint builder
# -------------------------
def build_ssb_url(start: QDate, end: QDate) -> str:
    base = (
        "https://data.ssb.no/api/pxwebapi/v2/tables/09654/data"
        "?lang=no&valueCodes[PetroleumProd]=035"
        "&valueCodes[ContentsCode]=Priser&valueCodes[Tid]="
    )
    sY, sM = start.year(), start.month()
    eY, eM = end.year(), end.month()
    return base + f"[range({sY}M{sM:02d},{eY}M{eM:02d})]"
