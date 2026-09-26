# Supply chain: which products are at risk?

Paste the text below into your coding agent from your project folder.

---

Use the Neo4j agent skills and the `neo4j` MCP server, which is hosted on my Aura Free instance and already connected. Don't install Neo4j locally or set up another MCP server. I don't know Cypher, so explain each step in plain English.

Build a supply chain knowledge graph and connect it to my app's agent.

Suggested model (adapt it to my data): Supplier, Part, Product, Facility, Region, Shipment, Customer. For example (Supplier)-[:SUPPLIES]->(Part), (Part)-[:USED_IN]->(Product), (Supplier)-[:LOCATED_IN]->(Region), (Shipment)-[:CARRIES]->(Part), (Customer)-[:ORDERS]->(Product).

1. Show me the model and wait for my OK.
2. Load realistic sample data (a few hundred records), or my own data if I point you to it.
3. Answer these with the path behind each answer:
   - Which products depend on a single supplier for any part?
   - If a region has a disruption, which products and customers are affected, and how much revenue is at risk?
   - Which delayed shipments block the most finished products?
4. Connect my app's agent to the graph with the Neo4j driver for my language. Put my Aura credentials in `.env` and keep that file out of git. Give the agent tools to get the schema and run read-only Cypher. Describe the graph model in its system prompt, and have it show the connections behind every answer.
