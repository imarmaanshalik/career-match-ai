import streamlit as st
import plotly.graph_objects as go

from src.resume_parser import extract_text_from_pdf
from src.skills import extract_skills
from src.matcher import calculate_match
from src.analyzer import analyze_skills


# -----------------------------
# PAGE CONFIG
# -----------------------------

st.set_page_config(
    page_title="CareerMatch AI",
    page_icon="🎯",
    layout="wide"
)


# -----------------------------
# CUSTOM CSS
# -----------------------------

st.markdown("""
<style>

.stApp {
    background: #080808;
    color: white;
}

.main-title {
    font-size: 48px;
    font-weight: 800;
    text-align: center;
    margin-top: 20px;
}

.subtitle {
    text-align: center;
    color: #999;
    font-size: 18px;
    margin-bottom: 40px;
}

.card {
    padding: 25px;
    border-radius: 18px;
    background: #121212;
    border: 1px solid #292929;
    margin-bottom: 20px;
}

.score {
    font-size: 64px;
    font-weight: 800;
    text-align: center;
}

.success {
    color: #4ade80;
}

.danger {
    color: #f87171;
}

.skill {
    display: inline-block;
    padding: 8px 14px;
    margin: 5px;
    border-radius: 20px;
    background: #202020;
    border: 1px solid #333;
}

</style>
""", unsafe_allow_html=True)


# -----------------------------
# HEADER
# -----------------------------

st.markdown(
    '<div class="main-title">🎯 CareerMatch AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'AI-powered Resume & Job Matching Platform'
    '</div>',
    unsafe_allow_html=True
)


# -----------------------------
# INPUT AREA
# -----------------------------

col1, col2 = st.columns(2)

with col1:

    st.markdown("### 📄 Upload Resume")

    resume_file = st.file_uploader(
        "Upload your PDF resume",
        type=["pdf"]
    )


with col2:

    st.markdown("### 💼 Job Description")

    job_description = st.text_area(
        "Paste the job description here",
        height=220,
        placeholder=(
            "Example: We are looking for a "
            "Machine Learning Engineer with "
            "Python, SQL, AWS and Docker..."
        )
    )


# -----------------------------
# ANALYZE
# -----------------------------

st.markdown("")

analyze_button = st.button(
    "🚀 Analyze My Resume",
    use_container_width=True
)


if analyze_button:

    if resume_file is None:

        st.error("Please upload your resume.")

        st.stop()


    if not job_description.strip():

        st.error("Please enter a job description.")

        st.stop()


    # Resume extraction

    with st.spinner("Reading your resume..."):

        resume_text = extract_text_from_pdf(
            resume_file
        )


    if not resume_text:

        st.error(
            "Could not extract text from this PDF."
        )

        st.stop()


    # Skill extraction

    with st.spinner("Analyzing skills..."):

        resume_skills = extract_skills(
            resume_text
        )

        job_skills = extract_skills(
            job_description
        )


    # AI matching

    with st.spinner(
        "Calculating semantic similarity..."
    ):

        match_score = calculate_match(
            resume_text,
            job_description
        )


    # Skill comparison

    matched, missing, skill_score = analyze_skills(
        resume_skills,
        job_skills
    )


    # Save results

    st.session_state["match_score"] = match_score
    st.session_state["matched"] = matched
    st.session_state["missing"] = missing
    st.session_state["skill_score"] = skill_score
    st.session_state["resume_skills"] = resume_skills
    st.session_state["job_skills"] = job_skills


# -----------------------------
# RESULTS
# -----------------------------

if "match_score" in st.session_state:

    match_score = st.session_state["match_score"]
    matched = st.session_state["matched"]
    missing = st.session_state["missing"]
    skill_score = st.session_state["skill_score"]


    st.divider()

    st.markdown("## 🎯 Analysis Result")


    # Score columns

    c1, c2, c3 = st.columns(3)


    with c1:

        st.markdown(
            '<div class="card">',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="score">'
            f'{match_score:.0f}%'
            '</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            "<center>AI Job Match</center>",
            unsafe_allow_html=True
        )

        st.markdown("</div>", unsafe_allow_html=True)


    with c2:

        st.metric(
            "Skills Match",
            f"{skill_score:.0f}%"
        )


    with c3:

        st.metric(
            "Missing Skills",
            len(missing)
        )


    # -----------------------------
    # SKILLS
    # -----------------------------

    left, right = st.columns(2)


    with left:

        st.markdown("### ✅ Matching Skills")

        if matched:

            for skill in matched:

                st.markdown(
                    f'<span class="skill">✓ {skill}</span>',
                    unsafe_allow_html=True
                )

        else:

            st.info("No matching skills detected.")


    with right:

        st.markdown("### ❌ Missing Skills")

        if missing:

            for skill in missing:

                st.markdown(
                    f'<span class="skill">✗ {skill}</span>',
                    unsafe_allow_html=True
                )

        else:

            st.success(
                "Excellent! No major skill gaps detected."
            )


    # -----------------------------
    # CHART
    # -----------------------------

    st.markdown("### 📊 Skill Analysis")

    fig = go.Figure(
        data=[
            go.Bar(
                x=["Matched Skills", "Missing Skills"],
                y=[len(matched), len(missing)]
            )
        ]
    )

    fig.update_layout(
        template="plotly_dark",
        height=350,
        showlegend=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


    # -----------------------------
    # RECOMMENDATION
    # -----------------------------

    st.markdown("### 💡 Career Recommendation")


    if match_score >= 80:

        st.success(
            "🔥 Strong match! "
            "Your profile is highly relevant to this role."
        )

    elif match_score >= 60:

        st.warning(
            "⚡ Good potential. "
            "Improve the missing skills before applying."
        )

    else:

        st.error(
            "📚 Significant skill gaps detected. "
            "Consider building projects around the missing skills."
        )


    # -----------------------------
    # ROADMAP
    # -----------------------------

    st.markdown("### 🗺️ Suggested Learning Roadmap")


    if missing:

        for index, skill in enumerate(
            missing[:5],
            start=1
        ):

            st.write(
                f"**{index}.** Learn **{skill}**"
            )

    else:

        st.write(
            "Keep strengthening your existing skills "
            "with real-world projects."
        )
