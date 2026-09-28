SELECT DISTINCT node
FROM (
    SELECT from_node AS node FROM scalar
    UNION
    SELECT to_node FROM scalar
    UNION
    SELECT from_node FROM sequence
    UNION
    SELECT to_node FROM sequence
) AS nodes
WHERE node IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM label WHERE label.component = nodes.node)
ORDER BY node
