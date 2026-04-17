
from PySide6.QtWidgets import (
    QMainWindow, QToolBar, QCheckBox, QWidget, QPushButton, QApplication, QLabel,
    QDateEdit, QLineEdit, QTextEdit, QMessageBox, QSizePolicy, QHBoxLayout, QFormLayout, QVBoxLayout
)
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import QSize, QDate

from gui_helpers import *
from reports import *
from KPI import kpiCalculations, getAllTripsInPeriod, getAllTripsInPeriods, getPricesInPeriod
from datafangst_client import DatafangstClient
from utility import *
from plot import *
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

#-------------------------------
# Colors for buttons and fields
#-------------------------------
bg_button = "#F1D014"
bg_field = "#91E7F7"
bg_outText = "#91E7F7"
bg_mainwindow = "#D3F1FD"
api_text = "#061EA8"

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

        # Shared client
        self.client = DatafangstClient()


    
#                           WINDOW LAYOUT                              
#------------------------------------------------------------------------
#                       |------------------rightCol_Form---------------||
#                       ||                       |                     ||
#                       ||       inLeftForm      |    inRightForm      ||                
#   leftCol_Form        ||                       |                     || 
#                       |---------------------------------------------- |   
#                       |-----------------------------------------------|                   
#                       |                   calcButton                  |  
#------------------------------------------------------------------------
#                               outTextEdit                             |                   
#------------------------------------------------------------------------

        # -------------------------
        # Window setup
        # -------------------------
        self.setWindowTitle("FiskInfoPlattformen Bærekraftsmodul")
        self.resize(QSize())
        mainWidget = QWidget()
        mainWidget.setStyleSheet(f"QWidget {{ background-color: {bg_mainwindow}; color: black; }}")
        self.setCentralWidget(mainWidget) 

        # --------------------------------------------------------
        # VERTCAL BOX (QVBoxLayout).
        # This is the outermost layout, 2 rows
        # Add it to the main widget
        # --------------------------------------------------------
        vbox = QVBoxLayout()
        mainWidget.setLayout(vbox)  

        # --------------------------------------------------------
        # HORIZONTAL BOX (QHBoxLayout).
        # This is the first nested layout inside vbox, 2 columns
        # Add it to the vbox 1. row
        # --------------------------------------------------------
        hbox = QHBoxLayout()
        vbox.addLayout(hbox)

        # --------------------------------------------------------
        # outTextEdit (QTextEdit).
        # This is the field at the bottom of the window where output is written
        # Add it to the vbox 2. row
        # --------------------------------------------------------
        self.outTextEdit = QTextEdit()
        self.outTextEdit.setStyleSheet(f"QTextEdit {{ background-color: {bg_outText}; color: black; }}")
        self.outTextEdit.setMinimumHeight(100)
        vbox.addWidget(self.outTextEdit)

        # --------------------------------------------------------
        #  HBOX_LEFTCOL (QFormLayout)
        # This is where the fields on the left side of the window will be put
        # Add it to the hbox 1. column
        # --------------------------------------------------------
        leftCol_Form = QFormLayout()
        leftCol_Form.setLabelAlignment(Qt.AlignRight)
        leftCol_Form.setFormAlignment(Qt.AlignTop)
        hbox.addLayout(leftCol_Form)

         # -------------------------------------------------------
        # VERTCAL BOX (QVBoxLayout). 
        # This is the nested layout, inside hbox, 2 rows
        # Add it to the hbox right column
        # --------------------------------------------------------
        vin_box = QVBoxLayout()
        hbox.addLayout(vin_box)

        # ---------------------------------------------------------
        # HORIZONTAL BOX (QHBoxLayout). 
        # This is the nested layout insider vin_box, 2 columns
        # Add it to the vin_box 1. row
        # ---------------------------------------------------------
        hin_box = QHBoxLayout()
        vin_box.addLayout(hin_box)
  
        # ---------------------------------------------------------
        # calculateButton (QPushButton). 
        # This is the button that starts KPI calculations
        # Add it to the vin_box 2. row
        # ---------------------------------------------------------
        # Create a button and add to vin_box 2. row
        self.calcButton = QPushButton("Beregn KPI")
        self.calcButton.setMinimumHeight(30)
        self.calcButton.setStyleSheet(f"QPushButton {{ background-color: {bg_button}; color: black; }}")
        self.calcButton.setToolTip("Trykk for å starte KPI beregninger")
        self.calcButton .clicked.connect(self.kpi_button_clicked)
        vin_box.addWidget(self.calcButton)

        # --------------------------------------------------------
        # inLeftForm (QFormLayout)
        # This is where the left side selection fields will be put
        # Add it to the hin_box 1. column
        # --------------------------------------------------------
        inLeftForm = QFormLayout()
        inLeftForm.setLabelAlignment(Qt.AlignRight)
        inLeftForm.setFormAlignment(Qt.AlignTop)
        hin_box.addLayout(inLeftForm)

        # --------------------------------------------------------
        # inRightForm (QFormLayout)
        # This is where the right side selection fields will be put
        # Add it to the hin_box 1. column
        # --------------------------------------------------------
        inRightForm = QFormLayout()
        inRightForm.setLabelAlignment(Qt.AlignRight)
        inRightForm.setFormAlignment(Qt.AlignTop)
        hin_box.addLayout(inRightForm)


        ##########################################################
        #
        # Populate all the forms
        # Left form
        ##########################################################

        # Stop date
        self.stopDateEdit = QDateEdit(QDate(2024, 12, 31))
        self.stopDateEdit.setDisplayFormat("MM / yyyy")
        self.stopDateEdit.setMinimumWidth(120)
        self.stopDateEdit.setMinimumHeight(30)
        self.stopDateEdit.setStyleSheet(f"QDateEdit {{ background-color: {bg_field}; color: black; }}")
        self.stopDateEdit.setToolTip("KPI beregningene starter med sluttmåned og går bakover i tid. \nAngi sluttmåned her")
        self.stopDateEdit.dateChanged.connect(self.inputChanged)
        leftCol_Form.addRow("Sluttmåned:", self.stopDateEdit)

        # Aggregation months
        self.aggEdit = QLineEdit()
        self.aggEdit.setMinimumWidth(80)
        self.aggEdit.setMinimumHeight(30)
        self.aggEdit.setStyleSheet(f"QLineEdit {{ background-color: {bg_field}; color: black; }}")
        self.aggEdit.setText("3")
        self.aggEdit.setToolTip("Oppgi antall måneder beregningene aggregeres over\nEks, summert over et år, oppgi 12 her")
        self.aggEdit.textChanged.connect(self.inputChanged)
        leftCol_Form.addRow("Aggregert tidsperiode [mnd]:", self.aggEdit)

        # Number of periods
        self.resEdit = QLineEdit()
        self.resEdit.setMinimumWidth(80)
        self.resEdit.setMinimumHeight(30)
        self.resEdit.setStyleSheet(f"QLineEdit {{ background-color: {bg_field}; color: black; }}")
        self.resEdit.setText("4")
        self.resEdit.setToolTip("Oppgi antall perioder å beregne for\nEks, summert per år over 2 år, oppgi 2 her")
        self.resEdit.textChanged.connect(self.inputChanged)
        leftCol_Form.addRow("Antall perioder bakover i tid\nfra sluttdato:", self.resEdit)

        # Calculate start date

        # Vessel group
        self.vesselCombo = MultiComboBox()
        self.vesselCombo.setMinimumWidth(80)
        self.vesselCombo.setMinimumHeight(30)
        self.vesselCombo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.vesselCombo.setStyleSheet(f"QComboBox {{ background-color: {bg_field}; color: black; }}")
        self.vesselCombo.add_items(VESSEL_GROUPS, [False, False, False, False, False, True])
        self.vesselCombo.setToolTip("Velg en eller flere lengdegrupper som skal inngå i beregningene\nHvis ingen velges brukes alle")
        self.vesselCombo.currentTextChanged.connect(self.inputChanged)
        leftCol_Form.addRow("Lengdegruppe:", self.vesselCombo)

        # Gear group
        self.gearCombo = MultiComboBox()
        self.gearCombo.setMinimumWidth(80)
        self.gearCombo.setMinimumHeight(30)
        self.gearCombo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.gearCombo.setStyleSheet(f"QComboBox {{ background-color: {bg_field}; color: black; }}")
        self.gearCombo.add_items(GEAR_GROUPS, [False]*5 + [True] + [False]*4)
        self.gearCombo.setToolTip("Velg en eller flere redskapstyper som skal inngå i beregningene\nHvis ingen velges brukes alle")
        self.gearCombo.currentTextChanged.connect(self.inputChanged)
        leftCol_Form.addRow("Redskapsgruppe:", self.gearCombo)

        # Species group
        self.speciesCombo = MultiComboBox()
        self.speciesCombo.setMinimumWidth(80)
        self.speciesCombo.setMinimumHeight(30)
        self.speciesCombo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.speciesCombo.setStyleSheet(f"QComboBox {{ background-color: {bg_field}; color: black; }}")
        self.speciesCombo.add_items(SPECIES_GROUPS)
        self.speciesCombo.setToolTip("Velg en eller flere artsgrupper som skal inngå i beregningene\nHvis ingen velges brukes alle")
        self.speciesCombo.currentTextChanged.connect(self.inputChanged)
        leftCol_Form.addRow("Artsgruppe:", self.speciesCombo)

        ## Add catch locations 
        self.locationText = QTextEdit()
        self.locationText.setStyleSheet(f"QTextEdit {{ background-color: {bg_field}; color: black; }}")
        self.locationText.textChanged.connect(self.inputChanged)
        leftCol_Form.addRow("Fangstfelt:", self.locationText)


        #------------------------------------
        # Middle form
        #------------------------------------

        # EEOI (KPI-01)
        self.eeoi = QCheckBox("EEOI")
        self.eeoi.setChecked(True)
        inLeftForm.addRow("", self.eeoi)

        # FUI (KPI-02)
    
        self.fui = QCheckBox("FUI")
        self.fui.setChecked(True)
        inLeftForm.addRow("", self.fui)
        
        # Catch & catch value (KPI-05)
        self.catch = QCheckBox("Fangst og fangstverdi")
        self.catch.setChecked(True)
        inLeftForm.addRow("", self.catch)

        # Fuel (KPI-07, KPI-08)
        self.fuel = QCheckBox("Drivstofforbruk")
        self.fuel.setChecked(True)
        inLeftForm.addRow("", self.fuel)

        # Fuel cost (KPI-06, KPI-10)
        self.fuelcost = QCheckBox("Drivstoffkostnad")
        self.fuelcost.setChecked(True)
        inLeftForm.addRow("", self.fuelcost)

        # Relativ revenue (KPI-03, KPI-04)
        self.revenue = QCheckBox("Relativ fortjeneste")
        self.revenue.setChecked(True)
        inLeftForm.addRow("", self.revenue)

        # CO2 utslipp
        self.co2 = QCheckBox("CO2 utslipp")
        self.co2.setChecked(True)
        inLeftForm.addRow("", self.co2)

        # CO2 utslipp
        self.dhd = QCheckBox("Dager, timer, distanse")
        self.dhd.setChecked(True)
        inLeftForm.addRow("", self.dhd)


        #----------------------------------------
        # Right form
        #----------------------------------------

        # Referansegruppe
        self.showRefG = QCheckBox("Vis data for referansegruppe")
        self.showRefG.setChecked(False)
        inRightForm.addRow("", self.showRefG)

        # Referansegruppe
        self.empty = QLabel("------------------------------------")
        inRightForm.addRow("", self.empty)

        # Label for right column
        self.rLabel = QLabel("Valg for Datafangst API test")
        self.rLabel.setStyleSheet(f"QLabel {{ color: {api_text}; }}")
        inRightForm.addRow("", self.rLabel)

        # My vessel
        self.myVessel = QCheckBox("Mitt fartøy")
        #self.myVessel.setStyleSheet(f"QCheckBox::indicator {{ background-color: {bg_button}; color: black; }}")
        self.myVessel.setStyleSheet(f"QCheckBox {{ color: {api_text}; }}")
        inRightForm.addRow("", self.myVessel)

        # Print API response to screen
        self.infoOutput = QCheckBox("Vis API respons på skjerm", self)
        self.infoOutput.setStyleSheet(f"QCheckBox {{ color: {api_text}; }}")
        inRightForm.addRow("", self.infoOutput)

        # Save CSV
        self.storeCsv = QCheckBox("Lagre API-data som CSV", self)
        self.storeCsv.setStyleSheet(f"QCheckBox {{ color: {api_text}; }}")
        inRightForm.addRow("", self.storeCsv)

        # Append CSV
        self.appendCsv = QCheckBox("Legge til data i filen", self)
        self.appendCsv.setStyleSheet(f"QCheckBox {{ color: {api_text}; }}")
        inRightForm.addRow("", self.appendCsv)

        # Label for max responses
        self.respLabel = QLabel("Max antall responser")
        self.respLabel.setStyleSheet(f"QLabel {{ color: {api_text}; }}")
        inRightForm.addRow("", self.respLabel)

        # Limit number of responses
        self.limitEdit = QLineEdit()
        self.limitEdit.setMinimumWidth(80)
        self.limitEdit.setMinimumHeight(30)
        self.limitEdit.setStyleSheet(f"QLineEdit {{ background-color: {bg_field}; color: {api_text}; }}")
        self.limitEdit.setText("100")
        self.limitEdit.setToolTip("Max antall element i responsen, mellom 1-100. \nGjelder kun for 'Get Trips' \nBrukes for å begrense responsen når det er mange turer i perioden")
        #self.limitEdit.textChanged.connect(self.inputChanged)
        inRightForm.addRow("", self.limitEdit)




        # -------------------------
        # Toolbar & Menus
        # -------------------------
        toolbar = QToolBar("My main toolbar")
        #toolbar.setStyleSheet("QToolBar { background-color: black; color: black; }")
        toolbar.setStyleSheet(f"QToolBar {{ background-color: {bg_button}; color: black; }}")
        #toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)

        menu = self.menuBar()
        api_menu = menu.addMenu("Datafangst API")
        pef_menu = menu.addMenu("Pef")
       

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
        # Calculates start date from stopDate, span and periods
        self.startDate = self.stopDateEdit.date().addMonths(-(int(self.aggEdit.text())*int(self.resEdit.text())-1))
        # set day of startDate to the first day in the month
        self.startDate.setDate(self.startDate.year(), self.startDate.month(), 1)
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
            sDate=self.startDate,
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
            sDate=self.startDate,
            eDate=self.stopDateEdit.date(),
            limit=safe_int(self.limitEdit.text(), 100),
            #offset=safe_int(self.offsetEdit.text(), 0),
            offset = 0,
            gearGroups=getGearGroups(self.gearCombo.checked_items_data()),
            vesselGroups=getLengthGroups(self.vesselCombo.checked_items_data()),
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
            sDate=self.startDate,
            eDate=self.stopDateEdit.date(),
            gearGroups=getGearGroups(self.gearCombo.checked_items_data()),
            vesselGroups=getLengthGroups(self.vesselCombo.checked_items_data()),
            vesselId=vesselId,
            print_out=self.infoOutput.isChecked(),
            csv_file=toCsvFile,
            append_csv=self.appendCsv.isChecked()
        )

    def getEEOI_button_clicked(self):
        toCsvFile = "output/EEOI.csv" if self.storeCsv.isChecked() else ""
        self.client.get(
            E_EEOI,
            sDate=self.startDate,
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
            sDate=self.startDate,
            eDate=self.stopDateEdit.date(),
            gearGroups=getGearGroups(self.gearCombo.checked_items_data()),
            vesselGroups=getLengthGroups(self.vesselCombo.checked_items_data()),
            speciesGroups=self.speciesCombo.checked_items_data(),
            vesselId=vesselId,
            auth=True,
            print_out=self.infoOutput.isChecked(),
            csv_file=toCsvFile,
            append_csv=self.appendCsv.isChecked()
        )

    def getHaul_button_clicked(self):
        toCsvFile = "output/haul.csv" if self.storeCsv.isChecked() else ""
        vesselId = self.vesselId if self.myVessel.isChecked() else None

        self.client.get(
            E_HAULS,
            sDate=self.startDate,
            eDate=self.stopDateEdit.date(),
            gearGroups=getGearGroups(self.gearCombo.checked_items_data()),
            vesselGroups=getLengthGroups(self.vesselCombo.checked_items_data()),
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
        url = build_ssb_url(self.startDate, self.stopDateEdit.date())

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
    
    def pef_button_clicked(self):
        QMessageBox.information(self, "PEF", "Ikke implementert ennå.")

    # -------------------------
    # KPI menu handlers
    # -------------------------
    
    def kpi_button_clicked(self):
        toCsvFile = "output/kpi_Report.csv" #if self.storeCsv.isChecked() else ""
        toJsonFile = "output/kpi_Report.json"
        toPdfFile = "output/kpi_Report.pdf"

        figList = []
        #Collect a copy of the gui data to be used in the KPI05 calculations
        this_kpiData = self.kpi_data(
            self.stopDateEdit.date(),
            self.vesselId,
            self.vesselRefIds,
            getLengthGroups(self.vesselCombo.checked_items_data()),
            getGearGroups(self.gearCombo.checked_items_data()),
            self.speciesCombo.checked_items_data(),
            splitCatchLocation(self.locationText.toPlainText()),
            int(self.aggEdit.text()),
            int(self.resEdit.text())
        )

        if self.isInputChanged():
            self.outTextEdit.append("Henter data for alle turer i perioden....")
            QApplication.processEvents()
            self.periodArray = getPeriodDates(this_kpiData)
            self.nVessels, self.tripsArray = getAllTripsInPeriods(E_TRIPS, this_kpiData, self.periodArray)
            self.outTextEdit.append("Henter bunkerspriser i perioden....")
            QApplication.processEvents()
            self.priceList = getPricesInPeriod(self.periodArray)
            self.setInputChanged(False)

        
        self.outTextEdit.append("Beregner KPI'er....")
        QApplication.processEvents()
        kpi_results = kpiCalculations(this_kpiData, self.tripsArray, self.priceList)

        # create plots of the results

        span = this_kpiData.span
        endDateList = []
        for i in self.periodArray:
            endDateList.append(i[1])

        norskLgroup = _norsk_length_group(this_kpiData.lengthG)

        today = datetime.today().strftime('%d-%m-%Y')

        self.outTextEdit.append("Plotter figurer....")
        QApplication.processEvents()

        #######################################
        # Plot EEOI per periode
        #######################################
        if self.eeoi.isChecked():
            toPngFile = OUTDIR + "eeoi"
            title = ("EEOI aggregert over {months} måneder\n\n").format(months=span)    # Add \n\n to push the title upwards
            text = ("Lengdegruppe {vGroup}, Redskap {gGroup}, Dato: {today}").format(vGroup=norskLgroup, gGroup=this_kpiData.gearG, today=today)

            if self.showRefG.isChecked():
                fig = plot(endDateList, kpi_results["myEeoiList"], kpi_results["refEeoiList"], title,text,
                    "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            else:
                fig = plot(endDateList, kpi_results["myEeoiList"], title = title,text = text,
                    xlabel = "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            figList.append(fig)

        #######################################
        # Plot FUI per periode
        #######################################
        if self.fui.isChecked():
            toPngFile = OUTDIR + "fui"
            title = ("FUI aggregert over {months} måneder\n\n").format(months=span)     # Add \n\n to push the title upwards
            text = ("Lengdegruppe {vGroup}, Redskap {gGroup}").format(vGroup=norskLgroup, gGroup=this_kpiData.gearG)

            if self.showRefG.isChecked():
                fig = plot(endDateList, kpi_results["myFuiList"], kpi_results["refFuiList"], title,text,
                    "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            else:
                fig = plot(endDateList, kpi_results["myFuiList"], title = title,text = text,
                    xlabel = "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            figList.append(fig)

        #######################################
        # Plot total Fangst per periode
        #######################################
        if self.catch.isChecked():
            toPngFile = OUTDIR + "fangst"
            title = ("Fangst aggregert over {months} måneder\n\n").format(months=span)      # Add \n\n to push the title upwards
            text = ("Lengdegruppe {vGroup}, Redskap {gGroup}").format(vGroup=norskLgroup, gGroup=this_kpiData.gearG)

            if self.showRefG.isChecked():
                fig = plot(endDateList, kpi_results["myCatchList"], kpi_results["refCatchList"], title,text,
                    "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            else:
                fig = plot(endDateList, kpi_results["myCatchList"], title = title,text = text,
                    xlabel = "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            figList.append(fig)
        
        ########################################
        # Plot gjennomsnittlig Fangst per tur
        ########################################
            toPngFile = OUTDIR + "fangstPerTur"
            title = ("Gj. snittlig fangst per tur, {months} mnd perioder\n\n").format(months=span)      # Add \n\n to push the title upwards
            text = ("Lengdegruppe {vGroup}, Redskap {gGroup}").format(vGroup=norskLgroup, gGroup=this_kpiData.gearG)

            if self.showRefG.isChecked():
                fig = plot(endDateList, kpi_results["weightPerTripList"], kpi_results["refWeightPerTripList"], title, text,
                    "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            else: 
                fig = plot(endDateList, kpi_results["weightPerTripList"], title = title,text = text,
                    xlabel = "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            figList.append(fig)


        #######################################
        # Plot total Fangstverdi per periode
        #######################################
            toPngFile = OUTDIR + "fangstVerdi"
            title = ("Fangstverdi aggregert over {months} måneder\n\n").format(months=span)     # Add \n\n to push the title upwards
            text = ("Lengdegruppe {vGroup}, Redskap {gGroup}").format(vGroup=norskLgroup, gGroup=this_kpiData.gearG)
            
            if self.showRefG.isChecked():
                fig = plot(endDateList, kpi_results["myCatchValueList"], kpi_results["refCatchValueList"], title, text,
                    "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            else:
                fig = plot(endDateList, kpi_results["myCatchValueList"], title = title,text = text,
                    xlabel = "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            figList.append(fig)
        
        ############################################
        # Plot gjennomsnittlig Fangstverdi per tur
        ############################################
            toPngFile = OUTDIR + "fangstVerdiPerTur"
            title = ("Gj. snittlig fangstverdi per tur, {months} mnd perioder\n\n").format(months=span)     # Add \n\n to push the title upwards
            text = ("Lengdegruppe {vGroup}, Redskap {gGroup}").format(vGroup=norskLgroup, gGroup=this_kpiData.gearG)
            
            if self.showRefG.isChecked():
                fig = plot(endDateList, kpi_results["catchValuePerTripList"], kpi_results["refCatchValuePerTripList"], title, text,
                    "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            else:
                fig = plot(endDateList, kpi_results["catchValuePerTripList"], title = title,text = text,
                    xlabel = "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            figList.append(fig)

        ########################################
        # Plot Drivstofforbruk per periode
        ########################################
        if self.fuel.isChecked():
            toPngFile = OUTDIR + "bunkersForbruk"
            title = ("Drivstofforbruk aggregert over {months} måneder\n\n").format(months=span)     # Add \n\n to push the title upwards
            text = ("Lengdegruppe {vGroup}, Redskap {gGroup}").format(vGroup=norskLgroup, gGroup=this_kpiData.gearG)

            if self.showRefG.isChecked():
                fig = plot(endDateList, kpi_results["myFuelList"], kpi_results["refFuelList"], title, text,
                    "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            else:
                fig = plot(endDateList, kpi_results["myFuelList"], title = title,text = text,
                    xlabel = "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            figList.append(fig)
        
         ##############################################
        # Plot gjennomsnittlig drivstofforbruk per tur
        ###############################################
            toPngFile = OUTDIR + "bunkersPerTur"
            title = ("Gj. snittlig drivstofforbruk per tur, {months} mnd perioder\n\n").format(months=span)     # Add \n\n to push the title upwards
            text = ("Lengdegruppe {vGroup}, Redskap {gGroup}").format(vGroup=norskLgroup, gGroup=this_kpiData.gearG)

            if self.showRefG.isChecked():
                fig = plot(endDateList, kpi_results["fuelPerTripList"], kpi_results["refFuelPerTripList"], title, text,
                    "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            else:
                fig = plot(endDateList, kpi_results["fuelPerTripList"], title = title,text = text,
                    xlabel = "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            figList.append(fig)

        #######################################
        # Plot Drivstoffkostnad per periode
        #######################################
        if self.fuelcost.isChecked():
            toPngFile = OUTDIR + "bunkersKostnad"
            title = ("Drivstoffkostnad aggregert over {months} måneder\n\n").format(months=span)        # Add \n\n to push the title upwards
            text = ("Lengdegruppe {vGroup}, Redskap {gGroup}").format(vGroup=norskLgroup, gGroup=this_kpiData.gearG)

            if self.showRefG.isChecked():
                fig = plot(endDateList, kpi_results["myFuelCostList"], kpi_results["refFuelCostList"], title, text,
                    "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            else:
                fig = plot(endDateList, kpi_results["myFuelCostList"], title = title,text = text,
                    xlabel = "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            figList.append(fig)

        ################################################
        # Plot gjennomsnittlig Drivstoffkostnad per tur
        ################################################
            toPngFile = OUTDIR + "bunkersKostnadPerTur"
            title = ("Gj. snittlig drivstoffkostnad per tur, {months} måneder\n\n").format(months=span)        # Add \n\n to push the title upwards
            text = ("Lengdegruppe {vGroup}, Redskap {gGroup}").format(vGroup=norskLgroup, gGroup=this_kpiData.gearG)

            if self.showRefG.isChecked():
                fig = plot(endDateList, kpi_results["fuelCostPerTripList"], kpi_results["refFuelCostPerTripList"], title, text,
                    "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            else:
                fig = plot(endDateList, kpi_results["fuelCostPerTripList"], title = title,text = text,
                    xlabel = "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            figList.append(fig)

        ################################################################################
        # Plot gjennomsnittlig drivstoffkostnad for fangstaktive døgn, gj.snitt per tur
        ################################################################################
        # Hva er fangstaktivt døgn?

        ##############################################
        # Plot relativ fortjeneste per tonn drivstoff
        ##############################################
        if self.revenue.isChecked():
            toPngFile = OUTDIR + "RelativFortjenestePerFangst"
            title = ("Relativ fortjeneste per tonn fangst, {months} mnd perioder\n\n").format(months=span)     # Add \n\n to push the title upwards
            text = ("Lengdegruppe {vGroup}, Redskap {gGroup}").format(vGroup=norskLgroup, gGroup=this_kpiData.gearG)

            if self.showRefG.isChecked():
                fig = plot(endDateList, kpi_results["myRevPerTonWeightList"], kpi_results["avRevPerTonWeightList"], title, text,
                    "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            else:
                fig = plot(endDateList, kpi_results["myRevPerTonWeightList"], title = title,text = text,
                    xlabel = "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            figList.append(fig)

        ##############################################
        # Plot relativ fortjeneste per time
        ##############################################
            toPngFile = OUTDIR + "RelativFortjenestePerTime"
            title = ("Relativ fortjeneste per time, {months} mnd perioder\n\n").format(months=span)     # Add \n\n to push the title upwards
            text = ("Lengdegruppe {vGroup}, Redskap {gGroup}").format(vGroup=norskLgroup, gGroup=this_kpiData.gearG)

            if self.showRefG.isChecked():
                fig = plot(endDateList, kpi_results["myRevPerHourList"], kpi_results["avRevPerHourList"], title, text,
                    "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            else:
                fig = plot(endDateList, kpi_results["myRevPerHourList"], title = title,text = text,
                    xlabel = "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            figList.append(fig)
        
        ############################################
        # Plot gjennomsnittlig CO2 per tur
        ############################################
        if self.co2.isChecked():
            toPngFile = OUTDIR + "co2PerTur"
            title = ("Gj. snittlig CO2 utslipp per tur, {months} mnd perioder\n\n").format(months=span)     # Add \n\n to push the title upwards
            text = ("Lengdegruppe {vGroup}, Redskap {gGroup}").format(vGroup=norskLgroup, gGroup=this_kpiData.gearG)

            if self.showRefG.isChecked():
                fig = plot(endDateList, kpi_results["myCO2PerTripList"], kpi_results["refCO2PerTripList"], title, text,
                    "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            else:
                fig = plot(endDateList, kpi_results["myCO2PerTripList"], title = title,text = text,
                    xlabel = "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            figList.append(fig)

        ##############################################
        # Plot gjennomsnittlig antall dager per tur
        ##############################################
        if self.dhd.isChecked():
            toPngFile = OUTDIR + "dagerPerTur"
            title = ("Gj. snittlig antall dager per tur, {months} mnd perioder\n\n").format(months=span)        # Add \n\n to push the title upwards
            text = ("Lengdegruppe {vGroup}, Redskap {gGroup}").format(vGroup=norskLgroup, gGroup=this_kpiData.gearG)

            if self.showRefG.isChecked():
                fig = plot(endDateList, kpi_results["daysPerTripList"], kpi_results["refDaysPerTripList"], title, text,
                    "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            else:
                fig = plot(endDateList, kpi_results["daysPerTripList"], title = title,text = text,
                    xlabel = "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            figList.append(fig)

        ###############################################
        # Plot gjennomsnittlig seilt distanse per tur
        ###############################################
            toPngFile = OUTDIR + "distansePerTur"
            title = ("Gj. snittlig seilt distanse per tur, {months} mnd perioder\n\n").format(months=span)      # Add \n\n to push the title upwards
            text = ("Lengdegruppe {vGroup}, Redskap {gGroup}").format(vGroup=norskLgroup, gGroup=this_kpiData.gearG)

            if self.showRefG.isChecked():
                fig = plot(endDateList, kpi_results["distancePerTripList"], kpi_results["refDistancePerTripList"], title, text,
                    "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)
            else:
                fig = plot(endDateList, kpi_results["distancePerTripList"], title = title,text = text,
                    xlabel = "Referanse\n{antall} båter".format(antall=self.nVessels), fName=toPngFile)

        
        #################################################
        # Plot gjennomsnittlig aktive fisketimer per tur
        #################################################
        # Finn start og stopp tid for alle hal på en tur og summer for å finne totaltid per tur
        # Legg sammen alle turer i perioden

        

        save_figs_to_pdf(
            figList,
            pdf_path=toPdfFile,
            metadata={
                "Title": "KPI-rapport",
                "Author": "Tore Syversen",
                "Keywords": "fiskeri, KPI, rapport",
            },
            close=True,   # free memory
            tight=True,   # prevent label clipping
        )

        self.outTextEdit.append(f"Lagrer plot til {toPdfFile}")
        QApplication.processEvents()

        #createPdfDoc(toPdfFile, toPngFile + ".png")

        if toCsvFile:
            jsonDict = createJsonItem(this_kpiData, self.nVessels, self.periodArray, kpi_results)
            createJson(jsonDict, toJsonFile)
            json_to_csv(jsonDict, toCsvFile)

        self.outTextEdit.append(f"Lagrer CSV til {toCsvFile} og JSON til {toJsonFile}\n")
        QApplication.processEvents()

    # -------------------------
    # Window close
    # -------------------------
    def closeEvent(self, event):
        self.close()





        


