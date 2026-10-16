# Homework Tracker — Project Plan

A website where students track homework: sign up, log in, add homework (subject + due date), mark done, see this week's due items, and view done / pending / late counts.

## Stack
- Backend: Python (Flask)
- Database: SQLite (simple, no setup)
- Frontend: HTML + CSS + a little JavaScript

## Features
1. Sign up / log in (password hashing)
2. Add homework (subject, description, due date)
3. Mark homework as done
4. "Due this week" view
5. Dashboard counts: done, pending, late
## Deployment (Vercel + Supabase)
- [x] app.py uses Supabase Postgres when `DATABASE_URL` is set, SQLite otherwise
- [x] Added psycopg2-binary, vercel.json, .gitignore
- [ ] Get Supabase connection string from user
- [ ] Set DATABASE_URL + SECRET_KEY on Vercel, push to GitHub, deploy
- [ ] Test signup / add homework on the live URL
