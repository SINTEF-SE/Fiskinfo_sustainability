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

#------------------------------------------------------------------------
# Approx. Price difference between normal diesel and marine diesel (MGO)
#------------------------------------------------------------------------
PRICE_DIFF = 5  

#-------------------------
# Time formats
#-------------------------
TIME_FORMATS = [
    "%Y-%m-%dT%H:%M:%SZ",      # no fractional seconds
    "%Y-%m-%dT%H:%M:%S.%fZ",   # with fractional seconds
]