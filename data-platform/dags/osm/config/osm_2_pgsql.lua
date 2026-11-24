-- ============================================================================
-- osm2pgsql v2 flex style — unified nodes + ways with tags
--
-- Imports OSM nodes and ways that carry at least one tag into a single
-- PostgreSQL table (osm_elements) with columns: osm_id, kind, tags (jsonb),
-- osm_version, osm_timestamp, osm_user, and geometry.
--
-- Usage
-- ─────
--   osm2pgsql --create \
--       --output flex \
--       --style src/osm_2_pgsql.lua \
--       --schema osm \
--       --number-processes 4 \
--       osm-ds/datasets/france-261108.osm.pbf
-- ============================================================================

-- Configuration
local projection = 4326 -- EPSG:4326 (WGS 84 lat/lon)

-- ---------------------------------------------------------------------------
-- Table definition
-- ---------------------------------------------------------------------------
local t = osm2pgsql.define_table({
    name    = "base_osm",
    ids     = { type = "any", id_column = "osm_id", create_index = "unique", type_column = "node_type" },
    columns = {
        { column = "kind",          type = "text",  not_null = true },
        { column = "tags",          type = "jsonb" },
        { column = "osm_version",   type = "int" },
        { column = "osm_timestamp", type = "bigint" },
        { column = "osm_user",      type = "text" },
        {
            column = "geom",
            type = "geometry",
            projection = projection,
            not_null = true
        },
    },
    indexes = {
        {
            column = "geom",
            name = "idx_osm_elements_geom",
            method = "gist"
        },
    },
    cluster = "no", -- mixed geometry types (point + linestring)
})

-- ---------------------------------------------------------------------------
-- Helper: return true if the tags table has at least one key
-- ---------------------------------------------------------------------------
local function has_tags(tags)
    for _ in pairs(tags) do
        return true
    end
    return false
end

-- ---------------------------------------------------------------------------
-- Helper: Filter the nodes to avoid non useful data
-- ---------------------------------------------------------------------------
local relevant_tags = {
    amenity = true,
    building = true,
    craft = true,
    healthcare = true,
    landuse = true,
    leisure = true,
    office = true,
    shop = true,
    telecom = true,
    tourism = true
}
local function has_relevant_tags(tags)
    for k, v in pairs(tags) do
        if relevant_tags[k] then
            return true
        end
    end
    return false
end

-- ---------------------------------------------------------------------------
-- Process callback: OSM node
-- ---------------------------------------------------------------------------
function osm2pgsql.process_node(object)
    if not has_tags(object.tags) then
        return
    end
    if has_relevant_tags(object.tags) then
        t:insert({
            tags          = object.tags,
            osm_version   = object.version,
            osm_timestamp = object.timestamp,
            osm_user      = object.user,
            geom          = object:as_point(),
        })
    end
end

-- ---------------------------------------------------------------------------
-- Process callback: OSM way
-- ---------------------------------------------------------------------------
function osm2pgsql.process_way(object)
    if not has_tags(object.tags) then
        return
    end
    if has_relevant_tags(object.tags) then
        t:insert({
            tags          = object.tags,
            osm_version   = object.version,
            osm_timestamp = object.timestamp,
            osm_user      = object.user,
            geom          = object:as_linestring(),
        })
    end
end
