SELECT
  dimensions.*,
  flow_label(from_node, to_node) AS label,
  category.category,
  category.carrier,
  timestamp,
  value
FROM sequence
JOIN timeseries ON timeseries.sequence_id = sequence.id
JOIN scenario_dimensions() AS dimensions USING (scenario_id)
LEFT JOIN category USING (from_node, to_node)
WHERE sequence.attribute = 'flow'
