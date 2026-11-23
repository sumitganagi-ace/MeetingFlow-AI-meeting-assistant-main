
from datetime import datetime, timezone

from extensions import db


def utc_now():
    return datetime.now(timezone.utc)


class ActionItem(db.Model):
    __tablename__ = "action_items"

    id = db.Column(db.Integer, primary_key=True)

    meeting_id = db.Column(
        db.Integer,
        db.ForeignKey("meetings.id"),
        nullable=False,
        index=True,
    )

    description = db.Column(db.Text, nullable=False)
    owner = db.Column(db.String(120), nullable=True)
    deadline = db.Column(db.DateTime(timezone=True), nullable=True)

    status = db.Column(
        db.String(30),
        nullable=False,
        default="pending",
    )

    priority = db.Column(db.String(20), nullable=True)
    evidence_excerpt = db.Column(db.Text, nullable=True)

    uncertainty_flags = db.Column(
        db.JSON,
        nullable=False,
        default=list,
    )

    original_ai_data = db.Column(db.JSON, nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), default=utc_now)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    meeting = db.relationship(
        "Meeting",
        back_populates="action_items",
    )
