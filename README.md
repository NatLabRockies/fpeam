# Introduction

The Feedstock Production Emissions to Air Model (FPEAM) calculates spatially explicit inventories of criteria air pollutants and precursors generated from agricultural and transportation activities associated with the production and supply of biomass feedstocks for renewable energy generation. FPEAM was originally developed to calculate air pollutants as part of the 2016 update to the Billion Ton Study (BTS). For this version of FPEAM, the code base has been substantially refactored and streamlined to provide increased flexibility around biomass production scenario definitions, including what activities and pollutants are included in the calculations and at what spatial scale. This document describes the FPEAM code base and default input files bundled with the beta model release.

A full list of the default pollutants calculated by FPEAM is given in the first table below. FPEAM calculations are organized into independent modules listed in the second table below along with the pollutants and pollutant-generating activities and processes included by default in each module. The EmissionFactors module is unique in that it can be used to calculate any pollutant from any activity, if sufficient input data is provided. In particular, users have the option of using the EmissionFactors module to replace the MOVES and/or NONROAD modules with emissions factors for agricultural equipment use and on-road biomass transportation. The EmissionFactors module can also be used to calculate pollutants from additional activities, such as non-nitrogen fertilizer application. At this stage of development calculating additional pollutants from either the NONROAD or MOVES modules is not allowed for in the model but this functionality can be added in the future if there is demand.

TABLE: Default list of pollutants calculated by FPEAM.

| Pollutant | Description |
| :------------: | :---------- |
| CO | Criteria air pollutant |
| NH<sub>3</sub> | Criteria air pollutant precursor|
| NO<sub>x</sub> | Criteria air pollutant |
| SO<sub>2</sub> | Criteria air pollutant |
| VOC |  Criteria air pollutant precursor |
| PM<sub>2.5</sub> | Criteria air pollutant |
| PM<sub>10</sub> | Criteria air pollutant | 

TABLE: Available FPEAM modules.

| Module | Default pollutants | Default activities |
| :----- | :-------------------: | :------------------ |
| MOVES | All | Off-farm, on-road transportation of biomass to biorefineries |
| NONROAD | All | On-farm use of agricultural equipment |
| EmissionFactors | VOC, NH<sub>3</sub>, NO<sub>x</sub> | Nitrogen fertilizer application; pesticide and herbicide application; other activities as data is available |
| FugitiveDust | PM<sub>2.5</sub>, PM<sub>10</sub> | On-farm use of agricultural equipment |

## Organization of this README

A high-level overview of how to use FPEAM via the graphical user interface (GUI) packaged with the FPEAM code base is given in the FPEAM Workflow section.

FPEAM requires several other pieces of software to run a complete default scenario. Installation instructions for these dependencies and FPEAM itself are given in the Installing FPEAM and Dependencies section. 

The Graphical User Interface section is organized around the GUI. Each sub-section gives details on each tab, including what user inputs are available, descriptions of each user option, input parameter, and dataset, and data sources for default parameter values and datasets.

Finally, details on the calculations performed by FPEAM and all simplifying and other assumptions are given in the Module Calculations and Assumptions section.

# FPEAM Workflow

FPEAM scenarios can be defined and run either through the graphical user interface or via the command line. The available functionality is the same regardless of how FPEAM is run.

## Graphical user interface

To open the GUI, first install FPEAM according to the instructions below. After installing, there are two options for running the GUI. Option one is to open the file `AllModuleTab.py`, located in `fpeam/src/FPEAM/gui` in PyCharm, Spyder or another Python integrated developement environment (IDE) and run the file from the IDE. Option two is to open a command prompt or Anaconda prompt (recommended) in the same directory, and execute `python AllModuleTab.py`. Either option will open the GUI and allow scenarios to be run.

The FPEAM GUI was developed to be relatively self-explanatory with an easy to follow workflow. Upon opening the GUI, users will need to specify a scenario name (it is recommended to use unique scenario names for every FPEAM run), a project path where output files are saved, and which modules to run.

Inputs for each module are entered on the module's tab. All tabs are pre-populated with default values such that users should need to enter custom values for relatively few inputs. Users may work through the tabs in any order before returning to the Home tab and clicking the Run button to generate results. The Reset button, also on the Home tab, will return all inputs to their default values.

While running FPEAM, a log is displayed on the Results tab with status messages that can be used to confirm FPEAM is running correctly or to debug a scenario. After the run completes, several basic visualizations are displayed on the same tab. These visualizations are intended to confirm that FPEAM ran correctly and returned results from all modules that were run. For more advanced visualizations, users should use the output CSV files saved in the project path directory.

## Command line interface

If FPEAM is run via command line, users must first generate config (.ini file extension) files for each module being run and one, the run config, for the scenario itself. These files contain the same inputs found in the GUI; users may use the template config files (.spec file extension) located in the `configs` folder in the repository as examples.

After defining the necessary config files, the following syntax is used to run an fpeam scenario:

`fpeam --[module name]_config [module config file name].ini [run config file name]`

where there is one `--[module_name]_config [module config file name].ini` combination for each module being run and the square-bracketed phrases should be replaced with module names and config file names.

Users can also enter `fpeam --help` to see additional command line syntax.

# Installing FPEAM and Dependencies

## Python

FPEAM is written in Python 3 and requires Python 3.5 or above to be installed. First-time users of Python are recommended to install Python via Anaconda, which streamlines installing packages and managing environments. Instructions for installing Anaconda on Windows and macOS are located at [anaconda.com](https://docs.anaconda.com/anaconda/install/). A user guide for Anaconda is also available at [docs.anaconda.com](https://docs.anaconda.com/anaconda/user-guide/).

## Required Python Packages

* configobj
* pandas
* networkx
* pymysql
* lxml
* numpy
* matplotlib
* qtpy

The most up-to-date version available of each package should be installed. Using `conda install` for any new packages is strongly recommended, if Python was installed with Anaconda.

## MOVES and NONROAD

FPEAM calls the U.S. Environmental Protection Agency's (EPA) MOtor Vehicle Emission Simulator (MOVES) model to calculate pollutants generated during on-road feedstock transportation. NONROAD, a similar model for off-road vehicles including agricultural and forestry equipment, is packaged with MOVES. The latest version of MOVES can be downloaded from the [EPA website](https://www.epa.gov/moves/latest-version-motor-vehicle-emission-simulator-moves) and installed using the built-in installation helper.

**MOVES should not be installed to the default directory recommended by the installer.** Instead, create a directory called MOVES2014b or a similar, brief name directly under the C:\ drive and install MOVES to that location. It is necessary to keep filepaths associated with NONROAD (packaged with MOVES) under 30 characters, or else NONROAD will not process the complete filepath. Installing MOVES to this C:\MOVES2014b directory will make running NONROAD through FPEAM possible.

MOVES itself has several dependencies including MySQL, installation instructions for which will be provided during the MOVES installation process. 

### MySQL Setup

When installing MySQL for the first time, users will need to create a username and password for accessing the local database. FPEAM will use this username and password to read from the MOVES default database and write results from MOVES; users should make note of the username and password for later use, or set them to `root` / `root` to use the default FPEAM values.

MySQL may also require the [Microsoft Visual C++ 2015 Redistributable](https://www.microsoft.com/en-us/download/details.aspx?id=52685) which can be downloaded and installed at the link.

## Miscellaneous

While not required to run FPEAM, it is recommended that users planning on implementing their own modules or otherwise editing the FPEAM code base install an integrated development environment (IDE) for Python such as [PyCharm](https://www.jetbrains.com/pycharm/). An IDE is not required for users who do not intend to make changes to the codebase.

## FPEAM

After all dependencies are installed, download the FPEAM repository from GitHub. Open either a Windows Command Prompt or an Anaconda Prompt and navigate to the outer FPEAM directory `fpeam` using cd. Then enter:

`pip install -e .`

*Please note* that FPEAM cannot be installed using `conda`, only `pip`. The above command will install FPEAM, the default datasets, and the GUI on your computer as a Python module. From this point you may run FPEAM using the GUI or via the command line.

# Graphical User Interface

Each sub-section goes over one of the GUI tabs.

## Home 

![Screenshot of the Home tab on the GUI, with all sections expanded and all inputs as they appear when the GUI is first opened.](https://github.com/NREL/fpeam/blob/master/src/FPEAM/gui/screenshots/home-top.PNG)

The Home tab contains the only required inputs for running a scenario, which are the scenario name and the project path. All other inputs are pre-populated with default values, such that FPEAM can quickly be run for a basic, nationwide feedstock production scenario.

The **Scenario Name** is used in several places to identify inputs, outputs and final results for this scenario. Using unique scenario names for every FPEAM run is strongly recommended, even if FPEAM is run several times for the same scenario or set of input data.

The **Project Path** is where FPEAM will save the final results in the form of CSV files. It is not necessary to create a new directory for every scenario or FPEAM run, as the scenario names are used in the results filenames to distinguish the results of various runs.

Modules to include or exclude in a scenario are indicated with checkboxes. By default, all modules are included in a scenario thus all boxes are checked. For any modules that are deselected - indicating that the module will not be run for the current FPEAM scenario - the corresponding tab will be greyed out and inaccessible to indicate that inputs for that module are not necessary.

The **Reset** button will return all inputs, on all tabs, to their default values, while the **Run** button will execute FPEAM. If a scenario name and project path have not been defined, or if there are key errors in the inputs (which are indicated by messages within the GUI), then the Run button cannot be clicked.

All other inputs on the Home tab are parameter values and input datasets that are used in multiple modules. Any datasets, parameters and other inputs used by only a single module are located on that module's specific tab.

### Custom Data Filepaths

![Screenshot of the Custom Data Filepaths section on the Home tab](https://github.com/NREL/fpeam/blob/master/src/FPEAM/gui/screenshots/home-customdatafilepaths.PNG)

**Equipment use**. The equipment dataset defines the agricultural activities involved in feedstock production. Columns and data types in this dataset are defined in the table below. The equipment dataset defines the equipment used for each agricultural activity (in the default equipment dataset, activities consist of establishment, maintenance, harvest and loading, but additional or alternate activities may be specified as needed) as well as the resources consumed, such as fuel, time, fertilizer, and other agricultural chemicals. Resource rate (amount) units in the equipment dataset must correspond with the units in the feedstock production dataset discussed below, or an error will be given when the data is read into FPEAM. For each activity that involves agricultural equipment, the equipment name must be provided. These are user-defined names that are matched to NONROAD equipment types with the `nonroad_equipment` file discussed further in the NONROAD module section.

TABLE: List of columns and data types in equipment dataset.

| Column name | Data type | Description |
| :---------- | :-------: | :---------- |
| feedstock | string | Feedstock being grown |
| tillage_type | string | Tillage practice |
| equipment_group | string | Region identifier |
| rotation_year | integer | Year of crop rotation |
| activity | string | Category of on-farm activity for which the equipment is used |
| equipment_name | string | Description of equipment used, if any |
| equipment_horsepower | float | Horsepower (if applicable to equipment) |
| resource | string | Resource used (each activity may have multiple resources associated with it) |
| rate | float | Quantity of resource used |
| unit_numerator | string | Numerator of resource rate unit |
| unit_denominator | string | Denominator of resource rate unit |

Equipment data must be specified at a regional level of resolution, but the exact bounds of each region can be user-defined and at any scale. In the default equipment data, some region identifiers are numbered, albeit with the numbers stored as characters rather than integers, and some are named. Numbered regions correspond to U.S. Farm Resource Regions (FRRs), while named regions correspond to forestry regions. Regions in the equipment dataset must correspond with the regions defined in the feedstock production dataset discussed below to allow feedstock production data to be merged with the equipment data. Feedstocks and tillage types in the equipment dataset must also match those in the feedstock production dataset. Any equipment data without matching feedstock production data or vice versa will be excluded from FPEAM calculations.

The `rotation_year` column in the equipment dataset refers to the year in a multi-year crop rotation such as a switchgrass cropping system. `rotation_year` should not contain calendar years but rather integers greater than or equal to 1. The calendar year in which the rotation begins is specified for each scenario within the FPEAM GUI. This `year` parameter specifies the calendar year in which biomass is first grown, harvested and transported in a scenario.

The equipment data provided with the FPEAM release was obtained from the Policy Analysis System (POLYSYS) model, "a national, interregional, agricultural model" [(Ugarte and Ray, 2000)](https://www.sciencedirect.com/science/article/pii/S0961953499000951 ). From the [University of Tennessee's Bio-Based Energy Analysis Group](https://ag.tennessee.edu/arec/Pages/beag.aspx ), POLYSYS 

> is a dynamic stochastic (in yields) model of the US agricultural sector, capable of estimating the competitive allocation of agricultural land and feedstock prices associated with changes in yield and management practices. Input requirements include a baseline solution typically from USDA, and policy or resource changes desired for a particular scenario. Output includes economic variables such as County-level feedstock supply, national feedstock demands and prices, National livestock supply and demand, farm income, and land use including forest harvest, afforestation, and pasture conversion. In addition, through the environmental module, estimates of changes in carbon emission and sequestration, soil erosion and sediment, fertilizer use, and chemical use are provided.

Equipment data for whole trees and forest residues was obtained from the Forest Sustainable and Economic Analysis Model (ForSEAM), "a national forest optimization model." Also from the [University of Tennessee's Bio-Based Energy Analysis Group](https://ag.tennessee.edu/arec/Pages/beag.aspx ):

> the Forest Sustainable and Economic Analysis Model (ForSEAM) was originally constructed to estimate forest land production over time and its ability to produce not only traditional forest products, but also products to meet biomass feedstock demands through a cost minimization algorithm (He et al., 2014). The model has three components. The supply component includes general forest production activities for 305 production regions based on USDA’s agricultural supply districts. Each region has a set of production activities defined by the USFS. The Forest Product Demand Component is based on six USFS Scenarios with estimates developed by the US Forest Products Model. The sustainability component ensures that harvest in each region does not exceed annual growth, forest tracts are located within one-half mile of existing roads, and that current year forest attributes reflect previous years’ harvests and fuel removals. The model incorporates dynamic tracking of forest growth.

The default equipment dataset did not originally include loading equipment. Rates for this equipment were incorporated into the dataset separately and are shown in the table below.

TABLE: Loading equipment information source from the [2016 Update to the Billion Ton Study, Volume 2](https://www.energy.gov/eere/bioenergy/downloads/2016-billion-ton-report-volume-2-environmental-sustainability-effects) (BTS 2016).
 
| feedstock | equipment type | equipment horsepower | resource | rate | unit |
| :-------- | :------------: | :------------------: | :------: | :--- | :--- |
| corn stover | tractor | 143 | time | 0.017361 | hour/dry short ton |
| wheat straw | tractor | 143 | time | 0.017361 | hour/dry short ton | 
| switchgrass | tractor | 143 | time | 0.017361 | hour/dry short ton |
| sorghum stubble | tractor | 450 | time | 0.050226017 | hour/dry short ton
| corn grain | tractor | 143 | time | 0.017361 | hour/dry short ton |
| miscanthus | tractor | 143 | time | 0.017361 | hour/dry short ton |

**Feedstock production**. The feedstock production dataset defines what feedstocks were produced where, in what amounts, and by which agricultural practices. Columns and data within this dataset are described in the table below. This dataset contains two region identifiers, `equipment_group` (these values must match those in the equipment dataset) and `region_production`, that indicate more precisely where feedstocks were produced. `region_production` values in the default feedstock production dataset correspond to the [Federal Information Processing Standards](https://www.nrcs.usda.gov/wps/portal/nrcs/detail/national/home/?cid=nrcs143_013697) (FIPS) codes which identify U.S. counties. If values in the `region_production` column are not FIPS codes, an additional input file giving the mapping of the `region_production` values to FIPS values must be provided in order for MOVES and NONROAD to run successfully; this file is discussed further in the Additional input datasets section.

Latitude and longitude values are also specified for feedstock production and destination locations. These values are used in the router engine which calculates minimum-distance routes for on-road biomass transportation between farms or forestry locations and biorefineries. If precise latitude and longitude values are not available for any production or destination locations, these columns can be left blank in the production dataset. Instead, the FIPS for the production and destination locations can be specified, and a lookup table included in the default input data will be used to find the latitude-longitude pairs for the county centroids. 

The feedstock production dataset, like the equipment dataset, does not contain the calendar year in which feedstock production took place. This is specified using the **Analysis Year** input in the GUI.

TABLE: List of columns in feedstock production data set with data types and descriptions

| Column name | Data type | Description |
| :---------- | :-------: | :---------- |
| feedstock | string | Feedstock being grown; may be food crop, energy feedstock or residue |
| tillage_type | string | Type of tillage practice |
| region_production | string | Identifies the region where the feedstock is grown |
| region_destination | string | Identifies the region to which the harvested feedstock from this region_production is transported |
| equipment_group | string | Region identifier; must match equipment_group values in equipment data set |
| feedstock_measure | string | Identifies the value in the feedstock_amount column | 
| feedstock_amount | float | Feedstock amount defined by feedstock_measure, with units given by unit_numerator and unit_denominator |
| unit_numerator | string | Numerator of feedstock_amount unit |
| unit_denominator | string | Denominator of feedstock_amount unit, if any |
| source_lon | float | Longitude of feedstock production location |
| source_lat | float | Latitude of feedstock production location |
| destination_lon | float | Longitude of feedstock destination location |
| destination_lat | float | Latitude of feedstock destination location |

**Feedstock Loss Factors**. Feedstock dry matter loss is accounted for using loss factors that represent the losses incurred during specific activities and at several key points along the feedstock supply chain. These loss factors were obtained from [GREET 2018](https://greet.es.anl.gov/), from the Herbaceous Feedstock 2018 State of Technology Report prepared by Idaho National Laboratory [1.], and from values reported in the [2016 Update to the Billion Ton Study, Volume 1](https://www.energy.gov/sites/prod/files/2016/12/f34/2016_billion_ton_report_12.2.16_0.pdf). Factors for the farm gate supply chain stage represent on-field covered storage and biorefinery gate factors represent dry matter lost during on-road transportation.

TABLE: Dry matter loss factors by feedstock and supply chain stage.

| Feedstock | Supply Chain Stage | Dry Matter Loss | Source |
| :-------- | :----------------- | :-------------: | :----- |
| corn grain | biorefinery gate | 0.10 | 2016 Billion Ton Report, Vol 1, Table 2.7 (derived value)|
| corn stover | farm gate | 0.12 | INL, 2018, Table A.6 |
| corn stover | biorefinery gate | 0.02 | INL, 2018, Figure A.4 (includes preprocessing) |
| switchgrass | farm gate | 0.08 | INL, 2018, Table A.6 |
| switchgrass | biorefinery gate | 0.02 | INL, 2018, Figure A.4 (includes preprocessing) |
| miscanthus | farm gate | 0.12 | GREET, 2018, EtOH pathway (derived value) |
| miscanthus | biorefinery gate | 0.02 | GREET, 2018, EtOH pathway (includes preprocessing) |
| sorghum | farm gate | 0.026 | GREET, 2018, EtOH pathway |
| sorghum | biorefinery gate | 0.02 | GREET, 2018, EtOH pathway |
| whole trees | biorefinery gate | 0.10 | 2016 Billion Ton Report, Vol 1, Table 2.7 (derived value) |
| forest residues | biorefinery gate | 0.10 | 2016 Billion Ton Report, Vol 1, Table 2.7 (derived value) |

[1.] Roni, M., Thompson, D., Hartley, D., Griffel, M., Hu, H., Nguyen, Q., Cai, H. Herbaceous Feedstock 2018 State of Technology Report. INL/EXT-18-51654. Idaho National Laboratory, September 30, 2018.

**Transportation Graph**. To obtain on-road routes for biomass transportation, the router engine uses a graph of all known, publicly accessible roads in the contiguous U.S., obtained from the [Global Roads Open Access Data Sets](http://sedac.ciesin.columbia.edu/data/set/groads-global-roads-open-access-v1) (gROADS) v1. This graph does not contain transportation pathways such as rivers, canals and train tracks, and therefore limits the transportation modes that can be used in FPEAM to on-road vehicles.

**Node Locations**.

**Truck Capacity**. This dataset defines the biomass carrying capacity of one truck in mass units by feedstock. 

TABLE: Default truck capacities by feedstock. Source: BTS 2016.

| Feedstock | Truck capacity (dry short tons/load) |
| :-------: | :----------------------------: |
| corn stover | 17.28 |
| wheat straw | 17.28 |
| switchgrass | 17.28 |
| corn grain | 17.28 |
| sorghum stubble | 21.10 |
| forest residues | 16.68 |
| forest whole trees | 16.68 |
| poplar | 16.68 |
| willow | 16.68 |

The truck capacity value for forest residues was also used as a proxy value for whole trees, poplar, and willow feedstocks, due to a lack of additional data.

### Advanced Options

![Screenshot of the Advanced Options section on the Home Tab](https://github.com/NREL/fpeam/blob/master/src/FPEAM/gui/screenshots/home-advancedoptions.PNG)

**Logging Level**. Select the level of log messages to be displayed in the Results tab and written to a log file as FPEAM runs.

**Use Router Engine**. The router engine locates minimum-distance on-road routes between feedstock production and destination locations and calculates the vehicle miles traveled (VMT) in each county for each route. Dijkstra's algorithm is applied to find the shortest path from the biomass production location to the destination, and the shortest path is used to obtain a list of FIPS through which the biomass is transported as well as the vehicle miles traveled within each FIPS. This information is used with the emission factors obtained from MOVES to calculate emissions within each FIPS where biomass is produced, transported and delivered. Due to MOVES' long run time, emission factors are not obtained for every FIPS through which biomass is transported; however, this functionality can be added in the future if there is demand. Because the router engine is only used internally to FPEAM, there are no user options for running the router.

**Backfill Missing Data**. Users have the option of backfilling any missing numeric data in the input datasets with the default value of 0 or a value of their choice. This option prevents FPEAM from excluding from the results any counties, feedstocks etc. that did not have complete input data for one or more pollutant processes. Instead, the pollutant inventories resulting from incomplete input data will appear in the results as 0. There is no option to backfill categorical and identifier variables (feedstock name, for instance) - if there are missing values in these variables, then the pollutant inventories for those variable values will not be included in the FPEAM results.

**Forestry Feedstock Names**. The default feedstock production datasets packaged with FPEAM cover both energy crops and forestry products. The production and harvesting activities are significantly different for forestry feedstocks, and so the forestry feedstocks must be specified and forestry-specific calculation methods applied. Single quotes should be used to define elements in the list of forestry feedstock names. If a forestry feedstock appears in this list but not in the feedstock production and/or equipment use datasets, it will not be included in the final results.

**VMT Per Truck**. By default, the router engine is used to calculate vehicle miles traveled (VMT) in each county. Users can choose to not use the router engine and instead specify a flat value for VMT to be used in calculating pollutants from on-road transportation. In this case, on-road transportation pollutants will only be calculated for the county in which feedstock was produced, because the route over which feedstock was transported was not generated. Users are recommended to always use the router engine, in which case the value of this parameter has no impact on FPEAM results.

## MOVES

![Screenshot of the top of the MOVES tab](https://github.com/NREL/fpeam/blob/master/src/FPEAM/gui/screenshots/moves-top.PNG)

Emissions from feedstock transportation are by default calculated using version 2014b of the EPA's MOtor Vehicle Emission Simulator (MOVES) model. FPEAM creates all required input files and runs MOVES in batch mode, using a set of parameters listed below to determine at what level of detail MOVES is run. Following the MOVES run(s), emission rates for vehicle operation and start and hotelling are postprocessed with feedstock production data, truck capacity data and feedstock transportation routes to calculate total pollutant amounts.

Currently the FPEAM MOVES module can only run MOVES at the FIPS (county) level. The FIPS for which MOVES is run are determined from `region_production` values in the feedstock production set, which are mapped to FIPS using the region-to-FIPS map discussed below under Custom Data Filepaths.

**Aggregation Level**. MOVES can be run for all FIPS for which a mapping from `region_production` to FIPS was provided, or at two levels of aggregation: one FIPS per state based on which FIPS had the highest total feedstock production ("By State"), or multiple FIPS per states based on which FIPS had the highest production of each feedstock ("By State-Feedstock"). By default, MOVES is run once per state with FIPS selected based on highest total feedstock production. This aggregation is done by default to keep FPEAM run times reasonable; MOVES requires between 10 and 15 minutes to run each FIPS and can easily extend model run times into days. Users can also select the "By County" aggregation level to run MOVES for every region in which feedstock is produced.

**Use Cached Results**. When True is selected, any MOVES results already saved to the MOVES output database (specified under Database Connection Parameters on this tab) for the FIPS being analyzed will be used instead of running MOVES again.

**Executable Path**. This is the directory where MOVES is installed. Use this input to select between MOVES 2014a and 2014b, if necessary.

**MOVES Datafiles**. This directory is where the batch and other input files created for the current scenario are saved.

**Feedstock Measure Type**. The feedstock production dataset has several feedstock measure types. For MOVES, specify the measure type that has mass units (dry short tons, in the case of the default dataset). The feedstock mass produced in each county will then be used to calculate the number of farm-to-biorefinery trips required.

### Database Connection Parameters

![Screenshot of the Database Connection Parameters section of the MOVES tab.](https://github.com/NREL/fpeam/blob/master/src/FPEAM/gui/screenshots/moves-databaseconnectionparams.PNG)

**Database Host**. The Host is the machine on which the MOVES databases are installed. For users running FPEAM locally, the database host should always be left as the default.

**MOVES Database**. This specifies the name of the default database installed with MOVES that contains input data used in running MOVES. The default database is always named as `movesdb` plus the date on which the database was last updated, which will vary depending on when MOVES was installed.

**Output Database**. Pollutant rates calculated by MOVES are saved to this SQL database and read in by FPEAM for additional postprocessing and pollutant inventory calculation. Users can specify either an existing database (other than the MOVES default database) or a new database; if the specified database does not exist, FPEAM will create it automatically. It is not necessary to create a new output database for every FPEAM run.

**Username** and **Password**. These are the credentials set up during the MySQL installation process.

**MySQL Exe** and **MySQL Dump Exe**. Define the path to the executables `mysql.exe` and `mysqldump.exe`. The paths should be very similar to the defaults although the MySQL Server version may change depending on when it was installed.

### Execution Timeframe

![Screenshot of the Execution Timeframe section of the MOVES tab.](https://github.com/NREL/fpeam/blob/master/src/FPEAM/gui/screenshots/moves-executiontimeframe.PNG)

**Analysis Year**. The year in which feedstock is grown and harvested. This value must match the analysis year defined on the NONROAD tab, and should correspond to the year of the feedstock production dataset being used. If the MOVES and NONROAD years do not match, then FPEAM cannot be run.

**Month**. The month in which the transportation takes place. The default value of 10 indicates October.

**Day Type**. Whether the transportation took place on a weekday (5) or weekend (2) day.

**Beginning Hour** and **Ending Hour**. These define the time of day during which the transportation takes place. The default values are 0700 and 1800, or between 7am and 6pm. 

This execution timeframe represents a typical post-harvest day for most feedstocks.

### Custom Data Filepaths

![Screenshot of the Custom Data Filepaths section of the MOVES tab.](https://github.com/NREL/fpeam/blob/master/src/FPEAM/gui/screenshots/moves-customdatafilepaths.PNG)

**AVFT**. This dataset ("Alternative Vehicle and Fuels Technology") defines the vehicle fleet  in use during the execution timeframe. Custom AVFT files can be generated using MOVES itself; however, the default file should suffice for present-day and near-future scenarios.

**Region to FIPS Map**. The region to FIPS map provides a mapping of region identifiers to FIPS. In the case that the input datasets are based on FIPS, this dataset can be ignored.

### VMT Fractions

![Screenshot of the VMT Fractions section of the MOVES tab.](https://github.com/NREL/fpeam/blob/master/src/FPEAM/gui/screenshots/moves-vmtfractions.PNG)

**Restricted** roads are accessed by entrance and exit ramps, including highways. **Unrestricted** roads are all other roads. 

Default vehicle miles traveled (VMT) fractions were calculated from Federal Highway Administration data on total vehicle miles traveled nationwide by combination trucks in 2006. The raw data is available from the [Federal Highway Administration](https://www.fhwa.dot.gov/policy/ohim/hs06/metric_tables.cfm) in the table "Vehicle distance of travel in kilometers and related data, by highway category and vehicle type." The VMT fraction representing vehicle idling (road type = 1) was assumed to be 0 due to lack of data and is hard-coded within FPEAM.

TABLE: Default VMT fraction values. 

| Road type | Road type description | VMT fraction value |
| :--------: | :--------------------- | :-----------: |
| 1 | Vehicle idling | 0 |
| 2 | Rural restricted | 0.30 |
| 3 | Rural unrestricted | 0.28 |
| 4 | Urban restricted | 0.21 |
| 5 | Urban unrestricted | 0.21 |

### Advanced Options

![Screenshot of the Advanced Options section of the MOVES tab.](https://github.com/NREL/fpeam/blob/master/src/FPEAM/gui/screenshots/moves-advancedoptions.PNG)

**Number of Trucks Used**. The number of trucks used for feedstock transportation. If this number is increased then emissions per vehicle and per vehicle start/stop will increase but emissions for vehicle miles traveled will remain the same. Changing this parameter is unlikely to have a significant impact on the overall pollutant inventory.

**HPMSV ID**. Highway Performance Monitoring System Vehicle ID are integers indicating vehicle classes. The default is 60 which indicates a generic combination truck.

**Source Type ID**. Source Type ID are IDs specific to MOVES that specify the vehicle type in more detail. The default is 61 which indicates a short-haul combination truck.

## NONROAD

![Screenshot of the top of the NONROAD tab.](https://github.com/NREL/fpeam/blob/master/src/FPEAM/gui/screenshots/nonroad-top.PNG)

**Data Folder**. This directory is where the input and output files associated with NONROAD will be saved. Because NONROAD cannot parse filepaths longer than 30 characters, it is strongly recommended to create the `C:/Nonroad` directory rather than using a Documents or other directory.

**Path to EXE** (executable). Because NONROAD is installed as part of MOVES, this directory will always be a subdirectory of wherever MOVES was installed. If MOVES was installed to the pre-selected directory rather than the C:\MOVES2014b directory recommended above, then this filepath will need to be changed. *Please note* that if MOVES was not installed into C:\MOVES2014b or a similarly named directory, NONROAD will not be able to process filepaths for any input data because the filepaths will be longer than 30 characters.

**Analysis Year**. The analysis years defined on this tab and on the MOVES tab need to match each other; if the years do not match, FPEAM cannot be run and an error will be displayed on the GUI. The two analysis year inputs should also match the year for which the feedstock production dataset is valid.

### Database Connection Parameters

![Screenshot of the Database Connection Parameters section of the NONROAD tab.](https://github.com/NREL/fpeam/blob/master/src/FPEAM/gui/screenshots/nonroad-databaseconnectionparams.PNG)

These values should be identical to the same parameters under the MOVES tab. The **Database Name** refers to the default MOVES database, not the MOVES output database. NONROAD writes results to individual files rather than an output database, and so no output database needs to be specified.

### Data Labels

![Screenshot of the Data Labels section of the NONROAD tab.](https://github.com/NREL/fpeam/blob/master/src/FPEAM/gui/screenshots/nonroad-datalabels.PNG)

**Feedstock Measure Type** and **Irrigation Feedstock Measure Type**. In the default equipment use dataset, many activities are defined by resource consumption per feedstock measure. The feedstock measure type parameters here define which measure should be used to scale up these activities to calculate total pollutants generated. In the default feedstock production datasets "harvested" is in units of acres, so this feedstock measure type is used to scale activities including fertilizer application, herbicide application, and plowing which are all given per acre in the equipment use dataset. For irrigation, we assume that the entire planted acreage is irrigated (where irrigation is used) and so the feedstock measure type used to scale irrigation activities is "planted". The units are still acres.

**Irrigation Feedstock Name**. This is the list of feedstocks from the feedstock production dataset for which irrigation activity data is available. If a feedstock in this list has either no production data or no irrigation activity data, it will be ignored.

**Time Resource Name**. NONROAD calculates pollutants based on how many hours equipment is being operated. This parameter specifies which rows in the equipment use dataset give the hours per acre that each piece of equipment is operated. If the value specified for this parameter does not match the actual time resource name in the equipment use dataset, then NONROAD may not return any results because no data was selected.

### Custom Data Filepaths

![Screenshot of the Custom Data Filepaths section of the NONROAD tab.](https://github.com/NREL/fpeam/blob/master/src/FPEAM/gui/screenshots/nonroad-customdatafilepaths.PNG)

**Irrigation Activity**. This is the dataset derived from the 2012 Farm and Ranch Irrigation Survey, and gives pump use in hours per acre for irrigated corn grain, as well as pump specifications such as horsepower. 

**Equipment Specs** (specifications): NONROAD identifies equipment based on Source Characterization Codes (SCCs) and equipment horsepower. In the default equipment data set, SCCs were not provided, so this additional input file mapping equipment names from the equipment dataset to equipment SCCs is supplied as well. A portion of this input file is given in the table below. SCCs for equipment types included in NONROAD but not used in the default equipment dataset may be found in Appendix B of the [NONROAD User Guide](https://www.epa.gov/moves/nonroad-model-nonroad-engines-equipment-and-vehicles#user%20guide).

TABLE: Sample entries from the nonroad_equipment input dataset. Equipment descriptions in this file are added to NONROAD input files but are not necessary for NONROAD to run, thus the descriptions may be left blank if desired. 

| Equipment name | Equipment description | Source Characterization Code (SCC) |
| :------------- | :-------------------- | :--------------------------------: |
| whole tree chipper (large) | Dsl - Chippers/Stump Grinders (com) | 2270004066 |
| loader (2 row) | Dsl - Forest Eqp - Feller/Bunch/Skidder | 2270007015 |
| combine (2wd) | Dsl - Combines | 2270005020 |
| tractor 2wd 150 hp | Dsl - Agricultural Tractors | 2270005015 |

**Region to FIPS Map**. The region to FIPS map provides a mapping of region identifiers (`region_production` and `region_destination`) to FIPS. In the case that the input datasets are based on FIPS, this dataset can be ignored.

### Operating Temperature

![Screenshot of the Operating Temperature section of the NONROAD tab.](https://github.com/NREL/fpeam/blob/master/src/FPEAM/gui/screenshots/nonroad-operatingtemperature.PNG)

These temperatures in degrees Fahrenheit give the minimum, maximum and mean expected ambient (outdoor) temperatures for operation of all agricultural and forestry equipment.

### Conversion Factors

![Screenshot of the Conversion Factors section of the NONROAD tab.](https://github.com/NREL/fpeam/blob/master/src/FPEAM/gui/screenshots/nonroad-conversionfactors.PNG)

NONROAD does not directly calculate NH<sub>3</sub> emissions or volatile organic carbon (VOC) emissions or PM<sub>10</sub> emissions, thus these factors are necessary to calculate NH<sub>3</sub> emissions from total diesel consumption, VOC from total hydrocarbon emissions, and PM<sub>2.5</sub>emissions from PM<sub>10</sub> emissions. The NH<sub>3</sub> emission factor is sourced from the [COBRA Screening Model](https://www.epa.gov/statelocalclimate/co-benefits-risk-assessment-cobra-screening-model.) developed by the U.S. EPA, and the total hydrocarbon to VOC conversion factor is sourced from EPA NONROAD Conversion Factors for Hydrocarbon Emission Components. 

### Advanced Options

![Screenshot of the Advanced Options section of the NONROAD tab.](https://github.com/NREL/fpeam/blob/master/src/FPEAM/gui/screenshots/nonroad-advancedoptions.PNG)

**Encode Names**. NONROAD generates, reads and writes a great many input and output files as it runs. Because NONROAD cannot process filenames longer than 30 characters, the option to encode names converts longer filenames to abbreviated versions. If this option is set to False, NONROAD may not execute properly or may not return all of the expected results.

## Emission Factors

![Screenshot of the top of the Emission Factors tab.](https://github.com/NREL/fpeam/blob/master/src/FPEAM/gui/screenshots/emissionfactors-top.PNG)

**Feedstock Measure Type**. As seen previously, the Emission Factors calculation runs off a specific measure of feedstock, in this case `harvested` which is in units of acres. Acres are required because the emission factors calculation also uses resource rates from the equipment dataset, which are in units of mass per acre. An alternative to using `harvested` would be `planted`, although in the default feedstock production datasets the `planted` amounts tend to be higher than `harvested` (that is, more acreage is planted than is harvested) which may over-estimate some pollutants.

### Custom Data Filepaths

![Screenshot of the Custom Data Filepaths section of the Emission Factors tab.](https://github.com/NREL/fpeam/blob/master/src/FPEAM/gui/screenshots/emissionfactors-customdatafilepaths.PNG)

**Emission Factors**. Default emission factors are provided for each relevant combination of resource subtype and pollutant, as demonstrated in the table below. The unit denominator (both unit columns refer to the emission factor) must match the resource unit from the equipment use dataset. For instance, if insecticide use is quantified as gallons per dry short ton of feedstock, the emission factor here must be in pounds of pollutant per gallon of insecticide. The activity column specifies which supply chain activity causes the resource use and thus the pollutant emissions.

TABLE: Default emissions factors for NO (used as a proxy for NO<sub>x</sub>) and NH<sub>3</sub> from nitrogen fertilizers and VOC from herbicides and insecticides. NO emission factors were obtained from FOA (2001) and GREET (ANL 2010). NH<sub>3</sub> factors were obtained from Goebes et al. 2003, Davidson et al. 2004 and the 17/14 ratio of NH<sub>3</sub> to N. See [Zhang et al. (2015)](https://onlinelibrary.wiley.com/doi/full/10.1002/bbb.1620) for additional information. Note that as of July 2, 2018 the Davidson et al. reference, the CMU Ammonia Model, Version 3.6 from The Environmental Institute at Carnegie Mellon University was not available online and source data could not be verified. 
 
| resource | resource subtype           | activity             | pollutant      | emission_factor | unit_numerator | unit_denominator |
| :------- | :------------------------- | :------------------- | :------------: | :-------------: | :--------: | :--------: |
| nitrogen | anhydrous ammonia          | chemical application | no<sub>x</sub> | 0.79            | pound      | pound |
| nitrogen | anhydrous ammonia          | chemical application | nh<sub>3</sub> | 4.86            | pound      | pound |
| nitrogen | ammonium nitrate (33.5% N) | chemical application | no<sub>x</sub> | 3.80            | pound      | pound |
| nitrogen | ammonium nitrate (33.5% N) | chemical application | nh<sub>3</sub> | 2.32            | pound      | pound |
| nitrogen | ammonium sulfate           | chemical application | no<sub>x</sub> | 3.50            | pound      | pound |
| nitrogen | ammonium sulfate           | chemical application | nh<sub>3</sub> | 11.6            | pound      | pound |
| nitrogen | urea (44 - 46% N)          | chemical application | no<sub>x</sub> | 0.90            | pound      | pound |
| nitrogen | urea (44 - 46% N)          | chemical application | nh<sub>3</sub> | 19.2            | pound      | pound |
| nitrogen | nitrogen solutions         | chemical application | no<sub>x</sub> | 0.79            | pound      | pound |
| nitrogen | nitrogen solutions         | chemical application | nh<sub>3</sub> | 9.71            | pound      | pound |
| herbicide | generic herbicide         | chemical application | voc            | 0.75            | pound      | pound |
| insecticide | generic insecticide     | chemical application | voc            | 0.75            | pound      | pound |

**Resource Distribution**. The default resource distribution file, a portion of which is shown in the first table below, specifies how much of each resource type such as nitrogen, herbicide and so on consists of various resource subtypes such as specific nitrogen fertilizers or herbicide brands. Currently the resource distribution table must be supplied for FPEAM to run correctly. However, users can include the resource subtypes directly in the equipment use dataset and populate the distribution column of the resource distribution file with the values 1 if desired.

TABLE: The default resource subtype distribution data file defines the nitrogen fertilizer distribution among five common nitrogenous fertilizers and the distribution of herbicide and insecticide to generics. The nitrogen fertilizer distribution varies between feedstocks. The national average distribution from 2010 [(USDA)](https://www.ers.usda.gov/data-products/fertilizer-use-and-price.aspx#26720) is used for corn grain and stover, sorghum stubble, and wheat straw. The perennial feedstock distribution which consists of nitrogen solutions only is used for switchgrass, miscanthus and all forest products. (Turhollow, 2011, personal communication). Two example distributions are shown in the table.

| feedstock | resource | resource_subtype | distribution |
| :-------- | :------- | :--------------- | :----------: |
| corn grain | nitrogen | anhydrous ammonia | 0.3404 |
| corn grain | nitrogen | ammonium nitrate | 0.0247 |
| corn grain | nitrogen | ammonium sulfate | 0.0179 |
| corn grain | nitrogen | urea | 0.2542 |
| corn grain | nitrogen | nitrogen solutions | 0.3528 |
| switchgrass | nitrogen | anhydrous ammonia |  0 |
| switchgrass | nitrogen | ammonium nitrate |  0 |
| switchgrass | nitrogen | ammonium sulfate |  0 |
| switchgrass | nitrogen | urea | 0 |
| switchgrass | nitrogen | nitrogen solutions | 1 |
| eucalyptus | herbicide | generic herbicide | 1 |
| wheat | insecticide | generic insecticide | 1 |

## Fugitive Dust

![Screenshot of the top of the Fugitive Dust tab.](https://github.com/NREL/fpeam/blob/master/src/FPEAM/gui/screenshots/fugitivedust-top.PNG)

**On-Farm Feedstock Measure Type** and **On-Road Feedstock Measure Type**. Fugitive dust generated on the farm is calculated from PM<sub>10</sub> and PM<sub>2.5</sub> rates per acre, while on-road fugitive dust is calculated from the number of trips required to transport the feedstock. Thus the on-farm fugitive dust is calculated from `harvested` feedstock (units of acres) while on-road fugitive dust is calculated from `production` (units of dry short tons).

### Custom Data Filepaths

![Screenshot of the Custom Data Filepaths section of the Fugitive Dust tab.](https://github.com/NREL/fpeam/blob/master/src/FPEAM/gui/screenshots/fugitivedust-customdatafilepaths.PNG)

**On-Farm Factors**. On-farm fugitive dust is calculated from PM<sub>10</sub> and PM<sub>2.5</ub> emission factors given in this dataset.

TABLE: List of columns and data types in fugitive dust emissions factors dataset.

| Column name | Data type | Description |
| :---------- | :-------: | :---------- |
| feedstock	| string | Feedstock being grown |
| tillage_type | string | Type of tillage practice | 
| pollutant | string | Identifies if the rate is for PM<sub>10</sub> or PM<sub>2.5</sub>|
| rate | float | Amount of fugitive dust generated per acre for the feedstock specified in an average year |
| unit_numerator | string | Numerator of rate unit |
| unit_denominator | string | Denominator of rate unit |

TABLE: Example rows in the fugitive dust emissions factors dataset. Source: BTS 2016.

| feedstock | tillage_type | pollutant | rate | unit_numerator | unit_denominator |
| :-------- | :----------- | :-------: | :--: | :--------- | :--------- |
| sorghum stubble | conventional tillage | PM<sub>10</sub> | 1.7 | pound | acre |
| sorghum stubble | conventional tillage | PM<sub>25</sub> | 0.34 | pound | acre |
| sorghum stubble | conventional tillage | PM<sub>10</sub> | 0 | pound | acre |
| sorghum stubble | conventional tillage | PM<sub>25</sub> | 0 | pound | acre |

**On-Road Constants**. The on-road fugitive dust calculation is more involved and requires empirical constants defined in this dataset. For details on the equations used, see the Fugitive Dust subsection of Module Calculations and Assumptions below.

TABLE: Parameter values for calculating particulate matter from feedstock transportation over paved roads. Source: BTS 2016.

|    P             | k<sub>P</sub> (lb/VMT) | a<sub>P</sub> | b<sub>P</sub> | s<sub>L</sub> (g/m<sup>2</sup>) |  W (short tons) |
| :--------------: | :-------------------:  | :-----------: | :-----------: | :-----------------------------: | :-------------: |
| PM<sub>10</sub>  | 0.0022                 | 0.91          | 1.02          | 0.045                           | 3.2             |
| PM<sub>2.5</sub> | 0.00054                | 0.91          | 1.02          | 0.045                           | 3.2             |

TABLE: Parameter values for calculating particulate matter from feedstock transportation over unpaved roads. Source: BTS 2016.

|   P              | k<sub>P</sub> (lb/VMT) | a<sub>P</sub> | b<sub>P</sub> |
| :-------------:  | :-:                    | :-:           | :-:           |
| PM<sub>10</sub>  | 1.5                    | 0.9           | 0.45          |
| PM<sub>2.5</sub> | 0.15                   | 0.9           | 0.45          |


**Road Silt Content**. Silt content of primary roads by state is another dataset required to calculate on-road fugitive dust.

TABLE: Sample values for silt content (s<sub>st</sub>). The complete list can be found in the `fugitive_dust_silt_content` CSV file in the default input data set. Source: BTS 2016.

| st      | s<sub>st</sub> |
| :------ | :------------: |
| Alabama | 3.9            |
| Alaska  | 3.8            |
| Arizona | 3.0            |

## Results

There are no input options on the Results tab, which appears blank when the GUI is first opened and before a scenario is run. While FPEAM is running, log outputs will appear on this tab. After a scenario has completed, basic visualizations will be shown.

# Module Calculations and Assumptions

## MOVES

The MOVES module performs all functions necessary to run MOVES for a single FPEAM scenario, including creating input data files, creating XML files for importing data and defining MOVES runs, executing MOVES, calling the router engine to find transportation routes, and postprocessing raw MOVES results into pollutant amounts by FIPS. 

MOVES requires two types of input files: national files, which are used for all FIPS, and county files which vary by FIPS. The methods `_create_national_data` and `_create_county_data` create the national and county input files using data pulled from the default MOVES database and user input data and parameters. `_create_national_data` is run only once per FPEAM scenario (the files will change based on the scenario year and vehicle selection) while `_create_county_data` is run for every relevant FIPS. Both types of input files are saved to the MOVES data directory and currently are overwritten if a different data directory is not specified for each FPEAM scenario. National input files are named according to their contents, and county input files are further identified by the corresponding FIPS.

The files that MOVES uses to find input data and execute runs are both XML files. One file controls the input data import and is created in the `_create_xml_import` method; the other file ("runspec") controls the MOVES run specifications and is created in the `_create_xml_runspec` method. Both methods are run once for every FIPS in an FPEAM scenario. The import and runspec file are saved in the MOVES data directory and named according to the corresponding FIPS and scenario year. Runspec and import files are overwritten if multiple FPEAM scenarios with the same FIPS and scenario year are run.

After MOVES is run, the `postprocess` method is used to extract raw MOVES output from the MOVES output database and calculate emission rates per vehicle (for start and hotelling emissions) and per vehicle-mile (for transportation emissions). `postprocess` also calls the Router module to obtain vehicle miles traveled through each FIPS involved in a transportation routes. Output of the Router module is used with the emission rates per vehicle-mile to calculate total pollutants in every FIPS through which biomass is transported. The `postprocess` method is called only once per FPEAM scenario, and creates a data table of pollutants that is combined with the output from other modules to create the overall FPEAM results.

Each of these methods is called by the `run` method, which also preprocesses a copy of the feedstock production dataset to determine for which FIPS MOVES should be run. User input parameters determine if MOVES is run once per state, several times per state, or for every FIPS in the input database, and are combined with the feedstock production dataset to pull out a list of FIPS to run MOVES on. `run` also calls the `_get_cached_results` method which checks the MOVES output database to determine if raw MOVES results already exist for any of the FIPS and years involved in an FPEAM scenario. Users can opt to use these cached results with the use_cached_results parameter or run MOVES for every FIPS regardless of whether results already exist.

## NONROAD

The NONROAD module has very similar functionality to the MOVES module; input files for running the model are created and saved, and batch files are used to run NONROAD on the input files. A separate postprocessing method for raw NONROAD output reads in the output files, concatenates the output from various runs together, and adds identifier columns.

The input files NONROAD needs to run are allocate, population and options files, created respectively by the `create_allocate_files`, `create_population_files` and `create_options_files` methods. The allocate files contain indicators for each FIPS within a particular state that, if county-level input data is not provided, are used to allocate state-wide pollutants to the county level. When NONROAD is run via FPEAM, the county-level input data is always provided and so the allocate files are overruled; however, they must be provided for NONROAD to run. The population files are created from the equipment use dataset and information on annual equipment use in the default MOVES database. The `create_population_files` method calculates the number of each equipment type needed per NONROAD run and writes the population to file.

Options files for NONROAD are similar to runspec files for MOVES. They contain specifications for the population and allocate files for a particular NONROAD run, default data, and FPEAM-scenario-specific information such as the year and temperature range. For every valid options file passed to NONROAD, one output file is generated.

After the input files have been generated, the `create_batch_files` method creates batch files for every NONROAD run and master batch files for every state in which NONROAD will be run. The master batch file calls the batch files for the runs defined by the options file.

The `run` method calls all other methods including the `postprocess` method. Postprocessing is different for NONROAD than for MOVES because NONROAD writes raw results to individual text files (one file per NONROAD run) with the extension .out. Postprocessing then involves gathering each .out file, extracting the FPEAM-relevant data, calculating a few pollutants that are not returned by NONROAD, and then concatenating and formatting the NONROAD results so they can be combined with the results of other modules.

## Emission Factors

The EmissionFactors module was developed from a module in the previous version of FPEAM that calculated NO<sub>x</sub> and NH<sub>3</sub> emissions from nitrogen fertilizer application and VOC emissions from herbicide and insecticide application. Rather than limit the module functionality to these pollutants and pollutant causes, the EmissionFactors module was written to calculate any pollutant from any pollutant process if sufficient input data is provided. This flexibility allows users to model pollutants from other fertilizers and agricultural chemicals, and could allow EmissionFactors to replace MOVES and NONROAD in the calculation of agricultural equipment and transportation vehicle emissions, albeit with a loss in spatial detail.

VOC emission factors from application of herbicides and insecticides were calculated from the following equation: ([Zhang et al., 2015](https://onlinelibrary.wiley.com/doi/full/10.1002/bbb.1620)):

VOC (lb/acre/year) = R * I * ER * C<sub>VOC</sub>

where R is the pesticide or herbicide application rate (lb/harvested acre/year), I is the amount of active ingredient per pound of pesticide or herbicide (lb active ingredient/lb chemical, assumed to be 1), ER is the evaporation rate (assumed to be 0.9 per EPA recommendations from emissions inventory improvement program guidance) and C<sub>VOC</sub> is the VOC content in the active ingredient (lb VOC/lb active ingredient, assumed to be 0.835) ( [Huntley 2015](https://www.epa.gov/air-emissions-inventories/2011-national-emissions-inventory-nei-technical-support-document) ).

## Fugitive Dust

The fugitive dust module calculates PM<sub>2.5</sub> and PM<sub>10</sub> emissions from on-farm (harvest and non-harvest) activities and on-road feedstock transportation over paved and unpaved roads.

On-road PM<sub>10</sub> and PM<sub>2.5</sub> emissions are calculated using empirical functions, parameters and data from ([EPA 2006](https://www3.epa.gov/ttn/chief/ap42/ch13/final/c13s0202.pdf), [EPA 2011](https://www3.epa.gov/ttn/chief/ap42/ch13/final/c13s0201.pdf)), [INL 2016](https://inldigitallibrary.inl.gov/sti/6038147.pdf) and [DOE 2016](http://energy.gov/sites/prod/files/2016/07/f33/2016_billion_ton_report_0.pdf). Additional information is available in the Appendix to Chapter 9 of the Billion Ton Study 2016 Update.

EQUATION: On-paved-road particulate matter (*P = {PM<sub>10</sub>, PM<sub>2.5</sub>}*) in lb per vehicle mile traveled over paved roads. Values for parameters <a href="https://www.codecogs.com/eqnedit.php?latex=\inline&space;k_P,&space;s_L,&space;a_P,&space;W" target="_blank"><img src="https://latex.codecogs.com/gif.latex?\inline&space;k_P,&space;s_L,&space;a_P,&space;W" title="k_P, s_L, a_P, W" /></a> and <a href="https://www.codecogs.com/eqnedit.php?latex=\inline&space;b_P" target="_blank"><img src="https://latex.codecogs.com/gif.latex?\inline&space;b_P" title="b_P" /></a> are given in the table following.

<a href="https://www.codecogs.com/eqnedit.php?latex=\text{Rate}_P\text{&space;(lb/VMT)}&space;=&space;k_P&space;s_L^{a_P}&space;W^{b_P}" target="_blank"><img src="https://latex.codecogs.com/gif.latex?\text{Rate}_P\text{&space;(lb/VMT)}&space;=&space;k_P&space;s_L^{a_P}&space;W^{b_P}" title="\text{Rate}_P\text{ (lb/VMT)} = k_P s_L^{a_P} W^{b_P}" /></a>

EQUATION: On-unpaved-road particulate matter (*P = {PM<sub>10</sub>, PM<sub>2.5</sub>}*) in lb per vehicle mile traveled over unpaved roads. Parameter values for k<sub>P</sub>, a<sub>P</sub> and b<sub>P</sub> are given in the table following. The silt content parameter s<sub>st</sub> varies by state; a partial list of values are given in the second table following.

<a href="https://www.codecogs.com/eqnedit.php?latex=\text{Rate}_P&space;\text{&space;(lb/VMT)}&space;=&space;k_P&space;\left&space;(&space;\frac{s_{st}}{12}&space;\right&space;)^{a_P}&space;\left&space;(&space;\frac{W}{3}&space;\right&space;)^{b_P}" target="_blank"><img src="https://latex.codecogs.com/gif.latex?\text{Rate}_P&space;\text{&space;(lb/VMT)}&space;=&space;k_P&space;\left&space;(&space;\frac{s_{st}}{12}&space;\right&space;)^{a_P}&space;\left&space;(&space;\frac{W}{3}&space;\right&space;)^{b_P}" title="\text{Rate}_P \text{ (lb/VMT)} = k_P \left ( \frac{s_{st}}{12} \right )^{a_P} \left ( \frac{W}{3} \right )^{b_P}" /></a>

## Miscellaneous

TABLE: Feedstock bushel weight in dry short tons.

| feedstock | dry short tons per bushel | source |
| :--- | :-----------------------: | :----: | 
| barley | 0.020 | 1. |
| corn | 0.024 | 1. |
| cotton | 0.015 | 1. |
| oats | 0.014 | 1. |
| rice | 0.019 | 2. |
| sorghum | 0.020 | 1. | 
| soybeans | 0.026 | 1. |
| wheat | 0.026 | 1. |

1. Murphy, William J. Tables for Weights and Measurements: Crops. University of Missouri Extension. Available at https://extension2.missouri.edu/G4020. Accessed May 25, 2018.
2. U.S. Department of Agriculture, Office of Weights and Measures. Standard weight per bushel for agricultural commodities. Available at ftp://www.ilga.gov/JCAR/AdminCode/008/00800600ZZ9998bR.html Accessed May 25, 2018.

Any feedstock amounts in mass units should be in dry short tons in the input data. Thus the amounts of any feedstocks traditionally measured in other units such as bushels must be converted before the data is supplied to FPEAM. While this conversion is not done internally, the following tables of average feedstock moisture contents and bushel sizes are provided to users to assist in the units conversion. 

TABLE: Moisture content (mass fraction) at time of transport.

| feedstock | moisture content | source |
| :--- | :--------------: | :----- |
| barley straw |  0.069 | Mani et al. (2004) |
| biomass sorghum | 0.650 | Estimated from Rocateli et al. (2012) |
| corn stover |  0.15 | McAloon et al. (2000) |
| energy cane | 0.1 | Estimated from Miao et al. (2011) |
| eucalyptus | 0.1 | Assumed equal to willow |
| forest residues | 0.5 | Bouchard et al. (2012) |
| hay | 0.069 | Assumed equal to barley straw |
| miscanthus | 0.1 | Estimated from Miao et al. (2011) |
| oats straw | 0.069 | Assumed equal to barley straw |
| pine | 0.1 | Assumed equal to willow |
| poplar | 0.1 | Assumed equal to willow |
| sorghum stubble | 0.650 | Assumed equal to biomass sorghum |
| switchgrass | 0.052 | Mani et al. (2004) |
| wheat straw | 0.083 | Mani et al. (2004) |
| whole tree | 0.5 | Bouchard et al. (2012) |
| willow | 0.1 | Estimated from Miao et al. (2011) |