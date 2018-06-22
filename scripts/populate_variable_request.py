#!/usr/bin/env python
"""
populate_variable_request.py

Populates the PRIMAVERA-DMT VariableRequest table with details from the
PRIMAVERA data request spreadsheet.

Uses the Google Sheets API:
https://developers.google.com/sheets/quickstart/python
To load the spreadsheet at:
https://docs.google.com/spreadsheets/d/1ewKkyuaUq99HUefWIdb3JzqUwwnPLNUGJxbQyqa-10U/
"""
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)
import httplib2
import os

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

import django
django.setup()
from pdata_app.models import VariableRequest
from vocabs.vocabs import FREQUENCY_VALUES, VARIABLE_TYPES
from pdata_app.utils.dbapi import get_or_create

# The ID of thr Google Speadsheet (taken from the sheet's URL)
SPREADSHEET_ID = '1ewKkyuaUq99HUefWIdb3JzqUwwnPLNUGJxbQyqa-10U'

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
CLIENT_SECRET_FILE = ('client_secret_920707869718-bjp97l2ikhi0qdqi4ibb5ivc'
                      'pmnml7n8.apps.googleusercontent.com.json')
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
    credential_path = os.path.join(credential_dir,
        'sheets.googleapis.com-populate_variable_request.json')

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
        print(('Storing credentials to ' + credential_path))
    return credentials


def main():
    """
    Run the processing.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discovery_url = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discovery_url)

    sheet_names = [
        'Amon', 'LImon', 'Lmon', 'Omon', 'SImon', 'AERmon',
        'CFmon', 'Emon', 'EmonZ', 'Primmon', 'PrimmonZ', 'PrimOmon', 'Oday',
        'CFday', 'day', 'Eday', 'EdayZ', 'SIday', 'PrimdayPt', 'Primday',
        'PrimOday', 'PrimSIday', '6hrPlev', '6hrPlevPt', 'PrimO6hr', 'Prim6hr',
        'Prim6hrPt', '3hr', 'E3hr', 'E3hrPt', 'Prim3hr', 'Prim3hrPt', 'E1hr',
        'Esubhr', 'Prim1hr', 'fx'
    ]

    for sheet in sheet_names:
        range_name = '{}!A2:AI'.format(sheet)
        result = list(service.spreadsheets().values()).get(
            spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
        else:
            for row in values:
                cmor_name = row[11] if row[11] else row[5]
                try:
                    _vr = get_or_create(VariableRequest, table_name=sheet,
                        long_name=row[1], units=row[2], var_name=row[5],
                        standard_name=row[6], cell_methods=row[7],
                        positive=row[8], variable_type=VARIABLE_TYPES[row[9]],
                        dimensions=row[10], cmor_name=cmor_name,
                        modeling_realm=row[12],
                        frequency=FREQUENCY_VALUES[row[13]],
                        cell_measures=row[14], uid=row[18])
                except (KeyError, IndexError):
                    # display some information to work out where the error
                    # happened and then re-raise the exception to crash out
                    print('cmor_name: {} table: {}'.format(row[11], sheet))
                    print(row)
                    raise

if __name__ == '__main__':
    main()
