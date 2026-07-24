import io


# Initializes all variables to their default values
class AttributeValueStorage:
    def __init__(self):

        self.logContents = ""
        self.streamGenerated = io.StringIO()

        # FPEAM home page - Attribute Initialization
        self.scenarioName = ""
        self.projectPath = ""
        self.module = "NONROAD", "MOVES", "emissionfactors", "fugitivedust"
        self.loggerLevel = "DEBUG"
        self.equipment = "data/equipment/bts16_equipment.csv"
        self.production = "data/production/production_2015_bc1060.csv"
        self.feedstockLossFactors = "data/inputs/feedstock_loss_factors.csv"
        self.transportationGraph = "data/inputs/transportation_graph.csv"
        self.vMTPerTruck = 20
        self.backfill = True
        self.useRouterEngine = True

        # Fugitive Dust module - Attribute Initialization
        self.feedMeasureTypeFD = "harvested"
        self.emissionFactorsFD = "data/inputs/fugitive_dust_emission_factors.csv"

        # Emission Factors Module - Attribute Initialization
        self.feedMeasureTypeEF = "harvested"
        self.emissionFactorsEF = "data/inputs/emission_factors.csv"
        self.resourceDistributionEF = "data/inputs/resource_distribution.csv"

        # Nonroad Module - Attribute Initialization
        self.yearNonroad = 2017
        self.feedstockMeasureTypeNon = "harvested"
        self.timeResourceNameNon = "time"
        self.dbHostN = "localhost"
        self.dbUsernameN = "root"
        self.dbNameN = "movesdb20180517"
        self.dbPwdN = "root"
        self.forestryFeedstockNames = "forest whole tree", "forest residues"
        self.regionFipsMapNonroad = "data/inputs/region_fips_map.csv"
        self.nonroadDatafilesPath = "C:/Nonroad"
        self.tempMin = 50.0
        self.tempMax = 68.8
        self.tempMean = 60.0
        self.dieselLHV = 0.12845
        self.dieselNh3Ef = 0.68
        self.dieselThcVocConversion = 1.053
        self.dieselPm10topm25 = 0.97
        self.irrigationFeedstockMeasureType = "planted"
        self.irrigatedFeedstockNames = "corn grain"
        self.irrigation = "data/inputs/irrigation.csv"
        self.encodeNames = True

        # Moves Module - Attribute Initialization
        self.aggregationLevel = "By County"
        self.cachedResults = "Yes"
        self.feedstockMeasureType = "production"
        self.noOfTrucksUsed = 1
        self.yearMoves = 2017
        self.dbHost = "localhost"
        self.dbUsername = "root"
        self.dbName = "movesdb20241112"
        self.dbPwd = "root"
        self.movesDatafilesPath = r"C:\MOVESdatb"
        self.movesPath = r"C:\MOVES5.0"
        self.truckCapacity = "data/inputs/truck_capacity.csv"
        self.avft = "data/inputs/avft.csv"
        self.regionFipsMapMoves = "data/inputs/region_fips_map.csv"
        self.ruralRestricted = 0.30
        self.ruralUnrestricted = 0.28
        self.urbanRestricted = 0.21
        self.urbanUnrestricted = 0.21
        self.month = 10
        self.date = 5
        self.beginningHr = 7
        self.endingHr = 18
        self.dayType = 5
