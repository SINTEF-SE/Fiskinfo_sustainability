import requests
import logging

from requests import get
from requests import post
import json
from PySide6.QtCore import QDate
from datetime import datetime, timezone
import pandas as pd
from typing import Dict, Any
import os



#app_Token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IkNCMDJGMDMzREVGMUYwOTc3RDQxNjEyRTYwQTM1RDI2IiwidHlwIjoiYXQrand0In0.eyJpc3MiOiJodHRwczovL2lkLmJhcmVudHN3YXRjaC5ubyIsIm5iZiI6MTc1MDY2NDYxMCwiaWF0IjoxNzUwNjY0NjEwLCJleHAiOjE3NTA2NjgyMTAsImF1ZCI6ImFwaSIsInNjb3BlIjpbIm9wZW5pZCIsImFwaSJdLCJhbXIiOlsicHdkIl0sImNsaWVudF9pZCI6ImZoZi1kYXRhZmFuZ3N0Iiwic3ViIjoiMGIzZGNlN2YtMjMzYS00NDUwLWE4ODItYTY5ZTA2ZWE0N2U0IiwiYXV0aF90aW1lIjoxNzUwMzQwMDk2LCJpZHAiOiJsb2NhbCIsInByZWZlcnJlZF91c2VybmFtZSI6ImZpc2tpbmZvLm5vcmRAZ21haWwuY29tIiwic2lkIjoiNEZBMjI0MzBCOURFNzVENDlENEE4QjlBRDBBNDg1Q0QifQ.AWIfRxrPi_up1uE2HZzhdpJiYYYS96itSF8Xp2t7OdqAu3z32AMG8CN3Ezfhr8kF460GLWBjJb_JTwVA4iI86Vrd5Zvu16nKfdfX7SXgkSTyBEv4VBxf9tw7ExYqVkZv-CoxZm4LfcQmZKS1uYzNza_p9N9BcjYigH9A3BrUKSsxIvD2Fj5Y7cxy9niKiY2iLgOv0ZpCHweSeu1TpliJuqNk2ma1YFeNw5Kh_6z2Ke_EOV257BVJia7PnpZkRGdgeA0AHsNJdwK45eD2sKMBRS3l5MU7k0aMjuFCxIwlXd6cvPj-AoU9ALdR5yha8T78uozNgFvYCMtqQ8a8aIw9oQ"
app_Token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IkNCMDJGMDMzREVGMUYwOTc3RDQxNjEyRTYwQTM1RDI2IiwidHlwIjoiYXQrand0In0.eyJpc3MiOiJodHRwczovL2lkLmJhcmVudHN3YXRjaC5ubyIsIm5iZiI6MTc1MTQ1MjgxMywiaWF0IjoxNzUxNDUyODEzLCJleHAiOjE3NTE0NTY0MTMsImF1ZCI6ImFwaSIsInNjb3BlIjpbIm9wZW5pZCIsImFwaSJdLCJhbXIiOlsicHdkIl0sImNsaWVudF9pZCI6ImZoZi1kYXRhZmFuZ3N0Iiwic3ViIjoiMGIzZGNlN2YtMjMzYS00NDUwLWE4ODItYTY5ZTA2ZWE0N2U0IiwiYXV0aF90aW1lIjoxNzUxMjgwNTg3LCJpZHAiOiJsb2NhbCIsInByZWZlcnJlZF91c2VybmFtZSI6ImZpc2tpbmZvLm5vcmRAZ21haWwuY29tIiwic2lkIjoiNUI0NTE2RDc2NUJDMTk3MjRFOUFDQUYxMzJCQ0VEQUQifQ.xYIKuLmqQrYPauo3gSdQeBEnBIMbMajPAXxtq0zQzc3RRxN9f07b-ZerRNE2Ts2VnDn9EH_5SNqy8uSAD0TDVaQcwIUOjcR2_FUC0W1ZcRMjiPXOfPYGZ5_M6zdnhedvN0aylDEqQP8e3Aw7AeP2cyjac7eAVKaJjFsZZX6On7ffyWDisvcTIApmyAC5Vng4dvQF1-gc8BTTm0HJPJ1Nh4WkFKF3mi3FC224zLWDKBybUzwCJ1wyS5gASuYaiX4u7e58T4Fm6pEmsPMQl4qeyIeNdhD9LYK6OyfHVrCfA-EpcT40UrlTEej8Usr2xPg28cJj3cmnl1ElCIUHct7ZgQ"

#### REQUESTST #############
base_url = 'https://api.dev.datafangst.orcalabs.no/'

#### input data to request parameters ####################
## My boat
fiskdirId = 2013063493  # Gadus Njord
fiskdirIdGroup = [2013063493, 1999001513, 2011054408, 2018101213, 2000013339]    # Nordland Havfiske

# Vessel group
allVesselGroups = ["Unknown", "UnderEleven", "ElevenToFifteen", "FifteenToTwentyOne", "TwentyTwoToTwentyEight", "TwentyEightAndAbove"]

# Gear group
allGearGroups = ["Unknown", "Seine", "Net", "HookGear", "LobsterTrapAndFykeNets", "Trawl", "DanishSeine", "HarpoonCannon", "OtherGear", "FishFarming"]

# Species group
allSpeciesGroups = ["Unknown", "Capelin", "NorwegianSpringSpawningHerring", "OtherHerring", "Mackerel", "BlueWhiting", "NorwayPout", "Sandeels", "Argentines", "EuropeanSpratSea", "EuropeanSpratCoast", "MesopelagicFish", "TunaAndTunaishSpecies", "OtherPelagicFish", "AtlanticCod", "Haddock", "Saithe", "Gadiformes", "GreenlandHalibut", "GoldenRedfish", "Wrasse", "Wolffishes", "FlatFishOtherBottomFishAndDeepSeaFish", "SharkFish", "SkatesAndOtherChondrichthyes", "QueenCrab", "EdibleCrab", "RedKingCrab", "RedKingCrabOther", "NorthernPrawn", "AntarcticKrill", "CalanusFinmarchicus", "OtherShellfishMolluscaAndEchinoderm", "BrownSeaweed", "OtherSeaweed", "FreshWaterFish", "FishFarming", "MarineMammals", "Seabird", "Other"]

########## Define endpoint adresses ###############
## GEAR
gear = "v1.0/gear"
gear_groups = "v1.0/gear_groups"
gear_main_groups = 'v1.0/gear_main_groups'

## SPECIES
species = 'v1.0/species'
species_fdir = 'v1.0/species_fiskeridir'

## USER
user = 'v1.0/user'

##  FuelMeasurements
fuel_measurements = 'v1.0/fuel_measurements'

## VESSEL
vessels = 'v1.0/vessels'
fuel = 'v1.0/vessel/fuel'
live_fuel = 'v1.0/vessel/live_fuel'
vessel_benchmarks ='v1.0/vessels/benchmarks'

## TRIP
eeoi = 'v1.0/trip/benchmarks/eeoi'
av_eeoi = 'v1.0/trip/benchmarks/average_eeoi'
average = 'v1.0/trip/benchmarks/average'
trip_benchmarks = 'v1.0/trip/benchmarks'
trips = 'v1.0/trips'
avTripBench = 'v1.0/trip/benchmarks/average'
fui = 'v1.0/trip/benchmarks/fui'
av_fui = 'v1.0/trip/benchmarks/average_fui'

## HAUL
haul = 'v1.0/hauls'

# dictionary with responses
itemDict = json.loads('[]')

## PRIVATE METHODS ###########
# Set up response logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def __logResponse(response, *args, **kwargs):
    logging.info(f"Response URL: {response.url}")
    logging.info(f"Response Status Code: {response.status_code}, Content Length: {len(response.content)} bytes")
    #logging.info(f"Response Headers: {response.headers}")

session = requests.Session()
session.hooks['response'].append(__logResponse)

def __logRequests(time = "", url= "", header = "", params = "", response = None, log_file= "", sep = "\t"):
    if log_file != "":  # Append to csv file
        try:
            with open(log_file, 'a') as f:
                if not os.path.exists(log_file) or os.path.getsize(log_file) == 0: 
                    # Append header if file does not exist or is empty
                    f.write(f"UTCtime{sep}URL{sep}Header{sep}Params{sep}APIcall{sep}Status{sep}Bytes\n")
                f.write(f"{time}{sep}{url}{sep}{header}{sep}{params}{sep}{response.url}{sep}{response.status_code}{sep}{len(response.content)}\n")
        except IOError as e:
            logging.error(f"Error writing to file {log_file}: {e}")
    else:
        logging.info(f"Request URL: {url}")
        logging.info(f"Header: {header}")
        logging.info(f"Params: {params}")

# set the parameters for the query
def __getParams(requestType, sDate, eDate, lengthG, gearG, specG, locationG, limit, offset, myVessel = False):
    params = {}
    if gearG[0] == "All": gearG = [] #allGearGroups
    if lengthG[0] == "All": lengthG = [] # allVesselGroups
    if specG[0] == "All": specG = [] #allSpeciesGroups
    if locationG[0] == "All": locationG = []

    if sDate != QDate(): params["startDate"] = f"{sDate.toPython()}"+"T00:00:00.000Z"
    if eDate != QDate(): params["endDate"] = f"{eDate.toPython()}"+"T23:59:59.999Z"  # Include last day, when we use end of month or year we expect to include that day
    
    if requestType == trips or requestType == haul: 
        if len(lengthG) > 0: params["vesselLengthGroups[]"] = lengthG
        if myVessel: params["fiskeridirVesselIds[]"] = fiskdirId
        if len(gearG) > 0: params['gearGroupIds[]'] = gearG
        if len(specG) > 0: params['speciesGroupIds[]'] = specG
        if len(locationG) > 0: params['catchLocations[]'] = locationG
    else:
        if len(lengthG) > 0 : params["lengthGroup"] = lengthG
        if myVessel: params["vesselIds[]"] = fiskdirId 
        else: params["vesselIds[]"] = fiskdirIdGroup
        if len(gearG) > 0: params['gearGroups[]'] = gearG
        if len(specG) > 0: params['speciesGroupId'] = specG
        if len(locationG) > 0: params['catchLocations[]'] = locationG

    if limit != 0: params["limit"] = f"{limit}"
    if offset != 0: params["offset"] = f"{offset}"

    return params

# Not used or tested
def get_access_token():
    bw_client_id = 'fiskinfo.nord@gmail.com:fiskinfo.nord@gmail.com'
    bw_client_secret = 'ARd98hB68OtF'
    bw_auth_url = 'https://id.barentswatch.no/connect/token'

    response = requests.post(
        bw_auth_url,
        headers =  {"content-Type": "application/x-www-form-urlencoded"},
        data = {"client_id": bw_client_id, "Client_secret": bw_client_secret, "scope": "api", "grant_type": "client_credentials"}
    )

    app_Token = response.json()["access_token"]
    expires_in = response.json()["expires_in"]
    token_type = response.json()["token_type"]
    scope = response.json()["scope"]

    print(response.json())


### External methods ################

def json_to_pandas_csv(json_data: Dict[Any, Any], output_file: str, flatten: bool = True, append: bool = True) -> None:
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
        if append:
            df.to_csv(output_file, index=False, encoding='utf-8-sig', mode='a', header=not os.path.exists(output_file) or os.path.getsize(output_file) == 0)
        else:
            df.to_csv(output_file, index=False, encoding='utf-8-sig', mode='w', header=True)
        logging.info(f"CSV file saved: {output_file}")

    except Exception as e:
        logging.error(f"Error writing CSV file: {str(e)}")

# Splitting up the request into one that uses prepared url, header and params, suitable for replaying a stored request later, enabling replaying api- scenarios
def get_prepared_request(url="", header= None, params= None, debug = False, csvFile = "", ):
    global itemDict

    if url != "" and header is not None and params is not None:
        utc_time = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')  # ISO 8601 format with 'Z' for UTC
        try:
            response = session.get(url, headers=header, params=params)
            response.raise_for_status()
            __logRequests(utc_time, url, header, params, response, log_file="output/api_request_log.csv")   # log api requests to file
            if response.status_code >= 400:
                logging.error(f"AUTHORIZATION REQUIRED!!! Error code:{response.status_code}")
                return 0
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP error: {e}")
            return 0
        except requests.exceptions.RequestException as err:
            logging.error(f"Request exception: {err}")
            return 0

        # If the response is JSON, parse it
        try:
            data = response.json()
            if data != None and csvFile != "":  # Store json response to CSV file if file name provided
                json_to_pandas_csv(data, csvFile)

            if isinstance(data, float):
                if debug: logging.debug(f"Float data received: {data}")
                return data

            if data != None:
                itemDict = json.loads(response.text)
                if debug: logging.debug(f"#Objects: {len(itemDict)}\nContent (JSON): {json.dumps(data, indent=2)}")
                return itemDict
            else:
                logging.error("No payload data received")

        except requests.exceptions.JSONDecodeError as e:
            logging.error(f"Response is no valid JSON: {e}")
            logging.error(f"Content: {response.text}")
    else:
        logging.error(f"Missing url {url}, header {header} or parameters {params} needed for request")
    return 0

def get_request(request_type, sDate = QDate(), eDate = QDate(), lengthG = [], gearG = [], specG = [], locationG = [], limit = 0, offset = 0, myVessel = False, debug = False, csvFile =""):
    url = base_url + request_type
    header = {'accept': 'application/json'}   
    params = __getParams(request_type, sDate, eDate, lengthG, gearG, specG, locationG, limit, offset, myVessel)
    return get_prepared_request(url, header, params, debug, csvFile)
