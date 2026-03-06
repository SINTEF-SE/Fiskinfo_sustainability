
# kpi_module.py
from typing import List, Optional, Any, Dict, Mapping, MutableMapping, Iterable, Tuple
import json
from collections import Counter

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
def kpi_01(gd, toPngFile: str):
    """EEOI [g CO2 /(fangst*nm)] aggregated over sliding windows."""
    client = _new_client()

    norskLgroup = _norsk_length_group(gd.lengthG)
    startDateList, endDateList = gd.datesArray
    if not startDateList or not endDateList:
        print("kpi_01: No dates provided.")
        return

    myEeoiArray = ['EEOI']
    avEeoiArray = ['Gj.snitt EEOI']

    for sDate, eDate in zip(startDateList, endDateList):
        my_val = client.get(
            E_AV_EEOI,
            sDate=sDate, eDate=eDate,
            vesselGroups=gd.lengthG, gearGroups=gd.gearG,
            speciesGroups=gd.specG, locationGroups=gd.locG,
            #vesselId=getattr(gd, "fiskdirId", None),  # if present
            vesselId = gd.vesselId,
        )
        av_val = client.get(
            E_AV_EEOI,
            sDate=sDate, eDate=eDate,
            vesselGroups=gd.lengthG, gearGroups=gd.gearG,
            speciesGroups=gd.specG, locationGroups=gd.locG,
            vesselId=gd.vesselRefIds,  # reference group
        )

        # endpoints return float; coerce and scale to grams
        myEeoiArray.append(1000.0 * float(my_val or 0))
        avEeoiArray.append(1000.0 * float(av_val or 0))

    gd.dataArray.append(myEeoiArray)
    gd.dataArray.append(avEeoiArray)

    print("myEeoi array:", myEeoiArray)
    print("AvEeoi array:", avEeoiArray)

    span = monthsBetweenQdates(startDateList[0], endDateList[0])
    title = (
        "KPI-01: EEOI [g CO2 /(fangst*nm)] aggregert over {months} måneder\n"
        "Lengde: {vGroup}, Redskap: {gGroup}"
    ).format(months=span, vGroup=norskLgroup, gGroup=gd.gearG)

    plot(endDateList, myEeoiArray, avEeoiArray, title,
         "{antall} båter i referansegruppen".format(antall=gd.nVessels),
         fName=toPngFile)

# ---------------------------------------------------------------------
# KPI-02: FUI
# ---------------------------------------------------------------------
def kpi_02(gd, toPngFile: str):
    """FUI [g CO2 /fangst] aggregated over sliding windows."""
    client = _new_client()

    norskLgroup = _norsk_length_group(gd.lengthG)
    startDateList, endDateList = gd.datesArray
    if not startDateList or not endDateList:
        print("kpi_02: No dates provided.")
        return

    myFuiArray = ['FUI']
    avFuiArray = ['Gj.snitt FUI']

    for sDate, eDate in zip(startDateList, endDateList):
        my_val = client.get(
            E_AV_FUI,
            sDate=sDate, eDate=eDate,
            vesselGroups=gd.lengthG, gearGroups=gd.gearG,
            speciesGroups=gd.specG, locationGroups=gd.locG,
            #vesselId=getattr(gd, "fiskdirId", None),
            vesselId = gd.vesselId,
        )
        av_val = client.get(
            E_AV_FUI,
            sDate=sDate, eDate=eDate,
            vesselGroups=gd.lengthG, gearGroups=gd.gearG,
            speciesGroups=gd.specG, locationGroups=gd.locG,
            vesselId=gd.vesselRefIds,  # reference group
        )

        myFuiArray.append(1000.0 * float(my_val or 0))
        avFuiArray.append(1000.0 * float(av_val or 0))

    gd.dataArray.append(myFuiArray)
    gd.dataArray.append(avFuiArray)

    print("myFui array:", myFuiArray)
    print("AvFui array:", avFuiArray)

    span = monthsBetweenQdates(startDateList[0], endDateList[0])
    title = (
        "KPI-02: FUI [g CO2 /fangst] aggregert over {months} måneder\n"
        "Lengde: {vGroup}, Redskap: {gGroup}"
    ).format(months=span, vGroup=norskLgroup, gGroup=gd.gearG)

    plot(endDateList, myFuiArray, avFuiArray, title,
         "{antall} båter i referansegruppen".format(antall=gd.nVessels),
         fName=toPngFile)

# ---------------------------------------------------------------------
# KPI-03 and KPI-04: Revenue per ton & per hour (net, price-adjusted)
# ---------------------------------------------------------------------
def kpi_03_04(gd):
    """Compute and plot:
       KPI-03: Netto fortjeneste per tonn fisk [NOK/tonn] ((fangstverdi - drivstoffkostnad) / tonn fangst)
       KPI-04: Netto fortjeneste per time [NOK/time]      ((fangstverdi - drivstoffkostnad) / timer)
    """
    df_client = _new_client()
    ssb_client = _new_client()  # used only for request(); auth=False

    toPngFile03 = "output/kpi03"
    toPngFile04 = "output/kpi04"

    norskLgroup = _norsk_length_group(gd.lengthG)
    startDateList, endDateList = gd.datesArray
    if not startDateList or not endDateList:
        print("kpi_03_04: No dates provided.")
        return

    myRevPerTonWeightArray = ['Netto fortjeneste per tonn fisk [NOK]']
    avRevPerTonWeightArray = ['Gj.snitt Netto fortjeneste per tonn fisk [NOK]']
    myRevPerHourArray = ['Netto fortjeneste per time [NOK])']
    avRevPerHourArray = ['Gj.snitt Netto fortjeneste per time [NOK]']

    for sDate, eDate in zip(startDateList, endDateList):
        # SSB price for the month of sDate
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

    gd.dataArray.append(myRevPerTonWeightArray)
    gd.dataArray.append(avRevPerTonWeightArray)
    gd.dataArray.append(myRevPerHourArray)
    gd.dataArray.append(avRevPerHourArray)

    span = monthsBetweenQdates(startDateList[0], endDateList[0])

    title = (
        "KPI-03: Rev. per Ton [NOK / Tonn] aggregert over {months} måneder\n"
        "Lengde: {vGroup}, Redskap: {gGroup}"
    ).format(months=span, vGroup=norskLgroup, gGroup=gd.gearG)
    plot(endDateList, myRevPerTonWeightArray, avRevPerTonWeightArray, title,
         "{antall} båter i referansegruppen".format(antall=gd.nVessels),
         fName=toPngFile03)

    title = (
        "KPI-04: Rev. per Hour [NOK / time] aggregert over {months} måneder\n"
        "Lengde: {vGroup}, Redskap: {gGroup}"
    ).format(months=span, vGroup=norskLgroup, gGroup=gd.gearG)
    plot(endDateList, myRevPerHourArray, avRevPerHourArray, title,
         "{antall} båter i referansegruppen".format(antall=gd.nVessels),
         fName=toPngFile04)

# ---------------------------------------------------------------------
# KPI-05: Annual catch and catch value
# ---------------------------------------------------------------------
def kpi_05(gd, toPngFile: str):
    """KPI-05: Årlig fangst [Tonn/År] og fangstverdi [mill. NOK/År]."""
    #client = _new_client()
    toPngFile05_1 = "output/kpi05_1"

    norskLgroup = _norsk_length_group(gd.lengthG)
    startDateList, endDateList = gd.datesArray
    if not startDateList or not endDateList:
        print("kpi_05: No dates provided.")
        return

    myCatchArray = ['Fangst [tonn]']
    myCatchValueArray = ['Fangstverdi [mill. NOK]']
    avCatchArray = ['Gj.snitt fangst [tonn]']
    avCatchValueArray = ['Gj.snitt fangstverdi [mill. NOK]']

    page_size = 100

    for sDate, eDate in zip(startDateList, endDateList):
        ##############################################
        # Collect data from all my trips in the period
        ##############################################
        weight = 0
        price = 0
        fuel = 0
        distance = 0    
        offset = 0
        my_items: List[Dict[str, Any]] = []
        
        while True:
            client = _new_client()
            page = client.get(
                E_TRIPS, sDate=sDate, eDate=eDate,
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
            
        for tur in my_items:
                delivery = _safe_get_dict(tur, 'delivery')
                weight += _safe_get(delivery, 'totalLivingWeight')
                price += _safe_get(delivery, 'totalPriceForFisher')
                fuel += _safe_get(tur, 'fuelConsumption')
                distance += _safe_get(tur, 'distance')
        
        #####################################################################
        # Collect data from trips in the reference group in the period
        #####################################################################
        av_Weight = 0
        av_Price = 0
        offset = 0
        all_items: List[Dict[str, Any]] = []

        while True:
            client = _new_client()
            page = client.get(
                E_TRIPS, sDate=sDate, eDate=eDate,
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

        for tur in all_items:
            delivery = _safe_get_dict(tur, 'delivery')
            av_Weight += _safe_get(delivery, 'totalLivingWeight')
            av_Price += _safe_get(delivery, 'totalPriceForFisher')
            #fuel += _safe_get(tur, 'fuelConsumption')
            #distance += _safe_get(tur, 'distance')

        av_Weight = av_Weight / len(gd.vesselRefIds)
        av_Price = av_Price / len(gd.vesselRefIds)

        myCatchArray.append(weight / 1000)
        avCatchArray.append(av_Weight / 1000)
        myCatchValueArray.append(price / 1000 / 1000)
        avCatchValueArray.append(av_Price / 1000 / 1000)

    gd.dataArray.append(myCatchArray)
    gd.dataArray.append(avCatchArray)
    gd.dataArray.append(myCatchValueArray)
    gd.dataArray.append(avCatchValueArray)

    print("myCatch array:", myCatchArray)
    print("myCatchValue array:", myCatchValueArray)
    print("avCatch array:", avCatchArray)
    print("avCatchValue array:", avCatchValueArray)

    span = monthsBetweenQdates(startDateList[0], endDateList[0])

    title = (
        "KPI-05: Fangst [Tonn] aggregert over {months} måneder\n"
        "Lengde: {vGroup}, Redskap: {gGroup}"
    ).format(months=span, vGroup=norskLgroup, gGroup=gd.gearG)
    plot(endDateList, myCatchArray, avCatchArray, title,
         "{antall} båter i referansegruppen".format(antall=gd.nVessels),
         fName=toPngFile)

    title = (
        "KPI-05: Fangstverdi [mill. NOK] aggregert over {months} måneder\n"
        "Lengde: {vGroup}, Redskap: {gGroup}"
    ).format(months=span, vGroup=norskLgroup, gGroup=gd.gearG)
    plot(endDateList, myCatchValueArray, avCatchValueArray, title,
         "{antall} båter i referansegruppen".format(antall=gd.nVessels),
         fName=toPngFile05_1)
    

# ---------------------------------------------------------------------
# KPI-05: Annual catch and catch value
# ---------------------------------------------------------------------
'''def kpi_05(noVessel, dataArray, toPngFile: str):
    """KPI-05: Årlig fangst [Tonn/År] og fangstverdi [mill. NOK/År]."""
    #client = _new_client()
    toPngFile05_1 = "output/kpi05_1"

    norskLgroup = _norsk_length_group(gd.lengthG)
    startDateList, endDateList = gd.datesArray
    if not startDateList or not endDateList:
        print("kpi_05: No dates provided.")
        return

    myCatchArray = ['Fangst [tonn]']
    myCatchValueArray = ['Fangstverdi [mill. NOK]']
    avCatchArray = ['Gj.snitt fangst [tonn]']
    avCatchValueArray = ['Gj.snitt fangstverdi [mill. NOK]']

    for element in dataArray:
        my_items = element[2]     
        for tur in my_items:
                delivery = _safe_get_dict(tur, 'delivery')
                weight += _safe_get(delivery, 'totalLivingWeight')
                price += _safe_get(delivery, 'totalPriceForFisher')
                fuel += _safe_get(tur, 'fuelConsumption')
                distance += _safe_get(tur, 'distance')
        
        
        all_items = element[3]
        for tur in all_items:
            delivery = _safe_get_dict(tur, 'delivery')
            av_Weight += _safe_get(delivery, 'totalLivingWeight')
            av_Price += _safe_get(delivery, 'totalPriceForFisher')
            #fuel += _safe_get(tur, 'fuelConsumption')
            #distance += _safe_get(tur, 'distance')

        av_Weight = av_Weight / len(gd.vesselRefIds)
        av_Price = av_Price / len(gd.vesselRefIds)

        myCatchArray.append(weight / 1000)
        avCatchArray.append(av_Weight / 1000)
        myCatchValueArray.append(price / 1000 / 1000)
        avCatchValueArray.append(av_Price / 1000 / 1000)

    gd.dataArray.append(myCatchArray)
    gd.dataArray.append(avCatchArray)
    gd.dataArray.append(myCatchValueArray)
    gd.dataArray.append(avCatchValueArray)

    print("myCatch array:", myCatchArray)
    print("myCatchValue array:", myCatchValueArray)
    print("avCatch array:", avCatchArray)
    print("avCatchValue array:", avCatchValueArray)

    span = monthsBetweenQdates(startDateList[0], endDateList[0])

    title = (
        "KPI-05: Fangst [Tonn] aggregert over {months} måneder\n"
        "Lengde: {vGroup}, Redskap: {gGroup}"
    ).format(months=span, vGroup=norskLgroup, gGroup=gd.gearG)
    plot(endDateList, myCatchArray, avCatchArray, title,
         "{antall} båter i referansegruppen".format(antall=gd.nVessels),
         fName=toPngFile)

    title = (
        "KPI-05: Fangstverdi [mill. NOK] aggregert over {months} måneder\n"
        "Lengde: {vGroup}, Redskap: {gGroup}"
    ).format(months=span, vGroup=norskLgroup, gGroup=gd.gearG)
    plot(endDateList, myCatchValueArray, avCatchValueArray, title,
         "{antall} båter i referansegruppen".format(antall=gd.nVessels),
         fName=toPngFile05_1)'''

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

def __getAllTripsInPeriod(endpoint: str, gd: List[Dict[str, Any]]) -> None:
    page_size = 100

    getDatesArray(gd)
    startDateList, endDateList = gd.datesArray
    returnElement = []

    for sDate, eDate in zip(startDateList, endDateList):
         ##############################################
        # Collect data from all my trips in the period
        ##############################################   
        offset = 0
        my_items: List[Dict[str, Any]] = []
        
        while True:
            client = _new_client()
            page = client.get(
                E_TRIPS, sDate=sDate, eDate=eDate,
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

        '''for tur in my_items:
                delivery = _safe_get_dict(tur, 'delivery')
                weight += _safe_get(delivery, 'totalLivingWeight')
                price += _safe_get(delivery, 'totalPriceForFisher')
                fuel += _safe_get(tur, 'fuelConsumption')
                distance += _safe_get(tur, 'distance')'''
        
        #####################################################################
        # Collect data from trips in the reference group in the period
        #####################################################################
        offset = 0
        all_items: List[Dict[str, Any]] = []

        while True:
            client = _new_client()
            page = client.get(
                E_TRIPS, sDate=sDate, eDate=eDate,
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

        '''for tur in all_items:
            delivery = _safe_get_dict(tur, 'delivery')
            av_Weight += _safe_get(delivery, 'totalLivingWeight')
            av_Price += _safe_get(delivery, 'totalPriceForFisher')
            #fuel += _safe_get(tur, 'fuelConsumption')
            #distance += _safe_get(tur, 'distance')

        av_Weight = av_Weight / len(gd.vesselRefIds)
        av_Price = av_Price / len(gd.vesselRefIds)'''

        '''myCatchArray.append(weight / 1000)
        avCatchArray.append(av_Weight / 1000)
        myCatchValueArray.append(price / 1000 / 1000)
        avCatchValueArray.append(av_Price / 1000 / 1000)'''

        returnElement.append([sDate, eDate, my_items, all_items])
    
    return noVessels(all_items), returnElement



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
