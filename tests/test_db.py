"""
=============================================================================
Unit & Integration Tests: Database Model & Leftover Calculations
File: tests/test_db.py
=============================================================================
"""

from datetime import date
import pytest
from app import create_app
from app.config import Config, mask_connection_uri
from app.extensions import db
from app.models.mess_record import MessRecord


class TestDBConfig:
    """Isolated In-Memory configuration for database unit tests."""
    SECRET_KEY = "test-secret"
    FLASK_ENV = "development"
    DEBUG = False
    TESTING = True
    IS_PRODUCTION = False
    ALLOW_SQLITE_FALLBACK = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    ACTIVE_DB_TYPE = "sqlite"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}


@pytest.fixture
def app():
    app = create_app(TestDBConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_mess_record_creation_and_leftover_calc(app):
    """Test adding a mess record and verifying leftover arithmetic."""
    record = MessRecord(
        record_date=date(2026, 11, 14),
        day_of_week="Saturday",
        meal_type="Lunch",
        menu_name="Paneer Butter Masala",
        prepared_meals=450,
        consumed_meals=410,
        notes="High turnout"
    )
    record.calculate_leftovers()

    assert record.leftover_meals == 40
    assert record.waste_percentage == round((40 / 450) * 100, 2)
    assert record.is_ongoing is False

    db.session.add(record)
    db.session.commit()

    queried = db.session.get(MessRecord, record.id)
    assert queried is not None
    assert queried.menu_name == "Paneer Butter Masala"
    assert queried.leftover_meals == 40


def test_ongoing_meal_record(app):
    """Test that a meal in progress does not calculate premature leftovers."""
    record = MessRecord(
        record_date=date(2026, 11, 15),
        day_of_week="Sunday",
        meal_type="Dinner",
        menu_name="Veg Pulao & Raita",
        prepared_meals=300,
        consumed_meals=None,  # Meal still in progress
    )
    record.calculate_leftovers()

    assert record.is_ongoing is True
    assert record.leftover_meals is None
    assert record.waste_percentage is None

    db.session.add(record)
    db.session.commit()

    # Now simulate meal completing
    record.consumed_meals = 280
    record.calculate_leftovers()
    db.session.commit()

    updated = db.session.get(MessRecord, record.id)
    assert updated.is_ongoing is False
    assert updated.leftover_meals == 20
    assert updated.waste_percentage == round((20 / 300) * 100, 2)


def test_zero_leftovers_when_all_served(app):
    """Test when all prepared meals are served (0 leftover)."""
    record = MessRecord(
        record_date=date(2026, 11, 16),
        day_of_week="Monday",
        meal_type="Breakfast",
        menu_name="Idli & Sambar",
        prepared_meals=200,
        consumed_meals=200,
    )
    record.calculate_leftovers()
    assert record.leftover_meals == 0
    assert record.waste_percentage == 0.0


def test_all_leftover_when_zero_served(app):
    """Test when zero meals are served (100% leftover)."""
    record = MessRecord(
        record_date=date(2026, 11, 17),
        day_of_week="Tuesday",
        meal_type="Lunch",
        menu_name="Rajma Chawal",
        prepared_meals=250,
        consumed_meals=0,
    )
    record.calculate_leftovers()
    assert record.leftover_meals == 250
    assert record.waste_percentage == 100.0


def test_uri_masking_utility():
    """Verify password masking utility hides sensitive credentials."""
    raw_uri = "mysql+pymysql://admin:MySecurePass123@db.example.com:3306/mess_db"
    masked = mask_connection_uri(raw_uri)
    assert "MySecurePass123" not in masked
    assert "admin:****@db.example.com" in masked
