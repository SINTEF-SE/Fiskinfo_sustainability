import requests
from requests import get
from requests import post
import json
from PySide6.QtCore import QDate
from datetime import date as dt

printout = True # Used to show debug printouts, set to false if not neccessary

#app_Token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IkNCMDJGMDMzREVGMUYwOTc3RDQxNjEyRTYwQTM1RDI2IiwidHlwIjoiYXQrand0In0.eyJpc3MiOiJodHRwczovL2lkLmJhcmVudHN3YXRjaC5ubyIsIm5iZiI6MTc1MDY2NDYxMCwiaWF0IjoxNzUwNjY0NjEwLCJleHAiOjE3NTA2NjgyMTAsImF1ZCI6ImFwaSIsInNjb3BlIjpbIm9wZW5pZCIsImFwaSJdLCJhbXIiOlsicHdkIl0sImNsaWVudF9pZCI6ImZoZi1kYXRhZmFuZ3N0Iiwic3ViIjoiMGIzZGNlN2YtMjMzYS00NDUwLWE4ODItYTY5ZTA2ZWE0N2U0IiwiYXV0aF90aW1lIjoxNzUwMzQwMDk2LCJpZHAiOiJsb2NhbCIsInByZWZlcnJlZF91c2VybmFtZSI6ImZpc2tpbmZvLm5vcmRAZ21haWwuY29tIiwic2lkIjoiNEZBMjI0MzBCOURFNzVENDlENEE4QjlBRDBBNDg1Q0QifQ.AWIfRxrPi_up1uE2HZzhdpJiYYYS96itSF8Xp2t7OdqAu3z32AMG8CN3Ezfhr8kF460GLWBjJb_JTwVA4iI86Vrd5Zvu16nKfdfX7SXgkSTyBEv4VBxf9tw7ExYqVkZv-CoxZm4LfcQmZKS1uYzNza_p9N9BcjYigH9A3BrUKSsxIvD2Fj5Y7cxy9niKiY2iLgOv0ZpCHweSeu1TpliJuqNk2ma1YFeNw5Kh_6z2Ke_EOV257BVJia7PnpZkRGdgeA0AHsNJdwK45eD2sKMBRS3l5MU7k0aMjuFCxIwlXd6cvPj-AoU9ALdR5yha8T78uozNgFvYCMtqQ8a8aIw9oQ"
app_Token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IkNCMDJGMDMzREVGMUYwOTc3RDQxNjEyRTYwQTM1RDI2IiwidHlwIjoiYXQrand0In0.eyJpc3MiOiJodHRwczovL2lkLmJhcmVudHN3YXRjaC5ubyIsIm5iZiI6MTc1MTQ1MjgxMywiaWF0IjoxNzUxNDUyODEzLCJleHAiOjE3NTE0NTY0MTMsImF1ZCI6ImFwaSIsInNjb3BlIjpbIm9wZW5pZCIsImFwaSJdLCJhbXIiOlsicHdkIl0sImNsaWVudF9pZCI6ImZoZi1kYXRhZmFuZ3N0Iiwic3ViIjoiMGIzZGNlN2YtMjMzYS00NDUwLWE4ODItYTY5ZTA2ZWE0N2U0IiwiYXV0aF90aW1lIjoxNzUxMjgwNTg3LCJpZHAiOiJsb2NhbCIsInByZWZlcnJlZF91c2VybmFtZSI6ImZpc2tpbmZvLm5vcmRAZ21haWwuY29tIiwic2lkIjoiNUI0NTE2RDc2NUJDMTk3MjRFOUFDQUYxMzJCQ0VEQUQifQ.xYIKuLmqQrYPauo3gSdQeBEnBIMbMajPAXxtq0zQzc3RRxN9f07b-ZerRNE2Ts2VnDn9EH_5SNqy8uSAD0TDVaQcwIUOjcR2_FUC0W1ZcRMjiPXOfPYGZ5_M6zdnhedvN0aylDEqQP8e3Aw7AeP2cyjac7eAVKaJjFsZZX6On7ffyWDisvcTIApmyAC5Vng4dvQF1-gc8BTTm0HJPJ1Nh4WkFKF3mi3FC224zLWDKBybUzwCJ1wyS5gASuYaiX4u7e58T4Fm6pEmsPMQl4qeyIeNdhD9LYK6OyfHVrCfA-EpcT40UrlTEej8Usr2xPg28cJj3cmnl1ElCIUHct7ZgQ"

#### REQUESTST #############
base_url = 'https://api.dev.datafangst.orcalabs.no/'

#### input data to request parameters ####################
## My boat
fiskdirId = 2013063493  # Gadus Njord

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

## HAUL
haul = 'v1.0/hauls'

# dictionary with responses
itemDict = json.loads('[]')

## PRIVATE METHODS ###########
# set the parameters for the query
def __getParams(requestType, sDate, eDate, lengthG, gearG, specG, limit, offset, myVessel = False):
    params = {}

    if gearG == "All": gearG = allGearGroups
    if lengthG == "All": lengthG = allVesselGroups
    if specG == "All": specG = allSpeciesGroups

    if sDate != QDate(): params["startDate"] = f"{sDate.toPython()}"+"T00:00:00Z"
    if eDate != QDate(): params["endDate"] = f"{eDate.toPython()}"+"T00:00:00Z"
    
    if requestType == trips or requestType == haul: 
        if lengthG != "": params["vesselLengthGroups[]"] = lengthG
        if myVessel: params["fiskeridirVesselIds[]"] = fiskdirId
        if gearG != "": params['gearGroupIds[]'] = gearG
        if specG != "": params['speciesGroupIds[]'] = specG
    else:
        if lengthG != "": params["lengthGroup"] = lengthG
        if myVessel: params["vesselIds[]"] = fiskdirId
        if gearG != "": params['gearGroups[]'] = gearG
        if specG != "": params['speciesGroupId'] = specG

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

def get_request(request_type, sDate = QDate(), eDate = QDate(), lengthG = "", gearG = "", specG = "", limit = 0, offset = 0, myVessel = False, show = False ):
    url = base_url + request_type
    header = {'accept': 'application/json'}   
    params = __getParams(request_type, sDate, eDate, lengthG, gearG, specG, limit, offset, myVessel)
    global itemDict

    if (printout):
        print("Requerst URL: ", url)
        print("Header: ", header)
        print("Params: ", params)

    # Send the request
    response = get(url, headers=header, params=params)
    if printout: print(response)

    if response.status_code == 404:
        print("AUTHORIZATION REQUIRED!!!")
        return
    # If the response is JSON, parse it
    try:
        data = response.json()
        if (isinstance(data, float)):
            if printout: print("data: ", data)
            return data

        if (data != None):
            itemDict = json.loads(response.text)
            if printout: print ("Antall objekt i siste respons: ", len(itemDict))
            if (show):
                json_formatted_str = json.dumps(data, indent=2)
                print(f"Content (JSON): {json_formatted_str}")
            return itemDict
        else:
            if printout: print("No payload data received")
            return 0
    except requests.exceptions.JSONDecodeError:
        print("Response is not valid JSON.")
        print(f"Content: {response.text}")

    