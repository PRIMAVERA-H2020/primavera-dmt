#!/usr/bin/env python
"""
get_mohc_data_volumes.py

This script will write to file the total volumes of data currently held for the various
HadGEM3 models.
"""
from __future__ import unicode_literals, division, absolute_import

import argparse
from collections import OrderedDict
from copy import copy
import logging.config
import sys

import django
from django.db.models import Sum
from django.template.defaultfilters import filesizeformat
django.setup()
from pdata_app.models import DataFile


__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)

def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Write to file the total volume '
                                                 'of data for the HadGEM3-GC31 models.')
    parser.add_argument('filepath', help='the file path to write to')
    parser.add_argument('-l', '--log-level', help='set logging level to one of '
        'debug, info, warn (the default), or error')
    parser.add_argument('--version', action='version',
        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()

    return args


def main(args):
    """Run the script"""
    projects = ['CMIP6', 'PRIMAVERA']

    experiments = ['highresSST-present', 'highresSST-future','spinup-1950',
                   'control-1950', 'hist-1950', 'highres-future']
    expts_no_amip = copy(experiments)
    expts_no_amip.remove('highresSST-present')
    expts_no_amip.remove('highresSST-future')
    expts_no_spinup = copy(experiments)
    expts_no_spinup.remove('spinup-1950')
    expts_hh = copy(expts_no_amip)
    expts_hh.remove('spinup-1950')


    models = OrderedDict([
        ('HadGEM3-GC31-LM', ['highresSST-present', 'highresSST-future']),
        ('HadGEM3-GC31-LL', expts_no_amip),
        ('HadGEM3-GC31-MM', experiments),
        ('HadGEM3-GC31-HM', expts_no_spinup),
        ('HadGEM3-GC31-MH', ['spinup-1950']),
        ('HadGEM3-GC31-HH', expts_hh)
    ])

    with open(args.filepath, 'w') as fh:
        fh.write('{}, {}, {}, {}\n\n'.format('Model', 'Experiment', 'Bytes', 'Human Readable'))
        for proj in projects:
            proj_total = 0
            fh.write('{},,,\n\n'.format(proj))
            for model in models:
                for expt in models[model]:
                    if expt == 'highresSST-future':
                        expt_query_name = 'highresSST-present'
                    elif expt == 'highres-future':
                        expt_query_name = 'hist-1950'
                    else:
                        expt_query_name = expt
                    data_volume = DataFile.objects.filter(
                        project__short_name=proj,
                        climate_model__short_name=model,
                        experiment__short_name=expt_query_name
                    ).aggregate(Sum('size'))['size__sum']
                    if 'future' in expt:
                        data_volume = data_volume / 65. * 35.
                    if 'HH' in model and 'control' in expt:
                        data_volume = data_volume * 2
                    proj_total += data_volume
                    human_readable = filesizeformat(data_volume)
                    human_readable = str(human_readable.replace('\xa0', ' '))
                    fh.write('{}, {}, {}, {}\n'.format(model, expt,
                                                       data_volume,
                                                       str(human_readable)))
            human_readable = filesizeformat(proj_total)
            human_readable = str(human_readable.replace('\xa0', ' '))
            fh.write('{} total, , {}, {}\n\n'.format(proj, proj_total,
                                                   str(human_readable)))

        fh.write('\nNotes: \nfuture experiment volumes have been estimated '
                 'from the historic or present runs.\n')
        fh.write("PRIMAVERA is the additional PRIMAVERA specific variables "
                 "that will be submitted to the ESGF mip_era "
                 "of PRIMAVERA rather than CMIP6.\n")
        fh.write("Several variables could not be generated so far but "
                 "may be generated in the future. In the very worst case "
                 "this would be a 33% increase in data volume but will "
                 "not be that bad as the model did not output the data "
                 "for all of these.\n")



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
