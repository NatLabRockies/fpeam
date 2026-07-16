import os


# Create Run config file
def runConfigCreation(tmpFolder, attributeValueObj, scenario_name):

    ini_template_string = """[run_config]
## run identifier
scenario_name = '{scenario_name}'
    
## project output directory
project_path = '{project_path}'

## modules to run
modules = {modules}

## logging verbosity level (CRITICAL, ERROR, WARNING, INFO, DEBUG, UNSET)
logger_level = {logger_level}

## use the router engine to calculate vmt by county
use_router_engine = {use_router_engine}

## data paths
equipment = '{equipment}'
production = '{production}'
feedstock_loss_factors = '{feedstock_loss_factors}'

## forest feedstocks have different allocation indicators in NONROAD and onroad fugitive dust calculations
forestry_feedstock_names = {forestry_feedstock_names}

## MOVES routing graph
transportation_graph = '{transportation_graph}'

## if router is not used, assume 20 vehicle miles traveled per biomass production county
vmt_short_haul = {VMT_per_truck}

## truck capacities for feedstock transportation
truck_capacity = '{truck_capacity}'

## graph node locations
node_locations = '{node_locations}'

## data backfill flag
backfill = {backfill}
 """

    my_ini_config = ini_template_string.format(
        scenario_name=attributeValueObj.scenarioName,
        project_path=attributeValueObj.projectPath,
        modules=attributeValueObj.module,
        logger_level=attributeValueObj.loggerLevel,
        equipment=attributeValueObj.equipment,
        production=attributeValueObj.production,
        feedstock_loss_factors=attributeValueObj.feedstockLossFactors,
        forestry_feedstock_names=attributeValueObj.forestryFeedstockNames,
        transportation_graph=attributeValueObj.transportationGraph,
        VMT_per_truck=attributeValueObj.vMTPerTruck,
        truck_capacity=attributeValueObj.truckCapacity,
        node_locations=attributeValueObj.nodeLocations,
        backfill=attributeValueObj.backfill,
        use_router_engine=attributeValueObj.useRouterEngine,
    )

    my_ini_file_path = os.path.join(tmpFolder, f"{scenario_name}_run_config.ini")

    with open(my_ini_file_path, "w") as f:
        f.write(my_ini_config)

    return my_ini_file_path
