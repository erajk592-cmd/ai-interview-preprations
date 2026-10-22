"""AI Interview Preparation Coach - Streamlit + Google Gemini Flash."""

import json
import os
import re

import streamlit as st
import google.generativeai as genai

MODEL_NAME = "gemini-flash-latest"

st.set_page_config(page_title="Interview Prep Coach", page_icon="🎯", layout="wide")


# ----------------------------- Gemini helpers ----------------------------- #
def get_api_key() -> str:
    """API key from sidebar input, Streamlit secrets, or environment."""
    key = st.session_state.get("api_key_input", "").strip()
    if key:
        return key
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    return os.environ.get("GEMINI_API_KEY", "")


def call_gemini(prompt: str) -> dict:
    """Call Gemini and parse a JSON response."""
    api_key = get_api_key()
    if not api_key:
        raise ValueError("Please add your Gemini API key in the sidebar.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        MODEL_NAME,
        generation_config={"response_mime_type": "application/json", "temperature": 0.7},
    )
    response = model.generate_content(prompt)
    text = response.text.strip()
    # Strip markdown fences if the model adds them anyway
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    return json.loads(text)


def generate_questions(job_title: str, job_description: str, num: int, difficulty: str, q_types: list) -> list:
    prompt = f"""You are an expert interviewer hiring for the role of "{job_title}".

Job description:
\"\"\"
{job_description}
\"\"\"

Generate {num} interview questions at {difficulty} difficulty.
Mix of question types to include: {", ".join(q_types)}.
Questions must be tailored to the specific skills, tools and responsibilities in the job description.

Return ONLY JSON in this format:
{{"questions": [{{"question": "...", "type": "Behavioral|Technical|Situational", "what_they_look_for": "one short sentence"}}]}}"""
    return call_gemini(prompt)["questions"]


def evaluate_answer(job_title: str, job_description: str, question: str, answer: str) -> dict:
    prompt = f"""You are a strict but fair interview coach evaluating a candidate for "{job_title}".

Job description:
\"\"\"
{job_description}
\"\"\"

Interview question: {question}

Candidate's answer:
\"\"\"
{answer}
\"\"\"

Evaluate the answer. Score honestly: vague or very short answers should score low.
Return ONLY JSON in this format:
{{
  "score": <integer 0-100>,
  "breakdown": {{"relevance": <0-100>, "clarity": <0-100>, "depth": <0-100>, "structure": <0-100>}},
  "strengths": ["..."],
  "weaknesses": ["..."],
  "improvements": ["specific, actionable suggestion", "..."],
  "example_answer": "A stronger model answer tailored to this job, written in first person, using the STAR method where appropriate."
}}"""
    return call_gemini(prompt)


def score_color(score: int) -> str:
    if score >= 80:
        return "green"
    if score >= 60:
        return "orange"
    return "red"


# ------------------------------ Session state ------------------------------ #
defaults = {
    "questions": [],
    "current": 0,
    "results": {},  # index -> evaluation dict
    "answers": {},  # index -> answer text
    "job_title": "",
    "job_description": "",
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)


def reset_session():
    for k, v in defaults.items():
        st.session_state[k] = v if not isinstance(v, (list, dict)) else type(v)()


# --------------------------------- Sidebar --------------------------------- #
with st.sidebar:
    st.title("🎯 Interview Coach")
    st.text_input(
        "Gemini API key",
        type="password",
        key="api_key_input",
        help="Get a free key at https://aistudio.google.com/apikey",
    )
    st.divider()
    num_questions = st.slider("Number of questions", 3, 10, 5)
    difficulty = st.select_slider("Difficulty", ["Easy", "Medium", "Hard"], value="Medium")
    q_types = st.multiselect(
        "Question types",
        ["Behavioral", "Technical", "Situational"],
        default=["Behavioral", "Technical", "Situational"],
    )
    st.divider()
    if st.button("🔄 Start over", use_container_width=True):
        reset_session()
        st.rerun()

# ---------------------------------- Setup ---------------------------------- #
st.title("AI Interview Preparation Coach")

if not st.session_state.questions:
    st.write("Enter the role you're targeting and paste the job description. The coach will generate tailored questions and score your answers.")
    job_title = st.text_input("Job title", placeholder="e.g. Data Analyst")
    job_description = st.text_area("Job description", height=250, placeholder="Paste the full job description here...")

    if st.button("Generate interview questions", type="primary"):
        if not job_title.strip() or not job_description.strip():
            st.warning("Please enter both a job title and a job description.")
        elif not q_types:
            st.warning("Select at least one question type in the sidebar.")
        else:
            with st.spinner("Preparing your interview..."):
                try:
                    st.session_state.questions = generate_questions(
                        job_title, job_description, num_questions, difficulty, q_types
                    )
                    st.session_state.job_title = job_title
                    st.session_state.job_description = job_description
                    st.session_state.current = 0
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not generate questions: {e}")
    st.stop()

# -------------------------------- Practice UI -------------------------------- #
questions = st.session_state.questions
idx = st.session_state.current
total = len(questions)
done = len(st.session_state.results)

tab_practice, tab_summary = st.tabs(["Practice", "Summary"])

with tab_practice:
    st.progress(done / total, text=f"{done}/{total} questions answered")
    nav1, nav2, nav3 = st.columns([1, 3, 1])
    with nav1:
        if st.button("← Previous", disabled=idx == 0):
            st.session_state.current -= 1
            st.rerun()
    with nav3:
        if st.button("Next →", disabled=idx >= total - 1):
            st.session_state.current += 1
            st.rerun()

    q = questions[idx]
    st.subheader(f"Question {idx + 1} of {total}")
    st.caption(f"{q.get('type', 'General')} • Role: {st.session_state.job_title}")
    st.markdown(f"### {q['question']}")
    with st.expander("What interviewers look for"):
        st.write(q.get("what_they_look_for", ""))

    answer = st.text_area(
        "Your answer",
        value=st.session_state.answers.get(idx, ""),
        height=200,
        key=f"answer_box_{idx}",
        placeholder="Type your answer as you would say it in the interview...",
    )

    if st.button("Evaluate my answer", type="primary"):
        if len(answer.strip()) < 10:
            st.warning("Please write a longer answer first.")
        else:
            st.session_state.answers[idx] = answer
            with st.spinner("Evaluating..."):
                try:
                    st.session_state.results[idx] = evaluate_answer(
                        st.session_state.job_title,
                        st.session_state.job_description,
                        q["question"],
                        answer,
                    )
                except Exception as e:
                    st.error(f"Evaluation failed: {e}")

    result = st.session_state.results.get(idx)
    if result:
        st.divider()
        score = int(result["score"])
        c1, c2 = st.columns([1, 2])
        with c1:
            st.metric("Overall score", f"{score}/100")
            st.markdown(f":{score_color(score)}[{'Strong' if score >= 80 else 'Decent' if score >= 60 else 'Needs work'}]")
        with c2:
            for name, val in result.get("breakdown", {}).items():
                st.progress(max(0, min(int(val), 100)) / 100, text=f"{name.title()}: {val}")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### ✅ Strengths")
            for s in result.get("strengths", []):
                st.markdown(f"- {s}")
        with col_b:
            st.markdown("#### ⚠️ Weaknesses")
            for w in result.get("weaknesses", []):
                st.markdown(f"- {w}")

        st.markdown("#### 💡 How to improve")
        for imp in result.get("improvements", []):
            st.markdown(f"- {imp}")

        st.markdown("#### ⭐ Better example answer")
        st.info(result.get("example_answer", ""))

with tab_summary:
    if not st.session_state.results:
        st.info("Answer at least one question to see your summary.")
    else:
        scores = [int(r["score"]) for r in st.session_state.results.values()]
        avg = sum(scores) / len(scores)
        st.metric("Average score", f"{avg:.0f}/100", help=f"Across {len(scores)} answered questions")
        st.bar_chart({f"Q{i + 1}": int(r["score"]) for i, r in sorted(st.session_state.results.items())})

        all_weak = [w for r in st.session_state.results.values() for w in r.get("weaknesses", [])]
        if all_weak:
            st.markdown("#### Recurring weaknesses to work on")
            for w in all_weak[:8]:
                st.markdown(f"- {w}")

        report = [f"# Interview Practice Report: {st.session_state.job_title}\n", f"Average score: {avg:.0f}/100\n"]
        for i, r in sorted(st.session_state.results.items()):
            report.append(f"\n## Q{i + 1}: {questions[i]['question']}")
            report.append(f"Score: {r['score']}/100\n")
            report.append(f"**Your answer:** {st.session_state.answers.get(i, '')}\n")
            report.append("**Improvements:**")
            report += [f"- {x}" for x in r.get("improvements", [])]
            report.append(f"\n**Example answer:** {r.get('example_answer', '')}")
        st.download_button("Download report (.md)", "\n".join(report), file_name="interview_report.md")
