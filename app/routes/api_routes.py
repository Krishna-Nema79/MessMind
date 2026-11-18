"""
=============================================================================
MESSMIND - Simple Daily Mess Meal Logging Portal
Module: app/routes/api_routes.py
Description: Lightweight endpoints for simple summary charts and CSV export.
=============================================================================
"""

import csv
import io
from flask import Blueprint, jsonify, Response, current_app
from sqlalchemy import text

from app.config import Config
from app.extensions import db
from app.models.mess_record import MessRecord

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/health")
@api_bp.route("/status")
def health_check():
    """Simple status check confirming the portal and database are operational."""
    active_type = current_app.config.get("ACTIVE_DB_TYPE", "sqlite")
    connected = False
    try:
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        connected = True
    except Exception:
        connected = False

    record_count = 0
    if connected:
        try:
            record_count = MessRecord.query.count()
        except Exception:
            pass

    return jsonify({
        "status": "healthy" if connected else "unhealthy",
        "storage": active_type,
        "total_records": record_count
    }), (200 if connected else 503)


@api_bp.route("/chart-data")
def chart_data():
    """
    Returns recent completed meal records for the simple Summary chart.
    Excludes meals that are currently in progress.
    """
    records = (
        MessRecord.query.filter(MessRecord.consumed_meals.isnot(None))
        .order_by(MessRecord.record_date.desc(), MessRecord.id.desc())
        .limit(10)
        .all()
    )
    # Reverse to chronological order
    records = list(reversed(records))

    dates = [f"{r.record_date.strftime('%d %b')} ({r.meal_type})" for r in records]
    prepared = [r.prepared_meals for r in records]
    served = [r.consumed_meals for r in records]
    leftovers = [r.wasted_meals for r in records]
    percentages = [r.waste_percentage for r in records]

    return jsonify({
        "dates": dates,
        "prepared": prepared,
        "consumed": served,
        "served": served,
        "leftover": leftovers,
        "wasted": leftovers,
        "waste_percentages": percentages,
    })


@api_bp.route("/export-csv")
def export_csv():
    """Exports all saved meal records as a downloadable CSV spreadsheet."""
    records = MessRecord.query.order_by(MessRecord.record_date.desc(), MessRecord.id.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Simple, everyday header row
    writer.writerow([
        "Record ID",
        "Date",
        "Day",
        "Meal Session",
        "Menu / Dishes",
        "Meals Prepared",
        "Meals Served",
        "Meals Left Over",
        "Leftover %",
        "Notes",
    ])

    for r in records:
        writer.writerow([
            r.id,
            r.record_date.strftime("%Y-%m-%d"),
            r.day_of_week,
            r.meal_type,
            r.menu_name,
            r.prepared_meals,
            r.consumed_meals if r.consumed_meals is not None else "Incomplete",
            r.wasted_meals if r.wasted_meals is not None else "Incomplete",
            f"{r.waste_percentage}%" if r.waste_percentage is not None else "Incomplete",
            r.notes or "",
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=mess_meal_records.csv"},
    )
