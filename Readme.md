# Sustainability_Report

This python program is used to collect data used in sustainability reporting for the fishing fleet. It uses the [API from Datafangst](https://api.dev.datafangst.orcalabs.no/swagger-ui/#/) to produce the data, and the output is made availbale in json and xml files, and graphs are produced to visualise the data.

The following libraries are neccessary to run the program: ``PySide6``, ``MatplotLib`` and ``Numpy``.

## Python files

``Main.py``                 - Initialises the application window   
``gui.py``                  - Sets up the graphical user interface using PySide6  
``gui_helpers.py``         - Overriding classes for PySide
``KPI.py``                  - Implements the KPI calculations and some of the endpoints from the Datafangst API  
``kpi_worker.py``           - Runs the KPI calculations in a separate thread  
``datafangst_client.py``    - Implements get requests to the Datafangst API   
``reports.py``              - Produces JSON and CSV files of the calculated KPI's
``plots.py``                - Create plots of the selected KPIs
``plot_helpers.py``         - Implements the plot and specifies how it should look 
``utility.py``              - Includes some utiulity methods used during calculations   
``Endpoints.py``            - Specify the specific endpoints at Datafangst and SSB
``Options.py``              - Specify options for the GUI, like colors, output files ++

## GUI

The GUI is made using PySide6. There are several input parameters in the GUI:

### Input data for KPI calculations
**Sluttmåned:** 
The end month and year for the calculations. The KPI calculations are performed up to and including this month/year.

**Aggregert tidsperiode:** 
This is the aggregated number of months over which the KPI's are calculated. For instance, setting this to 12 will calculate the KPI's over the last year, ending at **Sluttmåned**.

**Antall perioder bakover i tid fra sluttdato:** 
This is the number of periods in the KPI calculations. For instance, if **Aggregert tidsperiode** is 12, setting this to 3 will calculate the KPI's for the last 3 years.

**Lengdegruppe:** 
This is a dropdown menu to select the specific vessel length group. More than one can be selected.

**Redskapsgruppe:** 
This is a dropdown menu to select the specific gear group. More than one can be selected. 

**Artsgruppe:** 
This is a dropdown menu to select the specific specie group. More than one can be selected. 

**Fangstfelt:** 
This is a text box where you can specify the specific catch area.

### KPI check boxes
There are several check boxes to select the type of KPI's to be calculated: 

**EEOI**
Calculates the EEOI in the periods.

**FUI** 
Calculates FUI in the period.

**Fangst og fangstverdi** 
Calculates the total catch and catch value in the period, as well as the average catch and catch value per trip.

**Drivstofforbruk**
Calculates the total fuel in the period and the average fuel per trip

**Drivstoffkostnad**
Calculates the total fuel costs in the periods, and the average costs per trip.

**Relativ fortjeneste** 
Calculates the average profit per kg catch and the average profit per hour in the period.

**CO2 utslipp** 
Calculates the total emitted CO2 in the period, the average CO2 per trip.

**Dager, timer, distanse** 
Calculates the average number of days and distance per trip.

**VSME**                    - 
Calculates the emitted CO2 per revenue as specified by VSME.

**Vis data for referansegruppe**
Check this if the data for a reference group shall be included in the reports.

### Data for testing the API endpoints

**Mitt fartøy**
Check this if you want data only for my vessel, otherwise you will get data for all vessels in the selected lenght- and gear groups

**Vis API respons**
Check this if you want to print out the complete response from the API call (may be a lot of data)

**Lagre API-data som CSV**
Not used

**Legge til data i filen** 
Not used

**Max antall responser**
Specifies the maximum number of items reported from the API call, default is 100, can be smaller but not higher.

## Output data
All produced data in terms of .png figures, JSON files and CSV files, and a PDF file with all .png figures collected, are stored in the output directory specified in ``Options.py``.

## Other information

The textbox will show the progress of the KPI calculations, and the output from API calls. 
So far, authorisation is not implemented and used. To specify my vessel, at the moment you need to hard code the vessels ID into the ``Options.py``. The identifier is called ``fiskdirId`` and is a 9 digit number. This is also true if you want to specify a specific reference group of vessels. The plan is to implement this selection into the GUI in the future.


