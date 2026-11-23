
from datetime import datetime, timezone

from extensions import db


def utc_now():
    return datetime.now(timezone.utc)


class TaskComment(db.Model):
    __tablename__ = "task_comments"

    id = db.Column(db.Integer, primary_key=True)

    action_item_id = db.Column(
        db.Integer,
        db.ForeignKey("action_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    author = db.Column(
        db.String(120),
        nullable=False,
        default="You",
    )

    comment = db.Column(
        db.Text,
        nullable=False,
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    action_item = db.relationship(
        "ActionItem",
        backref=db.backref(
            "comments",
            lazy="dynamic",
            cascade="all, delete-orphan",
        ),
    )
