#!/usr/bin/env python
"""
add_spinup.py

Based on populate_data_request.py and adds to the PRIMAVERA-DMT DataRequest 
table the spinup-1950 experiment from the PRIMAVERA data request spreadsheet.

Uses the Google Sheets API:
https://developers.google.com/sheets/quickstart/python
To load the spreadsheet at:
https://docs.google.com/spreadsheets/d/1ewKkyuaUq99HUefWIdb3JzqUwwnPLNUGJxbQyqa-10U/
"""
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)
from datetime import datetime
import httplib2
import os
import re

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

from cf_units import (CALENDAR_360_DAY, CALENDAR_GREGORIAN,
                      CALENDAR_PROLEPTIC_GREGORIAN, CALENDAR_STANDARD,
                      date2num)

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

import django
django.setup()
from pdata_app.models import (DataRequest, Institute, Project, Settings,
                              ClimateModel, Experiment, VariableRequest)
from pdata_app.utils.dbapi import match_one, get_or_create

# The ID of the Google Speadsheet (taken from the sheet's URL)
SPREADSHEET_ID = '1ewKkyuaUq99HUefWIdb3JzqUwwnPLNUGJxbQyqa-10U'

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
CLIENT_SECRET_FILE = 'client_secret_920707869718-bjp97l2ikhi0qdqi4ibb5ivcpmnml7n8.apps.googleusercontent.com.json'
APPLICATION_NAME = 'PRIMAVERA-DMT'


def get_credentials():
    """
    Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, 'sheets.googleapis.'
                                                   'com-populate_variable_'
                                                   'request.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        curr_dir = os.path.dirname(__file__)
        secret_file_path = os.path.abspath(os.path.join(curr_dir, '..', 'etc',
                                                        CLIENT_SECRET_FILE))
        flow = client.flow_from_clientsecrets(secret_file_path, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def is_ecmwf(sheet_cell):
    """Is this variable produced by ECMWF?"""
    if not sheet_cell:
        return False

    int_string = re.findall(r'-?\d+', sheet_cell)
    if int_string:
        if (int_string[0] == '1' or
            int_string[0] == '2'):
            return True
        else:
            return False
    else:
        return False


def is_awi(sheet_cell):
    """Is this variable produced by AWI?"""
    if not sheet_cell:
        return False

    status_ignored = sheet_cell.split(':')[-1].strip().upper()

    if status_ignored == 'X' or status_ignored == 'LIMITED':
        return True
    elif status_ignored == 'FALSE':
        return False
    else:
        print('Unknown AWI status: {}. Ignoring.'.format(sheet_cell))
        return False


def is_cnrm(sheet_cell):
    """Is this variable produced by CNRM?"""
    if not sheet_cell:
        return False

    int_string = re.findall(r'-?\d+', sheet_cell)
    if int_string:
        if (int_string[0] == '1' or
            int_string[0] == '2' or
            int_string[0] == '3'):
            return True
        elif (int_string[0] == '-1' or
              int_string[0] == '-2' or
              int_string[0] == '-3' or
              int_string[0] == '-999'):
            return False
        else:
            print('Unknown CNRM status: {}. Ignoring.'.format(sheet_cell))
            return False


def is_cmcc(sheet_cell):
    """Is this variable produced by CMCC?"""
    if not sheet_cell:
        return False

    if sheet_cell.upper() == 'FALSE':
        return False
    else:
        return True


def is_ec_earth(sheet_cell):
    """Is this variable produced by `institute` using ECEarth?"""
    if not sheet_cell:
        return False

    if sheet_cell.upper() == 'X' or sheet_cell.upper() == 'LIMITED':
        return True
    elif sheet_cell.upper() == 'FALSE' or sheet_cell.upper() == 'NO':
        return False
    else:
        print('Unknown EC-Earth status: {}. Ignoring.'.format(sheet_cell))
        return False


def is_mpi(sheet_cell):
    """Is this variable produced by MPI?"""
    if not sheet_cell:
        return False

    status_ignored = sheet_cell.split(':')[-1].strip().upper()

    if status_ignored == 'X' or status_ignored == 'LIMITED':
        return True
    elif status_ignored == 'FALSE' or status_ignored == 'NO':
        return False
    else:
        print('Unknown MPI status: {}. Ignoring.'.format(sheet_cell))
        return False


def is_metoffice(sheet_cell):
    """Is this variable produced by the Met Office?"""
    if not sheet_cell:
        return False

    not_producing_values = ['CHECK', 'FALSE']
    for value in not_producing_values:
        if value == sheet_cell.upper():
            return False

    return True


def main():
    """
    Run the processing.
    """
    # initialize the spreadsheet access
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discovery_url = ('https://sheets.googleapis.com/$discovery/rest?'
                     'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discovery_url)

    # the names of each of the sheets
    sheet_names = [
        'Amon', 'LImon', 'Lmon', 'Omon', 'SImon', 'AERmon',
        'CFmon', 'Emon', 'EmonZ', 'Primmon', 'PrimmonZ', 'PrimOmon', 'Oday',
        'CFday', 'day', 'Eday', 'EdayZ', 'SIday', 'PrimdayPt', 'Primday',
        'PrimOday', 'PrimSIday', '6hrPlev', '6hrPlevPt', 'PrimO6hr', 'Prim6hr',
        'Prim6hrPt', '3hr', 'E3hr', 'E3hrPt', 'Prim3hr', 'Prim3hrPt', 'E1hr',
        'Esubhr', 'Prim1hr', 'fx'
    ]

    # details of each of the institutes
    # key is the column number in the spreadsheet
    institutes = {
        24: {'id': 'ECMWF', 'model_ids': ['ECMWF-IFS-LR', 'ECMWF-IFS-HR'], 
             'check_func': is_ecmwf, 'calendar': CALENDAR_GREGORIAN},
        25: {'id': 'AWI', 'model_ids': ['AWI-CM-1-0-LR', 'AWI-CM-1-0-HR'],
             'check_func': is_awi, 'calendar': CALENDAR_STANDARD},
        26: {'id': 'CNRM-CERFACS', 'model_ids': ['CNRM-CM6-1-HR', 'CNRM-CM6-1'], 
             'check_func': is_cnrm, 'calendar': CALENDAR_GREGORIAN},
        27: {'id': 'CMCC', 'model_ids': ['CMCC-CM2-HR4', 'CMCC-CM2-VHR4'],
             'check_func': is_cmcc, 'calendar': CALENDAR_STANDARD},
        28: {'id': 'EC-Earth-Consortium', 'model_ids': ['EC-Earth3-LR',
             'EC-Earth3-HR'], 'check_func': is_ec_earth,
             'calendar': CALENDAR_GREGORIAN},
        32: {'id': 'MPI-M', 'model_ids': ['MPIESM-1-2-HR', 'MPIESM-1-2-XR'],
             'check_func': is_mpi, 'calendar': CALENDAR_PROLEPTIC_GREGORIAN},
        33: {'id': 'MOHC', 'model_ids': ['HadGEM3-GC31-HM', 'HadGEM3-GC31-MM',
             'HadGEM3-GC31-LM'], 'check_func': is_metoffice,
             'calendar': CALENDAR_360_DAY}
    }

    # add the spinup-1950 experiment
    experiments = {
        'spinup-1950': "Coupled integration from ocean rest state using "
                       "recommended HighResMIP protocol spinup, starting from "
                       "1950 ocean temperature and salinity analysis EN4, "
                       "using constant 1950s forcing. At least 30 years to "
                       "satisfy near surface quasi-equilibrium"
    }
    for expt in experiments:
        _ex = get_or_create(Experiment, short_name=expt,
            full_name=experiments[expt])

    # The HighResMIP experiments
    experiments = {
        'spinup-1950': {'start_date': datetime(1950, 1, 1),
                         'end_date': datetime(1980, 1, 1)},
    }

    # some objects from constants
    # Experiment
    experiment_objs = []
    for expt in experiments:
        expt_obj = match_one(Experiment, short_name=expt)
        if expt_obj:
            experiment_objs.append(expt_obj)
        else:
            msg = 'experiment {} not found in the database.'.format(expt)
            print(msg)
            raise ValueError(msg)

    # Look up the Institute object for each institute_id  and save the
    # results to a dictionary for quick look up later
    institute_objs = {}
    for col_num in institutes:
        result = match_one(Institute, short_name=institutes[col_num]['id'])
        if result:
            institute_objs[col_num] = result
        else:
            msg = 'institute_id {} not found in the database.'.format(
                institutes[col_num]['id']
            )
            print(msg)
            raise ValueError(msg)

    # Look up the ClimateModel object for each institute_id  and save the
    # results to a dictionary for quick look up later
    model_objs = {}
    for col_num in institutes:
        model_objs[col_num] = []
        for clim_model in institutes[col_num]['model_ids']:
            result = match_one(ClimateModel, short_name=clim_model)
            if result:
                model_objs[col_num].append(result)
            else:
                msg = ('climate_model {} not found in the database.'.
                       format(clim_model))
                print(msg)
                raise ValueError(msg)

    # The standard reference time
    std_units = Settings.get_solo().standard_time_units

    # Loop through each sheet
    for sheet in sheet_names:
        range_name = '{}!A2:AI'.format(sheet)
        result = list(service.spreadsheets().values()).get(
            spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
        values = result.get('values', [])

        if not values:
            msg = ('No data found in sheet {}.'.format(sheet))
            print(msg)
            raise ValueError(msg)

        if sheet.startswith('Prim'):
            project = match_one(Project, short_name='PRIMAVERA')
        else:
            project = match_one(Project, short_name='CMIP6')

        for row in values:
            # for each row, make an entry for each institute/model
            try:
                for col_num in institutes:
                    # check if institute is producing this variable
                    institute_cell = (row[col_num]
                                      if len(row) > col_num else None)
                    if institutes[col_num]['check_func'](institute_cell):
                        # create an entry for each experiment
                        for expt in experiment_objs:
                            # find the corresponding variable request
                            cmor_name = row[11]
                            if cmor_name:
                                var_req_obj = match_one(VariableRequest,
                                                        cmor_name=row[11],
                                                        table_name=sheet)
                            else:
                                var_req_obj = match_one(VariableRequest,
                                                        long_name=row[1],
                                                        table_name=sheet)
                            if var_req_obj:
                                # create a DataRequest for each model in this
                                # combination
                                for clim_model in model_objs[col_num]:
                                    _dr = get_or_create(
                                        DataRequest,
                                        project=project,
                                        institute=institute_objs[col_num],
                                        climate_model=clim_model,
                                        experiment=expt,
                                        variable_request=var_req_obj,
                                        request_start_time=date2num(
                                            experiments[expt.short_name]['start_date'],
                                            std_units, institutes[col_num]['calendar']
                                        ),
                                        request_end_time=date2num(
                                            experiments[expt.short_name]['end_date'],
                                            std_units, institutes[col_num]['calendar']
                                        ),
                                        time_units=std_units,
                                        calendar=institutes[col_num]['calendar']
                                    )
                            else:
                                msg = ('Unable to find variable request matching '
                                       'cmor_name {} and table_name {} in the '
                                       'database.'.format(row[11], sheet))
                                print(msg)
                                raise ValueError(msg)
            except IndexError:
                msg = ('Exception at Sheet: {} Variable: {}'.
                       format(sheet, row[11]))
                print(msg)
                raise


if __name__ == '__main__':
    main()
