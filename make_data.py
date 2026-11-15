import csv
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

random.seed(7)
OUT = Path(__file__).parent / "data"
ZONES = ["DHA", "Saddar", "Malir", "Orangi"]
AGENTS = [f"A{i:02d}" for i in range(1, 31)]
START = datetime(2026, 10, 1)
N_ORDERS = 1500
N_DUPES = 55
N_ORPHANS = 25
N_BAD_DEPOSITS = 20


def messy_zone(z):
    return random.choice([z, z.upper(), z.lower(), f"  {z} ", f"{z}  "])


def messy_date(d):
    return random.choice([d.strftime("%Y-%m-%d"), d.strftime("%d/%m/%Y"), d.strftime("%d.%m.%Y")])


def messy_money(x):
    return random.choice([f"PKR {x:,.0f}", f"{x:.2f}", f" {x:.0f} ", f"{x:,.2f}"])


orders, events, deposits = [], [], []
truth = {}
event_no = 0

for i in range(1, N_ORDERS + 1):
    oid = f"O{i:05d}"
    booked = START + timedelta(days=random.randint(0, 27))
    promised = booked + timedelta(days=random.randint(3, 5))
    cod = 0 if random.random() < 0.12 else round(random.uniform(600, 18000), -1)
    zone, agent = random.choice(ZONES), random.choice(AGENTS)
    orders.append({
        "order_id": oid, "booked_date": messy_date(booked),
        "promised_date": messy_date(promised), "zone": messy_zone(zone),
        "agent_id": agent, "cod_amount": f"{cod:.2f}",
        "updated_at": (booked + timedelta(hours=1)).isoformat(sep=" "),
        "_zone": zone,
    })

    r = random.random()
    if r < 0.78:
        final = "delivered"
    elif r < 0.88:
        final = "returned"
    elif r < 0.92:
        final = "cancelled"
    else:
        final = "out_for_delivery"

    chain = [("dispatched", booked + timedelta(hours=9, minutes=random.randint(0, 150)))]
    if final != "cancelled":
        chain.append(("out_for_delivery", booked + timedelta(days=1, hours=random.randint(8, 14))))
    final_dt = None
    if final in ("delivered", "returned", "cancelled"):
        final_dt = booked + timedelta(days=random.randint(2, 6), hours=random.randint(10, 19))
        chain.append((final, final_dt))

    for status, ts in chain:
        event_no += 1
        events.append({"event_id": f"E{event_no:06d}", "order_id": oid, "status": status,
                       "event_at": ts.isoformat(sep=" "), "agent_id": agent})
        if random.random() < 0.10:
            event_no += 1
            echo = ts + timedelta(seconds=random.randint(30, 150))
            events.append({"event_id": f"E{event_no:06d}", "order_id": oid, "status": status,
                           "event_at": echo.isoformat(sep=" "), "agent_id": agent})

    truth[oid] = (final, cod if final == "delivered" else 0, final_dt, agent)

for oid in random.sample(list(truth), N_DUPES):
    base = next(o for o in orders if o["order_id"] == oid)
    row = dict(base)
    row["updated_at"] = (datetime.fromisoformat(base["updated_at"]) + timedelta(days=1)).isoformat(sep=" ")
    row["zone"] = messy_zone(base["_zone"])
    orders.append(row)

for _ in range(N_ORPHANS):
    event_no += 1
    events.append({"event_id": f"E{event_no:06d}", "order_id": f"O9{random.randint(1000, 9999)}",
                   "status": "delivered",
                   "event_at": (START + timedelta(days=random.randint(0, 27))).isoformat(sep=" "),
                   "agent_id": random.choice(AGENTS)})

deposit_no = 0
short_agents = set(random.sample(AGENTS, 5))
for oid, (final, due, dts, agent) in truth.items():
    if final != "delivered" or due == 0:
        continue
    if random.random() < 0.10:
        continue
    amount = due
    if agent in short_agents and random.random() < 0.40:
        amount = round(due * random.uniform(0.50, 0.85), -1)
    deposit_no += 1
    deposits.append({"deposit_id": f"D{deposit_no:05d}", "order_id": oid, "agent_id": agent,
                     "amount": messy_money(amount),
                     "deposited_at": (dts + timedelta(hours=random.randint(2, 9))).isoformat(sep=" ")})

undelivered = [o for o, t in truth.items() if t[0] != "delivered"]
for oid in random.sample(undelivered, N_BAD_DEPOSITS):
    deposit_no += 1
    deposits.append({"deposit_id": f"D{deposit_no:05d}", "order_id": oid, "agent_id": truth[oid][3],
                     "amount": messy_money(round(random.uniform(600, 12000), -1)),
                     "deposited_at": (START + timedelta(days=random.randint(2, 30))).isoformat(sep=" ")})

for row in orders:
    row.pop("_zone", None)

random.shuffle(events)
random.shuffle(deposits)
OUT.mkdir(exist_ok=True)
for name, rows in [("orders", orders), ("events", events), ("deposits", deposits)]:
    with open(OUT / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{name}.csv: {len(rows)} rows")

if "--check" in sys.argv:
    ids = [o["order_id"] for o in orders]
    assert len(ids) - len(set(ids)) == N_DUPES, "duplicate orders missing"
    assert sum(e["order_id"] not in truth for e in events) == N_ORPHANS, "orphan events missing"
    assert any(o["zone"] != o["zone"].strip() for o in orders), "zone spacing clean"
    assert any("." in o["booked_date"] for o in orders), "dotted dates missing"
    assert any("/" in o["booked_date"] for o in orders), "slash dates missing"
    assert any("PKR" in d["amount"] for d in deposits), "money not messy"
    assert sum(truth[d["order_id"]][0] != "delivered" for d in deposits) == N_BAD_DEPOSITS, "bad deposits missing"
    paid = {d["order_id"] for d in deposits}
    assert any(t[0] == "delivered" and t[1] > 0 and o not in paid for o, t in truth.items()), "missing-cash case absent"
    print("checks passed")
