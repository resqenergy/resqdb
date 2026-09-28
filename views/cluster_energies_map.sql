SELECT
    scenario_id,
    scenario.name AS scenario_name,
    cluster.name AS cluster_label,
    SUM(total_energy) AS energie,
    jsonb_build_object(
        'type',
        'Feature',
        'geometry',
        ST_AsGeoJSON (cluster.geometry)::JSONB,
        'properties',
        '{}'
    )::TEXT AS geojson
FROM sequence
JOIN cluster_component USING (from_node)
JOIN cluster ON cluster_component.cluster_id = cluster.id
JOIN scenario ON sequence.scenario_id = scenario.id
WHERE sequence.attribute = 'flow'
GROUP BY scenario_id, scenario_name, cluster.geometry, cluster.name
