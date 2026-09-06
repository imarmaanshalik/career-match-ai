```python
import streamlit as st
import plotly.graph_objects as go

from src.resume_parser import extract_text_from_pdf
from src.skills import extract_skills
from src.matcher import calculate_match
from src.analyzer import analyze_skills


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="CareerMatch AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>

    /* Main background */

    .stApp {
        background:
            radial-gradient(
                circle at 10% 10%,
                rgba(124, 58, 237, 0.15),
                transparent 30%
            ),
            radial-gradient(
                circle at 90% 20%,
                rgba(6, 182, 212, 0.12),
                transparent 30%
            ),
            #050505;
    }


    /* Main content */

    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }


    /* Hero */

    .hero-title {
        text-align: center;
        font-size: 64px;
        font-weight: 900;
        letter-spacing: -3px;

        background: linear-gradient(
            90deg,
            #ffffff,
            #a78bfa,
            #67e8f9,
            #ffffff
        );

        background-size: 300%;

        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;

        animation: gradientMove 6s infinite;
    }


    @keyframes gradientMove {

        0% {
            background-position: 0%;
        }

        50% {
            background-position: 100%;
        }

        100% {
            background-position: 0%;
        }

    }


    .hero-text {
        text-align: center;
        color: #a1a1aa;
        font-size: 18px;
        line-height: 1.7;
        max-width: 720px;
        margin: auto;
    }


    /* Cards */

    .card {
        background: rgba(20, 20, 20, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 22px;
        padding: 25px;
        margin-top: 10px;
        margin-bottom: 15px;

        box-shadow:
            0 15px 50px rgba(0, 0, 0, 0.35);

        transition: 0.3s ease;
    }


    .card:hover {
        transform: translateY(-4px);
        border-color: rgba(167, 139, 250, 0.35);
    }


    .card-title {
        font-size: 20px;
        font-weight: 800;
    }


    .card-subtitle {
        color: #71717a;
        font-size: 13px;
        margin-top: 5px;
    }


    /* Score */

    .score {
        font-size: 70px;
        font-weight: 900;
        text-align: center;

        background: linear-gradient(
            135deg,
            #a78bfa,
            #67e8f9
        );

        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;

        animation: scoreIn 0.8s ease;
    }


    @keyframes scoreIn {

        from {
            opacity: 0;
            transform: scale(0.5);
        }

        to {
            opacity: 1;
            transform: scale(1);
        }

    }


    .score-label {
        text-align: center;
        color: #71717a;
        font-size: 12px;
        letter-spacing: 2px;
        text-transform: uppercase;
    }


    /* Metric */

    .metric {
        text-align: center;
        padding: 20px;
        border-radius: 18px;

        background: rgba(255, 255, 255, 0.035);

        border: 1px solid rgba(255, 255, 255, 0.07);

        transition: 0.3s;
    }


    .metric:hover {
        transform: translateY(-5px);
        border-color: rgba(103, 232, 249, 0.3);
    }


    .metric-number {
        font-size: 30px;
        font-weight: 850;
    }


    .metric-label {
        color: #71717a;
        font-size: 12px;
        margin-top: 5px;
    }


    /* Skill pills */

    .skill {
        display: inline-block;

        padding: 8px 13px;

        margin: 4px;

        border-radius: 30px;

        background: rgba(255, 255, 255, 0.04);

        border: 1px solid rgba(255, 255, 255, 0.08);

        font-size: 13px;

        transition: 0.25s;
    }


    .skill:hover {
        transform: translateY(-3px);
        background: rgba(124, 58, 237, 0.15);
    }


    .matched {
        color: #86efac;
    }


    .missing {
        color: #fca5a5;
    }


    /* Roadmap */

    .roadmap {
        display: flex;
        align-items: center;

        padding: 15px;

        margin: 8px 0;

        border-radius: 15px;

        background: rgba(255, 255, 255, 0.035);

        border: 1px solid rgba(255, 255, 255, 0.07);

        transition: 0.3s;
    }


    .roadmap:hover {
        transform: translateX(6px);
        border-color: rgba(103, 232, 249, 0.3);
    }


    .roadmap-number {
        width: 34px;
        height: 34px;

        display: flex;
        align-items: center;
        justify-content: center;

        border-radius: 50%;

        background: rgba(124, 58, 237, 0.2);

        margin-right: 14px;

        font-weight: 800;
    }


    /* Button */

    .stButton > button {
        width: 100%;

        border-radius: 15px;

        border: none;

        padding: 14px;

        font-size: 16px;

        font-weight: 800;

        background: linear-gradient(
            90deg,
            #7c3aed,
            #2563eb,
            #06b6d4
        );

        color: white;

        transition: 0.3s;

        box-shadow:
            0 10px 35px rgba(124, 58, 237, 0.25);
    }


    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow:
            0 15px 45px rgba(124, 58, 237, 0.4);
    }


    /* Text area */

    textarea {
        border-radius: 15px !important;
    }


    /* Footer */

    .footer {
        text-align: center;
        color: #52525b;
        margin-top: 60px;
        padding-bottom: 20px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# HERO
# =========================================================

st.markdown(
    """
    <div class="hero-title">
        CareerMatch AI
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="hero-text">
        Your AI-powered career intelligence platform.
        Upload your resume, choose a job, and discover
        exactly how ready you are for the role.
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")


# =========================================================
# FEATURE ROW
# =========================================================

f1, f2, f3, f4 = st.columns(4)

with f1:
    st.info("🎯 Smart Matching")

with f2:
    st.info("🧠 AI Analysis")

with f3:
    st.info("📊 Skill Insights")

with f4:
    st.info("🗺️ Career Roadmap")


st.write("")


# =========================================================
# INPUT SECTION
# =========================================================

left, right = st.columns(2, gap="large")


with left:

    st.markdown(
        """
        <div class="card">

        <div class="card-title">
        📄 Upload Your Resume
        </div>

        <div class="card-subtitle">
        Upload your latest PDF resume.
        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    resume_file = st.file_uploader(
        "Choose PDF",
        type=["pdf"],
        label_visibility="collapsed"
    )


with right:

    st.markdown(
        """
        <div class="card">

        <div class="card-title">
        💼 Target Job
        </div>

        <div class="card-subtitle">
        Paste the job description you want to analyze.
        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    job_description = st.text_area(
        "Job description",
        height=190,
        placeholder=(
            "Paste the job description here..."
        ),
        label_visibility="collapsed"
    )


st.write("")


# =========================================================
# ANALYZE BUTTON
# =========================================================

analyze = st.button(
    "⚡ ANALYZE MY CAREER MATCH",
    use_container_width=True
)


# =========================================================
# ANALYSIS
# =========================================================

if analyze:

    if resume_file is None:

        st.error(
            "📄 Please upload your resume."
        )

        st.stop()


    if not job_description.strip():

        st.error(
            "💼 Please paste a job description."
        )

        st.stop()


    progress = st.progress(0)

    status = st.empty()


    status.write(
        "📄 Reading your resume..."
    )

    resume_text = extract_text_from_pdf(
        resume_file
    )

    progress.progress(25)


    if not resume_text:

        st.error(
            "Could not read the uploaded PDF."
        )

        st.stop()


    status.write(
        "🧠 Extracting skills..."
    )

    resume_skills = extract_skills(
        resume_text
    )

    job_skills = extract_skills(
        job_description
    )

    progress.progress(50)


    status.write(
        "🎯 Calculating semantic similarity..."
    )

    match_score = calculate_match(
        resume_text,
        job_description
    )

    progress.progress(75)


    status.write(
        "📊 Preparing your career report..."
    )

    matched, missing, skill_score = analyze_skills(
        resume_skills,
        job_skills
    )

    progress.progress(100)

    status.success(
        "Analysis complete!"
    )


    st.session_state["analyzed"] = True
    st.session_state["match_score"] = match_score
    st.session_state["matched"] = matched
    st.session_state["missing"] = missing
    st.session_state["skill_score"] = skill_score


# =========================================================
# RESULTS
# =========================================================

if st.session_state.get("analyzed", False):

    match_score = st.session_state["match_score"]

    matched = st.session_state["matched"]

    missing = st.session_state["missing"]

    skill_score = st.session_state["skill_score"]


    st.divider()

    st.subheader(
        "✨ Your Career Intelligence"
    )


    # -----------------------------------------------------
    # SCORE
    # -----------------------------------------------------

    c1, c2, c3 = st.columns(3)


    with c1:

        st.markdown(
            f"""
            <div class="card">

            <div class="score">
            {match_score:.0f}%
            </div>

            <div class="score-label">
            AI JOB MATCH
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    with c2:

        st.markdown(
            f"""
            <div class="metric">

            <div class="metric-number">
            {skill_score:.0f}%
            </div>

            <div class="metric-label">
            SKILLS MATCH
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    with c3:

        st.markdown(
            f"""
            <div class="metric">

            <div class="metric-number">
            {len(missing)}
            </div>

            <div class="metric-label">
            SKILLS TO LEARN
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    st.write("")


    # -----------------------------------------------------
    # SKILLS
    # -----------------------------------------------------

    skill1, skill2 = st.columns(2)


    with skill1:

        st.markdown(
            """
            <div class="card">

            <div class="card-title">
            🟢 Matching Skills
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        if matched:

            for skill in matched:

                st.markdown(
                    f"""
                    <span class="skill matched">
                    ✓ {skill}
                    </span>
                    """,
                    unsafe_allow_html=True
                )

        else:

            st.warning(
                "No matching skills detected."
            )


    with skill2:

        st.markdown(
            """
            <div class="card">

            <div class="card-title">
            🔴 Missing Skills
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        if missing:

            for skill in missing:

                st.markdown(
                    f"""
                    <span class="skill missing">
                    ✕ {skill}
                    </span>
                    """,
                    unsafe_allow_html=True
                )

        else:

            st.success(
                "Excellent! No major skill gaps."
            )


    st.write("")


    # -----------------------------------------------------
    # CHART
    # -----------------------------------------------------

    st.subheader(
        "📊 Skill Breakdown"
    )


    fig = go.Figure()


    fig.add_trace(
        go.Bar(
            x=[
                "Matching Skills",
                "Missing Skills"
            ],

            y=[
                len(matched),
                len(missing)
            ],

            text=[
                len(matched),
                len(missing)
            ],

            textposition="auto"
        )
    )


    fig.update_layout(
        template="plotly_dark",
        height=350,
        showlegend=False,
        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )


    # -----------------------------------------------------
    # CAREER VERDICT
    # -----------------------------------------------------

    st.subheader(
        "🧠 AI Career Verdict"
    )


    if match_score >= 80:

        st.success(
            "🔥 Excellent match! Your profile strongly "
            "aligns with this position."
        )

    elif match_score >= 60:

        st.warning(
            "⚡ Good match! You have a solid foundation, "
            "but improving your missing skills can "
            "increase your readiness."
        )

    else:

        st.error(
            "🚀 Several skill gaps were detected. "
            "Use the roadmap below to improve your profile."
        )


    # -----------------------------------------------------
    # ROADMAP
    # -----------------------------------------------------

    st.subheader(
        "🗺️ Personalized Skill Roadmap"
    )


    if missing:

        for number, skill in enumerate(
            missing[:6],
            start=1
        ):

            st.markdown(
                f"""
                <div class="roadmap">

                    <div class="roadmap-number">
                    {number}
                    </div>

                    <div>
                    <strong>
                    Learn {skill}
                    </strong>

                    <br>

                    <small>
                    Build a practical project using
                    {skill} and add it to your portfolio.
                    </small>

                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

    else:

        st.success(
            "🎉 Your detected skills closely match "
            "the job requirements!"
        )


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div class="footer">

    CareerMatch AI

    <br>

    Analyze • Improve • Get Hired

    </div>
    """,
    unsafe_allow_html=True
)
```
