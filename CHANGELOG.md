2019-10-28 (v2.5.0)
-------------------
* add results by production region shapefile export

2019-09-31 (v2.4.0)
-------------------
* add GUI
* update documentation
* route from lat/lon
* corrects trips calculation to prevent negative pollutant values
* add secondary roads to transportation network

2019-05-01 (v2.3.0-beta)
------------------------
* make routing engine available to all modules
* cache routing engine output to temporary directory
* summarize routing output by county and road class

2019-03-07 (v2.2.0-beta)
------------------------
* add backfilling to 0's to data tables
* enforce 30 character limit on NONROAD filepath
* bug fixes for filepath validation
* skip loading routing engine if not needed
* remove state_fips_map as config option
* decreases vmt_short_haul default value
* add updated silt data
* bug fix for use_cached_results
* add loss factors for biorefinery storage

2018-01-09 (v2.1.3-beta)
------------------------
* bug fixes for default filepaths
* bug fixes for filepath validation
* switch pd.read_table to pd.read_csv

2018-01-09 (v2.1.0-beta)
------------------------
* adds irrigation calculations and input data
* removes source category packet from NONROAD options file template
* includes backhaul emissions

2016-09-31 (v1.0.0)
-------------------
* BTS16 rewrite

2013-08-05
----------
    NEIComparision.__init__() line 18
    # Old NEI data from Noah.
    #self.nei_data_by_county = self.db.constantsSchema + ".nei_data_by_county"
    # new NEI data from Jeremy.
    self.nei_data_by_county = "full2008nei.nei_nonroad_nonpoint"

    # @change: Change allocation. Allocation is the amount of the feedstock that actually get's used to produce ethanol.
    # 9/3
    # old code:     self.cellulosicAllocation = 0.34
    #               self.cornGrainAllocation = 0.54
    # new code:     allocation = 0.52
    # @change: convert NEI data from short tons to metric tons.
    # 9/11
    # old code:     nei.nox
    # new code:     nei.nox * 0.907185

2013-07-12 
----------
    Options.NROptionFile._NRoptions() line 287
    @change: NONROAD was not processing files with 10 in it so SG_H10, SG_N10, and SG_T10 inputs
    files were being made correct, but not processing and saving correctly with NONROAD. Hacked around
    this by saving SG_*10 in the same folder but using inputs from SG_*9
    old code: self.run_code
    new code: run_code = self.run_code 
                  if run_code.endswith('0'):
                    # remove the last character.
                    run_code = run_code[:-1]
                    # change the number from 1 to 9
                    split = list(run_code)
                    split[-1] = '9'
                    run_code = "".join(split)
    
    
    Options.NROptionFile._addOPT() line 452
    @change: Changes made to run NONROAD with SG_*9 and save it as SG_*10.  
    Leave folder for output to be the same. Change output file to be run_code given.
    old code: Population File    : """ + self.outPathPopAlo + 'POP\\' + self.state + '_' + self.run_code + """.pop
              Harvested acres    : """ + self.outPathPopAlo + 'ALLOCATE\\' + self.state + '_' + self.run_code + """.alo
    new code: Population File    : """ + self.outPathPopAlo + 'POP\\' + self.state + '_' + new_run_code + """.pop
              Harvested acres    : """ + self.outPathPopAlo + 'ALLOCATE\\' + self.state + '_' + new_run_code + """.alo

2013-07-11
----------
    SinglePassAllocation.__init__() line 60 and 82
    @change: Fugitive dust was being calculated wrong. Causing fug_pm25 to appear to be fug_pm10 and be too high.
    old code: fug_pm25 = fug_pm10 * """+self.residueAllocation+"""
    new code: fug_pm25 = fug_pm25 * """+self.residueAllocation+"""

2013-07-08
----------
    Options.ScenarioOptions._getQuery() line191, 197
    @change: In the database there are rows that have produce = 0, while harvested acres and yield are non-zero.
    Need to skip over these faulty data points.
    new code: dat.prod  > 0.0

2013-07-01
----------
    Population.SwitchGrass.__getNonHarvHrsPerAcre__() line 558
    Comment: SWitch grass population decides what vehicles are used given the year. In the code
    it looked for run code 'NH1', while this was changed to 'N1', so it was allways running
    as if the switch grass was years 3-4, and 6-10 for non-harvest.
    /old code/
    if self.run_code.endswith('NH1'):
    /end/
    /new code/
    if self.run_code.endswith('N1'):    
    /end/


    Population.SwitchGrass.__getTransportHrsPerAcre__() line 623
    comment: was calculating the machine hour population incorrectly.
    Could tell b/c the units were wrong.
    /old code/
    self.pop_130 = ((scenario_yield * self.transportBales) / self.activity_tractor) * 1.1
    /end/
    /new code/
    self.pop_130 = ((scenario_yield) / (self.transportBales * self.activity_tractor) * 1.1
    /end/


    Population.SwitchGrass.__getTransportHrsPerAcre__() line 630
    @deprecated: Changed population equation to use produce instead of yield. Allows population to be in units of yr.
    old code: scenario_yield = (prod/harv_acre) * self.yield_factor  
    new code: scenario_prod = prod * self.yield_factor  
              self.pop_130 = (scenario_prod / (self.transportBales * self.activity_tractor)) * 1.1 # yr

2013-06-26
----------
    Population.CorngGrainPop.__setHarvPopFile__() line 280
    comment: Was calculating yield incorrectly.
    Should be yield = (produce / harvested acres) * conversion constant.
    prior scenario_yield = harv_ac * (56.0) * (1.0-0.155) / 2000.0
    Now it equals to scenario_yield = (prod / harv_ac) * (56.0) * (1.0-0.155) / 2000.0
    /Code/
    scenario_yield = 0
    if harv_ac > 0:
        scenario_yield = (prod / harv_ac) * (56.0) * (1.0-0.155) / 2000.0
    /end/

    CombustionEmissions.populateTables() line 106
    Comment: allocates non-harvest emissions form corn grain to
    corn stover and wheat straw.
    /code/
    # allocate non harvest emissions from cg to cs and ws.
    if operation and operation[0] == 'N' and feedstock == 'CG': 
       # add to cs.
       if self.operationDict['CS'][operation[0]]:
            self._record('CS', row[0], SCC, HP, FuelCons, THC, VOC, CO, NOx, CO2, SO2, PM10, PM25, NH3, description, run_code, writer, queries, self.alloc)
        # add to ws. 
            elif self.operationDict['WS'][operation[0]]:  
                self._record('WS', row[0], SCC, HP, FuelCons, THC, VOC, CO, NOx, CO2, SO2, PM10, PM25, NH3, description, run_code, writer, queries, self.alloc)
            # add to corn grain.
            self._record(feedstock, row[0], SCC, HP, FuelCons, THC, VOC, CO, NOx, CO2, SO2, PM10, PM25, NH3, description, run_code, writer, queries, self.alloc)
        # don't change allocation.
        else: 
            self._record(feedstock, row[0], SCC, HP, FuelCons, THC, VOC, CO, NOx, CO2, SO2, PM10, PM25, NH3, description, run_code, writer, queries)
    /end/

2013-06-21
----------
    CombustionEmissions.populateTables() line 100
    Comment: The function CombustionEmissions._getDescription() was being called before
    NH3 conversions were done. In this funciton it would set new values to these constants
    only in the corn grain feed stock, and never convert the constants back to their normal
    numbers. So the model would only run correctly if corn grain was ran last. Now the 
    run codes can be used in any order.
    /code/
    # change constants back to normal, b/c they can be changes in _getDescription()
    self.LHV = 128450.0 / 1e6  
    self.NH3_EF = 0.68
    self.vocConversion = 1.053
    /end/

2013-06-20
----------
    Population.CornGrainPop() line 244
    Removed the *.1. because corng grain is a one year cycle
    and not a 10 year cycle.
    /Code/
    '''
    @deprecated: this is not a 10 year cycle!
    harv_ac = dat[2] * 0.1    #10% of acres in each year of the 10-yr production cycle
    prod = dat[3] / 10.0 
    '''
    harv_ac = dat[2]     
    prod = dat[3]
    /end/

    Fertilizer.getFrtDistribution() line 59
    Added function in order to either collect fertilizer distribution from the db,
    or to allow the user to input their own distribution data.
    /code/
    '''
        Get fertilizer distribution. The user can either input their own distribution, 
        or use the predefined distribution on the db.
        @param fertDistribution: Distribution of the the five different fertilizers. 
        @return: Distribution of the five different fertilizers as a percentage. Must sum up to 1.
        Order: annhydrous_amonia, ammonium_nitrate, ammonium_sulfate, urea, nsol. (list(string))
        '''    
        def getFrtDistribution(self, fertDistribution=False):
            if not fertDistribution:
                query = """SELECT * 
                        FROM """ + self.db.constantsSchema + """.n_fert_distribution""" 
                fertDistribution = self.db.output(query, self.db.constantsSchema)
                # convert db data to usable strings.
                fertDistribution = [str(f) for f in fertDistribution[0]]
                return fertDistribution
            else: 
                return fertDistribution
    /end/

2013-06-01
----------
    Population.SwitchgrassPop.append_Pop() line 524
    /code/
    '''
    **********************************
    @attention: 'SG_N' was SG_NH before,
    meaning that part of the code never ran 
    giving false results.
    ***********************************
    '''
    if self.run_code.startswith('SG_N'): 
        self.__getNonHarvHrsPerAcre__(harv_ac)
    elif self.run_code.startswith('SG_H'):
        self.__getHarvHrsPerAcre__(harv_ac, prod)
    else:
        self.__getTransportHrsPerAcre__(harv_ac, prod)
    /end/
    Comment: Changed SG_NH to SG_N. Before the the non harvest run code
    was running as if it was the transport run code.
 
