
import json
import logging
from Options import*

#--------------------------------------------
# Helpers
#--------------------------------------------

def _getKeys(jsonData):
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


#------------------------------
# API
#------------------------------

def createJsonItem(kpi_data, nVessels, periodArray, dataList):
        
    """
    Creates a JSON‑ready dictionary containing vessel info and KPI values.

    - Extracts dataset names from dataDict (first element of each list)
    - Matches KPI values to each period in periodArray
    - Builds a list of rows, each with startDate, endDate, and KPI values

    Returns a dictionary with vessel metadata and a 'dataArray' list of rows.
    """

    #print(dataList)
    # ---- Static vessel metadata ----
    data = {
        "vesselName": ID_MY_VESSEL,
        "callSign": "",
        "numberOfRefVessels": nVessels,
        "group": kpi_data.lengthG,
        "gear": kpi_data.gearG,
        "specie": kpi_data.specG,
        "aggregatedMonths": kpi_data.span,
        "NumberOfPeriods": kpi_data.noPeriods,
    }

    dataset_names = []
    cleaned_data = []

    for arr in dataList:
        dataset_names.append(arr[0])        # first element is the dataset name
        cleaned_data.append(arr[1:])        # The rest of the elements are data values

    # ---- Index arrays ----
    #keys = list(cleaned_data.keys())
    num_points = len(cleaned_data[0])       # The number of data point in each element, ie. the number of date spans
            
    # ---- Construct json data rows ----
    jsonArray = []
    for dateSpan in range(num_points):
        startDate = periodArray[dateSpan][0].toString('dd-MM-yyyy')
        endDate   = periodArray[dateSpan][1].toString('dd-MM-yyyy')

        row = {
            "startDate": startDate,
            "endDate": endDate
        }

        for i in range(len(dataset_names)):
            dataset_name = dataset_names[i]
            row[dataset_name] = cleaned_data[i][dateSpan]

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
    
    logging.info(f"JSON file saved: {jsonFile}")

    

def json_to_csv(jsonData, toCsvFile): 
    """
    Writes JSON‑style KPI data to a CSV file.

    - Writes top‑level metadata
    - Writes column headers for the KPI table
    - Writes each row from dataArray

    Saves the CSV to the given file path.
    """

    keys1, keys2, dataArray = _getKeys(jsonData)

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



