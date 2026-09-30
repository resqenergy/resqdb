WITH flows AS (
    SELECT
        scenario_id,
        scenario.name AS scenario_name,
        flow_label(from_node, to_node) AS label,
        attribute,
        value
    FROM scalar
    JOIN scenario ON scalar.scenario_id = scenario.id
    WHERE attribute IN ('capacity', 'total')
)
SELECT
    scenario_id,
    scenario_name,
    label,
    COALESCE(
        MAX(CASE WHEN attribute = 'total' THEN value END),
        MAX(CASE WHEN attribute = 'capacity' THEN value END)
    ) AS capacity
FROM flows
WHERE label NOT LIKE ALL(
    ARRAY['Abregelung%', 'Fehlmenge%', '%Export', '%Import']
)
GROUP BY
    scenario_id,
    scenario_name,
    label
