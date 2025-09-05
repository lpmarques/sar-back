#!/usr/bin/env bash

psql postgresql://postgres@localhost:5432/postgres -f ./clear_database.sql

find . -path "*/migrations/*.py" -not -name "__init__.py" -delete;
find . -path "*/migrations/*.pyc" -delete;

python3 manage.py makemigrations core;
python3 manage.py makemigrations geography;
python3 manage.py makemigrations catalog;

python3 manage.py migrate core;
python3 manage.py migrate geography;
python3 manage.py migrate catalog;
