# Neo4j: the knowledge layer for your AI agents

Give your agent a knowledge graph and it can answer questions that need connected facts, such as
source code analysis, supply chain risk, fraud detection and agent memory, and show the
connections behind every answer.

This repo has two parts:

1. **[Add Neo4j to your agent](#add-neo4j-to-your-agent-about-5-minutes)**: setup commands and
   copy-paste prompts. Your coding agent does the Neo4j work. No prior Neo4j or Cypher knowledge required.
2. **[See why: the side-by-side demo](#see-why-the-side-by-side-demo)**: the same question answered
   by a vector-only agent and a graph + vector agent.

## Add Neo4j to your agent (about 5 minutes)

Works with Claude Code, Cursor, VS Code, Codex, Gemini CLI and other agents that support MCP and
Agent Skills.

**1. Create a free database.** Go to [console.neo4j.io](https://console.neo4j.io), sign up, and
create an **AuraDB Free** instance (no credit card). Copy its instance ID from the instance list.

**2. Install the Neo4j Agent Skills** in your project folder. They teach your agent Cypher, graph
modeling, data import, vector search, GraphRAG, agent memory and the Neo4j drivers. To pick the
skills and your agent from a menu, run:

```bash
npx -y skills add neo4j-contrib/neo4j-skills
```

Or install all the skills for Claude Code without any prompts:

```bash
npx -y skills add neo4j-contrib/neo4j-skills --skill '*' --agent claude-code -y
```

If you don't use Claude Code, replace `claude-code` with your agent: `cursor`, `codex`,
`gemini-cli`, `github-copilot` (VS Code) or `windsurf`.

**3. Connect your agent to your database** with the MCP server that Aura hosts for every instance.
Replace `<INSTANCE_ID>` with your instance ID.

Claude Code:
```bash
claude mcp add --transport http neo4j https://<INSTANCE_ID>.mcp-instances.neo4j.io
```

Cursor (`.cursor/mcp.json`):
```json
{ "mcpServers": { "neo4j": { "url": "https://<INSTANCE_ID>.mcp-instances.neo4j.io" } } }
```

VS Code (`.vscode/mcp.json`):
```json
{ "servers": { "neo4j": { "type": "http", "url": "https://<INSTANCE_ID>.mcp-instances.neo4j.io" } } }
```

For other agents, see [Neo4j's client configuration guide](https://neo4j.com/docs/mcp/current/client-configuration/).

Then sign in with your Aura account. In Claude Code, type `/mcp`, select `neo4j` and choose
**Authenticate**; other agents prompt you the first time they use the server. A browser window opens
for the sign-in. There's nothing to install and no password in any config file. Start a new chat
afterwards so your agent picks up the new tools.

**4. Check that it works.** Ask your agent: *"Use the neo4j MCP server to show me my database schema."*
A new database is empty, so expect an empty schema.

**5. Paste a prompt** from the [`prompts/`](prompts/) folder into your agent:

| Prompt | What your agent builds |
|---|---|
| [add-knowledge-layer.md](prompts/add-knowledge-layer.md) | A graph model of your own app's data, connected to your agent |
| [customer-churn.md](prompts/customer-churn.md) | Which customers are at risk and why, and how much revenue a bug puts at risk |
| [source-code-analysis.md](prompts/source-code-analysis.md) | Your codebase as a graph: what breaks if you change a function, circular imports, code owners |
| [supply-chain.md](prompts/supply-chain.md) | Single-supplier risks and what a regional disruption affects |
| [fraud-detection.md](prompts/fraud-detection.md) | Accounts connected to known fraud, and money moving through chains of accounts |
| [agent-memory.md](prompts/agent-memory.md) | Long-term memory for your agent that keeps track of how facts and people connect |

Each prompt has your agent propose a small graph model (and wait for your OK), load sample data or
your own, answer example questions with the connections behind them, and connect your app's agent.

**Your app's own agent:** the hosted MCP server signs in through a browser, which suits coding agents
and chat apps. An agent running inside your product connects with the Neo4j driver instead, and
every prompt includes that step. [`tools.py`](tools.py) in this repo is a working example.

## See why: the side-by-side demo

Two AI agents answer the same questions about a (fictional) SaaS company's customers:

- **Vector-only agent**: can search documents by similarity.
- **Graph + vector agent**: can do the same search, *and* query a knowledge graph.

Same model, same prompt, same data, same Neo4j database, same limits. The only difference is that
the agent on the right has two extra tools, `get_schema` and `read_cypher`: the same abilities the
hosted MCP server gives your agent. Ask a question that needs facts connected across many records,
and you'll see the difference.

The demo is a Python app that connects to Neo4j directly, so unlike the steps above it needs
connection details in a `.env` file.

### Why the comparison is fair

- Both agents call the **exact same** `search_documents` function. The graph agent just has more tools.
- Every fact in the graph also appears in a document, so the vector-only agent has access to the
  same information. `load_data.py` checks this and refuses to load if any fact is missing.
- Each document is one short, self-contained chunk: the easiest case for vector search.
- Both agents use the same Claude model, system prompt and limits.
- Each agent can only run the tools it was given: `run_agent` refuses a call to any other tool.
- One of the demo questions is a single-customer lookup, where vector search does well.
- The graph agent can also reach documents by following the graph (for example, every note linked
  to one customer). That's part of what a graph adds, and it shows up in the tool calls.
- The app shows every tool call, so you can see how each agent worked.

**Stress test:** want to see the vector agent with more room? Raise the limits for both agents:

```bash
MAX_TOOL_CALLS=20 MAX_SEARCH_RESULTS=50 python check.py 2
```

**What this demo doesn't show:**
- The baseline is plain similarity search, with no metadata filters or reranking. Those help, but
  combining facts across records (renewal dates + fix dates + the tickets that link them) and
  adding up numbers still means joining data in your own code.
- The dataset is small. With about 300 short documents you could fit everything in the prompt; the demo
  stands in for a real company with thousands of customers, where you can't.
- Questions 2 and 3 would also be answerable with SQL. The demo shows that structured, connected
  data beats similarity search alone, not that graphs beat every database.

### Setup (about 10 minutes)

1. **Create a free Neo4j database** (see step 1 above) and download the credentials file Aura gives you.
2. **Get a Claude API key** at [platform.claude.com](https://platform.claude.com).
3. **Configure:** copy `.env.example` to `.env` and fill in the values from steps 1 and 2.
4. **Install:**
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
5. **Load the demo data** (60 customers, 301 documents). The first run downloads a free embedding model (~440 MB):
   ```bash
   python load_data.py
   ```
6. **Run the app:**
   ```bash
   streamlit run app.py
   ```
   Or run the demo questions in the terminal: `python check.py`

### Try these questions

The right answers are listed here (and in the app's answer key) so you can judge both agents.
You don't have to take them on trust: the app's answer key recomputes each answer from the live
database, quotes the documents every fact appears in (the same documents the vector-only agent
searches), and shows the query so you can run it yourself in Neo4j Aura. The answers and queries
are in [`answer_key.py`](answer_key.py).

Answers change from run to run, because Claude words its searches differently each time, so
it's worth asking a question more than once.

**1. "Draft a short check-in email to our main contact at Globex about the export issue."**
- The contact is now Sam Patel (VP Operations), who replaced Maria Chen and prefers short emails. The fix is targeted for Acme 3.3 on Oct 20. This is a single-customer lookup, which vector search handles well: a check that the vector agent isn't handicapped.

**2. "How much ARR is exposed to the CSV export timeout bug, and which customers are affected?"**
- 11 customers, $1,223,000 ARR. Answering this means finding *every* affected customer and adding up their ARR. Similarity search returns the closest matches, not all of them.

**3. "Which customers renew this year before a fix ships for a bug they reported?"**
- 4 customers, $466,000 ARR: Amberline Shipping (renews Oct 13), Eastlake Water District (Oct 20), Lantern Nonprofit Network (Nov 1) and Meridian Freight (Dec 9). Each has an open ticket about a bug with no fix date. Answering this means comparing each bug's fix date with each affected customer's renewal date, across every ticket.
- Trap: Globex and Lumen Retail have the loudest bug (CSV export timeouts), but its fix ships Oct 20, before both renewals.

### How it works

| File | What it does |
|---|---|
| `acme_data.py` | Generates the fictional company data (graph records and text documents from the same source) |
| `load_data.py` | Loads the graph, the documents and a vector index into Neo4j |
| `tools.py` | The three tools: `search_documents`, `get_schema`, `read_cypher` |
| `agent.py` | The agent loop. `VECTOR_ONLY` and `GRAPH_AND_VECTOR` are the two tool lists |
| `app.py` | The side-by-side Streamlit app |
| `check.py` | Runs the demo questions through both agents in the terminal |
| `answer_key.py` | The right answer to each demo question, and the query that proves it from the live data |
| `graph_view.py` | Draws the graph behind the graph agent's answer, using Neo4j's visualization library (`neo4j-viz`) |
| `.streamlit/config.toml`, `assets/` | The app's Neo4j colors, fonts and logo |

The graph:

```
(:Customer)-[:HAS_CONTRACT]->(:Contract)
(:Customer)-[:PRIMARY_CONTACT {since, until}]->(:Person)
(:Customer)-[:OPENED]->(:Ticket)-[:REPORTS]->(:Issue)
(:Document)-[:ABOUT]->(:Customer)          // Document nodes hold the text and embeddings
```

**Using a different embedding model:** in `tools.py`, change the `embed()` function, set
`EMBEDDING_DIMENSIONS` to your model's vector size, and set `QUERY_PREFIX` to `""` unless your model
expects one. Then reload with `python load_data.py --reset`.
