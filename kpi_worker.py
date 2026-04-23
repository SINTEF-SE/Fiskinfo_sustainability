

from PySide6.QtCore import QObject, Signal
from utility import getPeriodDates
from KPI import getAllTripsInPeriods, getPricesInPeriod, kpiCalculations

class KPIWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)
    progress = Signal(str)

    def __init__(self, kpiData):
        super().__init__()
        self.kpiData = kpiData
        self.E_TRIPS = "v1.0/trips"

    def run(self):
        try:
            self.progress.emit("Beregner perioder …")
            periodArray = getPeriodDates(self.kpiData)

            self.progress.emit("Henter turer …")
            nVessels, tripsArray = getAllTripsInPeriods(
                self.E_TRIPS, self.kpiData, periodArray
            )

            self.progress.emit("Henter priser …")
            priceList = getPricesInPeriod(periodArray)

            self.progress.emit("Beregner KPI-er …")
            kpi_results = kpiCalculations(
                self.kpiData, tripsArray, priceList
            )

            self.finished.emit({
                "periods": periodArray,
                #"trips": tripsArray,
                #"prices": priceList,
                "kpi": kpi_results,
                "nVessels": nVessels
            })
        except Exception as e:
            self.error.emit(str(e))
