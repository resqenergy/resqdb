CREATE OR REPLACE FUNCTION scenario_dimensions() RETURNS TABLE (
  scenario_id integer,
  scenario_name text,
  climate_name text,
  period_name text,
  weather_name text,
  sensitivity text
)
LANGUAGE sql STABLE SET search_path = public AS $$
  SELECT
    scenario.id,
    scenario.name,
    climate.name,
    period.name,
    weather.name,
    sensitivity.node || '.' || sensitivity.attribute || '=' || sensitivity.value
  FROM scenario
  JOIN climate ON scenario.climate_id = climate.id
  JOIN period ON scenario.period_id = period.id
  JOIN weather ON scenario.weather_id = weather.id
  LEFT JOIN sensitivity ON scenario.sensitivity_id = sensitivity.id
$$;
