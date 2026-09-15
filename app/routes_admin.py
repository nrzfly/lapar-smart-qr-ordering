from functools import wraps

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
)
from werkzeug.security import generate_password_hash, check_password_hash

from .db import get_db, now_str, today_str

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

STATUS_FLOW = ["Pending", "Preparing", "Ready", "Completed"]


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)

    return wrapped


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    """RBAC: authenticates against a per-account password hash rather than
    a single shared passcode. An admin_id only has a usable account once
    it has completed /admin/register (see register() below)."""
    error = None
    if request.method == "POST":
        admin_id = request.form.get("admin_id", "").strip()
        password = request.form.get("password", "")
        db = get_db()
        row = db.execute("SELECT * FROM admin WHERE admin_id = ?", (admin_id,)).fetchone()
        db.close()
        if row is None or not row["active"]:
            error = "No active Cafe Admin account with that ID."
        elif not row["password_hash"]:
            error = "This account has not completed registration yet. Use the registration link below."
        elif not check_password_hash(row["password_hash"], password):
            error = "Incorrect admin ID or password."
        else:
            session["is_admin"] = True
            session["admin_id"] = admin_id
            return redirect(url_for("admin.orders"))
    return render_template("admin_login.html", error=error)


@admin_bp.route("/register", methods=["GET", "POST"])
def register():
    """RBAC gate: registration only succeeds for an admin_id that a Cafe
    Admin has already added via Manage Users (UC10) -- i.e. that row must
    already exist in the `admin` table with no password set yet. A FAMA
    staff member has no such row (they only exist in `staff`), so no ID
    they type here can ever pass this check -- only pre-authorized Cafe
    Admin accounts can be activated."""
    error = None
    success = None
    if request.method == "POST":
        admin_id = request.form.get("admin_id", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        db = get_db()
        row = db.execute("SELECT * FROM admin WHERE admin_id = ?", (admin_id,)).fetchone()

        if row is None or not row["active"]:
            error = "This ID is not authorized as a Cafe Admin. Ask an existing Cafe Admin to add it under Manage Users first."
        elif row["password_hash"]:
            error = "This account has already completed registration. Please log in instead."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        elif password != confirm:
            error = "Passwords do not match."
        else:
            db.execute(
                "UPDATE admin SET password_hash = ? WHERE admin_id = ?",
                (generate_password_hash(password), admin_id),
            )
            db.commit()
            success = "Registration complete. You can now log in."
        db.close()
    return render_template("admin_register.html", error=error, success=success)


@admin_bp.route("/logout")
def logout():
    session.pop("is_admin", None)
    session.pop("admin_id", None)
    return redirect(url_for("admin.login"))


@admin_bp.route("/")
@login_required
def dashboard():
    return redirect(url_for("admin.orders"))


@admin_bp.route("/menu", methods=["GET", "POST"])
@login_required
def menu():
    """UC7: Update Daily Menu."""
    db = get_db()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            db.execute(
                "INSERT INTO menu_item (name, price, category, available_date, is_available) "
                "VALUES (?, ?, ?, ?, 1)",
                (
                    request.form["name"],
                    float(request.form["price"]),
                    request.form["category"],
                    today_str(),
                ),
            )
            db.commit()
        elif action == "toggle":
            item_id = request.form["item_id"]
            db.execute(
                "UPDATE menu_item SET is_available = 1 - is_available WHERE item_id = ?",
                (item_id,),
            )
            db.commit()
        elif action == "delete":
            item_id = request.form["item_id"]
            db.execute("DELETE FROM menu_item WHERE item_id = ?", (item_id,))
            db.commit()
        db.close()
        return redirect(url_for("admin.menu"))

    items = db.execute(
        "SELECT * FROM menu_item WHERE available_date = ? ORDER BY category, name",
        (today_str(),),
    ).fetchall()
    db.close()
    return render_template("admin_menu.html", items=items, today=today_str())


@admin_bp.route("/orders", methods=["GET", "POST"])
@login_required
def orders():
    """UC8: View Orders, UC9: Update Order Status, UC6: Pay at Counter (mark Completed)."""
    db = get_db()
    if request.method == "POST":
        order_id = request.form["order_id"]
        new_status = request.form["new_status"]
        db.execute("UPDATE orders SET status = ? WHERE order_id = ?", (new_status, order_id))
        if new_status == "Ready":
            db.execute(
                "INSERT INTO notification (order_id, message, sent_time, is_read) VALUES (?, ?, ?, 0)",
                (order_id, "Your order is ready for collection and payment at the counter!", now_str()),
            )
        db.commit()
        db.close()
        return redirect(url_for("admin.orders"))

    type_filter = request.args.get("type", "All")
    status_filter = request.args.get("status", "All")

    query = "SELECT o.*, s.name AS staff_name FROM orders o JOIN staff s ON s.staff_id = o.staff_id WHERE 1=1"
    params = []
    if type_filter != "All":
        query += " AND o.order_type = ?"
        params.append(type_filter)
    if status_filter != "All":
        query += " AND o.status = ?"
        params.append(status_filter)
    query += " ORDER BY o.order_id DESC"

    order_rows = db.execute(query, params).fetchall()
    db.close()
    return render_template(
        "admin_orders.html",
        orders=order_rows,
        status_flow=STATUS_FLOW,
        type_filter=type_filter,
        status_filter=status_filter,
    )


@admin_bp.route("/users", methods=["GET", "POST"])
@login_required
def users():
    """UC10: Manage Users."""
    db = get_db()
    if request.method == "POST":
        action = request.form.get("action")
        role_table = request.form.get("role_table", "staff")
        table = "staff" if role_table == "staff" else "admin"
        id_col = "staff_id" if table == "staff" else "admin_id"

        if action == "add":
            new_id = request.form["user_id"].strip()
            name = request.form["name"].strip()
            extra = request.form.get("extra", "").strip()
            if table == "staff":
                db.execute(
                    "INSERT INTO staff (staff_id, name, department, active) VALUES (?, ?, ?, 1)",
                    (new_id, name, extra),
                )
            else:
                db.execute(
                    "INSERT INTO admin (admin_id, name, role, active) VALUES (?, ?, ?, 1)",
                    (new_id, name, extra),
                )
            db.commit()
        elif action == "toggle":
            user_id = request.form["user_id"]
            db.execute(
                f"UPDATE {table} SET active = 1 - active WHERE {id_col} = ?",
                (user_id,),
            )
            db.commit()
        db.close()
        return redirect(url_for("admin.users"))

    staff_rows = db.execute("SELECT * FROM staff ORDER BY staff_id").fetchall()
    admin_rows = db.execute("SELECT * FROM admin ORDER BY admin_id").fetchall()
    db.close()
    return render_template("admin_users.html", staff_rows=staff_rows, admin_rows=admin_rows)
