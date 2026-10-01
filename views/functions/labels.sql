CREATE OR REPLACE FUNCTION node_label(node text) RETURNS text
LANGUAGE sql STABLE SET search_path = public AS $$
  SELECT COALESCE((SELECT label FROM component WHERE component = node), node)
$$;

-- Labels a flow by its non-bus side; falls back to the raw name of the non-bus side if it has no label.
CREATE OR REPLACE FUNCTION flow_label(from_node text, to_node text) RETURNS text
LANGUAGE sql STABLE SET search_path = public AS $$
  SELECT COALESCE(
    (SELECT label FROM component WHERE component = from_node AND role IS DISTINCT FROM 'bus'),
    (SELECT label FROM component WHERE component = to_node AND role IS DISTINCT FROM 'bus'),
    CASE
      WHEN EXISTS (SELECT 1 FROM component WHERE component = from_node AND role = 'bus') THEN to_node
    END,
    from_node
  )
$$;
