-- Initialize PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_spatial_ref_sys_srid ON spatial_ref_sys(srid);

-- Set timezone
SET timezone = 'UTC';
