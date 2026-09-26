# Add a knowledge layer to your agent

Paste the text below into your coding agent (Claude Code, Cursor, Codex, ...) from your project folder.

---

Use the Neo4j agent skills and the `neo4j` MCP server, which is hosted on my Aura Free instance and already connected. Don't install Neo4j locally or set up another MCP server. I don't know Cypher, so explain each step in plain English.

I want my app's agent to answer questions using connected facts from a Neo4j knowledge graph, and to show the connections behind each answer.

1. Look through this project and tell me what data my agent works with (users, customers, documents, events, and so on). Propose a small graph model: at most 8 node types with clearly named relationships. Show it to me and wait for my OK.
2. Load realistic sample data for that model (a few hundred records), or my own data if I point you to it. Use the MCP server's write tool for small amounts; for more, write a short load script with the Neo4j driver. If the data includes text (notes, messages, documents), store it on nodes and create a vector index using the embedding model my app already uses.
3. Using the MCP server's read tool, answer 3 questions that need facts from several connected records, and show the path behind each answer.
4. Connect my app's agent to the graph with the Neo4j driver for my language. Put my Aura credentials in `.env` and keep that file out of git. Give the agent tools to get the schema, run read-only Cypher, and (if there's text) run vector search. Describe the graph model in its system prompt, and have it show the connections behind every answer.
5. Suggest one question I can use in my demo that shows what the graph adds.
