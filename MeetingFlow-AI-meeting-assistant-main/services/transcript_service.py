
import re

from config import Config
from services.gemini_service import (
    GeminiServiceError,
    analyze_with_gemini,
)

MAX_TRANSCRIPT_LENGTH = 50_000

UNCERTAIN_TASK_PHRASES = (
    "someone should",
    "somebody should",
    "we should",
    "we need to",
    "should probably",
    "needs to be handled",
    "someone needs to",
    "somebody needs to",
)

DECISION_PHRASES = (
    "we decided to ",
    "the team decided to ",
    "decision: ",
)


def _extract_meeting_title(lines: list[str]) -> str:
    for line in lines:
        if line.lower().startswith("meeting title:"):
            title = line.split(":", 1)[1].strip()
            if title:
                return title[:200]

    return "Meeting Analysis"


def _extract_deadline(task_text: str) -> tuple[str | None, str]:
    patterns = (
        r"\s+by\s+(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b",
        r"\s+by\s+(today|tomorrow|tonight|next week)\b",
        r"\s+by\s+(the end of the day|end of day)\b",
    )

    for pattern in patterns:
        match = re.search(pattern, task_text, flags=re.IGNORECASE)

        if match:
            deadline_phrase = match.group(1)
            cleaned_task = (
                task_text[:match.start()] + task_text[match.end():]
            ).strip(" ,.")

            return deadline_phrase, cleaned_task

    return None, task_text.strip(" ,.")


def _extract_action_items(lines: list[str]) -> list[dict]:
    action_items = []
    seen = set()

    for line in lines:
        normalized = line.strip()
        lower_line = normalized.lower()

        if any(phrase in lower_line for phrase in DECISION_PHRASES):
            continue

        uncertain_phrase = next(
            (
                phrase
                for phrase in UNCERTAIN_TASK_PHRASES
                if phrase in lower_line
            ),
            None,
        )

        if uncertain_phrase:
            description = normalized.rstrip(".")
            key = description.lower()

            if key not in seen:
                seen.add(key)

                action_items.append({
                    "description": description,
                    "owner": None,
                    "deadline": None,
                    "deadline_text": None,
                    "status": "pending",
                    "priority": None,
                    "evidence_excerpt": normalized,
                    "uncertainty_flags": [
                        "assignment_unclear",
                        "requires_human_review",
                    ],
                })

            continue

        match = re.match(
            r"^([A-Z][A-Za-z'-]*(?:\s+[A-Z][A-Za-z'-]*){0,2})"
            r"\s+will\s+(.+)$",
            normalized,
        )

        if not match:
            continue

        owner = match.group(1).strip()
        task_text = match.group(2).strip()

        deadline_phrase, description = _extract_deadline(task_text)

        if not description:
            continue

        key = (owner.lower(), description.lower())

        if key in seen:
            continue

        seen.add(key)

        flags = []

        if deadline_phrase is None:
            flags.append("deadline_missing")

        action_items.append({
            "description": description.rstrip("."),
            "owner": owner,
            "deadline": None,
            "deadline_text": deadline_phrase,
            "status": "pending",
            "priority": None,
            "evidence_excerpt": normalized,
            "uncertainty_flags": flags,
        })

    return action_items


def _extract_decisions(lines: list[str]) -> list[dict]:
    decisions = []
    seen = set()

    for line in lines:
        lower_line = line.lower()

        for phrase in DECISION_PHRASES:
            position = lower_line.find(phrase)

            if position == -1:
                continue

            description = line[position + len(phrase):].strip(" .,:")
            if not description:
                break

            key = description.lower()

            if key not in seen:
                seen.add(key)

                decisions.append({
                    "description": description,
                    "evidence_excerpt": line,
                })

            break

    return decisions


def _analyze_with_demo(transcript: str) -> dict:
    lines = [
        line.strip()
        for line in transcript.splitlines()
        if line.strip()
    ]

    title = _extract_meeting_title(lines)
    action_items = _extract_action_items(lines)
    decisions = _extract_decisions(lines)

    return {
        "meeting_title": title,
        "summary": (
            f"Rule-based analysis of {len(lines)} non-empty transcript lines. "
            f"Found {len(action_items)} possible action items and "
            f"{len(decisions)} possible decisions. "
            "Review all extracted information before relying on it."
        ),
        "discussion_points": lines[:8],
        "action_items": action_items,
        "decisions": decisions,
        "clarifications": [],
        "limitations": [
            "This is rule-based demo analysis, not an AI-generated result.",
            "Detected action items and decisions require human review.",
            "Deadline phrases are preserved, but calendar dates are not inferred.",
            "Task detection is pattern-based and may miss or misclassify statements.",
        ],
    }


def analyze_transcript(transcript: str) -> dict:
    """Analyze a transcript using the configured provider."""
    if not isinstance(transcript, str) or not transcript.strip():
        raise ValueError("Please provide a meeting transcript.")

    if len(transcript) > MAX_TRANSCRIPT_LENGTH:
        raise ValueError(
            f"Transcript must not exceed {MAX_TRANSCRIPT_LENGTH:,} characters."
        )

    provider = Config.AI_PROVIDER

    # Temporary diagnostic: confirms which analyzer the app selects.
    print(f"DEBUG: analyze_transcript is using provider={provider!r}")

    if provider == "demo":
        return _analyze_with_demo(transcript)

    if provider == "gemini":
        return analyze_with_gemini(
            transcript=transcript,
            api_key=Config.GEMINI_API_KEY,
            model=Config.GEMINI_MODEL,
        )

    raise GeminiServiceError(
        "Unsupported AI provider. Configure demo or gemini."
    )
