WITH flows AS (
    SELECT
        scenario_id,
        flow_label(from_node, to_node) AS label,
        category.carrier,
        attribute,
        value
    FROM scalar
    LEFT JOIN category USING (from_node, to_node)
    WHERE attribute IN ('capacity', 'total')
      AND NOT EXISTS (
        SELECT 1
        FROM component
        WHERE component.component IN (scalar.from_node, scalar.to_node)
          AND component.role IN ('excess', 'shortage', 'import', 'export')
      )
),
-- Result capacities ('total') replace input capacities ('capacity') of the same component.
capacities AS (
    SELECT
        scenario_id,
        label,
        carrier,
        MAX(value) AS capacity
    FROM flows
    WHERE attribute = 'total'
       OR NOT EXISTS (
        SELECT 1
        FROM flows AS totals
        WHERE totals.attribute = 'total'
          AND totals.scenario_id = flows.scenario_id
          AND totals.label = flows.label
      )
    GROUP BY
        scenario_id,
        label,
        carrier
)
SELECT
    dimensions.*,
    label,
    carrier,
    capacity
FROM capacities
JOIN scenario_dimensions() AS dimensions USING (scenario_id)
