
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_user, logout_user, current_user
from sqlalchemy import func

from extensions import db
from models import User, Meeting

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("meetings.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not email or not password:
            flash("Please fill in all required fields.", "error")
            return redirect(url_for("auth.register"))

        if len(username) > 80:
            flash("Username must not exceed 80 characters.", "error")
            return redirect(url_for("auth.register"))

        if len(email) > 255 or "@" not in email:
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("auth.register"))

        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
            return redirect(url_for("auth.register"))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("auth.register"))

        existing_user = User.query.filter(
            func.lower(User.email) == email
        ).first()

        if existing_user:
            flash("An account with this email already exists.", "error")
            return redirect(url_for("auth.register"))

        try:
            # Check whether this is the first registered account.
            is_first_user = User.query.count() == 0

            user = User(username=username, email=email)
            user.set_password(password)

            db.session.add(user)

            # Generate the user's ID before assigning existing meetings.
            db.session.flush()

            # Give the first account ownership of existing unassigned meetings.
            if is_first_user:
                Meeting.query.filter(
                    Meeting.user_id.is_(None)
                ).update(
                    {Meeting.user_id: user.id},
                    synchronize_session=False,
                )

            db.session.commit()

            login_user(user)

            flash(
                "Account created successfully. Welcome to MeetingFlow!",
                "success",
            )

            return redirect(url_for("meetings.index"))

        except Exception:
            db.session.rollback()
            flash(
                "Could not create your account. Please try again.",
                "error",
            )

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("meetings.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter(
            func.lower(User.email) == email
        ).first()

        if user and user.check_password(password):
            login_user(user)

            flash("Logged in successfully. Welcome back!", "success")
            return redirect(url_for("meetings.index"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("You have been logged out.", "success")

    return redirect(url_for("auth.login"))
