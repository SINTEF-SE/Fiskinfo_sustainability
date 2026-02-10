
import matplotlib.pyplot as plt
import numpy as np
from PySide6.QtCore import QDate
import datetime

# split catch location text into list of locations based on comma and line breaks
def splitCatchLocation(field_text):
    c_locs = []
    for loc_r in field_text.split('\n'):
        for loc_c in loc_r.split(','):
            loc = loc_c.strip()
            if loc != "": c_locs.append(loc)
    return c_locs

# If the group array is empty, return an array with "Alle" for the title plot
def emptyArrToAlle(arrgroup):
    if len(arrgroup) == 0:
        return ["Alle"]
    else:
        return arrgroup

# Get a group of months date between two dates for the haul API
def getMonthTimestamps(start_qdate, end_qdate):
    """
    Returns a list of UTC (Zulu) timestamps in milliseconds for each month between start_qdate and end_qdate (inclusive).
    """
    timestamps = []
    current = QDate(start_qdate.year(), start_qdate.month(), 1)
    end = QDate(end_qdate.year(), end_qdate.month(), 1)
    while current <= end: # only add last month once
        dt = datetime.datetime(current.year(), current.month(), current.day(), tzinfo=datetime.timezone.utc)
        timestamps.append(dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z')
        current = current.addMonths(1)
    return timestamps

# Get a list of end dates based on enddate, aggregated number of months and number of periods in calulations
def getDatesArray(eDate, gd):
        endDateArray = []   # holds the end dates for all requests
        startDateArray = [] # holds the start dates for all requests
        dateArray = []

        for m in reversed(range(0,gd.noPeriods)):
                endDateArray.append(eDate.addMonths(-m*gd.span))

        for d in endDateArray:
                startDateArray.append(d.addMonths(-gd.span))   

        dateArray.append(startDateArray)
        dateArray.append(endDateArray)  

        gd.datesArray = dateArray


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


def plot(x, y11, y21, title, xlabel, fName = "", show = False):
        ylabel = y11[0]
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
        if (show):         
                plt.show()
        if (fName != ""):
                plt.savefig(fName) 
        plt.close()

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

