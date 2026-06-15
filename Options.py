# -------------------------
# APP options
# -------------------------
APP_ICON = "SINTEF_FiskAgri_Main.png"
APP_TITLE = "FiskInfoPlattformen Bærekraftsmodul"

# -------------------------
# GUI options
# -------------------------
#-------------------------------
# Colors for buttons and fields
#-------------------------------
BG_BUTTON_COL = "#F1D014"
BG_FIELD_COL = "#91E7F7"
BG_OUTTEXT_COL = "#91E7F7"
#BG_MAINWINDOW_COL = "#D3F1FD"
BG_MAINWINDOW_COL = "#FFFFFFFF"
API_TEXT_COL = "#061EA8"

# -------------------------
# Group constants
# -------------------------
VESSEL_GROUPS = [
    "Alle", "< 11 m", "11-15 m",
    "15-21 m", "22-28 m", "> 28 m"
]

GEAR_GROUPS = [
    "Alle", "Not", "Garn", "Krokredskap", "Teine",
    "Trål", "Snurrevad", "Harpun", "Annet redskap", "Havbruk"
]

SPECIES_GROUPS = [
    "Unknown", "Capelin", "NorwegianSpringSpawningHerring", "OtherHerring",
    "Mackerel", "BlueWhiting", "NorwayPout", "Sandeels", "Argentines",
    "EuropeanSpratSea", "EuropeanSpratCoast", "MesopelagicFish",
    "TunaAndTunaishSpecies", "OtherPelagicFish", "AtlanticCod", "Haddock",
    "Saithe", "Gadiformes", "GreenlandHalibut", "GoldenRedfish", "Wrasse",
    "Wolffishes", "FlatFishOtherBottomFishAndDeepSeaFish", "SharkFish",
    "SkatesAndOtherChondrichthyes", "QueenCrab", "EdibleCrab", "RedKingCrab",
    "RedKingCrabOther", "NorthernPrawn", "AntarcticKrill",
    "CalanusFinmarchicus", "OtherShellfishMolluscaAndEchinoderm",
    "BrownSeaweed", "OtherSeaweed", "FreshWaterFish", "FishFarming",
    "MarineMammals", "Seabird", "Other"
]

# -------------------------
# Vessel IDs
# -------------------------
ID_MY_VESSEL        = 2013063493  # Gadus Njord
ID_REF_VESSELS      = [1999001513, 2011054408, 2018101213, 2000013339, 2013063493]        # Nordland Havfiske
#ID_REF_VESSELS      = []

#---------------------------------------
# Output files directory and file names
#---------------------------------------
OUTDIR      = 'output/'
CSV_FILE    = OUTDIR + "kpi_Report.csv" 
JDSON_FILE  = OUTDIR + "kpi_Report.json"
PDF_FILE    = OUTDIR + "kpi_Report.pdf"

#-------------------------
# Conversion factors
#-------------------------
CO2_FACTOR = 2.66              # kg CO2 / liter drivstoff
HOURS_IN_DAY = 24              # number of hours in a day
NM = 1852                      # nautisk mil in meters

#------------------------------------------------------------------------------
# Approx. Price difference in NOK between normal diesel and marine diesel (MGO)
#------------------------------------------------------------------------------
PRICE_DIFF = 5  

#-------------------------
# Time formats
#-------------------------
TIME_FORMATS = [
    "%Y-%m-%dT%H:%M:%SZ",      # no fractional seconds
    "%Y-%m-%dT%H:%M:%S.%fZ",   # with fractional seconds
]