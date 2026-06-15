
from PySide6.QtWidgets import (
    QMainWindow, QToolBar, QCheckBox, QWidget, QPushButton, QLabel,
    QDateEdit, QLineEdit, QTextEdit, QMessageBox, QSizePolicy, QHBoxLayout, QFormLayout, QVBoxLayout
)
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import QSize, QDate, Qt, QThread
from dataclasses import dataclass
import json
from gui_helpers import MultiComboBox
from datafangst_client import DatafangstClient
from utility import getLengthGroups, getGearGroups, splitCatchLocation, norsk_length_group
from plots import createPlots
from datetime import datetime
from kpi_worker import KPIWorker
from Options import *
import Endpoints as ep




def _safe_int(text: str, default: int = 0) -> int:
    try:
        return int(text)
    except Exception:
        return default
    

@dataclass(frozen=True)
class GUIData:
    endDate: QDate
    lengthG: list[str]
    gearG: list[str]
    specG: list[str]
    locG: list[str]
    span: int
    noPeriods: int

@dataclass(frozen = True)
class checkBoxes:
    eeoi: bool
    fui: bool
    catch: bool
    fuel: bool
    fuelcost: bool
    revenue: bool
    co2: bool
    dhd: bool
    vsme: bool
    showRefG: bool
    


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # -------------------------
        # Basic state
        # -------------------------
        self.inputHasChanged = True
        self.nVessels = 0
        self.actionText = ""
        self.getParams = ""
        self.myTrips = None
        self.refTrips = None

        self.periodArray = []
        self.tripsArray = []
        self.figList = []

        self._busy = False
        

    
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

        self.setWindowIcon(QIcon(APP_ICON))
        self.setWindowTitle(APP_TITLE)
       
        self.resize(QSize())
        mainWidget = QWidget()
        #mainWidget.setStyleSheet(f"QWidget {{ background-color: {bg_mainwindow}; color: black; }}")
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
        self.outTextEdit.setStyleSheet(f"QTextEdit {{ background-color: {BG_OUTTEXT_COL}; color: black; }}")
        self.outTextEdit.setMinimumHeight(300)
        self.outTextEdit.setMinimumWidth(600)
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
        self.calcButton.setStyleSheet(f"QPushButton {{ background-color: {BG_BUTTON_COL}; color: black; }}")
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
        self.stopDateEdit.setStyleSheet(f"QDateEdit {{ background-color: {BG_FIELD_COL}; color: black; }}")
        self.stopDateEdit.setToolTip("KPI beregningene starter med sluttmåned og går bakover i tid. \nAngi sluttmåned her")
        self.stopDateEdit.dateChanged.connect(self.inputChanged)
        leftCol_Form.addRow("Sluttmåned:", self.stopDateEdit)

        # Aggregation months
        self.aggEdit = QLineEdit()
        self.aggEdit.setMinimumWidth(80)
        self.aggEdit.setMinimumHeight(30)
        self.aggEdit.setStyleSheet(f"QLineEdit {{ background-color: {BG_FIELD_COL}; color: black; }}")
        self.aggEdit.setText("3")
        self.aggEdit.setToolTip("Oppgi antall måneder beregningene aggregeres over\nEks, summert over et år, oppgi 12 her")
        self.aggEdit.textChanged.connect(self.inputChanged)
        leftCol_Form.addRow("Aggregert tidsperiode [mnd]:", self.aggEdit)

        # Number of periods
        self.resEdit = QLineEdit()
        self.resEdit.setMinimumWidth(80)
        self.resEdit.setMinimumHeight(30)
        self.resEdit.setStyleSheet(f"QLineEdit {{ background-color: {BG_FIELD_COL}; color: black; }}")
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
        self.vesselCombo.setStyleSheet(f"QComboBox {{ background-color: {BG_FIELD_COL}; color: black; }}")
        self.vesselCombo.add_items(VESSEL_GROUPS, [False, False, False, False, False, True])
        self.vesselCombo.setToolTip("Velg en eller flere lengdegrupper som skal inngå i beregningene\nHvis ingen velges brukes alle")
        self.vesselCombo.currentTextChanged.connect(self.inputChanged)
        leftCol_Form.addRow("Lengdegruppe:", self.vesselCombo)

        # Gear group
        self.gearCombo = MultiComboBox()
        self.gearCombo.setMinimumWidth(80)
        self.gearCombo.setMinimumHeight(30)
        self.gearCombo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.gearCombo.setStyleSheet(f"QComboBox {{ background-color: {BG_FIELD_COL}; color: black; }}")
        self.gearCombo.add_items(GEAR_GROUPS, [False]*5 + [True] + [False]*4)
        self.gearCombo.setToolTip("Velg en eller flere redskapstyper som skal inngå i beregningene\nHvis ingen velges brukes alle")
        self.gearCombo.currentTextChanged.connect(self.inputChanged)
        leftCol_Form.addRow("Redskapsgruppe:", self.gearCombo)

        # Species group
        self.speciesCombo = MultiComboBox()
        self.speciesCombo.setMinimumWidth(80)
        self.speciesCombo.setMinimumHeight(30)
        self.speciesCombo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.speciesCombo.setStyleSheet(f"QComboBox {{ background-color: {BG_FIELD_COL}; color: black; }}")
        self.speciesCombo.add_items(SPECIES_GROUPS)
        self.speciesCombo.setToolTip("Velg en eller flere artsgrupper som skal inngå i beregningene\nHvis ingen velges brukes alle")
        self.speciesCombo.currentTextChanged.connect(self.inputChanged)
        leftCol_Form.addRow("Artsgruppe:", self.speciesCombo)

        ## Add catch locations 
        self.locationText = QTextEdit()
        self.locationText.setStyleSheet(f"QTextEdit {{ background-color: {BG_FIELD_COL}; color: black; }}")
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

        # VSME KPI's
        self.vsme = QCheckBox("VSME")
        self.vsme.setChecked(True)
        inLeftForm.addRow("", self.vsme)


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
        self.rLabel.setStyleSheet(f"QLabel {{ color: {API_TEXT_COL}; }}")
        inRightForm.addRow("", self.rLabel)

        # My vessel
        self.myVessel = QCheckBox("Mitt fartøy")
        #self.myVessel.setStyleSheet(f"QCheckBox::indicator {{ background-color: {bg_button}; color: black; }}")
        self.myVessel.setStyleSheet(f"QCheckBox {{ color: {API_TEXT_COL}; }}")
        inRightForm.addRow("", self.myVessel)

        # Print API response to screen
        self.infoOutput = QCheckBox("Vis API respons", self)
        self.infoOutput.setStyleSheet(f"QCheckBox {{ color: {API_TEXT_COL}; }}")
        inRightForm.addRow("", self.infoOutput)

        # Save CSV
        self.storeCsv = QCheckBox("Lagre API-data som CSV", self)
        self.storeCsv.setStyleSheet(f"QCheckBox {{ color: {API_TEXT_COL}; }}")
        inRightForm.addRow("", self.storeCsv)

        # Append CSV
        self.appendCsv = QCheckBox("Legge til data i filen", self)
        self.appendCsv.setStyleSheet(f"QCheckBox {{ color: {API_TEXT_COL}; }}")
        inRightForm.addRow("", self.appendCsv)

        # Label for max responses
        self.respLabel = QLabel("Max antall responser")
        self.respLabel.setStyleSheet(f"QLabel {{ color: {API_TEXT_COL}; }}")
        inRightForm.addRow("", self.respLabel)

        # Limit number of responses
        self.limitEdit = QLineEdit()
        self.limitEdit.setMinimumWidth(80)
        self.limitEdit.setMinimumHeight(30)
        self.limitEdit.setStyleSheet(f"QLineEdit {{ background-color: {BG_FIELD_COL}; color: {API_TEXT_COL}; }}")
        self.limitEdit.setText("100")
        self.limitEdit.setToolTip("Max antall element i responsen, mellom 1-100. \nGjelder kun for 'Get Trips' \nBrukes for å begrense responsen når det er mange turer i perioden")
        #self.limitEdit.textChanged.connect(self.inputChanged)
        inRightForm.addRow("", self.limitEdit)


        # -------------------------
        # Toolbar & Menus
        # -------------------------
        toolbar = QToolBar("My main toolbar")
        #toolbar.setStyleSheet("QToolBar { background-color: black; color: black; }")
        toolbar.setStyleSheet(f"QToolBar {{ background-color: {BG_BUTTON_COL}; color: black; }}")
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

        # shared client
        self.client = DatafangstClient(self)
        self.client.progress.connect(self.outTextEdit.append)

    # ---------------------------------
    # Track changes in input parameters
    # ---------------------------------
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
    # Printout to the textEditBox
    # -------------------------
    def printout(self, response):
        if self.infoOutput.isChecked(): 
            pretty = json.dumps(
                response,
                indent=4,
                ensure_ascii=False
            )
            self.outTextEdit.append("======= API RESULT ======")
            self.outTextEdit.append(pretty)
            self.outTextEdit.append("=========================\n")


    # -------------------------
    # API Button Handlers
    # -------------------------
    def getGear_button_clicked(self):
        toCsvFile = "output/gear.csv" if self.storeCsv.isChecked() else ""
        response = self.client.get(
            ep.E_GEAR,
            auth=False,  # public
            print_out=self.infoOutput.isChecked(),
            csv_file=toCsvFile,
            append_csv=self.appendCsv.isChecked()
        )
        self.printout(response)

    def getGearGroups_button_clicked(self):
        toCsvFile = "output/gearGroups.csv" if self.storeCsv.isChecked() else ""
        response = self.client.get(
            ep.E_GEAR_GROUPS,
            auth=False,
            print_out=self.infoOutput.isChecked(),
            csv_file=toCsvFile,
            append_csv=self.appendCsv.isChecked()
        )
        self.printout(response)

    def getGearMainGroups_button_clicked(self):
        toCsvFile = "output/gearMainGroups.csv" if self.storeCsv.isChecked() else ""
        response = self.client.get(
            ep.E_GEAR_MAIN_GROUPS,
            auth=False,
            print_out=self.infoOutput.isChecked(),
            csv_file=toCsvFile,
            append_csv=self.appendCsv.isChecked()
        )
        self.printout(response)

    def getVessels_button_clicked(self):
        toCsvFile = "output/vessels.csv" if self.storeCsv.isChecked() else ""
        response = self.client.get(
            ep.E_VESSELS,
            auth=True,
            print_out=self.infoOutput.isChecked(),
            csv_file=toCsvFile,
            append_csv=self.appendCsv.isChecked()
        )
        self.printout(response)

    def getVesselsFuel_button_clicked(self):
        toCsvFile = "output/vesselsFuel.csv" if self.storeCsv.isChecked() else ""
        response = self.client.get(
            ep.E_VESSEL_FUEL,
            sDate=self.startDate,
            eDate=self.stopDateEdit.date(),
            auth=True,
            print_out=self.infoOutput.isChecked(),
            csv_file=toCsvFile,
            append_csv=self.appendCsv.isChecked()
        )
        self.printout(response)

    def getVesselsLiveFuel_button_clicked(self):
        toCsvFile = "output/vesselsLiveFuel.csv" if self.storeCsv.isChecked() else ""
        response = self.client.get(
            ep.E_VESSEL_LIVE_FUEL,
            auth=True,
            print_out=self.infoOutput.isChecked(),
            csv_file=toCsvFile,
            append_csv=self.appendCsv.isChecked()
        )
        self.printout(response)

    def getVesselsBenchmarks_button_clicked(self):
        toCsvFile = "output/benchmarks.csv" if self.storeCsv.isChecked() else ""
        response = self.client.get(
            ep.E_VESSEL_BENCHMARKS,
            auth=True,
            print_out=self.infoOutput.isChecked(),
            csv_file=toCsvFile,
            append_csv=self.appendCsv.isChecked()
        )
        self.printout(response)

    def getUser_button_clicked(self):
        toCsvFile = "output/user.csv" if self.storeCsv.isChecked() else ""
        response = self.client.get(
            ep.E_USER,
            auth=True,
            print_out=self.infoOutput.isChecked(),
            csv_file=toCsvFile,
            append_csv=self.appendCsv.isChecked()
        )
        self.printout(response)

    def getTrips_button_clicked(self):
        toCsvFile = "output/trips.csv" if self.storeCsv.isChecked() else ""
        #vesselId = self.fiskdirId if self.myVessel.isChecked() else None
        vesselId = self.vesselId if self.myVessel.isChecked() else None

        response = self.client.get(
            ep.E_TRIPS,
            sDate=self.startDate,
            eDate=self.stopDateEdit.date(),
            limit=_safe_int(self.limitEdit.text(), 100),
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
        self.printout(response)

    def getAvTripBenchmarks_button_clicked(self):
        toCsvFile = "output/avTripBenchmarks.csv" if self.storeCsv.isChecked() else ""
        vesselId = self.vesselId if self.myVessel.isChecked() else None
        response = self.client.get(
            ep.E_TRIP_AVG,
            sDate=self.startDate,
            eDate=self.stopDateEdit.date(),
            gearGroups=getGearGroups(self.gearCombo.checked_items_data()),
            vesselGroups=getLengthGroups(self.vesselCombo.checked_items_data()),
            vesselId=vesselId,
            print_out=self.infoOutput.isChecked(),
            csv_file=toCsvFile,
            append_csv=self.appendCsv.isChecked()
        )
        self.printout(response)

    def getEEOI_button_clicked(self):
        toCsvFile = "output/EEOI.csv" if self.storeCsv.isChecked() else ""
        response = self.client.get(
            ep.E_EEOI,
            sDate=self.startDate,
            eDate=self.stopDateEdit.date(),
            auth=True,
            print_out=self.infoOutput.isChecked(),
            csv_file=toCsvFile,
           
            append_csv=self.appendCsv.isChecked()
        )
        self.printout(response)

    def getAvEEOI_button_clicked(self):
        toCsvFile = "output/avEEOI.csv" if self.storeCsv.isChecked() else ""
        vesselId = self.vesselId if self.myVessel.isChecked() else None

        response = self.client.get(
            ep.E_AVG_EEOI,
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
        self.printout(response)

    def getHaul_button_clicked(self):
        toCsvFile = "output/haul.csv" if self.storeCsv.isChecked() else ""
        vesselId = self.vesselId if self.myVessel.isChecked() else None

        response = self.client.get(
            ep.E_HAULS,
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
        self.printout(response)

    def getPrice_button_clicked(self):
        """SSB fuel price (public, no auth)."""
        toCsvFile = "output/price.csv" if self.storeCsv.isChecked() else ""
        url = ep.build_ssb_url(ep.SSB_PRICE_BASE, self.startDate, self.stopDateEdit.date())

        response = self.client.request(
            endpoint=url,
            auth=False,  # public
            print_out=self.infoOutput.isChecked(),
            csv_file=toCsvFile,
            append_csv=self.appendCsv.isChecked()
        )
        self.printout(response)

    # -------------------------
    # Pef button placeholders
    # -------------------------
    
    def pef_button_clicked(self):
        QMessageBox.information(self, "PEF", "Ikke implementert ennå.")

    # -------------------------
    # KPI calculate button handler
    # -------------------------
    def kpi_button_clicked(self):
        # Get CheckBox states
        self.myCheckBoxes = checkBoxes(
            self.eeoi.isChecked(),
            self.fui.isChecked(),
            self.catch.isChecked(),
            self.fuel.isChecked(),
            self.fuelcost.isChecked(),
            self.revenue.isChecked(),
            self.co2.isChecked(),
            self.dhd.isChecked(),
            self.vsme.isChecked(),
            self.showRefG.isChecked()           
            )

        # Perform new calculations only when input parameters have changed
        if self.isInputChanged():
            # Disable the button without loosing focus
            if self._busy:
                return
            self._busy = True
            self.calcButton.setDown(True)

            self.outTextEdit.append("Starter KPI-beregning…")
            # Build KPI input
            self.this_GUIData = GUIData(
                endDate=self.stopDateEdit.date(),
                lengthG=getLengthGroups(self.vesselCombo.checked_items_data()),
                gearG=getGearGroups(self.gearCombo.checked_items_data()),
                specG=self.speciesCombo.checked_items_data(),
                locG=splitCatchLocation(self.locationText.toPlainText()),
                span=int(self.aggEdit.text()),
                noPeriods=int(self.resEdit.text()),
            )

            # Start worker thread
            self._kpiThread = QThread()
            self._kpiWorker = KPIWorker(self.this_GUIData)

            self._kpiWorker.moveToThread(self._kpiThread)

            self._kpiWorker.progress.connect(self.outTextEdit.append)
            self._kpiWorker.finished.connect(self.on_kpi_finished)
            self._kpiWorker.error.connect(self.on_kpi_error)

            self._kpiThread.started.connect(self._kpiWorker.run)
        
            self._kpiWorker.finished.connect(self._kpiThread.quit)
            self._kpiWorker.finished.connect(self._kpiWorker.deleteLater)
            self._kpiThread.finished.connect(self._kpiThread.deleteLater)

            self._kpiThread.start()

        # If no change in input parameters, just plot results
        else:
            today = datetime.today().strftime('%d-%m-%Y')
            norskLgroup = norsk_length_group(self.this_GUIData.lengthG)
            text = ("Lengdegruppe {vGroup}, Redskap {gGroup}, Dato: {today}").format(vGroup=norskLgroup, gGroup=self.this_GUIData.gearG, today=today)
            createPlots(self.KpiResults, self.this_GUIData, text, self.myCheckBoxes, PDF_FILE, JDSON_FILE, CSV_FILE)
            self.outTextEdit.append(f"PLOT:   --->   {PDF_FILE}")
            self.outTextEdit.append(f"JSON:   --->   {JDSON_FILE}")
            self.outTextEdit.append(f"CSV :    --->   {CSV_FILE}\n")
      
            
    def on_kpi_finished(self, result):
        # Enable the calcButton
        self._busy = False
        self.calcButton.setDown(False)

        self.setInputChanged(False)
        self.KpiResults = result
        today = datetime.today().strftime('%d-%m-%Y')
        norskLgroup = norsk_length_group(self.this_GUIData.lengthG)
        text = ("Lengdegruppe {vGroup}, Redskap {gGroup}, Dato: {today}").format(vGroup=norskLgroup, gGroup=self.this_GUIData.gearG, today=today)
        createPlots(self.KpiResults, self.this_GUIData, text, self.myCheckBoxes, PDF_FILE, JDSON_FILE, CSV_FILE)
        self.outTextEdit.append(f"PLOT:   --->   {PDF_FILE}")
        self.outTextEdit.append(f"JSON:   --->   {JDSON_FILE}")
        self.outTextEdit.append(f"CSV :    --->   {CSV_FILE}\n")
        
        
    def on_kpi_error(self, message):
        # Enable the calcButton
        self._busy = False
        self.calcButton.setDown(False)

        self.statusBar().clearMessage()
        QMessageBox.critical(self, "KPI-feil", message)

    

    # -------------------------
    # Window close
    # -------------------------
    def closeEvent(self, event):
        event.accept()





        


