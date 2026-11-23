
from flask import Flask, jsonify
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import inspect, text

from config import Config
from extensions import db

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access MeetingFlow."
login_manager.login_message_category = "error"

csrf = CSRFProtect()


def create_app(test_config=None):
    app = Flask(__name__)

    app.config.from_object(Config)

    if test_config is not None:
        app.config.update(test_config)

    # Initialize database, authentication and CSRF protection.
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Import models so SQLAlchemy can register every table.
    from models import (
        User,
        Meeting,
        ActionItem,
        Decision,
        TaskActivity,
        TaskComment,
        TaskAttachment,
    )

    # Register the meeting pages.
    from routes.meeting_routes import meeting_bp
    app.register_blueprint(meeting_bp)

    # Register authentication pages.
    from routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp)

    # Create missing database tables and safely migrate meetings.
    with app.app_context():
        db.create_all()

        inspector = inspect(db.engine)

        if "meetings" in inspector.get_table_names():
            meeting_columns = {
                column["name"]
                for column in inspector.get_columns("meetings")
            }

            if "user_id" not in meeting_columns:
                with db.engine.begin() as connection:
                    connection.execute(
                        text(
                            "ALTER TABLE meetings "
                            "ADD COLUMN user_id INTEGER "
                            "REFERENCES users(id)"
                        )
                    )

                print("Database migration: added meetings.user_id")

    @app.route("/health")
    def health():
        return jsonify({"status": "healthy"})

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({"error": "An unexpected server error occurred"}), 500

    return app


@login_manager.user_loader
def load_user(user_id):
    from models import User

    try:
        return db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        return None


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
