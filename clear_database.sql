DO $$ DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename like 'auth%') LOOP
        EXECUTE 'DROP TABLE IF EXISTS public.' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
    
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename like 'django%') LOOP
        EXECUTE 'DROP TABLE IF EXISTS public.' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;

    DROP SCHEMA IF EXISTS core CASCADE;
    DROP SCHEMA IF EXISTS geography CASCADE;
    DROP SCHEMA IF EXISTS catalog CASCADE;
    DROP SCHEMA IF EXISTS agroforestry CASCADE;

    CREATE EXTENSION IF NOT EXISTS postgis;
    CREATE EXTENSION IF NOT EXISTS postgis_raster;

    CREATE SCHEMA IF NOT EXISTS core;
    CREATE SCHEMA IF NOT EXISTS geography;
    CREATE SCHEMA IF NOT EXISTS catalog;
    CREATE SCHEMA IF NOT EXISTS agroforestry;

    -- DELETE FROM django_migrations WHERE app IN ('catalog', 'core', 'geography', 'catalog', 'agroforestry');

END $$;
