-- Create schema if they don't exist
-- This is needed because restoration of the DB doesn't create schema

CREATE SCHEMA IF NOT EXISTS warehouse;
CREATE SCHEMA IF NOT EXISTS public;
