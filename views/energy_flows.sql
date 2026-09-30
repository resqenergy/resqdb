SELECT
    scenario_id,
    scenario.name AS scenario_name,
    from_node,
    to_node,
    CASE
        WHEN from_node LIKE ANY(Array['%storage%', '%battery%']) THEN CONCAT(node_label(from_node), ' (Entladen)')
        WHEN from_node = 'aquifer' THEN CONCAT(node_label(from_node), ' (Entnahme)')
        ELSE node_label(from_node)
    END AS from_label,
    CASE
        WHEN to_node LIKE ANY(Array['%storage%', '%battery%']) THEN CONCAT(node_label(to_node), ' (Laden)')
        WHEN to_node = 'aquifer' THEN CONCAT(node_label(to_node), ' (Einspeisung)')
        ELSE node_label(to_node)
    END AS to_label,
    category.category,
    total_energy
FROM sequence
JOIN scenario ON sequence.scenario_id = scenario.id
LEFT JOIN category USING(from_node, to_node)
WHERE sequence.attribute = 'flow' AND total_energy > 0
