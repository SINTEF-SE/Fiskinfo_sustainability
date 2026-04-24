

from PySide6.QtCore import QObject, Signal
from utility import getPeriodDates
from KPI import getAllTripsInPeriods, getPricesInPeriod, kpiCalculations
import Endpoints as ep

class KPIWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)
    progress = Signal(str)

    def __init__(self, kpiData):
        super().__init__()
        self.kpiData = kpiData

    def run(self):
        try:
            self.progress.emit("Beregner perioder …")
            periodArray = getPeriodDates(self.kpiData)

            self.progress.emit("Henter turer …")
            nVessels, tripsArray = getAllTripsInPeriods(
                ep.E_TRIPS, self.kpiData, periodArray
            )

            self.progress.emit("Henter priser …")
            priceList = getPricesInPeriod(periodArray)

            self.progress.emit("Beregner KPI-er …")
            kpi_results = kpiCalculations(
                self.kpiData, tripsArray, priceList
            )

            self.finished.emit({
                "periods": periodArray,
                "kpi": kpi_results,
                "nVessels": nVessels
            })
        except Exception as e:
            self.error.emit(str(e))
