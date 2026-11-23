
from datetime import datetime, timezone

from extensions import db


def utc_now():
    return datetime.now(timezone.utc)


class Meeting(db.Model):
    __tablename__ = "meetings"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    title = db.Column(db.String(200), nullable=True)
    transcript = db.Column(db.Text, nullable=False)
    meeting_date = db.Column(db.DateTime(timezone=True), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), nullable=False, default="pending")
    analysis_provider = db.Column(
        db.String(30),
        nullable=False,
        default="demo",
    )

    created_at = db.Column(db.DateTime(timezone=True), default=utc_now)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    user = db.relationship(
        "User",
        back_populates="meetings",
    )

    decisions = db.relationship(
        "Decision",
        back_populates="meeting",
        cascade="all, delete-orphan",
    )

    action_items = db.relationship(
        "ActionItem",
        back_populates="meeting",
        cascade="all, delete-orphan",
    )
