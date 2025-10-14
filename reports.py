
from KPI import*
import json
import csv
from PySide6.QtCore import QDate
import pandas as pd
from typing import Dict, Any
import os

class Output():
    def __init__(self, vesselId, group, gear, specie, location, span, periods):
        
        super().__init__()

        self.vesselId = vesselId
        self.lengthG = group
        self.gearG = gear
        self.specG = specie
        self.locG = location
        self.span = span
        self.noPeriods = periods
        self.dataArray = []     #create emty arry to be filled in by kpi measurements
                

    def createJsonItem(self):
        data = {}
        data['vesselName'] =self.vesselId
        data['callSign'] = ""
        data['numberOfRefVessels'] = self.nVessels
        data['group'] = self.lengthG
        data['gear'] = self.gearG
        data['specie'] = self.specG
        data['aggregatedMonths'] = self.span
        data['NumberOfPeriods'] = self.noPeriods

        dataSetName = []        # array with names of dataset
        for array in self.dataArray:
            dataSetName.append(array[0])
            array.pop(0)        # remove first item from array

        noItems = len(self.dataArray)
        itemIndex = list(range(0, noItems))             # list of item indexes
        noDataPoints = len(self.dataArray[0])       
        pointsIndex = list(range(0, noDataPoints))      # list of dataPoint indexes

        jsonArray = []
        startDates= self.datesArray[0]
        endDates= self.datesArray[1]
        for pIx in pointsIndex:
            jsonLine = {'startDate': startDates[pIx].toString('dd-MM-yyyy'), 'endDate':  endDates[pIx].toString('dd-MM-yyyy')}
            for iIx in itemIndex:
                jsonLine[dataSetName[iIx]] = self.dataArray[iIx][pIx]

            jsonArray.append(jsonLine)

        data['dataArray'] = jsonArray

        return data

    def createCsvItem(self, csvArray):
        for item in self.dataArray:
            item_line = ['01-12-2025', '01-12-2025', item]
            csvArray.append(item_line)

    def createCsvHeading(self, csvArray):
                 
        header1 = ['Vessel:', self.vesselId, 'CallSign:', "", 'Specie:', self.specie, 'Aggregated months:', self.span, 'Periods:', self.periods]
        csvArray.append(header1)
        line = [""]
        csvArray.append(line)
        header2 = []
        for array in self.dataArray:
            header2.append(array[0])
        
        csvArray.append(header2)


   

def jsonToCsv(json_data, csv_file):
    
    print(json_data)
    items = json_data['']
    print (items)
    csvf = open(csv_file, 'w')
    cw = csv.writer(csvf)
    c = 0
    data = []
    '''for rec in json_data:
        #Ed = rec['fiskeridir']
        data. append(rec)
        #print(data)'''

    for items in json_data:
        #print (items)
        '''if c == 0:

            # Writing headers of CSV file
            h = items.keys()
            cw.writerow(h)
            c += 1

        # Writing data of CSV file
        cw.writerow(items.values())'''

    print("CSV file written")
    csvf.close()


def createJson(data, jsonFile):
    
    json_data = json.dumps(data)
    #print(f"Content (JSON): {json_data}")

    with open(jsonFile, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    return json_data

def createJson(data, jsonFile):
    
    json_data = json.dumps(data)
    #print(f"Content (JSON): {json_data}")

    with open(jsonFile, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    return json_data

def createCsv(data, csvFile):
    #csvf = open(csvFile, 'w')
    #cw = csv.writer(csvf)
    #json_data = json.dumps(data)
    #print(f"Content (JSON): {json_data}")

    with open(csvFile, 'w', newline = '') as csvfile:
        cw = csv.writer(csvfile)
        cw.writerows(data)
        
def json_to_pandas_csv(json_data: Dict[Any, Any], output_file: str, flatten: bool = True) -> None:
    """
    Convert JSON response to CSV file using pandas DataFrame

    Args:
        json_data: JSON response data as dictionary
        output_file: Output CSV file path/name
        flatten: Whether to flatten nested JSON structures (default: True)
    """
    try:
        # Convert JSON to DataFrame
        df = pd.json_normalize(json_data) if flatten else pd.DataFrame(json_data)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # Write to CSV, handle encoding for Norwegian characters
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"CSV file saved: {output_file}")

    except Exception as e:
        print(f"Error writing CSV file: {str(e)}")
        print("end")

    

    
    
    