SELECT
    scenario_id,
    scenario.name AS scenario_name,
    flow_label(from_node, to_node) AS component,
    COALESCE(MAX(CASE WHEN attribute = 'total' THEN value END), MAX(CASE WHEN attribute = 'capacity' THEN value END)) AS capacity
FROM
  scalar
  JOIN scenario ON scalar.scenario_id = scenario.id
WHERE (attribute = 'capacity' OR attribute = 'total')
  AND COALESCE(from_node, '') NOT LIKE ALL(ARRAY['%-excess', '%-shortage'])
  AND COALESCE(to_node, '') NOT LIKE ALL(ARRAY['%-excess', '%-shortage'])
GROUP BY scenario_id, scenario.name, flow_label(from_node, to_node)
