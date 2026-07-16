import os


# Create Fugitve Dust config file
def fugitiveDustConfigCreation(tmpFolder, attributeValueObj, scenario_name):
    ini_template_string = """[fugitivedust]

## production table identifier (feedstock_measure in production data)
onfarm_feedstock_measure_type = '{onfarm_feedstock_measure_type}'
onroad_feedstock_measure_type = '{onroad_feedstock_measure_type}'

## particulate matter emission factors by acreage
fugitive_dust_factors = '{fugitive_dust_factors}'

## road silt content by state
silt_content = '{silt_content}'

## constants for calculating onroad fugitive dust
fugitive_dust_onroad_constants = '{fugitive_dust_onroad_constants}'
"""

    my_ini_config = ini_template_string.format(
        onfarm_feedstock_measure_type=attributeValueObj.OnfarmFeedMeasureTypeFD,
        onroad_feedstock_measure_type=attributeValueObj.OnroadFeedMeasureTypeFD,
        fugitive_dust_factors=attributeValueObj.emissionFactorsFD,
        silt_content=attributeValueObj.siltContent,
        fugitive_dust_onroad_constants=attributeValueObj.onroadConstants,
    )

    my_ini_file_path = os.path.join(tmpFolder, f"{scenario_name}_fugitivedust.ini")

    with open(my_ini_file_path, "w") as f:
        f.write(my_ini_config)

    return my_ini_file_path
