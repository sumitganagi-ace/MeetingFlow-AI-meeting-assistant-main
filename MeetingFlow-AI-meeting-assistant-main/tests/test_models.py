
from models import ActionItem, Decision, Meeting
from extensions import db


def test_meeting_can_store_related_records(app):
    with app.app_context():
        meeting = Meeting(
            title="Project Planning",
            transcript="Asha will prepare the database schema.",
            summary="The team discussed database planning.",
            status="completed",
        )

        meeting.action_items.append(
            ActionItem(
                description="Prepare the database schema",
                owner="Asha",
                evidence_excerpt="Asha will prepare the database schema.",
            )
        )

        meeting.decisions.append(
            Decision(
                description="Use Flask for the backend",
                evidence_excerpt="We will use Flask for the backend.",
            )
        )

        db.session.add(meeting)
        db.session.commit()

        meeting_id = meeting.id

        db.session.remove()

        saved_meeting = db.session.get(Meeting, meeting_id)

        assert saved_meeting is not None
        assert saved_meeting.title == "Project Planning"
        assert len(saved_meeting.action_items) == 1
        assert len(saved_meeting.decisions) == 1

        task = saved_meeting.action_items[0]
        assert task.owner == "Asha"
        assert task.status == "pending"

        decision = saved_meeting.decisions[0]
        assert decision.description == "Use Flask for the backend"
