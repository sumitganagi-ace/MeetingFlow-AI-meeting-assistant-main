
from datetime import datetime, timezone

from extensions import db


class Decision(db.Model):
    __tablename__ = "decisions"

    id = db.Column(db.Integer, primary_key=True)

    meeting_id = db.Column(
        db.Integer,
        db.ForeignKey("meetings.id"),
        nullable=False,
        index=True,
    )

    description = db.Column(db.Text, nullable=False)
    evidence_excerpt = db.Column(db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    meeting = db.relationship(
        "Meeting",
        back_populates="decisions",
    )
