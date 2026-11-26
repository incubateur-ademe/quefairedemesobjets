-- ============================================================================
-- osm2pgsql v2 flex style — ingestion of QFDMO-relevant OSM elements
--
-- Imports OSM nodes and ways carrying at least one QFDMO-relevant tag into a
-- single PostgreSQL table (base_osm) with columns: osm_id, tags (jsonb),
-- osm_version, osm_timestamp, osm_user, and geometry.
--
-- Filter philosophy:
--   - The filter is deliberately GENEROUS: an element is kept as soon as at
--     least one of its tags (key=value, lowercased) is in the whitelist
--     `relevant_tag_values` below (QFDMO scope: drop-off/recycling, repair,
--     second-hand/reuse, rental).
--   - The strict mapping to the acteur schema (actions, proposition
--     services, acteur types, ...) is done DOWNSTREAM (base_osm -> acteur
--     candidates), not here. We prefer to import a bit too wide rather than
--     being forced to re-run osm2pgsql on the full France PBF to recover a
--     wrongly excluded category.
-- ============================================================================

-- Configuration
local projection = 4326 -- EPSG:4326 (WGS 84 lat/lon)

-- ---------------------------------------------------------------------------
-- Table definition
-- ---------------------------------------------------------------------------
local t = osm2pgsql.define_table({
    name    = "base_osm",
    ids     = { type = "any", id_column = "osm_id", create_index = "unique" },
    columns = {
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
-- Whitelist of QFDMO-relevant tags, as "key=value" strings (lowercase).
--
-- All tags of an element are inspected: a node/way is kept as soon as ONE of
-- its tags matches an entry. An element with several tags (e.g. building=yes
-- + shop=bicycle) is thus imported through its relevant tag.
-- ---------------------------------------------------------------------------
local relevant_tag_values = {
    -- 1. Drop-off / recycling / donation (broad: déchèteries, recyclings
    --    points, give boxes; accepted materials are detailed by the
    --    recycling:*=yes subkeys on the object itself)
    ["amenity=recycling"] = true,       -- déchèterie (recycling_type=centre)
                                        -- or recycling point
                                        -- (recycling_type=container)
    ["amenity=givebox"] = true,         -- boîte à dons

    -- 2. Shops: repair / second-hand / reuse
    ["shop=bicycle"] = true,            -- bike sales and/or repair
    ["shop=second_hand"] = true,        -- dépôt-vente, second-hand, ressourcerie
    ["shop=charity"] = true,            -- charity / reuse shop
    ["shop=antiques"] = true,           -- antiques / flea market
    ["shop=electronics"] = true,        -- electronics / electrical appliances
    ["shop=mobile_phone"] = true,
    ["shop=computer"] = true,
    ["shop=appliance"] = true,          -- large appliances (repair)
    ["shop=furniture"] = true,          -- furniture
    ["shop=books"] = true,              -- books (second-hand)
    ["shop=clothes"] = true,
    ["shop=clothing"] = true,
    ["shop=footwear"] = true,
    ["shop=shoes"] = true,
    ["shop=musical_instrument"] = true, -- musical instruments
    ["shop=jewelry"] = true,
    ["shop=jewellery"] = true,
    ["shop=optician"] = true,           -- optician (repair)
    ["shop=tools"] = true,              -- tools

    -- 3. Craftspeople / specialists (repair)
    ["craft=shoe_repair"] = true,
    ["craft=shoemaker"] = true,
    ["craft=tailor"] = true,
    ["craft=seamstress"] = true,
    ["craft=watch_repair"] = true,
    ["craft=key_cutter"] = true,
    ["craft=locksmith"] = true,
    ["craft=electronics_repair"] = true,
    ["craft=bicycle_repair"] = true,
    ["craft=upholsterer"] = true,
    ["craft=jeweller"] = true,
    ["craft=jewelry"] = true,

    -- 4. Rental / sharing
    ["amenity=bicycle_rental"] = true,  -- bike rental
}

-- Deliberately excluded (not in QFDMO scope of object repair/reuse/
-- recycling): building trades (craft=plumber, craft=electrician, ...),
-- food & hospitality, health, tourism, leisure, offices, telecom,
-- landuse, and standalone `building=*` tags.

-- ---------------------------------------------------------------------------
-- Helper: return true if at least one tag is in the whitelist
-- ---------------------------------------------------------------------------
local function has_relevant_tags(tags)
    for k, v in pairs(tags) do
        local tag = string.lower(tostring(k)) .. "=" .. string.lower(tostring(v))
        if relevant_tag_values[tag] then
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
