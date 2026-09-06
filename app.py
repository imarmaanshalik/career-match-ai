import streamlit as st
import time
import plotly.graph_objects as go

from src.resume_parser import extract_text_from_pdf
from src.skills import extract_skills
from src.matcher import calculate_match
from src.analyzer import analyze_skills


# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="CareerMatch AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =========================================================
# SESSION STATE
# =========================================================

if "screen" not in st.session_state:
    st.session_state.screen = "home"

if "analyzed" not in st.session_state:
    st.session_state.analyzed = False


# =========================================================
# GLOBAL CSS
# =========================================================

st.markdown(
    """
    <style>

    /* ==============================
       GLOBAL
    ============================== */

    .stApp {

        background:
        radial-gradient(
            circle at 10% 10%,
            rgba(124,58,237,0.18),
            transparent 30%
        ),

        radial-gradient(
            circle at 90% 15%,
            rgba(6,182,212,0.14),
            transparent 30%
        ),

        radial-gradient(
            circle at 50% 100%,
            rgba(37,99,235,0.10),
            transparent 35%
        ),

        #030303;

        color: white;
    }


    .block-container {

        max-width: 1150px;

        padding-top: 25px;

        padding-bottom: 50px;
    }


    header {
        background: transparent !important;
    }


    #MainMenu {
        visibility: hidden;
    }


    footer {
        visibility: hidden;
    }


    /* ==============================
       ANIMATED GLOW
    ============================== */

    .stApp::before {

        content: "";

        position: fixed;

        width: 500px;

        height: 500px;

        border-radius: 50%;

        background:
        radial-gradient(
            circle,
            rgba(124,58,237,0.15),
            transparent 65%
        );

        left: -180px;

        top: 20%;

        animation: floatingGlow 9s ease-in-out infinite;

        pointer-events: none;

        z-index: 0;
    }


    .stApp::after {

        content: "";

        position: fixed;

        width: 450px;

        height: 450px;

        border-radius: 50%;

        background:
        radial-gradient(
            circle,
            rgba(6,182,212,0.12),
            transparent 65%
        );

        right: -180px;

        bottom: 10%;

        animation: floatingGlow2 11s ease-in-out infinite;

        pointer-events: none;

        z-index: 0;
    }


    @keyframes floatingGlow {

        0% {
            transform: translate(0,0);
        }

        50% {
            transform: translate(100px,-80px);
        }

        100% {
            transform: translate(0,0);
        }
    }


    @keyframes floatingGlow2 {

        0% {
            transform: translate(0,0);
        }

        50% {
            transform: translate(-90px,80px);
        }

        100% {
            transform: translate(0,0);
        }
    }


    /* ==============================
       HERO
    ============================== */

    .hero {

        text-align: center;

        padding-top: 75px;

        animation: fadeUp 0.8s ease;
    }


    @keyframes fadeUp {

        from {

            opacity: 0;

            transform: translateY(30px);
        }

        to {

            opacity: 1;

            transform: translateY(0);
        }
    }


    .hero-badge {

        display: inline-block;

        padding: 9px 18px;

        border-radius: 50px;

        border: 1px solid rgba(
            167,
            139,
            250,
            0.25
        );

        background: rgba(
            124,
            58,
            237,
            0.08
        );

        color: #c4b5fd;

        font-size: 13px;

        letter-spacing: 1px;

        margin-bottom: 25px;

        animation: badgePulse 3s infinite;
    }


    @keyframes badgePulse {

        0%,100% {

            box-shadow:
            0 0 0 rgba(
                139,
                92,
                246,
                0
            );
        }

        50% {

            box-shadow:
            0 0 30px rgba(
                139,
                92,
                246,
                0.2
            );
        }
    }


    .hero-title {

        font-size: clamp(
            48px,
            8vw,
            88px
        );

        font-weight: 950;

        line-height: 0.95;

        letter-spacing: -5px;

        background:
        linear-gradient(
            90deg,
            #ffffff,
            #c4b5fd,
            #67e8f9,
            #ffffff
        );

        background-size: 300% auto;

        -webkit-background-clip: text;

        -webkit-text-fill-color: transparent;

        animation:
        gradientMove 6s linear infinite;
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


    .hero-description {

        max-width: 690px;

        margin: 25px auto;

        color: #a1a1aa;

        font-size: 18px;

        line-height: 1.7;
    }


    /* ==============================
       GLASS CARDS
    ============================== */

    .glass {

        background:
        rgba(
            15,
            15,
            15,
            0.72
        );

        border:
        1px solid
        rgba(
            255,
            255,
            255,
            0.08
        );

        border-radius: 24px;

        padding: 28px;

        backdrop-filter: blur(20px);

        box-shadow:
        0 20px 70px
        rgba(0,0,0,0.35);

        transition:
        transform 0.3s,
        border-color 0.3s;
    }


    .glass:hover {

        transform: translateY(-5px);

        border-color:
        rgba(
            167,
            139,
            250,
            0.3
        );
    }


    /* ==============================
       FEATURES
    ============================== */

    .feature-title {

        font-size: 20px;

        font-weight: 800;

        margin-bottom: 8px;
    }


    .feature-text {

        color: #71717a;

        font-size: 14px;

        line-height: 1.6;
    }


    /* ==============================
       STEPS
    ============================== */

    .step {

        text-align: center;

        padding: 12px;

        color: #71717a;
    }


    .step-active {

        color: #c4b5fd;

        font-weight: 800;
    }


    .step-number {

        width: 38px;

        height: 38px;

        margin: auto auto 8px;

        border-radius: 50%;

        display: flex;

        align-items: center;

        justify-content: center;

        background: rgba(
            124,
            58,
            237,
            0.15
        );

        border: 1px solid
        rgba(
            167,
            139,
            250,
            0.25
        );
    }


    /* ==============================
       BUTTON
    ============================== */

    .stButton > button {

        width: 100%;

        border: none;

        border-radius: 15px;

        padding: 15px;

        font-size: 16px;

        font-weight: 800;

        color: white;

        background:
        linear-gradient(
            90deg,
            #7c3aed,
            #2563eb,
            #06b6d4
        );

        box-shadow:
        0 10px 35px
        rgba(
            124,
            58,
            237,
            0.25
        );

        transition: 0.3s;
    }


    .stButton > button:hover {

        transform:
        translateY(-3px)
        scale(1.01);

        box-shadow:
        0 18px 50px
        rgba(
            124,
            58,
            237,
            0.4
        );
    }


    /* ==============================
       SCORE
    ============================== */

    .score-card {

        text-align: center;

        padding: 35px;

        border-radius: 25px;

        background:
        linear-gradient(
            145deg,
            rgba(124,58,237,0.10),
            rgba(6,182,212,0.06)
        );

        border: 1px solid
        rgba(
            167,
            139,
            250,
            0.2
        );
    }


    .score {

        font-size: 90px;

        font-weight: 950;

        background:
        linear-gradient(
            135deg,
            #a78bfa,
            #67e8f9
        );

        -webkit-background-clip: text;

        -webkit-text-fill-color: transparent;

        animation: scorePop 0.9s ease;
    }


    @keyframes scorePop {

        from {

            opacity: 0;

            transform:
            scale(0.5)
            rotate(-8deg);
        }

        to {

            opacity: 1;

            transform:
            scale(1)
            rotate(0);
        }
    }


    .score-label {

        color: #71717a;

        text-transform: uppercase;

        letter-spacing: 3px;

        font-size: 12px;
    }


    /* ==============================
       SKILLS
    ============================== */

    .skill {

        display: inline-block;

        padding: 8px 14px;

        margin: 4px;

        border-radius: 30px;

        background:
        rgba(
            255,
            255,
            255,
            0.04
        );

        border: 1px solid
        rgba(
            255,
            255,
            255,
            0.08
        );

        font-size: 13px;

        transition: 0.25s;
    }


    .skill:hover {

        transform:
        translateY(-4px);

        background:
        rgba(
            124,
            58,
            237,
            0.12
        );
    }


    .green {
        color: #86efac;
    }


    .red {
        color: #fca5a5;
    }


    /* ==============================
       ROADMAP
    ============================== */

    .roadmap {

        display: flex;

        align-items: center;

        padding: 17px;

        margin: 9px 0;

        border-radius: 17px;

        background:
        rgba(
            255,
            255,
            255,
            0.035
        );

        border:
        1px solid
        rgba(
            255,
            255,
            255,
            0.07
        );

        transition: 0.3s;
    }


    .roadmap:hover {

        transform:
        translateX(8px);

        border-color:
        rgba(
            103,
            232,
            249,
            0.3
        );
    }


    .roadmap-number {

        width: 36px;

        height: 36px;

        min-width: 36px;

        display: flex;

        align-items: center;

        justify-content: center;

        border-radius: 50%;

        background:
        rgba(
            124,
            58,
            237,
            0.18
        );

        color: #c4b5fd;

        font-weight: 800;

        margin-right: 15px;
    }


    /* ==============================
       MOBILE
    ============================== */

    @media(max-width: 700px) {

        .hero {

            padding-top: 30px;
        }

        .hero-title {

            font-size: 50px;

            letter-spacing: -3px;
        }

        .hero-description {

            font-size: 15px;
        }

        .score {

            font-size: 65px;
        }

    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# HOME SCREEN
# =========================================================

if st.session_state.screen == "home":

    st.markdown(
        """
        <div class="hero">

            <div class="hero-badge">
                ✦ AI-POWERED CAREER INTELLIGENCE
            </div>

            <div class="hero-title">
                CareerMatch AI
            </div>

            <div class="hero-description">
                Your resume tells your story.
                We help you make sure companies
                see the right one.
                <br>
                Discover your job match,
                identify skill gaps, and build
                your path to your dream role.
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


    st.write("")


    if st.button(
        "🚀 CHECK MY JOB MATCH",
        use_container_width=True
    ):

        st.session_state.screen = "analyze"

        st.rerun()


    st.write("")


    # FEATURES

    c1, c2, c3 = st.columns(3)


    with c1:

        st.markdown(
            """
            <div class="glass">

                <div class="feature-title">
                    🎯 Smart Matching
                </div>

                <div class="feature-text">
                    Compare your resume with
                    real job requirements using
                    semantic AI matching.
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    with c2:

        st.markdown(
            """
            <div class="glass">

                <div class="feature-title">
                    🧠 Skill Intelligence
                </div>

                <div class="feature-text">
                    Discover the skills you already
                    have and the skills you need
                    to become job-ready.
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    with c3:

        st.markdown(
            """
            <div class="glass">

                <div class="feature-title">
                    🗺️ Career Roadmap
                </div>

                <div class="feature-text">
                    Get a personalized learning
                    roadmap based on the job
                    you want.
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    st.markdown(
        """
        <div style="
            text-align:center;
            margin-top:70px;
            color:#52525b;
            font-size:13px;
        ">
            Analyze • Improve • Get Hired
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# ANALYZE SCREEN
# =========================================================

elif st.session_state.screen == "analyze":

    st.markdown(
        "<h1 style='text-align:center;'>Let's find your match.</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <p style="
            text-align:center;
            color:#71717a;
        ">
        It takes less than a minute.
        </p>
        """,
        unsafe_allow_html=True
    )


    # STEPS

    s1, s2, s3 = st.columns(3)


    with s1:

        st.markdown(
            """
            <div class="step step-active">

            <div class="step-number">
            1
            </div>

            📄 Resume

            </div>
            """,
            unsafe_allow_html=True
        )


    with s2:

        st.markdown(
            """
            <div class="step">

            <div class="step-number">
            2
            </div>

            💼 Job

            </div>
            """,
            unsafe_allow_html=True
        )


    with s3:

        st.markdown(
            """
            <div class="step">

            <div class="step-number">
            3
            </div>

            🎯 Results

            </div>
            """,
            unsafe_allow_html=True
        )


    st.write("")


    left, right = st.columns(
        2,
        gap="large"
    )


    with left:

        st.markdown(
            """
            <div class="glass">

            <div class="feature-title">
            📄 Upload Resume
            </div>

            <div class="feature-text">
            Upload your latest resume as a PDF.
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )


        resume_file = st.file_uploader(
            "Resume",
            type=["pdf"],
            label_visibility="collapsed"
        )


    with right:

        st.markdown(
            """
            <div class="glass">

            <div class="feature-title">
            💼 Target Job
            </div>

            <div class="feature-text">
            Paste the job description you
            want to apply for.
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )


        job_description = st.text_area(
            "Job description",
            height=220,
            placeholder=(
                "Paste the complete job description here..."
            ),
            label_visibility="collapsed"
        )


    st.write("")


    if st.button(
        "⚡ ANALYZE MY CAREER",
        use_container_width=True
    ):

        if resume_file is None:

            st.error(
                "📄 Please upload your resume."
            )

            st.stop()


        if not job_description.strip():

            st.error(
                "💼 Please paste the job description."
            )

            st.stop()


        # Move to analyzing state

        st.session_state.screen = "processing"

        st.session_state.resume_file = resume_file

        st.session_state.job_description = job_description

        st.rerun()


# =========================================================
# PROCESSING SCREEN
# =========================================================

elif st.session_state.screen == "processing":

    st.markdown(
        """
        <div class="hero">

            <div class="hero-badge">
                ✦ AI ENGINE ACTIVE
            </div>

            <div class="hero-title">
                Analyzing...
            </div>

            <div class="hero-description">
                Our AI is understanding your experience,
                skills and the requirements of this role.
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


    progress = st.progress(0)


    status = st.empty()


    status.markdown(
        "📄 **Reading your resume...**"
    )

    time.sleep(0.8)

    resume_text = extract_text_from_pdf(
        st.session_state.resume_file
    )

    progress.progress(25)


    status.markdown(
        "🧠 **Understanding your skills...**"
    )

    time.sleep(0.8)

    resume_skills = extract_skills(
        resume_text
    )

    job_skills = extract_skills(
        st.session_state.job_description
    )

    progress.progress(50)


    status.markdown(
        "🎯 **Calculating semantic job match...**"
    )

    time.sleep(0.8)

    match_score = calculate_match(
        resume_text,
        st.session_state.job_description
    )

    progress.progress(75)


    status.markdown(
        "📊 **Generating your career insights...**"
    )

    time.sleep(0.8)

    matched, missing, skill_score = analyze_skills(
        resume_skills,
        job_skills
    )

    progress.progress(100)

    time.sleep(0.5)


    # Save results

    st.session_state.match_score = match_score

    st.session_state.matched = matched

    st.session_state.missing = missing

    st.session_state.skill_score = skill_score

    st.session_state.analyzed = True

    st.session_state.screen = "results"

    st.rerun()


# =========================================================
# RESULTS SCREEN
# =========================================================

elif st.session_state.screen == "results":

    match_score = st.session_state.match_score

    matched = st.session_state.matched

    missing = st.session_state.missing

    skill_score = st.session_state.skill_score


    st.markdown(
        """
        <div class="hero" style="padding-top:20px;">

            <div class="hero-badge">
                ✦ ANALYSIS COMPLETE
            </div>

            <div class="hero-title">
                Here's your result.
            </div>

            <div class="hero-description">
                Your resume has been compared
                with the target role.
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


    st.write("")


    # SCORE

    st.markdown(
        f"""
        <div class="score-card">

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


    st.write("")


    # METRICS

    c1, c2, c3 = st.columns(3)


    with c1:

        st.metric(
            "🎯 Job Match",
            f"{match_score:.0f}%"
        )


    with c2:

        st.metric(
            "🧠 Skills Match",
            f"{skill_score:.0f}%"
        )


    with c3:

        st.metric(
            "📚 Skills to Learn",
            len(missing)
        )


    st.write("")


    # SKILLS

    left, right = st.columns(
        2,
        gap="large"
    )


    with left:

        st.markdown(
            """
            <div class="glass">

            <div class="feature-title">
            🟢 Your Strengths
            </div>

            <div class="feature-text">
            Skills that match the job requirements.
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )


        if matched:

            for skill in matched:

                st.markdown(
                    f"""
                    <span class="skill green">
                    ✓ {skill}
                    </span>
                    """,
                    unsafe_allow_html=True
                )

        else:

            st.info(
                "No matching skills detected."
            )


    with right:

        st.markdown(
            """
            <div class="glass">

            <div class="feature-title">
            🔴 Skill Gaps
            </div>

            <div class="feature-text">
            Skills required by the job that
            weren't detected in your resume.
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )


        if missing:

            for skill in missing:

                st.markdown(
                    f"""
                    <span class="skill red">
                    ✕ {skill}
                    </span>
                    """,
                    unsafe_allow_html=True
                )

        else:

            st.success(
                "🎉 No major skill gaps detected!"
            )


    st.write("")


    # CHART

    st.subheader(
        "📊 Your Skill Breakdown"
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


    # CAREER VERDICT

    st.subheader(
        "🧠 Career Verdict"
    )


    if match_score >= 80:

        st.success(
            "🔥 Excellent match! "
            "Your current profile strongly "
            "aligns with this position."
        )

    elif match_score >= 60:

        st.warning(
            "⚡ Good match! "
            "You have a solid foundation. "
            "Work on the missing skills to "
            "strengthen your application."
        )

    else:

        st.error(
            "🚀 There are several skill gaps. "
            "Follow the roadmap below to "
            "become more job-ready."
        )


    # ROADMAP

    st.subheader(
        "🗺️ Your Career Roadmap"
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

                    <small style="color:#71717a;">
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
            "this position."
        )


    st.write("")


    # START AGAIN

    if st.button(
        "🔄 ANALYZE ANOTHER JOB",
        use_container_width=True
    ):

        st.session_state.screen = "analyze"

        st.rerun()


    st.markdown(
        """
        <div style="
            text-align:center;
            color:#52525b;
            margin-top:50px;
        ">
        CareerMatch AI · Analyze • Improve • Get Hired
        </div>
        """,
        unsafe_allow_html=True
    )

