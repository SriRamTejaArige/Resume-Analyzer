"""
extractor.py
------------
Extracts structured information from raw resume text using
regex patterns and spaCy NLP.
"""

import re
import spacy
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# spaCy model loader (en_core_web_sm)
# ---------------------------------------------------------------------------

def load_nlp():
    """Load spaCy model; return None if unavailable."""
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        try:
            from spacy.cli import download
            download("en_core_web_sm")
            return spacy.load("en_core_web_sm")
        except Exception:
            return None


NLP = load_nlp()


# ---------------------------------------------------------------------------
# Predefined skill database
# ---------------------------------------------------------------------------

SKILL_DB = [
    # Programming languages
    "Python", "Java", "C++", "C", "C#", "R", "Go", "Rust", "Swift", "Kotlin",
    "Scala", "MATLAB", "Bash", "Shell Scripting",
    # Web
    "JavaScript", "TypeScript", "React", "Angular", "Vue.js", "Node.js",
    "HTML", "CSS", "Bootstrap", "Tailwind CSS", "Next.js",
    # Backend / Frameworks
    "Flask", "Django", "FastAPI", "Spring Boot", "Express.js",
    # Databases
    "SQL", "MySQL", "PostgreSQL", "MongoDB", "SQLite", "Redis",
    "Cassandra", "Oracle", "MS SQL Server",
    # ML / AI
    "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Keras",
    "scikit-learn", "OpenCV", "NLP", "Computer Vision", "Data Science",
    "Pandas", "NumPy", "Matplotlib", "Seaborn",
    # Cloud / DevOps
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "CI/CD", "Jenkins",
    "Terraform", "Ansible", "Linux", "Git", "GitHub", "GitLab",
    # BI / Analytics
    "Power BI", "Tableau", "Excel", "Google Analytics", "Looker",
    # Other
    "REST API", "GraphQL", "Microservices", "Agile", "Scrum",
    "Project Management", "JIRA", "Confluence",
]

# Build a lowercase lookup for fast matching
SKILL_LOWER = {s.lower(): s for s in SKILL_DB}


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(
    r"(\+?\d{1,3}[\s\-]?)?(\(?\d{2,4}\)?[\s\-]?)\d{3,5}[\s\-]?\d{3,5}"
)
LINKEDIN_RE = re.compile(r"linkedin\.com/in/[a-zA-Z0-9\-_%]+", re.IGNORECASE)
GITHUB_RE  = re.compile(r"github\.com/[a-zA-Z0-9\-_]+", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Section keyword mapping
# ---------------------------------------------------------------------------

SECTION_HEADERS = {
    "education": [
        "education", "academic background", "qualifications",
        "educational qualification", "academic qualification",
    ],
    "experience": [
        "experience", "work experience", "employment history",
        "professional experience", "internship", "internships",
        "career history",
    ],
    "projects": [
        "projects", "academic projects", "personal projects",
        "project work", "key projects",
    ],
    "skills": [
        "skills", "technical skills", "core competencies",
        "technologies", "tools", "expertise",
    ],
    "certifications": [
        "certifications", "certificates", "courses",
        "training", "achievements", "awards",
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _split_lines(text: str) -> List[str]:
    return [l.strip() for l in text.splitlines() if l.strip()]


def _section_blocks(lines: List[str]) -> Dict[str, List[str]]:
    """
    Split raw lines into named sections based on header keywords.
    Returns dict: section_name -> [lines].
    """
    blocks: Dict[str, List[str]] = {"header": []}
    current = "header"

    for line in lines:
        lower = line.lower().strip(": ")
        matched = False
        for sec, keywords in SECTION_HEADERS.items():
            if any(lower == kw or lower.startswith(kw) for kw in keywords):
                current = sec
                if current not in blocks:
                    blocks[current] = []
                matched = True
                break
        if not matched:
            blocks.setdefault(current, []).append(line)

    return blocks


# ---------------------------------------------------------------------------
# Individual extractors
# ---------------------------------------------------------------------------

def extract_email(text: str) -> str:
    m = EMAIL_RE.search(text)
    return m.group(0) if m else ""


def extract_phone(text: str) -> str:
    m = PHONE_RE.search(text)
    return _clean(m.group(0)) if m else ""


def extract_linkedin(text: str) -> str:
    m = LINKEDIN_RE.search(text)
    return ("https://" + m.group(0)) if m else ""


def extract_github(text: str) -> str:
    m = GITHUB_RE.search(text)
    return ("https://" + m.group(0)) if m else ""


def extract_name(text: str) -> str:
    """
    Try spaCy PERSON entity first; fall back to the first non-empty line
    that looks like a name (2-4 words, no digits, no email/url chars).
    """
    if NLP:
        doc = NLP(text[:1000])
        for ent in doc.ents:
            if ent.label_ == "PERSON" and len(ent.text.split()) >= 2:
                return _clean(ent.text)

    # Heuristic fallback
    for line in _split_lines(text[:500]):
        words = line.split()
        if (
            2 <= len(words) <= 4
            and not any(c in line for c in ["@", "http", "linkedin", "github", "+"])
            and not any(c.isdigit() for c in line)
            and all(w[0].isupper() for w in words if w)
        ):
            return _clean(line)
    return ""


def extract_skills(text: str) -> List[str]:
    """Match skills from the predefined database (case-insensitive)."""
    found = set()
    text_lower = text.lower()
    for lower_skill, original_skill in SKILL_LOWER.items():
        # Use word-boundary-aware search
        pattern = r"(?<![a-zA-Z0-9_])" + re.escape(lower_skill) + r"(?![a-zA-Z0-9_])"
        if re.search(pattern, text_lower):
            found.add(original_skill)
    return sorted(found)


def extract_section_lines(blocks: Dict[str, List[str]], section: str) -> List[str]:
    """Return cleaned, non-empty lines for a given section."""
    return [l for l in blocks.get(section, []) if l.strip()]


# ---------------------------------------------------------------------------
# Main extraction entry point
# ---------------------------------------------------------------------------

def extract_all(text: str) -> Dict:
    """
    Run all extractors on the raw resume text.
    Returns a dict with all structured fields.
    """
    lines = _split_lines(text)
    blocks = _section_blocks(lines)

    education_lines    = extract_section_lines(blocks, "education")
    experience_lines   = extract_section_lines(blocks, "experience")
    projects_lines     = extract_section_lines(blocks, "projects")
    certs_lines        = extract_section_lines(blocks, "certifications")

    return {
        "name":           extract_name(text),
        "email":          extract_email(text),
        "phone":          extract_phone(text),
        "linkedin":       extract_linkedin(text),
        "github":         extract_github(text),
        "skills":         extract_skills(text),
        "education":      "\n".join(education_lines),
        "experience":     "\n".join(experience_lines),
        "projects":       "\n".join(projects_lines),
        "certifications": "\n".join(certs_lines),
    }
