
import io
import re
from datetime import datetime

import streamlit as st
import time
import plotly.graph_objects as go

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)

from src.resume_parser import extract_text_from_pdf
from src.skills import extract_skills
from src.matcher import calculate_match
from src.analyzer import analyze_skills


# =========================================================
# RESUME IMPROVEMENT SUGGESTIONS (inlined, no external API)
# =========================================================

ACTION_VERBS = [
    "led", "built", "designed", "developed", "implemented",
    "optimized", "managed", "created", "improved", "launched",
    "delivered", "automated", "architected", "spearheaded", "drove",
]

WEAK_PHRASES = [
    "responsible for", "worked on", "helped with", "involved in",
]


def generate_resume_tips(resume_text, matched_skills, missing_skills, match_score):
    """
    Return a list of short, actionable tip strings.

    Parameters
    ----------
    resume_text : str
    matched_skills : list[str]
    missing_skills : list[str]
    match_score : float  (0-100)
    """
    tips = []
    text_lower = resume_text.lower()
    word_count = len(resume_text.split())

    # Length check
    if word_count < 150:
        tips.append(
            f"Your resume looks quite short (~{word_count} words). Add more "
            "detail about your projects, responsibilities, and measurable "
            "achievements — recruiters and ATS systems reward specificity."
        )
    elif word_count > 900:
        tips.append(
            "Your resume is fairly long. Consider trimming it to the most "
            "relevant 1-2 pages so recruiters see your strongest points first."
        )

    # Missing skills
    if missing_skills:
        top_missing = missing_skills[:5]
        tips.append(
            "Add visible experience with: " + ", ".join(top_missing) + ". "
            "Even a personal project, certification, or coursework can help "
            "you pass keyword-based ATS filters for this role."
        )

    # Action verbs
    verb_hits = sum(1 for v in ACTION_VERBS if v in text_lower)
    if verb_hits < 3:
        tips.append(
            "Use more strong action verbs (e.g. 'led', 'built', 'optimized', "
            "'launched') at the start of your bullet points instead of "
            "passive descriptions — it makes achievements stand out."
        )

    # Weak phrasing
    weak_hits = [p for p in WEAK_PHRASES if p in text_lower]
    if weak_hits:
        tips.append(
            "Replace vague phrases like \"" + weak_hits[0] + "\" with a "
            "specific outcome — say what you actually did and what changed "
            "as a result."
        )

    # Quantifiable results
    has_numbers = bool(re.search(r"\d", resume_text))
    if not has_numbers:
        tips.append(
            "Add quantifiable results (e.g. 'reduced load time by 30%', "
            "'managed a team of 5', 'grew signups by 2x'). Numbers make "
            "achievements far more credible and memorable."
        )

    # Overall match
    if match_score < 60:
        tips.append(
            "Your overall match is below 60%. Mirror more of the target "
            "role's own language in your summary and skills section — "
            "many ATS tools score on keyword overlap."
        )

    # Strengths to highlight
    if matched_skills:
        tips.append(
            "You already show strength in: " + ", ".join(matched_skills[:5]) +
            ". Make sure these appear near the top of your resume — in the "
            "summary or a dedicated skills section — so they're seen first."
        )

    if not tips:
        tips.append(
            "Your resume looks well-aligned with this role. Do a final "
            "proofread and confirm the formatting is ATS-friendly (avoid "
            "text inside images or tables)."
        )

    return tips


def generate_combined_tips(resume_text, results_list):
    """
    Aggregate tips across multiple job comparisons (used in compare mode).
    Deduplicates missing skills across jobs and uses the best match score
    as the baseline for the 'overall match' tip.
    """
    if not results_list:
        return []

    all_missing = []
    all_matched = []
    for res in results_list:
        for s in res.get("missing", []):
            if s not in all_missing:
                all_missing.append(s)
        for s in res.get("matched", []):
            if s not in all_matched:
                all_matched.append(s)

    best_score = max(r["match_score"] for r in results_list)

    return generate_resume_tips(
        resume_text=resume_text,
        matched_skills=all_matched,
        missing_skills=all_missing,
        match_score=best_score,
    )


# =========================================================
# PDF REPORT GENERATOR (inlined, uses reportlab)
# =========================================================

# =========================================================
# COMPANY SUGGESTIONS (role inference + illustrative hiring guide)
# =========================================================
#
# NOTE: This maps detected resume skills to common tech/business roles,
# then to companies broadly known to hire for that role. It is a general
# industry reference — not a live job board — so scores/companies are
# illustrative, not scraped from real-time postings.

ROLE_SKILL_MAP = {
    "Software Engineer": [
        "python", "java", "c++", "c#", "algorithms", "data structures",
        "git", "sql", "oop", "system design",
    ],
    "Data Scientist": [
        "python", "machine learning", "statistics", "pandas", "numpy",
        "sql", "tensorflow", "pytorch", "data science", "r",
    ],
    "Data Analyst": [
        "excel", "sql", "tableau", "power bi", "statistics", "python",
        "data analysis", "data visualization",
    ],
    "Frontend Developer": [
        "javascript", "react", "html", "css", "vue", "angular",
        "typescript", "redux", "next.js",
    ],
    "Backend Developer": [
        "node.js", "python", "java", "sql", "api", "django", "flask",
        "spring", "rest", "microservices",
    ],
    "Full Stack Developer": [
        "javascript", "react", "node.js", "mongodb", "express", "html",
        "css", "sql", "rest api",
    ],
    "DevOps Engineer": [
        "docker", "kubernetes", "aws", "ci/cd", "jenkins", "terraform",
        "linux", "ansible", "azure", "gcp",
    ],
    "Cloud Engineer": [
        "aws", "azure", "gcp", "cloud", "terraform", "kubernetes",
        "cloud computing", "docker",
    ],
    "Machine Learning Engineer": [
        "python", "tensorflow", "pytorch", "machine learning",
        "deep learning", "nlp", "computer vision", "scikit-learn",
    ],
    "Product Manager": [
        "agile", "scrum", "roadmap", "stakeholder management", "jira",
        "product strategy", "market research",
    ],
    "UI/UX Designer": [
        "figma", "sketch", "adobe xd", "wireframing", "prototyping",
        "user research", "ui design", "ux design",
    ],
    "Cybersecurity Analyst": [
        "security", "penetration testing", "network security", "siem",
        "firewall", "cybersecurity", "vulnerability assessment",
    ],
    "QA Engineer": [
        "testing", "selenium", "automation testing", "qa", "test cases",
        "manual testing", "cypress",
    ],
    "Mobile Developer": [
        "android", "ios", "swift", "kotlin", "react native", "flutter",
        "mobile development",
    ],
    "Business Analyst": [
        "excel", "sql", "business analysis", "requirements gathering",
        "stakeholder management", "power bi", "process improvement",
    ],
}

ROLE_COMPANIES_MAP = {
    "Software Engineer": ["Google", "Microsoft", "Amazon", "Meta", "Apple", "Netflix"],
    "Data Scientist": ["Google", "Amazon", "Netflix", "Meta", "IBM", "Uber"],
    "Data Analyst": ["Deloitte", "Accenture", "EY", "Amazon", "IBM", "Flipkart"],
    "Frontend Developer": ["Google", "Adobe", "Airbnb", "Shopify", "Meta"],
    "Backend Developer": ["Amazon", "Microsoft", "Uber", "Stripe", "Twilio"],
    "Full Stack Developer": ["Amazon", "Flipkart", "Swiggy", "Zomato", "Paytm"],
    "DevOps Engineer": ["Amazon Web Services", "Google Cloud", "Microsoft", "Netflix", "Atlassian"],
    "Cloud Engineer": ["AWS", "Microsoft Azure", "Google Cloud", "IBM Cloud", "Oracle"],
    "Machine Learning Engineer": ["Google DeepMind", "OpenAI", "NVIDIA", "Amazon", "Meta"],
    "Product Manager": ["Google", "Amazon", "Microsoft", "Flipkart", "Zomato"],
    "UI/UX Designer": ["Adobe", "Google", "Airbnb", "Figma", "Zomato"],
    "Cybersecurity Analyst": ["IBM", "Cisco", "Palo Alto Networks", "Deloitte", "Accenture"],
    "QA Engineer": ["Infosys", "TCS", "Wipro", "Amazon", "Cognizant"],
    "Mobile Developer": ["Google", "Apple", "Uber", "Swiggy", "PhonePe"],
    "Business Analyst": ["Deloitte", "EY", "KPMG", "Accenture", "TCS"],
}


def infer_matching_roles(resume_skills, top_n=3):
    """
    Score each known role by how many of its associated skills overlap
    with the resume's detected skills. Returns the top N roles that had
    at least one overlapping skill, sorted by overlap count (desc).
    """
    resume_skills_lower = {s.lower().strip() for s in resume_skills}

    scored_roles = []
    for role, role_skills in ROLE_SKILL_MAP.items():
        overlap = [s for s in role_skills if s in resume_skills_lower]
        if overlap:
            scored_roles.append({
                "role": role,
                "overlap_count": len(overlap),
                "overlap_skills": overlap,
            })

    scored_roles.sort(key=lambda r: r["overlap_count"], reverse=True)
    return scored_roles[:top_n]


def suggest_companies(resume_skills, top_n_roles=3, companies_per_role=5):
    """
    Returns a list of dicts: {role, overlap_skills, companies}
    for the best-matching roles based on detected resume skills.
    """
    matching_roles = infer_matching_roles(resume_skills, top_n=top_n_roles)

    suggestions = []
    for entry in matching_roles:
        role = entry["role"]
        companies = ROLE_COMPANIES_MAP.get(role, [])[:companies_per_role]
        suggestions.append({
            "role": role,
            "overlap_skills": entry["overlap_skills"],
            "companies": companies,
        })

    return suggestions


def generate_pdf_report(resume_name, results_list, tips, company_suggestions=None):
    """
    Parameters
    ----------
    resume_name : str
        Display name of the resume file (for the header).
    results_list : list[dict]
        Each dict: {"label": str, "match_score": float,
                     "skill_score": float, "matched": list[str],
                     "missing": list[str]}
    tips : list[str]

    Returns
    -------
    bytes  -- the PDF file content
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CMTitle", parent=styles["Title"],
        textColor=colors.HexColor("#7c3aed"), fontSize=24,
    )
    subtitle_style = ParagraphStyle(
        "CMSubtitle", parent=styles["Normal"],
        textColor=colors.HexColor("#71717a"), fontSize=10,
    )
    heading_style = ParagraphStyle(
        "CMHeading", parent=styles["Heading2"],
        textColor=colors.HexColor("#2563eb"), spaceBefore=14, spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "CMBody", parent=styles["Normal"], fontSize=10.5, leading=15,
    )
    tip_style = ParagraphStyle(
        "CMTip", parent=styles["Normal"], fontSize=10.5, leading=15,
        leftIndent=12, spaceAfter=6,
    )

    story = []

    story.append(Paragraph("CareerMatch AI — Analysis Report", title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"Resume: {resume_name}  |  Generated: "
        f"{datetime.now().strftime('%B %d, %Y %I:%M %p')}",
        subtitle_style,
    ))
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#e4e4e7")))

    # Summary table if comparing multiple jobs
    if len(results_list) > 1:
        story.append(Paragraph("Comparison Summary", heading_style))
        table_data = [["Job", "Job Match", "Skill Match", "Gaps"]]
        for res in results_list:
            table_data.append([
                res.get("label", "Job"),
                f"{res['match_score']:.0f}%",
                f"{res['skill_score']:.0f}%",
                str(len(res.get("missing", []))),
            ])
        table = Table(table_data, hAlign="LEFT", colWidths=[2.6*inch, 1.2*inch, 1.2*inch, 0.9*inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7c3aed")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9.5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e4e4e7")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f4f5")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(table)
        story.append(Spacer(1, 10))

    # Per-job detail
    for idx, res in enumerate(results_list, start=1):
        label = res.get("label") or f"Job {idx}"
        story.append(Paragraph(label, heading_style))
        story.append(Paragraph(
            f"<b>Job Match:</b> {res['match_score']:.0f}%&nbsp;&nbsp;&nbsp;"
            f"<b>Skill Match:</b> {res['skill_score']:.0f}%",
            body_style,
        ))
        story.append(Spacer(1, 4))

        matched_str = ", ".join(res.get("matched", [])) or "None detected"
        missing_str = ", ".join(res.get("missing", [])) or "None — great coverage"

        story.append(Paragraph(f"<b>Strengths:</b> {matched_str}", body_style))
        story.append(Spacer(1, 3))
        story.append(Paragraph(f"<b>Skill Gaps:</b> {missing_str}", body_style))
        story.append(Spacer(1, 10))

    story.append(HRFlowable(width="100%", color=colors.HexColor("#e4e4e7")))
    story.append(Paragraph("Resume Improvement Tips", heading_style))
    for tip in tips:
        story.append(Paragraph(f"• {tip}", tip_style))

    if company_suggestions:
        story.append(HRFlowable(width="100%", color=colors.HexColor("#e4e4e7")))
        story.append(Paragraph("Companies That Might Hire You", heading_style))
        story.append(Paragraph(
            "Based on your detected skills, here are roles you're a strong "
            "fit for and companies commonly known to hire for them. This is "
            "a general industry guide, not a live list of open positions — "
            "check each company's careers page for current openings.",
            body_style,
        ))
        story.append(Spacer(1, 8))
        for sug in company_suggestions:
            story.append(Paragraph(f"<b>{sug['role']}</b>", body_style))
            story.append(Paragraph(
                "Companies: " + ", ".join(sug["companies"]), body_style
            ))
            story.append(Spacer(1, 8))

    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "Generated by CareerMatch AI — Analyze • Improve • Get Hired",
        subtitle_style,
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="CareerMatch AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

MAX_RESUME_SIZE_MB = 10
MIN_JOB_DESCRIPTION_CHARS = 50
MAX_JOBS_TO_COMPARE = 3

# =========================================================
# SESSION STATE
# =========================================================

if "screen" not in st.session_state:
    st.session_state.screen = "home"

if "analyzed" not in st.session_state:
    st.session_state.analyzed = False

if "history" not in st.session_state:
    st.session_state.history = []

if "num_jobs" not in st.session_state:
    st.session_state.num_jobs = 1

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
        0% { transform: translate(0,0); }
        50% { transform: translate(100px,-80px); }
        100% { transform: translate(0,0); }
    }

    @keyframes floatingGlow2 {
        0% { transform: translate(0,0); }
        50% { transform: translate(-90px,80px); }
        100% { transform: translate(0,0); }
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
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .hero-badge {
        display: inline-block;
        padding: 9px 18px;
        border-radius: 50px;
        border: 1px solid rgba(167,139,250,0.25);
        background: rgba(124,58,237,0.08);
        color: #c4b5fd;
        font-size: 13px;
        letter-spacing: 1px;
        margin-bottom: 25px;
        animation: badgePulse 3s infinite, fadeInUp 0.7s cubic-bezier(0.16, 1, 0.3, 1) both;
    }

    @keyframes badgePulse {
        0%,100% { box-shadow: 0 0 0 rgba(139,92,246,0); }
        50% { box-shadow: 0 0 30px rgba(139,92,246,0.2); }
    }

    .hero-title {
        font-size: clamp(48px, 8vw, 88px);
        font-weight: 950;
        line-height: 0.95;
        letter-spacing: -5px;
        background: linear-gradient(90deg, #ffffff, #c4b5fd, #67e8f9, #ffffff);
        background-size: 300% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradientMove 6s linear infinite, fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) 0.15s both;
    }

    @keyframes gradientMove {
        0% { background-position: 0%; }
        50% { background-position: 100%; }
        100% { background-position: 0%; }
    }

    .hero-description {
        max-width: 690px;
        margin: 25px auto;
        color: #a1a1aa;
        font-size: 18px;
        line-height: 1.7;
        animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) 0.3s both;
    }

    /* ==============================
       GLASS CARDS
    ============================== */

    .glass {
        background: rgba(15,15,15,0.72);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 24px;
        padding: 28px;
        backdrop-filter: blur(20px);
        box-shadow: 0 20px 70px rgba(0,0,0,0.35);
        transition: transform 0.3s, border-color 0.3s;
    }

    .glass:hover {
        transform: translateY(-5px);
        border-color: rgba(167,139,250,0.3);
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
        background: rgba(124,58,237,0.15);
        border: 1px solid rgba(167,139,250,0.25);
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
        background: linear-gradient(90deg, #7c3aed, #2563eb, #06b6d4);
        box-shadow: 0 10px 35px rgba(124,58,237,0.25);
        transition: 0.3s;
    }

    .stButton > button:hover {
        transform: translateY(-3px) scale(1.01);
        box-shadow: 0 18px 50px rgba(124,58,237,0.4);
    }

    .stDownloadButton > button {
        width: 100%;
        border: none;
        border-radius: 15px;
        padding: 15px;
        font-size: 16px;
        font-weight: 800;
        color: white;
        background: linear-gradient(90deg, #06b6d4, #2563eb);
        box-shadow: 0 10px 35px rgba(6,182,212,0.25);
        transition: 0.3s;
    }

    .stDownloadButton > button:hover {
        transform: translateY(-3px) scale(1.01);
        box-shadow: 0 18px 50px rgba(6,182,212,0.4);
    }

    /* ==============================
       SCORE
    ============================== */

    .score-card {
        text-align: center;
        padding: 35px;
        border-radius: 25px;
        background: linear-gradient(145deg, rgba(124,58,237,0.10), rgba(6,182,212,0.06));
        border: 1px solid rgba(167,139,250,0.2);
    }

    .score {
        font-size: 90px;
        font-weight: 950;
        background: linear-gradient(135deg, #a78bfa, #67e8f9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: scorePop 0.9s ease;
    }

    @keyframes scorePop {
        from { opacity: 0; transform: scale(0.5) rotate(-8deg); }
        to { opacity: 1; transform: scale(1) rotate(0); }
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
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        font-size: 13px;
        transition: 0.25s;
    }

    .skill:hover {
        transform: translateY(-4px);
        background: rgba(124,58,237,0.12);
    }

    .green { color: #86efac; }
    .red { color: #fca5a5; }

    /* ==============================
       ROADMAP
    ============================== */

    .roadmap {
        display: flex;
        align-items: center;
        padding: 17px;
        margin: 9px 0;
        border-radius: 17px;
        background: rgba(255,255,255,0.035);
        border: 1px solid rgba(255,255,255,0.07);
        transition: 0.3s;
    }

    .roadmap:hover {
        transform: translateX(8px);
        border-color: rgba(103,232,249,0.3);
    }

    .roadmap-number {
        width: 36px;
        height: 36px;
        min-width: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        background: rgba(124,58,237,0.18);
        color: #c4b5fd;
        font-weight: 800;
        margin-right: 15px;
    }

    /* ==============================
       TIPS
    ============================== */

    .tip-card {
        display: flex;
        align-items: flex-start;
        padding: 16px;
        margin: 9px 0;
        border-radius: 17px;
        background: rgba(103,232,249,0.04);
        border: 1px solid rgba(103,232,249,0.15);
    }

    .tip-icon {
        font-size: 18px;
        margin-right: 12px;
    }

    .tip-text {
        color: #d4d4d8;
        font-size: 14.5px;
        line-height: 1.6;
    }

    /* ==============================
       HISTORY
    ============================== */

    .history-card {
        padding: 18px 22px;
        margin: 10px 0;
        border-radius: 17px;
        background: rgba(255,255,255,0.035);
        border: 1px solid rgba(255,255,255,0.07);
    }

    .history-meta {
        color: #71717a;
        font-size: 12.5px;
        letter-spacing: 0.5px;
    }

    .best-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 30px;
        background: rgba(134,239,172,0.12);
        border: 1px solid rgba(134,239,172,0.3);
        color: #86efac;
        font-size: 12px;
        font-weight: 700;
        margin-left: 8px;
    }

    /* ==============================
       ENTRANCE + AMBIENT ANIMATION
    ============================== */

    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(22px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .fade-in-up {
        opacity: 0;
        animation: fadeInUp 0.7s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }

    @keyframes sparkleFloat {
        0%, 100% { transform: translateY(0) scale(1); opacity: 0.25; }
        50% { transform: translateY(-18px) scale(1.4); opacity: 0.9; }
    }

    .sparkle-field {
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        overflow: hidden;
    }

    .sparkle {
        position: absolute;
        width: 4px;
        height: 4px;
        border-radius: 50%;
        background: #c4b5fd;
        box-shadow: 0 0 8px 2px rgba(196,181,253,0.6);
        animation: sparkleFloat 4.5s ease-in-out infinite;
    }

    .sparkle:nth-child(odd) {
        background: #67e8f9;
        box-shadow: 0 0 8px 2px rgba(103,232,249,0.6);
    }

    /* Button shine sweep on hover */
    .stButton > button, .stDownloadButton > button {
        position: relative;
        overflow: hidden;
    }

    .stButton > button::after, .stDownloadButton > button::after {
        content: "";
        position: absolute;
        top: 0;
        left: -75%;
        width: 50%;
        height: 100%;
        background: linear-gradient(
            120deg,
            transparent,
            rgba(255,255,255,0.35),
            transparent
        );
        transform: skewX(-20deg);
        transition: left 0.6s ease;
    }

    .stButton > button:hover::after, .stDownloadButton > button:hover::after {
        left: 130%;
    }

    /* Score card ambient glow pulse */
    @keyframes cardGlowPulse {
        0%, 100% { box-shadow: 0 0 0 rgba(124,58,237,0); }
        50% { box-shadow: 0 0 55px rgba(124,58,237,0.25); }
    }

    .score-card {
        animation: cardGlowPulse 3.5s ease-in-out infinite;
    }

    /* Active step pulsing ring */
    @keyframes ringPulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(167,139,250,0.4); }
        50% { box-shadow: 0 0 0 8px rgba(167,139,250,0); }
    }

    .step-active .step-number {
        animation: ringPulse 2s ease-in-out infinite;
    }

    /* Typewriter tagline */
    @keyframes typing {
        from { width: 0; }
        to { width: 100%; }
    }

    @keyframes blinkCursor {
        50% { border-color: transparent; }
    }

    .tagline-type {
        display: inline-block;
        overflow: hidden;
        white-space: nowrap;
        border-right: 2px solid #67e8f9;
        margin: 0 auto;
        animation:
            typing 2.4s steps(30, end) 0.4s both,
            blinkCursor 0.75s step-end infinite;
    }

    /* Processing screen spinner + bouncing dots */
    @keyframes spinPulse {
        0% { transform: rotate(0deg) scale(1); }
        50% { transform: rotate(180deg) scale(1.15); }
        100% { transform: rotate(360deg) scale(1); }
    }

    .spinner-icon {
        display: inline-block;
        font-size: 34px;
        animation: spinPulse 2.2s ease-in-out infinite;
    }

    @keyframes bounceDot {
        0%, 80%, 100% { transform: translateY(0); opacity: 0.5; }
        40% { transform: translateY(-10px); opacity: 1; }
    }

    .loading-dots span {
        display: inline-block;
        width: 8px;
        height: 8px;
        margin: 0 4px;
        border-radius: 50%;
        background: linear-gradient(135deg, #a78bfa, #67e8f9);
        animation: bounceDot 1.2s ease-in-out infinite;
    }

    .loading-dots span:nth-child(2) { animation-delay: 0.15s; }
    .loading-dots span:nth-child(3) { animation-delay: 0.3s; }

    /* Extra glow on card hover, layered on top of existing transform */
    .glass:hover {
        box-shadow: 0 20px 70px rgba(0,0,0,0.35), 0 0 40px rgba(124,58,237,0.18);
    }

    /* Company / skill chip pop-in hover */
    .skill {
        animation: fadeInUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
    }

    /* ==============================
       MOBILE
    ============================== */

    @media(max-width: 700px) {
        .hero { padding-top: 30px; }
        .hero-title { font-size: 50px; letter-spacing: -3px; }
        .hero-description { font-size: 15px; }
        .score { font-size: 65px; }
    }

    </style>
    """,
    unsafe_allow_html=True
)

# Ambient sparkle field (decorative, purely visual, sits behind all content)
_SPARKLE_POSITIONS = [
    (6, 12, 0.0, 4.0), (18, 78, 0.8, 5.2), (32, 34, 1.4, 3.8),
    (47, 91, 0.3, 4.6), (61, 8, 1.9, 5.0), (74, 55, 0.6, 4.2),
    (85, 25, 1.1, 3.6), (93, 70, 1.7, 4.8), (12, 60, 2.2, 4.0),
    (55, 45, 0.9, 5.4),
]
_sparkle_html = '<div class="sparkle-field">' + "".join(
    f'<span class="sparkle" style="top:{t}%; left:{l}%; '
    f'animation-delay:{d}s; animation-duration:{dur}s;"></span>'
    for t, l, d, dur in _SPARKLE_POSITIONS
) + "</div>"
st.markdown(_sparkle_html, unsafe_allow_html=True)


def go_to_analyze_with_error(message):
    """Send the user back to the analyze screen with an error message."""
    st.session_state.screen = "analyze"
    st.session_state.pipeline_error = message
    st.rerun()


def render_top_nav(active_screen):
    """Small top-right nav so users can jump to History from anywhere."""
    cols = st.columns([6, 1, 1])
    with cols[1]:
        if active_screen != "home":
            if st.button("🏠 Home", key=f"nav_home_{active_screen}"):
                st.session_state.screen = "home"
                st.rerun()
    with cols[2]:
        if active_screen != "history":
            label = f"📜 History ({len(st.session_state.history)})"
            if st.button(label, key=f"nav_history_{active_screen}"):
                st.session_state.screen = "history"
                st.rerun()

# =========================================================
# HOME SCREEN
# =========================================================

if st.session_state.screen == "home":

    render_top_nav("home")

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
        """, unsafe_allow_html=True)

    st.write("")

    if st.button(
        "🚀 CHECK MY JOB MATCH",
        use_container_width=True
    ):
        st.session_state.screen = "analyze"
        st.rerun()

    st.write("")

    # FEATURES
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            """
            <div class="glass fade-in-up" style="animation-delay:0s;">
                <div class="feature-title">🎯 Smart Matching</div>
                <div class="feature-text">
                    Compare your resume with real job requirements
                    using semantic AI matching.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            """
            <div class="glass fade-in-up" style="animation-delay:0.12s;">
                <div class="feature-title">🧠 Skill Intelligence</div>
                <div class="feature-text">
                    Discover the skills you already have and the
                    skills you need to become job-ready.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c3:
        st.markdown(
            """
            <div class="glass fade-in-up" style="animation-delay:0.24s;">
                <div class="feature-title">⚖️ Compare Jobs</div>
                <div class="feature-text">
                    Check your resume against up to 3 job postings
                    at once and see which fits best.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c4:
        st.markdown(
            """
            <div class="glass fade-in-up" style="animation-delay:0.36s;">
                <div class="feature-title">📄 PDF Reports</div>
                <div class="feature-text">
                    Download a polished report of your match score,
                    skill gaps, and improvement tips.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        """
        <div style="text-align:center; margin-top:70px; color:#52525b; font-size:13px;">
            <span class="tagline-type">Analyze • Improve • Get Hired</span>
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================================================
# ANALYZE SCREEN
# =========================================================

elif st.session_state.screen == "analyze":

    render_top_nav("analyze")

    st.markdown(
        "<h1 style='text-align:center;'>Let's find your match.</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <p style="text-align:center; color:#71717a;">
        It takes less than a minute.
        </p>
        """,
        unsafe_allow_html=True
    )

    if st.session_state.get("pipeline_error"):
        st.error(st.session_state.pipeline_error)
        st.session_state.pipeline_error = None

    # STEPS
    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown(
            """<div class="step step-active"><div class="step-number">1</div>
            📄 Resume</div>""",
            unsafe_allow_html=True
        )
    with s2:
        st.markdown(
            """<div class="step"><div class="step-number">2</div>
            💼 Job</div>""",
            unsafe_allow_html=True
        )
    with s3:
        st.markdown(
            """<div class="step"><div class="step-number">3</div>
            🎯 Results</div>""",
            unsafe_allow_html=True
        )

    st.write("")

    # RESUME UPLOAD
    st.markdown(
        """
        <div class="glass">
        <div class="feature-title">📄 Upload Resume</div>
        <div class="feature-text">Upload your latest resume as a PDF.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    resume_file = st.file_uploader(
        "Resume",
        type=["pdf"],
        label_visibility="collapsed"
    )

    st.write("")

    # JOB MODE TOGGLE
    st.markdown(
        """
        <div class="glass">
        <div class="feature-title">💼 Target Job(s)</div>
        <div class="feature-text">
        Paste one job description, or compare your resume against
        up to 3 job postings at once.
        </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    num_jobs = st.radio(
        "How many jobs?",
        options=[1, 2, 3],
        index=st.session_state.num_jobs - 1,
        horizontal=True,
        format_func=lambda n: "Single Job" if n == 1 else f"Compare {n} Jobs",
    )
    st.session_state.num_jobs = num_jobs

    st.write("")

    job_entries = []
    if num_jobs == 1:
        job_description = st.text_area(
            "Job description",
            height=220,
            placeholder="Paste the complete job description here...",
            label_visibility="collapsed",
            key="job_desc_0",
        )
        job_entries.append({"title": "Target Job", "description": job_description})
    else:
        cols = st.columns(num_jobs)
        for i in range(num_jobs):
            with cols[i]:
                title = st.text_input(
                    f"Job {i + 1} title (optional)",
                    key=f"job_title_{i}",
                    placeholder=f"Job {i + 1}",
                )
                desc = st.text_area(
                    f"Job {i + 1} description",
                    height=220,
                    placeholder="Paste job description here...",
                    label_visibility="collapsed",
                    key=f"job_desc_{i}",
                )
                job_entries.append({
                    "title": title.strip() if title.strip() else f"Job {i + 1}",
                    "description": desc,
                })

    st.write("")

    if st.button(
        "⚡ ANALYZE MY CAREER",
        use_container_width=True
    ):
        if resume_file is None:
            st.error("📄 Please upload your resume.")
            st.stop()

        max_bytes = MAX_RESUME_SIZE_MB * 1024 * 1024
        if resume_file.size > max_bytes:
            st.error(
                f"📄 That PDF is larger than {MAX_RESUME_SIZE_MB}MB. "
                "Please upload a smaller file."
            )
            st.stop()

        # Validate every job description slot that's in play
        for entry in job_entries:
            if not entry["description"].strip():
                st.error(f"💼 Please paste a description for '{entry['title']}'.")
                st.stop()
            if len(entry["description"].strip()) < MIN_JOB_DESCRIPTION_CHARS:
                st.error(
                    f"💼 The description for '{entry['title']}' looks too short. "
                    "Please paste the full listing for an accurate match."
                )
                st.stop()

        resume_bytes = resume_file.getvalue()

        st.session_state.screen = "processing"
        st.session_state.resume_bytes = resume_bytes
        st.session_state.resume_name = resume_file.name
        st.session_state.job_entries = job_entries
        st.rerun()

# =========================================================
# PROCESSING SCREEN
# =========================================================

elif st.session_state.screen == "processing":

    st.markdown(
        """
        <div class="hero">
            <div class="hero-badge">✦ AI ENGINE ACTIVE</div>
            <div class="hero-title">Analyzing...</div>
            <div class="hero-description">
                Our AI is understanding your experience,
                skills and the requirements of this role.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div style="text-align:center; margin: 10px 0 25px;">
            <span class="spinner-icon">🧭</span>
            <div class="loading-dots" style="margin-top:10px;">
                <span></span><span></span><span></span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    progress = st.progress(0)
    status = st.empty()

    try:
        status.markdown("📄 **Reading your resume...**")
        time.sleep(0.4)

        resume_stream = io.BytesIO(st.session_state.resume_bytes)
        resume_text = extract_text_from_pdf(resume_stream)

        if not resume_text or not resume_text.strip():
            raise ValueError(
                "We couldn't extract any text from that PDF. It may be a "
                "scanned image without selectable text — try a text-based "
                "PDF instead."
            )

        progress.progress(15)

        status.markdown("🧠 **Understanding your skills...**")
        time.sleep(0.4)
        resume_skills = extract_skills(resume_text)
        st.session_state.resume_skills = resume_skills

        progress.progress(30)

        job_entries = st.session_state.job_entries
        results_list = []
        total_jobs = len(job_entries)

        for idx, entry in enumerate(job_entries):
            status.markdown(
                f"🎯 **Matching against '{entry['title']}'... "
                f"({idx + 1}/{total_jobs})**"
            )
            time.sleep(0.4)

            job_skills = extract_skills(entry["description"])
            match_score = calculate_match(resume_text, entry["description"])
            matched, missing, skill_score = analyze_skills(resume_skills, job_skills)

            results_list.append({
                "label": entry["title"],
                "match_score": match_score,
                "skill_score": skill_score,
                "matched": matched,
                "missing": missing,
            })

            progress.progress(30 + int(50 * (idx + 1) / total_jobs))

        status.markdown("📊 **Generating your career insights...**")
        time.sleep(0.4)

        tips = generate_combined_tips(resume_text, results_list)
        company_suggestions = suggest_companies(resume_skills)

        progress.progress(100)
        time.sleep(0.3)

        # Save results
        st.session_state.results_list = results_list
        st.session_state.tips = tips
        st.session_state.company_suggestions = company_suggestions
        st.session_state.analyzed = True
        st.session_state.screen = "results"

        # Save to history
        best = max(results_list, key=lambda r: r["match_score"])
        st.session_state.history.insert(0, {
            "timestamp": datetime.now().strftime("%b %d, %Y · %I:%M %p"),
            "resume_name": st.session_state.resume_name,
            "jobs": [
                {"label": r["label"], "match_score": r["match_score"],
                 "skill_score": r["skill_score"]}
                for r in results_list
            ],
            "best_label": best["label"],
            "best_score": best["match_score"],
        })

        st.rerun()

    except Exception as exc:
        go_to_analyze_with_error(
            f"Something went wrong while analyzing your resume: {exc}"
        )

# =========================================================
# RESULTS SCREEN
# =========================================================

elif st.session_state.screen == "results":

    if not st.session_state.get("analyzed"):
        st.session_state.screen = "analyze"
        st.rerun()

    render_top_nav("results")

    results_list = st.session_state.get("results_list", [])
    tips = st.session_state.get("tips", [])
    resume_name = st.session_state.get("resume_name", "Resume")
    is_compare = len(results_list) > 1

    st.markdown(
        """
        <div class="hero" style="padding-top:20px;">
            <div class="hero-badge">✦ ANALYSIS COMPLETE</div>
            <div class="hero-title">Here's your result.</div>
            <div class="hero-description">
                Your resume has been compared with the target role(s).
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    if not is_compare:
        res = results_list[0]
        match_score = res["match_score"]
        skill_score = res["skill_score"]
        matched = res["matched"]
        missing = res["missing"]

        # SCORE
        st.markdown(
            f"""
            <div class="score-card">
                <div class="score">{match_score:.0f}%</div>
                <div class="score-label">AI JOB MATCH</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write("")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("🎯 Job Match", f"{match_score:.0f}%")
        with c2:
            st.metric("🧠 Skills Match", f"{skill_score:.0f}%")
        with c3:
            st.metric("📚 Skills to Learn", len(missing))

        st.write("")

        left, right = st.columns(2, gap="large")
        with left:
            st.markdown(
                """<div class="glass"><div class="feature-title">🟢 Your Strengths</div>
                <div class="feature-text">Skills that match the job requirements.</div>
                </div>""",
                unsafe_allow_html=True
            )
            if matched:
                for i, skill in enumerate(matched):
                    delay = min(i * 0.05, 0.6)
                    st.markdown(
                        f'<span class="skill green" style="animation-delay:{delay}s;">✓ {skill}</span>',
                        unsafe_allow_html=True
                    )
            else:
                st.info("No matching skills detected.")

        with right:
            st.markdown(
                """<div class="glass"><div class="feature-title">🔴 Skill Gaps</div>
                <div class="feature-text">Skills required by the job that weren't detected
                in your resume.</div></div>""",
                unsafe_allow_html=True
            )
            if missing:
                for i, skill in enumerate(missing):
                    delay = min(i * 0.05, 0.6)
                    st.markdown(
                        f'<span class="skill red" style="animation-delay:{delay}s;">✕ {skill}</span>',
                        unsafe_allow_html=True
                    )
            else:
                st.success("🎉 No major skill gaps detected!")

        st.write("")
        st.subheader("📊 Your Skill Breakdown")

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=["Matching Skills", "Missing Skills"],
            y=[len(matched), len(missing)],
            text=[len(matched), len(missing)],
            textposition="auto"
        ))
        fig.update_layout(
            template="plotly_dark", height=350, showlegend=False,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("🧠 Career Verdict")
        if match_score >= 80:
            st.success("🔥 Excellent match! Your current profile strongly aligns with this position.")
        elif match_score >= 60:
            st.warning("⚡ Good match! You have a solid foundation. Work on the missing skills to strengthen your application.")
        else:
            st.error("🚀 There are several skill gaps. Follow the roadmap below to become more job-ready.")

        st.subheader("🗺️ Your Career Roadmap")
        if missing:
            roadmap_items = missing[:6]
            for number, skill in enumerate(roadmap_items, start=1):
                delay = (number - 1) * 0.1
                st.markdown(
                    f"""<div class="roadmap fade-in-up" style="animation-delay:{delay}s;">
                    <div class="roadmap-number">{number}</div>
                    <div><strong>Learn {skill}</strong><br>
                    <small style="color:#71717a;">Build a practical project using
                    {skill} and add it to your portfolio.</small></div></div>""",
                    unsafe_allow_html=True
                )
            if len(missing) > 6:
                st.caption(f"Showing top 6 of {len(missing)} skill gaps.")
        else:
            st.success("🎉 Your detected skills closely match this position.")

    else:
        # COMPARE MODE
        best = max(results_list, key=lambda r: r["match_score"])

        st.subheader("⚖️ Job Comparison")

        cols = st.columns(len(results_list))
        for i, res in enumerate(results_list):
            with cols[i]:
                is_best = res["label"] == best["label"]
                badge = '<span class="best-badge">BEST MATCH</span>' if is_best else ""
                st.markdown(
                    f"""
                    <div class="score-card fade-in-up" style="padding:22px; animation-delay:{i * 0.15}s;">
                        <div style="font-size:14px; color:#a1a1aa; margin-bottom:8px;">
                            {res['label']} {badge}
                        </div>
                        <div class="score" style="font-size:52px;">{res['match_score']:.0f}%</div>
                        <div class="score-label">JOB MATCH</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                st.metric("🧠 Skills Match", f"{res['skill_score']:.0f}%")
                st.metric("📚 Gaps", len(res["missing"]))

        st.write("")
        st.subheader("📊 Match Score Comparison")

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[r["label"] for r in results_list],
            y=[r["match_score"] for r in results_list],
            text=[f"{r['match_score']:.0f}%" for r in results_list],
            textposition="auto",
        ))
        fig.update_layout(
            template="plotly_dark", height=350, showlegend=False,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.write("")
        st.markdown(
            f"**🏆 Best fit: {best['label']}** with a {best['match_score']:.0f}% match. "
            "See the breakdown for each job below."
        )

        tabs = st.tabs([r["label"] for r in results_list])
        for tab, res in zip(tabs, results_list):
            with tab:
                left, right = st.columns(2, gap="large")
                with left:
                    st.markdown("**🟢 Strengths**")
                    if res["matched"]:
                        for i, skill in enumerate(res["matched"]):
                            delay = min(i * 0.05, 0.6)
                            st.markdown(
                                f'<span class="skill green" style="animation-delay:{delay}s;">✓ {skill}</span>',
                                unsafe_allow_html=True
                            )
                    else:
                        st.info("No matching skills detected.")
                with right:
                    st.markdown("**🔴 Skill Gaps**")
                    if res["missing"]:
                        for i, skill in enumerate(res["missing"]):
                            delay = min(i * 0.05, 0.6)
                            st.markdown(
                                f'<span class="skill red" style="animation-delay:{delay}s;">✕ {skill}</span>',
                                unsafe_allow_html=True
                            )
                    else:
                        st.success("🎉 No major skill gaps detected!")

    # RESUME IMPROVEMENT TIPS (shared across single/compare mode)
    st.write("")
    st.subheader("💡 Resume Improvement Tips")
    for i, tip in enumerate(tips):
        delay = i * 0.1
        st.markdown(
            f"""<div class="tip-card fade-in-up" style="animation-delay:{delay}s;">
            <div class="tip-icon">✨</div>
            <div class="tip-text">{tip}</div></div>""",
            unsafe_allow_html=True
        )

    # COMPANIES THAT MIGHT HIRE YOU
    company_suggestions = st.session_state.get("company_suggestions", [])
    st.write("")
    st.subheader("🏢 Companies That Might Hire You")
    st.caption(
        "Based on your detected skills — a general industry guide, not "
        "live job postings. Check each company's careers page for current openings."
    )

    if company_suggestions:
        for idx, sug in enumerate(company_suggestions):
            card_delay = idx * 0.15
            skills_str = ", ".join(sug["overlap_skills"][:5])
            companies_html = "".join(
                f'<span class="skill" style="animation-delay:{min(j * 0.05, 0.4)}s;">🏢 {c}</span>'
                for j, c in enumerate(sug["companies"])
            )
            st.markdown(
                f"""
                <div class="glass fade-in-up" style="margin-bottom:14px; animation-delay:{card_delay}s;">
                    <div class="feature-title">🎯 {sug['role']}</div>
                    <div class="feature-text" style="margin-bottom:10px;">
                        Matched on: {skills_str}
                    </div>
                    <div>{companies_html}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info(
            "We couldn't confidently match your skills to a known role yet. "
            "Try adding more specific technical or domain skills to your resume."
        )

    # PDF REPORT DOWNLOAD
    st.write("")
    st.subheader("📄 Download Your Report")
    pdf_bytes = generate_pdf_report(resume_name, results_list, tips, company_suggestions)
    st.download_button(
        label="⬇️ DOWNLOAD PDF REPORT",
        data=pdf_bytes,
        file_name=f"careermatch_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    st.write("")

    nav1, nav2 = st.columns(2)
    with nav1:
        if st.button("🔄 ANALYZE ANOTHER JOB", use_container_width=True):
            st.session_state.screen = "analyze"
            st.session_state.analyzed = False
            st.rerun()
    with nav2:
        if st.button("📜 VIEW HISTORY", use_container_width=True):
            st.session_state.screen = "history"
            st.rerun()

    st.markdown(
        """
        <div style="text-align:center; color:#52525b; margin-top:50px;">
        CareerMatch AI · Analyze • Improve • Get Hired
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================================================
# HISTORY SCREEN
# =========================================================

elif st.session_state.screen == "history":

    render_top_nav("history")

    st.markdown(
        """
        <div class="hero" style="padding-top:20px;">
            <div class="hero-badge">✦ YOUR ACTIVITY</div>
            <div class="hero-title">Analysis History</div>
            <div class="hero-description">
                Every resume check you've run this session, most recent first.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    history = st.session_state.history

    if not history:
        st.info("No analyses yet. Run your first job match to see it here.")
    else:
        for h_idx, entry in enumerate(history):
            h_delay = min(h_idx * 0.08, 0.6)
            jobs_summary = " · ".join(
                f"{j['label']}: {j['match_score']:.0f}%" for j in entry["jobs"]
            )
            st.markdown(
                f"""
                <div class="history-card fade-in-up" style="animation-delay:{h_delay}s;">
                    <div style="font-weight:800; font-size:16px;">
                        {entry['resume_name']}
                        <span class="best-badge">Best: {entry['best_label']}
                        · {entry['best_score']:.0f}%</span>
                    </div>
                    <div class="history-meta">{entry['timestamp']}</div>
                    <div style="margin-top:8px; color:#a1a1aa; font-size:14px;">
                        {jobs_summary}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.write("")
        if st.button("🗑️ CLEAR HISTORY", use_container_width=True):
            st.session_state.history = []
            st.rerun()

    st.write("")
    if st.button("🚀 NEW ANALYSIS", use_container_width=True):
        st.session_state.screen = "analyze"
        st.rerun()
