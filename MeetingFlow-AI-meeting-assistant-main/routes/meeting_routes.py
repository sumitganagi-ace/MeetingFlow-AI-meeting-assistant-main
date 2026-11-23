
import os
import uuid
from datetime import datetime, timedelta, timezone

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from config import Config
from extensions import db
from models import (
    ActionItem,
    Decision,
    Meeting,
    TaskActivity,
    TaskAttachment,
    TaskComment,
)
from services.gemini_service import GeminiServiceError
from services.transcript_service import (
    MAX_TRANSCRIPT_LENGTH,
    analyze_transcript,
)

meeting_bp = Blueprint("meetings", __name__)

SAMPLE_TRANSCRIPT = """Meeting Title: Project Planning

Asha will prepare the database schema.
Rahul will create the dashboard by Friday.
We decided to use Flask for the backend.
The team discussed testing and documentation.
Someone should probably handle deployment.
"""

MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024

ALLOWED_ATTACHMENT_EXTENSIONS = {
    "pdf", "png", "jpg", "jpeg", "gif", "webp",
    "doc", "docx", "txt", "csv", "xls", "xlsx",
    "ppt", "pptx",
}


def get_upload_folder():
    """Return the task attachment storage directory."""

    upload_folder = os.path.join(
        current_app.root_path,
        "uploads",
    )

    os.makedirs(upload_folder, exist_ok=True)

    return upload_folder


def allowed_attachment(filename):
    """Check whether an attachment has an allowed extension."""

    if "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()

    return extension in ALLOWED_ATTACHMENT_EXTENSIONS


def get_owned_meeting(meeting_id):
    """Return a meeting only if it belongs to the logged-in user."""

    return Meeting.query.filter_by(
        id=meeting_id,
        user_id=current_user.id,
    ).first_or_404()


def get_owned_action_item(item_id):
    """Return an action item only if its meeting belongs to the user."""

    return (
        ActionItem.query
        .join(Meeting)
        .filter(
            ActionItem.id == item_id,
            Meeting.user_id == current_user.id,
        )
        .first_or_404()
    )


@meeting_bp.route("/", methods=["GET"])
@login_required
def index():
    search_query = request.args.get("search", "").strip()

    meetings_query = Meeting.query.filter_by(
        user_id=current_user.id
    )

    if search_query:
        meetings_query = meetings_query.filter(
            Meeting.title.ilike(f"%{search_query}%")
        )

    recent_meetings = (
        meetings_query
        .order_by(Meeting.created_at.desc())
        .limit(5)
        .all()
    )

    total_meetings = (
        db.session.query(func.count(Meeting.id))
        .filter(Meeting.user_id == current_user.id)
        .scalar()
        or 0
    )

    user_tasks_query = (
        ActionItem.query
        .join(Meeting)
        .filter(Meeting.user_id == current_user.id)
    )

    total_tasks = user_tasks_query.count()

    completed_tasks = (
        user_tasks_query
        .filter(func.lower(ActionItem.status) == "completed")
        .count()
    )

    pending_tasks = total_tasks - completed_tasks

    completion_percentage = (
        round((completed_tasks / total_tasks) * 100)
        if total_tasks > 0
        else 0
    )

    all_tasks = (
        ActionItem.query
        .join(Meeting)
        .filter(Meeting.user_id == current_user.id)
        .order_by(
            ActionItem.deadline.is_(None),
            ActionItem.deadline.asc(),
            ActionItem.created_at.desc(),
        )
        .all()
    )

    today = datetime.now(timezone.utc).date()
    upcoming_limit = today + timedelta(days=3)

    overdue_tasks = []
    upcoming_tasks = []

    for item in all_tasks:
        if (item.status or "").lower() != "pending":
            continue

        if item.deadline is None:
            continue

        deadline_date = item.deadline.date()

        if deadline_date < today:
            overdue_tasks.append(item)
        elif deadline_date <= upcoming_limit:
            upcoming_tasks.append(item)

    return render_template(
        "index.html",
        sample_transcript=SAMPLE_TRANSCRIPT,
        recent_meetings=recent_meetings,
        max_length=MAX_TRANSCRIPT_LENGTH,
        ai_provider=Config.AI_PROVIDER,
        total_meetings=total_meetings,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        completion_percentage=completion_percentage,
        search_query=search_query,
        all_tasks=all_tasks,
        overdue_tasks=overdue_tasks,
        upcoming_tasks=upcoming_tasks,
        overdue_count=len(overdue_tasks),
        upcoming_count=len(upcoming_tasks),
    )


@meeting_bp.route("/meetings", methods=["POST"])
@login_required
def create_meeting():
    transcript = request.form.get("transcript", "").strip()

    if not transcript:
        flash("Please enter a meeting transcript.", "error")
        return redirect(url_for("meetings.index"))

    if len(transcript) > MAX_TRANSCRIPT_LENGTH:
        flash(
            f"Transcript must not exceed {MAX_TRANSCRIPT_LENGTH:,} characters.",
            "error",
        )
        return redirect(url_for("meetings.index"))

    try:
        result = analyze_transcript(transcript)

        meeting = Meeting(
            user_id=current_user.id,
            title=result["meeting_title"],
            transcript=transcript,
            summary=result["summary"],
            status="completed",
            analysis_provider=Config.AI_PROVIDER,
        )

        for item in result["action_items"]:
            meeting.action_items.append(
                ActionItem(
                    description=item["description"],
                    owner=item.get("owner"),
                    deadline=None,
                    status=item.get("status", "pending"),
                    priority=item.get("priority"),
                    evidence_excerpt=item.get("evidence_excerpt"),
                    uncertainty_flags=item.get("uncertainty_flags", []),
                    original_ai_data=item,
                )
            )

        for item in result["decisions"]:
            meeting.decisions.append(
                Decision(
                    description=item["description"],
                    evidence_excerpt=item.get("evidence_excerpt"),
                )
            )

        db.session.add(meeting)
        db.session.commit()

        flash("Meeting analyzed successfully.", "success")

        return redirect(
            url_for("meetings.meeting_detail", meeting_id=meeting.id)
        )

    except GeminiServiceError:
        db.session.rollback()
        flash(
            "Gemini analysis failed. Check your API configuration and try again.",
            "error",
        )
        return redirect(url_for("meetings.index"))

    except ValueError as exc:
        db.session.rollback()
        flash(str(exc), "error")
        return redirect(url_for("meetings.index"))

    except SQLAlchemyError:
        db.session.rollback()
        flash(
            "We couldn't save the meeting. Please try again.",
            "error",
        )
        return redirect(url_for("meetings.index"))

    except Exception:
        db.session.rollback()
        flash(
            "An unexpected error occurred. Please try again.",
            "error",
        )
        return redirect(url_for("meetings.index"))


@meeting_bp.route("/meetings/<int:meeting_id>", methods=["GET"])
@login_required
def meeting_detail(meeting_id):
    meeting = get_owned_meeting(meeting_id)

    today = datetime.now().date()
    due_soon_limit = today + timedelta(days=3)

    due_alerts = {}

    for item in meeting.action_items:
        alert = None

        if (
            (item.status or "").lower() == "pending"
            and item.deadline is not None
        ):
            deadline_date = item.deadline.date()

            if deadline_date < today:
                alert = "overdue"
            elif deadline_date <= due_soon_limit:
                alert = "due_soon"
            else:
                alert = "on_track"

        due_alerts[item.id] = alert

    return render_template(
        "meeting_detail.html",
        meeting=meeting,
        due_alerts=due_alerts,
    )


def validate_and_update_action_item(item):
    """Validate and save editable action item fields."""

    owner = request.form.get("owner", "").strip()
    deadline_text = request.form.get("deadline", "").strip()
    status = request.form.get("status", "").strip().lower()
    priority = request.form.get("priority", "").strip().lower()

    if len(owner) > 120:
        return "Owner name must not exceed 120 characters."

    if status not in {"pending", "completed"}:
        return "Invalid action item status."

    if priority not in {"", "high", "medium", "low"}:
        return "Invalid task priority."

    deadline = None

    if deadline_text:
        try:
            deadline = datetime.strptime(deadline_text, "%Y-%m-%d")
        except ValueError:
            return "Please select a valid deadline."

    item.owner = owner or None
    item.deadline = deadline
    item.status = status
    item.priority = priority or None

    return None


def get_action_item_snapshot(item):
    """Capture editable values before an update."""

    return {
        "owner": item.owner or None,
        "deadline": (
            item.deadline.strftime("%Y-%m-%d")
            if item.deadline
            else None
        ),
        "status": (item.status or "").lower(),
        "priority": (item.priority or "").lower() or None,
    }


def record_action_item_changes(item, old_values):
    """Create history records only for fields that changed."""

    new_values = get_action_item_snapshot(item)

    field_labels = {
        "owner": "Owner",
        "deadline": "Due date",
        "status": "Status",
        "priority": "Priority",
    }

    for field_name, new_value in new_values.items():
        old_value = old_values[field_name]

        if old_value != new_value:
            activity = TaskActivity(
                action_item_id=item.id,
                field_name=field_labels[field_name],
                old_value=old_value,
                new_value=new_value,
            )

            db.session.add(activity)


@meeting_bp.route(
    "/meetings/<int:meeting_id>/action-items/<int:item_id>/update",
    methods=["POST"],
)
@login_required
def update_action_item(meeting_id, item_id):
    meeting = get_owned_meeting(meeting_id)

    item = ActionItem.query.filter_by(
        id=item_id,
        meeting_id=meeting.id,
    ).first_or_404()

    try:
        old_values = get_action_item_snapshot(item)

        error = validate_and_update_action_item(item)

        if error:
            flash(error, "error")
            return redirect(
                url_for("meetings.meeting_detail", meeting_id=meeting.id)
            )

        record_action_item_changes(item, old_values)

        db.session.commit()

        flash("Action item updated successfully.", "success")

    except SQLAlchemyError:
        db.session.rollback()
        flash("Could not update the action item. Please try again.", "error")

    return redirect(
        url_for("meetings.meeting_detail", meeting_id=meeting.id)
    )


@meeting_bp.route(
    "/action-items/<int:item_id>/update",
    methods=["POST"],
)
@login_required
def update_dashboard_action_item(item_id):
    """Update an action item directly from the dashboard."""

    item = get_owned_action_item(item_id)

    try:
        old_values = get_action_item_snapshot(item)

        error = validate_and_update_action_item(item)

        if error:
            flash(error, "error")
            return redirect(url_for("meetings.index"))

        record_action_item_changes(item, old_values)

        db.session.commit()

        flash("Dashboard task updated successfully.", "success")

    except SQLAlchemyError:
        db.session.rollback()
        flash(
            "Could not update the dashboard task. Please try again.",
            "error",
        )

    return redirect(url_for("meetings.index"))


@meeting_bp.route(
    "/meetings/<int:meeting_id>/action-items/<int:item_id>/comments",
    methods=["POST"],
)
@login_required
def add_task_comment(meeting_id, item_id):
    """Add a comment to an action item."""

    meeting = get_owned_meeting(meeting_id)

    item = ActionItem.query.filter_by(
        id=item_id,
        meeting_id=meeting.id,
    ).first_or_404()

    author = request.form.get("author", "").strip()
    comment_text = request.form.get("comment", "").strip()

    if not comment_text:
        flash("Please enter a comment before submitting.", "error")
        return redirect(
            url_for("meetings.meeting_detail", meeting_id=meeting.id)
        )

    if len(author) > 120:
        flash("Author name must not exceed 120 characters.", "error")
        return redirect(
            url_for("meetings.meeting_detail", meeting_id=meeting.id)
        )

    if len(comment_text) > 5000:
        flash("Comment must not exceed 5,000 characters.", "error")
        return redirect(
            url_for("meetings.meeting_detail", meeting_id=meeting.id)
        )

    try:
        new_comment = TaskComment(
            action_item_id=item.id,
            author=author or "You",
            comment=comment_text,
        )

        db.session.add(new_comment)
        db.session.commit()

        flash("Comment added successfully.", "success")

    except SQLAlchemyError:
        db.session.rollback()
        flash("Could not save your comment. Please try again.", "error")

    return redirect(
        url_for("meetings.meeting_detail", meeting_id=meeting.id)
    )


@meeting_bp.route(
    "/meetings/<int:meeting_id>/action-items/<int:item_id>/attachments",
    methods=["POST"],
)
@login_required
def upload_task_attachment(meeting_id, item_id):
    """Upload an attachment to an owned action item."""

    meeting = get_owned_meeting(meeting_id)

    item = ActionItem.query.filter_by(
        id=item_id,
        meeting_id=meeting.id,
    ).first_or_404()

    uploaded_file = request.files.get("file")

    if not uploaded_file or not uploaded_file.filename:
        flash("Please select a file to upload.", "error")
        return redirect(
            url_for("meetings.meeting_detail", meeting_id=meeting.id)
        )

    original_filename = secure_filename(uploaded_file.filename)

    if not original_filename:
        flash("Invalid filename.", "error")
        return redirect(
            url_for("meetings.meeting_detail", meeting_id=meeting.id)
        )

    if not allowed_attachment(original_filename):
        flash(
            "File type not allowed. Upload PDF, images, Word, text, "
            "CSV, Excel or PowerPoint files.",
            "error",
        )
        return redirect(
            url_for("meetings.meeting_detail", meeting_id=meeting.id)
        )

    file_path = None

    try:
        uploaded_file.stream.seek(0, os.SEEK_END)
        file_size = uploaded_file.stream.tell()
        uploaded_file.stream.seek(0)

        if file_size == 0:
            flash("The selected file is empty.", "error")
            return redirect(
                url_for("meetings.meeting_detail", meeting_id=meeting.id)
            )

        if file_size > MAX_ATTACHMENT_SIZE:
            flash("File size must not exceed 10 MB.", "error")
            return redirect(
                url_for("meetings.meeting_detail", meeting_id=meeting.id)
            )

        extension = original_filename.rsplit(".", 1)[1].lower()
        stored_filename = f"{uuid.uuid4().hex}.{extension}"

        upload_folder = get_upload_folder()
        file_path = os.path.join(upload_folder, stored_filename)

        uploaded_file.save(file_path)

        attachment = TaskAttachment(
            action_item_id=item.id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_size=file_size,
        )

        db.session.add(attachment)
        db.session.commit()

        flash("Task attachment uploaded successfully.", "success")

    except (SQLAlchemyError, OSError):
        db.session.rollback()

        if file_path and os.path.exists(file_path):
            os.remove(file_path)

        flash("Could not upload the attachment. Please try again.", "error")

    return redirect(
        url_for("meetings.meeting_detail", meeting_id=meeting.id)
    )


@meeting_bp.route(
    "/meetings/<int:meeting_id>/action-items/<int:item_id>/attachments/<int:attachment_id>/download",
    methods=["GET"],
)
@login_required
def download_task_attachment(meeting_id, item_id, attachment_id):
    """Download an attachment after verifying meeting ownership."""

    meeting = get_owned_meeting(meeting_id)

    item = ActionItem.query.filter_by(
        id=item_id,
        meeting_id=meeting.id,
    ).first_or_404()

    attachment = TaskAttachment.query.filter_by(
        id=attachment_id,
        action_item_id=item.id,
    ).first_or_404()

    upload_folder = get_upload_folder()

    return send_from_directory(
        upload_folder,
        attachment.stored_filename,
        as_attachment=True,
        download_name=attachment.original_filename,
    )
