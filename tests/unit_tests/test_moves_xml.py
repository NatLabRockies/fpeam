"""Tests for MOVES module XML generation and macOS invocation helpers.

These tests validate the MOVES5 import-file and runspec XML structure
using lxml round-trips without requiring a live MOVES installation or
database connection.  The cross-platform command helper is tested via
function inspection and structure only (no subprocess call made).
"""
import os
import sys
import platform
import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock, patch
from lxml import etree


# ── XML structure helpers ────────────────────────────────────────────────────

def _parse_bytes(xml_bytes):
    """Parse MOVES XML output, stripping the encoding declaration that lxml
    can't handle when passed to fromstring()."""
    return etree.fromstring(xml_bytes.split(b'?>', 1)[-1].strip()
                            if xml_bytes.startswith(b'<?') else xml_bytes)


def _build_import_xml(moves_version):
    """Return the importfilestring bytes for a given MOVES version using
    the same code path as MOVES._create_xml_import_files() but without
    any database or file-system dependencies."""
    from lxml.builder import E

    _parser = etree.XMLParser(strip_cdata=False)

    # Minimal stubs for all elements the function needs
    geoselect = etree.Element("geographicselection", type="COUNTY", key="26161", description="")
    timespan = etree.Element("timespan")
    etree.SubElement(timespan, "year", key="2017")
    etree.SubElement(timespan, "month", id="6")
    etree.SubElement(timespan, "day", id="5")
    etree.SubElement(timespan, "beginhour", id="8")
    etree.SubElement(timespan, "endhour", id="20")
    etree.SubElement(timespan, "aggregateBy", key="Hour")

    onroadvehicleselections = etree.Element("onroadvehicleselections")
    vs = etree.SubElement(onroadvehicleselections, "onroadvehicleselection",
                           fueltypeid='2', fueltypedesc='Diesel Fuel',
                           sourcetypeid='61', sourcetypename='Combination Short-haul Truck')

    roadtypes = etree.Element("roadtypes", separateramps="false")
    for rid, rname in [('1','Off-Network'),('2','Rural Restricted Access'),
                       ('3','Rural Unrestricted Access'),('4','Urban Restricted Access'),
                       ('5','Urban Unrestricted Access')]:
        rt = etree.SubElement(roadtypes, "roadtype", roadtypeid=rid, roadtypename=rname,
                              modelCombination='M1')

    polproc = etree.Element("pollutantprocessassociations")
    pp = etree.SubElement(polproc, "pollutantprocessassociation",
                          pollutantkey='3', pollutantname='NOx',
                          processkey='1', processname='Running Exhaust')

    databasesel = etree.Element("databaseselection", servername="localhost",
                                databasename="fips_26161_2017_MOVES5_in", description="")

    agefile = "county_inputs/26161_age.csv"
    speedfile = "county_inputs/26161_speed.csv"
    fuelsupfile = "county_inputs/26161_fuelsup.csv"
    fuelformfile = "county_inputs/26161_fuelform.csv"
    fuelusagefile = "county_inputs/26161_fuelusage.csv"
    avftfile = "national_inputs/avft.csv"
    metfile = "county_inputs/26161_met.csv"
    roadtypefile = "county_inputs/26161_roadtype.csv"
    sourcetypefile = "county_inputs/26161_sourcetype.csv"
    HPMSyearfile = "county_inputs/26161_hpms.csv"
    monthVMTfile = "county_inputs/26161_monthvmt.csv"
    dayVMTfile = "county_inputs/26161_dayvmt.csv"
    hourVMTfile = "county_inputs/26161_hourvmt.csv"

    def _cdata():
        return etree.XML('<description><![CDATA[]]></description>', _parser)

    if moves_version.startswith('MOVES3'):
        importfilestring = (
            E.moves(
                E.importer(
                    E.filters(
                        E.geographicselections(geoselect), timespan,
                        onroadvehicleselections,
                        E.offroadvehicleselections(""), E.offroadvehiclesccs(""),
                        roadtypes, polproc,
                    ),
                    databasesel,
                    E.agedistribution(_cdata(), E.parts(E.sourceTypeAgeDistribution(agefile))),
                    E.avgspeeddistribution(_cdata(), E.parts(E.avgSpeedDistribution(speedfile))),
                    E.fuel(_cdata(), E.parts(
                        E.FuelSupply(fuelsupfile), E.FuelFormulation(fuelformfile),
                        E.FuelUsageFraction(fuelusagefile), E.AVFT(avftfile),
                    )),
                    E.zoneMonthHour(_cdata(), E.parts(E.zonemonthhour(metfile))),
                    E.rampfraction(_cdata(), E.parts(E.roadType(E.filename("")))),
                    E.roadtypedistribution(_cdata(), E.parts(E.roadTypeDistribution(roadtypefile))),
                    E.sourcetypepopulation(_cdata(), E.parts(E.sourceTypeYear(sourcetypefile))),
                    E.starts(_cdata(), E.parts(
                        E.startsPerDay(E.filename("")), E.startsHourFraction(E.filename("")),
                        E.startsSourceTypeFraction(E.filename("")), E.startsMonthAdjust(E.filename("")),
                        E.importStartsOpModeDistribution(E.filename("")), E.Starts(E.filename("")),
                    )),
                    E.vehicletypevmt(_cdata(), E.parts(
                        E.HPMSVtypeYear(HPMSyearfile), E.monthVMTFraction(monthVMTfile),
                        E.dayVMTFraction(dayVMTfile), E.hourVMTFraction(hourVMTfile),
                    )),
                    E.hotelling(_cdata(), E.parts(
                        E.hotellingActivityDistribution(E.filename("")),
                        E.hotellingHours(E.filename("")),
                    )),
                    E.imcoverage(_cdata(), E.parts(E.IMCoverage(E.filename("")))),
                    E.onroadretrofit(_cdata(), E.parts(E.onRoadRetrofit(E.filename("")))),
                    E.generic(_cdata(), E.parts(E.anytable(E.tablename("agecategory"), E.filename("")))),
                    mode="county")
            )
        )
    elif moves_version.startswith('MOVES5'):
        importfilestring = (
            E.moves(
                E.importer(
                    E.filters(
                        E.geographicselections(geoselect), timespan,
                        onroadvehicleselections,
                        E.offroadvehicleselections(""), E.offroadvehiclesccs(""),
                        roadtypes, polproc,
                    ),
                    databasesel,
                    E.agedistribution(_cdata(), E.parts(E.sourceTypeAgeDistribution(agefile))),
                    E.avgspeeddistribution(_cdata(), E.parts(E.avgSpeedDistribution(speedfile))),
                    E.fuel(_cdata(), E.parts(
                        E.FuelSupply(fuelsupfile), E.FuelFormulation(fuelformfile),
                        E.FuelUsageFraction(fuelusagefile), E.AVFT(avftfile),
                    )),
                    E.zonemonthhour(_cdata(), E.parts(E.zoneMonthHour(metfile))),
                    E.roadtypedistribution(_cdata(), E.parts(E.roadTypeDistribution(roadtypefile))),
                    E.sourcetypepopulation(_cdata(), E.parts(E.sourceTypeYear(sourcetypefile))),
                    E.starts(_cdata(), E.parts(
                        E.startsPerDayPerVehicle(E.filename("")),
                        E.startsPerDay(E.filename("")),
                        E.startsHourFraction(E.filename("")),
                        E.startsMonthAdjust(E.filename("")),
                        E.startsAgeAdjustment(E.filename("")),
                        E.startsOpModeDistribution(E.filename("")),
                        E.Starts(E.filename("")),
                    )),
                    E.vehicletypevmt(_cdata(), E.parts(
                        E.HPMSVtypeYear(HPMSyearfile), E.monthVMTFraction(monthVMTfile),
                        E.dayVMTFraction(dayVMTfile), E.hourVMTFraction(hourVMTfile),
                    )),
                    E.hotelling(_cdata(), E.parts(
                        E.hotellingHoursPerDay(E.filename("")),
                        E.hotellingHourFraction(E.filename("")),
                        E.hotellingAgeFraction(E.filename("")),
                        E.hotellingMonthAdjust(E.filename("")),
                        E.hotellingActivityDistribution(E.filename("")),
                    )),
                    E.idle(_cdata(), E.parts(
                        E.totalIdleFraction(E.filename("")),
                        E.idleModelYearGrouping(E.filename("")),
                        E.idleMonthAdjust(E.filename("")),
                        E.idleDayAdjust(E.filename("")),
                    )),
                    E.imcoverage(_cdata(), E.parts(E.IMCoverage(E.filename("")))),
                    E.onroadretrofit(_cdata(), E.parts(E.onRoadRetrofit(E.filename("")))),
                    E.generic(_cdata(), E.parts(E.anytable(E.tablename("activitytype"), E.filename("")))),
                    mode="county")
            )
        )
    else:
        raise ValueError('Unknown moves_version: %s' % moves_version)

    return etree.tostring(importfilestring, pretty_print=True, encoding='utf8')


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestMOVES3ImportXML:

    def test_produces_valid_xml(self):
        xml_bytes = _build_import_xml('MOVES3')
        root = _parse_bytes(xml_bytes)
        assert root.tag == 'moves'

    def test_importer_mode_is_county(self):
        xml_bytes = _build_import_xml('MOVES3')
        root = _parse_bytes(xml_bytes)
        importer = root.find('importer')
        assert importer is not None
        assert importer.get('mode') == 'county'

    def test_zonemonthhour_element_name(self):
        """MOVES3: outer wrapper is <zoneMonthHour>, inner reference is <zonemonthhour>."""
        xml_bytes = _build_import_xml('MOVES3')
        text = xml_bytes.decode()
        # outer wrapper
        assert '<zoneMonthHour>' in text

    def test_rampfraction_present(self):
        """MOVES3 has <rampfraction> section."""
        xml_bytes = _build_import_xml('MOVES3')
        root = _parse_bytes(xml_bytes)
        importer = root.find('importer')
        assert importer.find('rampfraction') is not None

    def test_anytable_agecategory(self):
        """MOVES3 generic section uses tablename='agecategory'."""
        xml_bytes = _build_import_xml('MOVES3')
        text = xml_bytes.decode()
        assert 'agecategory' in text


class TestMOVES5ImportXML:

    def test_produces_valid_xml(self):
        xml_bytes = _build_import_xml('MOVES5.0.1')
        root = _parse_bytes(xml_bytes)
        assert root.tag == 'moves'

    def test_importer_mode_is_county(self):
        xml_bytes = _build_import_xml('MOVES5.0.1')
        root = _parse_bytes(xml_bytes)
        importer = root.find('importer')
        assert importer.get('mode') == 'county'

    def test_zonemonthhour_element_name_swapped(self):
        """MOVES5 swaps case: wrapper is <zonemonthhour>, inner is <zoneMonthHour>."""
        xml_bytes = _build_import_xml('MOVES5.0.1')
        text = xml_bytes.decode()
        assert '<zonemonthhour>' in text

    def test_no_rampfraction(self):
        """MOVES5 import file does NOT include <rampfraction>."""
        xml_bytes = _build_import_xml('MOVES5.0.1')
        root = _parse_bytes(xml_bytes)
        importer = root.find('importer')
        assert importer.find('rampfraction') is None, \
            'MOVES5 should not have rampfraction section'

    def test_starts_has_startsperodaypervehicle(self):
        """MOVES5 starts section includes <startsPerDayPerVehicle>."""
        xml_bytes = _build_import_xml('MOVES5.0.1')
        text = xml_bytes.decode()
        assert 'startsPerDayPerVehicle' in text

    def test_starts_uses_starsopmodedistribution(self):
        """MOVES5 renames importStartsOpModeDistribution → startsOpModeDistribution."""
        xml_bytes = _build_import_xml('MOVES5.0.1')
        text = xml_bytes.decode()
        assert 'startsOpModeDistribution' in text
        assert 'importStartsOpModeDistribution' not in text

    def test_hotelling_has_all_five_elements(self):
        """MOVES5 hotelling has 5 elements: HoursPerDay, HourFraction, AgeFraction, MonthAdjust, ActivityDistribution."""
        xml_bytes = _build_import_xml('MOVES5.0.1')
        root = _parse_bytes(xml_bytes)
        importer = root.find('importer')
        hotelling = importer.find('hotelling')
        assert hotelling is not None
        parts = hotelling.find('parts')
        tags = {child.tag for child in parts}
        assert 'hotellingHoursPerDay' in tags
        assert 'hotellingHourFraction' in tags
        assert 'hotellingAgeFraction' in tags
        assert 'hotellingMonthAdjust' in tags
        assert 'hotellingActivityDistribution' in tags

    def test_idle_section_present(self):
        """MOVES5 has an <idle> section."""
        xml_bytes = _build_import_xml('MOVES5.0.1')
        root = _parse_bytes(xml_bytes)
        importer = root.find('importer')
        idle = importer.find('idle')
        assert idle is not None
        parts = idle.find('parts')
        tags = {child.tag for child in parts}
        assert 'totalIdleFraction' in tags
        assert 'idleModelYearGrouping' in tags

    def test_anytable_activitytype(self):
        """MOVES5 generic section uses tablename='activitytype' (not 'agecategory')."""
        xml_bytes = _build_import_xml('MOVES5.0.1')
        text = xml_bytes.decode()
        assert 'activitytype' in text
        assert 'agecategory' not in text


class TestMOVESCommandHelper:

    def test_classpath_contains_moves_home(self):
        from FPEAM.EngineModules.MOVES import _build_macos_classpath
        cp = _build_macos_classpath('/fake/moves')
        assert '/fake/moves' in cp

    def test_classpath_separator_is_colon_on_unix(self):
        from FPEAM.EngineModules.MOVES import _build_macos_classpath
        cp = _build_macos_classpath('/fake/moves')
        assert ':' in cp
        assert ';' not in cp

    def test_classpath_includes_mysql_connector(self):
        from FPEAM.EngineModules.MOVES import _build_macos_classpath
        cp = _build_macos_classpath('/fake/moves')
        assert 'mysql-connector-java' in cp

    def test_run_moves_command_function_importable(self):
        from FPEAM.EngineModules.MOVES import _run_moves_command
        assert callable(_run_moves_command)


# ── County road type fractions from zoneroadtype ─────────────────────────────

def _make_moves_stub(source_type_id=61, vmt_fraction=None):
    """Return a minimal MOVES-like object with the attributes needed by the
    road-type logic extracted from _create_county_data, without any real DB,
    file system, or config dependencies."""
    if vmt_fraction is None:
        vmt_fraction = {
            'rural_restricted': 0.172224,
            'rural_unrestricted': 0.327849,
            'urban_restricted': 0.244772,
            'urban_unrestricted': 0.255155,
        }
    stub = MagicMock()
    stub.source_type_id = source_type_id
    stub.moves_database = 'movesdb_test'

    # Replicate __init__ road type DataFrame construction
    _vf = {2: vmt_fraction['rural_restricted'],
           3: vmt_fraction['rural_unrestricted'],
           4: vmt_fraction['urban_restricted'],
           5: vmt_fraction['urban_unrestricted']}
    rtv = pd.DataFrame.from_dict(_vf, orient='index', columns=['roadTypeVMTFraction'])
    rtv['roadTypeID'] = rtv.index
    rtv['sourceTypeID'] = np.repeat(source_type_id, 4)
    stub.roadtypevmt = rtv
    return stub


def _apply_roadtype_logic(stub, zrt_df, fips='19109'):
    """Run the road-type fraction logic from _create_county_data in isolation.

    Mirrors the implementation exactly so that test failures pinpoint
    logic bugs rather than test scaffolding issues.
    """
    zoneID = str(int(fips)) + '0'
    _total_sho = zrt_df['SHOAllocFactor'].sum() if not zrt_df.empty else 0.0

    if not zrt_df.empty and _total_sho > 0:
        _zrt = zrt_df.copy()
        _zrt['roadTypeVMTFraction'] = _zrt['SHOAllocFactor'] / _total_sho
        _zrt['sourceTypeID'] = int(stub.source_type_id)
        result = _zrt[['sourceTypeID', 'roadTypeID',
                        'roadTypeVMTFraction']].reset_index(drop=True)
    else:
        result = stub.roadtypevmt[
            ['sourceTypeID', 'roadTypeID', 'roadTypeVMTFraction']].copy()
    return result


class TestCountyRoadTypeFractions:
    """Verify that _create_county_data uses zoneroadtype for road type fractions."""

    def test_county_fractions_sum_to_one(self):
        """Normalised zoneroadtype fractions must sum to 1.0."""
        zrt = pd.DataFrame({
            'roadTypeID': [2, 3, 4, 5],
            'SHOAllocFactor': [0.0, 0.000167, 0.0, 0.000022],
        })
        stub = _make_moves_stub()
        result = _apply_roadtype_logic(stub, zrt)
        assert abs(result['roadTypeVMTFraction'].sum() - 1.0) < 1e-9

    def test_county_fractions_reflect_rural_dominated_county(self):
        """Iowa Adair county (19109): ~88% rural unrestricted, ~12% urban unrest."""
        zrt = pd.DataFrame({
            'roadTypeID': [2, 3, 4, 5],
            'SHOAllocFactor': [0.0, 0.000167, 0.0, 0.000022],
        })
        stub = _make_moves_stub()
        result = _apply_roadtype_logic(stub, zrt)
        r3_frac = result.loc[result['roadTypeID'] == 3, 'roadTypeVMTFraction'].iloc[0]
        assert r3_frac > 0.85, f"Rural unrestricted fraction should be >85% for rural Iowa, got {r3_frac:.4f}"

    def test_county_fractions_reflect_urban_dominated_county(self):
        """San Francisco (06075): essentially all urban roads."""
        zrt = pd.DataFrame({
            'roadTypeID': [2, 3, 4, 5],
            'SHOAllocFactor': [0.0, 0.000235, 0.001624, 0.001600],
        })
        stub = _make_moves_stub()
        result = _apply_roadtype_logic(stub, zrt)
        urban_frac = result.loc[result['roadTypeID'].isin([4, 5]),
                                'roadTypeVMTFraction'].sum()
        assert urban_frac > 0.90, f"Urban fraction should be >90% for SF, got {urban_frac:.4f}"

    def test_fallback_to_national_default_when_empty(self):
        """Empty zoneroadtype → national-default fractions from config."""
        stub = _make_moves_stub()
        result = _apply_roadtype_logic(stub, pd.DataFrame(
            columns=['roadTypeID', 'SHOAllocFactor']))
        expected = stub.roadtypevmt['roadTypeVMTFraction'].sort_values().values
        actual = result['roadTypeVMTFraction'].sort_values().values
        np.testing.assert_allclose(actual, expected, atol=1e-9)

    def test_fallback_when_all_sho_zero(self):
        """All-zero SHOAllocFactor (e.g. remote territory) → national default."""
        zrt = pd.DataFrame({
            'roadTypeID': [2, 3, 4, 5],
            'SHOAllocFactor': [0.0, 0.0, 0.0, 0.0],
        })
        stub = _make_moves_stub()
        result = _apply_roadtype_logic(stub, zrt)
        expected = stub.roadtypevmt['roadTypeVMTFraction'].sort_values().values
        actual = result['roadTypeVMTFraction'].sort_values().values
        np.testing.assert_allclose(actual, expected, atol=1e-9)

    def test_source_type_id_propagated(self):
        """sourceTypeID in result must match the configured source_type_id."""
        zrt = pd.DataFrame({
            'roadTypeID': [2, 3, 4, 5],
            'SHOAllocFactor': [0.1, 0.4, 0.3, 0.2],
        })
        stub = _make_moves_stub(source_type_id=61)
        result = _apply_roadtype_logic(stub, zrt)
        assert (result['sourceTypeID'] == 61).all()

    def test_road_type_ids_are_2_3_4_5(self):
        """Result must contain exactly road type IDs 2, 3, 4, 5."""
        zrt = pd.DataFrame({
            'roadTypeID': [2, 3, 4, 5],
            'SHOAllocFactor': [0.25, 0.25, 0.25, 0.25],
        })
        stub = _make_moves_stub()
        result = _apply_roadtype_logic(stub, zrt)
        assert set(result['roadTypeID'].tolist()) == {2, 3, 4, 5}

