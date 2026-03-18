
#from KPI import*
import json
import csv
from PySide6.QtCore import QDate
import pandas as pd
from typing import Dict, Any
import os
import logging
import pdfExt




def createJsonItem(kpi_data, nVessels, periodArray, dataDict):
        
    """
    Creates a JSON‑ready dictionary containing vessel info and KPI values.

    - Extracts dataset names from dataDict (first element of each list)
    - Matches KPI values to each period in periodArray
    - Builds a list of rows, each with startDate, endDate, and KPI values

    Returns a dictionary with vessel metadata and a 'dataArray' list of rows.
    """

    # ---- Static vessel metadata ----
    data = {
        "vesselName": kpi_data.vesselId,
        "callSign": "",
        "numberOfRefVessels": nVessels,
        "group": kpi_data.lengthG,
        "gear": kpi_data.gearG,
        "specie": kpi_data.specG,
        "aggregatedMonths": kpi_data.span,
        "NumberOfPeriods": kpi_data.noPeriods,
    }

    dataset_names = []
    cleaned_data = {}

    for key, arr in dataDict.items():
        dataset_names.append(arr[0])     # first element is the dataset name
        cleaned_data[key] = arr[1:]      # values only

    # ---- Index arrays ----
    keys = list(cleaned_data.keys())
    num_points = len(cleaned_data[keys[0]])
            
    # ---- Construct json data rows ----
    jsonArray = []
    for idx in range(num_points):
        startDate = periodArray[idx][0].toString('dd-MM-yyyy')
        endDate   = periodArray[idx][1].toString('dd-MM-yyyy')

        row = {
            "startDate": startDate,
            "endDate": endDate
        }

        for i, key in enumerate(keys):
            dataset_name = dataset_names[i]
            row[dataset_name] = cleaned_data[key][idx]

        jsonArray.append(row)

    data["dataArray"] = jsonArray

    return data



def createJson(data, jsonFile):   
    """
    Writes the given data to a JSON file and also returns the JSON string.

    - Saves 'data' to the file path given by jsonFile (UTF‑8, pretty‑printed)
    - Returns the same data as a JSON string

    Useful when you need both a saved JSON file and the JSON content in memory.
    """
    
    json_data = json.dumps(data)
    with open(jsonFile, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    return json_data

    

def getKeys(jsonData):
    """
    Extracts the top‑level keys and the dataArray keys from a JSON‑like dict.

    Returns:
        keys1 : keys from the main metadata section
        keys2 : keys from the first row in dataArray
        dArr  : the full dataArray list
    """
    dArr = jsonData['dataArray']
    jsonData = jsonData.copy()      # avoid mutating caller's data
    jsonData.pop('dataArray')

    keys1 = jsonData.keys()
    keys2 = dArr[0].keys()

    return keys1, keys2, dArr



def json_to_csv(jsonData, toCsvFile): 
    """
    Writes JSON‑style KPI data to a CSV file.

    - Writes top‑level metadata
    - Writes column headers for the KPI table
    - Writes each row from dataArray

    Saves the CSV to the given file path.
    """

    keys1, keys2, dataArray = getKeys(jsonData)

    try:
        with open(toCsvFile, "w", encoding="utf-8") as f:

            # Write main metadata keys
            print(",".join(keys1), file=f)
            print(",".join(str(jsonData[k]) for k in keys1), file=f)
            print("", file=f)  # blank line

            # Write table header
            print(",".join(keys2), file=f)

            # Write table rows
            for item in dataArray:
                row = ",".join(str(item[k]) for k in keys2)
                print(row, file=f)

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
