
## run identifier; defaults to FPEAM scenario name
scenario_name = string(default='')

## start year (equipment year #1)
year = integer(default='2017')

## NONROAD output folder
nonroad_datafiles_path = filepath(default='C:\Nonroad')

# encode feedstock, tillage type and activity names
encode_names = boolean(default=True)

### input data options

## production table row identifier (feedstock_measure in production data)
feedstock_measure_type = string(default='harvested')

## production table row identifier for irrigation activity calculation
irrigation_feedstock_measure_type = string(default='planted')

## equipment table row identifier (resource in equipment data)
time_resource_name = string(default='time')

## list of irrigated feedstocks
irrigated_feedstock_names = string_list(default=list('corn grain'))

### input data files

## production region to NONROAD FIPS mapping
region_fips_map = filepath(default='data/inputs/region_fips_map.csv')

## equipment name to NONROAD equipment name and SCC mapping
nonroad_equipment = filepath(default='data/inputs/nonroad_equipment.csv')

## irrigation dataset
irrigation = filepath(default='data/inputs/irrigation.csv')


### NONROAD database connection options
nonroad_database = string(default='movesdb20220802')
nonroad_db_port = integer(default=3306)
nonroad_db_user = string(default='root')
nonroad_db_pass = string(default='root')
nonroad_db_host = string(default='localhost')


### NONROAD application options
nonroad_path = filepath(default='C:/MOVES3.0/NONROAD/NR08a/', max_length=30)
nonroad_exe = string(default='NONROAD.exe')


### NONROAD input options

## temperature range
nonroad_temp_min = float(default=50.0)
nonroad_temp_max = float(default=68.8)
nonroad_temp_mean = float(default=60.0)

## lower heating value for diesel fuel (mmBTU/gallon) (DOE)
diesel_lhv = float(default=0.12845)

## nh3 emission factor for diesel fuel (grams NH3/mmBTU diesel) (SF2 impact analysis)
diesel_nh3_ef = float(default=0.68)

## VOC conversion factor (EPA NONROAD Conversion Factors for Hydrocarbon Emission Components)
diesel_thc_voc_conversion = float(default=1.053)

## pm10 to PM2.5 conversion factor
diesel_pm10topm25 = float(default=0.97)
