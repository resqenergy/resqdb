SELECT
    dimensions.*,
    from_node,
    to_node,
    flow_label(from_node, to_node) AS label,
    category.category,
    category.carrier,
    total_energy
FROM sequence
JOIN scenario_dimensions() AS dimensions USING (scenario_id)
LEFT JOIN category USING (from_node, to_node)
WHERE sequence.attribute = 'flow'
  AND NOT EXISTS (
    SELECT 1
    FROM component
    WHERE component.component IN (sequence.from_node, sequence.to_node)
      AND component.role IN ('storage', 'connector')
  )
