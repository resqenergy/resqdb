SELECT
    scenario_id,
    scenario.name AS scenario_name,
    from_node,
    to_node,
    flow_label(from_node, to_node) AS label,
    category.category,
    category.carrier,
    total_energy
FROM sequence
JOIN scenario ON sequence.scenario_id = scenario.id
LEFT JOIN category USING(from_node, to_node)
WHERE sequence.attribute = 'flow' and to_node NOT LIKE ALL(ARRAY['%storage%', '%battery%', '%conn%']) and from_node NOT LIKE ALL(ARRAY['%storage%', '%battery%', '%conn%'])
ORDER BY scenario_id
