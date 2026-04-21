

from PySide6.QtCore import QDate
import datetime
#from mpl_toolkits.axes_grid1.anchored_artists import AnchoredText

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
def getDatesArray(gd):
        endDateArray = []   # holds the end dates for all requests
        startDateArray = [] # holds the start dates for all requests
        dateArray = []

        for m in reversed(range(0,gd.noPeriods)):
                endDateArray.append(gd.endDate.addMonths(-m*gd.span))

        for d in endDateArray:
                startDateArray.append(d.addMonths(-gd.span))   

        dateArray.append(startDateArray)
        dateArray.append(endDateArray)  

        gd.datesArray = dateArray



def getPeriodDates(gd):
        
        """
        Creates a list of date periods based on a given end date, the number of
        months in each period (gd.span), and the number of periods (gd.noPeriods).

        For each period:
        - The end date is set to the last day of the target month.
        - The start date is set to the first day of the month (span - 1) months earlier.
        - The period is stored as a tuple: (startDate, endDate)

        The final list is saved in gd.periodArray.
        """

        periodArray = []

        for m in reversed(range(0,gd.noPeriods)):
                endDate = gd.endDate.addMonths(-m*gd.span)
                endDate.setDate(endDate.year(), endDate.month(), endDate.daysInMonth())
                startDate = endDate.addMonths(-(gd.span-1))
                startDate.setDate(startDate.year(), startDate.month(), 1)
                newDate = (startDate, endDate)
                periodArray.append(newDate)

        return periodArray


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

def getLengthGroups(lengthG):
      df_lengthG = []
      
      for lg in lengthG:
            if lg == "< 11 m": df_lengthG.append("UnderEleven")
            if lg == "11-15 m": df_lengthG.append("ElevenToFifteen")
            if lg == "15-21 m": df_lengthG.append("FifteenToTwentyOne")
            if lg == "22-28 m": df_lengthG.append("TwentyTwoToTwentyEight")
            if lg == "> 28 m": df_lengthG.append("TwentyEightAndAbove")

      return df_lengthG

def getGearGroups(gearG):
      df_gearG = []
      
      for gear in gearG:
            if gear == "Not": df_gearG.append("Seine")
            if gear == "Garn": df_gearG.append("Net")
            if gear == "Krokredskap": df_gearG.append("HookGear")
            if gear == "Teine": df_gearG.append("LobsterTrapAndFykeNets")
            if gear == "Trål": df_gearG.append("Trawl")
            if gear == "Snurrevad": df_gearG.append("DanishSeine")
            if gear == "Harpun": df_gearG.append("HarpoonCannon")
            if gear == "Annet redskap": df_gearG.append("OtherGear")
            if gear == "Havbruk": df_gearG.append("FishFarming")

      return df_gearG

