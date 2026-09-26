# Source code analysis: what breaks if I change this?

Paste the text below into your coding agent from the folder of the codebase you want to analyze.

---

Use the Neo4j agent skills and the `neo4j` MCP server, which is hosted on my Aura Free instance and already connected. Don't install Neo4j locally or set up another MCP server. I don't know Cypher, so explain each step in plain English.

Turn this codebase into a knowledge graph and connect it to my app's agent.

Suggested model: File, Module, Class, Function, Author, Commit. For example (File)-[:DEFINES]->(Function), (Function)-[:CALLS]->(Function), (Module)-[:IMPORTS]->(Module), (Commit)-[:CHANGED]->(File), (Author)-[:AUTHORED]->(Commit).

1. Show me the model and wait for my OK.
2. Write a short script that parses this repository (files, imports, classes, functions, calls) and its git history (commits, authors), and loads it with the Neo4j driver. Put my Aura credentials in `.env` and keep that file out of git.
3. Answer these with the path behind each answer:
   - If I change the most-called function, what else could break?
   - Are there circular imports between modules?
   - Who has changed the payments (or other core) code most in the last 3 months?
4. Connect my app's agent to the graph with the Neo4j driver for my language. Give it tools to get the schema and run read-only Cypher. Describe the graph model in its system prompt, and have it show the connections behind every answer.
