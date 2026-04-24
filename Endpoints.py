from PySide6.QtCore import QDate

# -------------------------
# Datafangst Endpoint constants
# -------------------------
DATAFANGST_BASE_URL  = "https://api.dev.datafangst.orcalabs.no/"

E_GEAR               = "v1.0/gear"
E_GEAR_GROUPS        = "v1.0/gear_groups"
E_GEAR_MAIN_GROUPS   = "v1.0/gear_main_groups"

E_SPECIES            = "v1.0/species"
E_USER               = "v1.0/user"

E_VESSELS            = "v1.0/vessels"
E_VESSEL_FUEL        = "v1.0/vessel/fuel"
E_VESSEL_LIVE_FUEL   = "v1.0/vessel/live_fuel"
E_VESSEL_BENCHMARKS  = "v1.0/vessels/benchmarks"

E_TRIPS              = "v1.0/trips"
E_HAULS              = "v1.0/hauls"

E_TRIP_AVG           = "v1.0/trip/benchmarks/average"
E_AVG_EEOI           = "v1.0/trip/benchmarks/average_eeoi"
E_AVG_FUI            = "v1.0/trip/benchmarks/average_fui"
E_EEOI               = "v1.0/trip/benchmarks/eeoi"


SSB_PRICE_BASE      = (
                    "https://data.ssb.no/api/pxwebapi/v2/tables/09654/data"
                    "?lang=no&valueCodes[PetroleumProd]=035"
                    "&valueCodes[ContentsCode]=Priser&valueCodes[Tid]="
                    )

# -------------------------
# SSB price endpoint builder
# -------------------------
def build_ssb_url(endpoint: str, start: QDate, end: QDate) -> str:
    base = endpoint
    sY, sM = start.year(), start.month()
    eY, eM = end.year(), end.month()
    return base + f"[range({sY}M{sM:02d},{eY}M{eM:02d})]"

