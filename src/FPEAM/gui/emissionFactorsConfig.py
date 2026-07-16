import os


# Create Emission Fcators config file
def emissionFactorsConfigCreation(tmpFolder, attributeValueObj, scenario_name):

    ini_template_string = """[emissionfactors]
    # production table identifier (feedstock_measure in production data)
    feedstock_measure_type = '{feedstock_measure_type}'
    
    # emission factors as lb pollutant per lb resource subtype
    emission_factors = '{emission_factors}'
    
    # resource subtype distribution for all resources
    resource_distribution = '{resource_distribution}'
    
    """

    my_ini_config = ini_template_string.format(
        feedstock_measure_type=attributeValueObj.feedMeasureTypeEF,
        emission_factors=attributeValueObj.emissionFactorsEF,
        resource_distribution=attributeValueObj.resourceDistributionEF,
    )

    my_ini_file_path = os.path.join(tmpFolder, f"{scenario_name}_emissionfactors.ini")

    with open(my_ini_file_path, "w") as f:
        f.write(my_ini_config)

    return my_ini_file_path
