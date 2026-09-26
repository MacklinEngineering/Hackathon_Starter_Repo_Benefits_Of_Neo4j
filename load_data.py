"""Load the Acme demo data into Neo4j: the graph, the documents, and a vector index.

    python load_data.py           # load into an empty database
    python load_data.py --reset   # delete everything in the database first
"""

import sys

import acme_data
from tools import DATABASE, EMBEDDING_DIMENSIONS, VECTOR_INDEX, embed, get_driver

SCHEMA = [
    "CREATE CONSTRAINT customer_name IF NOT EXISTS FOR (c:Customer) REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT contract_id IF NOT EXISTS FOR (c:Contract) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT person_name IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE",
    "CREATE CONSTRAINT ticket_id IF NOT EXISTS FOR (t:Ticket) REQUIRE t.id IS UNIQUE",
    "CREATE CONSTRAINT issue_id IF NOT EXISTS FOR (i:Issue) REQUIRE i.id IS UNIQUE",
    "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
    f"""CREATE VECTOR INDEX {VECTOR_INDEX} IF NOT EXISTS
        FOR (d:Document) ON d.embedding
        OPTIONS {{indexConfig: {{`vector.dimensions`: {EMBEDDING_DIMENSIONS},
                                 `vector.similarity_function`: 'cosine'}}}}""",
]

LOAD_CUSTOMERS = """
UNWIND $rows AS r
CREATE (:Customer {name: r.name, industry: r.industry, plan: r.plan, arr: r.arr})
"""
LOAD_CONTRACTS = """
UNWIND $rows AS r
MATCH (c:Customer {name: r.customer})
CREATE (c)-[:HAS_CONTRACT]->(:Contract {
  id: r.id, start_date: date(r.start_date), renewal_date: date(r.renewal_date),
  status: r.status, auto_renew: r.auto_renew})
"""
LOAD_CONTACTS = """
UNWIND $rows AS r
MATCH (c:Customer {name: r.customer})
MERGE (p:Person {name: r.name}) SET p.title = r.title
CREATE (c)-[:PRIMARY_CONTACT {since: date(r.since), until: date(r.until)}]->(p)
"""
LOAD_ISSUES = """
UNWIND $rows AS r
CREATE (:Issue {id: r.id, title: r.title, status: r.status, introduced_in: r.introduced_in,
                fixed_in: r.fixed_in, fix_target: date(r.fix_target)})
"""
LOAD_TICKETS = """
UNWIND $rows AS r
MATCH (c:Customer {name: r.customer})
CREATE (c)-[:OPENED]->(t:Ticket {
  id: r.id, subject: r.subject, severity: r.severity, status: r.status,
  opened_on: date(r.opened_on), closed_on: date(r.closed_on)})
WITH t, r WHERE r.issue IS NOT NULL
MATCH (i:Issue {id: r.issue})
CREATE (t)-[:REPORTS]->(i)
"""
LOAD_DOCUMENTS = """
UNWIND $rows AS r
CREATE (d:Document {id: r.id, type: r.type, date: date(r.date), title: r.title,
                    text: r.text, embedding: r.embedding})
WITH d, r WHERE r.customer IS NOT NULL
MATCH (c:Customer {name: r.customer})
CREATE (d)-[:ABOUT]->(c)
"""


def main():
    driver = get_driver()
    driver.verify_connectivity()
    run = lambda query, **params: driver.execute_query(query, database_=DATABASE, **params)

    existing = run("MATCH (n) RETURN count(n) AS n").records[0]["n"]
    if existing and "--reset" not in sys.argv:
        sys.exit(f"The database already has {existing} nodes. Run `python load_data.py --reset` "
                 "to delete ALL data in it and load the demo data.")
    if existing:
        print(f"Deleting {existing} existing nodes...")
        with driver.session(database=DATABASE) as session:  # batched deletes need a session
            session.run("MATCH (n) CALL (n) { DETACH DELETE n } IN TRANSACTIONS OF 1000 ROWS").consume()
    # Recreate the vector index so its size always matches the current embedding model.
    run(f"DROP INDEX {VECTOR_INDEX} IF EXISTS")

    ds = acme_data.build()
    missing = acme_data.check_parity(ds)
    if missing:  # keeps the comparison fair: the vector agent must be able to find every fact
        sys.exit(f"These graph facts don't appear in any document: {missing}")
    print("Parity check passed: every fact in the graph also appears in a document.")

    print("Creating constraints and vector index...")
    for statement in SCHEMA:
        run(statement)

    print("Loading the graph...")
    run(LOAD_CUSTOMERS, rows=ds.customers)
    run(LOAD_CONTRACTS, rows=ds.contracts)
    run(LOAD_CONTACTS, rows=ds.contacts)
    run(LOAD_ISSUES, rows=ds.issues)
    run(LOAD_TICKETS, rows=ds.tickets)

    print(f"Embedding {len(ds.documents)} documents (the first run downloads a small model)...")
    vectors = embed([d["text"] for d in ds.documents])
    rows = [{**doc, "embedding": vec} for doc, vec in zip(ds.documents, vectors)]
    run(LOAD_DOCUMENTS, rows=rows)
    run("CALL db.awaitIndexes(300)")

    counts = run("MATCH (n) RETURN labels(n)[0] AS label, count(*) AS n ORDER BY label").records
    print("Done: " + ", ".join(f"{r['n']} {r['label']}" for r in counts))


if __name__ == "__main__":
    main()
