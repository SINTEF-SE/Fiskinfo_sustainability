
# kpi_module.py
from typing import List, Optional, Any, Dict, Mapping, MutableMapping, Iterable, Tuple
import json
from collections import Counter
import re
import datetime

from PySide6.QtCore import QDate
from datafangst_client import DatafangstClient

# Only import what you need from utility to avoid namespace clashes
from utility import nlg, monthsBetweenQdates, plot, noVessels, findMainSpecie, getDatesArray

PRICE_DIFF = 5  # NOK: approx difference between autodiesel and MGO

# --- Datafangst endpoints (same as your previous constants) ---
E_AV_EEOI   = "v1.0/trip/benchmarks/average_eeoi"
E_AV_FUI    = "v1.0/trip/benchmarks/average_fui"
E_AVERAGE   = "v1.0/trip/benchmarks/average"
E_TRIPS     = "v1.0/trips"

# --- SSB PXWeb endpoint base (fixed &amp; -> &) ---
SSB_PRICE_BASE = (
    "https://data.ssb.no/api/pxwebapi/v2/tables/09654/data"
    "?lang=no&valueCodes[PetroleumProd]=035&valueCodes[ContentsCode]=Priser&valueCodes[Tid]="
)

CO2_FACTOR = 2.66           # kg CO2 / liter drivstoff

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _new_client() -> DatafangstClient:
    """Create a fresh API client (reads token from env if not passed)."""
    return DatafangstClient()

def _norsk_length_group(lengthG: List[str]) -> str:
    """Format Norwegian vessel length group label."""
    return f"[{', '.join(nlg(lg) for lg in lengthG) if lengthG else 'Alle'}]"

def _safe_get(d: Dict[str, Any], key: str, default: float = 0.0) -> float:
    """Get numeric key safely from dict, coercing to float."""
    try:
        return float(d.get(key, default))
    except Exception:
        return default
    
def _safe_get_string(d: Dict[str, Any], key: str, default: str = '') -> str:
    """Get numeric key safely from dict, coercing to float."""
    try:
        return str(d.get(key, default))
    except Exception:
        return default
    
def _safe_get_dict(d: Mapping[str, Any], key: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    fallback: Dict[str, Any] = dict(default) if isinstance(default, dict) else {}
    """Get dictionary safely from dict, coercing to dict."""
    
    try:
        value = d.get(key, None)
        if value is None:
            return fallback

        # Fast path for mappings
        if isinstance(value, (dict, Mapping, MutableMapping)):
            return dict(value)

        # JSON object in a string
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict):
                    return parsed
                else:
                    return fallback
            except Exception:
                return fallback

        # Iterable of pairs (e.g., [("a", 1), ("b", 2)])
        if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
            try:
                return dict(value)  # will raise if not convertible
            except Exception:
                return fallback

        # Anything else is not acceptable
        return fallback
    except Exception:
        return fallback


def _safe_div(n: float, d: float, fallback: float = 0.0) -> float:
    """Safe division with fallback when denominator is 0/None."""
    return (n / d) if d else fallback

def _ssb_price_url(start: QDate, end: QDate) -> str:
    """Build SSB URL with the [range(YYYYMmm,YYYYMmm)] time selector."""
    sY, sM = start.year(), start.month()
    eY, eM = end.year(), end.month()
    return SSB_PRICE_BASE + f"[range({sY}M{sM:02d},{eY}M{eM:02d})]"

# ---------------------------------------------------------------------
# KPI-01: EEOI
# ---------------------------------------------------------------------
'''
def kpi_01(gd: List[Dict[str, Any]], periodArray: List[Dict[str, Any]], nVessels: int) -> List[Dict[str, Any]]: 
    """
        Calculates EEOI (Energy Efficiency Operational Indicator) for each
        time period in periodArray.

        For every (startDate, endDate) tuple:
        - Retrieves EEOI for the main vessel (gd.vesselId)
        - Retrieves average EEOI for the reference vessels (gd.vesselRefIds)

        Values are returned in grams CO2 per (catch * nautical mile),
        scaled from kg to grams (×1000).

        Returns a dictionary containing:
        - myEeoiArray: EEOI values for the main vessel
        - avEeoiArray: Average EEOI values for the reference group
        """

    client = _new_client()

    # JSON keys
    myEeoiArray = ['EEOI']
    avEeoiArray = ['avEEOI']

    for dateTuple in periodArray:
        my_val = client.get(
            E_AV_EEOI,
            sDate=dateTuple[0], eDate=dateTuple[1],
            vesselGroups=gd.lengthG, gearGroups=gd.gearG,
            speciesGroups=gd.specG, locationGroups=gd.locG,
            vesselId = gd.vesselId,
        )
        av_val = client.get(
            E_AV_EEOI,
            sDate=dateTuple[0], eDate=dateTuple[1],
            vesselGroups=gd.lengthG, gearGroups=gd.gearG,
            speciesGroups=gd.specG, locationGroups=gd.locG,
            vesselId=gd.vesselRefIds,  # reference group
        )

        # endpoints return float; coerce and scale to grams
        myEeoiArray.append(1000.0 * float(my_val or 0))
        avEeoiArray.append(1000.0 * float(av_val or 0))

    resultArray = {"myEeoiArray": myEeoiArray}
    resultArray.update({"avEeoiArray": avEeoiArray})

    return resultArray'''


def kpi_01(gd: List[Dict[str, Any]], tripsArray: List[Dict[str, Any]]) -> List[Dict[str, Any]]: 
    """
        Calculates EEOI (Energy Efficiency Operational Indicator) for each
        time period in periodArray.

        For every (startDate, endDate) tuple:
        - Retrieves EEOI for the main vessel (gd.vesselId)
        - Retrieves average EEOI for the reference vessels (gd.vesselRefIds)

        Values are returned in grams CO2 per (catch * nautical mile),
        scaled from kg to grams (×1000).

        Returns a dictionary containing:
        - myEeoiArray: EEOI values for the main vessel
        - avEeoiArray: Average EEOI values for the reference group
        """

    # JSON keys
    myEeoiList = ['EEOI']
    refEeoiList = ['refEEOI']
    myFuiList = ['FUI']
    refFuiList = ['refFUI']
    
    for trip in tripsArray:
        sumFuel = 0
        sumWeightXdistance = 0
        sumWeight = 0
        sumRefFuel = 0
        sumRefWeightXdistance = 0
        sumRefWeight = 0
        
        myTrip = trip[0]    
        for tur in myTrip:
            delivery = _safe_get_dict(tur, 'delivery')
            tripFuel = _safe_get(tur, 'fuelConsumption') 
            sumFuel += tripFuel                                        # Aggregate over all tours
            tripWeight = _safe_get(delivery, 'totalLivingWeight')
            sumWeight += tripWeight                                    # Aggregate over all tours
            tripDistance = _safe_get(tur, 'distance')
            sumWeightXdistance += tripWeight/1000*tripDistance/1852     # Aggregate over all tours
                
        eeoi = sumFuel*CO2_FACTOR/sumWeightXdistance*1000               #(kg CO2 / (ton*nm) → g CO2 / (ton*nm))
        fui = sumFuel*CO2_FACTOR/sumWeight*1000                        #(kg CO2 / ton → g CO2 / ton)
        
        allTrips = trip[1]
        for tur in allTrips:
            delivery = _safe_get_dict(tur, 'delivery')
            tripRefFuel = _safe_get(tur, 'fuelConsumption')
            sumRefFuel += tripRefFuel                                   # Aggregate over all tours
            tripRefWeight = _safe_get(delivery, 'totalLivingWeight')
            sumRefWeight += tripRefWeight
            tripRefDistance = _safe_get(tur, 'distance')
            sumRefWeightXdistance += tripRefWeight/1000*tripRefDistance/1852        # Aggregate over all tours
        
        ref_eeoi = sumRefFuel*CO2_FACTOR/sumRefWeightXdistance*1000     #(kg CO2 / (ton*nm) → g CO2 / (ton*nm))
        ref_fui = sumRefFuel*CO2_FACTOR/sumRefWeight*1000               #(kg CO2 / ton → g CO2 / ton)

        myEeoiList.append(eeoi)                 
        refEeoiList.append(ref_eeoi)
        myFuiList.append(fui)     
        refFuiList.append(ref_fui)          

    # resultArray to be returned
    resultDict = {"myEeoiList": myEeoiList}
    resultDict.update({"refEeoiList": refEeoiList})
    resultDict.update({"myFuiList": myFuiList})
    resultDict.update({"refFuiList": refFuiList})

    return resultDict


# ---------------------------------------------------------------------
# KPI-02: FUI
# ---------------------------------------------------------------------
def kpi_02(gd: List[Dict[str, Any]], tripsArray: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    
    """
        Calculates FUI (Fuel Use Intensity) for each time period in periodArray.

        For every (startDate, endDate) tuple:
        - Retrieves FUI for the main vessel (gd.vesselId)
        - Retrieves average FUI for the reference vessels (gd.vesselRefIds)

        Values are converted from kg to grams (×1000).

        Returns a dictionary containing:
        - myFuiArray: FUI values for the main vessel
        - avFuiArray: Average FUI values for the reference group
        """

    # JSON keys
    myEeoiList = ['EEOI']
    refEeoiList = ['refEEOI']
    myFuiList = ['FUI']
    refFuiList = ['refFUI']
    
    for trip in tripsArray:
        sumFuel = 0
        sumWeightXdistance = 0
        sumWeight = 0
        sumRefFuel = 0
        sumRefWeightXdistance = 0
        sumRefWeight = 0
        
        myTrip = trip[0]    
        for tur in myTrip:
            delivery = _safe_get_dict(tur, 'delivery')
            tripFuel = _safe_get(tur, 'fuelConsumption') 
            sumFuel += tripFuel                                        # Aggregate over all tours
            tripWeight = _safe_get(delivery, 'totalLivingWeight')
            sumWeight += tripWeight                                    # Aggregate over all tours
            tripDistance = _safe_get(tur, 'distance')
            sumWeightXdistance += tripWeight/1000*tripDistance/1852     # Aggregate over all tours
                
        eeoi = sumFuel*CO2_FACTOR/sumWeightXdistance*1000               #(kg CO2 / (ton*nm) → g CO2 / (ton*nm))
        fui = sumFuel*CO2_FACTOR/sumWeight*1000                        #(kg CO2 / ton → g CO2 / ton)
        
        allTrips = trip[1]
        for tur in allTrips:
            delivery = _safe_get_dict(tur, 'delivery')
            tripRefFuel = _safe_get(tur, 'fuelConsumption')
            sumRefFuel += tripRefFuel                                   # Aggregate over all tours
            tripRefWeight = _safe_get(delivery, 'totalLivingWeight')
            sumRefWeight += tripRefWeight
            tripRefDistance = _safe_get(tur, 'distance')
            sumRefWeightXdistance += tripRefWeight/1000*tripRefDistance/1852        # Aggregate over all tours
        
        ref_eeoi = sumRefFuel*CO2_FACTOR/sumRefWeightXdistance*1000     #(kg CO2 / (ton*nm) → g CO2 / (ton*nm))
        ref_fui = sumRefFuel*CO2_FACTOR/sumRefWeight*1000               #(kg CO2 / ton → g CO2 / ton)

        myEeoiList.append(eeoi)                 
        refEeoiList.append(ref_eeoi)
        myFuiList.append(fui)     
        refFuiList.append(ref_fui)          

    # resultArray to be returned
    resultDict = {"myEeoiList": myEeoiList}
    resultDict.update({"refEeoiList": refEeoiList})
    resultDict.update({"myFuiList": myFuiList})
    resultDict.update({"refFuiList": refFuiList})

    return resultDict

# ---------------------------------------------------------------------
# KPI-03 and KPI-04: Revenue per ton & per hour (net, price-adjusted)
# ---------------------------------------------------------------------
def kpi_03_04(gd: List[Dict[str, Any]], periodArray: List[Dict[str, Any]], nVessels: int) -> List[Dict[str, Any]]:
    
    """
        Calculates two KPIs for each (startDate, endDate) in periodArray:

        KPI‑03: Netto fortjeneste per tonn fisk [NOK/tonn]
                = (fangstverdi − drivstoffkostnad) / fangst (kg→tonn)

        KPI‑04: Netto fortjeneste per time [NOK/time]
                = (fangstverdi − drivstoffkostnad) / timer

        For each period:
        - Retrieves average metrics for the main vessel (gd.vesselId) and the reference group (gd.vesselRefIds)
        - Uses SSB price for the month of sDate (adjusted by PRICE_DIFF)
        - Computes NOK/tonn (by scaling kg → tonn with ×1000) and NOK/time

        Returns a dictionary with four arrays:
        - myRevPerTonWeightArray      : main vessel, NOK/tonn
        - avRevPerTonWeightArray      : reference group, NOK/tonn
        - myRevPerHourArray           : main vessel, NOK/time
        - avRevPerHourArray           : reference group, NOK/time
        """

    df_client = _new_client()
    ssb_client = _new_client()  # used only for request(); auth=False

    # JSON keys
    myRevPerTonWeightArray = ['NetRevenuePerTon']
    avRevPerTonWeightArray = ['avNetRevenuePerTon']
    myRevPerHourArray = ['NetRevenuePerHour']
    avRevPerHourArray = ['avNetRevenuePerHour']

    for dateTuple in periodArray:
        # SSB price for the month of sDate
        sDate=dateTuple[0]
        eDate=dateTuple[1]
        ssb_url = _ssb_price_url(sDate, sDate)
        ssb = ssb_client.request(endpoint=ssb_url, auth=False) or {}
        price_values = ssb.get('value') if isinstance(ssb, dict) else None
        price = (price_values[0] if price_values else 0) - PRICE_DIFF

        # My vessel
        my_avg = df_client.get(
            E_AVERAGE, sDate=sDate, eDate=eDate,
            vesselGroups=gd.lengthG, gearGroups=gd.gearG,
            speciesGroups=gd.specG, locationGroups=gd.locG,
            vesselId = gd.vesselId,
        ) or {}
        my_cvf = _safe_get(my_avg, 'catchValuePerFuel')
        my_wpf = _safe_get(my_avg, 'weightPerFuel')
        my_wph = _safe_get(my_avg, 'weightPerHour')

        # Reference group
        av_avg = df_client.get(
            E_AVERAGE, sDate=sDate, eDate=eDate,
            vesselGroups=gd.lengthG, gearGroups=gd.gearG,
            speciesGroups=gd.specG, locationGroups=gd.locG,
            vesselId=gd.vesselRefIds,  # reference group
        ) or {}
        av_cvf = _safe_get(av_avg, 'catchValuePerFuel')
        av_wpf = _safe_get(av_avg, 'weightPerFuel')
        av_wph = _safe_get(av_avg, 'weightPerHour')

        # NOK/tonn (kg→tonn)
        my_rev_per_ton = _safe_div(my_cvf - price, my_wpf) * 1000.0
        av_rev_per_ton = _safe_div(av_cvf - price, av_wpf) * 1000.0

        # NOK/time
        my_rev_per_hour = _safe_div((my_cvf - price) * my_wph, my_wpf)
        av_rev_per_hour = _safe_div((av_cvf - price) * av_wph, av_wpf)

        myRevPerTonWeightArray.append(my_rev_per_ton)
        avRevPerTonWeightArray.append(av_rev_per_ton)
        myRevPerHourArray.append(my_rev_per_hour)
        avRevPerHourArray.append(av_rev_per_hour)

    resultArray = {"myRevPerTonWeightArray": myRevPerTonWeightArray}
    resultArray.update({"avRevPerTonWeightArray": avRevPerTonWeightArray})
    resultArray.update({"myRevPerHourArray": myRevPerHourArray})
    resultArray.update({"avRevPerHourArray": avRevPerHourArray})

    return resultArray


# ---------------------------------------------------------------------
# KPI-05: Annual catch and catch value
# ---------------------------------------------------------------------
def kpi_05(gd: List[Dict[str, Any]], tripsArray: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    
    """
       
        Calculates KPI metrics related to catch weight and catch value for a vessel
        compared to the average of a reference group.

        For each period in tripsArray:
        - trip[0] contains trips for the main vessel
        - trip[1] contains trips for all vessels in the reference group

        The function sums:
        - Catch weight (kg → tons)
        - Catch value (NOK → million NOK)

        It then calculates average values based on the number of vessels
        in gd.vesselRefIds.

        Returns a dictionary with 6 Lists:
        - myCatchList
        - refCatchList
        - myCatchValueList
        - refCatchValueList
        - myFuelList
        - refFuelList
        """
    
    # JSON keys
    myCatchList = ['Fangst']
    myCatchValueList = ['Fangstverdi']
    refCatchList = ['refFangst']
    refCatchValueList = ['refFangstverdi']
    myFuelList = ["Drivstoff"]
    refFuelList = ["refDrivstoff"]

    formatString = '%Y-%m-%dT%H:%M:%S%z'

    for trip in tripsArray:
        sumWeight = 0
        sumPrice = 0
        sumFuel = 0
        sumDistance = 0  
        sumRefWeight = 0
        sumRefPrice = 0
        sumRefFuel = 0
        sumHours = 0
        sumRefHours = 0
        
        myTrip = trip[0]    
        for tur in myTrip:
                delivery = _safe_get_dict(tur, 'delivery')
                sumWeight += _safe_get(delivery, 'totalLivingWeight')
                sumPrice += _safe_get(delivery, 'totalPriceForFisher')
                sumFuel += _safe_get(tur, 'fuelConsumption')
                sumDistance += _safe_get(tur, 'distance')
                startString = _safe_get_string(tur, 'start')
                endString = _safe_get_string(tur, 'end')
                startDateTime = datetime.datetime.strptime(startString, formatString)
                endDateTime = datetime.datetime.strptime(endString, formatString)
                timeDiff = endDateTime - startDateTime
                tripHours = timeDiff.total_seconds() / 3600
                sumHours += tripHours

                
        
        allTrips = trip[1]
        for tur in allTrips:
            delivery = _safe_get_dict(tur, 'delivery')
            sumRefWeight += _safe_get(delivery, 'totalLivingWeight')
            sumRefPrice += _safe_get(delivery, 'totalPriceForFisher')
            sumRefFuel += _safe_get(tur, 'fuelConsumption')
            startDateTime = datetime.datetime.strptime(startString, formatString)
            endDateTime = datetime.datetime.strptime(endString, formatString)
            timeDiff = endDateTime - startDateTime
            refHours = timeDiff.total_seconds() / 3600
            sumRefHours += refHours
            
        sumRefWeight = sumRefWeight / len(gd.vesselRefIds)        #Average over all vessels in ref group
        sumRefPrice = sumRefPrice / len(gd.vesselRefIds)          #Average over all vessels in ref group
        sumRefFuel = sumRefFuel / len(gd.vesselRefIds)            #Average over all vessels in ref group

        myCatchList.append(sumWeight / 1000)                  #(kg → tons)
        refCatchList.append(sumRefWeight / 1000)               #(kg → tons)
        myCatchValueList.append(sumPrice / 1000 / 1000)       #(NOK → million NOK)
        refCatchValueList.append(sumRefPrice / 1000 / 1000)    #(NOK → million NOK)
        myFuelList.append(sumFuel / 1000)                     #(Liter → kLiter)
        refFuelList.append(sumRefFuel / 1000)                  #(Liter → kLiter)

    # resultArray to be returned
    resultDict = {"myCatchList": myCatchList}
    resultDict.update({"refCatchList": refCatchList})
    resultDict.update({"myCatchValueList": myCatchValueList})
    resultDict.update({"refCatchValueList": refCatchValueList})
    resultDict.update({"myFuelList": myFuelList})
    resultDict.update({"refFuelList": refFuelList})

    return resultDict 




# ---------------------------------------------------------------------
# Utilities (pagination, main species), now using the client per call
# ---------------------------------------------------------------------
def getAllTripsInPeriod(endpoint: str, sDate: QDate, eDate: QDate,
                    lengthG: List[str], gearG: List[str], specG: List[str], locG: List[str]) -> int:
    page_size = 100
    offset = 0
    all_items: List[Dict[str, Any]] = []

    while True:
        client = _new_client()
        page = client.get(
            endpoint,
            sDate=sDate, eDate=eDate,
            vesselGroups=lengthG, gearGroups=gearG,
            speciesGroups=specG, locationGroups=locG,
            #vesselId = gd.vesselId,
            limit=page_size, offset=offset,
        )

        if not page or not isinstance(page, list):
            break

        all_items.extend(page)
        if len(page) < page_size:
            break
        offset += page_size

    print("Antall turer funnet:", len(all_items))
    return noVessels(all_items)


# ---------------------------------------------------------------------
#   getAllDatesInPeriod(endpoint, gd)
#
#   This function will calculate the time periods, and for each period
#   download all my trips and all trips for the reference group.
#   Output is an array with elements for each time period. 
#   Each time period element is an array including startDate, endDate,
#   myTrips dictionary and refGroupTrips dictionary
# ---------------------------------------------------------------------

def getAllTripsInPeriods(endpoint: str, gd: List[Dict[str, Any]], periodArray: List[Dict[str, Any]] ) -> None:
    page_size = 100
    dataSet = []
    maxNoVessels = 0

    for dateTuple in periodArray:
         ##############################################
        # Collect data from all my trips in the period
        ##############################################   
        offset = 0
        my_items: List[Dict[str, Any]] = []

        # Set start date one month earlier to include trips that have started in prevoious period
        sDate = dateTuple[0].addMonths(-1)
        
        while True:
            client = _new_client()
            page = client.get(
                endpoint, sDate=sDate, eDate=dateTuple[1],
                vesselGroups=gd.lengthG, gearGroups=gd.gearG,
                speciesGroups=gd.specG, locationGroups=gd.locG,
                vesselId = gd.vesselId, limit = page_size, offset = offset
            ) or {}
            
            if not page or not isinstance(page, list):
                break

            my_items.extend(page)
            if len(page) < page_size:
                break
            offset += page_size

                
        #####################################################################
        # Collect data from trips in the reference group in the period
        #####################################################################
        offset = 0
        all_items: List[Dict[str, Any]] = []

        while True:
            client = _new_client()
            page = client.get(
                endpoint, sDate=sDate, eDate=dateTuple[1],
                vesselGroups=gd.lengthG, gearGroups=gd.gearG,
                speciesGroups=gd.specG, locationGroups=gd.locG,
                vesselId = gd.vesselRefIds,  # reference group
                limit = page_size, offset = offset
            ) or {}

            if not page or not isinstance(page, list):
                break

            all_items.extend(page)
            if len(page) < page_size:
                break
            offset += page_size

        periodNoVessels = noVessels(all_items)
        if (periodNoVessels > maxNoVessels):
            maxNoVessels = periodNoVessels
        
        # Now we must exclude trips that both started and ended in the month before our period starts
        myNewItems, allNewItems = excludeTrips(my_items, all_items, sDate)
        
        dataSet.append((myNewItems, allNewItems))
    
    return maxNoVessels, dataSet
    
def excludeTrips(myItems, allItems, sDate):
    #Convert sDat to string
    sDateString = sDate.toString("yyyy-MM-dd")
    
    #extract month number
    m = re.search(r'\b(0?[1-9]|1[0-2])\b', sDateString)
    if m:
        ext_month = int(m.group(1))  

    new_myList = []
    for tour in myItems:
        eDateString = tour["end"]
        #extract month number
        m = re.search(r'\b(0?[1-9]|1[0-2])\b', eDateString)
        if m:
            thisMonth = int(m.group(1))

        if (thisMonth != ext_month):
            new_myList.append(tour)
            
    #print("oldLen: ", len(myItems), "newLen: ", len(new_myList))
    new_allList = []
    for tour in allItems:
        eDateString = tour["end"]
        #extract month number
        m = re.search(r'\b(0?[1-9]|1[0-2])\b', eDateString)
        if m:
            thisMonth = int(m.group(1))

        if (thisMonth != ext_month):
            new_allList.append(tour)
    
    #print("oldLen: ", len(allItems), "newLen: ", len(new_allList))
    return new_myList, new_allList




def getMainSpecie(endpoint: str, sDate: QDate, eDate: QDate,
                  lengthG: List[str], gearG: List[str], specG: List[str], locG: List[str]) -> Optional[str]:
    page_size = 100
    offset = 0
    all_items: List[Dict[str, Any]] = []

    while True:
        client = _new_client()
        page = client.get(
            endpoint,
            sDate=sDate, eDate=eDate,
            vesselGroups=lengthG, gearGroups=gearG,
            speciesGroups=specG, locationGroups=locG,
            limit=page_size, offset=offset,
            vesselId=None,  # my vessel? set fiskdirId if needed
        )

        if not page or not isinstance(page, list):
            break

        all_items.extend(page)
        if len(page) < page_size:
            break
        offset += page_size

    print("Antall turer funnet:", len(all_items))
    mainSpecieList = findMainSpecie(all_items)
    return Counter(mainSpecieList).most_common(1)[0][0] if mainSpecieList else None
