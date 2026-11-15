import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent


def _load_dotenv():
    env_file = PROJECT_DIR / ".env"
    if not env_file.exists():
        return False
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip().strip("\"'"))
    return True


DOTENV_LOADED = _load_dotenv()

DATA_FILES = ["orders.csv", "events.csv", "deposits.csv"]


def _find_data_dir():
    candidates = []
    if os.environ.get("DATA_DIR"):
        candidates.append(Path(os.environ["DATA_DIR"]))
    candidates += [PROJECT_DIR / "data", PROJECT_DIR.parent / "data"]
    for folder in candidates:
        if (folder / "orders.csv").exists():
            return folder
    return PROJECT_DIR / "data"


DATA_DIR = _find_data_dir()
RESULTS_DIR = PROJECT_DIR / "results"

SQL_SERVER = os.environ.get("SQL_SERVER", "localhost")
SQL_DATABASE = os.environ.get("SQL_DATABASE", "quickcart_class")
SQL_DRIVER = os.environ.get("SQL_DRIVER", "ODBC Driver 18 for SQL Server")
SQL_USER = os.environ.get("SQL_USER", "")
SQL_PASSWORD = os.environ.get("SQL_PASSWORD", "")


def connection_string(database=None):
    database = database or SQL_DATABASE
    if SQL_USER:
        login = f"UID={SQL_USER};PWD={SQL_PASSWORD};"
    else:
        login = "Trusted_Connection=yes;"
    return (
        f"DRIVER={{{SQL_DRIVER}}};"
        f"SERVER={SQL_SERVER};"
        f"DATABASE={database};"
        f"{login}"
        "TrustServerCertificate=yes;"
    )


CONNECTION_STRING = connection_string()
