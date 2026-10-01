SELECT
    dimensions.*,
    cluster.name,
    flow_label(from_node, to_node) AS label,
    category.category,
    category.carrier,
    total_energy
FROM sequence
JOIN cluster_component USING (from_node)
JOIN cluster ON cluster_component.cluster_id = cluster.id
LEFT JOIN category USING (from_node, to_node)
JOIN scenario_dimensions() AS dimensions USING (scenario_id)
WHERE sequence.attribute = 'flow'
