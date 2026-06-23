"""
builder.py
----------
Generates professional PDF resumes from structured data
using ReportLab.  Provides three templates:
  1. Modern Professional
  2. ATS Friendly
  3. Fresher Resume
"""

import os
from datetime import datetime
from typing import Dict, List

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate,
    Paragraph, Spacer, Table, TableStyle, HRFlowable,
    KeepTogether,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "generated_resumes")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Color palettes per template
# ---------------------------------------------------------------------------

PALETTES = {
    "Modern Professional": {
        "primary":   colors.HexColor("#1a237e"),   # deep indigo
        "secondary": colors.HexColor("#283593"),
        "accent":    colors.HexColor("#e8eaf6"),
        "text":      colors.HexColor("#212121"),
        "subtext":   colors.HexColor("#546e7a"),
        "white":     colors.white,
    },
    "ATS Friendly": {
        "primary":   colors.HexColor("#000000"),
        "secondary": colors.HexColor("#333333"),
        "accent":    colors.HexColor("#f5f5f5"),
        "text":      colors.HexColor("#000000"),
        "subtext":   colors.HexColor("#444444"),
        "white":     colors.white,
    },
    "Fresher Resume": {
        "primary":   colors.HexColor("#00695c"),   # teal
        "secondary": colors.HexColor("#00897b"),
        "accent":    colors.HexColor("#e0f2f1"),
        "text":      colors.HexColor("#1c1c1c"),
        "subtext":   colors.HexColor("#546e7a"),
        "white":     colors.white,
    },
}


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _safe_lines(text: str) -> List[str]:
    """Split multiline text into non-empty lines."""
    return [l.strip() for l in (text or "").splitlines() if l.strip()]


def _bullet_items(text: str) -> List[str]:
    """Return list of bullet strings from multiline text."""
    return _safe_lines(text)


def _skills_list(skills_raw) -> List[str]:
    if isinstance(skills_raw, list):
        return [s.strip() for s in skills_raw if s.strip()]
    return [s.strip() for s in str(skills_raw or "").split(",") if s.strip()]


def _auto_summary(data: Dict) -> str:
    """Generate a professional summary if none provided."""
    name      = data.get("name", "The candidate")
    role      = data.get("target_role", "professional")
    skills    = _skills_list(data.get("skills", []))
    skill_str = ", ".join(skills[:5]) if skills else "various technical skills"
    return (
        f"Motivated {role} with strong expertise in {skill_str}. "
        "Passionate about delivering high-quality solutions and continuously "
        "improving technical skills through hands-on experience and learning."
    )


# ---------------------------------------------------------------------------
# Style factory
# ---------------------------------------------------------------------------

def _make_styles(palette: dict) -> dict:
    base = getSampleStyleSheet()
    P  = palette

    styles = {
        "name": ParagraphStyle(
            "Name",
            fontName="Helvetica-Bold",
            fontSize=22,
            textColor=P["white"],
            alignment=TA_CENTER,
            spaceAfter=2,
        ),
        "contact_header": ParagraphStyle(
            "ContactHeader",
            fontName="Helvetica",
            fontSize=9,
            textColor=P["white"],
            alignment=TA_CENTER,
            spaceAfter=0,
        ),
        "section_title": ParagraphStyle(
            "SectionTitle",
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=P["primary"],
            spaceBefore=10,
            spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "Body",
            fontName="Helvetica",
            fontSize=9.5,
            textColor=P["text"],
            leading=14,
            spaceAfter=2,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            fontName="Helvetica",
            fontSize=9.5,
            textColor=P["text"],
            leading=13,
            leftIndent=12,
            bulletIndent=0,
            spaceAfter=2,
        ),
        "subtext": ParagraphStyle(
            "Subtext",
            fontName="Helvetica-Oblique",
            fontSize=9,
            textColor=P["subtext"],
            spaceAfter=2,
        ),
        "skills_chip": ParagraphStyle(
            "SkillsChip",
            fontName="Helvetica",
            fontSize=9,
            textColor=P["text"],
            spaceAfter=2,
        ),
    }
    return styles


# ---------------------------------------------------------------------------
# Shared section builders
# ---------------------------------------------------------------------------

def _section_header(title: str, styles: dict, palette: dict) -> List:
    items = [
        Paragraph(title.upper(), styles["section_title"]),
        HRFlowable(
            width="100%", thickness=1,
            color=palette["primary"], spaceAfter=4
        ),
    ]
    return items


def _contact_line(data: Dict) -> str:
    parts = []
    if data.get("email"):    parts.append(data["email"])
    if data.get("phone"):    parts.append(data["phone"])
    if data.get("address"):  parts.append(data["address"])
    if data.get("linkedin"): parts.append(data["linkedin"])
    if data.get("github"):   parts.append(data["github"])
    return "  |  ".join(parts)


# ---------------------------------------------------------------------------
# Template 1 – Modern Professional
# ---------------------------------------------------------------------------

def _build_modern(data: Dict, filepath: str):
    palette = PALETTES["Modern Professional"]
    styles  = _make_styles(palette)

    doc = BaseDocTemplate(
        filepath, pagesize=A4,
        rightMargin=1.5*cm, leftMargin=1.5*cm,
        topMargin=0, bottomMargin=1.5*cm,
    )

    frame = Frame(
        doc.leftMargin, doc.bottomMargin,
        doc.width, doc.height,
        id="normal",
    )
    doc.addPageTemplates([PageTemplate(id="main", frames=frame)])

    story = []

    # ── Header band ──────────────────────────────────────────────────────────
    header_data = [
        [Paragraph(data.get("name", "Your Name"), styles["name"])],
        [Paragraph(_contact_line(data), styles["contact_header"])],
    ]
    header_table = Table(header_data, colWidths=[doc.width])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), palette["primary"]),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.4*cm))

    # ── Summary ──────────────────────────────────────────────────────────────
    summary = data.get("career_objective") or _auto_summary(data)
    story += _section_header("Professional Summary", styles, palette)
    story.append(Paragraph(summary, styles["body"]))

    # ── Skills ───────────────────────────────────────────────────────────────
    skills = _skills_list(data.get("skills", []))
    if skills:
        story += _section_header("Skills", styles, palette)
        chips = " • ".join(skills)
        story.append(Paragraph(chips, styles["skills_chip"]))

    # ── Experience ───────────────────────────────────────────────────────────
    exp_lines = _bullet_items(data.get("experience", ""))
    if exp_lines:
        story += _section_header("Work Experience", styles, palette)
        for line in exp_lines:
            story.append(Paragraph(f"• {line}", styles["bullet"]))

    # ── Education ────────────────────────────────────────────────────────────
    edu_lines = _bullet_items(data.get("education", ""))
    if edu_lines:
        story += _section_header("Education", styles, palette)
        for line in edu_lines:
            story.append(Paragraph(f"• {line}", styles["bullet"]))

    # ── Projects ─────────────────────────────────────────────────────────────
    proj_lines = _bullet_items(data.get("projects", ""))
    if proj_lines:
        story += _section_header("Projects", styles, palette)
        for line in proj_lines:
            story.append(Paragraph(f"• {line}", styles["bullet"]))

    # ── Certifications ───────────────────────────────────────────────────────
    cert_lines = _bullet_items(data.get("certifications", ""))
    if cert_lines:
        story += _section_header("Certifications & Achievements", styles, palette)
        for line in cert_lines:
            story.append(Paragraph(f"• {line}", styles["bullet"]))

    # ── Achievements ─────────────────────────────────────────────────────────
    ach_lines = _bullet_items(data.get("achievements", ""))
    if ach_lines:
        story += _section_header("Achievements", styles, palette)
        for line in ach_lines:
            story.append(Paragraph(f"• {line}", styles["bullet"]))

    doc.build(story)


# ---------------------------------------------------------------------------
# Template 2 – ATS Friendly
# ---------------------------------------------------------------------------

def _build_ats(data: Dict, filepath: str):
    palette = PALETTES["ATS Friendly"]
    styles  = _make_styles(palette)

    doc = BaseDocTemplate(
        filepath, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height)
    doc.addPageTemplates([PageTemplate(id="main", frames=frame)])

    story = []

    # Name & contact (plain, ATS-safe)
    story.append(Paragraph(data.get("name", "Your Name"), ParagraphStyle(
        "ATSName", fontName="Helvetica-Bold", fontSize=18,
        alignment=TA_CENTER, spaceAfter=4,
    )))
    story.append(Paragraph(_contact_line(data), ParagraphStyle(
        "ATSContact", fontName="Helvetica", fontSize=9,
        alignment=TA_CENTER, spaceAfter=8, textColor=palette["subtext"],
    )))
    story.append(HRFlowable(width="100%", thickness=1.5, color=palette["primary"], spaceAfter=8))

    # Summary
    summary = data.get("career_objective") or _auto_summary(data)
    story.append(Paragraph("PROFESSIONAL SUMMARY", styles["section_title"]))
    story.append(Paragraph(summary, styles["body"]))
    story.append(Spacer(1, 0.2*cm))

    # Skills
    skills = _skills_list(data.get("skills", []))
    if skills:
        story.append(Paragraph("SKILLS", styles["section_title"]))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey, spaceAfter=4))
        # 3-column skill table for clean ATS layout
        rows = [skills[i:i+3] for i in range(0, len(skills), 3)]
        if rows[-1] and len(rows[-1]) < 3:
            rows[-1] += [""] * (3 - len(rows[-1]))
        skill_table = Table(rows, colWidths=[doc.width/3]*3)
        skill_table.setStyle(TableStyle([
            ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("TOPPADDING", (0,0), (-1,-1), 2),
            ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        ]))
        story.append(skill_table)
        story.append(Spacer(1, 0.2*cm))

    def ats_section(title, text):
        lines = _bullet_items(text)
        if not lines:
            return
        story.append(Paragraph(title, styles["section_title"]))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey, spaceAfter=4))
        for line in lines:
            story.append(Paragraph(f"• {line}", styles["bullet"]))
        story.append(Spacer(1, 0.2*cm))

    ats_section("WORK EXPERIENCE",            data.get("experience", ""))
    ats_section("EDUCATION",                  data.get("education", ""))
    ats_section("PROJECTS",                   data.get("projects", ""))
    ats_section("CERTIFICATIONS",             data.get("certifications", ""))
    ats_section("ACHIEVEMENTS",               data.get("achievements", ""))

    doc.build(story)


# ---------------------------------------------------------------------------
# Template 3 – Fresher Resume
# ---------------------------------------------------------------------------

def _build_fresher(data: Dict, filepath: str):
    palette = PALETTES["Fresher Resume"]
    styles  = _make_styles(palette)

    doc = BaseDocTemplate(
        filepath, pagesize=A4,
        rightMargin=1.5*cm, leftMargin=1.5*cm,
        topMargin=0, bottomMargin=1.5*cm,
    )

    # Two-column layout: left sidebar (35%) + main content (65%)
    sidebar_width = doc.width * 0.34
    main_width    = doc.width * 0.63
    gap           = doc.width * 0.03

    sidebar_frame = Frame(
        doc.leftMargin, doc.bottomMargin,
        sidebar_width, doc.height, id="sidebar",
    )
    main_frame = Frame(
        doc.leftMargin + sidebar_width + gap, doc.bottomMargin,
        main_width, doc.height, id="main",
    )

    # We'll build a single-frame version for simplicity & reliability
    single_frame = Frame(
        doc.leftMargin, doc.bottomMargin,
        doc.width, doc.height, id="normal",
    )
    doc.addPageTemplates([PageTemplate(id="main", frames=single_frame)])

    story = []

    # Coloured header
    header_table = Table(
        [[Paragraph(data.get("name", "Your Name"), styles["name"])],
         [Paragraph(_contact_line(data), styles["contact_header"])]],
        colWidths=[doc.width],
    )
    header_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), palette["primary"]),
        ("TOPPADDING",    (0,0), (-1,-1), 16),
        ("BOTTOMPADDING", (0,0), (-1,-1), 12),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.4*cm))

    # Career objective
    obj = data.get("career_objective") or _auto_summary(data)
    story += _section_header("Career Objective", styles, palette)
    story.append(Paragraph(obj, styles["body"]))

    # Education (prominent for fresher)
    edu_lines = _bullet_items(data.get("education", ""))
    if edu_lines:
        story += _section_header("Education", styles, palette)
        for line in edu_lines:
            story.append(Paragraph(f"• {line}", styles["bullet"]))

    # Skills
    skills = _skills_list(data.get("skills", []))
    if skills:
        story += _section_header("Technical Skills", styles, palette)
        # Coloured accent table
        rows = [skills[i:i+4] for i in range(0, len(skills), 4)]
        if rows and len(rows[-1]) < 4:
            rows[-1] += [""] * (4 - len(rows[-1]))
        if rows:
            skill_table = Table(rows, colWidths=[doc.width/4]*4)
            skill_table.setStyle(TableStyle([
                ("BACKGROUND",    (0,0), (-1,-1), palette["accent"]),
                ("FONTNAME",      (0,0), (-1,-1), "Helvetica"),
                ("FONTSIZE",      (0,0), (-1,-1), 9),
                ("TOPPADDING",    (0,0), (-1,-1), 4),
                ("BOTTOMPADDING", (0,0), (-1,-1), 4),
                ("LEFTPADDING",   (0,0), (-1,-1), 6),
                ("GRID",          (0,0), (-1,-1), 0.5, palette["secondary"]),
            ]))
            story.append(skill_table)

    def fresher_section(title, text):
        lines = _bullet_items(text)
        if not lines:
            return
        story.append(Spacer(1, 0.1*cm))
        story += _section_header(title, styles, palette)
        for line in lines:
            story.append(Paragraph(f"• {line}", styles["bullet"]))

    fresher_section("Projects",                   data.get("projects", ""))
    fresher_section("Internships / Experience",   data.get("experience", ""))
    fresher_section("Certifications",             data.get("certifications", ""))
    fresher_section("Achievements",               data.get("achievements", ""))

    doc.build(story)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

TEMPLATE_BUILDERS = {
    "Modern Professional": _build_modern,
    "ATS Friendly":        _build_ats,
    "Fresher Resume":      _build_fresher,
}


def generate_resume(data: Dict, template: str = "Modern Professional") -> str:
    """
    Generate a PDF resume and return the file path.

    Parameters
    ----------
    data     : dict with keys: name, email, phone, address, linkedin, github,
               career_objective, target_role, skills (list or csv str),
               education, experience, projects, certifications, achievements
    template : one of TEMPLATE_BUILDERS keys
    """
    builder = TEMPLATE_BUILDERS.get(template, _build_modern)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = re.sub(r"[^\w]", "_", data.get("name", "resume"))
    filename  = f"{safe_name}_{template.replace(' ', '_')}_{timestamp}.pdf"
    filepath  = os.path.join(OUTPUT_DIR, filename)

    builder(data, filepath)
    return filepath


import re  # noqa – already imported above; kept here for clarity
