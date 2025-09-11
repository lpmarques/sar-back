#!/usr/bin/env bash

psql postgresql://postgres@localhost:5432/postgres -f ./clear_database.sql

find . -path "*/migrations/*.py" -not -name "__init__.py" -delete;
find . -path "*/migrations/*.pyc" -delete;

apps=(
  core
  geography
  catalog
)

for app in ${apps[@]}; do
  python3 manage.py makemigrations $app;
  python3 manage.py migrate $app;
done
