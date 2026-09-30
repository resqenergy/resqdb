SELECT
  scenario_id,
  scenario.name AS scenario_name,
  flow_label(from_node, to_node) AS label,
  category.category,
  category.carrier,
  timestamp,
  value
FROM sequence
JOIN timeseries ON timeseries.sequence_id = sequence.id
JOIN scenario ON sequence.scenario_id = scenario.id
LEFT JOIN category USING(from_node, to_node)
ORDER BY scenario_id, label, timestamp
