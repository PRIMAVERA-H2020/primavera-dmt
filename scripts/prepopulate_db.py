#!/usr/bin/env python
"""
prepopulate_db.py

This script is run by the data manager to populate the database with the
expected climate models, experiments, etc.
"""
from __future__ import unicode_literals, division, absolute_import

import django
django.setup()

from pdata_app.models import (Project, ClimateModel, Experiment, Institute,
                              ActivityId)
from pdata_app.utils.dbapi import get_or_create


def main():
    """
    Populate the database
    """
    # Projects
    proj = get_or_create(Project, short_name='CMIP6',
        full_name='Coupled Model Intercomparison Project Phase 6')
    proj = get_or_create(Project, short_name='PRIMAVERA',
        full_name='PRIMAVERA High Resolution Modelling Project')

    # Activty ID
    act_id = get_or_create(ActivityId, short_name='HighResMIP',
                           full_name='High Resolution Model Intercomparison '
                                     'Project')

    # Experiments HighResMIP
    experiments = {
        'control-1950': "coupled control with fixed 1950's forcing (HighResMIP "
                        "equivalent of pre-industrial control)",
        'highres-future': "coupled future 2015-2050 using a scenario as close "
                          "to CMIP5 RCP8.5 as possible within CMIP6",
        'hist-1950': "coupled historical 1950-2014",
        'highresSST-present': "forced atmosphere experiment for 1950-2014",
        'highresSST-future': "forced atmosphere experiment for 2015-2050 using "
                             "SST/sea-ice derived from CMIP5 RCP8.5 simulations "
                             "and a scenario as close to RCP8.5 as possible "
                             "within CMIP6",
        'highresSST-LAI': "common LAI dataset within the highresSST-present "
                          "experiment",
        'highresSST-smoothed': "smoothed SST version of highresSST-present",
        'highresSST-p4K': "uniform 4K warming of highresSST-present SST",
        'highresSST-4co2': "highresSST-present SST with 4xCO2 concentrations"
    }
    for expt in experiments:
        _ex = get_or_create(Experiment, short_name=expt,
            full_name=experiments[expt])

    # Institutes
    institutes = {
        'AWI': 'Alfred Wegener Institute, Helmholtz Centre for Polar and Marine '
            'Research, Am Handelshafen 12, 27570 Bremerhaven, Germany',
        'CNRM-CERFACS': 'Centre National de Recherches Meteorologiques, Meteo-France, '
            'Toulouse, France) and CERFACS (Centre Europeen de Recherches '
            'et de Formation Avancee en Calcul Scientifique, Toulouse, '
            'France',
        'CMCC': 'Centro Euro-Mediterraneo per i Cambiamenti Climatici, Bologna 40127, '
            'Italy',
        'EC-Earth-Consortium': 'KNMI, The Netherlands; SMHI, Sweden; DMI, Denmark; '
            'AEMET, Spain; Met Eireann, Ireland; CNR-ISAC, Italy; Instituto de '
            'Meteorologia, Portugal; FMI, Finland; BSC, Spain; Centro de Geofisica, '
            'University of Lisbon, Portugal; ENEA, Italy; Geomar, Germany; Geophysical '
            'Institute, University of Bergen, Norway; ICHEC, Ireland; ICTP, Italy; '
            'IMAU, The Netherlands; IRV, Sweden;  Lund University, Sweden; '
            'Meteorologiska Institutionen, Stockholms University, Sweden; Niels '
            'Bohr Institute, University of Copenhagen, Denmark; NTNU, Norway; SARA, '
            'The Netherlands; Unite ASTR, Belgium; Universiteit Utrecht, The Netherlands; '
            'Universiteit Wageningen, The Netherlands; University College Dublin, Ireland; '
            'Vrije Universiteit Amsterdam, the Netherlands; University of Helsinki, Finland; '
            'KIT, Karlsruhe, Germany; USC, University of Santiago de Compostela, Spain; '
            'Uppsala Universitet, Sweden; NLeSC, Netherlands eScience Center, The Netherlands',
        'MPI-M': 'Max Planck Institute for Meteorology, Hamburg 20146, Germany',
        'MOHC': 'Met Office Hadley Centre, Fitzroy Road, Exeter, Devon, '
            'EX1 3PB, UK',
        'ECMWF': 'ECMWF (European Centre for Medium-Range Weather Forecasts, Reading '
            'RG2 9AX, United Kingdom)'
    }
    for inst in institutes:
        _inst = get_or_create(Institute, short_name=inst,
            full_name=institutes[inst])

    # Models
    models = {
        'AWI-CM-1-0-LR': 'AWI-CM-1-0-LR',
        'AWI-CM-1-0-HR': 'AWI-CM-1-0-HR',
        'CNRM-CM6-1-HR': 'CNRM-CM6-1-HR',
        'CNRM-CM6-1': 'CNRM-CM6-1',
        'CMCC-CM2-HR4': 'CMCC-CM2-HR4',
        'CMCC-CM2-VHR4': 'CMCC-CM2-VHR4',
        'MPIESM-1-2-HR': 'MPIESM-1-2-HR',
        'MPIESM-1-2-XR': 'MPIESM-1-2-XR',
        'HadGEM3-GC31-HM': 'HadGEM3-GC31-HM',
        'HadGEM3-GC31-MM': 'HadGEM3-GC31-MM',
        'HadGEM3-GC31-LM': 'HadGEM3-GC31-LM',
        'ECMWF-IFS-LR': 'ECMWF-IFS-LR',
        'ECMWF-IFS-HR': 'ECMWF-IFS-HR',
        'EC-Earth3-HR' :'EC-Earth3-HR',
        'EC-Earth3-LR': 'EC-Earth3-LR'
    }
    for model in models:
        _mdl = get_or_create(ClimateModel, short_name=model,
            full_name=models[model])


if __name__ == '__main__':
    main()
