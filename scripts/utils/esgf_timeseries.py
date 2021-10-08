#!/usr/bin/env python
"""
esgf_timeseries.py

Calculate the volume of Stream 1 and Stream 2 data submitted to the ESGF. Save
the results in a file and generate a plot to show the progress.

The files are specified on the command line. There's no backup of the files
made as it's assumed that they'll be stored in a user's home directory, where
regular snapshots are taken.
"""
import argparse
import datetime
import logging.config

import matplotlib
# use the Agg environment to generate an image rather than outputting to screen
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import pandas as pd

import django
from django.db.models import Sum
from django.template.defaultfilters import filesizeformat
django.setup()
from pdata_app.models import DataFile, ESGFDataset


__version__ = '0.1.0b1'

logger = logging.getLogger(__name__)

# The number of bytes in a tebibyte
BYTES_IN_TEBIBYTE = 1024 ** 4

# The date that PRIMAVERA ends and we want all data published by
PRIM_END = datetime.datetime(2021, 12, 31, 0, 0)


def get_volume_published():
    """
    Calculate the total volume in bytes of files in the ESGF publication
    process.

    :return: volume in bytes
    """
    esgf_volume = 0
    for esgf in ESGFDataset.objects.all():
        dataset_volume = (esgf.data_request.datafile_set.distinct().
                          aggregate(Sum('size'))['size__sum'])
        if dataset_volume:
            esgf_volume += dataset_volume

    return esgf_volume


def get_total_volume():
    """
    Calculate the total volume in bytes of files that need to be published.

    :return: volume in bytes.
    """
    amip_expts = ['highresSST-present', 'highresSST-future']
    coupled_expts = ['spinup-1950', 'hist-1950', 'control-1950',
                     'highres-future']
    stream1_2_expts = amip_expts + coupled_expts

    # MOHC stream 2 is members r1i2p2f1 to r1i15p1f1
    mohc_stream2_members = [f'r1i{init_index}p1f1'
                            for init_index in range(2, 16)]

    stream1_2 = DataFile.objects.filter(
        experiment__short_name__in=stream1_2_expts
    ).exclude(
        # Exclude MOHC Stream 2
        institute__short_name__in=['MOHC', 'NERC'],
        rip_code__in=mohc_stream2_members,
    ).exclude(
        # Exclude EC-Earth alevhalf
        institute__short_name='EC-Earth-Consortium',
        variable_request__dimensions__contains='alevhalf'
    ).exclude(
        # Exclude EC-Earth alevel
        institute__short_name='EC-Earth-Consortium',
        variable_request__dimensions__contains='alevel'
    ).distinct()

    mohc_stream2_members = DataFile.objects.filter(
        institute__short_name__in=['MOHC', 'NERC'],
        experiment__short_name__in=stream1_2_expts,
        rip_code__in=mohc_stream2_members
    ).distinct()

    mohc_stream2_low_freq = mohc_stream2_members.filter(
        variable_request__frequency__in=['mon', 'day']
    ).exclude(
        variable_request__table_name='CFday'
    ).distinct()

    mohc_stream2_cfday = mohc_stream2_members.filter(
        variable_request__table_name='CFday',
        variable_request__cmor_name='ps'
    ).distinct()

    mohc_stream2_6hr = mohc_stream2_members.filter(
        variable_request__table_name='Prim6hr',
        variable_request__cmor_name='wsgmax'
    ).distinct()

    mohc_stream2_3hr = mohc_stream2_members.filter(
        variable_request__table_name__in=['3hr', 'E3hr', 'E3hrPt', 'Prim3hr',
                                          'Prim3hrPt'],
        variable_request__cmor_name__in=['rsdsdiff', 'rsds', 'tas', 'uas',
                                         'vas', 'ua50m', 'va50m', 'ua100m',
                                         'va100m', 'ua7h', 'va7h', 'sfcWind',
                                         'sfcWindmax', 'pr', 'psl', 'zg7h']
    ).distinct()

    publishable_files = (stream1_2 | mohc_stream2_low_freq |
                         mohc_stream2_cfday | mohc_stream2_6hr |
                         mohc_stream2_3hr)

    return publishable_files.aggregate(Sum('size'))['size__sum']


def generate_plots(time_series_file, output_image):
    """
    Load the CSV formatted time series file and generate an image showing the
    publication progress made over the last 30 days.

    :param str time_series_file: the full path of the time series file.
    :param str output_image: the full path of the image.
    """
    # The number of seconds in a day
    seconds_in_day = 60**2 * 24

    df = pd.read_csv(time_series_file, names=['Date', 'Submitted', 'Total'],
                     parse_dates=[0], index_col=[0])
    # Swap the order of the columns as this looks better when plotted
    df = df[['Total', 'Submitted']]
    # Convert to tebibytes
    df = df.div(BYTES_IN_TEBIBYTE)
    # Calculate the current rate
    df['Rate of submission'] = (
        df['Submitted'].diff() /
        (df.index.to_series().diff().dt.total_seconds() / seconds_in_day)
    )
    # display a maximum of 30 time points
    times_in_df = df.shape[0]
    if times_in_df <= 30:
        num_times = -1 * times_in_df
    else:
        num_times = -30
    # Plot
    ax = df.iloc[num_times:, 0:3].plot(secondary_y=['Rate of submission'],
                                       mark_right=False)
    # Set the x-axis tick format to be day month
    ax.xaxis.set_major_formatter(DateFormatter('%d %b'))
    # Set the y-axes limits
    ax.right_ax.set_ylim((0, 20))
    ax.set_ylim((0, 1700))
    # Set the y-axis titles
    ax.set_ylabel('Volume submitted (TiB)')
    ax.right_ax.set_ylabel('Rate of submission (TiB/day)')
    # Move the legend
    ax.get_legend().set_bbox_to_anchor((0.4, 0.9))
    # Estimate publication rate required
    to_publish = df['Total'][-1] - df['Submitted'][-1]
    days_left = (PRIM_END - datetime.datetime.utcnow()).days
    rate_needed = to_publish / days_left
    # Set the title
    percent_complete = df['Submitted'][-1] / df['Total'][-1] * 100
    plt.title(f'ESGF Submission Progress - {percent_complete:.0f}% complete\n'
              f'({days_left} days left so require {rate_needed:.1f} TiB/day)')
    # Include the date and time that the plot was generated at
    time_str = ('Created at: ' + datetime.datetime.utcnow().
                replace(microsecond=0).isoformat())
    plt.figtext(0.8, 0.05, time_str, va='center', ha='center',
                color='lightgray')

    # Save the image
    plt.savefig(output_image)


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Plot the volume of data '
                                                 'submitted to the ESGF.')
    parser.add_argument('time_series_file', action='store',
                        help='The full path to the comma separated file to '
                             'save the time series data in.',)
    parser.add_argument('output_image', action='store',
                        help='The full path to the image that will be '
                             'generated.')
    parser.add_argument('-l', '--log-level',
                        help='set logging level (default: %(default)s)',
                        choices=['debug', 'info', 'warning', 'error'],
                        default='warning')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()

    return args


def main(args):
    """Run the script"""
    esgf_volume = get_volume_published()
    total_volume = get_total_volume()

    pretty_esgf = filesizeformat(esgf_volume).replace('\xa0', ' ')
    pretty_total = filesizeformat(total_volume).replace('\xa0', ' ')
    logger.info(f'Volume published to ESGF {pretty_esgf}')
    logger.info(f'Total Volume {pretty_total}')
    logger.info(f'Percentage published to ESGF '
                f'{esgf_volume / total_volume:.0%}')

    # Append the values to the file in a CSV format
    with open(args.time_series_file, 'a') as fh:
        fh.write(f'{datetime.datetime.utcnow()}, '
                 f'{esgf_volume}, {total_volume}\n')

    generate_plots(args.time_series_file, args.output_image)


if __name__ == "__main__":
    cmd_args = parse_args()

    # configure the logger
    log_level = getattr(logging, cmd_args.log_level.upper())
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(levelname)s: %(message)s',
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
