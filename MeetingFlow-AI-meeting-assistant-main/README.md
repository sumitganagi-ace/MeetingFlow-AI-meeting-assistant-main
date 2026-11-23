# MeetingFlow – AI-Powered Meeting-to-Action Assistant

MeetingFlow is an AI-powered web application that transforms meeting transcripts into structured and actionable information. It uses Google Gemini to identify important discussions, action items, decisions, responsibilities and deadlines.

The goal is to help teams save time, organize meeting outcomes and track tasks efficiently.

## Features  

- **AI Meeting Analysis:** Analyze meeting transcripts using Google Gemini.
- **Automatic Task Extraction:** Identify action items, owners and deadlines.
- **Decision Extraction:** Automatically identify important meeting decisions.
- **Dashboard:** View meetings, tasks and progress in one place.
- **Task Management:** Update task status, priority, owner and due date.
- **Search and Filters:** Find meetings and filter tasks.
- **Task Comments:** Add comments to individual tasks.
- **File Attachments:** Upload and download task-related files.
- **User Authentication:** Register, log in and log out securely.
- **Data Isolation:** Users can access only their own meetings and tasks.
- **CSRF Protection:** Protect POST forms against cross-site request forgery.
- **Automated Testing:** Includes a pytest test suite.

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, Flask |
| Frontend | HTML, CSS, Jinja2 |
| Database | SQLite |
| ORM | Flask-SQLAlchemy |
| AI Integration | Google Gemini API |
| Authentication | Flask-Login |
| Security | Flask-WTF, CSRF Protection |
| Testing | Pytest |

## Project Structure

```text
MeetingFlow/
│
├── app.py
├── config.py
├── extensions.py
├── requirements.txt
├── .env.example
├── .gitignore
│
├── models/
├── routes/
├── services/
├── templates/
└── tests/
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/yarrish-01/MeetingFlow-AI-meeting-assistant.git
```

### 2. Navigate to the project directory

```bash
cd MeetingFlow-AI-meeting-assistant
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

### 4. Activate the virtual environment

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure environment variables

Create a `.env` file using `.env.example` as a reference.

Configure your own values:

```env
SECRET_KEY=your-random-secret-key
DATABASE_URL=sqlite:///meeting_assistant.db
AI_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash
```

You must provide your own Gemini API key. Never upload your `.env` file or API key to GitHub.

### 7. Run the application

```bash
python app.py
```

Open your browser:

```text
http://127.0.0.1:5000
```

## Run Tests

Execute the automated test suite:

```bash
python -m pytest -q
```

## AI Integration

MeetingFlow integrates Google Gemini to analyze meeting transcripts and extract structured information, including:

- Meeting summaries
- Action items
- Task assignments
- Deadlines
- Important decisions

## Future Improvements

- Meeting audio transcription
- Calendar integration
- Email notifications
- Team collaboration features
- Advanced meeting analytics

## Author

**R G Yarrish**

AI & Machine Learning Engineering Student

GitHub: [@yarrish-01](https://github.com/yarrish-01)

---

⭐ If you find this project interesting, consider giving the repository a star!
