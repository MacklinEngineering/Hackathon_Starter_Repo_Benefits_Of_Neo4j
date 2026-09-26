# Fraud detection: who is connected to known fraud?

Paste the text below into your coding agent from your project folder.

---

Use the Neo4j agent skills and the `neo4j` MCP server, which is hosted on my Aura Free instance and already connected. Don't install Neo4j locally or set up another MCP server. I don't know Cypher, so explain each step in plain English.

Build a fraud detection knowledge graph and connect it to my app's agent.

Suggested model (adapt it to my data): Person, Account, Device, IPAddress, Card, Transaction, Merchant. For example (Person)-[:OWNS]->(Account), (Account)-[:USED]->(Device), (Account)-[:LOGGED_IN_FROM]->(IPAddress), (Account)-[:SENT]->(Transaction)-[:TO]->(Account), (Transaction)-[:AT]->(Merchant).

1. Show me the model and wait for my OK.
2. Load realistic sample data (a few hundred records, including a small fraud ring that shares devices), or my own data if I point you to it.
3. Answer these with the path behind each answer:
   - Which accounts share a device or IP address with an account already flagged for fraud?
   - Where does money move through 3 or more accounts within 24 hours?
   - Which merchants have an unusual cluster of brand-new accounts?
4. Connect my app's agent to the graph with the Neo4j driver for my language. Put my Aura credentials in `.env` and keep that file out of git. Give the agent tools to get the schema and run read-only Cypher. Describe the graph model in its system prompt, and have it show the connections behind every answer.
