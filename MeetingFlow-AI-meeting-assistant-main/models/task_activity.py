
from datetime import datetime, timezone

from extensions import db


def utc_now():
    return datetime.now(timezone.utc)


class TaskActivity(db.Model):
    __tablename__ = "task_activities"

    id = db.Column(db.Integer, primary_key=True)

    action_item_id = db.Column(
        db.Integer,
        db.ForeignKey("action_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    field_name = db.Column(db.String(50), nullable=False)
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)

    changed_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    action_item = db.relationship(
        "ActionItem",
        backref=db.backref(
            "activity_history",
            lazy="dynamic",
            cascade="all, delete-orphan",
        ),
    )
