#!/usr/bin/env bash

source .env.development.local
psql postgresql://postgres@localhost:5432/postgres -f ./clear_database.sql

# source .env.staging.local
# psql postgres://avnadmin@sar-perma.b.aivencloud.com:21193/defaultdb?sslmode=require -f ./clear_database.sql

python3 manage.py migrate # uncomment if not running before reset_migrations
