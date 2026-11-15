import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent

STEPS = [
    ("01_profile_the_data.py", "Look at the files"),
    ("02_load_raw.py", "Load them into SQL Server"),
    ("03_clean_tables.py", "Clean the three tables"),
    ("04_build_order_final.py", "One row per order"),
    ("05_answer_the_questions.py", "Answer Finance's six questions"),
    ("06_quality_checks.py", "Prove the numbers"),
]


def main():
    start_at = 1
    if "--from" in sys.argv:
        start_at = int(sys.argv[sys.argv.index("--from") + 1])
    quiet = "--quiet" in sys.argv

    if not (HERE / "data" / "orders.csv").exists():
        sys.exit("No data found. Run this first:\n\n    python make_data.py\n")

    began = time.time()

    for number, (script, title) in enumerate(STEPS, start=1):
        if number < start_at:
            print(f"  ..  skipping step {number}: {title}")
            continue

        print()
        print("#" * 72)
        print(f"#  STEP {number} - {title}   ({script})")
        print("#" * 72, flush=True)

        result = subprocess.run([sys.executable, str(HERE / script)],
                                cwd=HERE, capture_output=quiet, text=True)

        if quiet and result.stdout:
            for line in result.stdout.strip().splitlines()[-6:]:
                print(line)

        if result.returncode != 0:
            if quiet and result.stdout:
                print(result.stdout[-2000:])
            if quiet and result.stderr:
                print(result.stderr[-2000:])
            sys.exit(f"\nSTOPPED: {script} failed. Fix that before continuing.")

    print()
    print("#" * 72)
    print(f"#  ALL STEPS FINISHED in {time.time() - began:.0f} seconds.")
    print("#  Your answers are in results/. Now write findings.md.")
    print("#" * 72)


if __name__ == "__main__":
    main()
