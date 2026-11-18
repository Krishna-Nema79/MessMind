"""
=============================================================================
MESSMIND - Simple Daily Mess Meal Logging Portal
Module: database/seed_data.py
Description: Populates database with sample realistic mess records for easy testing.
=============================================================================
"""

import sys
from datetime import date, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app import create_app
from app.extensions import db
from app.models.mess_record import MessRecord


SAMPLE_MENUS = [
    ("Breakfast", "Poha, Boiled Eggs / Banana, Tea"),
    ("Breakfast", "Idli, Vada, Sambar & Coconut Chutney"),
    ("Breakfast", "Aloo Paratha, Curd & Pickle"),
    ("Lunch", "Dal Makhani, Steamed Rice, Roti & Salad"),
    ("Lunch", "Rajma Masala, Jeera Rice, Chapati & Raita"),
    ("Lunch", "Paneer Butter Masala, Veg Pulao & Roti"),
    ("Snacks", "Veg Cutlet, Green Chutney & Masala Chai"),
    ("Snacks", "Samosa, Mint Chutney & Tea"),
    ("Dinner", "Mixed Vegetable Curry, Dal Tadka, Rice & Phulka"),
    ("Dinner", "Chole Masala, Bhature, Steamed Rice & Salad"),
    ("Dinner", "Paneer Kadhai, Butter Roti, Rice & Gulab Jamun"),
]


def seed_database(num_days: int = 14):
    """
    Seeds database with a couple of weeks of realistic daily mess records.
    """
    app = create_app()
    with app.app_context():
        existing_count = MessRecord.query.count()
        if existing_count > 0:
            print(f"[INFO] Database already contains {existing_count} records. Seeding skipped.")
            return

        print("=" * 60)
        print("Seeding Database with Sample Mess Records...")
        print("=" * 60)

        today = date.today()
        records_to_insert = []
        days_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        for i in range(num_days, -1, -1):
            cur_date = today - timedelta(days=i)
            day_name = days_names[cur_date.weekday()]

            for meal_type, default_menu in [
                ("Breakfast", "Idli, Vada, Sambar & Chutney"),
                ("Lunch", "Dal Makhani, Rice, Roti & Salad"),
                ("Dinner", "Mixed Veg, Dal Tadka, Rice & Roti"),
            ]:
                if i == 0 and meal_type == "Dinner":
                    prep = 450
                    cons = None
                else:
                    prep = 420 + (cur_date.day * 3) % 80
                    cons = prep - (15 + (cur_date.day * 2) % 35)

                rec = MessRecord(
                    record_date=cur_date,
                    day_of_week=day_name,
                    meal_type=meal_type,
                    menu_name=default_menu,
                    attendance=prep,
                    prepared_meals=prep,
                    consumed_meals=cons,
                    notes="Regular mess dining." if cons else "Dinner currently in progress."
                )
                rec.calculate_leftovers()
                records_to_insert.append(rec)

        db.session.bulk_save_objects(records_to_insert)
        db.session.commit()
        print(f"[OK] Successfully inserted {len(records_to_insert)} sample mess records.")
