
from PySide6.QtWidgets import (
    QMainWindow, QToolBar, QLabel, QCheckBox, QGridLayout, QWidget,
    QDateEdit, QLineEdit, QComboBox, QTextEdit, QMessageBox, QSizePolicy, QHBoxLayout
)
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import QSize, QDate

#from gui_helpers import MultiComboBox, splitCatchLocation, getDatesArray
from gui_helpers import *
from reports import *
#import reports as r
from KPI import kpi_01, kpi_02, kpi_03_04, kpiCalculations, getAllTripsInPeriod, getAllTripsInPeriods

from datafangst_client import DatafangstClient
from utility import *
from plot import *
from dataclasses import dataclass
from datetime import datetime


# -------------------------
# Vessel IDs
# -------------------------
ID_MY_VESSEL        = 2013063493  # Gadus Njord
ID_REF_VESSELS      = [1999001513, 2011054408, 2018101213, 2000013339, 2013063493]        # Nordland Havfiske
#ID_REF_VESSELS      = []

#-------------------------
# Output files directory
#-------------------------
OUTDIR = 'output/'

# -------------------------
# Endpoint constants
# -------------------------
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

# -------------------------
# Group constants
# -------------------------
'''VESSEL_GROUPS = [
    "Unknown", "UnderEleven", "ElevenToFifteen",
    "FifteenToTwentyOne", "TwentyTwoToTwentyEight", "TwentyEightAndAbove"
]'''

VESSEL_GROUPS = [
    "Ukjent", "< 11 m", "11 - 15 m",
    "15 -21 m", "22 -28 m", "> 28 m"
]



GEAR_GROUPS = [
    "Unknown", "Seine", "Net", "HookGear", "LobsterTrapAndFykeNets",
    "Trawl", "DanishSeine", "HarpoonCannon", "OtherGear", "FishFarming"
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

def safe_int(text: str, default: int = 0) -> int:
    try:
        return int(text)
    except Exception:
        return default
    
def _norsk_length_group(lengthG) -> str:
    """Format Norwegian vessel length group label."""
    return f"[{', '.join(nlg(lg) for lg in lengthG) if lengthG else 'Alle'}]"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # -------------------------
        # Basic state
        # -------------------------
        self.vesselId = ID_MY_VESSEL
        self.vesselRefIds = ID_REF_VESSELS
        self.inputHasChanged = True
        self.nVessels = 0
        self.actionText = ""
        self.getParams = ""
        self.myTrips = None
        self.refTrips = None

        self.periodArray = []
        self.tripsArray = []

        
        # Shared client (fast & clean)
        self.client = DatafangstClient()

        # -------------------------
        # Window setup
        # -------------------------
        self.setWindowTitle("FiskInfoPlattformen Bærekraftsmodul")
        #self.setFixedSize(QSize(700, 400))
        self.resize(QSize(700, 400))

        # Layout
        layout = QGridLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        
        left = QGridLayout()
        right = QGridLayout()

        # -------------------------
        # Controls
        # -------------------------
        # Limit
        left.addWidget(QLabel("Max antall:"), 4, 0)
        self.limitEdit = QLineEdit()
        self.limitEdit.setFixedWidth(80)
        self.limitEdit.setStyleSheet("QLineEdit { background-color: lightblue; color: black; }")
        self.limitEdit.setText("100")
        self.limitEdit.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        left.addWidget(self.limitEdit, 4, 1)

        # Offset
        right.addWidget(QLabel("Offset:"), 4, 0)
        self.offsetEdit = QLineEdit()
        self.offsetEdit.setStyleSheet("QLineEdit { background-color: lightblue; color: black; }")
        right.addWidget(self.offsetEdit, 4, 1)

        # Start date
        left.addWidget(QLabel("Start dato:"), 0, 0)
        self.startDateEdit = QDateEdit(QDate(2024, 1, 1))
        self.startDateEdit.setFixedWidth(80)
        self.startDateEdit.setStyleSheet("QDateEdit { background-color: lightblue; color: black; }")
        self.startDateEdit.dateChanged.connect(self.inputChanged)
        left.addWidget(self.startDateEdit, 0, 1)

        # Stop date
        right.addWidget(QLabel("Stopp dato:"), 0, 0)
        self.stopDateEdit = QDateEdit(QDate(2024, 12, 31))
        self.stopDateEdit.setStyleSheet("QDateEdit { background-color: lightblue; color: black; }")
        self.stopDateEdit.dateChanged.connect(self.inputChanged)
        right.addWidget(self.stopDateEdit, 0, 1)

        # Vessel group
        left.addWidget(QLabel("Lengdegruppe:"), 1, 0)
        self.vesselCombo = MultiComboBox()
        self.vesselCombo.setMinimumWidth(80)
        self.vesselCombo.setMinimumHeight(30)
        self.vesselCombo.resize(80, self.vesselCombo.sizeHint().height())  # default
        self.vesselCombo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.vesselCombo.setStyleSheet("QComboBox { background-color: lightblue; color: black; }")
       # self.vesselCombo.add_item("All", checked=False)
        # Default selection same as your earlier code (last group checked)
        self.vesselCombo.add_items(VESSEL_GROUPS, [False, False, False, False, False, True])
        self.vesselCombo.currentTextChanged.connect(self.inputChanged)
        left.addWidget(self.vesselCombo, 1, 1)
        #layout.setColumnStretch(1, 1)   # column

        # Gear group
        left.addWidget(QLabel("Redskapsgruppe:"), 2, 0)
        self.gearCombo = MultiComboBox()
        self.gearCombo.setMinimumWidth(80)
        self.gearCombo.setMinimumHeight(30)
        self.gearCombo.resize(80, self.gearCombo.sizeHint().height())  # default
        self.gearCombo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.gearCombo.setStyleSheet("QComboBox { background-color: lightblue; color: black; }")
       # self.gearCombo.add_item("All", checked=False)
        self.gearCombo.add_items(GEAR_GROUPS, [False, False, False, False, False, True, False, False, False, False])
        self.gearCombo.currentTextChanged.connect(self.inputChanged)
        left.addWidget(self.gearCombo, 2, 1)

        # Species group
        left.addWidget(QLabel("Artsgruppe:"), 3, 0)
        self.speciesCombo = MultiComboBox()
        self.speciesCombo.setMinimumWidth(80)
        self.speciesCombo.setMinimumHeight(30)
        self.speciesCombo.resize(80, self.speciesCombo.sizeHint().height())  # default
        self.speciesCombo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.speciesCombo.setStyleSheet("QComboBox { background-color: lightblue; color: black; }")
      #  self.speciesCombo.add_item("All", checked=True)
        self.speciesCombo.add_items(SPECIES_GROUPS)
        self.speciesCombo.currentTextChanged.connect(self.inputChanged)
        left.addWidget(self.speciesCombo, 3, 1)

        # Catch locations
        right.addWidget(QLabel("Fangstfelt:"), 3, 0)
        self.locationText = QTextEdit()
        self.locationText.setStyleSheet("QTextEdit { background-color: lightblue; color: black; }")
        self.locationText.textChanged.connect(self.inputChanged)
        right.addWidget(self.locationText, 3, 1)

        # My vessel
        self.myVessel = QCheckBox("Mitt fartøy", self)
        left.addWidget(self.myVessel, 5, 0)

        # Print API response to screen
        self.infoOutput = QCheckBox("Vis API respons på skjerm", self)
        left.addWidget(self.infoOutput, 5, 1)

        # Save CSV
        self.storeCsv = QCheckBox("Lagre API-data som CSV", self)
        right.addWidget(self.storeCsv, 5, 0)

        # Append CSV
        self.appendCsv = QCheckBox("Legge til data i filen", self)
        right.addWidget(self.appendCsv, 5, 1)

        # Aggregation months (KPI)
        right.addWidget(QLabel("Aggregert tidsperiode [mnd]:"), 1, 0)
        self.aggEdit = QLineEdit()
        self.aggEdit.setStyleSheet("QLineEdit { background-color: lightblue; color: black; }")
        self.aggEdit.setText("3")
        self.aggEdit.textChanged.connect(self.inputChanged)
        right.addWidget(self.aggEdit, 1, 1)

        # Number of periods (KPI)
        right.addWidget(QLabel("Antall perioder bakover \ni tid fra sluttdato:"), 2, 0)
        self.resEdit = QLineEdit()
        self.resEdit.setStyleSheet("QLineEdit { background-color: lightblue; color: black; }")
        self.resEdit.setText("4")
        self.resEdit.textChanged.connect(self.inputChanged)
        right.addWidget(self.resEdit, 2, 1)

        
        # combine them
        top = QHBoxLayout()
        top.addLayout(left, 1)   # <– left column stretches normally
        top.addLayout(right, 3)  # <– right has more weight
        
        widget = QWidget()
        widget.setLayout(top)
        self.setCentralWidget(widget)


        # -------------------------
        # Toolbar & Menus
        # -------------------------
        toolbar = QToolBar("My main toolbar")
        toolbar.setStyleSheet("QToolBar { background-color: black; color: black; }")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)

        menu = self.menuBar()
        api_menu = menu.addMenu("Datafangst API")
        auth_menu = menu.addMenu("Innlogging")
        sust_menu = menu.addMenu("Rapporter")
        pef_menu = menu.addMenu("Pef")
        kpi_menu = menu.addMenu("KPI")

        # API submenus
        gear_menu = api_menu.addMenu("Gear")
        vessels_menu = api_menu.addMenu("Vessels")
        user_menu = api_menu.addMenu("User")
        trip_menu = api_menu.addMenu("Trip")
        haul_menu = api_menu.addMenu("Haul")
        price_menu = api_menu.addMenu("Price")

        # --- Gear actions ---
        getGear_action = QAction(QIcon("AppIcons/bug.png"), "&Get Gear", self)
        getGear_action.triggered.connect(self.getGear_button_clicked)
        gear_menu.addAction(getGear_action)

        getGearGroups_action = QAction(QIcon("AppIcons/bug.png"), "&Get Gear Groups", self)
        getGearGroups_action.triggered.connect(self.getGearGroups_button_clicked)
        gear_menu.addAction(getGearGroups_action)

        getGearMainGroups_action = QAction(QIcon("AppIcons/bug.png"), "&Get Gear Main Groups", self)
        getGearMainGroups_action.triggered.connect(self.getGearMainGroups_button_clicked)
        gear_menu.addAction(getGearMainGroups_action)

        api_menu.addSeparator()

        # --- Vessel actions ---
        getVessels_action = QAction(QIcon("AppIcons/bug.png"), "&Get Vessels", self)
        getVessels_action.triggered.connect(self.getVessels_button_clicked)
        vessels_menu.addAction(getVessels_action)

        getVesselsBenchmarks_action = QAction(QIcon("AppIcons/bug.png"), "&Get Vessel Benchmarks", self)
        getVesselsBenchmarks_action.triggered.connect(self.getVesselsBenchmarks_button_clicked)
        vessels_menu.addAction(getVesselsBenchmarks_action)

        getVesselsFuel_action = QAction(QIcon("AppIcons/bug.png"), "&Get Vessel Fuel", self)
        getVesselsFuel_action.triggered.connect(self.getVesselsFuel_button_clicked)
        vessels_menu.addAction(getVesselsFuel_action)

        getVesselsLiveFuel_action = QAction(QIcon("AppIcons/bug.png"), "&Get Vessel Live Fuel", self)
        getVesselsLiveFuel_action.triggered.connect(self.getVesselsLiveFuel_button_clicked)
        vessels_menu.addAction(getVesselsLiveFuel_action)

        api_menu.addSeparator()

        # --- User ---
        getUser_action = QAction(QIcon("AppIcons/user.png"), "&Get User", self)
        getUser_action.triggered.connect(self.getUser_button_clicked)
        user_menu.addAction(getUser_action)

        # --- Trip ---
        getTrips_action = QAction(QIcon("AppIcons/user.png"), "&Get Trips", self)
        getTrips_action.triggered.connect(self.getTrips_button_clicked)
        trip_menu.addAction(getTrips_action)

        getAvTripBenchmarks_action = QAction(QIcon("AppIcons/user.png"), "&Get Average Trip Benchmarks", self)
        getAvTripBenchmarks_action.triggered.connect(self.getAvTripBenchmarks_button_clicked)
        trip_menu.addAction(getAvTripBenchmarks_action)

        getEEOI_action = QAction(QIcon("AppIcons/user.png"), "&Get EEOI", self)
        getEEOI_action.triggered.connect(self.getEEOI_button_clicked)
        trip_menu.addAction(getEEOI_action)

        getAvEEOI_action = QAction(QIcon("AppIcons/user.png"), "&Get Average EEOI", self)
        getAvEEOI_action.triggered.connect(self.getAvEEOI_button_clicked)
        trip_menu.addAction(getAvEEOI_action)

        # --- Haul ---
        getHaul_action = QAction(QIcon("AppIcons/user.png"), "&Get Hauls", self)
        getHaul_action.triggered.connect(self.getHaul_button_clicked)
        haul_menu.addAction(getHaul_action)

        # --- Price (SSB) ---
        getPrice_action = QAction(QIcon("AppIcons/user.png"), "&Get Price", self)
        getPrice_action.triggered.connect(self.getPrice_button_clicked)
        price_menu.addAction(getPrice_action)

        # --- KPI ---
        kpi_01_action = QAction(QIcon("AppIcons/cross-circle-frame.png"), "&KPI_01 EEOI", self)
        kpi_01_action.triggered.connect(self.kpi01_button_clicked)
        kpi_menu.addAction(kpi_01_action)

        kpi_02_action = QAction(QIcon("AppIcons/cross-circle-frame.png"), "&KPI_02 FUI", self)
        kpi_02_action.triggered.connect(self.kpi02_button_clicked)
        kpi_menu.addAction(kpi_02_action)

        kpi_03_04_action = QAction(QIcon("AppIcons/cross-circle-frame.png"), "&KPI_03/04 Netto fortjeneste", self)
        kpi_03_04_action.triggered.connect(self.kpi03_04_button_clicked)
        kpi_menu.addAction(kpi_03_04_action)

        kpi_action = QAction(QIcon("AppIcons/cross-circle-frame.png"), "&KPI", self)
        kpi_action.triggered.connect(self.kpi_button_clicked)
        kpi_menu.addAction(kpi_action)

        # --- Auth menu (status)
        auth_action = QAction(QIcon("AppIcons/door-open.png"), "&Authorize", self)
        auth_action.triggered.connect(self.auth_button_clicked)
        auth_menu.addAction(auth_action)

        # --- Sustainability (placeholders)
        reder_action = QAction(QIcon("AppIcons/building.png"), "&Reder", self)
        reder_action.triggered.connect(self.reder_button_clicked)
        sust_menu.addAction(reder_action)

        skipper_action = QAction(QIcon("AppIcons/user-business-boss.png"), "&Skipper", self)
        skipper_action.triggered.connect(self.skipper_button_clicked)
        sust_menu.addAction(skipper_action)

        bank_action = QAction(QIcon("AppIcons/bank.png"), "&Bank", self)
        bank_action.triggered.connect(self.bank_button_clicked)
        sust_menu.addAction(bank_action)

        supplier_action = QAction(QIcon("AppIcons/shopping-basket.png"), "&Supplier", self)
        supplier_action.triggered.connect(self.supplier_button_clicked)
        sust_menu.addAction(supplier_action)

        pef_action = QAction(QIcon("AppIcons/star--arrow.png"), "&PEF calc", self)
        pef_action.triggered.connect(self.pef_button_clicked)
        pef_menu.addAction(pef_action)


    class kpi_data():
        def __init__(self, endDate: QDate, vesselId: int, vesselRefIds: list[int],
                 lengthgroup: list[str], gear: list[str], specie: list[str],
                 location: list[str], span: int, periods: int):

            self.endDate = endDate
            self.vesselId = vesselId
            self.vesselRefIds = vesselRefIds
            self.lengthG = lengthgroup
            self.gearG = gear
            self.specG = specie
            self.locG = location
            self.span = span
            self.noPeriods = periods


    # -------------------------
    # Change tracking
    # -------------------------
    def inputChanged(self):
        self.inputHasChanged = True

    def setInputChanged(self, state: bool):
        self.inputHasChanged = state

    def isInputChanged(self) -> bool:
        return self.inputHasChanged

    # -------------------------
    # API Button Handlers
    # -------------------------
    def getGear_button_clicked(self):
        toCsvFile = "output/gear.csv" if self.storeCsv.isChecked() else ""
        self.client.get(
            E_GEAR,
            auth=False,  # public
            print_out=self.infoOutput.isChecked(),
            csv_file=toCsvFile,
            append_csv=self.appendCsv.isChecked()
        )

    def getGearGroups_button_clicked(self):
        toCsvFile = "output/gearGroups.csv" if self.storeCsv.isChecked() else ""
        self.client.get(
            E_GEAR_GROUPS,
            auth=False,
            print_out=self.infoOutput.isChecked(),
            csv_file=toCsvFile,
            append_csv=self.appendCsv.isChecked()
        )

    def getGearMainGroups_button_clicked(self):
        toCsvFile = "output/gearMainGroups.csv" if self.storeCsv.isChecked() else ""
        self.client.get(
            E_GEAR_MAIN_GROUPS,
            auth=False,
            print_out=self.infoOutput.isChecked(),
            csv_file=toCsvFile,
            append_csv=self.appendCsv.isChecked()
        )

    def getVessels_button_clicked(self):
        toCsvFile = "output/vessels.csv" if self.storeCsv.isChecked() else ""
        self.client.get(
            E_VESSELS,
            auth=True,
            print_out=self.infoOutput.isChecked(),
            csv_file=toCsvFile,
            append_csv=self.appendCsv.isChecked()
        )

    def getVesselsFuel_button_clicked(self):
        toCsvFile = "output/vesselsFuel.csv" if self.storeCsv.isChecked() else ""
        self.client.get(
            E_VESSEL_FUEL,
            sDate=self.startDateEdit.date(),
            eDate=self.stopDateEdit.date(),
            auth=True,
            print_out=self.infoOutput.isChecked(),
            csv_file=toCsvFile,
            append_csv=self.appendCsv.isChecked()
        )

    def getVesselsLiveFuel_button_clicked(self):
        toCsvFile = "output/vesselsLiveFuel.csv" if self.storeCsv.isChecked() else ""
        self.client.get(
            E_VESSEL_LIVE_FUEL,
            auth=True,
            print_out=self.infoOutput.isChecked(),
            csv_file=toCsvFile,
            append_csv=self.appendCsv.isChecked()
        )

    def getVesselsBenchmarks_button_clicked(self):
        toCsvFile = "output/benchmarks.csv" if self.storeCsv.isChecked() else ""
        self.client.get(
            E_VESSEL_BENCHMARKS,
            auth=True,
            print_out=self.infoOutput.isChecked(),
            csv_file=toCsvFile,
            append_csv=self.appendCsv.isChecked()
        )

    def getUser_button_clicked(self):
        toCsvFile = "output/user.csv" if self.storeCsv.isChecked() else ""
        self.client.get(
            E_USER,
            auth=True,
            print_out=self.infoOutput.isChecked(),
            csv_file=toCsvFile,
            append_csv=self.appendCsv.isChecked()
        )

    def getTrips_button_clicked(self):
        toCsvFile = "output/trips.csv" if self.storeCsv.isChecked() else ""
        #vesselId = self.fiskdirId if self.myVessel.isChecked() else None
        vesselId = self.vesselId if self.myVessel.isChecked() else None

        self.client.get(
            E_TRIPS,
            sDate=self.startDateEdit.date(),
            eDate=self.stopDateEdit.date(),
            limit=safe_int(self.limitEdit.text(), 100),
            offset=safe_int(self.offsetEdit.text(), 0),
            gearGroups=self.gearCombo.checked_items_data(),
            vesselGroups=self.vesselCombo.checked_items_data(),
            speciesGroups=self.speciesCombo.checked_items_data(),
            vesselId=vesselId,
            print_out=self.infoOutput.isChecked(),
            csv_file=toCsvFile,
            append_csv=self.appendCsv.isChecked()
        )

    def getAvTripBenchmarks_button_clicked(self):
        toCsvFile = "output/avTripBenchmarks.csv" if self.storeCsv.isChecked() else ""
        vesselId = self.vesselId if self.myVessel.isChecked() else None
        self.client.get(
            E_TRIP_AVG,
            sDate=self.startDateEdit.date(),
            eDate=self.stopDateEdit.date(),
            gearGroups=self.gearCombo.checked_items_data(),
            vesselGroups=self.vesselCombo.checked_items_data(),
            vesselId=vesselId,
            print_out=self.infoOutput.isChecked(),
            csv_file=toCsvFile,
            append_csv=self.appendCsv.isChecked()
        )

    def getEEOI_button_clicked(self):
        toCsvFile = "output/EEOI.csv" if self.storeCsv.isChecked() else ""
        self.client.get(
            E_EEOI,
            sDate=self.startDateEdit.date(),
            eDate=self.stopDateEdit.date(),
            auth=True,
            print_out=self.infoOutput.isChecked(),
            csv_file=toCsvFile,
            append_csv=self.appendCsv.isChecked()
        )

    def getAvEEOI_button_clicked(self):
        toCsvFile = "output/avEEOI.csv" if self.storeCsv.isChecked() else ""
        vesselId = self.vesselId if self.myVessel.isChecked() else None

        self.client.get(
            E_AVG_EEOI,
            sDate=self.startDateEdit.date(),
            eDate=self.stopDateEdit.date(),
            gearGroups=self.gearCombo.checked_items_data(),
            vesselGroups=self.vesselCombo.checked_items_data(),
            speciesGroups=self.speciesCombo.checked_items_data(),
            vesselId=vesselId,
            auth=True,
            print_out=self.infoOutput.isChecked(),
            csv_file=toCsvFile,
            append_csv=self.appendCsv.isChecked()
        )

    def getHaul_button_clicked(self):
        toCsvFile = "output/haul.csv" if self.storeCsv.isChecked() else ""
        vesselId = self.fiskdirId if self.myVessel.isChecked() else None

        self.client.get(
            E_HAULS,
            sDate=self.startDateEdit.date(),
            eDate=self.stopDateEdit.date(),
            gearGroups=self.gearCombo.checked_items_data(),
            vesselGroups=self.vesselCombo.checked_items_data(),
            speciesGroups=self.speciesCombo.checked_items_data(),
            locationGroups=splitCatchLocation(self.locationText.toPlainText()),
            vesselId=vesselId,
            auth=True,
            print_out=self.infoOutput.isChecked(),
            csv_file=toCsvFile,
            append_csv=self.appendCsv.isChecked()
        )

    def getPrice_button_clicked(self):
        """SSB fuel price (public, no auth)."""
        toCsvFile = "output/price.csv" if self.storeCsv.isChecked() else ""
        url = build_ssb_url(self.startDateEdit.date(), self.stopDateEdit.date())

        self.client.request(
            endpoint=url,
            auth=False,  # public
            print_out=self.infoOutput.isChecked(),
            csv_file=toCsvFile,
            append_csv=self.appendCsv.isChecked()
        )

    # -------------------------
    # Auth / Sustainability placeholders
    # -------------------------
    def auth_button_clicked(self):
        # Token comes from env (DATAFANGST_TOKEN). Show simple status.
        from os import environ
        if environ.get("DATAFANGST_TOKEN"):
            QMessageBox.information(self, "Auth status", "Token found in environment (DATAFANGST_TOKEN).")
        else:
            QMessageBox.warning(
                self, "Auth status",
                "No token found.\nSet environment variable DATAFANGST_TOKEN before using protected endpoints."
            )

    def reder_button_clicked(self):
        QMessageBox.information(self, "Reder", "Ikke implementert ennå.")

    def skipper_button_clicked(self):
        QMessageBox.information(self, "Skipper", "Ikke implementert ennå.")

    def bank_button_clicked(self):
        # Prepare files
        toCsvFile = "output/bank-Report.csv" if self.storeCsv.isChecked() else ""
        toJsonFile = "output/bank-Report.json"
        kpi01_pngFile = "output/kpi01"  # no .png here
        kpi02_pngFile = "output/kpi02"
        kpi05_pngFile = "output/kpi05"

        # Prepare KPI input
        this_kpiData = self.kpi_data(
            self.vesselId,
            self.vesselRefIds,
            self.vesselCombo.checked_items_data(),
            self.gearCombo.checked_items_data(),
            self.speciesCombo.checked_items_data(),
            splitCatchLocation(self.locationText.toPlainText()),
            int(self.aggEdit.text()),
            int(self.resEdit.text())
        )

        getDatesArray(self.stopDateEdit.date(), this_kpiData)

        # Update vessels count if input changed
        if (self.vesselRefIds == None) or (self.vesselRefIds == []):  
            if self.isInputChanged():
                startDateList, endDateList = this_kpiData.datesArray
                if endDateList:
                    self.nVessels = getAllTripsInPeriod(
                        E_TRIPS,
                        startDateList[0], endDateList[-1],
                        this_kpiData.lengthG, this_kpiData.gearG, this_kpiData.specG, this_kpiData.locG
                    )
                self.setInputChanged(False)
        else:
            self.nVessels = len(self.vesselRefIds)

        this_kpiData.nVessels = self.nVessels

        # KPIs
        kpi_01(this_kpiData, kpi01_pngFile)
        kpi_02(this_kpiData, kpi02_pngFile)
        kpiCalculations(this_kpiData, kpi05_pngFile)

        # Export
        if toCsvFile:
            jsonArray = [createJsonItem(this_kpiData)]
            createJson(jsonArray, toJsonFile)
            json_to_csv(jsonArray[0], toCsvFile)

    def supplier_button_clicked(self):
        QMessageBox.information(self, "Supplier", "Ikke implementert ennå.")

    def pef_button_clicked(self):
        QMessageBox.information(self, "PEF", "Ikke implementert ennå.")

    # -------------------------
    # KPI menu handlers
    # -------------------------
    def kpi01_button_clicked(self):
        toCsvFile = "output/kpi_01-Report.csv" if self.storeCsv.isChecked() else ""
        toJsonFile = "output/kpi_01-Report.json"
        toPdfFile = "output/kpi_01-Report.pdf"
        toPngFile = "output/kpi01"

        #Collect a copy of the gui data to be used in the KPI01 calculations
        this_kpiData = self.kpi_data(
            self.stopDateEdit.date(),
            self.vesselId,
            self.vesselRefIds,
            self.vesselCombo.checked_items_data(),
            self.gearCombo.checked_items_data(),
            self.speciesCombo.checked_items_data(),
            splitCatchLocation(self.locationText.toPlainText()),
            int(self.aggEdit.text()),
            int(self.resEdit.text())
        )

        if self.isInputChanged():
            self.periodArray = getPeriodDates(this_kpiData)
            self.nVessels, self.tripsArray = getAllTripsInPeriods(E_TRIPS, this_kpiData, self.periodArray)
            self.setInputChanged(False)

        
        kpi01_results = kpi_01(this_kpiData, self.tripsArray)

        span = this_kpiData.span
        endDateList = []
        for i in self.periodArray:
            endDateList.append(i[1])

        norskLgroup = _norsk_length_group(this_kpiData.lengthG)
        title = ( "KPI-01: EEOI [g CO2 /(fangst*nm)] aggregert over {months} måneder\n"
                "Lengde: {vGroup}, Redskap: {gGroup}").format(months=span, vGroup=norskLgroup, gGroup=this_kpiData.gearG)

        plot(endDateList, kpi01_results["myEeoiList"], kpi01_results["refEeoiList"], title,
            "{antall} båter i referansegruppen".format(antall=self.nVessels), fName=toPngFile)

        createPdfDoc(toPdfFile, toPngFile + ".png")

        jsonKeys = ["EEOI", "refEEOI"]

        if toCsvFile:
            jsonDict = createJsonItem(this_kpiData, self.nVessels, self.periodArray, kpi01_results)
            createJson(jsonDict, toJsonFile)
            json_to_csv(jsonDict, toCsvFile)

    def kpi02_button_clicked(self):
        toPngFile = "output/kpi02"
        toCsvFile = "output/kpi-02-Report.csv" if self.storeCsv.isChecked() else ""
        toJsonFile = "output/kpi_02-Report.json"
        toPdfFile = "output/kpi_02-Report.pdf"

        this_kpiData = self.kpi_data(
            self.stopDateEdit.date(),
            self.vesselId,
            self.vesselRefIds,
            self.vesselCombo.checked_items_data(),
            self.gearCombo.checked_items_data(),
            self.speciesCombo.checked_items_data(),
            splitCatchLocation(self.locationText.toPlainText()),
            int(self.aggEdit.text()),
            int(self.resEdit.text())
        )

        if self.isInputChanged():
            self.periodArray = getPeriodDates(this_kpiData)
            self.nVessels, self.tripsArray = getAllTripsInPeriods(E_TRIPS, this_kpiData, self.periodArray)
            self.setInputChanged(False)
 
        kpi02_results = kpi_02(this_kpiData, self.tripsArray)

        span = this_kpiData.span
        endDateList = []
        for i in self.periodArray:
            endDateList.append(i[1])

        norskLgroup = _norsk_length_group(this_kpiData.lengthG)
        title = ( "KPI-02: FUI [g CO2 /fangst] aggregert over {months} måneder\n"
                "Lengde: {vGroup}, Redskap: {gGroup}").format(months=span, vGroup=norskLgroup, gGroup=this_kpiData.gearG)

        plot(endDateList, kpi02_results["myFuiList"], kpi02_results["refFuiList"], title,
            "{antall} båter i referansegruppen".format(antall=self.nVessels), fName=toPngFile)

        createPdfDoc(toPdfFile, toPngFile + ".png")

        if toCsvFile:
            jsonDict = createJsonItem(this_kpiData, self.nVessels, self.periodArray, kpi02_results)
            createJson(jsonDict, toJsonFile)
            json_to_csv(jsonDict, toCsvFile)

    def kpi03_04_button_clicked(self):
        toPngFile03 = "output/kpi03"
        toPngFile04 = "output/kpi04"
        toCsvFile = "output/kpi-03_04-Report.csv" if self.storeCsv.isChecked() else ""
        toJsonFile = "output/kpi_03_04-Report.json"
        toPdfFile = "output/kpi_03_04-Report.pdf"

        this_kpiData = self.kpi_data(
            self.stopDateEdit.date(),
            self.vesselId,
            self.vesselRefIds,
            self.vesselCombo.checked_items_data(),
            self.gearCombo.checked_items_data(),
            self.speciesCombo.checked_items_data(),
            splitCatchLocation(self.locationText.toPlainText()),
            int(self.aggEdit.text()),
            int(self.resEdit.text())
        )

        if self.isInputChanged():
            self.periodArray = getPeriodDates(this_kpiData)
            self.nVessels, self.tripsArray = getAllTripsInPeriods(E_TRIPS, this_kpiData, self.periodArray)
            self.setInputChanged(False)

        kpi03_04_results = kpi_03_04(this_kpiData, self.periodArray, self.nVessels)

        span = this_kpiData.span
        endDateList = []
        for i in self.periodArray:
            endDateList.append(i[1])

        norskLgroup = _norsk_length_group(this_kpiData.lengthG)
        title = ("KPI-03: Rev. per Ton [NOK / Tonn] aggregert over {months} måneder\n"
                "Lengde: {vGroup}, Redskap: {gGroup}").format(months=span, vGroup=norskLgroup, gGroup=this_kpiData.gearG)

        plot(endDateList, kpi03_04_results["myRevPerTonWeightArray"], kpi03_04_results["avRevPerTonWeightArray"], title,
            "{antall} båter i referansegruppen".format(antall=self.nVessels), fName=toPngFile03)


        title = ("KPI-04: Rev. per Hour [NOK / time] aggregert over {months} måneder\n"
                "Lengde: {vGroup}, Redskap: {gGroup}").format(months=span, vGroup=norskLgroup, gGroup=this_kpiData.gearG)
        
        plot(endDateList, kpi03_04_results["myRevPerHourArray"], kpi03_04_results["avRevPerHourArray"], title,
            "{antall} båter i referansegruppen".format(antall=self.nVessels), fName=toPngFile04)

        if toCsvFile:
            jsonDict = createJsonItem(this_kpiData, self.nVessels, self.periodArray, kpi03_04_results)
            createJson(jsonDict, toJsonFile)
            json_to_csv(jsonDict, toCsvFile)


    def kpi_button_clicked(self):
        toPngFile5 = "output/kpi05"
        toPngFile6 = "output/kpi06"
        toCsvFile = "output/kpi-05-Report.csv" if self.storeCsv.isChecked() else ""
        toJsonFile = "output/kpi_05-Report.json"
        toPdfFile = "output/kpi_05-Report.pdf"

        figList = []
        #Collect a copy of the gui data to be used in the KPI05 calculations
        this_kpiData = self.kpi_data(
            self.stopDateEdit.date(),
            self.vesselId,
            self.vesselRefIds,
            self.vesselCombo.checked_items_data(),
            self.gearCombo.checked_items_data(),
            self.speciesCombo.checked_items_data(),
            splitCatchLocation(self.locationText.toPlainText()),
            int(self.aggEdit.text()),
            int(self.resEdit.text())
        )

        
        if self.isInputChanged():
            self.periodArray = getPeriodDates(this_kpiData)
            self.nVessels, self.tripsArray = getAllTripsInPeriods(E_TRIPS, this_kpiData, self.periodArray)
            self.setInputChanged(False)

        
        kpi_results = kpiCalculations(this_kpiData, self.tripsArray)
        # create plots of the results

        span = this_kpiData.span
        endDateList = []
        for i in self.periodArray:
            endDateList.append(i[1])

        norskLgroup = _norsk_length_group(this_kpiData.lengthG)

        today = datetime.today().strftime('%d-%m-%Y')

        #######################################
        # Plot EEOI per periode
        #######################################
        toPngFile = OUTDIR + "eeoi"
        title = ("EEOI aggregert over {months} måneder\n\n").format(months=span)    # Add \n\n to push the title upwards
        text = ("Lengdegruppe {vGroup}, Redskap {gGroup}, Dato: {today}").format(vGroup=norskLgroup, gGroup=this_kpiData.gearG, today=today)

        fig = plot(endDateList, kpi_results["myEeoiList"], kpi_results["refEeoiList"], title,text,
            "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
        figList.append(fig)

        #######################################
        # Plot FUI per periode
        #######################################
        toPngFile = OUTDIR + "fui"
        title = ("FUI aggregert over {months} måneder\n\n").format(months=span)     # Add \n\n to push the title upwards
        text = ("Lengdegruppe {vGroup}, Redskap {gGroup}").format(vGroup=norskLgroup, gGroup=this_kpiData.gearG)

        fig = plot(endDateList, kpi_results["myFuiList"], kpi_results["refFuiList"], title,text,
            "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
        figList.append(fig)

        #######################################
        # Plot total Fangst per periode
        #######################################
        toPngFile = OUTDIR + "fangst"
        title = ("Fangst aggregert over {months} måneder\n\n").format(months=span)      # Add \n\n to push the title upwards
        text = ("Lengdegruppe {vGroup}, Redskap {gGroup}").format(vGroup=norskLgroup, gGroup=this_kpiData.gearG)

        fig = plot(endDateList, kpi_results["myCatchList"], kpi_results["refCatchList"], title,text,
            "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
        figList.append(fig)
        
        #input("Press Enter to continue...")
        #exit()
        
        ########################################
        # Plot gjennomsnittlig Fangst per tur
        ########################################
        toPngFile = OUTDIR + "fangstPerTur"
        title = ("Gj. snittlig fangst per tur, {months} mnd perioder\n\n").format(months=span)      # Add \n\n to push the title upwards
        text = ("Lengdegruppe {vGroup}, Redskap {gGroup}").format(vGroup=norskLgroup, gGroup=this_kpiData.gearG)

        fig = plot(endDateList, kpi_results["weightPerTripList"], kpi_results["refWeightPerTripList"], title, text,
            "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
        figList.append(fig)


        #######################################
        # Plot total Fangstverdi per periode
        #######################################
        toPngFile = OUTDIR + "fangstVerdi"
        title = ("Fangstverdi aggregert over {months} måneder\n\n").format(months=span)     # Add \n\n to push the title upwards
        text = ("Lengdegruppe {vGroup}, Redskap {gGroup}").format(vGroup=norskLgroup, gGroup=this_kpiData.gearG)
        
        fig = plot(endDateList, kpi_results["myCatchValueList"], kpi_results["refCatchValueList"], title, text,
            "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
        figList.append(fig)
        
        ############################################
        # Plot gjennomsnittlig Fangstverdi per tur
        ############################################
        toPngFile = OUTDIR + "fangstVerdiPerTur"
        title = ("Gj. snittlig fangstverdi per tur, {months} mnd perioder\n\n").format(months=span)     # Add \n\n to push the title upwards
        text = ("Lengdegruppe {vGroup}, Redskap {gGroup}").format(vGroup=norskLgroup, gGroup=this_kpiData.gearG)
        
        fig = plot(endDateList, kpi_results["catchValuePerTripList"], kpi_results["refCatchValuePerTripList"], title, text,
            "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
        figList.append(fig)
        
        ########################################
        # Plot Drivstofforbruk per periode
        ########################################
        toPngFile = OUTDIR + "bunkersForbruk"
        title = ("Drivstofforbruk aggregert over {months} måneder\n\n").format(months=span)     # Add \n\n to push the title upwards
        text = ("Lengdegruppe {vGroup}, Redskap {gGroup}").format(vGroup=norskLgroup, gGroup=this_kpiData.gearG)

        fig = plot(endDateList, kpi_results["myFuelList"], kpi_results["refFuelList"], title, text,
            "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
        figList.append(fig)
        
         ##############################################
        # Plot gjennomsnittlig drivstofforbruk per tur
        ###############################################
        toPngFile = OUTDIR + "bunkersPerTur"
        title = ("Gj. snittlig drivstofforbruk per tur, {months} mnd perioder\n\n").format(months=span)     # Add \n\n to push the title upwards
        text = ("Lengdegruppe {vGroup}, Redskap {gGroup}").format(vGroup=norskLgroup, gGroup=this_kpiData.gearG)

        fig = plot(endDateList, kpi_results["fuelPerTripList"], kpi_results["refFuelPerTripList"], title, text,
            "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
        figList.append(fig)

        #######################################
        # Plot Drivstoffkostnad per periode
        #######################################
        # NB! Need fuel costs
        toPngFile = OUTDIR + "bunkersKostnad"
        title = ("Drivstoffkostnad aggregert over {months} måneder\n\n").format(months=span)        # Add \n\n to push the title upwards
        text = ("Lengdegruppe {vGroup}, Redskap {gGroup}").format(vGroup=norskLgroup, gGroup=this_kpiData.gearG)

        fig = plot(endDateList, kpi_results["myFuelList"], kpi_results["refFuelList"], title, text,
            "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
        figList.append(fig)

        # Plot gjennomsnittlig Drivstoffkostnad per tur

        ##############################################
        # Plot gjennomsnittlig antall dager per tur
        ##############################################
        toPngFile = OUTDIR + "dagerPerTur"
        title = ("Gj. snittlig antall dager per tur, {months} mnd perioder\n\n").format(months=span)        # Add \n\n to push the title upwards
        text = ("Lengdegruppe {vGroup}, Redskap {gGroup}").format(vGroup=norskLgroup, gGroup=this_kpiData.gearG)

        fig = plot(endDateList, kpi_results["daysPerTripList"], kpi_results["refDaysPerTripList"], title, text,
            "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
        figList.append(fig)

        ###############################################
        # Plot gjennomsnittlig seilt distanse per tur
        ###############################################
        toPngFile = OUTDIR + "distansePerTur"
        title = ("Gj. snittlig seilt distanse per tur, {months} mnd perioder\n\n").format(months=span)      # Add \n\n to push the title upwards
        text = ("Lengdegruppe {vGroup}, Redskap {gGroup}").format(vGroup=norskLgroup, gGroup=this_kpiData.gearG)

        fig = plot(endDateList, kpi_results["distancePerTripList"], kpi_results["refDistancePerTripList"], title, text,
            "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
        figList.append(fig)

        ############################################
        # Plot gjennomsnittlig CO2 per tur
        ############################################
        toPngFile = OUTDIR + "co2PerTur"
        title = ("Gj. snittlig CO2 utslipp per tur, {months} mnd perioder\n\n").format(months=span)     # Add \n\n to push the title upwards
        text = ("Lengdegruppe {vGroup}, Redskap {gGroup}").format(vGroup=norskLgroup, gGroup=this_kpiData.gearG)

        fig = plot(endDateList, kpi_results["myCO2PerTripList"], kpi_results["refCO2PerTripList"], title, text,
            "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
        figList.append(fig)

        # Plot gjennomsnittlig aktive fisketimer per tur

        # Plot gjennomsnittlig drivstoffkostnad for fangstaktive døgn, gj.snitt per tur

        save_figs_to_pdf(
            figList,
            pdf_path=OUTDIR + "rapport.pdf",
            metadata={
                "Title": "KPI-rapport",
                "Author": "Tore Syversen",
                "Keywords": "fiskeri, KPI, rapport",
            },
            close=True,   # free memory
            tight=True,   # prevent label clipping
        )

        createPdfDoc(toPdfFile, toPngFile + ".png")

        if toCsvFile:
            jsonDict = createJsonItem(this_kpiData, self.nVessels, self.periodArray, kpi_results)
            createJson(jsonDict, toJsonFile)
            json_to_csv(jsonDict, toCsvFile)

        print('KPI calculation complete')

    # -------------------------
    # Window close
    # -------------------------
    def closeEvent(self, event):
        self.close()


