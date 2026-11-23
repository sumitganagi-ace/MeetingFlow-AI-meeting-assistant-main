
import pytest

from config import Config
from services.transcript_service import (
    MAX_TRANSCRIPT_LENGTH,
    analyze_transcript,
)


@pytest.fixture(autouse=True)
def use_demo_provider(monkeypatch):
    """Keep transcript unit tests deterministic and offline."""
    monkeypatch.setattr(Config, "AI_PROVIDER", "demo")


def test_extracts_meeting_title():
    result = analyze_transcript(
        "Meeting Title: Sprint Planning\nAsha will prepare the database."
    )

    assert result["meeting_title"] == "Sprint Planning"


def test_extracts_assigned_action_item():
    result = analyze_transcript(
        "Asha will prepare the database schema."
    )

    assert len(result["action_items"]) == 1

    item = result["action_items"][0]
    assert item["owner"] == "Asha"
    assert item["description"] == "prepare the database schema"
    assert item["evidence_excerpt"] == (
        "Asha will prepare the database schema."
    )


def test_extracts_deadline_phrase_without_inventing_date():
    result = analyze_transcript(
        "Rahul will create the dashboard by Friday."
    )

    item = result["action_items"][0]

    assert item["owner"] == "Rahul"
    assert item["description"] == "create the dashboard"
    assert item["deadline_text"] == "Friday"
    assert item["deadline"] is None
    assert "deadline_missing" not in item["uncertainty_flags"]


def test_flags_unclear_assignment():
    result = analyze_transcript(
        "Someone should probably handle deployment."
    )

    assert len(result["action_items"]) == 1

    item = result["action_items"][0]
    assert item["owner"] is None
    assert "assignment_unclear" in item["uncertainty_flags"]
    assert "requires_human_review" in item["uncertainty_flags"]


def test_extracts_decision_with_evidence():
    result = analyze_transcript(
        "We decided to use Flask for the backend."
    )

    assert len(result["decisions"]) == 1
    assert result["decisions"][0]["description"] == (
        "use Flask for the backend"
    )
    assert result["decisions"][0]["evidence_excerpt"] == (
        "We decided to use Flask for the backend."
    )


def test_ignores_duplicate_action_items():
    result = analyze_transcript(
        "Asha will prepare the database.\n"
        "Asha will prepare the database."
    )

    assert len(result["action_items"]) == 1


def test_rejects_empty_transcript():
    with pytest.raises(ValueError, match="transcript"):
        analyze_transcript("   ")


def test_rejects_oversized_transcript():
    transcript = "A" * (MAX_TRANSCRIPT_LENGTH + 1)

    with pytest.raises(ValueError, match="must not exceed"):
        analyze_transcript(transcript)
