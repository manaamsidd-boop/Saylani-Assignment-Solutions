from config import PROJECT_DIR, RESULTS_DIR
from db import banner, done, fetch_df, step

QUERY_DIR = PROJECT_DIR / "queries"

QUESTIONS = [
    ("q1", "How many orders ended in each status, per zone?"),
    ("q2", "What share of deliveries beat the promised date, per zone?"),
    ("q3", "Top 5 agents by total COD shortfall"),
    ("q4", "Which deposits sit against orders that were never delivered?"),
    ("q5", "How much cash is due on delivered orders with no deposit at all?"),
    ("q6", "Headline: due versus collected on delivered orders"),
]

RESULTS_DIR.mkdir(exist_ok=True)
banner("STEP 5 - ANSWERING THE QUESTIONS")

for number, (name, question) in enumerate(QUESTIONS, start=1):
    step(number, question)
    sql = (QUERY_DIR / f"{name}.sql").read_text(encoding="utf-8")
    df = fetch_df(sql)
    df.to_csv(RESULTS_DIR / f"{name}.csv", index=False, encoding="utf-8-sig")
    print()
    print(df.head(12).to_string(index=False))
    if len(df) > 12:
        print(f"  ... {len(df) - 12} more rows in results/{name}.csv")

done("Answers written to results/.\n"
     "     Next:  python 06_quality_checks.py")
