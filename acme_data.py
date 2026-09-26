"""Synthetic customer data for Acme Analytics, a fictional B2B analytics SaaS company.

All companies and people are made up. One set of records produces both:
  - the graph: customers, contracts, contacts, support tickets, engineering issues
  - the documents: contract summaries, support tickets, call notes, release notes

Every fact the graph agent can query also appears in at least one document,
so the vector-only agent has access to the same information.
"""

import random
from datetime import date, timedelta

TODAY = date(2026, 9, 29)

ISSUES = [
    {"id": "ISSUE-311", "title": "Scheduled CSV exports time out on datasets over 1M rows",
     "status": "open", "introduced_in": "3.2", "fixed_in": None, "fix_target": "2026-10-20"},
    {"id": "ISSUE-298", "title": "Dashboards take over 10 seconds to load in large workspaces",
     "status": "fixed", "introduced_in": "3.1", "fixed_in": "3.2.1", "fix_target": None},
    {"id": "ISSUE-305", "title": "Some users get stuck in a login loop after a session timeout",
     "status": "fixed", "introduced_in": "3.2", "fixed_in": "3.2.1", "fix_target": None},
    {"id": "ISSUE-320", "title": "Threshold alert emails arrive 10-15 minutes late",
     "status": "open", "introduced_in": "3.2", "fixed_in": None, "fix_target": None},
    {"id": "ISSUE-322", "title": "Some characters render in the wrong font in PDF exports",
     "status": "open", "introduced_in": "3.2", "fixed_in": None, "fix_target": None},
]

BACKGROUND_CUSTOMERS = [
    "Bluefin Logistics", "Cedar Health Partners", "Driftwood Media", "Evergreen Grocers",
    "Foxtail Insurance", "Granite Payroll", "Harborview Hotels", "Ironclad Security",
    "Juniper Schools", "Keystone Builders", "Larkspur Biotech", "Meridian Freight",
    "Northgate Credit Union", "Oakridge Clinics", "Pinecrest Realty", "Quarry Materials",
    "Redwood Travel", "Silverline Telecom", "Tidewater Energy", "Upland Farms",
    "Vantage Robotics", "Willow Pet Care", "Yellowpine Outfitters", "Zephyr Charter",
    "Alder Legal Group", "Brightwater Utilities", "Copperleaf Fintech", "Dunmore Publishing",
    "Emberly Games", "Fieldstone Storage", "Glacier Springs", "Hollis Manufacturing",
    "Indigo Apparel", "Jetty Marine", "Kestrel Aerospace", "Lantern Nonprofit Network",
    "Mosaic Architecture", "Nimbus Weather Services", "Orchard Foods", "Paragon Staffing",
    "Quillon Books", "Riverbend Hospital", "Summit Fitness", "Trellis Home Goods",
    "Umber Coffee Roasters", "Violet Cosmetics", "Westbrook University", "Yardley Auto Group",
    "Zenith Solar", "Amberline Shipping", "Birchwood Senior Living", "Crestview Dental Group",
    "Dovetail Furniture", "Eastlake Water District", "Falcon Courier",
]

INDUSTRIES = [
    "Logistics", "Healthcare", "Media", "Retail", "Insurance", "Financial Services",
    "Hospitality", "Manufacturing", "Education", "Construction", "Energy", "Real Estate",
]
TITLES = [
    "Director of Analytics", "Head of Data", "BI Manager", "VP Finance",
    "Analytics Lead", "Director of IT", "COO", "Operations Director",
]
FIRST_NAMES = [
    "Aisha", "Ben", "Carmen", "Diego", "Erin", "Farah", "Gavin", "Hana", "Ivan", "Jada",
    "Kenji", "Leah", "Mateo", "Nadia", "Omar", "Paige", "Quinn", "Rosa", "Theo", "Uma",
    "Victor", "Wen", "Yusuf", "Zoe", "Arjun", "Bianca", "Cole", "Delia", "Emeka", "Freya",
]
LAST_NAMES = [
    "Alvarez", "Brooks", "Castillo", "Dang", "Ellis", "Fischer", "Gupta", "Hughes",
    "Ibrahim", "Jensen", "Kowalski", "Lopez", "Mensah", "Novak", "Okafor", "Petrov",
    "Quintero", "Reyes", "Sato", "Turner", "Usman", "Varga", "Wright", "Yilmaz", "Zhou",
]

POSITIVE_NOTES = [
    "Quarterly business review with {contact} ({title}), our primary contact at {customer}. "
    "{users} active users, up {growth}% since last quarter. The team is happy with the "
    "dashboards and asked about the forecasting add-on.",
    "Check-in with {contact} ({title}), our primary contact at {customer}. Adoption is steady "
    "at {users} weekly users. No open concerns; they may add seats next year.",
    "Onboarding wrap-up with {contact} ({title}), our primary contact at {customer}. All data "
    "sources are connected and {users} users are trained.",
]
NEGATIVE_PAINS = [
    "the price of additional seats",
    "missing integrations with their CRM",
    "limits on report scheduling",
]
MISC_TICKETS = [
    ("Adding new users", "How do we add users to a workspace and assign roles?"),
    ("API rate limits", "What are the API rate limits on our plan?"),
    ("Feature request: dark mode", "Several of our users asked whether a dark mode is planned."),
    ("Custom domain for shared dashboards", "Can shared dashboards use our own domain?"),
]
EXPORT_TABLES = ["orders", "transactions", "inventory", "claims", "shipments", "payroll"]


class Dataset:
    def __init__(self):
        self.customers = []
        self.contracts = []
        self.contacts = []
        self.tickets = []
        self.issues = ISSUES
        self.documents = []
        self._ticket_seq = 1000

    def customer(self, name, industry, plan, arr):
        self.customers.append({"name": name, "industry": industry, "plan": plan, "arr": arr})
        self._profile = {"industry": industry, "plan": plan, "arr": arr}

    def contract(self, customer, start, renewal, status="active", auto_renew=False):
        contract_id = f"C-{len(self.contracts) + 1:03d}"
        profile = next(c for c in self.customers if c["name"] == customer)
        self.contracts.append({
            "id": contract_id, "customer": customer, "start_date": start.isoformat(),
            "renewal_date": renewal.isoformat(), "status": status, "auto_renew": auto_renew,
        })
        months = (renewal.year - start.year) * 12 + renewal.month - start.month
        self._doc("contract", start, customer, f"Contract summary: {customer}", (
            f"Contract {contract_id}: {customer}\n"
            f"Plan: {profile['plan']} | Industry: {profile['industry']}\n"
            f"Annual recurring revenue (ARR): ${profile['arr']:,}\n"
            f"Term: {start.isoformat()} to {renewal.isoformat()} ({months} months) | "
            f"Auto-renew: {'yes' if auto_renew else 'no'}\n"
            f"Contract status: {status}"
        ))

    def contact(self, customer, name, title, since, until=None):
        self.contacts.append({
            "customer": customer, "name": name, "title": title,
            "since": since.isoformat(), "until": until.isoformat() if until else None,
        })
        self._doc("contact", until or since, customer, f"CRM contact record: {name}", (
            f"CRM contact record: {name}, {title} at {customer}. Primary contact from "
            f"{since.isoformat()} to {until.isoformat() if until else 'present'}."
        ))

    def ticket(self, customer, opened, severity, status, subject, body, issue=None, closed=None):
        self._ticket_seq += 1
        ticket_id = f"T-{self._ticket_seq}"
        self.tickets.append({
            "id": ticket_id, "customer": customer, "subject": subject, "severity": severity,
            "status": status, "opened_on": opened.isoformat(),
            "closed_on": closed.isoformat() if closed else None, "issue": issue,
        })
        closed_text = f" (closed {closed.isoformat()})" if closed else ""
        issue_text = f"\nLinked engineering issue: {issue}" if issue else ""
        self._doc("ticket", opened, customer, f"Support ticket {ticket_id}: {subject}", (
            f"Support ticket {ticket_id} from {customer}\n"
            f"Opened: {opened.isoformat()} | Severity: {severity} | Status: {status}{closed_text}"
            f"{issue_text}\nSubject: {subject}\n{body}"
        ))

    def note(self, customer, day, title, text):
        self._doc("note", day, customer, title, text)

    def _doc(self, doc_type, day, customer, title, text):
        self.documents.append({
            "id": f"D-{len(self.documents) + 1:04d}", "type": doc_type, "date": day.isoformat(),
            "customer": customer, "title": title, "text": text,
        })


def build() -> Dataset:
    rng = random.Random(42)
    ds = Dataset()
    _key_accounts(ds)
    _background_accounts(ds, rng)
    _engineering_docs(ds)
    return ds


def _key_accounts(ds: Dataset):
    # Globex: no single document says "churn risk". The signals are spread out:
    # a renewal in November (contract), open high-severity tickets (support),
    # and a champion who just left (call notes).
    ds.customer("Globex Corporation", "Manufacturing", "Enterprise", 240_000)
    ds.contract("Globex Corporation", date(2025, 11, 18), date(2026, 11, 18))
    ds.contact("Globex Corporation", "Maria Chen", "Director of Analytics",
               since=date(2024, 11, 1), until=date(2026, 9, 2))
    ds.contact("Globex Corporation", "Sam Patel", "VP Operations", since=date(2026, 9, 8))
    ds.note("Globex Corporation", date(2026, 3, 12), "QBR with Globex Corporation", (
        "Quarterly business review with Maria Chen (Director of Analytics), our primary contact "
        "at Globex Corporation. 180 active users, up 22% since last quarter. Maria presented Acme "
        "dashboards to their COO. Globex's finance team depends on nightly scheduled CSV exports."
    ))
    ds.note("Globex Corporation", date(2026, 6, 18), "Check-in with Globex Corporation", (
        "Check-in with Maria Chen at Globex Corporation. She is a strong advocate for Acme "
        "internally and wants to roll dashboards out to the supply chain team next year."
    ))
    ds.note("Globex Corporation", date(2026, 9, 8), "Primary contact change at Globex Corporation", (
        "Maria Chen has left Globex Corporation (last day September 2). Sam Patel (VP Operations) "
        "is now our primary contact. Intro call with Sam: he is new to Acme and mostly asked "
        "about the failing exports. He prefers short, direct emails."
    ))
    for opened, subject, body in [
        (date(2026, 8, 19), "Nightly finance export failing",
         "Our nightly CSV export of the general ledger table (about 3.4M rows) fails with a "
         "timeout after 30 minutes. Smaller exports still work. Is there a workaround?"),
        (date(2026, 9, 3), "Export timeout again",
         "The scheduled ledger export timed out again last night. Our finance team pulls this "
         "file every morning, so they are building the report by hand for now."),
        (date(2026, 9, 21), "Still seeing export timeouts",
         "Third week of export timeouts on the ledger table. Splitting the export by month "
         "helps but it is manual. When is the fix expected?"),
    ]:
        ds.ticket("Globex Corporation", opened, "high", "open", subject, body, issue="ISSUE-311")

    # Initech: sounds like the biggest churn risk, but already renewed for 3 years.
    ds.customer("Initech", "Software", "Business", 96_000)
    ds.contract("Initech", date(2025, 10, 31), date(2026, 10, 31), status="superseded")
    ds.contract("Initech", date(2026, 9, 22), date(2029, 9, 30), auto_renew=True)
    ds.contact("Initech", "Dana Whitfield", "Director of Product Analytics", since=date(2025, 1, 10))
    for opened, subject, body in [
        (date(2026, 8, 6), "Dashboards unusable",
         "Dashboards are taking 20+ seconds to load. This is unacceptable for a product we pay "
         "this much for."),
        (date(2026, 8, 12), "STILL slow",
         "Another week of slow dashboards. Our execs are asking why we pay for a tool nobody can "
         "use. We are seriously considering other vendors at renewal."),
        (date(2026, 8, 20), "Escalation: performance",
         "Please escalate this. If it isn't fixed soon we will not renew."),
    ]:
        ds.ticket("Initech", opened, "high", "closed", subject, body,
                  issue="ISSUE-298", closed=date(2026, 9, 10))
    ds.note("Initech", date(2026, 8, 21), "Escalation call with Initech", (
        "Tense call with Dana Whitfield (Director of Product Analytics), our primary contact at "
        "Initech. Initech is furious about dashboard performance and threatened to cancel at "
        "their October renewal. Engineering committed to a fix in 3.2.1."
    ))
    ds.note("Initech", date(2026, 9, 22), "Initech renewal signed", (
        "After the 3.2.1 performance fix, Initech signed a 3-year renewal today. The new term "
        "runs through September 30, 2029. Dana Whitfield says the dashboards are fast now."
    ))

    # Fathom Legal: says the quiet part out loud. Both agents should catch this one.
    ds.customer("Fathom Legal", "Legal Services", "Business", 72_000)
    ds.contract("Fathom Legal", date(2025, 12, 10), date(2026, 12, 10))
    ds.contact("Fathom Legal", "Priya Raman", "Operations Director", since=date(2024, 12, 1))
    ds.note("Fathom Legal", date(2026, 5, 14), "QBR with Fathom Legal", (
        "Quarterly business review with Priya Raman (Operations Director), our primary contact at "
        "Fathom Legal. 45 active users. They use Acme mainly for billable-hours reporting."
    ))
    ds.note("Fathom Legal", date(2026, 9, 15), "Budget review with Fathom Legal", (
        "Priya Raman shared that Fathom's CFO wants to cut software spend by 30%. They are "
        "evaluating two cheaper alternatives before their December renewal and asked for a discount."
    ))
    ds.ticket("Fathom Legal", date(2026, 7, 2), "low", "closed", "Exporting a dashboard to PDF",
              "How do we export a dashboard to PDF for a client meeting?", closed=date(2026, 7, 3))

    # Lumen Retail: renewal next month plus open high-severity tickets. Easy to miss.
    ds.customer("Lumen Retail", "Retail", "Enterprise", 180_000)
    ds.contract("Lumen Retail", date(2025, 10, 30), date(2026, 10, 30))
    ds.contact("Lumen Retail", "Marcus Lee", "Head of Data", since=date(2023, 6, 1))
    ds.note("Lumen Retail", date(2026, 7, 9), "Check-in with Lumen Retail", (
        "Check-in with Marcus Lee (Head of Data), our primary contact at Lumen Retail. They use "
        "Acme for store-level sales reporting across 140 stores. Renewal conversation planned "
        "for October."
    ))
    for opened, subject, body in [
        (date(2026, 9, 10), "Store sales export timing out",
         "The daily store sales export (about 2.1M rows) now fails with a timeout. We need this "
         "file for Monday reporting."),
        (date(2026, 9, 24), "Export timeouts continuing",
         "The store sales export has failed four days in a row. Please advise."),
    ]:
        ds.ticket("Lumen Retail", opened, "high", "open", subject, body, issue="ISSUE-311")

    # Cobalt Dental: unhappy, but the renewal is next June.
    ds.customer("Cobalt Dental", "Healthcare", "Business", 60_000)
    ds.contract("Cobalt Dental", date(2026, 6, 15), date(2027, 6, 15))
    ds.contact("Cobalt Dental", "Elena Park", "Practice Operations Manager", since=date(2026, 6, 15))
    ds.note("Cobalt Dental", date(2026, 9, 1), "Check-in with Cobalt Dental", (
        "Check-in with Elena Park (Practice Operations Manager), our primary contact at Cobalt "
        "Dental. She is frustrated with onboarding: setup is taking longer than promised and her "
        "team is unhappy with the training so far. She said they may reconsider Acme if things "
        "don't improve."
    ))
    ds.ticket("Cobalt Dental", date(2026, 8, 25), "medium", "open",
              "Data source connection keeps failing",
              "Our practice management system connection has failed three times this week. "
              "Onboarding is way behind schedule.")
    ds.ticket("Cobalt Dental", date(2026, 9, 9), "medium", "open", "Training materials out of date",
              "The training videos don't match the current product. Our staff are confused.")


def _background_accounts(ds: Dataset, rng: random.Random):
    names = BACKGROUND_CUSTOMERS[:]
    rng.shuffle(names)
    used_people = {c["name"] for c in ds.contacts}

    def person():
        while True:
            name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
            if name not in used_people:
                used_people.add(name)
                return name

    def day_between(start, end):
        return start + timedelta(days=rng.randint(0, (end - start).days))

    # Account groups. Each group is a different mix of signals, so the at-risk
    # accounts only stand out when you combine renewal dates, tickets and contacts.
    groups = (
        ["renews_soon_healthy"] * 10
        + ["open_export_tickets"] * 6
        + ["contact_changed"] * 5
        + ["unhappy"] * 3
        + ["export_ticket_medium"] * 3
        + ["steady"] * (len(names) - 27)
    )

    for name, group in zip(names, groups):
        plan = rng.choice(["Starter", "Business", "Business", "Enterprise"])
        arr_range = {"Starter": (12, 30), "Business": (36, 120), "Enterprise": (130, 300)}[plan]
        ds.customer(name, rng.choice(INDUSTRIES), plan, rng.randint(*arr_range) * 1000)

        if group == "renews_soon_healthy":
            renewal = day_between(date(2026, 10, 5), date(2026, 12, 20))
        else:
            renewal = day_between(date(2027, 1, 10), date(2027, 9, 20))
        ds.contract(name, renewal.replace(year=renewal.year - 1), renewal,
                    auto_renew=rng.random() < 0.4)

        contact, title = person(), rng.choice(TITLES)
        ds.contact(name, contact, title, since=day_between(date(2023, 1, 1), date(2025, 12, 1)),
                   until=date(2026, 9, 1) - timedelta(days=rng.randint(0, 40))
                   if group == "contact_changed" else None)
        ds.note(name, day_between(date(2026, 3, 1), date(2026, 7, 31)), f"Account note: {name}",
                rng.choice(POSITIVE_NOTES).format(
                    contact=contact, title=title, customer=name,
                    users=rng.randint(15, 400), growth=rng.randint(3, 30)))

        if group == "contact_changed":
            old = ds.contacts[-1]
            left = date.fromisoformat(old["until"])
            new_contact, new_title = person(), rng.choice(TITLES)
            ds.contact(name, new_contact, new_title, since=left + timedelta(days=rng.randint(3, 10)))
            ds.note(name, left + timedelta(days=rng.randint(5, 12)),
                    f"Primary contact change at {name}", (
                        f"{contact} has left {name} (last day {left:%B} {left.day}). {new_contact} "
                        f"({new_title}) is now our primary contact. Intro call went well; "
                        f"{new_contact.split()[0]} wants a refresher training for the team."))

        if group == "unhappy":
            ds.note(name, day_between(date(2026, 8, 15), date(2026, 9, 25)), f"Check-in with {name}", (
                f"Check-in with {contact} at {name}. They are frustrated with "
                f"{rng.choice(NEGATIVE_PAINS)} and said they are looking at other tools."))

        if group in ("open_export_tickets", "export_ticket_medium"):
            severity = "high" if group == "open_export_tickets" else "medium"
            for _ in range(rng.randint(1, 2) if severity == "high" else 1):
                rows = round(rng.uniform(1.2, 6.0), 1)
                ds.ticket(name, day_between(date(2026, 8, 5), date(2026, 9, 27)), severity, "open",
                          f"Scheduled {rng.choice(EXPORT_TABLES)} export timing out",
                          f"Our scheduled CSV export (about {rows}M rows) fails with a timeout "
                          "since the 3.2 upgrade. Smaller exports work.", issue="ISSUE-311")

        # Everyday noise: low-severity questions and minor bugs.
        if group == "renews_soon_healthy" and rng.random() < 0.3:
            ds.ticket(name, day_between(date(2026, 8, 10), date(2026, 9, 25)), "low", "open",
                      "Late alert emails", "Threshold alerts arrive 10-15 minutes after the metric "
                      "crosses the threshold.", issue="ISSUE-320")
        if rng.random() < 0.15:
            ds.ticket(name, day_between(date(2026, 8, 10), date(2026, 9, 25)), "low", "open",
                      "PDF fonts look wrong", "Exported PDF reports show some characters in the "
                      "wrong font.", issue="ISSUE-322")
        if rng.random() < 0.15:
            opened = day_between(date(2026, 8, 5), date(2026, 9, 1))
            ds.ticket(name, opened, "medium", "closed", "Login loop after timeout",
                      "Some of our users get stuck in a login loop after their session times out.",
                      issue="ISSUE-305", closed=date(2026, 9, 8))
        for subject, body in rng.sample(MISC_TICKETS, rng.randint(0, 2)):
            opened = day_between(date(2026, 4, 1), date(2026, 9, 20))
            ds.ticket(name, opened, "low", "closed", subject, body,
                      closed=opened + timedelta(days=rng.randint(1, 4)))


def _engineering_docs(ds: Dataset):
    for issue in ISSUES:
        ds._doc("issue", date(2026, 9, 28), None, f"Engineering issue {issue['id']}", (
            f"Engineering issue {issue['id']}: {issue['title']}\n"
            f"Status: {issue['status']} | Introduced in: {issue['introduced_in']} | "
            f"Fixed in: {issue['fixed_in'] or 'not yet'} | Fix target: {issue['fix_target'] or 'none'}"
        ))
    ds._doc("release_note", date(2026, 8, 4), None, "Release notes: Acme 3.2", (
        "Acme 3.2 ships a new scheduled export engine and redesigned alerts. Known issue "
        "ISSUE-311: scheduled CSV exports may time out on datasets over 1M rows."
    ))
    ds._doc("release_note", date(2026, 9, 8), None, "Release notes: Acme 3.2.1", (
        "Acme 3.2.1 fixes ISSUE-298 (dashboards taking over 10 seconds to load in large "
        "workspaces) and ISSUE-305 (login loop after a session timeout)."
    ))
    ds._doc("release_note", date(2026, 9, 24), None, "Engineering update: open issues", (
        "ISSUE-311 (scheduled CSV exports time out on datasets over 1M rows): fix is in QA, "
        "targeted for Acme 3.3 on 2026-10-20. Workaround: split exports by date range. "
        "ISSUE-320 (alert emails arrive 10-15 minutes late) and ISSUE-322 (wrong font for some "
        "characters in PDF exports) are open with no fix date yet."
    ))


def check_parity(ds: Dataset) -> list[str]:
    """Return every graph fact that doesn't appear in a document (should be none)."""
    docs_by_customer: dict[str, str] = {}
    for doc in ds.documents:
        docs_by_customer[doc["customer"]] = docs_by_customer.get(doc["customer"], "") + doc["text"]
    all_text = "".join(docs_by_customer.values())

    checks = []  # (description, value, text it must appear in)
    for c in ds.customers:
        text = docs_by_customer.get(c["name"], "")
        checks += [(c["name"], v, text) for v in (c["industry"], c["plan"], f"${c['arr']:,}")]
    for k in ds.contracts:
        text = docs_by_customer.get(k["customer"], "")
        values = (k["id"], k["start_date"], k["renewal_date"], f"status: {k['status']}",
                  f"Auto-renew: {'yes' if k['auto_renew'] else 'no'}")
        checks += [(k["id"], v, text) for v in values]
    for p in ds.contacts:
        text = docs_by_customer.get(p["customer"], "")
        checks += [(p["name"], v, text) for v in (p["name"], p["title"], p["since"], p["until"]) if v]
    for t in ds.tickets:
        text = docs_by_customer.get(t["customer"], "")
        values = (t["id"], t["subject"], t["severity"], t["status"], t["opened_on"],
                  t["closed_on"], t["issue"])
        checks += [(t["id"], v, text) for v in values if v]
    for i in ds.issues:
        values = (i["id"], i["title"], i["status"], i["introduced_in"], i["fixed_in"], i["fix_target"])
        checks += [(i["id"], v, all_text) for v in values if v]

    return [f"{name}: {value!r}" for name, value, text in checks if str(value) not in text]


if __name__ == "__main__":
    ds = build()
    print(f"{len(ds.customers)} customers, {len(ds.contracts)} contracts, {len(ds.contacts)} contacts, "
          f"{len(ds.tickets)} tickets, {len(ds.documents)} documents")
    missing = check_parity(ds)
    print("Every graph fact appears in a document." if not missing else f"Missing: {missing}")
