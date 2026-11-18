"""
=============================================================================
MESSMIND - Simple Daily Mess Meal Logging Portal
Module: app/models/mess_record.py
Description: SQLAlchemy ORM model for daily mess meal records.
=============================================================================
"""

from datetime import datetime, timezone
from app.extensions import db


def get_utc_now():
    """Returns current UTC timestamp in a Python 3.14+ compliant manner."""
    return datetime.now(timezone.utc)


class MessRecord(db.Model):
    """Daily record of prepared meals, served meals, and leftover portions."""
    __tablename__ = "mess_records"
    __table_args__ = (
        db.CheckConstraint("prepared_meals >= 0", name="chk_prepared_positive"),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    record_date = db.Column(db.Date, nullable=False, index=True)
    day_of_week = db.Column(db.String(20), nullable=False)
    meal_type = db.Column(db.String(20), nullable=False, index=True)  # Breakfast, Lunch, Snacks, Dinner
    menu_name = db.Column(db.String(200), nullable=False)
    attendance = db.Column(db.Integer, nullable=True, default=0)
    prepared_meals = db.Column(db.Integer, nullable=False)
    consumed_meals = db.Column(db.Integer, nullable=True)  # Null if meal is ongoing
    wasted_meals = db.Column(db.Integer, nullable=True)    # Leftover meals = prepared - consumed
    waste_percentage = db.Column(db.Float, nullable=True)   # Leftover percentage
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=get_utc_now)
    updated_at = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now)

    def calculate_leftovers(self):
        """Calculates leftover meals from prepared and served counts."""
        if self.consumed_meals is not None and self.prepared_meals is not None:
            self.wasted_meals = max(0, self.prepared_meals - self.consumed_meals)
            if self.prepared_meals > 0:
                pct = (self.wasted_meals / self.prepared_meals) * 100
                self.waste_percentage = round(min(100.0, max(0.0, pct)), 2)
            else:
                self.waste_percentage = 0.0
        else:
            self.wasted_meals = None
            self.waste_percentage = None

    # Alias for backwards compatibility with any remaining references
    calculate_waste = calculate_leftovers

    @property
    def leftover_meals(self):
        """Convenience property for leftover meals."""
        return self.wasted_meals

    @property
    def is_ongoing(self):
        """Returns True if the meal record is still in progress (served count not yet entered)."""
        return self.consumed_meals is None

    def to_dict(self):
        return {
            "id": self.id,
            "record_date": self.record_date.isoformat() if self.record_date else None,
            "day_of_week": self.day_of_week,
            "meal_type": self.meal_type,
            "menu_name": self.menu_name,
            "prepared_meals": self.prepared_meals,
            "consumed_meals": self.consumed_meals,
            "leftover_meals": self.wasted_meals,
            "leftover_percentage": self.waste_percentage,
            "is_ongoing": self.is_ongoing,
            "notes": self.notes
        }
