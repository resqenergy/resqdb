SELECT
    scenario_id,
    scenario.name AS scenario_name,
    cluster.name,
    flow_label(from_node, to_node) AS label,
    total_energy
FROM sequence
JOIN cluster_component USING (from_node)
JOIN cluster ON cluster_component.cluster_id = cluster.id
JOIN scenario ON sequence.scenario_id = scenario.id
WHERE sequence.attribute = 'flow'
ORDER BY scenario_id, cluster.name
