# AI Interview Preparation Coach

A Streamlit app that generates tailored interview questions from a job title and job description, then scores your answers with Google Gemini Flash.

## Features
- Enter a job title and paste a job description
- AI-generated questions (behavioral, technical, situational) at your chosen difficulty
- Score out of 100 with a breakdown (relevance, clarity, depth, structure)
- Strengths, weaknesses, and actionable improvements
- A stronger example answer for each question
- Session summary with average score, recurring weaknesses, and a downloadable report

## Setup
1. Get a free API key at https://aistudio.google.com/apikey
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Provide the key in one of three ways:
   - Paste it into the sidebar when the app runs
   - Set the `GEMINI_API_KEY` environment variable
   - Add `GEMINI_API_KEY = "your-key"` to `.streamlit/secrets.toml` (or Streamlit Cloud secrets)
4. Run:
   ```
   streamlit run app.py
   ```

## Deploying to Streamlit Community Cloud
Push the repo to GitHub, create a new app pointing at `app.py`, and add `GEMINI_API_KEY` under Settings → Secrets.
Do not commit `.streamlit/secrets.toml` or your key.

## Changing the model
Edit `MODEL_NAME` at the top of `app.py` (default: `gemini-flash-latest`).# ai-interview-preprations
