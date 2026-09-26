"""The tools the agents can call.

search_documents  vector search over text documents (both agents get this)
get_schema        describe the graph (graph agent only)
read_cypher       run a read-only Cypher query (graph agent only)

get_schema and read_cypher mirror the schema and read tools of the Neo4j MCP
server that Aura hosts for every instance. Coding agents and chat apps can use
that server directly (see the README); an agent running inside your own app can
copy these functions instead.
"""

import json
import os
import threading
from datetime import date, datetime

import neo4j
from dotenv import load_dotenv
from neo4j.time import Date, DateTime, Duration

load_dotenv()

DATABASE = os.getenv("NEO4J_DATABASE") or None
VECTOR_INDEX = "document_embeddings"
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"  # free, runs locally, no API key
EMBEDDING_DIMENSIONS = 768
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "  # bge models expect this
MAX_RESULT_CHARS = 12_000
MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "10"))

_lock = threading.Lock()
_driver = None
_embedder = None


def get_driver():
    global _driver
    with _lock:
        if _driver is None:
            _driver = neo4j.GraphDatabase.driver(
                os.environ["NEO4J_URI"],
                auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
                notifications_min_severity="OFF",
            )
        return _driver


def embed(texts: list[str]) -> list[list[float]]:
    """Swap this function to use your own embedding provider."""
    global _embedder
    with _lock:
        if _embedder is None:
            from sentence_transformers import SentenceTransformer
            _embedder = SentenceTransformer(EMBEDDING_MODEL)
        return _embedder.encode(texts, normalize_embeddings=True).tolist()


def search_documents(query: str, k: int = 5) -> str:
    k = max(1, min(int(k), MAX_SEARCH_RESULTS))
    records, _, _ = get_driver().execute_query(
        """
        CALL db.index.vector.queryNodes($index, $k, $embedding) YIELD node, score
        RETURN node.id AS id, node.type AS type, toString(node.date) AS date,
               node.text AS text, round(score, 3) AS score
        """,
        index=VECTOR_INDEX, k=k, embedding=embed([QUERY_PREFIX + query])[0],
        database_=DATABASE, routing_=neo4j.RoutingControl.READ,
    )
    return _to_text([r.data() for r in records])


def get_schema() -> str:
    driver = get_driver()
    read = {"database_": DATABASE, "routing_": neo4j.RoutingControl.READ}

    node_props, _, _ = driver.execute_query("CALL db.schema.nodeTypeProperties()", **read)
    rel_props, _, _ = driver.execute_query("CALL db.schema.relTypeProperties()", **read)
    schema, _, _ = driver.execute_query("CALL db.schema.visualization()", **read)
    patterns = {
        (rel.start_node["name"], rel.type, rel.end_node["name"])
        for rel in schema[0]["relationships"]
    }

    lines = ["Node labels and properties:"]
    labels: dict[str, list[str]] = {}
    for r in node_props:
        label = ":".join(r["nodeLabels"])
        if r["propertyName"] and r["propertyName"] != "embedding":
            types = "|".join(t.replace("NOT NULL", "").strip() for t in r["propertyTypes"] or [])
            labels.setdefault(label, []).append(f"{r['propertyName']} ({types})")
    for label, props in sorted(labels.items()):
        lines.append(f"  (:{label}) {', '.join(props)}")

    rel_types: dict[str, list[str]] = {}
    for r in rel_props:
        rel_type = r["relType"].strip(":`")
        if r["propertyName"]:
            types = "|".join(r["propertyTypes"] or [])
            rel_types.setdefault(rel_type, []).append(f"{r['propertyName']} ({types})")
    lines.append("Relationships:")
    for start, rel_type, end in sorted(patterns):
        props = rel_types.get(rel_type)
        props_text = f" {{{', '.join(props)}}}" if props else ""
        lines.append(f"  (:{start})-[:{rel_type}{props_text}]->(:{end})")
    lines.append(
        f"Vector index `{VECTOR_INDEX}` on Document.embedding is used by search_documents; "
        "don't return the embedding property."
    )
    return "\n".join(lines)


def read_cypher(query: str) -> str:
    # RoutingControl.READ runs the query in a read transaction, so Neo4j rejects writes.
    records, _, _ = get_driver().execute_query(
        neo4j.Query(query, timeout=20),
        database_=DATABASE, routing_=neo4j.RoutingControl.READ,
    )
    rows = [{key: _jsonable(value) for key, value in r.items()} for r in records[:100]]
    if len(records) > 100:
        rows.append({"note": f"{len(records) - 100} more rows not shown"})
    return _to_text(rows)


def _jsonable(value):
    if isinstance(value, neo4j.graph.Node):
        props = {k: _jsonable(v) for k, v in value.items() if k != "embedding"}
        return {"labels": list(value.labels), **props}
    if isinstance(value, neo4j.graph.Relationship):
        return {"type": value.type, **{k: _jsonable(v) for k, v in value.items()}}
    if isinstance(value, neo4j.graph.Path):
        # Alternate nodes and relationships so the agent can show each connection.
        items = [_jsonable(value.start_node)]
        for rel, node in zip(value.relationships, value.nodes[1:]):
            items += [_jsonable(rel), _jsonable(node)]
        return items
    if isinstance(value, (Date, DateTime, Duration, date, datetime)):
        return str(value)
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    return value


def _to_text(rows) -> str:
    text = json.dumps(rows, indent=1, default=str)
    if len(text) > MAX_RESULT_CHARS:
        text = text[:MAX_RESULT_CHARS] + "\n... (truncated)"
    return text


# The graph model lives in the read_cypher description rather than the system prompt,
# so both agents keep the same system prompt and differ only in their tools.
GRAPH_MODEL = """The graph:
(:Customer)-[:HAS_CONTRACT]->(:Contract)
(:Customer)-[:PRIMARY_CONTACT {since, until}]->(:Person)  // until is empty for the current contact
(:Customer)-[:OPENED]->(:Ticket)-[:REPORTS]->(:Issue)     // an Issue is an engineering bug
(:Document)-[:ABOUT]->(:Customer)                         // the documents search_documents searches"""

# Tool definitions sent to Claude. The functions above run when Claude calls them.
TOOLS = {
    "search_documents": {
        "function": search_documents,
        "definition": {
            "name": "search_documents",
            "description": (
                "Semantic (vector) search over Acme's customer documents: contract summaries, "
                "support tickets, call notes and release notes. Returns the k most similar "
                "documents to the query. Call it again with different queries to find more."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "What to search for."},
                    "k": {"type": "integer",
                          "description": f"Number of results (1-{MAX_SEARCH_RESULTS}). Default 5."},
                },
                "required": ["query"],
            },
        },
    },
    "get_schema": {
        "function": get_schema,
        "definition": {
            "name": "get_schema",
            "description": (
                "Describe the Neo4j knowledge graph: node labels, properties and relationship "
                "types. Call this before writing Cypher."
            ),
            "input_schema": {"type": "object", "properties": {}},
        },
    },
    "read_cypher": {
        "function": read_cypher,
        "definition": {
            "name": "read_cypher",
            "description": (
                "Run a read-only Cypher query against the Neo4j knowledge graph and return the "
                "rows as JSON. Use it to follow relationships, filter, count and aggregate "
                "across all customers. Write queries are rejected.\n\n" + GRAPH_MODEL
            ),
            "input_schema": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "A Cypher query."}},
                "required": ["query"],
            },
        },
    },
}
