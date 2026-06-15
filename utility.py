


from typing import List


# split catch location text into list of locations based on comma and line breaks
def splitCatchLocation(field_text):
    c_locs = []
    for loc_r in field_text.split('\n'):
        for loc_c in loc_r.split(','):
            loc = loc_c.strip()
            if loc != "": c_locs.append(loc)
    return c_locs


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



def noVessels(dict):      
	idList = []
	for v in dict:
		if (v['fiskeridirVesselId'] not in idList):
			idList.append(v['fiskeridirVesselId'])
					
	return len(idList)

#--------------------------------------------------------------
# Translate vessel groups to norwegian
#--------------------------------------------------------------
def norsk_length_group(lengthG: List[str]) -> str:
    """Format Norwegian vessel length group label."""
    return f"[{', '.join(_nlg(lg) for lg in lengthG) if lengthG else 'Alle'}]"

# Get the Norwegian name of specified length group
def _nlg(lg):
        match lg:
                case 'Unknown': return 'ukjent'
                case 'UnderEleven': return '< 11 m'
                case  'ElevenToFifteen': return '11-15 m'
                case 'FifteenToTwentyOne': return '15-21 m'
                case 'TwentyTwoToTwentyEight': return '22-28 m'
                case 'TwentyEightAndAbove': return '> 28 m'


#----------------------------------------------------------------
# Translate norwegian length groups to english for the API calls
#----------------------------------------------------------------
def getLengthGroups(lengthG):
      df_lengthG = []
      
      for lg in lengthG:
            if lg == "< 11 m": df_lengthG.append("UnderEleven")
            if lg == "11-15 m": df_lengthG.append("ElevenToFifteen")
            if lg == "15-21 m": df_lengthG.append("FifteenToTwentyOne")
            if lg == "22-28 m": df_lengthG.append("TwentyTwoToTwentyEight")
            if lg == "> 28 m": df_lengthG.append("TwentyEightAndAbove")

      return df_lengthG

#----------------------------------------------------------------
# Translate norwegian gear groups to english for the API calls
#----------------------------------------------------------------
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

