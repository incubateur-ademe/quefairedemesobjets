-- Create role if it doesn't exist
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'webapp_sample') THEN
    CREATE USER webapp_sample WITH PASSWORD 'webapp_sample' SUPERUSER;
  END IF;
END
$$;

-- Ensure user is superuser (in case it already existed)
ALTER USER webapp_sample WITH SUPERUSER;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE webapp_sample TO webapp_sample;
ALTER DATABASE webapp_sample OWNER TO webapp_sample;
