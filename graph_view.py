"""Draw the graph behind an answer with Neo4j's visualization library (neo4j-viz).

The picture shows the customers named in the answer, with their active contract,
primary contacts, open tickets (and the issues they report) and recent call notes.
"""

import re
from functools import lru_cache

import neo4j
from neo4j_viz import Node, Relationship, VisualizationGraph

from tools import DATABASE, get_driver

COLORS = {
    "Customer": "#4C8EDA", "Contract": "#57C7A3", "Person": "#F79767",
    "Ticket": "#F16667", "Issue": "#C990C0", "Document": "#A5ABB6",
}

EVIDENCE_QUERY = """
MATCH (c:Customer) WHERE c.name IN $names
CALL (c) {
  MATCH (c)-[r:HAS_CONTRACT]->(n:Contract {status: 'active'}) RETURN c AS a, r, n AS b
  UNION
  MATCH (c)-[r:PRIMARY_CONTACT]->(n:Person) RETURN c AS a, r, n AS b
  UNION
  MATCH (c)-[r:OPENED]->(n:Ticket {status: 'open'}) RETURN c AS a, r, n AS b
  UNION
  MATCH (c)-[:OPENED]->(t:Ticket {status: 'open'})-[r:REPORTS]->(n:Issue) RETURN t AS a, r, n AS b
  UNION
  MATCH (n:Document {type: 'note'})-[r:ABOUT]->(c) WHERE n.date >= date('2026-08-15')
  RETURN n AS a, r, c AS b
}
RETURN a, r, b
"""


@lru_cache
def _customer_aliases() -> dict[str, str]:
    """Map each customer name, and its first word when unique (e.g. "Globex"), to the full name."""
    records, _, _ = get_driver().execute_query(
        "MATCH (c:Customer) RETURN c.name AS name",
        database_=DATABASE, routing_=neo4j.RoutingControl.READ,
    )
    names = [r["name"] for r in records]
    first_words = [name.split()[0] for name in names]
    aliases = {name: name for name in names}
    for name, first in zip(names, first_words):
        if first_words.count(first) == 1 and len(first) > 3:
            aliases[first] = name
    return aliases


def customers_named_in(text: str) -> list[str]:
    found = {full for alias, full in _customer_aliases().items()
             if re.search(rf"\b{re.escape(alias)}\b", text)}
    return sorted(found)


LEFT_COLOR = "#6B6B6B"  # contacts who left the customer


def _caption(node) -> str:
    """Short captions: the renderer wraps long ones mid-word."""
    label, p = next(iter(node.labels)), node
    if label == "Customer":
        return f"{p['name'].split()[0]} ${p['arr'] // 1000}K"
    if label == "Contract":
        return str(p["renewal_date"])
    if label == "Ticket":
        return f"{p['id']} {p['severity']}"
    if label == "Document":
        return "note " + p["date"].to_native().strftime("%b %-d")
    return p.get("name") or p.get("id") or label


def evidence_html(answer: str, max_customers: int = 12) -> str | None:
    """Return an interactive graph picture (HTML) for the customers named in the answer."""
    names = customers_named_in(answer)[:max_customers]
    if not names:
        return None
    records, _, _ = get_driver().execute_query(
        EVIDENCE_QUERY, names=names, database_=DATABASE, routing_=neo4j.RoutingControl.READ,
    )

    # Contacts who left get their own color (relationship captions are too small to read).
    departed = {r["b"].element_id for r in records
                if r["r"].type == "PRIMARY_CONTACT" and r["r"].get("until")}

    nodes, relationships = {}, []
    for record in records:
        for node in (record["a"], record["b"]):
            label = next(iter(node.labels))
            nodes[node.element_id] = Node(
                id=node.element_id, caption=_caption(node),
                color=LEFT_COLOR if node.element_id in departed else COLORS.get(label),
                size=90 if label == "Customer" else 60,
                properties={"label": label, **{k: str(v) for k, v in node.items() if k != "embedding"}},
            )
        rel = record["r"]
        left = rel.type == "PRIMARY_CONTACT" and rel.get("until")
        relationships.append(Relationship(
            id=rel.element_id, source=rel.start_node.element_id, target=rel.end_node.element_id,
            caption="LEFT" if left else rel.type,
            properties={k: str(v) for k, v in rel.items()},
            **({"color": "#D64545"} if left else {}),  # highlight contacts who left
        ))

    graph = VisualizationGraph(nodes=list(nodes.values()), relationships=relationships)
    return graph.render(height="440px", theme="light", show_search_button=False).data
