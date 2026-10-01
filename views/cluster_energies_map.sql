-- Only flows leaving cluster components (from_node) are counted, so demand sinks (to_node) do not show up per cluster.
WITH cluster_energies AS (
    SELECT
        scenario_id,
        cluster_component.cluster_id,
        category.category,
        category.carrier,
        SUM(total_energy) AS energie
    FROM sequence
    JOIN cluster_component USING (from_node)
    LEFT JOIN category USING (from_node, to_node)
    WHERE sequence.attribute = 'flow'
    GROUP BY scenario_id, cluster_component.cluster_id, category.category, category.carrier
)
SELECT
    dimensions.*,
    cluster.name AS cluster_label,
    category,
    carrier,
    energie,
    jsonb_build_object(
        'type',
        'Feature',
        'geometry',
        ST_AsGeoJSON (cluster.geometry)::JSONB,
        'properties',
        '{}'::JSONB
    )::TEXT AS geojson
FROM cluster_energies
JOIN cluster ON cluster_energies.cluster_id = cluster.id
JOIN scenario_dimensions() AS dimensions USING (scenario_id)
