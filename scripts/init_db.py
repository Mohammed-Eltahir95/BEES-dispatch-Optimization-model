"""Creates the SQLite database and tables from database/schema.sql."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bess_opt.db.connection import init_db_from_schema
from bess_opt.utils.helpers import load_yaml

if __name__ == "__main__":
    config = load_yaml("config/config.yaml")
    init_db_from_schema(config["database"]["path"])
    print(f"Database initialized at {config['database']['path']}")
