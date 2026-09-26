# Customer churn: which revenue is at risk?

The same idea as this repo's demo, built into your own app. Paste the text below into your coding agent from your project folder.

---

Use the Neo4j agent skills and the `neo4j` MCP server, which is hosted on my Aura Free instance and already connected. Don't install Neo4j locally or set up another MCP server. I don't know Cypher, so explain each step in plain English.

Build a customer knowledge graph and connect it to my app's agent.

Suggested model (adapt it to my data): Customer, Contract, Person (contacts), Ticket, Issue (bugs), Note. For example (Customer)-[:HAS_CONTRACT]->(Contract), (Customer)-[:PRIMARY_CONTACT {since, until}]->(Person), (Customer)-[:OPENED]->(Ticket)-[:REPORTS]->(Issue), (Note)-[:ABOUT]->(Customer).

1. Show me the model and wait for my OK.
2. Load realistic sample data (about 50 customers), or my own data if I point you to it. Store note and ticket text on nodes with a vector index.
3. Answer these with the path behind each answer:
   - Which customers are most at risk of churning this quarter, and why? (Signals: renewal soon, open high-severity tickets, primary contact left, negative notes.)
   - How much revenue is exposed to our worst open bug, and which customers are affected?
   - Who is our current contact at our biggest customer, and what have they asked about recently?
4. Connect my app's agent to the graph with the Neo4j driver for my language. Put my Aura credentials in `.env` and keep that file out of git. Give the agent tools to get the schema, run read-only Cypher, and run vector search over the text. Describe the graph model in its system prompt, and have it show the connections behind every answer.
