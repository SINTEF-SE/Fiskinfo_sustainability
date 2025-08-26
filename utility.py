

import matplotlib.pyplot as plt
import numpy as np

# Get a list of end dates based on enddate, aggregated number of months and number of periods in calulations
def sliWin(eDate, span, periods):  
        endDateList = []          # holds the end dates for all requests

        for m in reversed(range(0,periods)):
                endDateList.append(eDate.addMonths(-m*span))

        #print(endDateList)   
        return endDateList

def plot(x, y1, y2, title, xlabel, ylabel):
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