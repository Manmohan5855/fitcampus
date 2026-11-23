# FitCampus

FitCampus is a campus-focused fitness and wellness web app built with Flask. It provides personalized workout and diet plans, daily habit tracking, reminders, weekly progress reports, and an administrator dashboard.

## Features

- User signup, login, profiles, and premium tiers
- Personalized workout and diet recommendations
- Daily workout, hydration, sleep, and weight tracking
- Weekly consistency reports
- Reminder settings and admin management
- Optional Gemini AI-generated recommendations with built-in fallbacks

## Local setup

```powershell
py -3.11 -m pip install -r requirements.txt
py -3.11 app.py
```

Open `http://127.0.0.1:5000`.

## Environment variables

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Flask session signing key |
| `GEMINI_API_KEY` | Optional Gemini API key for AI-generated plans |

## Render deployment

Render can deploy this repository using the included `render.yaml` Blueprint.
