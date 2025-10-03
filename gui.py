from PySide6.QtWidgets import QMainWindow, QPushButton, QToolBar, QLabel, QCheckBox, QStatusBar, QCheckBox, QGridLayout, QWidget, QDateEdit, QLineEdit, QComboBox, QSlider, QTextEdit, QStyledItemDelegate
from PySide6.QtGui import QAction, QIcon, QStandardItem, QStandardItemModel, QFontMetrics
from PySide6.QtCore import*
import api_requests as ep
import copy
from utility import*
from reports import*
from KPI import*


# CheckableQCombobox with multiple choices
"""
    Multiple choice ComboBox with checked items display
    based on:
    https://gis.stackexchange.com/questions/350148/qcombobox-multiple-selection-pyqt5
"""
class MultiComboBox(QComboBox):
    class Delegate(QStyledItemDelegate):
        # Subclass Delegate to increase item line spacing
        def sizeHint(self, option, index):
            size = super().sizeHint(option, index)
            size.setHeight(max(20, size.height()))
            return size

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make the combo editable to set a custom text, but readonly
        self.setEditable(True)      # needed to create LineEdit
        self.lineEdit().setReadOnly(True)

        # Catch exit via RETURN key to ensure proper text display
        self.lineEdit().returnPressed.connect(self.update_text)

        # Allow clicks on item's text to perform toggle
        self.view().pressed.connect(self.handle_item_press)

        # Use custom delegate for sizing
        self.setItemDelegate(MultiComboBox.Delegate())

        # Update the text when an item is toggled
        self.model().dataChanged.connect(self.update_text)

    def resizeEvent(self, e):
        # Recompute text to elide *after* resizing so updated width is used
        super().resizeEvent(e)
        self.update_text()

    def get_model(self) -> QStandardItemModel:
        # Perform "cast" on QAbstractItemModel to what QComboBox instantiates
        # to avoid linter complaints about it not being a QStandardItemModel
        model = self.model()
        if isinstance(model, QStandardItemModel):
            return model
        else:
            raise ValueError(f'model is {type(model)}?')

    def handle_item_press(self, index: QModelIndex):
        # Toggle checkbox of clicked on item; triggers dataChanged which updates the text
        item = self.get_model().itemFromIndex(index)
        if item.checkState == Qt.CheckState.Checked:
            item.setCheckState(Qt.CheckState.Unchecked)
        else:
            item.setCheckState(Qt.CheckState.Checked)

    def update_text(self):
        texts = []
        model = self.get_model()
        for i in range(model.rowCount()):
            if model.item(i).checkState() == Qt.CheckState.Checked:
                texts.append(model.item(i).text())
        text = ", ".join(texts)

        # Compute elided text (with "...")
        metrics = QFontMetrics(self.lineEdit().font())
        elided_text = metrics.elidedText(text, Qt.TextElideMode.ElideRight, self.lineEdit().width())
        self.lineEdit().setText(elided_text)
        # print('update_text:', elided_text)

    def add_item(self, text, checked=False, data=None):
        # Add a new "choice" with optional initial check state and data value
        item = QStandardItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        item.setData(data if data is not None else text)
        self.get_model().appendRow(item)

    def add_items(self, texts, checklist=None, datalist=None):
        # Add a list of new "choices" with optional initial states and data values
        for i, text in enumerate(texts):
            checked = False if not checklist else checklist[i]
            data = None if not datalist else datalist[i]
            self.add_item(text, checked, data)

    def checked_items_data(self):
        # Return a list of the checked items' data values (defaulted to item's text)
        items = []
        model = self.get_model()
        for i in range(model.rowCount()):
            item = model.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                items.append(item.data())
        return items

    def checked_items_text(self):
        # Return a list of tuple(text, data) for checked items
        tds = []
        model = self.get_model()
        for i in range(model.rowCount()):
            item = model.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                tds.append((item.text(), item.data()))
        return tds
#--------

class MainWindow(QMainWindow):
    def __init__(self):
        
        super().__init__()
       
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
        self.startDateEdit = QDateEdit(QDate.currentDate())
        self.startDateEdit.setStyleSheet("QDateEdit { background-color: lightblue; color: black; }")
        layout.addWidget(self.startDateEdit, 0, 1)

        ## Add stopdate field
        stopDateLabel = QLabel("Stopp dato:")
        layout.addWidget(stopDateLabel, 0, 2)
        self.stopDateEdit = QDateEdit(QDate.currentDate())
        self.stopDateEdit.setStyleSheet("QDateEdit { background-color: lightblue; color: black; }")
        layout.addWidget(self.stopDateEdit, 0, 3)

        ## Add vessel group dropdown box
        vesselLabel = QLabel("Lengdegruppe:")
        layout.addWidget(vesselLabel, 1, 0)
        self.vesselCombo = MultiComboBox()
        self.vesselCombo.setStyleSheet("QComboBox { background-color: lightblue; color: black; }")
        self.vesselCombo.add_item("All")
        self.vesselCombo.add_items(ep.allVesselGroups)
        layout.addWidget(self.vesselCombo, 1, 1)

        ## Add gear group field dropdown box
        gearLabel = QLabel("Redskapsgruppe:")
        layout.addWidget(gearLabel, 2, 0)
        self.gearCombo = MultiComboBox()
        self.gearCombo.setStyleSheet("QComboBox { background-color: lightblue; color: black; }")
        self.gearCombo.add_item("All")
        self.gearCombo.add_items(ep.allGearGroups)
        layout.addWidget(self.gearCombo, 2, 1)

        ## Add species group dropdown box
        speciesLabel = QLabel("Artsgruppe:")
        layout.addWidget(speciesLabel, 3, 0)
        self.speciesCombo = MultiComboBox()
        self.speciesCombo.setStyleSheet("QComboBox { background-color: lightblue; color: black; }")
        self.speciesCombo.add_item("All")
        self.speciesCombo.add_items(ep.allSpeciesGroups)
        layout.addWidget(self.speciesCombo, 3, 1)

        ## Add catch locations array
        locationLabel = QLabel("Fangstfelt:")
        layout.addWidget(locationLabel, 3, 2)
        self.locationText = QTextEdit("All")
        self.locationText.setStyleSheet("QTextEdit { background-color: lightblue; color: black; }")
        layout.addWidget(self.locationText, 3, 3)

        ## Add a my boat checkbox (to run query on my boat only foor those endpoints that support this)
        self.myVessel = QCheckBox("Mitt fartøy", self)
        layout.addWidget(self.myVessel, 5, 1)

        ## Add a show checkbox (to output results of the query)
        self.showOutput = QCheckBox("Vis resultat", self)
        layout.addWidget(self.showOutput, 5, 2)

        ## Add a scsv checkbox (to output results of the query)
        self.storeCsv = QCheckBox("Lagre API-respons som CSV", self)
        layout.addWidget(self.storeCsv, 5, 3)

        ## Add field for aggregated time period (for KPI calculations)
        aggLabel = QLabel("Aggregert tidsperiode [mnd]:")
        layout.addWidget(aggLabel, 1, 2)
        self.aggEdit = QLineEdit()
        self.aggEdit.setStyleSheet("QLineEdit { background-color: lightblue; color: black; }")
        self.aggEdit.setText(str('1'))
        layout.addWidget(self.aggEdit, 1, 3)

        ## Add field for number of periods calculated (for KPI calculations)
        resLabel = QLabel("Antall perioder bakover \ni tid fra sluttdato:")
        layout.addWidget(resLabel, 2, 2)
        self.resEdit = QLineEdit()
        self.resEdit.setStyleSheet("QLineEdit { background-color: lightblue; color: black; }")
        self.resEdit.setText(str('1'))
        layout.addWidget(self.resEdit, 2, 3)
               
        ## Create toolbar
        toolbar = QToolBar("My main toolbar")
        toolbar.setStyleSheet("QToolBar { background-color: black; color: black; }")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)

        ## Create menu items to toolbar
        menu = self.menuBar()
        api_menu = menu.addMenu("&Datafangst API")
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

        #### Add button actions to KPI menu ###############
        # Action for KPI-01, EEOI calculations
        kpi_01_action = QAction(QIcon("AppIcons/cross-circle-frame.png"), "&KPI_01 EEIO", self)
        kpi_01_action.triggered.connect(self.kpi01_button_clicked)
        kpi_menu.addAction(kpi_01_action)

        # Action for KPI-02, FUI calculations
        kpi_02_action = QAction(QIcon("AppIcons/cross-circle-frame.png"), "&KPI_02 FUI", self)
        kpi_02_action.triggered.connect(self.kpi02_button_clicked)
        kpi_menu.addAction(kpi_02_action)

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
    
    def getGear_button_clicked(self):
        toCsvFile = "output/gear.csv" if self.storeCsv.isChecked() else ""
        ep.get_request(ep.gear, show = self.showOutput.isChecked(), csvFile = toCsvFile)

    def getGearGroups_button_clicked(self):
        toCsvFile = "output/gearGroups.csv" if self.storeCsv.isChecked() else ""
        ep.get_request(ep.gear_groups, show = self.showOutput.isChecked(), csvFile = toCsvFile)

    def getGearMainGroups_button_clicked(self):
        toCsvFile = "output/gearMainGroups.csv" if self.storeCsv.isChecked() else ""
        ep.get_request(ep.gear_main_groups, show = self.showOutput.isChecked(), csvFile = toCsvFile)

    def getVessels_button_clicked(self):
        toCsvFile = "output/vessels.csv" if self.storeCsv.isChecked() else ""
        ep.get_request(ep.vessels, show = self.showOutput.isChecked(), csvFile = toCsvFile)
        #if jsonData: jsonToCsv(jsonData, "csvTest.csv")

    def getVesselsFuel_button_clicked(self):
        toCsvFile = "output/vesselsFuel.csv" if self.storeCsv.isChecked() else ""
        ep.get_request(ep.fuel, self.startDateEdit.date(), self.stopDateEdit.date(), show = self.showOutput.isChecked(), csvFile = toCsvFile)

    def getVesselsLiveFuel_button_clicked(self):
        toCsvFile = "output/vesselsLiveFuel.csv" if self.storeCsv.isChecked() else ""
        ep.get_request(ep.live_fuel, show = self.showOutput.isChecked(), csvFile = toCsvFile)

    def getVesselsBenchmarks_button_clicked(self):
        toCsvFile = "output/benchmarks.csv" if self.storeCsv.isChecked() else ""
        ep.get_request(ep.vessel_benchmarks, show = self.showOutput.isChecked(), csvFile = toCsvFile)

    def getUser_button_clicked(self):
        toCsvFile = "output/user.csv" if self.storeCsv.isChecked() else ""
        ep.get_request(ep.user, show = self.showOutput.isChecked(), csvFile = toCsvFile)

    def getTrips_button_clicked(self):
        toCsvFile = "output/trips.csv" if self.storeCsv.isChecked() else ""
        ep.get_request(ep.trips,
                       self.startDateEdit.date(),
                       self.stopDateEdit.date(),
                       limit = self.limitEdit.text(),
                       gearG = self.gearCombo.checked_items_data(),
                       lengthG = self.vesselCombo.checked_items_data(),
                       specG = self.speciesCombo.checked_items_data(),
                       myVessel = self.myVessel.isChecked(),
                       show = self.showOutput.isChecked(),
                       csvFile = toCsvFile)

    def getAvTripBenchmarks_button_clicked(self):
        toCsvFile = "output/avTripBenchmarks.csv" if self.storeCsv.isChecked() else ""
        ep.get_request(ep.avTripBench,
                       self.startDateEdit.date(),
                       self.stopDateEdit.date(),
                       gearG = self.gearCombo.checked_items_data(),
                       lengthG = self.vesselCombo.checked_items_data(),
                       myVessel = self.myVessel.isChecked(),
                       show = self.showOutput.isChecked(),
                       csvFile = toCsvFile)

    def getEEOI_button_clicked(self):
        toCsvFile = "output/EEOI.csv" if self.storeCsv.isChecked() else ""
        ep.get_request(ep.eeoi, self.startDateEdit.date(), self.stopDateEdit.date(), show = self.showOutput.isChecked(), csvFile = toCsvFile)

    def getAvEEOI_button_clicked(self):
        toCsvFile = "output/avEEOI.csv" if self.storeCsv.isChecked() else ""
        ep.get_request(ep.av_eeoi,
                       self.startDateEdit.date(),
                       self.stopDateEdit.date(),
                       gearG = self.gearCombo.checked_items_data(),
                       lengthG = self.vesselCombo.checked_items_data(),
                       specG = self.speciesCombo.checked_items_data(),
                       myVessel = self.myVessel.isChecked(),
                       show = self.showOutput.isChecked(),
                       csvFile = toCsvFile)

    def getHaul_button_clicked(self):
        locStr = self.locationText.toPlainText().split('\n')
        toCsvFile = "output/haul.csv" if self.storeCsv.isChecked() else ""
        ep.get_request(ep.haul,
                       self.startDateEdit.date(),
                       self.stopDateEdit.date(),
                       lengthG = self.vesselCombo.checked_items_data(),
                       gearG = self.gearCombo.checked_items_data(),
                       specG = self.speciesCombo.checked_items_data(),
                       locationG = locStr,
                       limit = self.limitEdit.text(),
                       offset = self.offsetEdit.text(),
                       myVessel = self.myVessel.isChecked(),
                       show = self.showOutput.isChecked(),
                       csvFile = toCsvFile)

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
        ## get start and stop dates
        createBankReport(self.stopDateEdit.date(),
                         self.vesselCombo.checked_items_data(),
                         self.gearCombo.checked_items_data(),
                         self.speciesCombo.checked_items_data(),
                         int(self.aggEdit.text()),
                         int(self.resEdit.text()))
         

    def supplier_button_clicked(self):
        # Not implemented
        self.actionText = ep.trips     #just dummy cmd

    def pef_button_clicked(self):
        # Not implemented
        self.actionText = ep.trips     #just dummy cmd
       
        
    def kpi01_button_clicked(self):
        # Produce graphics and output for EEOI
        dateArray = getDatesArray(self.stopDateEdit.date(), int(self.aggEdit.text()), int(self.resEdit.text()))
        print (dateArray)
        kpi_01(self.vesselCombo.checked_items_data(),
               self.gearCombo.checked_items_data(),
               self.speciesCombo.checked_items_data(),
               dateArray)

    def kpi02_button_clicked(self):
        # Produce graphics and output for FUI
        print()
       # kpi_02(self.stopDateEdit.date(), self.vesselCombo.currentText(), self.gearCombo.currentText(), self.speciesCombo.currentText(), int(self.aggEdit.text()), int(self.resEdit.text()))


    def kpi05_button_clicked(self):
        # Produce graphics and output for annual Catch and catch value 
        print()
       # kpi_05(self.stopDateEdit.date(), self.vesselCombo.currentText(), self.gearCombo.currentText(), self.speciesCombo.currentText(), int(self.aggEdit.text()), int(self.resEdit.text()))


    def closeEvent(self, event):
        # do stuff
        self.close()   
        

    