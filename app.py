import decimal
from contextlib import contextmanager
from datetime import datetime

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

from db import ensure_database_exists, get_connection

app = Flask(__name__)
app.secret_key = "change-this-in-production-use-env"

try:
    ensure_database_exists()
except Exception as exc:
    import sys

    print("Could not auto-create database (check MYSQL_* in .env):", exc, file=sys.stderr)


@contextmanager
def db_cursor():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            yield conn, cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@app.route("/")
def index():
    try:
        with db_cursor() as (_, cur):
            cur.execute("SELECT COUNT(*) AS c FROM customers")
            customers = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) AS c FROM cars")
            cars = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) AS c FROM bookings WHERE status = 'booked'")
            active = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) AS c FROM servicing WHERE status = 'pending'")
            pending_service = cur.fetchone()["c"]
    except Exception as exc:
        flash(f"Database error: {exc}", "error")
        customers = cars = active = pending_service = None
    return render_template(
        "index.html",
        customers=customers,
        cars=cars,
        active_bookings=active,
        pending_service=pending_service,
    )


@app.route("/customers", methods=["GET", "POST"])
def customers():
    if request.method == "POST":
        name = request.form.get("customer_name", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        dl = request.form.get("driving_license", "").strip()
        upi = request.form.get("upi_id", "").strip()
        if not name:
            flash("Customer name is required.", "error")
            return redirect(url_for("customers"))
        try:
            with db_cursor() as (_, cur):
                cur.execute(
                    """
                    INSERT INTO customers (customer_name, phone, address, driving_license, upi_id)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (name, phone or None, address or None, dl or None, upi or None),
                )
            flash("Customer added.", "success")
        except Exception as exc:
            flash(f"Could not add customer: {exc}", "error")
        return redirect(url_for("customers"))

    try:
        with db_cursor() as (_, cur):
            cur.execute(
                "SELECT * FROM customers ORDER BY customer_id DESC"
            )
            rows = cur.fetchall()
    except Exception as exc:
        flash(f"Database error: {exc}", "error")
        rows = []
    return render_template("customers.html", customers=rows)


@app.route("/cars", methods=["GET", "POST"])
def cars():
    if request.method == "POST":
        plate = request.form.get("car_numberplate", "").strip()
        name = request.form.get("car_name", "").strip()
        vtype = request.form.get("vehicle_type", "").strip()
        rent = request.form.get("rent_per_hour", "").strip()
        if not plate or not name or not rent:
            flash("Number plate, car name, and rent per hour are required.", "error")
            return redirect(url_for("cars"))
        try:
            rent_val = decimal.Decimal(rent)
        except decimal.InvalidOperation:
            flash("Invalid rent per hour.", "error")
            return redirect(url_for("cars"))
        try:
            with db_cursor() as (_, cur):
                cur.execute(
                    """
                    INSERT INTO cars (car_numberplate, car_name, vehicle_type, rent_per_hour)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (plate, name, vtype or None, str(rent_val)),
                )
            flash("Car added.", "success")
        except Exception as exc:
            flash(f"Could not add car: {exc}", "error")
        return redirect(url_for("cars"))

    try:
        with db_cursor() as (_, cur):
            cur.execute("SELECT * FROM cars ORDER BY car_id DESC")
            rows = cur.fetchall()
    except Exception as exc:
        flash(f"Database error: {exc}", "error")
        rows = []
    return render_template("cars.html", cars=rows)


@app.route("/bookings", methods=["GET", "POST"])
def bookings():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "create":
            cid = request.form.get("customer_id")
            carid = request.form.get("car_id")
            hours = request.form.get("hours", "").strip()
            if not cid or not carid or not hours:
                flash("Customer, car, and hours are required.", "error")
                return redirect(url_for("bookings"))
            try:
                hours_val = decimal.Decimal(hours)
            except decimal.InvalidOperation:
                flash("Invalid hours.", "error")
                return redirect(url_for("bookings"))
            try:
                with db_cursor() as (_, cur):
                    cur.execute(
                        "SELECT rent_per_hour, status FROM cars WHERE car_id = %s FOR UPDATE",
                        (carid,),
                    )
                    car = cur.fetchone()
                    if not car:
                        flash("Car not found.", "error")
                        return redirect(url_for("bookings"))
                    if car["status"] == "maintenance":
                        flash("Car is in maintenance and cannot be booked.", "error")
                        return redirect(url_for("bookings"))
                    cur.execute(
                        """
                        SELECT COUNT(*) AS c
                        FROM bookings
                        WHERE car_id = %s AND status = 'booked'
                        FOR UPDATE
                        """,
                        (carid,),
                    )
                    active_count = cur.fetchone()["c"]
                    if active_count > 0:
                        flash("Car is not available for booking.", "error")
                        return redirect(url_for("bookings"))
                    total = (decimal.Decimal(str(car["rent_per_hour"])) * hours_val).quantize(
                        decimal.Decimal("0.01")
                    )
                    cur.execute(
                        """
                        INSERT INTO bookings (customer_id, car_id, hours, total_rent, status)
                        VALUES (%s, %s, %s, %s, 'booked')
                        """,
                        (cid, carid, str(hours_val), str(total)),
                    )
                    cur.execute(
                        "UPDATE cars SET status = 'booked' WHERE car_id = %s",
                        (carid,),
                    )
                flash("Booking created.", "success")
            except Exception as exc:
                flash(f"Could not create booking: {exc}", "error")
            return redirect(url_for("bookings"))

        if action == "complete":
            bid = request.form.get("booking_id")
            if not bid:
                flash("Missing booking.", "error")
                return redirect(url_for("bookings"))
            try:
                with db_cursor() as (_, cur):
                    cur.execute(
                        "SELECT car_id, status FROM bookings WHERE booking_id = %s FOR UPDATE",
                        (bid,),
                    )
                    b = cur.fetchone()
                    if not b:
                        flash("Booking not found.", "error")
                        return redirect(url_for("bookings"))
                    if b["status"] != "booked":
                        flash("Only active bookings can be completed.", "error")
                        return redirect(url_for("bookings"))
                    cur.execute(
                        "UPDATE bookings SET status = 'completed' WHERE booking_id = %s",
                        (bid,),
                    )
                    # Fallback if DB trigger is missing: release car when booking completes.
                    # If trigger is present and sends it to maintenance, this won't override it.
                    cur.execute(
                        """
                        UPDATE cars
                        SET status = 'available'
                        WHERE car_id = %s AND status = 'booked'
                        """,
                        (b["car_id"],),
                    )
                flash("Booking marked completed (trigger may schedule servicing).", "success")
            except Exception as exc:
                flash(f"Could not complete booking: {exc}", "error")
            return redirect(url_for("bookings"))

        if action == "cancel":
            bid = request.form.get("booking_id")
            if not bid:
                flash("Missing booking.", "error")
                return redirect(url_for("bookings"))
            try:
                with db_cursor() as (_, cur):
                    cur.execute(
                        "SELECT car_id, status FROM bookings WHERE booking_id = %s FOR UPDATE",
                        (bid,),
                    )
                    b = cur.fetchone()
                    if not b:
                        flash("Booking not found.", "error")
                        return redirect(url_for("bookings"))
                    if b["status"] != "booked":
                        flash("Only active bookings can be cancelled.", "error")
                        return redirect(url_for("bookings"))
                    cur.execute(
                        "UPDATE bookings SET status = 'cancelled' WHERE booking_id = %s",
                        (bid,),
                    )
                    cur.execute(
                        "UPDATE cars SET status = 'available' WHERE car_id = %s",
                        (b["car_id"],),
                    )
                flash("Booking cancelled.", "success")
            except Exception as exc:
                flash(f"Could not cancel: {exc}", "error")
            return redirect(url_for("bookings"))

    try:
        with db_cursor() as (_, cur):
            # Self-heal stale states: if a car is marked booked but has no active
            # booked booking, mark it available so it appears in the booking list.
            cur.execute(
                """
                UPDATE cars c
                LEFT JOIN bookings b
                  ON b.car_id = c.car_id AND b.status = 'booked'
                SET c.status = 'available'
                WHERE c.status = 'booked' AND b.booking_id IS NULL
                """
            )
            cur.execute(
                """
                SELECT b.*, c.customer_name, k.car_name, k.car_numberplate
                FROM bookings b
                JOIN customers c ON c.customer_id = b.customer_id
                JOIN cars k ON k.car_id = b.car_id
                ORDER BY b.booking_id DESC
                """
            )
            rows = cur.fetchall()
            cur.execute(
                "SELECT customer_id, customer_name FROM customers ORDER BY customer_name"
            )
            cust_opts = cur.fetchall()
            cur.execute(
                """
                SELECT c.car_id, c.car_name, c.car_numberplate, c.rent_per_hour
                FROM cars c
                LEFT JOIN bookings b
                  ON b.car_id = c.car_id AND b.status = 'booked'
                WHERE c.status != 'maintenance' AND b.booking_id IS NULL
                ORDER BY c.car_name
                """
            )
            car_opts = cur.fetchall()
    except Exception as exc:
        flash(f"Database error: {exc}", "error")
        rows = cust_opts = car_opts = []
    return render_template(
        "bookings.html",
        bookings=rows,
        customers=cust_opts,
        cars=car_opts,
    )


@app.route("/payments", methods=["GET", "POST"])
def payments():
    if request.method == "POST":
        bid = request.form.get("booking_id")
        amount = request.form.get("amount_paid", "").strip()
        method = request.form.get("payment_method", "UPI")
        status = request.form.get("payment_status", "paid")
        if not bid or not amount:
            flash("Booking and amount are required.", "error")
            return redirect(url_for("payments"))
        try:
            amt = decimal.Decimal(amount).quantize(decimal.Decimal("0.01"))
        except decimal.InvalidOperation:
            flash("Invalid amount.", "error")
            return redirect(url_for("payments"))
        try:
            with db_cursor() as (_, cur):
                cur.execute(
                    "SELECT booking_id FROM bookings WHERE booking_id = %s",
                    (bid,),
                )
                if not cur.fetchone():
                    flash("Booking not found.", "error")
                    return redirect(url_for("payments"))
                cur.execute(
                    """
                    INSERT INTO payments (booking_id, amount_paid, payment_method, payment_status)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (bid, str(amt), method, status),
                )
            flash("Payment recorded.", "success")
        except Exception as exc:
            flash(f"Could not record payment: {exc}", "error")
        return redirect(url_for("payments"))

    try:
        with db_cursor() as (_, cur):
            cur.execute(
                """
                SELECT p.*, b.customer_id, b.total_rent, b.status AS booking_status,
                       c.customer_name
                FROM payments p
                JOIN bookings b ON b.booking_id = p.booking_id
                JOIN customers c ON c.customer_id = b.customer_id
                ORDER BY p.payment_id DESC
                """
            )
            rows = cur.fetchall()
            cur.execute(
                """
                SELECT booking_id, customer_id, total_rent, status
                FROM bookings
                WHERE status IN ('booked', 'completed')
                ORDER BY booking_id DESC
                """
            )
            booking_opts = cur.fetchall()
    except Exception as exc:
        flash(f"Database error: {exc}", "error")
        rows = booking_opts = []
    return render_template("payments.html", payments=rows, bookings=booking_opts)


@app.route("/servicing", methods=["GET", "POST"])
def servicing():
    if request.method == "POST":
        sid = request.form.get("service_id")
        if not sid:
            flash("Missing service.", "error")
            return redirect(url_for("servicing"))
        try:
            with db_cursor() as (_, cur):
                cur.execute(
                    "SELECT car_id FROM servicing WHERE service_id = %s",
                    (sid,),
                )
                svc = cur.fetchone()
                if not svc:
                    flash("Service record not found.", "error")
                    return redirect(url_for("servicing"))
                cur.execute(
                    "UPDATE servicing SET status = 'completed' WHERE service_id = %s",
                    (sid,),
                )
                cur.execute(
                    "UPDATE cars SET status = 'available' WHERE car_id = %s",
                    (svc["car_id"],),
                )
            flash("Service marked completed; car set to available.", "success")
        except Exception as exc:
            flash(f"Could not update service: {exc}", "error")
        return redirect(url_for("servicing"))

    try:
        with db_cursor() as (_, cur):
            cur.execute(
                """
                SELECT s.*, k.car_name, k.car_numberplate, k.status AS car_status
                FROM servicing s
                JOIN cars k ON k.car_id = s.car_id
                ORDER BY s.service_id DESC
                """
            )
            rows = cur.fetchall()
    except Exception as exc:
        flash(f"Database error: {exc}", "error")
        rows = []
    return render_template("servicing.html", servicing=rows)


@app.route("/api/health")
def api_health():
    try:
        with db_cursor() as (_, cur):
            cur.execute("SELECT DATABASE() AS db, NOW() AS server_time")
            row = cur.fetchone()
        return jsonify({"ok": True, "database": row["db"], "server_time": str(row["server_time"])})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.template_filter("dt")
def dt_filter(value):
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    return str(value)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
