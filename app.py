"""Side-by-side demo: a vector-only agent vs. a graph + vector agent.

    streamlit run app.py
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor

import streamlit as st
import streamlit.components.v1 as components

from agent import DEMO_QUESTIONS, GRAPH_AND_VECTOR, MAX_TOOL_CALLS, VECTOR_ONLY, run_agent
from graph_view import evidence_html
from tools import MAX_SEARCH_RESULTS, embed

AGENTS = {
    "vector": ("Vector-only agent", VECTOR_ONLY),
    "graph": ("Graph + vector agent", GRAPH_AND_VECTOR),
}

# The right answers, taken straight from the data, so viewers can judge both agents themselves.
ANSWER_KEY = {
    DEMO_QUESTIONS[0]: """
- **Globex Corporation** ($240K): renews Nov 18, 3 open high-severity export tickets, and its primary contact Maria Chen left on Sep 2.
- **Lumen Retail** ($180K): renews Oct 30, 2 open high-severity export tickets.
- **Fathom Legal** ($72K): evaluating cheaper alternatives before its Dec 10 renewal.
- Not at risk: **Initech** sounds angry but signed a 3-year renewal on Sep 22.
- Not at risk this year: **Cobalt Dental** is unhappy with onboarding, but doesn't renew until Jun 15, 2027.""",
    DEMO_QUESTIONS[1]: """
**$1,223,000 ARR across 11 customers:** Globex Corporation, Orchard Foods, Lumen Retail, Fieldstone Storage,
Falcon Courier, Keystone Builders, Umber Coffee Roasters, Riverbend Hospital, Jetty Marine, Alder Legal Group,
Bluefin Logistics.""",
    DEMO_QUESTIONS[2]: """
The main contact is now **Sam Patel** (VP Operations), who replaced Maria Chen on Sep 8 and prefers short emails.
The fix is targeted for Acme 3.3 on **Oct 20**; the workaround is splitting exports by date range.""",
}

st.set_page_config(page_title="Vector vs. Graph + Vector", layout="wide")
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
        st.markdown(answer_key)
        st.caption("The agents' answers can change from run to run: Claude words its searches "
                   "differently each time, and each search returns only the closest matches.")
