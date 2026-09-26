"""Run the demo questions through both agents in the terminal (for rehearsal and testing).

    python check.py        # all demo questions
    python check.py 2      # just question 2

Stress test: give both agents a bigger budget, e.g.
    MAX_TOOL_CALLS=20 MAX_SEARCH_RESULTS=50 python check.py 2
"""

import sys

from agent import DEMO_QUESTIONS, GRAPH_AND_VECTOR, MAX_TOOL_CALLS, VECTOR_ONLY, run_agent
from tools import MAX_SEARCH_RESULTS

print(f"Settings: up to {MAX_TOOL_CALLS} tool calls, up to {MAX_SEARCH_RESULTS} results per search")
selected = [DEMO_QUESTIONS[int(n) - 1] for n in sys.argv[1:]] or DEMO_QUESTIONS
for question in selected:
    print("=" * 100 + f"\nQ: {question}")
    for title, tools in [("VECTOR-ONLY", VECTOR_ONLY), ("GRAPH + VECTOR", GRAPH_AND_VECTOR)]:
        result = run_agent(question, tools)
        print(f"\n--- {title} ({len(result['steps'])} tool calls, {result['seconds']}s)")
        for step in result["steps"]:
            print(f"  > {step['tool']}: {str(step['input'])[:140]}" + ("  [error]" if step["error"] else ""))
        print(result["answer"])
