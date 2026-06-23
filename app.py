"""
app.py  –  AI Resume Parser & Resume Builder
Run:  streamlit run app.py
"""

import os, json
import streamlit as st
from pathlib import Path

from parser import extract_text
from extractor import extract_all
from builder import generate_resume, TEMPLATE_BUILDERS

# ── Paths ────────────────────────────────────────────────────────────────────
UPLOADS_DIR   = Path(__file__).parent / "uploads"
GENERATED_DIR = Path(__file__).parent / "generated_resumes"
DATA_DIR      = Path(__file__).parent / "data"
for d in [UPLOADS_DIR, GENERATED_DIR, DATA_DIR]:
    d.mkdir(exist_ok=True)

# ── Session state ────────────────────────────────────────────────────────────
def _init():
    for k, v in {"parsed": {}, "builder": {}, "pdf": None, "page": "Home"}.items():
        if k not in st.session_state:
            st.session_state[k] = v

def _save(data, fname="saved_data.json"):
    with open(DATA_DIR / fname, "w") as f:
        json.dump(data, f, indent=2)

def _load(fname="saved_data.json"):
    p = DATA_DIR / fname
    return json.loads(p.read_text()) if p.exists() else {}

# ── Navigation ───────────────────────────────────────────────────────────────
PAGES = ["Home", "Resume Parser", "Resume Builder", "Generated Resumes"]

def _sidebar():
    with st.sidebar:
        st.markdown("## 📋 AI Resume Tool")
        st.markdown("---")
        for p in PAGES:
            is_active = st.session_state["page"] == p
            if st.button(p, use_container_width=True,
                         type="primary" if is_active else "secondary",
                         key=f"nav_{p}"):
                st.session_state["page"] = p
                st.rerun()

# ── Shared builder form ───────────────────────────────────────────────────────
def _builder_form(prefix, bd):
    """Render full form, return data dict (includes _template key)."""

    st.subheader("Personal Information")
    c1, c2, c3 = st.columns(3)
    with c1:
        name  = st.text_input("Full Name *", value=bd.get("name",""),  key=f"{prefix}_name")
        email = st.text_input("Email",       value=bd.get("email",""), key=f"{prefix}_email")
    with c2:
        phone   = st.text_input("Phone",   value=bd.get("phone",""),   key=f"{prefix}_phone")
        address = st.text_input("Address", value=bd.get("address",""), key=f"{prefix}_address")
    with c3:
        linkedin = st.text_input("LinkedIn URL", value=bd.get("linkedin",""), key=f"{prefix}_li")
        github   = st.text_input("GitHub URL",   value=bd.get("github",""),   key=f"{prefix}_gh")

    target_role = st.text_input(
        "Target Role / Job Title",
        value=bd.get("target_role",""),
        placeholder="e.g. Data Analyst, Software Engineer",
        key=f"{prefix}_role",
    )

    st.divider()
    st.subheader("Career Objective")
    career_obj = st.text_area(
        "Career Objective (leave blank to auto-generate)",
        value=bd.get("career_objective",""), height=90,
        key=f"{prefix}_obj", label_visibility="collapsed",
        placeholder="Leave blank to auto-generate from your skills and role.",
    )

    st.divider()
    st.subheader("Skills")
    raw_skills = bd.get("skills", [])
    skills_str = ", ".join(raw_skills) if isinstance(raw_skills, list) else raw_skills
    skills_input = st.text_area(
        "Skills", value=skills_str, height=75,
        placeholder="Python, SQL, Machine Learning, Docker, Power BI…",
        key=f"{prefix}_skills", label_visibility="collapsed",
    )

    st.divider()
    st.subheader("Education")
    education = st.text_area(
        "Education", value=bd.get("education",""), height=110,
        placeholder="B.Tech in Computer Science – XYZ University (2020–2024)\n12th Grade – ABC School (2019)",
        key=f"{prefix}_edu", label_visibility="collapsed",
    )

    st.divider()
    st.subheader("Work Experience / Internships")
    experience = st.text_area(
        "Experience", value=bd.get("experience",""), height=130,
        placeholder="Software Engineer Intern – TechCorp (Jun 2023 – Aug 2023)\nBuilt REST APIs with FastAPI. Deployed on AWS. Improved DB performance by 40%.",
        key=f"{prefix}_exp", label_visibility="collapsed",
    )

    st.divider()
    st.subheader("Projects")
    projects = st.text_area(
        "Projects", value=bd.get("projects",""), height=130,
        placeholder="AI Chatbot – Python & TensorFlow chatbot for customer support.\nE-commerce Site – Full-stack app with React and Django REST.",
        key=f"{prefix}_proj", label_visibility="collapsed",
    )

    st.divider()
    st.subheader("Certifications")
    certifications = st.text_area(
        "Certifications", value=bd.get("certifications",""), height=80,
        placeholder="AWS Certified Solutions Architect (2023)\nGoogle Data Analytics Certificate (2022)",
        key=f"{prefix}_cert", label_visibility="collapsed",
    )

    st.divider()
    st.subheader("Achievements")
    achievements = st.text_area(
        "Achievements", value=bd.get("achievements",""), height=80,
        placeholder="Winner – National Hackathon 2023\nDean's List – 3 consecutive semesters",
        key=f"{prefix}_ach", label_visibility="collapsed",
    )

    st.divider()
    st.subheader("Choose Template")
    template = st.radio(
        "Template", options=list(TEMPLATE_BUILDERS.keys()),
        horizontal=True, key=f"{prefix}_tmpl", label_visibility="collapsed",
    )
    desc = {
        "Modern Professional": "Indigo header, polished layout — great for experienced professionals.",
        "ATS Friendly":        "Clean black & white — optimised for Applicant Tracking Systems.",
        "Fresher Resume":      "Teal accents, skill grid — ideal for students and new graduates.",
    }
    st.caption(desc.get(template, ""))

    return {
        "name": name.strip(), "email": email.strip(), "phone": phone.strip(),
        "address": address.strip(), "linkedin": linkedin.strip(), "github": github.strip(),
        "target_role": target_role.strip(), "career_objective": career_obj.strip(),
        "skills": [s.strip() for s in skills_input.split(",") if s.strip()],
        "education": education.strip(), "experience": experience.strip(),
        "projects": projects.strip(), "certifications": certifications.strip(),
        "achievements": achievements.strip(), "_template": template,
    }


def _generate(data, prefix):
    template = data.pop("_template", "Modern Professional")
    if not data.get("name"):
        st.error("Full Name is required.")
        return
    st.session_state["builder"] = data
    _save(data, "last_build.json")
    with st.spinner("Generating PDF…"):
        try:
            path = generate_resume(data, template)
            st.session_state["pdf"] = path
            st.success(f"Resume ready: **{Path(path).name}**")
        except Exception as e:
            st.error(f"Failed: {e}")
            return
    with open(path, "rb") as f:
        st.download_button(
            "Download Resume PDF", data=f,
            file_name=Path(path).name, mime="application/pdf",
            use_container_width=True, key=f"{prefix}_dl",
        )


# ── Pages ────────────────────────────────────────────────────────────────────

def page_home():
    # Simple header — no custom HTML cards that break in dark mode
    st.title("AI Resume Parser & Builder")
    st.markdown("Build a professional resume in minutes — completely offline.")
    st.divider()

    # Quick-action buttons at the top
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📄  Parse an Existing Resume", use_container_width=True):
            st.session_state["page"] = "Resume Parser"
            st.rerun()
    with col2:
        if st.button("📁  View Generated Resumes", use_container_width=True):
            st.session_state["page"] = "Generated Resumes"
            st.rerun()
    with col3:
        # Pre-fill from parsed data if available
        if st.session_state.get("parsed") and st.button(
            "⚡  Pre-fill from Parsed Resume", use_container_width=True
        ):
            st.session_state["builder"] = dict(st.session_state["parsed"])
            st.rerun()

    st.divider()

    # ── Inline Resume Builder ─────────────────────────────────────────────
    st.header("Build Your Resume")

    bd = st.session_state.get("builder", {})
    data = _builder_form("home", bd)

    st.divider()
    if st.button("Generate Resume PDF", type="primary", use_container_width=True, key="home_gen"):
        _generate(data, "home")

    # Re-show download if PDF already exists
    if st.session_state.get("pdf") and Path(st.session_state["pdf"]).exists():
        st.markdown("---")
        with open(st.session_state["pdf"], "rb") as f:
            st.download_button(
                f"Re-download: {Path(st.session_state['pdf']).name}", data=f,
                file_name=Path(st.session_state["pdf"]).name,
                mime="application/pdf", key="home_redl",
            )


def page_parser():
    st.title("Resume Parser")
    st.markdown("Upload a PDF or DOCX resume to extract information automatically.")
    st.divider()

    uploaded = st.file_uploader("Upload resume (PDF or DOCX)", type=["pdf","docx","doc"])

    if not uploaded:
        return

    with open(UPLOADS_DIR / uploaded.name, "wb") as f:
        f.write(uploaded.getbuffer())

    with st.spinner("Parsing resume…"):
        try:
            raw   = extract_text(uploaded, uploaded.name)
            parsed = extract_all(raw)
            st.session_state["parsed"] = parsed
            st.success("Parsed successfully.")
        except Exception as e:
            st.error(str(e))
            return

    st.divider()
    st.subheader("Extracted Information")
    d = st.session_state["parsed"]

    c1, c2 = st.columns(2)
    with c1:
        d["name"]  = st.text_input("Full Name", value=d.get("name",""))
        d["email"] = st.text_input("Email",     value=d.get("email",""))
        d["phone"] = st.text_input("Phone",     value=d.get("phone",""))
    with c2:
        d["linkedin"] = st.text_input("LinkedIn", value=d.get("linkedin",""))
        d["github"]   = st.text_input("GitHub",   value=d.get("github",""))

    raw_sk = d.get("skills",[])
    sk_str = ", ".join(raw_sk) if isinstance(raw_sk,list) else raw_sk
    edited = st.text_area("Skills (comma-separated)", value=sk_str, height=75)
    d["skills"] = [s.strip() for s in edited.split(",") if s.strip()]

    d["education"]      = st.text_area("Education",       value=d.get("education",""),      height=110)
    d["experience"]     = st.text_area("Work Experience",  value=d.get("experience",""),     height=110)
    d["projects"]       = st.text_area("Projects",         value=d.get("projects",""),       height=110)
    d["certifications"] = st.text_area("Certifications",   value=d.get("certifications",""), height=75)

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Save Data", use_container_width=True):
            _save(d)
            st.success("Saved.")
    with c2:
        if st.button("Use in Builder →", use_container_width=True, type="primary"):
            st.session_state["builder"] = dict(d)
            st.session_state["page"] = "Home"
            st.rerun()

    with st.expander("Raw extracted text"):
        st.text(raw[:3000] + ("…" if len(raw) > 3000 else ""))


def page_builder():
    st.title("Resume Builder")
    st.divider()

    with st.expander("Load previously saved data"):
        if st.button("Load"):
            d = _load()
            if d:
                st.session_state["builder"] = d
                st.success("Loaded.")
                st.rerun()
            else:
                st.warning("No saved data found.")

    bd = st.session_state.get("builder", {})
    data = _builder_form("builder", bd)

    st.divider()
    if st.button("Generate Resume PDF", type="primary", use_container_width=True, key="bld_gen"):
        _generate(data, "builder")


def page_generated():
    st.title("Generated Resumes")
    st.divider()

    files = sorted(GENERATED_DIR.glob("*.pdf"), key=os.path.getmtime, reverse=True)
    if not files:
        st.info("No resumes yet. Build one on the Home page.")
        return

    st.markdown(f"{len(files)} resume(s) found.")
    for pdf in files:
        c1, c2 = st.columns([4, 1])
        with c1:
            st.markdown(f"**{pdf.name}** — {max(1, pdf.stat().st_size//1024)} KB")
        with c2:
            with open(pdf,"rb") as f:
                st.download_button("Download", data=f, file_name=pdf.name,
                                   mime="application/pdf", key=str(pdf))


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="AI Resume Tool", page_icon="📋",
        layout="wide", initial_sidebar_state="expanded",
    )
    _init()
    _sidebar()

    p = st.session_state["page"]
    if p == "Home":              page_home()
    elif p == "Resume Parser":   page_parser()
    elif p == "Resume Builder":  page_builder()
    elif p == "Generated Resumes": page_generated()


if __name__ == "__main__":
    main()
