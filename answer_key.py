"""The answer key for the demo questions, and the proof behind each answer.

The answers are written out by hand. Each one comes with a query that recomputes it from
the live database and quotes the documents every fact appears in (the same documents the
vector-only agent searches), so viewers can check the answer key instead of trusting it.
"""

import neo4j

from agent import DEMO_QUESTIONS
from tools import DATABASE, get_driver

ANSWER_KEY = {
    DEMO_QUESTIONS[0]: {
        "answer": """
- **Globex Corporation** ($240K): renews Nov 18, 3 open high-severity export tickets, and its primary contact Maria Chen left on Sep 2.
- **Lumen Retail** ($180K): renews Oct 30, 2 open high-severity export tickets.
- **Fathom Legal** ($72K): evaluating cheaper alternatives before its Dec 10 renewal.
- Not at risk: **Initech** sounds angry but signed a 3-year renewal on Sep 22.
- Not at risk this year: **Cobalt Dental** is unhappy with onboarding, but doesn't renew until Jun 15, 2027.""",
        "proof": r"""
// Every contract that renews before the end of the year, with each churn signal
MATCH (c:Customer)-[:HAS_CONTRACT]->(k:Contract)
WHERE date('2026-09-29') <= k.renewal_date <= date('2026-12-31')
MATCH (kd:Document) WHERE kd.text STARTS WITH 'Contract ' + k.id + ':'
OPTIONAL MATCH (c)-[:OPENED]->(t:Ticket {status: 'open', severity: 'high'})
WITH c, k, kd, collect(t.id) AS tickets
OPTIONAL MATCH (c)-[r:PRIMARY_CONTACT]->(p:Person) WHERE r.until >= date('2026-07-01')
WITH c, k, kd, tickets, collect(p.name + ' left ' + toString(r.until)) AS contacts
OPTIONAL MATCH (n:Document {type: 'note'})-[:ABOUT]->(c) WHERE n.date >= date('2026-08-15')
WITH c, k, kd, tickets, contacts, collect(n.id + ': ' + n.text) AS notes
RETURN c.name AS customer, toString(k.renewal_date) AS renews,
       tickets AS `open high-severity tickets`, contacts AS `contact left since July`,
       notes AS `notes since Aug 15`,
       kd.id + ': ' + [l IN split(kd.text, '\n') WHERE l STARTS WITH 'Term:'][0] + ' | '
         + [l IN split(kd.text, '\n') WHERE l STARTS WITH 'Contract status:'][0] AS `contract (source)`
ORDER BY size(tickets) + size(contacts) + size(notes) DESC, k.renewal_date""",
    },
    DEMO_QUESTIONS[1]: {
        "answer": """
**$1,223,000 ARR across 11 customers:** Globex Corporation, Orchard Foods, Lumen Retail, Fieldstone Storage,
Falcon Courier, Keystone Builders, Umber Coffee Roasters, Riverbend Hospital, Jetty Marine, Alder Legal Group,
Bluefin Logistics.""",
        "total": "ARR",
        "proof": r"""
// Every customer with a ticket about the CSV export bug (ISSUE-311), and their ARR
MATCH (:Issue {id: 'ISSUE-311'})<-[:REPORTS]-(t:Ticket)<-[:OPENED]-(c:Customer)
MATCH (c)-[:HAS_CONTRACT]->(k:Contract {status: 'active'})
MATCH (kd:Document) WHERE kd.text STARTS WITH 'Contract ' + k.id + ':'
MATCH (td:Document) WHERE td.title STARTS WITH 'Support ticket ' + t.id + ':'
WITH c, kd, collect(td.id + ': ' + [l IN split(td.text, '\n')
                   WHERE l STARTS WITH 'Linked engineering issue'][0]) AS tickets
RETURN c.name AS customer, c.arr AS ARR,
       kd.id + ': ' + [l IN split(kd.text, '\n') WHERE l STARTS WITH 'Annual'][0] AS `ARR (source)`,
       tickets AS `tickets about the bug (source)`
ORDER BY ARR DESC""",
    },
    DEMO_QUESTIONS[2]: {
        "answer": """
The main contact is now **Sam Patel** (VP Operations), who replaced Maria Chen on Sep 8 and prefers short emails.
The fix is targeted for Acme 3.3 on **Oct 20**; the workaround is splitting exports by date range.""",
        "proof": r"""
// Globex's primary contacts, the new contact's preferences, and the fix date
MATCH (:Customer {name: 'Globex Corporation'})-[r:PRIMARY_CONTACT]->(p:Person)
MATCH (d:Document {type: 'contact'}) WHERE d.title = 'CRM contact record: ' + p.name
RETURN CASE WHEN r.until IS NULL THEN 'Current primary contact' ELSE 'Former primary contact' END AS fact,
       p.name + ', ' + p.title + ' (' + toString(r.since) + ' to ' + coalesce(toString(r.until), 'now') + ')'
         AS `in the graph`,
       d.id + ': ' + d.text AS source
UNION ALL
MATCH (d:Document {type: 'note'})-[:ABOUT]->(:Customer {name: 'Globex Corporation'})
WHERE d.text CONTAINS 'prefers'
RETURN 'How Sam likes to be contacted' AS fact, '(only in documents)' AS `in the graph`,
       d.id + ': ' + d.text AS source
UNION ALL
MATCH (i:Issue {id: 'ISSUE-311'}), (d:Document {type: 'release_note'})
WHERE d.text CONTAINS 'ISSUE-311' AND d.text CONTAINS 'targeted'
RETURN 'When the export fix ships' AS fact, 'fix_target ' + toString(i.fix_target) AS `in the graph`,
       d.id + ': ' + d.text AS source""",
    },
    DEMO_QUESTIONS[3]: {
        "answer": """
**4 customers, $466,000 ARR.** Each has an open ticket about a bug with no fix date, and renews before the end of the year:
- **Amberline Shipping** ($70K): renews Oct 13; waiting on the late alert emails bug (ISSUE-320).
- **Eastlake Water District** ($245K): renews Oct 20; waiting on the PDF fonts bug (ISSUE-322).
- **Lantern Nonprofit Network** ($98K): renews Nov 1; waiting on ISSUE-320.
- **Meridian Freight** ($53K): renews Dec 9; waiting on ISSUE-320.
- Trap: **Globex** and **Lumen Retail** have the loudest bug (CSV export timeouts), but its fix ships Oct 20, before both renewals.""",
        "proof": r"""
// Every customer that renews this year with an open ticket about an open bug,
// and whether their renewal comes before the bug's fix date
MATCH (c:Customer)-[:HAS_CONTRACT]->(k:Contract {status: 'active'})
WHERE date('2026-09-29') <= k.renewal_date <= date('2026-12-31')
MATCH (c)-[:OPENED]->(t:Ticket {status: 'open'})-[:REPORTS]->(i:Issue {status: 'open'})
MATCH (kd:Document) WHERE kd.text STARTS WITH 'Contract ' + k.id + ':'
MATCH (td:Document) WHERE td.title STARTS WITH 'Support ticket ' + t.id + ':'
MATCH (bd:Document) WHERE bd.title = 'Engineering issue ' + i.id
WITH c, k, i, kd, bd,
     collect(td.id + ': ' + [l IN split(td.text, '\n') WHERE l STARTS WITH 'Opened:'][0] + ' | '
             + [l IN split(td.text, '\n') WHERE l STARTS WITH 'Linked engineering issue'][0]) AS tickets
RETURN c.name AS customer,
       CASE WHEN i.fix_target IS NULL OR i.fix_target > k.renewal_date THEN 'yes'
            ELSE 'no, the fix ships first' END AS `renews before the fix`,
       toString(k.renewal_date) AS renews, coalesce(toString(i.fix_target), 'none') AS `fix date`,
       kd.id + ': ' + [l IN split(kd.text, '\n') WHERE l STARTS WITH 'Term:'][0] AS `renewal (source)`,
       tickets AS `tickets (source)`,
       bd.id + ': ' + [l IN split(bd.text, '\n') WHERE l STARTS WITH 'Status:'][0] AS `fix date (source)`
ORDER BY `renews before the fix` DESC, k.renewal_date""",
    },
}


def run_proof(question: str) -> list[dict]:
    """Recompute the answer to a demo question from the live database."""
    records, _, _ = get_driver().execute_query(
        ANSWER_KEY[question]["proof"], database_=DATABASE, routing_=neo4j.RoutingControl.READ,
    )
    return [r.data() for r in records]
