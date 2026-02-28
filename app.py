import streamlit as st
from google import genai
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import numpy as np
import PyPDF2
import json
import re

# ----------------------------
# Load API Key
# ----------------------------
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("GEMINI_API_KEY not found. Check your .env file.")
    st.stop()

client = genai.Client(api_key=api_key)

MODEL_NAME = "gemini-3-flash-preview"   # Stable and widely supported

response = client.models.generate_content(
    model="gemini-3-flash-preview", contents="Explain how AI works in a few words"
)
print(response.text)

# ----------------------------
# UI
# ----------------------------
st.title("🚀 AI Career Advancement Advisor")
st.markdown("Dynamic Skill Gap + Resume Intelligence + ROI Forecasting")

career = st.text_input("Enter Your Target Career Role")

experience_level = st.selectbox(
    "Experience Level",
    ["Fresher", "Final Year Student", "1-2 Years Experience", "Career Switcher"]
)

gpa = st.slider("Current GPA", 0.0, 10.0, 7.0)
weekly_hours = st.slider("Available Learning Hours per Week", 1, 40, 10)

# ----------------------------
# Resume Upload
# ----------------------------
st.subheader("Upload Resume (Optional)")
uploaded_file = st.file_uploader("Upload Resume (PDF or TXT)", type=["pdf", "txt"])

resume_text = ""

if uploaded_file:
    try:
        if uploaded_file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    resume_text += text
        else:
            resume_text = uploaded_file.read().decode("utf-8")
    except:
        st.warning("Could not fully extract resume text.")

# ----------------------------
# Skill Input
# ----------------------------
st.subheader("Enter Your Skills")

num_skills = st.number_input("Number of Skills", 1, 10, 3)

user_skills = {}

for i in range(num_skills):
    col1, col2 = st.columns(2)
    with col1:
        skill_name = st.text_input(f"Skill {i+1} Name", key=f"name_{i}")
    with col2:
        skill_rating = st.slider(f"Skill {i+1} Level", 0, 10, 5, key=f"rate_{i}")
    if skill_name:
        user_skills[skill_name] = skill_rating

# ----------------------------
# ANALYZE
# ----------------------------
if st.button("Generate Career Report"):

    if not career:
        st.warning("Please enter your target career role.")
        st.stop()

    if not user_skills:
        st.warning("Please enter at least one skill.")
        st.stop()

    # ----------------------------
    # Get Required Skills
    # ----------------------------
    required_prompt = f"""
    For the career role '{career}',
    list the top 5 essential technical skills required.

    Return ONLY valid JSON.
    Example:
    {{"Skill1": 8, "Skill2": 7}}
    """

    try:
        required_response = client.models.generate_content(
            model=MODEL_NAME,
            contents=required_prompt
        )
        raw_text = required_response.text
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)

        if json_match:
            required_skills = json.loads(json_match.group())
        else:
            st.error("AI returned invalid format for required skills.")
            st.stop()

    except Exception as e:
        st.error("Error while getting required skills.")
        st.write(e)
        st.stop()

    # ----------------------------
    # Skill Gap Analysis
    # ----------------------------
    gap = {}
    missing_skills = []

    for req_skill, req_level in required_skills.items():
        if req_skill in user_skills:
            if user_skills[req_skill] < req_level:
                gap[req_skill] = req_level - user_skills[req_skill]
        else:
            missing_skills.append(req_skill)

    total_required = sum(required_skills.values())
    total_user = sum(user_skills.get(skill, 0) for skill in required_skills)
    skill_percent = (total_user / total_required) * 100 if total_required else 0

    # Career Maturity
    if skill_percent < 60:
        maturity = "Foundation Level"
    elif skill_percent < 80:
        maturity = "Industry Ready"
    elif skill_percent < 95:
        maturity = "Highly Competitive"
    else:
        maturity = "Premium Candidate"

    resume_score = min(len(resume_text) // 50, 100) if resume_text else 0
    ats_score = int(skill_percent * 0.8)

    # ----------------------------
    # Display Metrics
    # ----------------------------
    st.subheader("📊 Career Analytics")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Skill Match %", f"{skill_percent:.1f}%")
        st.metric("Career Category", maturity)
    with col2:
        st.metric("Resume Strength", f"{resume_score}%")
        st.metric("ATS Readiness", f"{ats_score}%")

    if gap:
        st.error("Skill Gaps Detected")
        st.write(gap)

    if missing_skills:
        st.warning("Missing Required Skills")
        st.write(missing_skills)

    # ----------------------------
    # Time Allocation
    # ----------------------------
    if gap or missing_skills:
        focus_hours = int(weekly_hours * 0.7)
        growth_hours = weekly_hours - focus_hours
    else:
        focus_hours = int(weekly_hours * 0.4)
        growth_hours = weekly_hours - focus_hours

    st.subheader("⏳ Time Allocation Plan")
    st.write(f"Skill Improvement Hours/Week: {focus_hours}")
    st.write(f"Advanced Growth Hours/Week: {growth_hours}")

    # ----------------------------
    # Generate Career Plan
    # ----------------------------
    plan_prompt = f"""
    Target Role: {career}
    Experience Level: {experience_level}
    GPA: {gpa}
    User Skills: {user_skills}
    Required Skills: {required_skills}
    Skill Gaps: {gap}
    Missing Skills: {missing_skills}
    Weekly Learning Hours: {weekly_hours}
    Resume Content: {resume_text}

    Provide:
    1. Resume improvement suggestions
    2. 30-day skill roadmap
    3. 6-month career acceleration plan
    4. Interview preparation strategy
    5. Salary growth advice
    """

    with st.spinner("Generating Career Advancement Plan..."):
        try:
            plan_response = client.models.generate_content(
                model=MODEL_NAME,
                contents=plan_prompt
            )

            st.subheader("🤖 AI Career Advancement Plan")
            st.write(plan_response.text)

        except Exception as e:
            st.error("Error generating career plan.")
            st.write(e)

    # ----------------------------
    # Radar Chart
    # ----------------------------
    if user_skills:
        st.subheader("🕸 Skill Radar")

        labels = list(user_skills.keys())
        values = list(user_skills.values())

        angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False)
        values += values[:1]
        angles = np.concatenate((angles, [angles[0]]))

        fig, ax = plt.subplots(subplot_kw=dict(polar=True))
        ax.plot(angles, values)
        ax.fill(angles, values, alpha=0.25)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels)
        ax.set_yticklabels([])

        st.pyplot(fig)