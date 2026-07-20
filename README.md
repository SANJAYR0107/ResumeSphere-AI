# AI Resume Analyzer

An intelligent, professional application designed to analyze PDF resumes, extract structured text, run NLP-based analysis (including skill parsing and matching), calculate ATS scores, and provide job recommendations.

## Project Structure

```text
AI-Resume-Analyzer/
├── backend/
│   ├── app/
│   ├── uploads/
│   ├── models/
│   ├── services/
│   │   └── parser_service.py
│   ├── utils/
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── datasets/
├── README.md
└── .gitignore
```

## Tech Stack

- **Backend**: FastAPI (Python 3.10+), pypdf, spaCy
- **Frontend**: Premium Vanilla HTML, CSS, JavaScript (Dashboard UI with glassmorphism and smooth animations)

## Setup & Running

### 1. Backend Setup
Activate the virtual environment and install dependencies:
```bash
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r backend/requirements.txt

# Run the FastAPI server
python -m uvicorn backend.main:app --reload
```

### 2. Frontend Setup
Open `frontend/index.html` in a web browser or serve it using any simple static file server. The application is pre-configured to communicate with the FastAPI server running on `http://127.0.0.1:8000`.
