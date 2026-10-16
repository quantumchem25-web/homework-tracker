# 📚 Homework Tracker

A simple website where students can track their homework.

🌐 Live site: https://homework-tracker-eight-iota.vercel.app

## Features
- Sign up and log in (passwords are hashed)
- Add homework with subject, description and due date
- Mark homework as done (or undo)
- See what's due this week
- Dashboard counts: done, pending and late
- Delete homework

## Stack
- Backend: Python + Flask
- Database: SQLite (no setup needed)
- Frontend: HTML + CSS

## Run it locally

```bash
# 1. Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python app.py
```

Then open http://127.0.0.1:5000 in your browser.