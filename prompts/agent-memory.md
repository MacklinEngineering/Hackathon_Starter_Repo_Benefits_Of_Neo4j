# Agent memory: remember every user, with the connections

Paste the text below into your coding agent from your project folder.

---

Use the Neo4j agent skills and the `neo4j` MCP server, which is hosted on my Aura Free instance and already connected. Don't install Neo4j locally or set up another MCP server. I don't know Cypher, so explain each step in plain English.

Give my app's agent long-term memory stored as a knowledge graph in my Aura Free instance.

1. Add the `neo4j-agent-memory` package to my app, using its direct connection to my own Aura instance (not the hosted memory service). Put my Aura credentials in `.env` and keep that file out of git. Use my app's existing LLM and embedding providers.
2. Wire it into my agent: save each conversation, extract people, companies, preferences and facts, and recall relevant memories before each answer.
3. Show me it working with a short script of three sessions: in session 1 I share a few facts about myself and people I work with; in session 2 one of those facts changes; in session 3 I ask a question that needs both the updated fact and a connection between two people.
4. Using the MCP server's read tool, show me the memory graph for my test user and explain how the agent found its answer.
