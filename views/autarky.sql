WITH
  renewables AS (
    SELECT
      scenario_id,
      sequence.id AS sequence_id,
      category,
      total_energy
    FROM
      sequence
      LEFT JOIN category USING (from_node, to_node)
    WHERE
      attribute = 'flow'
      AND carrier = 'electricity'
      AND (
        is_renewable
        OR from_node IN (SELECT component FROM component WHERE role = 'storage')
        OR category = 'Verbrauch'
      )
  ),
  autarky_per_timestep AS (
    SELECT
      scenario_id,
      timestamp,
      SUM(CASE WHEN category = 'Verbrauch' THEN -value ELSE value END) AS value
    FROM renewables
    JOIN timeseries USING (sequence_id)
    GROUP BY scenario_id, timestamp
  ),
  autarky AS (
    SELECT
      scenario_id,
      'Zeitgleich' AS type,
      COUNT(*) FILTER (
        WHERE
          value > 0
      ) AS autarky
    FROM
      autarky_per_timestep
    GROUP BY
      scenario_id

    UNION ALL

    SELECT
      scenario_id,
      'Bilanziell' AS type,
      SUM(total_energy) FILTER (
        WHERE
          category = 'Erzeugung'
      ) / NULLIF(
        SUM(total_energy) FILTER (
          WHERE
            category = 'Verbrauch'
        ),
        0
      ) * 100 AS autarky
    FROM
      renewables
    GROUP BY
      scenario_id
  )
SELECT
  dimensions.*,
  type,
  autarky
FROM autarky
JOIN scenario_dimensions() AS dimensions USING (scenario_id)
