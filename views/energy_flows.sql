SELECT
    dimensions.*,
    from_node,
    to_node,
    COALESCE(source.label_out, source.label, from_node) AS from_label,
    COALESCE(target.label_in, target.label, to_node) AS to_label,
    category.category,
    total_energy
FROM sequence
JOIN scenario_dimensions() AS dimensions USING (scenario_id)
LEFT JOIN category USING (from_node, to_node)
LEFT JOIN component AS source ON source.component = from_node
LEFT JOIN component AS target ON target.component = to_node
WHERE sequence.attribute = 'flow' AND total_energy > 0
