import unittest

import pandas
from pkg_resources import resource_filename

from FPEAM.Data import Equipment, Production
from FPEAM.EmissionFactors import EmissionFactors
from FPEAM.IO import CONFIG_FOLDER, DATA_FOLDER, load_configs


class EmissionFactorsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config_path = resource_filename("FPEAM", "%s/run_config.ini" % CONFIG_FOLDER)
        cls.config = load_configs(config_path)

        results_path = resource_filename(
            "FPEAM", "%s/outputs/default_emission_factors_results.csv" % DATA_FOLDER
        )
        cls.default_results = pandas.read_csv(
            results_path,
            index_col=False,
            dtype={"region_production": str, "region_destination": str},
        )

        equipment_path = resource_filename(
            "FPEAM", "%s/equipment/bts16_equipment.csv" % DATA_FOLDER
        )
        cls.equipment = Equipment(fpath=equipment_path)

        production_path = resource_filename(
            "FPEAM", "%s/production/production_2015_bc1060.csv" % DATA_FOLDER
        )
        cls.production = Production(fpath=production_path)

    def test_emission_factors_run(self):
        with EmissionFactors(
            config=self.config,
            equipment=self.equipment,
            production=self.production,
        ) as emission_factors:
            emission_factors.run()

        self.assertTrue(
            emission_factors.results.round(3).equals(self.default_results.round(3))
        )
