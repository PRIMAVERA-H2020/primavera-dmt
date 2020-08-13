#!/usr/bin/env python
"""
crepp_prim_volumes.py

Writes to crepp_prim_volumes.csv the data volumes taken to store the
PRIMAVERA specific data
"""
import django
django.setup()
from django.db.models import Sum  # NOPEP8
from pdata_app.models import DataRequest, DataFile  # NOPEP8
from pdata_app.utils.common import filter_hadgem_stream2  # NOPEP8


FILENAME = 'crepp_prim_volumes_ensemble_table.csv'


def main():
    """
    Run the processing.
    """
    amip_expts = ['highresSST-present', 'highresSST-future']
    coupled_expts = ['spinup-1950', 'hist-1950', 'control-1950',
                     'highres-future']
    stream1_2_expts = amip_expts + coupled_expts

    # MOHC stream 2 is members r1i2p2f1 to r1i15p1f1
    hadgem_stream2_members = [f'r1i{init_index}p1f1'
                              for init_index in range(2, 16)]

    other_models = DataRequest.objects.filter(
        project__short_name='PRIMAVERA',
        experiment__short_name__in=stream1_2_expts,
        variable_request__table_name__startswith='Prim',
        datafile__isnull=False
    ).exclude(
        # Exclude HadGEM2 stream 2 for the moment
        climate_model__short_name__startswith='HadeGEM',
        rip_code__in=hadgem_stream2_members
    ).exclude(
        # Exclude EC-Earth coupled r1i1p1f1
        institute__short_name='EC-Earth-Consortium',
        experiment__short_name__in=coupled_expts,
        rip_code='r1i1p1f1'
    ).distinct()

    hadgem_s2 = filter_hadgem_stream2(DataRequest.objects.filter(
        project__short_name='PRIMAVERA',
        experiment__short_name__in=stream1_2_expts,
        variable_request__table_name__startswith='Prim',
        climate_model__short_name__startswith='HadeGEM',
        rip_code__in=hadgem_stream2_members,
        datafile__isnull = False
    )).distinct()

    ec_earth_s1 = DataRequest.objects.filter(
        institute__short_name='EC-Earth-Consortium',
        experiment__short_name__in=coupled_expts,
        rip_code='r1i1p1f1',
        datafile__isnull=False
    ).distinct()

    wp5 = DataRequest.objects.filter(
        experiment__short_name__in=['primWP5-amv-neg', 'primWP5-amv-pos',
                        'dcppc-amv-neg', 'dcppc-amv-pos'],
        datafile__isnull = False
    ).distinct()

    prim_reqs = other_models | hadgem_s2 | ec_earth_s1 | wp5

    unique_expts = (prim_reqs.values_list('institute__short_name',
                                          'climate_model__short_name',
                                          'experiment__short_name',
                                          'rip_code',
                                          'variable_request__table_name').
                    distinct().order_by('institute__short_name',
                                        'climate_model__short_name',
                                        'experiment__short_name',
                                        'rip_code',
                                        'variable_request__table_name'))

    with open(FILENAME, 'w') as fh:
        fh.write('drs_id, Volume (TB)\n')
        for inst_name, model_name, expt_name, rip_code, table_name in unique_expts:
            dreqs = prim_reqs.filter(
                institute__short_name=inst_name,
                climate_model__short_name=model_name,
                experiment__short_name=expt_name,
                rip_code=rip_code,
                variable_request__table_name=table_name
            )
            if dreqs:
                dreq_size = (
                    DataFile.objects.filter(data_request__in=dreqs).
                    distinct().aggregate(Sum('size'))['size__sum']
                )
                df = dreqs.first().datafile_set.first()
                drs_id = (
                    f'PRIMAVERA.'
                    f'{df.activity_id.short_name}.'
                    f'{df.institute.short_name}.'
                    f'{df.climate_model.short_name}.'
                    f'{df.experiment.short_name}.'
                    f'{df.rip_code}.'
                    f'{df.variable_request.table_name}'
                )
                if 'MPI' in drs_id and 'DCPP' in drs_id:
                    drs_id = (drs_id.replace('DCPP', 'primWP5').
                              replace('dcppc', 'primWP5'))
                if 'NCAS' in drs_id:
                    drs_id = drs_id.replace('NCAS', 'NERC')
                fh.write(
                    f'{drs_id}, {dreq_size / 1024**4}\n'
                )


if __name__ == '__main__':
    main()
