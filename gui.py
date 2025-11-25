from PySide6.QtWidgets import QMainWindow, QToolBar, QLabel, QCheckBox, QGridLayout, QWidget, QDateEdit, QLineEdit, QComboBox, QTextEdit
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import*
from gui_helpers import *
from reports import*
from KPI import*

class MainWindow(QMainWindow):
    def __init__(self):
        
        super().__init__()
       
        self.inputHasChanged = True
        self.nVessels = 0
        ## Main window
        self.actionText =""
        self.getParams = ""
        self.fiskdirId = 2013063493      # Gadus Njord
        self.setWindowTitle("FiskInfoPlattformen Bærekraftsmodul")
        self.setFixedSize(QSize(700, 400))
        #self.setStyleSheet("background-color: lightyellow;")
        
        ###########  LAYOUT ###############
        layout = QGridLayout()
        layout.setContentsMargins(20,20,20,20)
        layout.setSpacing(20)
           
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        ## Add limit field
        limitLabel = QLabel("Max antall:")
        layout.addWidget(limitLabel, 4, 0)
        self.limitEdit = QLineEdit()
        self.limitEdit.setStyleSheet("QLineEdit { background-color: lightblue; color: black; }")
        self.limitEdit.setText('100')
        layout.addWidget(self.limitEdit, 4, 1)

        ## Add offset field
        offsetLabel = QLabel("Offset:")
        layout.addWidget(offsetLabel, 4, 2)
        self.offsetEdit = QLineEdit()
        self.offsetEdit.setStyleSheet("QLineEdit { background-color: lightblue; color: black; }")
        #self.offsetEdit.setText('100')
        layout.addWidget(self.offsetEdit, 4, 3)

        ## Add startdate field
        startDateLabel = QLabel("Start dato:")
        layout.addWidget(startDateLabel, 0, 0)
        self.startDateEdit = QDateEdit(QDate(2024,1,1))
        self.startDateEdit.setStyleSheet("QDateEdit { background-color: lightblue; color: black; }")
        layout.addWidget(self.startDateEdit, 0, 1)
        self.startDateEdit.dateChanged.connect(self.inputChanged)

        ## Add stopdate field
        stopDateLabel = QLabel("Stopp dato:")
        layout.addWidget(stopDateLabel, 0, 2)
        self.stopDateEdit = QDateEdit(QDate(2024,12,31))
        self.stopDateEdit.setStyleSheet("QDateEdit { background-color: lightblue; color: black; }")
        layout.addWidget(self.stopDateEdit, 0, 3)
        self.stopDateEdit.dateChanged.connect(self.inputChanged)

        ## Add vessel group dropdown box
        vesselLabel = QLabel("Lengdegruppe:")
        layout.addWidget(vesselLabel, 1, 0)
        self.vesselCombo = MultiComboBox()
        self.vesselCombo.setStyleSheet("QComboBox { background-color: lightblue; color: black; }")
        self.vesselCombo.add_item("All", checked = False)
        self.vesselCombo.add_items(ep.allVesselGroups,[False,False,False,False,False,True])

        # Gear group
        allGearGroups = ["Unknown", "Seine", "Net", "HookGear", "LobsterTrapAndFykeNets", "Trawl", "DanishSeine",
                         "HarpoonCannon", "OtherGear", "FishFarming"]
        layout.addWidget(self.vesselCombo, 1, 1)
        self.vesselCombo.currentTextChanged.connect(self.inputChanged)

        ## Add gear group field dropdown box
        gearLabel = QLabel("Redskapsgruppe:")
        layout.addWidget(gearLabel, 2, 0)
        self.gearCombo = MultiComboBox()
        self.gearCombo.setStyleSheet("QComboBox { background-color: lightblue; color: black; }")
        self.gearCombo.add_item("All", checked = False)
        self.gearCombo.add_items(ep.allGearGroups,[False,False,False,False,False,True,False,False,False,False])
        layout.addWidget(self.gearCombo, 2, 1)
        self.gearCombo.currentTextChanged.connect(self.inputChanged)

        ## Add species group dropdown box
        speciesLabel = QLabel("Artsgruppe:")
        layout.addWidget(speciesLabel, 3, 0)
        self.speciesCombo = MultiComboBox()
        self.speciesCombo.setStyleSheet("QComboBox { background-color: lightblue; color: black; }")
        self.speciesCombo.add_item("All", checked = True)
        self.speciesCombo.add_items(ep.allSpeciesGroups)
        layout.addWidget(self.speciesCombo, 3, 1)
        self.speciesCombo.currentTextChanged.connect(self.inputChanged)

        ## Add catch locations array
        locationLabel = QLabel("Fangstfelt:")
        layout.addWidget(locationLabel, 3, 2)
        self.locationText = QTextEdit("All")
        self.locationText.setStyleSheet("QTextEdit { background-color: lightblue; color: black; }")
        layout.addWidget(self.locationText, 3, 3)
        self.locationText.textChanged.connect(self.inputChanged)

        ## Add a my boat checkbox (to run query on my boat only foor those endpoints that support this)
        self.myVessel = QCheckBox("Mitt fartøy", self)
        layout.addWidget(self.myVessel, 5, 0)

        ## Add a show checkbox (to output results of the query)
        self.infoOutput = QCheckBox("Vis API respons på skjerm", self)
        layout.addWidget(self.infoOutput, 5, 1)

        ## Add a store csv checkbox (to output results of the query)
        self.storeCsv = QCheckBox("Lagre API-data som CSV", self)
        layout.addWidget(self.storeCsv, 5, 2)

        ## Add a append checkbox to aggregate data in api-csv file
        self.appendCsv = QCheckBox("Legge til data i filen", self)
        layout.addWidget(self.appendCsv, 5, 3)

        ## Add field for aggregated time period (for KPI calculations)
        aggLabel = QLabel("Aggregert tidsperiode [mnd]:")
        layout.addWidget(aggLabel, 1, 2)
        self.aggEdit = QLineEdit()
        self.aggEdit.setStyleSheet("QLineEdit { background-color: lightblue; color: black; }")
        self.aggEdit.setText(str('3'))
        layout.addWidget(self.aggEdit, 1, 3)
        self.aggEdit.textChanged.connect(self.inputChanged)

        ## Add field for number of periods calculated (for KPI calculations)
        resLabel = QLabel("Antall perioder bakover \ni tid fra sluttdato:")
        layout.addWidget(resLabel, 2, 2)
        self.resEdit = QLineEdit()
        self.resEdit.setStyleSheet("QLineEdit { background-color: lightblue; color: black; }")
        self.resEdit.setText(str('4'))
        layout.addWidget(self.resEdit, 2, 3)
        self.resEdit.textChanged.connect(self.inputChanged)
               
        ## Create toolbar
        toolbar = QToolBar("My main toolbar")
        toolbar.setStyleSheet("QToolBar { background-color: black; color: black; }")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)

        ## Create menu items to toolbar
        menu = self.menuBar()
        api_menu = menu.addMenu("Datafangst API")
        auth_menu = menu.addMenu("Innlogging")
        sust_menu = menu.addMenu("Rapporter")
        pef_menu = menu.addMenu("Pef")
        kpi_menu = menu.addMenu("KPI")

        ## Sub menus  to API menu ############
        gear_menu = api_menu.addMenu("Gear")
        vessels_menu = api_menu.addMenu("Vessels")
        user_menu = api_menu.addMenu("User")
        trip_menu = api_menu.addMenu("Trip")
        haul_menu = api_menu.addMenu("Haul")
        price_menu = api_menu.addMenu("Price")

        #### Add button actions to API menu ##############
        # Gear
        getGear_action = QAction(QIcon("AppIcon/bug.png"), "&Get Gear", self)
        getGear_action.triggered.connect(self.getGear_button_clicked)
        gear_menu.addAction(getGear_action)

        getGearGroups_action = QAction(QIcon("AppIcon/bug.png"), "&Get Gear Groups", self)
        getGearGroups_action.triggered.connect(self.getGearGroups_button_clicked)
        gear_menu.addAction(getGearGroups_action)

        getGearMainGroups_action = QAction(QIcon("AppIcon/bug.png"), "&Get Gear Main Groups", self)
        getGearMainGroups_action.triggered.connect(self.getGearMainGroups_button_clicked)
        gear_menu.addAction(getGearMainGroups_action)

        api_menu.addSeparator()

        # Vessels
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

        # User
        getUser_action = QAction(QIcon("AppIcons/user.png"), "&Get User", self)
        getUser_action.triggered.connect(self.getUser_button_clicked)
        user_menu.addAction(getUser_action)

         # Trip
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

        # Haul
        getHaul_action = QAction(QIcon("AppIcons/user.png"), "&Get Hauls", self)
        getHaul_action.triggered.connect(self.getHaul_button_clicked)
        haul_menu.addAction(getHaul_action)

        # Price
        getPrice_action = QAction(QIcon("AppIcons/user.png"), "&Get Price", self)
        getPrice_action.triggered.connect(self.getPrice_button_clicked)
        price_menu.addAction(getPrice_action)

        #### Add button actions to KPI menu ###############
        # Action for KPI-01, EEOI calculations
        kpi_01_action = QAction(QIcon("AppIcons/cross-circle-frame.png"), "&KPI_01 EEIO", self)
        kpi_01_action.triggered.connect(self.kpi01_button_clicked)
        kpi_menu.addAction(kpi_01_action)

        # Action for KPI-02, FUI calculations
        kpi_02_action = QAction(QIcon("AppIcons/cross-circle-frame.png"), "&KPI_02 FUI", self)
        kpi_02_action.triggered.connect(self.kpi02_button_clicked)
        kpi_menu.addAction(kpi_02_action)

        # Action for KPI-03 Netto fortjeneste per tonn
        kpi_03_04_action = QAction(QIcon("AppIcons/cross-circle-frame.png"), "&KPI_03/04 Netto fortjeneste", self)
        kpi_03_04_action.triggered.connect(self.kpi03_04_button_clicked)
        kpi_menu.addAction(kpi_03_04_action)

        # Action for KPI-05 Fangst og fangstverdi per år
        kpi_05_action = QAction(QIcon("AppIcons/cross-circle-frame.png"), "&KPI_05", self)
        kpi_05_action.triggered.connect(self.kpi05_button_clicked)
        kpi_menu.addAction(kpi_05_action)

        ## Add button actions to AUTHORIZATION menu
        auth_action = QAction(QIcon("AppIcons/door-open.png"), "&Authorize", self)
        auth_action.triggered.connect(self.auth_button_clicked)
        auth_menu.addAction(auth_action)

        ## add button actions to SUSTAINABILITY menu
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


        ## Add button actions to PEF menu
        pef_action = QAction(QIcon("AppIcons/star--arrow.png"), "&PEF calc", self)
        pef_action.triggered.connect(self.pef_button_clicked)
        pef_menu.addAction(pef_action)
      
    ###########  Define button-clicked actions ################

    def inputChanged(self):
        self.inputHasChanged = True

    def setInputChanged(self, state):
        self.inputHasChanged = state

    def isInputChanged(self):
        return self.inputHasChanged
    
    def getGear_button_clicked(self):
        toCsvFile = "output/gear.csv" if self.storeCsv.isChecked() else ""
        ep.get_request(ep.gear, info_log=self.infoOutput.isChecked(), csvFile=toCsvFile, appendCSV=self.appendCsv.isChecked())

    def getGearGroups_button_clicked(self):
        toCsvFile = "output/gearGroups.csv" if self.storeCsv.isChecked() else ""
        ep.get_request(ep.gear_groups, info_log=self.infoOutput.isChecked(), csvFile=toCsvFile, appendCSV=self.appendCsv.isChecked())

    def getGearMainGroups_button_clicked(self):
        toCsvFile = "output/gearMainGroups.csv" if self.storeCsv.isChecked() else ""
        ep.get_request(ep.gear_main_groups, info_log=self.infoOutput.isChecked(), csvFile=toCsvFile, appendCSV=self.appendCsv.isChecked())

    def getVessels_button_clicked(self):
        toCsvFile = "output/vessels.csv" if self.storeCsv.isChecked() else ""
        ep.get_request(ep.vessels, info_log=self.infoOutput.isChecked(), csvFile=toCsvFile, appendCSV=self.appendCsv.isChecked())
        #if jsonData: jsonToCsv(jsonData, "csvTest.csv")

    def getVesselsFuel_button_clicked(self):
        toCsvFile = "output/vesselsFuel.csv" if self.storeCsv.isChecked() else ""
        ep.get_request(ep.fuel, self.startDateEdit.date(), self.stopDateEdit.date(), info_log=self.infoOutput.isChecked(), csvFile=toCsvFile, appendCSV=self.appendCsv.isChecked())

    def getVesselsLiveFuel_button_clicked(self):
        toCsvFile = "output/vesselsLiveFuel.csv" if self.storeCsv.isChecked() else ""
        ep.get_request(ep.live_fuel, info_log=self.infoOutput.isChecked(), csvFile=toCsvFile, appendCSV=self.appendCsv.isChecked())

    def getVesselsBenchmarks_button_clicked(self):
        toCsvFile = "output/benchmarks.csv" if self.storeCsv.isChecked() else ""
        ep.get_request(ep.vessel_benchmarks, info_log=self.infoOutput.isChecked(), csvFile=toCsvFile, appendCSV=self.appendCsv.isChecked())

    def getUser_button_clicked(self):
        toCsvFile = "output/user.csv" if self.storeCsv.isChecked() else ""
        ep.get_request(ep.user, info_log=self.infoOutput.isChecked(), csvFile=toCsvFile, appendCSV=self.appendCsv.isChecked())

    def getTrips_button_clicked(self):
        toCsvFile = "output/trips.csv" if self.storeCsv.isChecked() else ""
        ep.get_request(ep.trips,
                       self.startDateEdit.date(),
                       self.stopDateEdit.date(),
                       limit=self.limitEdit.text(),
                       gearG=self.gearCombo.checked_items_data(),
                       lengthG=self.vesselCombo.checked_items_data(),
                       specG=self.speciesCombo.checked_items_data(),
                       myVessel=self.myVessel.isChecked(),
                       info_log=self.infoOutput.isChecked(),
                       csvFile=toCsvFile,
                       appendCSV=self.appendCsv.isChecked())

    def getAvTripBenchmarks_button_clicked(self):
        toCsvFile = "output/avTripBenchmarks.csv" if self.storeCsv.isChecked() else ""
        ep.get_request(ep.avTripBench,
                       self.startDateEdit.date(),
                       self.stopDateEdit.date(),
                       gearG=self.gearCombo.checked_items_data(),
                       lengthG=self.vesselCombo.checked_items_data(),
                       myVessel=self.myVessel.isChecked(),
                       info_log=self.infoOutput.isChecked(),
                       csvFile=toCsvFile,
                       appendCSV=self.appendCsv.isChecked())

    def getEEOI_button_clicked(self):
        toCsvFile = "output/EEOI.csv" if self.storeCsv.isChecked() else ""
        ep.get_request(ep.eeoi,
                       self.startDateEdit.date(),
                       self.stopDateEdit.date(),
                       gearG=self.gearCombo.checked_items_data(),
                       lengthG=self.vesselCombo.checked_items_data(),
                       specG=self.speciesCombo.checked_items_data(),
                       locationG=splitCatchLocation(self.locationText.toPlainText()),
                       limit=self.limitEdit.text(),
                       offset=self.offsetEdit.text(),
                       myVessel=self.myVessel.isChecked(),
                       info_log=self.infoOutput.isChecked(),
                       csvFile=toCsvFile,
                       appendCSV=self.appendCsv.isChecked())

    def getAvEEOI_button_clicked(self):
        toCsvFile = "output/avEEOI.csv" if self.storeCsv.isChecked() else ""
        ep.get_request(ep.av_eeoi,
                       self.startDateEdit.date(),
                       self.stopDateEdit.date(),
                       gearG=self.gearCombo.checked_items_data(),
                       lengthG=self.vesselCombo.checked_items_data(),
                       specG=self.speciesCombo.checked_items_data(),
                       locationG=splitCatchLocation(self.locationText.toPlainText()),
                       limit=self.limitEdit.text(),
                       offset=self.offsetEdit.text(),
                       myVessel=self.myVessel.isChecked(),
                       info_log=self.infoOutput.isChecked(),
                       csvFile=toCsvFile,
                       appendCSV=self.appendCsv.isChecked())

    def getHaul_button_clicked(self):
        toCsvFile = "output/haul.csv" if self.storeCsv.isChecked() else ""
        ep.get_request(ep.haul,
                       self.startDateEdit.date(),
                       self.stopDateEdit.date(),
                       lengthG=self.vesselCombo.checked_items_data(),
                       gearG=self.gearCombo.checked_items_data(),
                       specG=self.speciesCombo.checked_items_data(),
                       locationG=splitCatchLocation(self.locationText.toPlainText()),
                       limit=self.limitEdit.text(),
                       offset=self.offsetEdit.text(),
                       myVessel=self.myVessel.isChecked(),
                       info_log=self.infoOutput.isChecked(),
                       csvFile=toCsvFile,
                       appendCSV=self.appendCsv.isChecked())

    def getPrice_button_clicked(self):
        toCsvFile = "output/price.csv" if self.storeCsv.isChecked() else ""
        itemDict = ep.get_ssb_request(ep.price, 
                        self.startDateEdit.date(),
                        self.stopDateEdit.date(),
                        info_log=self.infoOutput.isChecked(), 
                        csvFile=toCsvFile, 
                        appendCSV=self.appendCsv.isChecked())
        
        print(itemDict['value'])
    
    def auth_button_clicked(self):
        # Not implemented
        ep.get_access_token()

    def reder_button_clicked(self):
        # Not implemented
        self.actionText = ep.trips     #just dummy cmd

    def skipper_button_clicked(self):
        # Not implemented
        self.actionText = ep.trips     #just dummy cmd

    def bank_button_clicked(self):
        toCsvFile = "output/bank-Report.csv" if self.storeCsv.isChecked() else ""
        ## get start and stop dates
        # Create item holding input parameters from gui
        gui_data = r.Output('Gadus  Njord', 
                self.vesselCombo.checked_items_data(), 
                self.gearCombo.checked_items_data(), 
                self.speciesCombo.checked_items_data(),
                splitCatchLocation(self.locationText.toPlainText()), 
                int(self.aggEdit.text()), 
                int(self.resEdit.text()))
        
        # Calculate dates for all periodes, and all kpi's required
        getDatesArray(self.stopDateEdit.date(), gui_data)             
        kpi_01(gui_data)
        kpi_02(gui_data)
        kpi_05(gui_data)

         # Find total number of vessels in in group
        if (self.isInputChanged()):
            startDateList = gui_data.datesArray[0]
            endDateList = gui_data.datesArray[1]
            entries = len(endDateList)
            self.nVessels = getTotalVessels(ep.trips, startDateList[0], endDateList[entries-1], gui_data.lengthG, gui_data.gearG, gui_data.specG, gui_data.locG)
            self.setInputChanged(False)
            print ("Antall båter. ", self.nVessels)

        gui_data.nVessels = self.nVessels
        # create json fiole
        jsonArray = []
        data = gui_data.createJsonItem()
        jsonArray.append(data)
        r.createJson(jsonArray, 'jsonTestFile.json')
        if (toCsvFile != ""):
            ep.json_to_pandas_csv(jsonArray, toCsvFile)  
         

    def supplier_button_clicked(self):
        # Not implemented
        self.actionText = ep.trips     #just dummy cmd

    def pef_button_clicked(self):
        # Not implemented
        self.actionText = ep.trips     #just dummy cmd
       
        
    def kpi01_button_clicked(self):
        # Produce graphics and output for EEOI
        toCsvFile = "output/kpi_01-Report.csv" if self.storeCsv.isChecked() else ""
        toJsonFile = "output/kpi_01-Report.json"
        # Create item holding input parameters from gui
        gui_data = r.Output('Gadus  Njord', 
                self.vesselCombo.checked_items_data(), 
                self.gearCombo.checked_items_data(), 
                self.speciesCombo.checked_items_data(),
                splitCatchLocation(self.locationText.toPlainText()), 
                int(self.aggEdit.text()), 
                int(self.resEdit.text()))
        
        # Calculate dates for all periodes 
        getDatesArray(self.stopDateEdit.date(), gui_data) 
        
        # Calculate KPI-01
        kpi_01(gui_data)  

        # Find total number of vessels in in group
        if (self.isInputChanged()):
            startDateList = gui_data.datesArray[0]
            endDateList = gui_data.datesArray[1]
            entries = len(endDateList)
            self.nVessels = getTotalVessels(ep.trips, startDateList[0], endDateList[entries-1], gui_data.lengthG, gui_data.gearG, gui_data.specG, gui_data.locG)
            self.setInputChanged(False)
            print ("Antall båter. ", self.nVessels)
        
        gui_data.nVessels = self.nVessels
        # create plot
        r.createPlot(gui_data, 'KPI-01: EEOI [g CO2 /(fangst*nm)]')

        # Create JSON and CSV files for these data        
        if (toCsvFile != ""):
            jsonArray = []
            data = gui_data.createJsonItem()
            jsonArray.append(data)
            r.createJson(jsonArray, toJsonFile)
            ep.json_to_pandas_csv(jsonArray, toCsvFile)  


    def kpi02_button_clicked(self):
        # Produce graphics and output for FUI
        toCsvFile = "output/kpi-02-Report.csv" if self.storeCsv.isChecked() else ""
        # Create item holding input parameters from gui
        gui_data = r.Output('Gadus  Njord', 
                self.vesselCombo.checked_items_data(), 
                self.gearCombo.checked_items_data(), 
                self.speciesCombo.checked_items_data(),
                splitCatchLocation(self.locationText.toPlainText()), 
                int(self.aggEdit.text()), 
                int(self.resEdit.text()))
        
        # Calculate dates for all periodes 
        getDatesArray(self.stopDateEdit.date(), gui_data) 

        # Calculate KPI-02
        kpi_02(gui_data) 

        # Find total number of vessels in in group
        if (self.isInputChanged()):
            startDateList = gui_data.datesArray[0]
            endDateList = gui_data.datesArray[1]
            entries = len(endDateList)
            self.nVessels = getTotalVessels(ep.trips, startDateList[0], endDateList[entries-1], gui_data.lengthG, gui_data.gearG, gui_data.specG, gui_data.locG)
            self.setInputChanged(False)
            print ("Antall båter. ", self.nVessels)
        
        gui_data.nVessels = self.nVessels
        # create plot
        r.createPlot(gui_data, 'KPI-02: FUI [g CO2 /fangst]')

        # create json file
        jsonArray = []
        data = gui_data.createJsonItem()
        jsonArray.append(data)
        r.createJson(jsonArray, 'jsonTestFile.json')

        if (toCsvFile != ""):
            ep.json_to_pandas_csv(jsonArray, toCsvFile)  

    def kpi03_04_button_clicked(self):
        # Produce graphics and output for catch value per ton catch and fuel costs
        toCsvFile = "output/kpi-03_04-Report.csv" if self.storeCsv.isChecked() else ""
        # Create item holding input parameters from gui
        gui_data = r.Output('Gadus  Njord', 
                self.vesselCombo.checked_items_data(), 
                self.gearCombo.checked_items_data(), 
                self.speciesCombo.checked_items_data(),
                splitCatchLocation(self.locationText.toPlainText()), 
                int(self.aggEdit.text()), 
                int(self.resEdit.text()))
        
        # Calculate dates for all periodes 
        getDatesArray(self.stopDateEdit.date(), gui_data) 

        # Calculate KPI-03
        kpi_03_04(gui_data) 

        # Find total number of vessels in in group
        if (self.isInputChanged()):
            startDateList = gui_data.datesArray[0]
            endDateList = gui_data.datesArray[1]
            entries = len(endDateList)
            self.nVessels = getTotalVessels(ep.trips, startDateList[0], endDateList[entries-1], gui_data.lengthG, gui_data.gearG, gui_data.specG, gui_data.locG)
            self.setInputChanged(False)
            print ("Antall båter. ", self.nVessels)
        
        gui_data.nVessels = self.nVessels
        # create plot
        r.createPlot(gui_data, 'KPI-03/04 netto fortjeneste:')

        # create json file
        jsonArray = []
        data = gui_data.createJsonItem()
        jsonArray.append(data)
        r.createJson(jsonArray, 'jsonTestFile.json')

        if (toCsvFile != ""):
            ep.json_to_pandas_csv(jsonArray, toCsvFile)  


    def kpi05_button_clicked(self):
        # Produce graphics and output for catch and catch value per yesr
        toCsvFile = "output/kpi-05-Report.csv" if self.storeCsv.isChecked() else ""
        # Create item holding input parameters from gui
        gui_data = r.Output('Gadus  Njord', 
                self.vesselCombo.checked_items_data(), 
                self.gearCombo.checked_items_data(), 
                self.speciesCombo.checked_items_data(),
                splitCatchLocation(self.locationText.toPlainText()), 
                int(self.aggEdit.text()), 
                int(self.resEdit.text()))
        
        # Calculate dates for all periodes 
        getDatesArray(self.stopDateEdit.date(), gui_data) 

        # Calculate KPI-05
        kpi_05(gui_data) 

        # Find total number of vessels in in group
        if (self.isInputChanged()):
            startDateList = gui_data.datesArray[0]
            endDateList = gui_data.datesArray[1]
            entries = len(endDateList)
            self.nVessels = getTotalVessels(ep.trips, startDateList[0], endDateList[entries-1], gui_data.lengthG, gui_data.gearG, gui_data.specG, gui_data.locG)
            self.setInputChanged(False)
            print ("Antall båter. ", self.nVessels)
        
        gui_data.nVessels = self.nVessels
        # create plot
        r.createPlot(gui_data, 'KPI-05:')

        # create json file
        jsonArray = []
        data = gui_data.createJsonItem()
        jsonArray.append(data)
        r.createJson(jsonArray, 'jsonTestFile.json')

        if (toCsvFile != ""):
            ep.json_to_pandas_csv(jsonArray, toCsvFile)  

    def closeEvent(self, event):
        # do stuff
        self.close()   

