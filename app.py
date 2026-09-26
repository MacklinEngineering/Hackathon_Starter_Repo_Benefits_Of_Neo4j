"""Side-by-side demo: a vector-only agent vs. a graph + vector agent.

    streamlit run app.py
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from agent import DEMO_QUESTIONS, GRAPH_AND_VECTOR, MAX_TOOL_CALLS, VECTOR_ONLY, run_agent
from answer_key import ANSWER_KEY, run_proof
from graph_view import evidence_html
from tools import MAX_SEARCH_RESULTS, embed

AGENTS = {
    "vector": ("Vector-only agent", VECTOR_ONLY),
    "graph": ("Graph + vector agent", GRAPH_AND_VECTOR),
}

ASSETS = Path(__file__).parent / "assets"

st.set_page_config(page_title="Vector vs. Graph + Vector", page_icon=str(ASSETS / "neo4j-icon.png"),
                   layout="wide")
st.logo(str(ASSETS / "neo4j-logo.svg"), size="large", link="https://neo4j.com")
st.title("Does your agent need a knowledge graph?")
st.caption(
    "Two agents with the same model, prompt, data and Neo4j database, and the same limits "
    f"(up to {MAX_TOOL_CALLS} tool calls, up to {MAX_SEARCH_RESULTS} results per search). "
    "The only difference: the agent on the right can also query the graph."
)

missing = [name for name in ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD") if not os.getenv(name)]
if missing:
    st.error(f"Missing {', '.join(missing)}. Copy .env.example to .env and fill it in.")
    st.stop()


@st.cache_resource(show_spinner="Loading the embedding model...")
def warm_up():
    embed(["warm up"])  # load the model once so the first question isn't slow


warm_up()

for column, question in zip(st.columns(len(DEMO_QUESTIONS)), DEMO_QUESTIONS):
    if column.button(question, use_container_width=True):
        st.session_state.question = question
        st.session_state.ask = True

question = st.text_input("Ask about Acme Analytics' customers", key="question")
if st.button("Ask both agents", type="primary"):
    st.session_state.ask = True


def render(slot, steps, result=None):
    with slot.container():
        if result:
            calls, seconds = st.columns(2)
            calls.metric("Tool calls", len(steps))
            seconds.metric("Seconds", result["seconds"])
            st.markdown(result["answer"])
            label = f"Tool calls ({len(steps)})"
        else:
            st.info(f"Working... {len(steps)} tool calls so far")
            label = "Tool calls"
        with st.expander(label, expanded=result is None):
            for i, step in enumerate(steps, 1):
                st.markdown(f"**{i}. {step['tool']}**" + (" (error)" if step["error"] else ""))
                if step["tool"] == "read_cypher":
                    st.code(step["input"]["query"], language="cypher")
                elif step["input"]:
                    st.code(json.dumps(step["input"]), language="json")
                st.code(step["output"][:1500] + ("\n..." if len(step["output"]) > 1500 else ""),
                        language="json")
        if result and result.get("graph_html"):
            with st.expander("The graph behind this answer", expanded=True):
                st.caption(
                    "Customers named in the answer and what's connected to them. "
                    ":blue[**blue**] customer · :green[**green**] contract renewal date · "
                    ":red[**red**] open ticket · :violet[**purple**] bug · :orange[**orange**] contact · "
                    ":gray[**dark gray**] contact who left · light gray: recent note. "
                    "Drag, zoom, and click a node for details."
                )
                components.html(result["graph_html"], height=460)


columns = dict(zip(AGENTS, st.columns(2)))
slots = {}
for key, (title, tools) in AGENTS.items():
    columns[key].subheader(title)
    columns[key].caption("Tools: " + ", ".join(tools))
    slots[key] = columns[key].empty()

if st.session_state.pop("ask", False) and question.strip():
    steps = {key: [] for key in AGENTS}
    with ThreadPoolExecutor(len(AGENTS)) as pool:
        futures = {key: pool.submit(run_agent, question, tools, steps[key].append)
                   for key, (_, tools) in AGENTS.items()}
        while not all(f.done() for f in futures.values()):
            for key in AGENTS:
                render(slots[key], steps[key])
            time.sleep(0.5)
    results = {}
    for key, future in futures.items():
        try:
            results[key] = future.result()
        except Exception as e:
            results[key] = {"answer": f":red[Error: {e}]", "steps": steps[key], "seconds": 0}
    try:
        results["graph"]["graph_html"] = evidence_html(results["graph"]["answer"])
    except Exception as e:
        results["graph"]["graph_html"] = None
        st.warning(f"Couldn't draw the graph: {e}")
    st.session_state.results = results
    st.session_state.results_question = question

for key, result in st.session_state.get("results", {}).items():
    render(slots[key], result["steps"], result)

answer_key = ANSWER_KEY.get(st.session_state.get("results_question"))
if answer_key and st.session_state.get("results"):
    with st.expander("Answer key: the right answer, from the data"):
        st.markdown(answer_key["answer"])
        st.caption("The agents' answers can change from run to run: Claude words its searches "
                   "differently each time, and each search returns only the closest matches.")
        st.markdown("**Check it yourself.** This table was recomputed just now from the live database. "
                    "The *(source)* columns quote the documents each fact appears in: the same documents "
                    "the vector-only agent searches.")
        try:
            rows = run_proof(st.session_state.results_question)
            st.table([{k: " ".join(f"• {x}" for x in v) if isinstance(v, list) else v for k, v in row.items()}
                      for row in rows], hide_index=True, border="horizontal")
            if total := answer_key.get("total"):
                st.markdown(f"**Total {total}: ${sum(r[total] for r in rows):,} "
                            f"across {len(rows)} customers**")
        except Exception as e:
            st.warning(f"Couldn't recompute the answer: {e}")
        st.caption("The query behind the table. Paste it into the Query tool in Neo4j Aura to run it yourself.")
        st.code(answer_key["proof"].strip(), language="cypher")
