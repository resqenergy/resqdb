CREATE OR REPLACE FUNCTION node_label(node text) RETURNS text
LANGUAGE sql STABLE SET search_path = public AS $$
  SELECT COALESCE((SELECT label FROM label WHERE component = node), node)
$$;

CREATE OR REPLACE FUNCTION flow_label(from_node text, to_node text) RETURNS text
LANGUAGE sql STABLE SET search_path = public AS $$
  SELECT COALESCE(
    (SELECT label FROM label WHERE component = from_node AND NOT is_bus),
    (SELECT label FROM label WHERE component = to_node AND NOT is_bus),
    from_node,
    to_node
  )
$$;
