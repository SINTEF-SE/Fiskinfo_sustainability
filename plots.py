from datetime import datetime
from plot_helpers import save_figs_to_pdf, plot
from reports import createJsonItem, createJson, json_to_csv
from Options import*

def plot_kpi(x, myValue, refValue, title, yLabel, nVessels, text, fname, showRefG):
    if showRefG:
        return plot(
            x, myValue, refValue, title, yLabel, text,
            label=f"Referanse\n{nVessels} båter",
            fName=fname
        )
    else:
        return plot(
            x, myValue,
            title=title,
            yLabel=yLabel,
            text=text,
            label=f"Referanse\n{nVessels} båter",
            fName=fname
        )

def createPlots(result, kpiData, text, checkBox, toPdfFile, toJsonFile, toCsvFile):
    figList = []
    jsonCsvDataList = []
    periodArray = result["periods"]
    nVessels = result["nVessels"]
    kpi_results = result["kpi"]
    span = kpiData.span

    endDateList = []
    for i in periodArray:
        endDateList.append(i[1])

    #######################################
    # Plot EEOI per periode
    #######################################
    if checkBox.eeoi:
        toPngFile = OUTDIR + "eeoi"
        title = ("EEOI aggregert over {months} måneder\n\n").format(months=span)    # Add \n\n to push the title upwards
        yLabel = "EEOI"
        
        fig = plot_kpi(endDateList, 
            kpi_results["myEeoiList"], 
            kpi_results.get("refEeoiList"), 
            title, 
            yLabel,
            nVessels,
            text,
            toPngFile,
            checkBox.showRefG
        )
        figList.append(fig)
        jsonCsvDataList.append(kpi_results["myEeoiList"])
        if checkBox.showRefG:
            jsonCsvDataList.append(kpi_results["refEeoiList"]) 

    #######################################
    # Plot FUI per periode
    #######################################
    if checkBox.fui:
        toPngFile = OUTDIR + "fui"
        title = ("FUI aggregert over {months} måneder\n\n").format(months=span)     # Add \n\n to push the title upwards
        yLabel = "FUI"
        
        fig = plot_kpi(endDateList, 
            kpi_results["myFuiList"], 
            kpi_results.get("refFuiList"), 
            title, 
            yLabel,
            nVessels,
            text,
            toPngFile,
            checkBox.showRefG
        )
        figList.append(fig)
        jsonCsvDataList.append(kpi_results["myFuiList"])
        if checkBox.showRefG:
            jsonCsvDataList.append(kpi_results["refFuiList"]) 

    #######################################
    # Plot total Fangst per periode
    #######################################
    if checkBox.catch:
        toPngFile = OUTDIR + "fangst"
        title = ("Fangst aggregert over {months} måneder\n\n").format(months=span)      # Add \n\n to push the title upwards
        yLabel = "Tonn"
        
        fig = plot_kpi(endDateList, 
            kpi_results["myCatchList"], 
            kpi_results.get("refCatchList"), 
            title, 
            yLabel,
            nVessels,
            text,
            toPngFile,
            checkBox.showRefG
        )
        figList.append(fig)
        jsonCsvDataList.append(kpi_results["myCatchList"])
        if checkBox.showRefG:
            jsonCsvDataList.append(kpi_results["refCatchList"]) 
    
    ########################################
    # Plot gjennomsnittlig Fangst per tur
    ########################################
        toPngFile = OUTDIR + "fangstPerTur"
        title = ("Gj. snittlig fangst per tur, {months} mnd perioder\n\n").format(months=span)      # Add \n\n to push the title upwards
        yLabel = "Tonn"
        
        fig = plot_kpi(endDateList, 
            kpi_results["weightPerTripList"], 
            kpi_results.get("refWeightPerTripList"), 
            title, 
            yLabel,
            nVessels,
            text,
            toPngFile,
            checkBox.showRefG
        )
        figList.append(fig)
        jsonCsvDataList.append(kpi_results["weightPerTripList"])
        if checkBox.showRefG:
            jsonCsvDataList.append(kpi_results["refWeightPerTripList"]) 


    #######################################
    # Plot total Fangstverdi per periode
    #######################################
        toPngFile = OUTDIR + "fangstVerdi"
        title = ("Fangstverdi aggregert over {months} måneder\n\n").format(months=span)     # Add \n\n to push the title upwards
        yLabel = "mill. NOK"
        
        fig = plot_kpi(endDateList, 
            kpi_results["myCatchValueList"], 
            kpi_results.get("refCatchValueList"), 
            title, 
            yLabel,
            nVessels,
            text,
            toPngFile,
            checkBox.showRefG
        )
        figList.append(fig)
        jsonCsvDataList.append(kpi_results["myCatchValueList"])
        if checkBox.showRefG:
            jsonCsvDataList.append(kpi_results["refCatchValueList"]) 
        
    
    ############################################
    # Plot gjennomsnittlig Fangstverdi per tur
    ############################################
        toPngFile = OUTDIR + "fangstVerdiPerTur"
        title = ("Gj. snittlig fangstverdi per tur, {months} mnd perioder\n\n").format(months=span)     # Add \n\n to push the title upwards
        yLabel = "mill. NOK"
        
        fig = plot_kpi(endDateList, 
            kpi_results["catchValuePerTripList"], 
            kpi_results.get("refCatchValuePerTripList"), 
            title, 
            yLabel,
            nVessels,
            text,
            toPngFile,
            checkBox.showRefG
        )
        figList.append(fig)
        jsonCsvDataList.append(kpi_results["catchValuePerTripList"])
        if checkBox.showRefG:
            jsonCsvDataList.append(kpi_results["refCatchValuePerTripList"]) 

    ########################################
    # Plot Drivstofforbruk per periode
    ########################################
    if checkBox.fuel:
        toPngFile = OUTDIR + "bunkersForbruk"
        title = ("Drivstofforbruk aggregert over {months} måneder\n\n").format(months=span)     # Add \n\n to push the title upwards
        yLabel = "1000 liter"
        
        fig = plot_kpi(endDateList, 
            kpi_results["myFuelList"], 
            kpi_results["refFuelList"], 
            title,
            yLabel,
            nVessels, 
            text,
            toPngFile,
            checkBox.showRefG
        )
        figList.append(fig)
        jsonCsvDataList.append(kpi_results["myFuelList"])
        if checkBox.showRefG:
            jsonCsvDataList.append(kpi_results["refFuelList"]) 
    
        ##############################################
    # Plot gjennomsnittlig drivstofforbruk per tur
    ###############################################
        toPngFile = OUTDIR + "bunkersPerTur"
        title = ("Gj. snittlig drivstofforbruk per tur, {months} mnd perioder\n\n").format(months=span)     # Add \n\n to push the title upwards
        yLabel = "1000 liter"
        
        fig = plot_kpi(endDateList, 
            kpi_results["fuelPerTripList"], 
            kpi_results.get("refFuelPerTripList"), 
            title,
            yLabel,
            nVessels, 
            text,
            toPngFile,
            checkBox.showRefG
        )
        figList.append(fig)
        jsonCsvDataList.append(kpi_results["fuelPerTripList"])
        if checkBox.showRefG:
            jsonCsvDataList.append(kpi_results["refFuelPerTripList"]) 

    #######################################
    # Plot Drivstoffkostnad per periode
    #######################################
    if checkBox.fuelcost:
        toPngFile = OUTDIR + "bunkersKostnad"
        title = ("Drivstoffkostnad aggregert over {months} måneder\n\n").format(months=span)        # Add \n\n to push the title upwards
        yLabel = "mill. NOK"
        
        fig = plot_kpi(endDateList, 
            kpi_results["myFuelCostList"], 
            kpi_results["refFuelCostList"], 
            title, 
            yLabel,
            nVessels,
            text,
            toPngFile,
            checkBox.showRefG
        )
        figList.append(fig)
        jsonCsvDataList.append(kpi_results["myFuelCostList"])
        if checkBox.showRefG:
            jsonCsvDataList.append(kpi_results["refFuelCostList"]) 

    ################################################
    # Plot gjennomsnittlig Drivstoffkostnad per tur
    ################################################
        toPngFile = OUTDIR + "bunkersKostnadPerTur"
        title = ("Gj. snittlig drivstoffkostnad per tur, {months} måneder\n\n").format(months=span)        # Add \n\n to push the title upwards
        yLabel = "mill. NOK"
        
        fig = plot_kpi(endDateList, 
            kpi_results["fuelCostPerTripList"], 
            kpi_results.get("refFuelCostPerTripList"), 
            title,
            yLabel,
            nVessels, 
            text,
            toPngFile,
            checkBox.showRefG
        )
        figList.append(fig)
        jsonCsvDataList.append(kpi_results["fuelCostPerTripList"])
        if checkBox.showRefG:
            jsonCsvDataList.append(kpi_results["refFuelCostPerTripList"]) 

    ################################################################################
    # Plot gjennomsnittlig drivstoffkostnad for fangstaktive døgn, gj.snitt per tur
    ################################################################################
    # Hva er fangstaktivt døgn?

    ##############################################
    # Plot relativ fortjeneste per tonn drivstoff
    ##############################################
    if checkBox.revenue:
        toPngFile = OUTDIR + "RelativFortjenestePerFangst"
        title = ("Relativ fortjeneste per tonn fangst, {months} mnd perioder\n\n").format(months=span)     # Add \n\n to push the title upwards'
        yLabel = "1000 NOK"
        
        fig = plot_kpi(endDateList, 
            kpi_results["myRevPerTonWeightList"], 
            kpi_results.get("refRevPerTonWeightList"), 
            title, 
            yLabel,
            nVessels,
            text,
            toPngFile,
            checkBox.showRefG
        )
        figList.append(fig)
        jsonCsvDataList.append(kpi_results["myRevPerTonWeightList"])
        if checkBox.showRefG:
            jsonCsvDataList.append(kpi_results["refRevPerTonWeightList"]) 

    ##############################################
    # Plot relativ fortjeneste per time
    ##############################################
        toPngFile = OUTDIR + "RelativFortjenestePerTime"
        title = ("Relativ fortjeneste per time, {months} mnd perioder\n\n").format(months=span)     # Add \n\n to push the title upwards
        yLabel = "1000 NOK"
        
        fig = plot_kpi(endDateList, 
            kpi_results["myRevPerHourList"], 
            kpi_results.get("refRevPerHourList"), 
            title,
            yLabel,
            nVessels, 
            text,
            toPngFile,
            checkBox.showRefG
        )
        figList.append(fig)
        jsonCsvDataList.append(kpi_results["myRevPerHourList"])
        if checkBox.showRefG:
            jsonCsvDataList.append(kpi_results["refRevPerHourList"]) 
    
    ############################################
    # Plot gjennomsnittlig CO2 per tur
    ############################################
    if checkBox.co2:
        toPngFile = OUTDIR + "co2PerTur"
        title = ("Gj. snittlig CO2 utslipp per tur, {months} mnd perioder\n\n").format(months=span)     # Add \n\n to push the title upwards
        yLabel = "Tonn CO2"
        
        fig = plot_kpi(endDateList, 
            kpi_results["myCO2PerTripList"], 
            kpi_results.get("refCO2PerTripList"), 
            title, 
            yLabel,
            nVessels,
            text,
            toPngFile,
            checkBox.showRefG
        )
        figList.append(fig)
        jsonCsvDataList.append(kpi_results["myCO2PerTripList"])
        if checkBox.showRefG:
            jsonCsvDataList.append(kpi_results["refCO2PerTripList"]) 

    ##############################################
    # Plot gjennomsnittlig antall dager per tur
    ##############################################
    if checkBox.dhd:
        toPngFile = OUTDIR + "dagerPerTur"
        title = ("Gj. snittlig antall dager per tur, {months} mnd perioder\n\n").format(months=span)        # Add \n\n to push the title upwards
        yLabel = "Dager"
        
        fig = plot_kpi(endDateList, 
            kpi_results["daysPerTripList"], 
            kpi_results.get("refDaysPerTripList"), 
            title, 
            yLabel,
            nVessels,
            text,
            toPngFile,
            checkBox.showRefG
        )
        figList.append(fig)
        jsonCsvDataList.append(kpi_results["daysPerTripList"])
        if checkBox.showRefG:
            jsonCsvDataList.append(kpi_results["refDaysPerTripList"]) 

    ###############################################
    # Plot gjennomsnittlig seilt distanse per tur
    ###############################################
        toPngFile = OUTDIR + "distansePerTur"
        title = ("Gj. snittlig seilt distanse per tur, {months} mnd perioder\n\n").format(months=span)      # Add \n\n to push the title upwards
        yLabel = "Nautiske mil"
        
        fig = plot_kpi(endDateList, 
            kpi_results["distancePerTripList"], 
            kpi_results.get("refDistancePerTripList"), 
            title, 
            yLabel,
            nVessels,
            text,
            toPngFile,
            checkBox.showRefG
        )
        figList.append(fig)
        jsonCsvDataList.append(kpi_results["distancePerTripList"])
        if checkBox.showRefG:
            jsonCsvDataList.append(kpi_results["refDistancePerTripList"]) 

    
    #################################################
    # Plot gjennomsnittlig aktive fisketimer per tur
    #################################################
    # Finn start og stopp tid for alle hal på en tur og summer for å finne totaltid per tur
    # Legg sammen alle turer i perioden


    #-------------------------------------------
    # Save all plotted figures to a pdf file
    #-------------------------------------------
    save_figs_to_pdf(
        figList,
        pdf_path=toPdfFile,
        metadata={
            "Title": "KPI-rapport",
            "Author": "Tore Syversen",
            "Keywords": "fiskeri, KPI, rapport",
        },
        close=True,   # free memory
        tight=True,   # prevent label clipping
    )

    #------------------------------------------
    # Save the data to JSON and CSV files
    #------------------------------------------
    jsonDict = createJsonItem(kpiData, result["nVessels"], result["periods"], jsonCsvDataList)
    createJson(jsonDict, toJsonFile)
    json_to_csv(jsonDict, toCsvFile)


        
        