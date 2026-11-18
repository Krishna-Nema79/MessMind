"""
=============================================================================
Unit & Integration Tests: MessMind Routes, Validations & Simple Workflows
File: tests/test_routes.py
=============================================================================
"""

from datetime import date
import pytest
from app import create_app
from app.extensions import db
from app.models.mess_record import MessRecord


class TestRoutesConfig:
    """Isolated In-Memory configuration for route testing."""
    SECRET_KEY = "test-routes-secret"
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
def client():
    app = create_app(TestRoutesConfig)
    app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
    })
    with app.app_context():
        # Seed an initial record
        rec = MessRecord(
            record_date=date(2026, 11, 14),
            day_of_week="Saturday",
            meal_type="Lunch",
            menu_name="Paneer Butter Masala & Naan",
            prepared_meals=450,
            consumed_meals=410,
            wasted_meals=40,
            waste_percentage=8.89,
            notes="Initial test record",
        )
        db.session.add(rec)
        db.session.commit()

        with app.test_client() as test_client:
            yield test_client
            db.session.remove()
            db.drop_all()


def test_root_redirects_to_dashboard(client):
    """Verify root / redirects to dashboard/summary."""
    response = client.get("/")
    assert response.status_code == 302
    assert "/dashboard" in response.headers["Location"] or "/summary" in response.headers["Location"]


def test_dashboard_page(client):
    """Verify Summary page loads with plain everyday labels."""
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert b"Meals prepared" in response.data
    assert b"Meals served" in response.data
    assert b"Meals left over" in response.data
    assert b"consumptionChart" in response.data


def test_entry_page_get_and_post(client):
    """Verify adding a new meal record."""
    # GET
    res_get = client.get("/entry")
    assert res_get.status_code == 200
    assert b"Record a Meal" in res_get.data

    # POST valid
    post_data = {
        "record_date": "2026-11-15",
        "meal_type": "Dinner",
        "menu_name": "Dal Tadka, Steamed Rice & Roti",
        "prepared_meals": "350",
        "consumed_meals": "330",
        "notes": "Sunday dinner",
    }
    res_post = client.post("/entry", data=post_data, follow_redirects=True)
    assert res_post.status_code == 200
    assert b"saved successfully" in res_post.data

    rec = MessRecord.query.filter_by(record_date=date(2026, 11, 15), meal_type="Dinner").first()
    assert rec is not None
    assert rec.prepared_meals == 350
    assert rec.consumed_meals == 330
    assert rec.leftover_meals == 20


def test_entry_ongoing_meal_without_served_count(client):
    """Verify saving a meal in progress without entering meals served."""
    post_data = {
        "record_date": "2026-11-16",
        "meal_type": "Breakfast",
        "menu_name": "Poha & Tea",
        "prepared_meals": "200",
        "consumed_meals": "",  # Blank: ongoing meal
        "notes": "Meal in progress",
    }
    res_post = client.post("/entry", data=post_data, follow_redirects=True)
    assert res_post.status_code == 200
    assert b"saved as Incomplete" in res_post.data or b"Past Meal Records" in res_post.data

    rec = MessRecord.query.filter_by(record_date=date(2026, 11, 16), meal_type="Breakfast").first()
    assert rec is not None
    assert rec.is_ongoing is True
    assert rec.leftover_meals is None


def test_entry_validation_missing_required_fields(client):
    """Verify validation when required fields are missing."""
    res = client.post("/entry", data={
        "record_date": "",
        "meal_type": "",
        "menu_name": "",
        "prepared_meals": "",
    })
    assert res.status_code == 200
    assert b"Please fill in all required fields" in res.data


def test_entry_validation_served_exceeds_prepared(client):
    """Verify that served meals cannot exceed prepared meals."""
    res = client.post("/entry", data={
        "record_date": "2026-11-18",
        "meal_type": "Lunch",
        "menu_name": "Veg Thali",
        "prepared_meals": "300",
        "consumed_meals": "350",  # Exceeds prepared
    })
    assert res.status_code == 200
    assert b"cannot be greater than meals prepared" in res.data


def test_entry_validation_negative_served_count(client):
    """Verify that negative served count is rejected."""
    res = client.post("/entry", data={
        "record_date": "2026-11-18",
        "meal_type": "Lunch",
        "menu_name": "Veg Thali",
        "prepared_meals": "300",
        "consumed_meals": "-10",
    })
    assert res.status_code == 200
    assert b"cannot be negative" in res.data


def test_entry_duplicate_redirects_to_edit(client):
    """Verify that entering duplicate meal session redirects to edit page."""
    # Baseline record exists for 2026-11-14 Lunch
    res = client.post("/entry", data={
        "record_date": "2026-11-14",
        "meal_type": "Lunch",
        "menu_name": "Paneer Butter Masala",
        "prepared_meals": "450",
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"already exists" in res.data
    assert b"Edit Meal Record" in res.data


def test_records_page_and_filtering(client):
    """Verify Past Records table and filter options."""
    res = client.get("/records")
    assert res.status_code == 200
    assert b"Past Meal Records" in res.data
    assert b"Paneer Butter Masala" in res.data

    # Filter by Lunch
    res_lunch = client.get("/records?meal_type=Lunch")
    assert res_lunch.status_code == 200
    assert b"Paneer Butter Masala" in res_lunch.data

    # Filter by Dinner (no dinner exists initially)
    res_dinner = client.get("/records?meal_type=Dinner")
    assert res_dinner.status_code == 200
    assert b"No records found" in res_dinner.data


def test_edit_record_get_and_post(client):
    """Verify editing an existing record."""
    rec = MessRecord.query.first()

    # GET
    res_get = client.get(f"/records/edit/{rec.id}")
    assert res_get.status_code == 200
    assert b"Edit Meal Record" in res_get.data

    # POST update
    res_post = client.post(f"/records/edit/{rec.id}", data={
        "record_date": "2026-11-14",
        "meal_type": "Lunch",
        "menu_name": "Paneer Butter Masala & Naan Updated",
        "prepared_meals": "460",
        "consumed_meals": "420",
        "notes": "Updated count",
    }, follow_redirects=True)
    assert res_post.status_code == 200
    assert b"updated successfully" in res_post.data

    updated = db.session.get(MessRecord, rec.id)
    assert updated.prepared_meals == 460
    assert updated.consumed_meals == 420
    assert updated.leftover_meals == 40


def test_delete_record_post(client):
    """Verify deleting a record."""
    rec = MessRecord.query.first()
    rec_id = rec.id

    res_del = client.post(f"/records/delete/{rec_id}", follow_redirects=True)
    assert res_del.status_code == 200
    assert b"successfully deleted" in res_del.data

    deleted = db.session.get(MessRecord, rec_id)
    assert deleted is None


def test_api_chart_data(client):
    """Verify /api/chart-data endpoint returns clean data for summary graph."""
    res = client.get("/api/chart-data")
    assert res.status_code == 200
    data = res.get_json()
    assert "dates" in data
    assert "prepared" in data
    assert "consumed" in data


def test_api_export_csv(client):
    """Verify CSV export produces clean spreadsheet."""
    res = client.get("/api/export-csv")
    assert res.status_code == 200
    assert res.mimetype == "text/csv"
    assert b"Meals Prepared" in res.data
    assert b"Meals Served" in res.data
    assert b"Meals Left Over" in res.data


def test_api_health(client):
    """Verify health endpoint."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert data["total_records"] >= 1


def test_csrf_token_enforcement():
    """Verify CSRF middleware blocks requests without a valid CSRF token when enabled."""
    class CSRFActiveConfig(TestRoutesConfig):
        TESTING = True
        WTF_CSRF_ENABLED = True

    csrf_app = create_app(CSRFActiveConfig)
    csrf_app.config["TESTING"] = True
    csrf_app.config["WTF_CSRF_ENABLED"] = True

    with csrf_app.test_client() as csrf_client:
        # POST without token is blocked with 403 Forbidden
        blocked_res = csrf_client.post("/entry", data={
            "record_date": "2026-11-28",
            "meal_type": "Lunch",
            "menu_name": "Veg Pulav",
            "prepared_meals": "320",
        })
        assert blocked_res.status_code == 403

        # POST with valid token succeeds
        with csrf_client.session_transaction() as sess:
            sess["_csrf_token"] = "valid-token-123"

        allowed_res = csrf_client.post("/entry", data={
            "csrf_token": "valid-token-123",
            "record_date": "2026-11-28",
            "meal_type": "Lunch",
            "menu_name": "Veg Pulav",
            "prepared_meals": "320",
            "consumed_meals": "300",
        }, follow_redirects=True)
        assert allowed_res.status_code == 200
        assert b"saved successfully" in allowed_res.data


def test_custom_404_error_page(client):
    """Verify custom 404 page renders cleanly without tracebacks."""
    res = client.get("/non-existent-endpoint-404")
    assert res.status_code == 404
    assert b"Page Not Found" in res.data
    assert b"Traceback" not in res.data


def test_empty_state_handling():
    """Verify that empty database renders clean empty states without crashes."""
    class EmptyConfig(TestRoutesConfig):
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

    empty_app = create_app(EmptyConfig)
    with empty_app.test_client() as empty_client:
        dash_res = empty_client.get("/dashboard")
        assert dash_res.status_code == 200
        assert b"No meal records yet" in dash_res.data

        rec_res = empty_client.get("/records")
        assert rec_res.status_code == 200
        assert b"No records found" in rec_res.data
