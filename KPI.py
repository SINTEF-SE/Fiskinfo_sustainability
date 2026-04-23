
# kpi_module.py
from typing import List, Optional, Any, Dict, Mapping, MutableMapping, Iterable
import json
from collections import Counter
import re
from datetime import datetime, timezone

from PySide6.QtCore import QDate
from datafangst_client import DatafangstClient

# Only import what you need from utility to avoid namespace clashes
from utility import nlg, noVessels, findMainSpecie, getLengthGroups

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

CO2_FACTOR = 2.66              # kg CO2 / liter drivstoff
HOURS_IN_DAY = 24              # number of hours in a day
NM = 1852                      # nautisk mil in meters

_FORMATS = [
    "%Y-%m-%dT%H:%M:%SZ",      # no fractional seconds
    "%Y-%m-%dT%H:%M:%S.%fZ",   # with fractional seconds
]


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

def _excludeTrips(myItems, allItems, sDate):
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

def _getTripHours(startString, endString):
    startDateTime = _parse_utc_z_strptime(startString)
    endDateTime = _parse_utc_z_strptime(endString)
    timeDiff = endDateTime - startDateTime
    tripHours = timeDiff.total_seconds() / 3600   
    return tripHours  

def _parse_utc_z_strptime(s: str) -> datetime:
    last_err = None
    for fmt in _FORMATS:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError as e:
            last_err = e
    raise ValueError(f"Unsupported datetime format for: {s}")

# ---------------------------------------------------------------------
# KPI: Calculate all KPIs
# ---------------------------------------------------------------------
def kpiCalculations(gd: List[Dict[str, Any]], tripsArray: List[Dict[str, Any]], priceList: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    
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
        
    #-----------------------------------------------------------------------
    # Define Lists for all the calculated data, the first value is the JSON key
    #-----------------------------------------------------------------------
    myEeoiList =                ["EEOI"]
    refEeoiList =               ["refEEOI"]
    myFuiList =                 ["FUI"]
    refFuiList =                ["refFUI"]
    myCatchList =               ["Fangst"]
    refCatchList =              ["refFangst"]
    myCatchValueList =          ["FangstVerdi"]
    refCatchValueList =         ["refFangstVerdi"]
    myFuelList =                ["Drivstofforbruk"]
    refFuelList =               ["refDrivstofforbruk"]
    myFuelCostList =            ["Drivstoffkostnad"]
    refFuelCostList =           ["refDrivstoffKostnad"]
    myCO2PerTripList =          ["CO2utslippPerTur"]
    refCO2PerTripList =         ["refCO2utslippPerTur"]
    myDistanceList =            ["SeiltDistanse"]
    refDistanceList =           ["refSeiltDistanse"]
    myHoursList =               ["FiskeTimer"]
    refHoursList =              ["refFiskeTimer"]
    weightPerTripList =         ["FangstPerTur"]
    refWeightPerTripList =      ["refFangstPerTur"]
    catchValuePerTripList =     ["FangstVerdiPerTur"]
    refCatchValuePerTripList =  ["refFangstVerdiPerTur"]
    daysPerTripList =           ["DagerPerTur"]
    refDaysPerTripList =        ["refDagerPerTur"]
    fuelPerTripList =           ["DrivstofforbrukPerTur"]
    refFuelPerTripList =        ["refDrivstofforbrukPerTur"]
    distancePerTripList =       ["SeiltDistansePerTur"]
    refDistancePerTripList =    ["refSeiltDistansePerTur"]
    fuelCostPerTripList =       ["DrivstoffkostnadPerTur"]
    refFuelCostPerTripList =    ["refDrivstoffkostnadPerTur"]
    myRevPerTonWeightList =     ["NettoFortjenestePerTonnFangst"]
    refRevPerTonWeightList =     ["refNettoFortjenestePerTonnFangst"]
    myRevPerHourList =          ["NettoFortjenestePerTime"]
    refRevPerHourList =          ["refNettoFortjenestePerTime"]
    
    i = 0
    for period in tripsArray:
        sumWeight = 0
        sumPrice = 0
        sumFuel = 0
        sumCO2 = 0
        sumDistance = 0  
        sumRefWeight = 0
        sumRefPrice = 0
        sumRefFuel = 0
        sumRefDistance = 0
        sumHours = 0
        sumRefHours = 0
        sumRefWeightXdistance = 0
        sumWeightXdistance = 0
        myTrip = period[0] 
        noMyTrips = len(myTrip)

        for tur in myTrip:
            delivery = _safe_get_dict(tur, 'delivery')
            tripWeight = _safe_get(delivery, 'totalLivingWeight')
            sumWeight += tripWeight
            sumPrice += _safe_get(delivery, 'totalPriceForFisher')
            fuel = _safe_get(tur, 'fuelConsumption')
            if (fuel == 0):
                sumFuel += _safe_get(tur, 'fuelConsumptionEstimatedOnly')
            else:
                sumFuel += fuel

            tripDistance = _safe_get(tur, 'distance')
            sumDistance += tripDistance
            startString = _safe_get_string(tur, 'start')
            endString = _safe_get_string(tur, 'end')
            tripHours = _getTripHours(startString, endString)
            sumHours += tripHours
            tripDistance = _safe_get(tur, 'distance')
            sumWeightXdistance += tripWeight/1000*tripDistance/1852     # Aggregate over all tours

        eeoi = sumFuel*CO2_FACTOR/sumWeightXdistance*1000               #(kg CO2 / (ton*nm) → g CO2 / (ton*nm))
        fui = sumFuel*CO2_FACTOR/sumWeight*1000                         #(kg CO2 / ton → g CO2 / ton)
        fuelCost = sumFuel * priceList[i]                               # Total fuel cost in the period
        revPerTonWeight = (sumPrice - fuelCost) / sumWeight
        revPerHour = (sumPrice - fuelCost) / sumHours


        sumCO2 = sumFuel*CO2_FACTOR / noMyTrips                 # average over all trips
        weightPerTrip = sumWeight / noMyTrips                   # average over all trips
        pricePerTrip = sumPrice / noMyTrips                     # average over all trips
        daysPerTrip = sumHours/HOURS_IN_DAY/noMyTrips           # average over all trips
        fuelPerTrip = sumFuel/noMyTrips                         # average over all trips
        distancePerTrip = sumDistance / noMyTrips               # average over all trips
        fuelCostPerTrip = fuelCost / noMyTrips                  # average over all trips
        

                
        
        allTrips = period[1]
        noAllTrips = len(allTrips)
        for tur in allTrips:
            delivery = _safe_get_dict(tur, 'delivery')
            tripRefWeight = _safe_get(delivery, 'totalLivingWeight')
            sumRefWeight += tripRefWeight
            sumRefPrice += _safe_get(delivery, 'totalPriceForFisher')
            refFuel = _safe_get(tur, 'fuelConsumption')
            if (refFuel == 0):
                sumRefFuel += _safe_get(tur, 'fuelConsumptionEstimatedOnly')
            else:
                sumRefFuel += refFuel

            tripRefDistance = _safe_get(tur, 'distance')
            sumRefDistance += tripRefDistance
            startString = _safe_get_string(tur, 'start')
            endString = _safe_get_string(tur, 'end')
            refHours = _getTripHours(startString, endString)
            sumRefHours += refHours
            sumRefWeightXdistance += tripRefWeight/1000*tripRefDistance/1852        # Aggregate over all tours
        
        refFuelCost = sumRefFuel * priceList[i]
        ref_eeoi = sumRefFuel*CO2_FACTOR/sumRefWeightXdistance*1000     #(kg CO2 / (ton*nm) → g CO2 / (ton*nm))
        ref_fui = sumRefFuel*CO2_FACTOR/sumRefWeight*1000               #(kg CO2 / ton → g CO2 / ton)  
        refRevPerTonWeight = (sumRefPrice - refFuelCost) / sumRefWeight
        refRevPerHour = (sumRefPrice - refFuelCost) / sumRefHours
        refFuelCostPerTrip = refFuelCost / noAllTrips           # average over all trips  
        
        refFuelCost = sumRefFuel * priceList[i] / len(gd.vesselRefIds)  # average over all trips
        refFuelPerTrip = sumRefFuel/noAllTrips                  # average over all trips
        refPricePerTrip = sumRefPrice / noAllTrips              # average over all trips
        refDaysPerTrip = sumRefHours/HOURS_IN_DAY/noAllTrips    # average over all trips
        refDistancePerTrip = sumRefDistance / noAllTrips        # average over all trips
        sumRefCO2 = sumRefFuel*CO2_FACTOR / noAllTrips          # average over all trips
        refWeightPerTrip = sumRefWeight / noAllTrips            # average over all trips
        # må sjekkes
         
        sumRefWeight = sumRefWeight / len(gd.vesselRefIds)      #Average over all vessels in ref group
        sumRefPrice = sumRefPrice / len(gd.vesselRefIds)        #Average over all vessels in ref group
        sumRefFuel = sumRefFuel / len(gd.vesselRefIds)          #Average over all vessels in ref group

       
        myEeoiList.append(eeoi)                 
        refEeoiList.append(ref_eeoi)
        myFuiList.append(fui)     
        refFuiList.append(ref_fui)   
        myCatchList.append(sumWeight / 1000)                                #(kg → tons)
        refCatchList.append(sumRefWeight / 1000)                            #(kg → tons)
        myCatchValueList.append(sumPrice / 1000 / 1000)                     #(NOK → million NOK)
        refCatchValueList.append(sumRefPrice / 1000 / 1000)                 #(NOK → million NOK)
        myFuelList.append(sumFuel / 1000)                                   #(Liter → kLiter)
        refFuelList.append(sumRefFuel / 1000)                               #(Liter → kLiter)
        myFuelCostList.append(fuelCost / 1000 / 1000)                       #(NOK → mill NOK)
        refFuelCostList.append(refFuelCost / 1000 / 1000)                   #(NOK → mill NOK)
        myCO2PerTripList.append(sumCO2 / 1000)                              #(kg → tons)
        refCO2PerTripList.append(sumRefCO2 / 1000)                          #(kg → tons)
        myDistanceList.append(sumDistance)
        refDistanceList.append(sumRefDistance)
        myHoursList.append(sumHours)
        refHoursList.append(sumRefHours)
        weightPerTripList.append(weightPerTrip / 1000)                      #(kg → tons)
        refWeightPerTripList.append(refWeightPerTrip / 1000)                #(kg → tons)
        catchValuePerTripList.append(pricePerTrip / 1000 / 1000)            #(NOK → million NOK)
        refCatchValuePerTripList.append(refPricePerTrip / 1000 / 1000)      #(NOK → million NOK)
        daysPerTripList.append(daysPerTrip)
        refDaysPerTripList.append(refDaysPerTrip)
        fuelPerTripList.append(fuelPerTrip / 1000)                          #(Liter → kLiter)
        refFuelPerTripList.append(refFuelPerTrip / 1000)                    #(Liter → kLiter)
        distancePerTripList.append(distancePerTrip / NM)                    # (meter -> nautisk mil)
        refDistancePerTripList.append(refDistancePerTrip / NM)              # (meter -> nautisk mil)
        myRevPerTonWeightList.append(revPerTonWeight)                       #(1000 NOK / tonn)
        refRevPerTonWeightList.append(refRevPerTonWeight)                    #(1000 NOK / tonn)
        myRevPerHourList.append(revPerHour / 1000)                          #(NOK → 1000 NOK)
        refRevPerHourList.append(refRevPerHour / 1000)                       #(NOK → 1000 NOK)
        fuelCostPerTripList.append(fuelCostPerTrip / 1000 / 1000)           #(NOK → mill NOK)
        refFuelCostPerTripList.append(refFuelCostPerTrip /1000 / 1000)      #(NOK → mill NOK)
        i += 1


    #--------------------------------------------------------------
    # resultDictionary to be returned
    #--------------------------------------------------------------
    resultDict =      {"myCatchList":               myCatchList}
    resultDict.update({"refCatchList":              refCatchList})
    resultDict.update({"myCatchValueList":          myCatchValueList})
    resultDict.update({"refCatchValueList":         refCatchValueList})
    resultDict.update({"myFuelList":                myFuelList})
    resultDict.update({"refFuelList":               refFuelList})
    resultDict.update({"myFuelCostList":            myFuelCostList})
    resultDict.update({"refFuelCostList":           refFuelCostList})
    resultDict.update({"myCO2PerTripList":          myCO2PerTripList})
    resultDict.update({"refCO2PerTripList":         refCO2PerTripList})
    resultDict.update({"myDistanceList":            myDistanceList})
    resultDict.update({"refDistanceList":           refDistanceList})
    resultDict.update({"myHoursList":               myHoursList})
    resultDict.update({"refHoursList":              refHoursList})
    resultDict.update({"weightPerTripList":         weightPerTripList})
    resultDict.update({"refWeightPerTripList":      refWeightPerTripList})
    resultDict.update({"catchValuePerTripList":     catchValuePerTripList})
    resultDict.update({"refCatchValuePerTripList":  refCatchValuePerTripList})
    resultDict.update({"daysPerTripList":           daysPerTripList})
    resultDict.update({"refDaysPerTripList":        refDaysPerTripList})
    resultDict.update({"fuelPerTripList":           fuelPerTripList})
    resultDict.update({"refFuelPerTripList":        refFuelPerTripList})
    resultDict.update({"distancePerTripList":       distancePerTripList})
    resultDict.update({"refDistancePerTripList":    refDistancePerTripList})
    resultDict.update({"myEeoiList":                myEeoiList})
    resultDict.update({"refEeoiList":               refEeoiList})
    resultDict.update({"myFuiList":                 myFuiList})
    resultDict.update({"refFuiList":                refFuiList})
    resultDict.update({"myRevPerTonWeightList":     myRevPerTonWeightList})
    resultDict.update({"refRevPerTonWeightList":    refRevPerTonWeightList})
    resultDict.update({"myRevPerHourList":          myRevPerHourList})
    resultDict.update({"refRevPerHourList":         refRevPerHourList})
    resultDict.update({"fuelCostPerTripList":       fuelCostPerTripList})
    resultDict.update({"refFuelCostPerTripList":    refFuelCostPerTripList})

    return resultDict 


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

        #lengthGroup = getLenghtGroups(gd.lengthG)
        
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
        myNewItems, allNewItems = _excludeTrips(my_items, all_items, sDate)
        
        dataSet.append((myNewItems, allNewItems))
    
    return maxNoVessels, dataSet


def getPricesInPeriod(periodArray):
    priceList = []
    ssb_client = _new_client()  # used only for request(); auth=False
    for dateTuple in periodArray:
        # SSB price for the month of sDate
        sDate=dateTuple[0]
        eDate=dateTuple[1]
        ssb_url = _ssb_price_url(sDate, eDate)
        ssb = ssb_client.request(endpoint=ssb_url, auth=False) or {}
        price_values = ssb.get('value') if isinstance(ssb, dict) else None
        price = (price_values[0] if price_values else 0) - PRICE_DIFF
        priceList.append(price)

    return priceList
