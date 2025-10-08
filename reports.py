
from KPI import*
import json
import csv
from PySide6.QtCore import QDate

class Output():
    def __init__(self, repType, vesselId, noVessels, specie, span, periods, dataArray):
        
        super().__init__()

        self.repType = repType
        self.vesselId = vesselId
        self.noVessels = noVessels
        self.specie = specie
        self.span = span
        self.periods = periods
        self.dataArray = dataArray

    def createJsonItem(self):
        data = {}
        data['type'] = self.repType
        data['vesselName'] =self.vesselId
        data['callSign'] = ""
        data['numberOfVessels'] = self.noVessels
        data['specie'] = self.specie
        data['aggregatedMonths'] = self.span
        data['periods'] = self.periods
        item_array = []
        for item in self.dataArray:
            item_array.append({'startDate': '01-12-2025', 'endDate': '01-12-2025', 'value': item})

        data['dataArray'] = item_array

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

def createCsv(data, csvFile):
    #csvf = open(csvFile, 'w')
    #cw = csv.writer(csvf)
    #json_data = json.dumps(data)
    #print(f"Content (JSON): {json_data}")

    with open(csvFile, 'w', newline = '') as csvfile:
        cw = csv.writer(csvfile)
        cw.writerows(data)
        
    
def createBankReport(eDate, lengthG, gearG, specG, locG, span, periods):
    expArray = []
    dateArray = getDatesArray(eDate, span, periods)
    for array in dateArray:
        expArray.append(array)

    eeoiArray = kpi_01(lengthG, gearG, specG, locG, dateArray)
    for array in eeoiArray:
        expArray.append(array)

    fuiArray = kpi_02(lengthG, gearG, specG, locG, dateArray)
    for array in fuiArray:
        expArray.append(array)
        
    item = Output('EEOI', 'Gadus  Njord', 1, "", 3, 4, expArray)
    print (expArray)
    #data = item.createJsonItem()
    csvArray = []
    item.createCsvHeading(csvArray)
    item.createCsvItem(csvArray)
    r.createCsv(csvArray, 'csvtestFile.csv')
    
    