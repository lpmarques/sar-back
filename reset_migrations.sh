#!/usr/bin/env bash

apps=(
  # admin
  # authemail
  # authtoken
  # sessions
  # core
  # geography
  # catalog
  # agroforestry
)

for app in ${apps[@]}; do
  find . -path "./${app}/migrations/*.py" -not -name "__init__.py" -delete;
  find . -path "./${app}/migrations/*.pyc" -delete;
  
  python3 manage.py makemigrations $app;
done

python3 manage.py migrate #--fake; # uncomment if not running after reset_database
