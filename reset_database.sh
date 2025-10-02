#!/usr/bin/env bash

psql postgresql://postgres@localhost:5432/postgres -f ./clear_database.sql

python3 manage.py migrate
