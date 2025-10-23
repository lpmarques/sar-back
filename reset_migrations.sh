#!/usr/bin/env bash

# psql postgresql://postgres@localhost:5432/postgres -f ./clear_database.sql
# psql postgres://avnadmin@sar-perma.b.aivencloud.com:21193/defaultdb?sslmode=require -f ./clear_database.sql

apps=(
  admin
  authemail
  authtoken
  sessions
  core
  geography
  catalog
  agroforestry
)

for app in ${apps[@]}; do
  echo $app;

  find . -path "./${app}/migrations/*.py" -not -name "__init__.py" -delete;
  find . -path "./${app}/migrations/*.pyc" -delete;
done

python3 manage.py makemigrations;
python3 manage.py migrate;
