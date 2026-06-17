import os


# Create MOVES config file
def movesConfigCreation(tmpFolder, attributeValueObj, scenario_name):

    ini_template_string = """[moves]
    # run identifier
    scenario_name = '{scenario_name}'
    
    
    ### MOVES execution options

    ## use a single representative county for all counties in each state
    moves_by_state = {aggregation_level_state}
    
    ## use a single representative county for each crop for all counties in each state
    moves_by_state_and_feedstock = {aggregation_level_state_feedstock}

    ## use existing results in MOVES output database or run MOVES for all counties
    use_cached_results = {use_cached_results}

    ## production table identifier (feedstock_measure in production data)
    feedstock_measure_type = '{feedstock_measure_type}'

    ## population of combination short-haul trucks per trip
    pop_short_haul = {no_of_trucks_used}
    
    ## vehicle category: combination trucks
    hpmsv_type_id = {hpmsv_type_id}
    
    ## specific vehicle type: short-haul combination truck
    source_type_id = {source_type_id}

    ## start year (equipment year #1)
    year = {year}
    
    ### MOVES database connection options
    moves_db_host = '{moves_db_host}'
    moves_db_user = '{moves_db_user}'
    moves_db_pass = '{moves_db_pass}'
    moves_database = '{moves_database}'
    moves_output_db = '{moves_output_db}'
    
    
    ### MOVES application options
    
    ## the moves version used only for human reference; it's ignored by MOVES
    moves_version = 'MOVES'
    
    ## this directory contains all input files created for MOVES runs
    moves_datafiles_path = '{moves_datafiles_path}'
    
    ## use this path to specify which version of MOVES should be run
    moves_path = '{moves_path}'
    
    ### MySQL options
    mysql_binary = '{mysql_bin_path}'
    
    
    ### input files

    ## fuel fraction by engine type
    avft = '{avft}'

    ## production region to MOVES FIPS mapping
    region_fips_map = '{region_fips_map}'
    
    
    ### MOVES input options

    ## fraction of VMT by road type (must sum to 1)
    [vmt_fraction]
    rural_restricted = {rural_restricted}
    rural_unrestricted = {rural_unrestricted}
    urban_restricted = {urban_restricted}
    urban_unrestricted = {urban_unrestricted}

    ## timespan(s)
    [moves_timespan]
    month = {month}
    day = {day_type}
    beginning_hour = {beginning_hour}
    ending_hour = {ending_hour}
    
    # MOVES pollutant dictionary (pollutant name to pollutant ID)
    [pollutant_dict]
    NH3 = 30
    CO = 2
    NOX = 3
    PM10 = 100
    PM25 = 110
    SO2 = 31
    VOC = 87
    """

    my_ini_config = ini_template_string.format(scenario_name=attributeValueObj.scenarioName,
                                               aggregation_level_state=attributeValueObj.aggregation_level_state,
                                               aggregation_level_state_feedstock=attributeValueObj.aggregation_level_state_feedstock,
                                               use_cached_results=attributeValueObj.cachedResults,
                                               feedstock_measure_type=attributeValueObj.feedstockMeasureTypeMoves,
                                               no_of_trucks_used=attributeValueObj.noOfTrucksUsed,
                                               hpmsv_type_id=attributeValueObj.hpmsvTypeId,
                                               source_type_id=attributeValueObj.sourceTypeId,
                                               year=attributeValueObj.yearMoves,
                                               moves_path=attributeValueObj.movesPath,
                                               mysql_bin_path=attributeValueObj.mysqlBinPath,
                                               moves_datafiles_path=attributeValueObj.movesDatafilesPath,
                                               moves_db_host=attributeValueObj.dbHost,
                                               moves_db_user=attributeValueObj.dbUsername,
                                               moves_db_pass=attributeValueObj.dbPwd,
                                               moves_database=attributeValueObj.dbName,
                                               moves_output_db=attributeValueObj.outDb,
                                               avft=attributeValueObj.avft,
                                               region_fips_map=attributeValueObj.regionFipsMapMoves,
                                               rural_restricted=attributeValueObj.ruralRestricted,
                                               rural_unrestricted=attributeValueObj.ruralUnrestricted,
                                               urban_restricted=attributeValueObj.urbanRestricted,
                                               urban_unrestricted=attributeValueObj.urbanUnrestricted,
                                               month=attributeValueObj.month, date=attributeValueObj.date,
                                               beginning_hour=attributeValueObj.beginningHr,
                                               ending_hour=attributeValueObj.endingHr,
                                               day_type=attributeValueObj.dayType)

    my_ini_file_path = os.path.join(tmpFolder, f"{scenario_name}_moves.ini")

    with open(my_ini_file_path, 'w') as f:
        f.write(my_ini_config)

    return my_ini_file_path
