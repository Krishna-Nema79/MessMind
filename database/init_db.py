"""
=============================================================================
MESSMIND - Simple Daily Mess Meal Logging Portal
Module: database/init_db.py
Description: Standalone CLI database setup script.
=============================================================================
"""

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import text
from app import create_app
from app.config import Config
from app.extensions import db
from app.models.mess_record import MessRecord
from database.seed_data import seed_database


def init_database(seed: bool = False):
    print("=" * 60)
    print("MESSMIND DATABASE SETUP")
    print("=" * 60)

    info = Config.get_db_info()
    print(f"Database Type : {info['active_type'].upper()}")
    print(f"Target File   : {info['uri_masked']}")
    print("-" * 60)

    app = create_app()
    with app.app_context():
        try:
            # 1. Connection check
            with db.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("[OK] Database connection verified.")

            # 2. Table creation
            db.create_all()
            print("[OK] Database tables verified.")

            # 3. Existing record audit
            record_count = MessRecord.query.count()
            print(f"[INFO] Current record count: {record_count} mess records")

            # 4. Optional seeding
            if seed:
                print("\nSeeding sample records...")
                seed_database()
            elif record_count == 0:
                print("\n[INFO] Database is empty. Seeding with sample records for demonstration...")
                seed_database()

            print("-" * 60)
            print("Setup complete! You can now start the portal.")
            print("=" * 60)

        except Exception as e:
            print(f"[ERROR] Database setup error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize MessMind Database.")
    parser.add_argument("--seed", action="store_true", help="Populate database with sample records")
    args = parser.parse_args()
    init_database(seed=args.seed)
