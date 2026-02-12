
#from KPI import*
import json
import csv
from PySide6.QtCore import QDate
import pandas as pd
from typing import Dict, Any
import os
import logging
import pdfExt



def createJsonItem(kpi_data):
        data = {}
        data['vesselName'] =kpi_data.vesselId
        data['callSign'] = ""
        data['numberOfRefVessels'] = kpi_data.nVessels
        data['group'] = kpi_data.lengthG
        data['gear'] = kpi_data.gearG
        data['specie'] = kpi_data.specG
        data['aggregatedMonths'] = kpi_data.span
        data['NumberOfPeriods'] = kpi_data.noPeriods

        dataSetName = []        # array with names of dataset
        for array in kpi_data.dataArray:
            dataSetName.append(array[0])
            array.pop(0)        # remove first item from array

        noItems = len(kpi_data.dataArray)
        itemIndex = list(range(0, noItems))             # list of item indexes
        noDataPoints = len(kpi_data.dataArray[0])       
        pointsIndex = list(range(0, noDataPoints))      # list of dataPoint indexes

        jsonArray = []
        startDates= kpi_data.datesArray[0]
        endDates= kpi_data.datesArray[1]
        for pIx in pointsIndex:
            jsonLine = {'startDate': startDates[pIx].toString('dd-MM-yyyy'), 'endDate':  endDates[pIx].toString('dd-MM-yyyy')}
            for iIx in itemIndex:
                jsonLine[dataSetName[iIx]] = kpi_data.dataArray[iIx][pIx]

            jsonArray.append(jsonLine)

        data['dataArray'] = jsonArray

        return data


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
        
#def json_to_pandas_csv(json_data: Dict[Any, Any], output_file: str, flatten: bool = True) -> None:
    """
    Convert JSON response to CSV file using pandas DataFrame

    Args:
        json_data: JSON response data as dictionary
        output_file: Output CSV file path/name
        flatten: Whether to flatten nested JSON structures (default: True)
    """
    ''' try:
        # Convert JSON to DataFrame
        df = pd.json_normalize(json_data) if flatten else pd.DataFrame(json_data)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # Write to CSV, handle encoding for Norwegian characters
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"CSV file saved: {output_file}")

    except Exception as e:
        print(f"Error writing CSV file: {str(e)}")
        print("end")'''

    
def getKeys(jsonData):
   # data = json.loads(jsonData)

    # Get all keys
    dArr = jsonData['dataArray']
    jsonData.pop('dataArray')
    keys1 = jsonData.keys()      #keys linje 1
    keys2 = dArr[0].keys()   #keys linje 2
        
    
   # print(list(keys)) 
    return keys1, keys2, dArr

    
def json_to_csv(jsonData, toCsvFile):
    keys1, keys2, dataArray = getKeys(jsonData)
    
    try:
        with open(toCsvFile, "w") as f:
            for key in keys1:
                print(key, ',', end='', file = f)
            print(file=f)

            for key in keys1:
                val = jsonData[key]       
                print(val,',', end='', file = f)   
            print(file=f)
            print(file=f)
            
            for key in keys2:
                print(key,',', end='', file = f)
            print(file=f)

            for item in dataArray:
                for key in keys2:
                    val = item[key]
                    print(val,',', end='', file = f)
                print(file=f)
        logging.info(f"CSV file saved: {toCsvFile}")

    except Exception as e:
        logging.error(f"Error writing CSV file: {str(e)}")


 #----------------------- PDF Report-------------------------------------------------------

def createPdfDoc(filename, plotFileName):
    pdf = pdfExt.PDF() 
    #filename = 'tuto2.pdf'
    '''fExt = fName.rsplit('.')
    pdfName = fName.replace(fExt[1], 'pdf')
    filename = testDir + "/" + pdfName        #Test result PDF name'''

    #y_pos = pdf.printImage2('org.png', 'box.png')  
    y_pos = pdf.printImage(plotFileName)  
    #pdf.set_y(y_pos)

    #pdf.printHeadLine('Nummer', 'Dekning %', 'Type', 'Beskrivelse', 'Plasttype', 'Forurensning') 

    '''for m in classified_masks:
        #if method == "SAM":
        areaString = f'{(m["area"] / size * 100):.1f}'
        #else:
        #  areaString = 'Null'
    
        Plastic = 'PE'
        pdf.printObjectLine(str(m['id']), areaString, m['class'], m['description'], Plastic, str(m['pollution']), m['color'])'''

    pdf.output(filename)

    # -------------------------------------------------
