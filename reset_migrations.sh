#!/usr/bin/env bash

apps=(
  core
  admin
  authemail
  authtoken
  sessions
  geography
  catalog
  agroforestry
)

source .env.development.local
CONN_STRING=postgresql://postgres@localhost:5432/postgres
# source .env.staging.local
# CONN_STRING=postgres://avnadmin@sar-perma.b.aivencloud.com:21193/defaultdb?sslmode=require

for app in ${apps[@]}; do
  find . -path "./${app}/migrations/*.py" -not -name "__init__.py" -delete;
  find . -path "./${app}/migrations/*.pyc" -delete;

  #psql $CONN_STRING -c "DELETE FROM django_migrations WHERE app = '$app';" # uncomment if not running after reset_database
done

#FAKE_MIGRATION_FLAG=--fake # uncomment if not running after reset_database
for app in ${apps[@]}; do
  python3 manage.py makemigrations $app;
  python3 manage.py migrate $app $FAKE_MIGRATION_FLAG;
done
