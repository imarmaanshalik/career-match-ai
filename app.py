
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
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

/* ---------- GLOBAL ---------- */

.stApp {
    background:
        radial-gradient(circle at 15% 20%, rgba(88, 28, 135, 0.18), transparent 28%),
        radial-gradient(circle at 85% 15%, rgba(37, 99, 235, 0.16), transparent 28%),
        radial-gradient(circle at 50% 90%, rgba(14, 116, 144, 0.12), transparent 30%),
        #050505;

    color: #f5f5f5;
}

/* Hide Streamlit chrome */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    background: transparent !important;
}


/* ---------- ANIMATED BACKGROUND ---------- */

.stApp::before {
    content: "";
    position: fixed;
    width: 500px;
    height: 500px;
    border-radius: 50%;

    background: radial-gradient(
        circle,
        rgba(124, 58, 237, 0.16),
        transparent 65%
    );

    top: -150px;
    left: -150px;

    animation: floatGlow 9s ease-in-out infinite;

    pointer-events: none;
    z-index: 0;
}


.stApp::after {
    content: "";
    position: fixed;
    width: 450px;
    height: 450px;
    border-radius: 50%;

    background: radial-gradient(
        circle,
        rgba(6, 182, 212, 0.12),
        transparent 65%
    );

    bottom: -150px;
    right: -100px;

    animation: floatGlow2 11s ease-in-out infinite;

    pointer-events: none;
    z-index: 0;
}


@keyframes floatGlow {

    0% {
        transform: translate(0, 0) scale(1);
    }

    50% {
        transform: translate(100px, 70px) scale(1.15);
    }

    100% {
        transform: translate(0, 0) scale(1);
    }
}


@keyframes floatGlow2 {

    0% {
        transform: translate(0, 0);
    }

    50% {
        transform: translate(-80px, -60px);
    }

    100% {
        transform: translate(0, 0);
    }
}


/* ---------- MAIN CONTAINER ---------- */

.block-container {
    max-width: 1250px;
    padding-top: 35px;
    position: relative;
    z-index: 1;
}


/* ---------- HERO ---------- */

.hero {
    text-align: center;
    padding: 45px 20px 30px 20px;
}


.badge {
    display: inline-block;

    padding: 8px 18px;

    border-radius: 50px;

    background: rgba(255,255,255,0.05);

    border: 1px solid rgba(255,255,255,0.12);

    color: #c4b5fd;

    font-size: 13px;

    letter-spacing: 1px;

    margin-bottom: 20px;

    animation: badgePulse 3s infinite;
}


@keyframes badgePulse {

    0%,100% {
        box-shadow: 0 0 0 rgba(139,92,246,0);
    }

    50% {
        box-shadow: 0 0 30px rgba(139,92,246,0.18);
    }
}


.hero-title {

    font-size: clamp(45px, 7vw, 82px);

    font-weight: 900;

    line-height: 1;

    letter-spacing: -4px;

    margin-bottom: 20px;

    background: linear-gradient(
        90deg,
        #ffffff,
        #c4b5fd,
        #67e8f9,
        #ffffff
    );

    background-size: 300% auto;

    -webkit-background-clip: text;

    -webkit-text-fill-color: transparent;

    animation: gradientMove 6s linear infinite;
}


@keyframes gradientMove {

    0% {
        background-position: 0% center;
    }

    50% {
        background-position: 100% center;
    }

    100% {
        background-position: 0% center;
    }
}


.hero-subtitle {

    max-width: 720px;

    margin: auto;

    color: #a1a1aa;

    font-size: 18px;

    line-height: 1.7;
}


/* ---------- FEATURE PILLS ---------- */

.features {

    display: flex;

    justify-content: center;

    gap: 10px;

    flex-wrap: wrap;

    margin: 28px 0 45px;
}


.feature {

    padding: 9px 15px;

    border-radius: 30px;

    background: rgba(255,255,255,0.04);

    border: 1px solid rgba(255,255,255,0.09);

    color: #d4d4d8;

    font-size: 13px;

    transition: 0.3s;
}


.feature:hover {

    transform: translateY(-4px);

    border-color: rgba(167,139,250,0.5);

    background: rgba(139,92,246,0.08);
}


/* ---------- GLASS CARD ---------- */

.glass {

    background: rgba(15,15,15,0.72);

    border: 1px solid rgba(255,255,255,0.09);

    border-radius: 24px;

    padding: 28px;

    backdrop-filter: blur(20px);

    box-shadow:
        0 20px 70px rgba(0,0,0,0.35);

    transition: 0.35s ease;
}


.glass:hover {

    transform: translateY(-4px);

    border-color: rgba(167,139,250,0.28);

    box-shadow:
        0 25px 80px rgba(0,0,0,0.5);
}


/* ---------- CARD TITLE ---------- */

.card-title {

    font-size: 20px;

    font-weight: 750;

    margin-bottom: 6px;
}


.card-description {

    color: #71717a;

    font-size: 13px;

    margin-bottom: 20px;
}


/* ---------- FILE UPLOADER ---------- */

[data-testid="stFileUploader"] {

    background: rgba(255,255,255,0.025);

    border: 1px dashed rgba(167,139,250,0.35);

    border-radius: 18px;

    padding: 15px;

    transition: 0.3s;
}


[data-testid="stFileUploader"]:hover {

    border-color: #a78bfa;

    background: rgba(139,92,246,0.06);
}


/* ---------- TEXT AREA ---------- */

textarea {

    background: rgba(255,255,255,0.025) !important;

    border: 1px solid rgba(255,255,255,0.1) !important;

    border-radius: 16px !important;

    color: white !important;

    transition: 0.3s !important;
}


textarea:focus {

    border-color: #8b5cf6 !important;

    box-shadow:
        0 0 0 2px rgba(139,92,246,0.12) !important;
}


/* ---------- BUTTON ---------- */

.stButton > button {

    width: 100%;

    border: none;

    border-radius: 15px;

    padding: 15px;

    font-size: 16px;

    font-weight: 750;

    background: linear-gradient(
        90deg,
        #7c3aed,
        #2563eb,
        #06b6d4
    );

    color: white;

    transition: 0.3s;

    box-shadow:
        0 10px 35px rgba(124,58,237,0.22);
}


.stButton > button:hover {

    transform: translateY(-3px) scale(1.01);

    box-shadow:
        0 15px 45px rgba(124,58,237,0.4);
}


.stButton > button:active {

    transform: scale(0.98);
}


/* ---------- RESULT SCORE ---------- */

.score-container {

    text-align: center;

    padding: 15px;
}


.score {

    font-size: 72px;

    font-weight: 900;

    background: linear-gradient(
        135deg,
        #a78bfa,
        #67e8f9
    );

    -webkit-background-clip: text;

    -webkit-text-fill-color: transparent;

    animation: scoreAppear 0.8s ease;
}


@keyframes scoreAppear {

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

    color: #71717a;

    font-size: 14px;

    text-transform: uppercase;

    letter-spacing: 2px;
}


/* ---------- METRIC ---------- */

.metric-card {

    background: rgba(255,255,255,0.035);

    border: 1px solid rgba(255,255,255,0.08);

    border-radius: 18px;

    padding: 22px;

    text-align: center;

    transition: 0.3s;
}


.metric-card:hover {

    transform: translateY(-5px);

    border-color: rgba(103,232,249,0.25);
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


/* ---------- SKILLS ---------- */

.skill {

    display: inline-block;

    padding: 8px 13px;

    margin: 4px;

    border-radius: 30px;

    font-size: 13px;

    background: rgba(255,255,255,0.045);

    border: 1px solid rgba(255,255,255,0.08);

    transition: 0.25s;
}


.skill:hover {

    transform: translateY(-3px);

    background: rgba(139,92,246,0.12);

    border-color: rgba(139,92,246,0.4);
}


.match {

    color: #86efac;
}


.missing {

    color: #fca5a5;
}


/* ---------- SECTION ---------- */

.section-title {

    font-size: 28px;

    font-weight: 800;

    margin-top: 40px;

    margin-bottom: 20px;
}


/* ---------- ROADMAP ---------- */

.roadmap {

    display: flex;

    align-items: center;

    gap: 14px;

    padding: 16px;

    margin: 8px 0;

    border-radius: 15px;

    background: rgba(255,255,255,0.035);

    border: 1px solid rgba(255,255,255,0.06);

    transition: 0.3s;
}


.roadmap:hover {

    transform: translateX(7px);

    border-color: rgba(103,232,249,0.25);
}


.roadmap-number {

    width: 34px;

    height: 34px;

    display: flex;

    align-items: center;

    justify-content: center;

    border-radius: 50%;

    background: rgba(139,92,246,0.15);

    color: #c4b5fd;

    font-weight: 800;
}


/* ---------- FOOTER ---------- */

.footer {

    text-align: center;

    color: #52525b;

    padding: 60px 0 20px;

    font-size: 13px;
}


</style>
""", unsafe_allow_html=True)


# =========================================================
# HERO
# =========================================================

st.markdown("""
<div class="hero">

    <div class="badge">
        ✦ AI-POWERED CAREER INTELLIGENCE
    </div>

    <div class="hero-title">
        CareerMatch AI
    </div>

    <div class="hero-subtitle">
        Turn your resume into your career advantage.
        Discover how well you match a job, identify missing
        skills, and get an intelligent roadmap to become
        the candidate companies are looking for.
    </div>

</div>
""", unsafe_allow_html=True)


# =========================================================
# FEATURE PILLS
# =========================================================

st.markdown("""
<div class="features">

    <div class="feature">🎯 Smart Job Matching</div>
    <div class="feature">🧠 AI Skill Analysis</div>
    <div class="feature">📊 Resume Intelligence</div>
    <div class="feature">🗺️ Career Roadmap</div>
    <div class="feature">⚡ Instant Analysis</div>

</div>
""", unsafe_allow_html=True)


# =========================================================
# INPUT
# =========================================================

left, right = st.columns(2, gap="large")


with left:

    st.markdown("""
    <div class="glass">

        <div class="card-title">
            📄 Your Resume
        </div>

        <div class="card-description">
            Upload your latest resume in PDF format.
        </div>

    </div>
    """, unsafe_allow_html=True)

    resume_file = st.file_uploader(
        "Drop your resume here",
        type=["pdf"],
        label_visibility="collapsed"
    )


with right:

    st.markdown("""
    <div class="glass">

        <div class="card-title">
            💼 Target Job
        </div>

        <div class="card-description">
            Paste the job description you want to apply for.
        </div>

    </div>
    """, unsafe_allow_html=True)

    job_description = st.text_area(
        "Job description",
        height=210,
        placeholder=(
            "Paste the complete job description here...\n\n"
            "Example:\n"
            "We are looking for a Machine Learning Engineer..."
        ),
        label_visibility="collapsed"
    )


st.markdown("<br>", unsafe_allow_html=True)


# =========================================================
# ANALYZE BUTTON
# =========================================================

analyze = st.button(
    "⚡ Analyze My Career Match",
    use_container_width=True
)


# =========================================================
# ANALYSIS
# =========================================================

if analyze:

    if resume_file is None:

        st.error(
            "📄 Please upload your resume first."
        )

        st.stop()


    if not job_description.strip():

        st.error(
            "💼 Please paste a job description first."
        )

        st.stop()


    with st.spinner("✨ Reading your resume..."):

        resume_text = extract_text_from_pdf(
            resume_file
        )


    if not resume_text:

        st.error(
            "Unable to extract text from this PDF."
        )

        st.stop()


    with st.spinner("🧠 Understanding your skills..."):

        resume_skills = extract_skills(
            resume_text
        )

        job_skills = extract_skills(
            job_description
        )


    with st.spinner("🎯 Calculating your AI match score..."):

        match_score = calculate_match(
            resume_text,
            job_description
        )


    matched, missing, skill_score = analyze_skills(
        resume_skills,
        job_skills
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


    st.markdown(
        '<div class="section-title">Your Career Intelligence</div>',
        unsafe_allow_html=True
    )


    # -----------------------------------------------------
    # TOP METRICS
    # -----------------------------------------------------

    c1, c2, c3 = st.columns(3, gap="medium")


    with c1:

        st.markdown(f"""
        <div class="glass score-container">

            <div class="score">
                {match_score:.0f}%
            </div>

            <div class="score-label">
                AI Job Match
            </div>

        </div>
        """, unsafe_allow_html=True)


    with c2:

        st.markdown(f"""
        <div class="metric-card">

            <div class="metric-number">
                {skill_score:.0f}%
            </div>

            <div class="metric-label">
                SKILLS MATCH
            </div>

        </div>
        """, unsafe_allow_html=True)


    with c3:

        st.markdown(f"""
        <div class="metric-card">

            <div class="metric-number">
                {len(missing)}
            </div>

            <div class="metric-label">
                SKILLS TO LEARN
            </div>

        </div>
        """, unsafe_allow_html=True)


    st.markdown("<br>", unsafe_allow_html=True)


    # -----------------------------------------------------
    # SKILLS
    # -----------------------------------------------------

    skill_left, skill_right = st.columns(2, gap="large")


    with skill_left:

        st.markdown("""
        <div class="glass">

            <div class="card-title">
                🟢 Your Strengths
            </div>

            <div class="card-description">
                Skills found in both your resume and the job.
            </div>

        """, unsafe_allow_html=True)


        if matched:

            for skill in matched:

                st.markdown(
                    f'<span class="skill match">✓ {skill}</span>',
                    unsafe_allow_html=True
                )

        else:

            st.write(
                "No matching skills detected."
            )


        st.markdown("</div>", unsafe_allow_html=True)


    with skill_right:

        st.markdown("""
        <div class="glass">

            <div class="card-title">
                🔴 Your Skill Gaps
            </div>

            <div class="card-description">
                Skills required by the job but missing from your resume.
            </div>

        """, unsafe_allow_html=True)


        if missing:

            for skill in missing:

                st.markdown(
                    f'<span class="skill missing">✕ {skill}</span>',
                    unsafe_allow_html=True
                )

        else:

            st.success(
                "Excellent! No major skill gaps detected."
            )


        st.markdown("</div>", unsafe_allow_html=True)


    # -----------------------------------------------------
    # CHART
    # -----------------------------------------------------

    st.markdown(
        '<div class="section-title">📊 Skill Breakdown</div>',
        unsafe_allow_html=True
    )


    fig = go.Figure()


    fig.add_trace(
        go.Bar(
            x=["Matched Skills", "Missing Skills"],
            y=[len(matched), len(missing)],
            text=[len(matched), len(missing)],
            textposition="auto"
        )
    )


    fig.update_layout(

        template="plotly_dark",

        height=350,

        margin=dict(
            l=20,
            r=20,
            t=30,
            b=20
        ),

        paper_bgcolor="rgba(0,0,0,0)",

        plot_bgcolor="rgba(0,0,0,0)",

        showlegend=False
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )


    # -----------------------------------------------------
    # AI RECOMMENDATION
    # -----------------------------------------------------

    st.markdown(
        '<div class="section-title">🧠 AI Career Verdict</div>',
        unsafe_allow_html=True
    )


    if match_score >= 80:

        message = """
        <div class="glass">

        <h3>🔥 You're a strong candidate.</h3>

        <p style="color:#a1a1aa;">
        Your profile has strong alignment with this position.
        Focus on demonstrating your existing skills through
        projects and measurable achievements.
        </p>

        </div>
        """

    elif match_score >= 60:

        message = """
        <div class="glass">

        <h3>⚡ You're close.</h3>

        <p style="color:#a1a1aa;">
        You have a solid foundation, but improving the missing
        skills below could significantly increase your chances.
        </p>

        </div>
        """

    else:

        message = """
        <div class="glass">

        <h3>🚀 Time to level up.</h3>

        <p style="color:#a1a1aa;">
        There are several skill gaps between your profile and
        this role. Use the roadmap below to systematically
        close them.
        </p>

        </div>
        """


    st.markdown(
        message,
        unsafe_allow_html=True
    )


    # -----------------------------------------------------
    # ROADMAP
    # -----------------------------------------------------

    st.markdown(
        '<div class="section-title">🗺️ Your Skill Roadmap</div>',
        unsafe_allow_html=True
    )


    if missing:

        for i, skill in enumerate(
            missing[:6],
            start=1
        ):

            st.markdown(f"""
            <div class="roadmap">

                <div class="roadmap-number">
                    {i}
                </div>

                <div>
                    <strong>
                        Learn {skill}
                    </strong>

                    <div style="
                        color:#71717a;
                        font-size:12px;
                        margin-top:3px;
                    ">
                        Add this skill to increase your job readiness.
                    </div>

                </div>

            </div>
            """, unsafe_allow_html=True)

    else:

        st.success(
            "🎉 Your detected skills closely match the job requirements!"
        )


# =========================================================
# FOOTER
# =========================================================

st.markdown("""
<div class="footer">

    CareerMatch AI · Built with Python & AI

    <br><br>

    ✦ Analyze · Improve · Get Hired

</div>
""", unsafe_allow_html=True)
