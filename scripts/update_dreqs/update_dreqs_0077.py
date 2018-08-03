#!/usr/bin/env python
"""
update_dreqs_0077.py

This file adds data and variable requests for CERFACS for both models for all the
experiments for variant_label r21i1p1f2.
"""
import argparse
from datetime import datetime
import logging.config
import sys

from cf_units import date2num, CALENDAR_GREGORIAN

import django
django.setup()

from pdata_app.models import (DataRequest, VariableRequest, Experiment,
                              Institute, ClimateModel, Project, Settings)
from pdata_app.utils.dbapi import match_one, get_or_create


__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)



def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Add additional data requests')
    parser.add_argument('-l', '--log-level', help='set logging level to one of '
        'debug, info, warn (the default), or error')
    parser.add_argument('--version', action='version',
        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()

    return args


def main(args):
    """
    Main entry point
    """
    new_vreqs = [
        {'table_name': 'AERmon',
         'long_name': 'Cloud Optical Depth',
         'units': '1',
         'var_name': 'cod',
         'standard_name': 'atmosphere_optical_thickness_due_to_cloud',
         'cell_methods': 'area: time: mean',
         'positive': '',
         'variable_type': 'real',
         'dimensions': 'longitude latitude time',
         'cmor_name': 'cod',
         'modeling_realm': 'aerosol',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': '19bf238e-81b1-11e6-92de-ac72891c3257'},
        {'table_name': 'AERmon',
         'long_name': 'liquid water path',
         'units': 'kg m-2',
         'var_name': 'lwp',
         'standard_name': 'atmosphere_mass_content_of_cloud_liquid_water',
         'cell_methods': 'area: time: mean',
         'positive': '',
         'variable_type': 'real',
         'dimensions': 'longitude latitude time',
         'cmor_name': 'lwp',
         'modeling_realm': 'aerosol',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': '19bf71ae-81b1-11e6-92de-ac72891c3257'},
        {'table_name': 'AERmon',
         'long_name': 'black carbon aod at 550nm',
         'units': '1',
         'var_name': 'od550bc',
         'standard_name': 'atmosphere_optical_thickness_due_to_black_carbon_ambient_aerosol',
         'cell_methods': 'area: time: mean',
         'positive': '',
         'variable_type': 'real',
         'dimensions': 'longitude latitude time',
         'cmor_name': 'od550bc',
         'modeling_realm': 'aerosol',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': '19bf8f18-81b1-11e6-92de-ac72891c3257'},
        {'table_name': 'AERmon',
         'long_name': 'Dust Optical Depth at 550nm',
         'units': '1',
         'var_name': 'od550dust',
         'standard_name': 'atmosphere_optical_thickness_due_to_dust_ambient_aerosol',
         'cell_methods': 'area: time: mean',
         'positive': '',
         'variable_type': 'real',
         'dimensions': 'longitude latitude time',
         'cmor_name': 'od550dust',
         'modeling_realm': 'aerosol',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': '19bf97d8-81b1-11e6-92de-ac72891c3257'},
        {'table_name': 'AERmon',
         'long_name': 'Total Organic Aerosol Optical Depth at 550nm',
         'units': '1',
         'var_name': 'od550oa',
         'standard_name': 'atmosphere_optical_thickness_due_to_particulate_organic_matter_ambient_aerosol',
         'cell_methods': 'area: time: mean',
         'positive': '',
         'variable_type': 'real',
         'dimensions': 'longitude latitude time',
         'cmor_name': 'od550oa',
         'modeling_realm': 'aerosol',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': '19c03a6c-81b1-11e6-92de-ac72891c3257'},
        {'table_name': 'AERmon',
         'long_name': 'Sea Salt Aersol Optical Depth at 550nm',
         'units': '1',
         'var_name': 'od550ss',
         'standard_name': 'atmosphere_optical_thickness_due_to_seasalt_ambient_aerosol',
         'cell_methods': 'area: time: mean',
         'positive': '',
         'variable_type': 'real',
         'dimensions': 'longitude latitude time',
         'cmor_name': 'od550ss',
         'modeling_realm': 'aerosol',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': '19bec380-81b1-11e6-92de-ac72891c3257'},
        {'table_name': 'AERmon',
         'long_name': 'Tropopause Air Pressure',
         'units': 'Pa',
         'var_name': 'ptp',
         'standard_name': 'tropopause_air_pressure',
         'cell_methods': 'area: time: mean',
         'positive': '',
         'variable_type': 'real',
         'dimensions': 'longitude latitude time',
         'cmor_name': 'ptp',
         'modeling_realm': 'aerosol',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': '19be3f96-81b1-11e6-92de-ac72891c3257'},
        {'table_name': 'AERmon',
         'long_name': 'TOA Outgoing Aerosol-Free Longwave Radiation',
         'units': 'W m-2',
         'var_name': 'rlutaf',
         'standard_name': 'toa_outgoing_longwave_flux',
         'cell_methods': 'area: time: mean',
         'positive': 'up',
         'variable_type': 'real',
         'dimensions': 'longitude latitude time',
         'cmor_name': 'rlutaf',
         'modeling_realm': 'aerosol',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': '8feba756-267c-11e7-8933-ac72891c3257'},
        {'table_name': 'AERmon',
         'long_name': 'TOA Outgoing Clear-Sky, Aerosol-Free Longwave Radiation',
         'units': 'W m-2',
         'var_name': 'rlutcsaf',
         'standard_name': 'toa_outgoing_longwave_flux_assuming_clear_sky',
         'cell_methods': 'area: time: mean',
         'positive': 'up',
         'variable_type': 'real',
         'dimensions': 'longitude latitude time',
         'cmor_name': 'rlutcsaf',
         'modeling_realm': 'aerosol',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': '8febbae8-267c-11e7-8933-ac72891c3257'},
        {'table_name': 'AERmon',
         'long_name': 'TOA Outgoing Aerosol-Free Shortwave Radiation',
         'units': 'W m-2',
         'var_name': 'rsutaf',
         'standard_name': 'toa_outgoing_shortwave_flux',
         'cell_methods': 'area: time: mean',
         'positive': 'up',
         'variable_type': 'real',
         'dimensions': 'longitude latitude time',
         'cmor_name': 'rsutaf',
         'modeling_realm': 'aerosol',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': '8feb097c-267c-11e7-8933-ac72891c3257'},
        {'table_name': 'AERmon',
         'long_name': 'Tropopause Air Temperature',
         'units': 'K',
         'var_name': 'tatp',
         'standard_name': 'tropopause_air_temperature',
         'cell_methods': 'area: time: mean',
         'positive': '',
         'variable_type': 'real',
         'dimensions': 'longitude latitude time',
         'cmor_name': 'tatp',
         'modeling_realm': 'aerosol',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': '19bf81b2-81b1-11e6-92de-ac72891c3257'},
        {'table_name': 'AERmon',
         'long_name': 'Total Ozone Column',
         'units': 'm',
         'var_name': 'toz',
         'standard_name': 'equivalent_thickness_at_stp_of_atmosphere_ozone_content',
         'cell_methods': 'area: time: mean',
         'positive': '',
         'variable_type': 'real',
         'dimensions': 'longitude latitude time',
         'cmor_name': 'toz',
         'modeling_realm': 'aerosol',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': '19bf12b8-81b1-11e6-92de-ac72891c3257'},
        {'table_name': 'AERmon',
         'long_name': 'air temperature at cloud top',
         'units': 'K',
         'var_name': 'ttop',
         'standard_name': 'air_temperature_at_cloud_top',
         'cell_methods': 'area: time: mean',
         'positive': '',
         'variable_type': 'real',
         'dimensions': 'longitude latitude time',
         'cmor_name': 'ttop',
         'modeling_realm': 'aerosol',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': '19be9072-81b1-11e6-92de-ac72891c3257'},
        {'table_name': 'AERmon',
         'long_name': 'Tropopause Altitude above Geoid',
         'units': 'm',
         'var_name': 'ztp',
         'standard_name': 'tropopause_altitude',
         'cell_methods': 'area: time: mean',
         'positive': '',
         'variable_type': 'real',
         'dimensions': 'longitude latitude time',
         'cmor_name': 'ztp',
         'modeling_realm': 'aerosol',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': '19be55a8-81b1-11e6-92de-ac72891c3257'},
        {'table_name': 'Emon',
         'long_name': 'Total water content of soil layer',
         'units': 'kg m-2',
         'var_name': 'mrsol',
         'standard_name': 'moisture_content_of_soil_layer',
         'cell_methods': 'area: mean where land time: mean',
         'positive': '',
         'variable_type': 'real',
         'dimensions': 'longitude latitude sdepth time',
         'cmor_name': 'mrsol',
         'modeling_realm': 'land',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': '8b803cac-4a5b-11e6-9cd2-ac72891c3257'},
        {'table_name': 'Emon',
         'long_name': 'Daily Maximum Near-Surface Wind Speed',
         'units': 'm s-1',
         'var_name': 'sfcWindmax',
         'standard_name': 'wind_speed',
         'cell_methods': 'area: mean time: maximum within days time: mean over days',
         'positive': '',
         'variable_type': 'real',
         'dimensions': 'longitude latitude time height10m',
         'cmor_name': 'sfcWindmax',
         'modeling_realm': 'atmos',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': 'fee11078-5270-11e6-bffa-5404a60d96b5'},
        {'table_name': 'Emon',
         'long_name': 'Convective Condensed Water Path',
         'units': 'kg m-2',
         'var_name': 'clwvic',
         'standard_name': 'atmosphere_convective_cloud_condensed_water_content',
         'cell_methods': 'area: time: mean',
         'positive': '',
         'variable_type': 'real',
         'dimensions': 'longitude latitude time',
         'cmor_name': 'clwvic',
         'modeling_realm': 'atmos',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': '7b064354-a220-11e6-a33f-ac72891c3257'},
        {'table_name': 'Emon',
         'long_name': 'Net Carbon Mass Flux out of Atmosphere due to Net Ecosystem Productivity on Land.',
         'units': 'kg m-2 s-1',
         'var_name': 'nep',
         'standard_name': 'surface_net_downward_mass_flux_of_carbon_dioxide_expressed_as_carbon_due_to_all_land_processes_excluding_anthropogenic_land_use_change',
         'cell_methods': 'area: mean where land time: mean',
         'positive': 'down',
         'variable_type': 'real',
         'dimensions': 'longitude latitude time',
         'cmor_name': 'nep',
         'modeling_realm': 'land',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': 'd2290cee-4a9f-11e6-b84e-ac72891c3257'},
        {'table_name': 'Emon',
         'long_name': 'Potential Evapotranspiration',
         'units': 'kg m-2 s-1',
         'var_name': 'evspsblpot',
         'standard_name': 'water_potential_evaporation_flux',
         'cell_methods': 'area: mean where land time: mean',
         'positive': '',
         'variable_type': 'real',
         'dimensions': 'longitude latitude time',
         'cmor_name': 'evspsblpot',
         'modeling_realm': 'land',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': '6f68edb4-9acb-11e6-b7ee-ac72891c3257'},
        {'table_name': 'EmonZ',
         'long_name': 'u-tendency nonorographic gravity wave drag',
         'units': 'm s-2',
         'var_name': 'utendnogw',
         'standard_name': 'tendency_of_eastward_wind_due_to_nonorographic_gravity_wave_drag',
         'cell_methods': 'longitude: mean time: mean',
         'positive': '',
         'variable_type': 'real',
         'dimensions': 'latitude plev39 time',
         'cmor_name': 'utendnogw',
         'modeling_realm': 'atmos',
         'frequency': 'mon',
         'cell_measures': '',
         'uid': '8183e5fa-f906-11e6-a176-5404a60d96b5'},
        {'table_name': 'Amon',
         'long_name': 'Ozone volume mixing ratio',
         'units': 'mol mol-1',
         'var_name': 'o3',
         'standard_name': 'mole_fraction_of_ozone_in_air',
         'cell_methods': 'time: mean',
         'positive': '',
         'variable_type': 'real',
         'dimensions': 'longitude latitude plev19 time',
         'cmor_name': 'o3',
         'modeling_realm': 'atmos atmosChem',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': '59fbf2a8-c77d-11e6-8a33-5404a60d96b5'},
        {'table_name': 'Amon',
         'long_name': 'Total Atmospheric Mass of CO2',
         'units': 'kg',
         'var_name': 'co2mass',
         'standard_name': 'atmosphere_mass_of_carbon_dioxide',
         'cell_methods': 'area: time: mean',
         'positive': '',
         'variable_type': 'real',
         'dimensions': ' time',
         'cmor_name': 'co2mass',
         'modeling_realm': 'atmos',
         'frequency': 'mon',
         'cell_measures': '',
         'uid': 'baab2d9e-e5dd-11e5-8482-ac72891c3257'},
        {'table_name': 'Amon',
         'long_name': 'Global Mean Mole Fraction of CH4',
         'units': '1e-09',
         'var_name': 'ch4global',
         'standard_name': 'mole_fraction_of_methane_in_air',
         'cell_methods': 'area: time: mean',
         'positive': '',
         'variable_type': 'real',
         'dimensions': ' time',
         'cmor_name': 'ch4global',
         'modeling_realm': 'atmos atmosChem',
         'frequency': 'mon',
         'cell_measures': '',
         'uid': 'baa9e22c-e5dd-11e5-8482-ac72891c3257'},
        {'table_name': 'Amon',
         'long_name': 'Global Mean Mole Fraction of N2O',
         'units': '1e-09',
         'var_name': 'n2oglobal',
         'standard_name': 'mole_fraction_of_nitrous_oxide_in_air',
         'cell_methods': 'area: time: mean',
         'positive': '',
         'variable_type': 'real',
         'dimensions': ' time',
         'cmor_name': 'n2oglobal',
         'modeling_realm': 'atmos atmosChem',
         'frequency': 'mon',
         'cell_measures': '',
         'uid': 'bab221e4-e5dd-11e5-8482-ac72891c3257'},
        {'table_name': 'CFmon',
         'long_name': 'TOA Outgoing Shortwave Radiation in 4XCO2 Atmosphere',
         'units': 'W m-2',
         'var_name': 'rsut4co2',
         'standard_name': 'toa_outgoing_shortwave_flux',
         'cell_methods': 'area: time: mean',
         'positive': 'up',
         'variable_type': 'real',
         'dimensions': 'longitude latitude time',
         'cmor_name': 'rsut4co2',
         'modeling_realm': 'atmos',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': 'bab68158-e5dd-11e5-8482-ac72891c3257'},
        {'table_name': 'CFmon',
         'long_name': 'TOA Outgoing Longwave Radiation 4XCO2 Atmosphere',
         'units': 'W m-2',
         'var_name': 'rlut4co2',
         'standard_name': 'toa_outgoing_longwave_flux',
         'cell_methods': 'area: time: mean',
         'positive': 'up',
         'variable_type': 'real',
         'dimensions': 'longitude latitude time',
         'cmor_name': 'rlut4co2',
         'modeling_realm': 'atmos',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': 'bab59a22-e5dd-11e5-8482-ac72891c3257'},
        {'table_name': 'CFmon',
         'long_name': 'TOA Outgoing Clear-Sky Shortwave Radiation 4XCO2 Atmosphere',
         'units': 'W m-2',
         'var_name': 'rsutcs4co2',
         'standard_name': 'toa_outgoing_shortwave_flux_assuming_clear_sky',
         'cell_methods': 'area: time: mean',
         'positive': 'up',
         'variable_type': 'real',
         'dimensions': 'longitude latitude time',
         'cmor_name': 'rsutcs4co2',
         'modeling_realm': 'atmos',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': 'bab699c2-e5dd-11e5-8482-ac72891c3257'},
        {'table_name': 'CFmon',
         'long_name': 'TOA Outgoing Clear-Sky Longwave Radiation 4XCO2 Atmosphere',
         'units': 'W m-2',
         'var_name': 'rlutcs4co2',
         'standard_name': 'toa_outgoing_longwave_flux_assuming_clear_sky',
         'cell_methods': 'area: time: mean',
         'positive': 'up',
         'variable_type': 'real',
         'dimensions': 'longitude latitude time',
         'cmor_name': 'rlutcs4co2',
         'modeling_realm': 'atmos',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': 'bab5b822-e5dd-11e5-8482-ac72891c3257'},
        {'table_name': 'CFmon',
         'long_name': 'Upwelling Longwave Radiation 4XCO2 Atmosphere',
         'units': 'W m-2',
         'var_name': 'rlu4co2',
         'standard_name': 'upwelling_longwave_flux_in_air',
         'cell_methods': 'area: time: mean',
         'positive': 'up',
         'variable_type': 'real',
         'dimensions': 'longitude latitude alevhalf time',
         'cmor_name': 'rlu4co2',
         'modeling_realm': 'atmos',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': 'bab56b24-e5dd-11e5-8482-ac72891c3257'},
        {'table_name': 'CFmon',
         'long_name': 'Upwelling Shortwave Radiation 4XCO2 Atmosphere',
         'units': 'W m-2',
         'var_name': 'rsu4co2',
         'standard_name': 'upwelling_shortwave_flux_in_air',
         'cell_methods': 'area: time: mean',
         'positive': 'up',
         'variable_type': 'real',
         'dimensions': 'longitude latitude alevhalf time',
         'cmor_name': 'rsu4co2',
         'modeling_realm': 'atmos',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': 'bab6438c-e5dd-11e5-8482-ac72891c3257'},
        {'table_name': 'CFmon',
         'long_name': 'Downwelling Longwave Radiation 4XCO2 Atmosphere',
         'units': 'W m-2',
         'var_name': 'rld4co2',
         'standard_name': 'downwelling_longwave_flux_in_air',
         'cell_methods': 'area: time: mean',
         'positive': 'down',
         'variable_type': 'real',
         'dimensions': 'longitude latitude alevhalf time',
         'cmor_name': 'rld4co2',
         'modeling_realm': 'atmos',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': 'bab51a98-e5dd-11e5-8482-ac72891c3257'},
        {'table_name': 'CFmon',
         'long_name': 'Downwelling Shortwave Radiation 4XCO2 Atmosphere',
         'units': 'W m-2',
         'var_name': 'rsd4co2',
         'standard_name': 'downwelling_shortwave_flux_in_air',
         'cell_methods': 'area: time: mean',
         'positive': 'down',
         'variable_type': 'real',
         'dimensions': 'longitude latitude alevhalf time',
         'cmor_name': 'rsd4co2',
         'modeling_realm': 'atmos',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': 'bab5cf9c-e5dd-11e5-8482-ac72891c3257'},
        {'table_name': 'CFmon',
         'long_name': 'Upwelling Clear-Sky Longwave Radiation 4XCO2 Atmosphere',
         'units': 'W m-2',
         'var_name': 'rlucs4co2',
         'standard_name': 'upwelling_longwave_flux_in_air_assuming_clear_sky',
         'cell_methods': 'area: time: mean',
         'positive': 'up',
         'variable_type': 'real',
         'dimensions': 'longitude latitude alevhalf time',
         'cmor_name': 'rlucs4co2',
         'modeling_realm': 'atmos',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': 'bab571f0-e5dd-11e5-8482-ac72891c3257'},
        {'table_name': 'CFmon',
         'long_name': 'Upwelling Clear-Sky Shortwave Radiation 4XCO2 Atmosphere',
         'units': 'W m-2',
         'var_name': 'rsucs4co2',
         'standard_name': 'upwelling_shortwave_flux_in_air_assuming_clear_sky',
         'cell_methods': 'area: time: mean',
         'positive': 'up',
         'variable_type': 'real',
         'dimensions': 'longitude latitude alevhalf time',
         'cmor_name': 'rsucs4co2',
         'modeling_realm': 'atmos',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': 'bab64a6c-e5dd-11e5-8482-ac72891c3257'},
        {'table_name': 'CFmon',
         'long_name': 'Downwelling Clear-Sky Longwave Radiation 4XCO2 Atmosphere',
         'units': 'W m-2',
         'var_name': 'rldcs4co2',
         'standard_name': 'downwelling_longwave_flux_in_air_assuming_clear_sky',
         'cell_methods': 'area: time: mean',
         'positive': 'down',
         'variable_type': 'real',
         'dimensions': 'longitude latitude alevhalf time',
         'cmor_name': 'rldcs4co2',
         'modeling_realm': 'atmos',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': 'bab52196-e5dd-11e5-8482-ac72891c3257'},
        {'table_name': 'CFmon',
         'long_name': 'Downwelling Clear-Sky Shortwave Radiation 4XCO2 Atmosphere',
         'units': 'W m-2',
         'var_name': 'rsdcs4co2',
         'standard_name': 'downwelling_shortwave_flux_in_air_assuming_clear_sky',
         'cell_methods': 'area: time: mean',
         'positive': 'down',
         'variable_type': 'real',
         'dimensions': 'longitude latitude alevhalf time',
         'cmor_name': 'rsdcs4co2',
         'modeling_realm': 'atmos',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': 'bab5d65e-e5dd-11e5-8482-ac72891c3257'}
    ]

    institute_details = {
        'id': 'CNRM-CERFACS',
        'model_ids': ['CNRM-CM6-1-HR', 'CNRM-CM6-1'],
        'calendar': CALENDAR_GREGORIAN
    }

    experiments = {
        'control-1950': {'start_date': datetime(1950, 1, 1),
                         'end_date': datetime(2050, 1, 1)},
        'highres-future': {'start_date': datetime(2015, 1, 1),
                           'end_date': datetime(2051, 1, 1)},
        'hist-1950': {'start_date': datetime(1950, 1, 1),
                      'end_date': datetime(2015, 1, 1)},
        'highresSST-present': {'start_date': datetime(1950, 1, 1),
                               'end_date': datetime(2015, 1, 1)},
        'highresSST-future': {'start_date': datetime(2015, 1, 1),
                              'end_date': datetime(2051, 1, 1)},
        'spinup-1950': {'start_date': datetime(1950, 1, 1),
                        'end_date': datetime(1980, 1, 1)},
    }

    variant_label = 'r21i1p1f2'

    # Experiment
    new_dreqs = [
        'cod_AERmon',
        'lwp_AERmon',
        'od550bc_AERmon',
        'od550dust_AERmon',
        'od550oa_AERmon',
        'od550ss_AERmon',
        'ptp_AERmon',
        'rlutaf_AERmon',
        'rlutcsaf_AERmon',
        'rsutaf_AERmon',
        'tatp_AERmon',
        'toz_AERmon',
        'ttop_AERmon',
        'ztp_AERmon',
        'ch4global_Amon',
        'co2mass_Amon',
        'n2oglobal_Amon',
        'o3_Amon',
        'rld4co2_CFmon',
        'rldcs4co2_CFmon',
        'rlu4co2_CFmon',
        'rlucs4co2_CFmon',
        'rlut4co2_CFmon',
        'rlutcs4co2_CFmon',
        'rsd4co2_CFmon',
        'rsdcs4co2_CFmon',
        'rsu4co2_CFmon',
        'rsucs4co2_CFmon',
        'rsut4co2_CFmon',
        'rsutcs4co2_CFmon',
        'clwvic_Emon',
        'evspsblpot_Emon',
        'mrsol_Emon',
        'nep_Emon',
        'sfcWindmax_Emon',
        'utendnogw_EmonZ',
        'albisccp_CFmon',
        'ccb_Amon',
        'cct_Amon',
        'cdnc_Primmon',
        'ci_Amon',
        'clcalipso_CFmon',
        'cldicemxrat27_Emon',
        'cldwatmxrat27_Emon',
        'clhcalipso_CFmon',
        'clic_CFmon',
        'clis_CFmon',
        'clisccp_CFmon',
        'cllcalipso_CFmon',
        'clmcalipso_CFmon',
        'cltcalipso_CFmon',
        'cltisccp_CFmon',
        'clws_CFmon',
        'clwvic_Primmon',
        'cod_Primmon',
        'hfdsn_LImon',
        'mcd_CFmon',
        'mcu_CFmon',
        'parasolRefl_Emon',
        'pctisccp_CFmon',
        't2_Emon',
        'tnhusa_CFmon',
        'tnhusmp_CFmon',
        'tnhusscpbl_CFmon',
        'tnt_CFmon',
        'tnta_CFmon',
        'tntmp27_Emon',
        'tntmp_CFmon',
        'tntr_CFmon',
        'twap_Emon',
        'u2_Emon',
        'uqint_Emon',
        'ut_Emon',
        'uv_Emon',
        'uwap_Emon',
        'v2_Emon',
        'vqint_Emon',
        'vt_Emon',
        'vwap_Emon',
        'wap2_Emon'
    ]
    experiment_objs = []
    for expt in experiments:
        expt_obj = match_one(Experiment, short_name=expt)
        if expt_obj:
            experiment_objs.append(expt_obj)
        else:
            msg = 'experiment {} not found in the database.'.format(expt)
            print msg
            raise ValueError(msg)

    # Institute
    result = match_one(Institute, short_name=institute_details['id'])
    if result:
        institute = result
    else:
        msg = 'institute_id {} not found in the database.'.format(
            institute_details['id']
        )
        print msg
        raise ValueError(msg)

    # Look up the ClimateModel object for each institute_id  and save the
    # results to a dictionary for quick look up later
    model_objs = []
    for clim_model in institute_details['model_ids']:
        result = match_one(ClimateModel, short_name=clim_model)
        if result:
            model_objs.append(result)
        else:
            msg = ('climate_model {} not found in the database.'.
                   format(clim_model))
            print msg
            raise ValueError(msg)

    # The standard reference time
    std_units = Settings.get_solo().standard_time_units

    # create the additional variable requests
    for new_vreq in new_vreqs:
        _vr = get_or_create(VariableRequest, **new_vreq)

    # create the new data requests
    for new_dreq in new_dreqs:
        cmor_name, table_name = new_dreq.split('_')
        if table_name.startswith('Prim'):
            project = match_one(Project, short_name='PRIMAVERA')
        else:
            project = match_one(Project, short_name='CMIP6')

        var_req_obj = match_one(VariableRequest, cmor_name=cmor_name,
                                table_name=table_name)
        if var_req_obj:
            for expt in experiment_objs:
                for clim_model in model_objs:
                    _dr = get_or_create(
                        DataRequest,
                        project=project,
                        institute=institute,
                        climate_model=clim_model,
                        experiment=expt,
                        variable_request=var_req_obj,
                        request_start_time=date2num(
                            experiments[expt.short_name]['start_date'],
                            std_units, institute_details['calendar']
                        ),
                        request_end_time=date2num(
                            experiments[expt.short_name]['end_date'],
                            std_units, institute_details['calendar']
                        ),
                        time_units=std_units,
                        calendar=institute_details['calendar'],
                        rip_code = variant_label
                    )
        else:
            msg = ('Unable to find variable request matching '
                   'cmor_name {} and table_name {} in the '
                   'database.'.format(cmor_name, table_name))
            print msg
            raise ValueError(msg)


if __name__ == "__main__":
    cmd_args = parse_args()

    # determine the log level
    if cmd_args.log_level:
        try:
            log_level = getattr(logging, cmd_args.log_level.upper())
        except AttributeError:
            logger.setLevel(logging.WARNING)
            logger.error('log-level must be one of: debug, info, warn or error')
            sys.exit(1)
    else:
        log_level = DEFAULT_LOG_LEVEL

    # configure the logger
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': DEFAULT_LOG_FORMAT,
            },
        },
        'handlers': {
            'default': {
                'level': log_level,
                'class': 'logging.StreamHandler',
                'formatter': 'standard'
            },
        },
        'loggers': {
            '': {
                'handlers': ['default'],
                'level': log_level,
                'propagate': True
            }
        }
    })

    # run the code
    main(cmd_args)
