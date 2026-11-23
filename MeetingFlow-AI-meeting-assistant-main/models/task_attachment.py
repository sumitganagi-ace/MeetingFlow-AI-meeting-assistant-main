
from datetime import datetime, timezone

from extensions import db


def utc_now():
    return datetime.now(timezone.utc)


class TaskAttachment(db.Model):
    __tablename__ = "task_attachments"

    id = db.Column(db.Integer, primary_key=True)

    action_item_id = db.Column(
        db.Integer,
        db.ForeignKey("action_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    original_filename = db.Column(
        db.String(255),
        nullable=False,
    )

    stored_filename = db.Column(
        db.String(255),
        nullable=False,
        unique=True,
    )

    file_size = db.Column(
        db.Integer,
        nullable=False,
    )

    uploaded_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    action_item = db.relationship(
        "ActionItem",
        backref=db.backref(
            "attachments",
            lazy="dynamic",
            cascade="all, delete-orphan",
        ),
    )
