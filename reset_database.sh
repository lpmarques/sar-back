#!/usr/bin/env bash

# psql postgresql://postgres@localhost:5432/postgres -f ./clear_database.sql
psql postgres://avnadmin@sar-perma.b.aivencloud.com:21193/defaultdb?sslmode=require -f ./clear_database.sql

python3 manage.py migrate
