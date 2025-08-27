# Sustainability_Report

This python program is used to test the [API from Datafangst](https://api.dev.datafangst.orcalabs.no/swagger-ui/#/) and to produce data used to create sustainability reports. The data output is made availbale in json and xml files, and a graphs are produced to visualise the data.

Before running the program, ``PySide6`` and ``MatplotLib`` must be installed on the system

## Python files

``Main.py``         - Initialises the application window   
``gui.py``          - Sets up the graphical user interface using PySide6   
``api_requests.py`` - Implements some of the available API get requests   
``KPI.py``          - Implements the different KPIs as defined in the specification and outputs graphics, json and xml files   
``reports.py``      - Produces reports by for different user groups by combining KPI calls   
``utility.py``      - Includes some utiulity methods used during calculations   

## GUI

The GUI is made using PySide6. There are several input parameters in the GUI:

#### Input data for API calls
**Start dato and Stopp dato:** These are used in some of the API calls, check the API documentation for which one. For KPI calculations, only the Stopp dato is used.   
**Lengdegruppe:** This is a dropdown menu to select the specific length group used by some of the API calls.   
**Redskapsgruppe:** This is a dropdown menu to select the specific gear group used by some of the API calls.   
**Artsgruppe:** This is a dropdown menu to selct the specific specie group used by some of the API calls.   
**Max antall:** Specifies the maximum number of items reported from the API call. The maximum number is 100, but can be set lower. It is used togehter with **Offset**. For instance, when requesting trips within a specific data span there may be several thousand trips, but only the first 100 will show. To get the others, use the API call repeatedly by increasing offset by 100 each time. If offset is not used, the first 100 trips will show, setting offset to 100 wil return the trips from 100-200, and so on.

#### Input data for KPI calculations
**Aggregert tidsperiode:** This is the number of months over which the KPI is calculated. Setting this to 3 will, for instance, calculate the EEOI over the last 3 months, where Stopp dato is the last month.   
**Antall perioder bakover i tid fra sluttdato:** This is the number of periods in the KPI calculations. For instance, setting this to 4 will calculate EEIO for the last year, splitting it into 4 periods of 3 months each.

#### Other input data
**Vis resultat:** This will print out the data returned by the API call. Not recommended if there are many items returned.   
**Mitt fartøy:** This will return data from my vessel only, for API calls that support this. See below for more information.   

## Other information

So far, authorisation is not implemented and used. To specify my vessel, you need to hard code the vessels ID into the ``api_requests.py``. The identifier is called ``fiskdirId`` and is a 9 digit number. At the moment, only the Id of Gadus Njord is used.

Debug printing: At the top of ``api_requests.py``, a parameter called ``printout`` is is used to tell if debug parameters should be printed out. Set to *false* if this is not neccessary, it will speed up the program. The debug output mainly shows the API calls and the parameters used in the calls.
