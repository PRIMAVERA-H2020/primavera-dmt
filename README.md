[![Build Status](https://travis-ci.org/PRIMAVERA-H2020/primavera-dmt.svg?branch=master)](https://travis-ci.org/PRIMAVERA-H2020/primavera-dmt) [![DOI](https://zenodo.org/badge/139697569.svg)](https://zenodo.org/badge/latestdoi/139697569)

# primavera-dmt
PRIMAVERA Data Management Tool

### Quick set-up

1. Load a Conda or virtualenv environment containing:   
   ```  
   django  
   django-filter  
   django-solo  
   django-tables2
   mock
   netcdftime  
   iris  
   ```  
   
   For example in Conda:
   ```
   conda create -n primavera-dmt -c conda-forge python=3.6 django=2.2 django-filter mock netcdftime iris
   source activate primavera-dmt
   pip install django-solo django-tables2
   ```
   Get a copy of the primavera-val code:
   ```
   git clone https://github.com/PRIMAVERA-H2020/primavera-val.git
   export PYTHONPATH=$PYTHONPATH:./primavera-val
   ```
   
2. Create local settings:    
   ```  
   $ cp pdata_site/settings_local.py.tmpl pdata_site/settings_local.py  
    ``` 
   Populate the value of `SECRET_KEY` on line 23 of `pdata_site/settings_local.py`
   with a suitable random string. A string can be generated from the command line:
   ```
   $ python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
   ```

3. Django set-up:  
   ```
   mkdir db
   python manage.py makemigrations pdata_app
   python manage.py migrate
   ```

4. Run tests:
   ```
   python manage.py test
   ```
   
5. View the website in a local development server:
   In `pdata_site/settings.py` enable debug mode by changing line 19 to:
   ```
   DEBUG = True
   ```
   Start the development server:
   ```
   $ python manage.py runserver
   ```
   Point your browser at `http://localhost:8000/` to view the site.