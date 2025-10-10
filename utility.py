

import matplotlib.pyplot as plt
import numpy as np

def splitCatchLocation(field_text):
    c_locs = []
    for loc_r in field_text.split('\n'):
        for loc_c in loc_r.split(','):
            loc = loc_c.strip()
            if loc != "": c_locs.append(loc)
    return c_locs

def emptyArrToAlle(arrgroup):
    if len(arrgroup) == 0:
        return ["Alle"]
    else:
        return arrgroup

# Get a list of end dates based on enddate, aggregated number of months and number of periods in calulations
def getDatesArray(eDate, span, periods):
        endDateArray = []   # holds the end dates for all requests
        startDateArray = [] # holds the start dates for all requests
        dateArray = []

        for m in reversed(range(0,periods)):
                endDateArray.append(eDate.addMonths(-m*span))

        for d in endDateArray:
                startDateArray.append(d.addMonths(-span))   

        dateArray.append(startDateArray)
        dateArray.append(endDateArray)  

        return dateArray


def monthsBetweenQdates(start_date, end_date) -> int:
    """
    Calculates the number of calendar months between two QDate objects.
    This method provides a more accurate count of full and partial months spanned.
    """
    if start_date > end_date:
        start_date, end_date = end_date, start_date # Ensure start_date is earlier

    months = 0
    current_date = start_date # Create a mutable copy

    while current_date <= end_date:
        months += 1
        current_date = current_date.addMonths(1)
        # Handle cases where addMonths might jump past the end_date due to day differences
        if current_date > end_date and current_date.day() != end_date.day() and current_date.month() == end_date.month():
            # If we've passed the end_date but are in the same month, we still count that month
            break 
    return months -1 # Subtract 1 because the loop counts the starting month as well


def plot(x, y11, y21, title, xlabel, ylabel):
        y1 = y11[1: len(y11)]
        y2 = y21[1: len(y21)]
        width = 0.25
        dx = np.arange(len(x))
        xT = [n.toPython() for n in x]
        xl = np.array(xT)
        xf = [n.strftime("%m-%Y") for n in xl]          # format date label
        
        plt.figure()
        plt.bar(dx - width/2, y1, width = width, label = "Min båt", color='red')
        plt.bar(dx + width/2, y2, width = width, label = "Gjennomsnitt", color = 'blue')
        plt.title(title)
        plt.xlabel(xlabel)
        plt.xticks(dx, labels=xf)
        plt.ylabel(ylabel)
        plt.legend()
        #plt.grid(True)

        plt.show()

def noVessels(dict):      
        idList = []
        for v in dict:
                if (v['fiskeridirVesselId'] not in idList):
                       idList.append(v['fiskeridirVesselId'])
                      
        return len(idList)

# Get the Norwegian name of specified length group
def nlg(lg):
        match lg:
                case 'Unknown': return 'ukjent'
                case 'UnderEleven': return '< 11 m'
                case  'ElevenToFifteen': return '11-15 m'
                case 'FifteenToTwentyOne': return '15-21 m'
                case 'TwentyTwoToTwentyEight': return '22-28 m'
                case 'TwentyEightAndAbove': return '> 28 m'

def findMainSpecie(dict):
        idList = []
        for v in dict:
                #if (v['fiskeridirVesselId']['catches']['speciesGroupId'] not in idList):
                hauls = v['hauls']
                #print(hauls)
                for w in hauls:                       
                        catch = w['catches']
                        #print(catch)
                        for y in catch:
                                specie = y['speciesGroupId']
                                idList.append(specie)

                
       # print (idList)
        return idList

