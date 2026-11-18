"""
=============================================================================
MESSMIND - Simple Daily Mess Meal Logging Portal
Module: app/routes/main_routes.py
Description: Clean, straightforward UI routes for Summary, Add Meal Record,
and Past Records with validation and pagination.
=============================================================================
"""

from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import func

from app.extensions import db
from app.models.mess_record import MessRecord

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Root route redirects to Home / Summary."""
    return redirect(url_for("main.dashboard"))


@main_bp.route("/dashboard")
@main_bp.route("/summary")
def dashboard():
    """Home / Summary view: Simple summary of meals prepared, served, and left over."""
    total_records = MessRecord.query.count()
    completed_records = MessRecord.query.filter(MessRecord.consumed_meals.isnot(None)).count()
    ongoing_records = MessRecord.query.filter(MessRecord.consumed_meals.is_(None)).count()

    if total_records > 0:
        total_prepared = db.session.query(func.sum(MessRecord.prepared_meals)).scalar() or 0
        total_consumed = db.session.query(func.sum(MessRecord.consumed_meals)).filter(MessRecord.consumed_meals.isnot(None)).scalar() or 0
        total_leftover = db.session.query(func.sum(MessRecord.wasted_meals)).filter(MessRecord.wasted_meals.isnot(None)).scalar() or 0
        completed_prep = db.session.query(func.sum(MessRecord.prepared_meals)).filter(MessRecord.consumed_meals.isnot(None)).scalar() or 0
        leftover_pct = round((total_leftover / completed_prep) * 100, 1) if completed_prep > 0 else 0.0
    else:
        total_prepared = 0
        total_consumed = 0
        total_leftover = 0
        leftover_pct = 0.0

    stats = {
        "total_prepared": total_prepared,
        "total_consumed": total_consumed,
        "total_leftover": total_leftover,
        "leftover_percentage": leftover_pct,
        "total_records": total_records,
        "completed_records": completed_records,
        "ongoing_records": ongoing_records,
    }

    # Recent 8 meal logs
    recent_records = (
        MessRecord.query.order_by(MessRecord.record_date.desc(), MessRecord.id.desc())
        .limit(8)
        .all()
    )

    return render_template("dashboard.html", stats=stats, recent_records=recent_records)


@main_bp.route("/entry", methods=["GET", "POST"])
@main_bp.route("/add", methods=["GET", "POST"])
def entry():
    """Add a Meal Record: Simple form for date, meal, menu, prepared, served, notes."""
    today_str = date.today().strftime("%Y-%m-%d")

    if request.method == "POST":
        try:
            record_date_raw = request.form.get("record_date", "").strip()
            meal_type = request.form.get("meal_type", "").strip()
            menu_name = request.form.get("menu_name", "").strip()
            prepared_meals_raw = request.form.get("prepared_meals", "").strip()
            consumed_meals_raw = request.form.get("consumed_meals", "").strip()
            notes = request.form.get("notes", "").strip()

            # 1. Required fields check
            if not record_date_raw or not meal_type or not menu_name or not prepared_meals_raw:
                flash("Please fill in all required fields: Date, Meal session, Menu, and Meals prepared.", "danger")
                return render_template(
                    "entry.html",
                    today_str=today_str,
                    prefill_date=record_date_raw or today_str,
                    prefill_meal=meal_type,
                    prefill_menu=menu_name,
                    prefill_prep=prepared_meals_raw,
                    prefill_cons=consumed_meals_raw,
                    prefill_notes=notes,
                )

            # 2. Date parsing
            try:
                record_date = datetime.strptime(record_date_raw, "%Y-%m-%d").date()
            except ValueError:
                flash("Invalid date format. Please select a valid date (YYYY-MM-DD).", "danger")
                return render_template("entry.html", today_str=today_str)

            # 3. Prepared meals validation
            try:
                prepared_meals = int(prepared_meals_raw)
            except ValueError:
                flash("Meals prepared must be a valid whole number.", "danger")
                return render_template("entry.html", today_str=today_str)

            if prepared_meals <= 0:
                flash("Meals prepared must be greater than zero.", "danger")
                return render_template("entry.html", today_str=today_str)

            if prepared_meals > 10000:
                flash("Meals prepared cannot exceed 10,000.", "danger")
                return render_template("entry.html", today_str=today_str)

            # 4. Duplicate meal session check
            existing_duplicate = MessRecord.query.filter_by(record_date=record_date, meal_type=meal_type).first()
            if existing_duplicate:
                flash(
                    f"A record for {meal_type} on {record_date} already exists. You can update it here.",
                    "warning"
                )
                return redirect(url_for("main.edit_record", record_id=existing_duplicate.id))

            # 5. Served / consumed meals validation (optional)
            if consumed_meals_raw != "":
                try:
                    consumed_meals = int(consumed_meals_raw)
                except ValueError:
                    flash("Meals served must be a valid whole number.", "danger")
                    return render_template("entry.html", today_str=today_str)

                if consumed_meals < 0:
                    flash("Meals served cannot be negative.", "danger")
                    return render_template("entry.html", today_str=today_str)

                if consumed_meals > prepared_meals:
                    flash("Meals served cannot be greater than meals prepared.", "danger")
                    return render_template("entry.html", today_str=today_str)
            else:
                consumed_meals = None

            # Day of week
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            day_name = days[record_date.weekday()]

            record = MessRecord(
                record_date=record_date,
                day_of_week=day_name,
                meal_type=meal_type,
                menu_name=menu_name,
                attendance=prepared_meals,
                prepared_meals=prepared_meals,
                consumed_meals=consumed_meals,
                notes=notes,
            )
            record.calculate_leftovers()

            db.session.add(record)
            db.session.commit()

            if record.consumed_meals is None:
                flash(f"{meal_type} meal on {record_date} was saved as Incomplete. Please enter meals served once dining finishes.", "info")
            else:
                flash(f"{meal_type} record saved successfully! {record.leftover_meals} leftover meals ({record.waste_percentage}%).", "success")

            return redirect(url_for("main.records"))

        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while saving: {str(e)}", "danger")

    return render_template("entry.html", today_str=today_str)


@main_bp.route("/records")
def records():
    """Past Records: Searchable and filterable list of saved meal records with pagination."""
    page = request.args.get("page", 1, type=int)
    per_page = 20
    start_date_str = request.args.get("start_date", "").strip()
    end_date_str = request.args.get("end_date", "").strip()
    meal_type = request.args.get("meal_type", "").strip()
    search_q = request.args.get("q", "").strip()

    query = MessRecord.query

    if start_date_str:
        try:
            start_dt = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            query = query.filter(MessRecord.record_date >= start_dt)
        except ValueError:
            pass

    if end_date_str:
        try:
            end_dt = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            query = query.filter(MessRecord.record_date <= end_dt)
        except ValueError:
            pass

    if meal_type:
        query = query.filter(MessRecord.meal_type == meal_type)

    if search_q:
        query = query.filter(MessRecord.menu_name.ilike(f"%{search_q}%"))

    pagination = query.order_by(MessRecord.record_date.desc(), MessRecord.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template(
        "records.html",
        records=pagination.items,
        pagination=pagination,
        filter_start=start_date_str,
        filter_end=end_date_str,
        filter_meal=meal_type,
        search_q=search_q,
    )


@main_bp.route("/records/edit/<int:record_id>", methods=["GET", "POST"])
def edit_record(record_id: int):
    """Edit an existing meal record."""
    record = db.session.get(MessRecord, record_id)
    if not record:
        flash(f"Record #{record_id} not found.", "danger")
        return redirect(url_for("main.records"))

    if request.method == "POST":
        try:
            record_date_raw = request.form.get("record_date", "").strip()
            meal_type = request.form.get("meal_type", "").strip()
            menu_name = request.form.get("menu_name", "").strip()
            prepared_meals_raw = request.form.get("prepared_meals", "").strip()
            consumed_meals_raw = request.form.get("consumed_meals", "").strip()
            notes = request.form.get("notes", "").strip()

            if not record_date_raw or not meal_type or not menu_name or not prepared_meals_raw:
                flash("Please fill in all required fields (Date, Meal, Menu, Prepared).", "danger")
                return render_template("edit_entry.html", record=record)

            try:
                record_date = datetime.strptime(record_date_raw, "%Y-%m-%d").date()
            except ValueError:
                flash("Invalid date format.", "danger")
                return render_template("edit_entry.html", record=record)

            try:
                prepared_meals = int(prepared_meals_raw)
            except ValueError:
                flash("Meals prepared must be a valid whole number.", "danger")
                return render_template("edit_entry.html", record=record)

            if prepared_meals <= 0:
                flash("Meals prepared must be greater than zero.", "danger")
                return render_template("edit_entry.html", record=record)

            if prepared_meals > 10000:
                flash("Meals prepared cannot exceed 10,000.", "danger")
                return render_template("edit_entry.html", record=record)

            # Consumed meals handling
            if consumed_meals_raw != "":
                try:
                    consumed_meals = int(consumed_meals_raw)
                except ValueError:
                    flash("Meals served must be a valid whole number.", "danger")
                    return render_template("edit_entry.html", record=record)

                if consumed_meals < 0:
                    flash("Meals served cannot be negative.", "danger")
                    return render_template("edit_entry.html", record=record)
                if consumed_meals > prepared_meals:
                    flash("Meals served cannot be greater than meals prepared.", "danger")
                    return render_template("edit_entry.html", record=record)
            else:
                consumed_meals = None

            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            day_name = days[record_date.weekday()]

            record.record_date = record_date
            record.day_of_week = day_name
            record.meal_type = meal_type
            record.menu_name = menu_name
            record.prepared_meals = prepared_meals
            record.consumed_meals = consumed_meals
            record.notes = notes

            record.calculate_leftovers()
            db.session.commit()

            flash(f"Record #{record.id} updated successfully!", "success")
            return redirect(url_for("main.records"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error updating record: {str(e)}", "danger")

    return render_template("edit_entry.html", record=record)


@main_bp.route("/records/delete/<int:record_id>", methods=["POST"])
def delete_record(record_id: int):
    """Deletes a meal record by ID with confirmation."""
    record = db.session.get(MessRecord, record_id)
    if record:
        try:
            db.session.delete(record)
            db.session.commit()
            flash(f"Record #{record_id} was successfully deleted.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error deleting record: {str(e)}", "danger")
    else:
        flash(f"Record #{record_id} not found.", "danger")
    return redirect(url_for("main.records"))
