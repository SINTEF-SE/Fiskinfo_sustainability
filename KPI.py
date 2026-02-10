from utility import*
import api_requests as ep
from collections import Counter
import reports as r
from PySide6.QtCore import QDate, QDateTime


PRICE_DIFF = 5          # approximate price difference between autodiesel and marine gas oil (MGO) in NOK

def kpi_01(gd, toPngFile):
    # Get Norwegian name of length group
    norskLgroup = "["
    if len(gd.lengthG) == 0:
        norskLgroup += "Alle"
    else:
        for lg in gd.lengthG: norskLgroup += nlg(lg) + ","
    norskLgroup += "]" 
    
    #Calculate list of end dates for all periods
    #dList = sliWin(eDate, span, periods)

    # get eeio for all sliding windows
    myEeoiArray = ['EEOI']
    avEeoiArray = ['Gj.snitt EEOI']
    startDateList = gd.datesArray[0]
    endDateList = gd.datesArray[1]
    m = 0
    for sDate in startDateList:     
        eeoi = 1000*ep.get_request(ep.av_eeoi, sDate, endDateList[m], lengthG = gd.lengthG, gearG = gd.gearG, specG = gd.specG, locationG = gd.locG, myVessel = True)
        myEeoiArray.append(eeoi)
        eeoi = 1000*ep.get_request(ep.av_eeoi, sDate, endDateList[m], lengthG = gd.lengthG, gearG = gd.gearG, specG= gd.specG, locationG = gd.locG, myVessel = False)
        avEeoiArray.append(eeoi)
        m += 1

    gd.dataArray.append(myEeoiArray)
    gd.dataArray.append(avEeoiArray)
    
    print("myEeoi array: ", myEeoiArray)
    print("AvEeoi array: ", avEeoiArray)

    # create title for plot
    span = monthsBetweenQdates(startDateList[0], endDateList[0])
    title = "KPI-01: EEOI [g CO2 /(fangst*nm)] aggregert over {months} måneder\nLengde: {vGroup}, Redskap: {gGroup}".format(months = span, vGroup = norskLgroup, gGroup = gd.gearG)
    plot(endDateList, myEeoiArray,avEeoiArray, title, "{antall} båter i referansegruppen".format(antall = gd.nVessels), fName = toPngFile)


def kpi_02(gd, toPngFile):
    # Get Norwegian name of lenght group
    norskLgroup = "["
    if len(gd.lengthG) == 0:
        norskLgroup += "Alle"
    else:
        for lg in gd.lengthG: norskLgroup += nlg(lg) + ","
    norskLgroup += "]" 

    #Calculate list of end dates for all periods
    #dList = sliWin(eDate, span, periods)

    # get fui for all sliding windows
    myFuiArray = ['FUI']
    avFuiArray = ['Gj.snitt FUI']
    startDateList = gd.datesArray[0]
    endDateList = gd.datesArray[1]
    m = 0
    for sDate in startDateList:     
        fui = 1000*ep.get_request(ep.av_fui, sDate, endDateList[m], lengthG = gd.lengthG, gearG = gd.gearG, specG = gd.specG, locationG = gd.locG, myVessel = True)
        myFuiArray.append(fui)
        fui = 1000*ep.get_request(ep.av_fui, sDate, endDateList[m], lengthG = gd.lengthG, gearG = gd.gearG, specG= gd.specG, locationG = gd.locG, myVessel = False)
        avFuiArray.append(fui)
        m += 1

    gd.dataArray.append(myFuiArray)
    gd.dataArray.append(avFuiArray)

    print("myFui array: ", myFuiArray)
    print("AvFui array: ", avFuiArray)

    # create title for plot
    span = monthsBetweenQdates(startDateList[0], endDateList[0])
    title = "KPI-02: FUI [g CO2 /fangst] aggregert over {months} måneder\nLengde: {vGroup}, Redskap: {gGroup}".format(months = span, vGroup = norskLgroup, gGroup = gd.gearG)
    plot(endDateList, myFuiArray,avFuiArray, title, "{antall} båter i referansegruppen".format(antall = gd.nVessels), fName = toPngFile)


def kpi_03_04(gd):
    toPngFile03 = "output/kpi03"
    toPngFile04 = "output/kpi04"

    # Get Norwegian name of lenght group
    norskLgroup = "["
    if len(gd.lengthG) == 0:
        norskLgroup += "Alle"
    else:
        for lg in gd.lengthG: norskLgroup += nlg(lg) + ","
    norskLgroup += "]" 

    # get values for all sliding windows
    myRevPerTonWeightArray = ['Netto fortjeneste per tonn fisk']
    avRevPerTonWeightArray = ['Gj.snitt Netto fortjeneste per tonn fisk']
    myRevPerHourArray = ['Netto fortjeneste per time']
    avRevPerHourArray = ['Gj.snitt Netto fortjeneste per time']
    startDateList = gd.datesArray[0]
    endDateList = gd.datesArray[1]
    m = 0
    for sDate in startDateList:   
        dict = ep.get_ssb_request(ep.price, sDate, sDate, info_log=False, csvFile ="", appendCSV=False)
        priceArray = dict['value']  
        price = priceArray[0] - PRICE_DIFF       # subract NOK 5 from diesel price
        dict = ep.get_request(ep.average, sDate, endDateList[m], lengthG = gd.lengthG, gearG = gd.gearG, specG = gd.specG, locationG = gd.locG, myVessel = True)
        catchValPerFuel = dict['catchValuePerFuel'] 
        weightPerFuel = dict['weightPerFuel']
        weightPerHour = dict['weightPerHour']
        myRevPerTonWeightArray.append((catchValPerFuel - price)/(weightPerFuel)*1000)
        myRevPerHourArray.append((catchValPerFuel - price)*weightPerFuel/weightPerHour)
        dict = ep.get_request(ep.average, sDate, endDateList[m], lengthG = gd.lengthG, gearG = gd.gearG, specG = gd.specG, locationG = gd.locG, myVessel = False)
        avCatchValPerFuel = dict['catchValuePerFuel'] 
        avWeightPerFuel = dict['weightPerFuel']
        avWeightPerHour = dict['weightPerHour']
        avRevPerTonWeightArray.append((avCatchValPerFuel - price)/(avWeightPerFuel)*1000)
        avRevPerHourArray.append((avCatchValPerFuel - price)*avWeightPerFuel/avWeightPerHour)
        m += 1
        
    gd.dataArray.append(myRevPerTonWeightArray)
    gd.dataArray.append(avRevPerTonWeightArray)
    gd.dataArray.append(myRevPerHourArray)
    gd.dataArray.append(avRevPerHourArray)
        
    # create title for plot
    span = monthsBetweenQdates(startDateList[0], endDateList[0])
    title = "KPI-03: Rev. per Ton [NOK / Tonn] aggregert over {months} måneder\nLengde: {vGroup}, Redskap: {gGroup}".format(months = span, vGroup = norskLgroup, gGroup = gd.gearG)
    plot(endDateList, myRevPerTonWeightArray, avRevPerTonWeightArray, title, "{antall} båter i referansegruppen".format(antall = gd.nVessels), fName = toPngFile03)

    title = "KPI-04: Rev. per Hour [NOK / time] aggregert over {months} måneder\nLengde: {vGroup}, Redskap: {gGroup}".format(months = span, vGroup = norskLgroup, gGroup = gd.gearG)
    plot(endDateList, myRevPerHourArray, avRevPerHourArray, title, "{antall} båter i referansegruppen".format(antall = gd.nVessels), fName = toPngFile04)


def kpi_05(gd, toPngFile):
    toPngFile05_1 = "output/kpi05_1"
    
    # Get Norwegian name of lenght group
    norskLgroup = "["
    if len(gd.lengthG) == 0:
        norskLgroup += "Alle"
    else:
        for lg in gd.lengthG: norskLgroup += nlg(lg) + ","
    norskLgroup += "]" 

    # get values for all sliding windows
    myCatchArray = ['Fangst i tonn']
    myCatchValueArray = ['Fangstverdi']
    avCatchArray = ['Gj.snitt fangst i tonn']
    avCatchValueArray = ['Gj.snitt fangstverdi']
    startDateList = gd.datesArray[0]
    endDateList = gd.datesArray[1]
    m = 0
    for sDate in startDateList:      
        dict = ep.get_request(ep.average, sDate, endDateList[m], lengthG = gd.lengthG, gearG = gd.gearG, specG = gd.specG, locationG = gd.locG, myVessel = True)
        catchWeight = dict['weightPerFuel'] * dict['fuelConsumption'] /1000
        myCatchArray.append(catchWeight)
        catchValue = dict['catchValuePerFuel'] * dict['fuelConsumption'] /1000
        myCatchValueArray.append(catchValue)
        dict = ep.get_request(ep.average, sDate, endDateList[m], lengthG = gd.lengthG, gearG = gd.gearG, specG = gd.specG, locationG = gd.locG, myVessel = False)
        catchWeight = dict['weightPerFuel'] * dict['fuelConsumption'] /1000
        avCatchArray.append(catchWeight)
        catchValue = dict['catchValuePerFuel'] * dict['fuelConsumption'] /1000
        avCatchValueArray.append(catchValue)
        m += 1
        
    gd.dataArray.append(myCatchArray)
    gd.dataArray.append(avCatchArray)
    gd.dataArray.append(myCatchValueArray)
    gd.dataArray.append(avCatchValueArray)
    
    print("myCatch array: ", myCatchArray)
    print("myCatchValue array: ", myCatchValueArray)
    print("avCatch array: ", avCatchArray)
    print("avCatchValue array: ", avCatchValueArray)

    '''# create titles for two plots
    title1 = "KPI-05: Total fangst i 1000 tonn over {months} måneder".format(months = span)
    title2 = "KPI-05: Total fangstverdi i kNOK over {months} måneder".format(months = span)
    plot(dList, myCatchArray,avCatchArray, title1, "{antall} båter i referansegruppen".format(antall = nVessels), "1000 Tonn")
    plot(dList, myCatchValueArray,avCatchValueArray, title2, "{antall} båter i referansegruppen".format(antall = nVessels), "kNOK")'''

    # create title for plot
    span = monthsBetweenQdates(startDateList[0], endDateList[0])
    title = "KPI-05: Årlig fangst [Tonn / År] aggregert over {months} måneder\nLengde: {vGroup}, Redskap: {gGroup}".format(months = span, vGroup = norskLgroup, gGroup = gd.gearG)
    plot(endDateList, myCatchArray, avCatchArray, title, "{antall} båter i referansegruppen".format(antall = gd.nVessels), fName = toPngFile)
    title = "KPI-05: Årlig fangstverdi [NOK / År] aggregert over {months} måneder\nLengde: {vGroup}, Redskap: {gGroup}".format(months = span, vGroup = norskLgroup, gGroup = gd.gearG)
    plot(endDateList, myCatchValueArray, avCatchValueArray, title, "{antall} båter i referansegruppen".format(antall = gd.nVessels), fName = toPngFile05_1)


## Utility functions  
# Get total number of vessels in a gear group and lenght group (and specied group) within specified dates
def getTotalVessels(request, sDate, eDate, lengthG, gearG, specG, locG):
    
    offset = 0
    nItems = 100
    allItems = []

    while (nItems == 100):
        print('request:', request, 'sDate:', sDate, 'eDate:', eDate, 'lengthG:', lengthG, 'gearG:', gearG, 'specG', specG, 'location', locG)
        itemDict = ep.get_request(request, sDate, eDate, lengthG = lengthG, gearG = gearG, specG = specG, locationG = locG, limit = 100, offset = offset)
        if itemDict != 0:
            allItems += itemDict
        nItems = len(itemDict)
        offset += 100

    print("Antall turer funnet: ", len(allItems))
    nVessels = noVessels(allItems)
    return nVessels


# get main specie for a my vessel within specified dates (should be changed to use landings instead)
# Not used
def getMainSpecie(request, sDate, eDate, lengthG, gearG, specG, locG):
    
    offset = 0
    nItems = 100
    allItems = []

    while (nItems == 100):
        itemDict = ep.get_request(request, sDate, eDate, lengthG = lengthG, gearG = gearG, specG = specG, locationG = locG, limit = 100, offset = offset, myVessel = True)
        allItems += itemDict
        nItems = len(itemDict)
        offset += 100

    print("Antall turer funnet: ", len(allItems))
    mainSpecieList = findMainSpecie(allItems)
    counts = Counter(mainSpecieList)

    mci_tuple = counts.most_common(1)
    mci = mci_tuple[0][0]

    print("Flest arter: ", mci)

    return mci