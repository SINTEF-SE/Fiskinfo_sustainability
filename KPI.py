from utility import*
import api_requests as ep
from collections import Counter

def kpi_01(eDate, lengthG, gearG, specG, span, periods):
    # Get Norwegian name of lenght group
    norskLgroup = nlg(lengthG)
   
    #Calculate list of end dates for all periods
    dList = sliWin(eDate, span, periods)

    # get eeio for all sliding windows
    myEeoiArray = []
    avEeoiArray = []
    for mDate in dList:     
        eeoi = 1000*ep.get_request(ep.av_eeoi, mDate.addMonths(-span), mDate, lengthG = lengthG, gearG = gearG, specG = specG, myVessel = True)
        myEeoiArray.append(eeoi)
        eeoi = 1000*ep.get_request(ep.av_eeoi, mDate.addMonths(-span), mDate, lengthG = lengthG, gearG = gearG, specG= specG, myVessel = False)
        avEeoiArray.append(eeoi)

    # Calculate start date
    sDate = eDate.addMonths(-span*periods)
   
    # Find total number of vessels in in group
    nVessels = getTotalVessels(ep.trips, sDate, eDate, lengthG, gearG, specG = specG)
    
    print("myEeoi array: ", myEeoiArray)
    print("AvEeoi array: ", avEeoiArray)
    print ("Antall båter. ", nVessels)

    # create title for plot
    title = "KPI-01: EEOI [g CO2 /nm] aggregert over {months} måneder\nLengde: {vGroup}, Redskap: {gGroup}".format(months = span, vGroup = norskLgroup, gGroup = gearG)
    plot(dList, myEeoiArray,avEeoiArray, title, "{antall} båter i referansegruppen".format(antall = nVessels), "EEOI")


def kpi_05(eDate, lengthG, gearG, specG, span, periods):

    #Calculate list of end dates for all periods
    dList = sliWin(eDate, span, periods)

    # get values for all sliding windows
    myCatchArray = []
    myCatchValueArray = []
    avCatchArray = []
    avCatchValueArray = []
    for mDate in dList:      
        dict = ep.get_request(ep.average, mDate.addMonths(-span), mDate, lengthG = lengthG, gearG = gearG, myVessel = True)
        catchWeight = dict['weightPerFuel'] * dict['fuelConsumption'] /1000
        myCatchArray.append(catchWeight)
        catchValue = dict['catchValuePerFuel'] * dict['fuelConsumption'] /1000
        myCatchValueArray.append(catchValue)
        dict = ep.get_request(ep.average, mDate.addMonths(-span), mDate, lengthG = lengthG, gearG = gearG, myVessel = False)
        catchWeight = dict['weightPerFuel'] * dict['fuelConsumption'] /1000
        avCatchArray.append(catchWeight)
        catchValue = dict['catchValuePerFuel'] * dict['fuelConsumption'] /1000
        avCatchValueArray.append(catchValue)
        
    # calculate start date
    sDate = eDate.addMonths(-span*periods)

    # Find total number of vessels in in group
    nVessels = getTotalVessels(ep.trips, sDate, eDate, lengthG, gearG, specG = specG)
    
    print("myCatch array: ", myCatchArray)
    print("myCatchValue array: ", myCatchValueArray)
    print("avCatch array: ", avCatchArray)
    print("avCatchValue array: ", avCatchValueArray)
    print ("Antall båter. ", nVessels)

    # create titles for two plots
    title1 = "KPI-05: Total fangst i 1000 tonn over {months} måneder".format(months = span)
    title2 = "KPI-05: Total fangstverdi i kNOK over {months} måneder".format(months = span)
    plot(dList, myCatchArray,avCatchArray, title1, "{antall} båter i referansegruppen".format(antall = nVessels), "1000 Tonn")
    plot(dList, myCatchValueArray,avCatchValueArray, title2, "{antall} båter i referansegruppen".format(antall = nVessels), "kNOK")


## Utility functions  
# Get total number of vessels in a gear group and lenght group (and specied group) within specified dates
def getTotalVessels(request, sDate, eDate, lengthG, gearG, specG):
    
    offset = 0
    nItems = 100
    allItems = []

    while (nItems == 100):
        itemDict = ep.get_request(request, sDate, eDate, lengthG = lengthG, gearG = gearG, specG = specG, limit = 100, offset = offset)
        allItems += itemDict
        nItems = len(itemDict)
        offset += 100

    print("Antall turer funnet: ", len(allItems))
    nVessels = noVessels(allItems)
    return nVessels


# get main specie for a my vessel within specified dates (should be changed to use landings instead)
# Not used
def getMainSpecie(request, sDate, eDate, lengthG, gearG, specG):
    
    offset = 0
    nItems = 100
    allItems = []

    while (nItems == 100):
        itemDict = ep.get_request(request, sDate, eDate, lengthG = lengthG, gearG = gearG, specG = specG, limit = 100, offset = offset, myVessel = True)
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