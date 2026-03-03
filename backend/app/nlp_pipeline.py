import re
from datetime import datetime


ACTION_VERBS = [
    "built", "developed", "implemented", "designed", "optimized", "improved", "reduced", "increased",
    "led", "created", "automated", "deployed", "tested", "debugged", "analyzed", "integrated",
]

ROLE_PROFILES = {
    "Software Engineering Intern": {
        "keywords": [
            "python", "javascript", "react", "fastapi", "sql", "git", "docker", "linux",
            "testing", "pytest", "api", "rest", "ci", "aws", "postgres",
        ]
    },
    "Backend Engineer": {
        "keywords": [
            "python", "java", "go", "sql", "postgres", "mysql", "rest", "api",
            "docker", "kubernetes", "aws", "system design", "microservices", "redis", "linux",
        ]
    },
    "Frontend Engineer": {
        "keywords": [
            "javascript", "typescript", "react", "html", "css", "frontend", "ui",
            "accessibility", "redux", "next.js", "testing", "jest", "figma", "api",
        ]
    },
    "Full Stack Engineer": {
        "keywords": [
            "javascript", "typescript", "react", "node.js", "python", "sql", "postgres",
            "api", "docker", "aws", "frontend", "backend", "testing", "git",
        ]
    },
    "Data/AI Intern": {
        "keywords": [
            "python", "pandas", "numpy", "sql", "ml", "nlp", "sklearn", "tensorflow", "pytorch",
            "data cleaning", "feature engineering", "evaluation", "etl",
        ]
    },
    "Data Scientist": {
        "keywords": [
            "python", "pandas", "numpy", "sql", "machine learning", "statistics", "sklearn",
            "tensorflow", "pytorch", "data visualization", "experimentation", "nlp", "evaluation",
        ]
    },
    "Machine Learning Engineer": {
        "keywords": [
            "python", "pytorch", "tensorflow", "ml", "feature engineering", "deployment", "docker",
            "aws", "api", "evaluation", "data pipelines", "sql", "nlp",
        ]
    },
    "DevOps Engineer": {
        "keywords": [
            "aws", "azure", "gcp", "docker", "kubernetes", "linux", "terraform", "ci", "cd",
            "monitoring", "python", "bash", "git", "networking",
        ]
    },
}

SECTION_PATTERNS = {
    "education": r"\b(education|academic)\b",
    "experience": r"\b(experience|employment|work history)\b",
    "projects": r"\b(projects|project experience)\b",
    "skills": r"\b(skills|technologies|tools)\b",
    "certifications": r"\b(certifications|certificates)\b",
}

SKILL_PATTERNS = {
    "aws": [r"\baws\b", r"\bamazon web services\b"],
    "api": [r"\bapi\b", r"\bapis\b"],
    "azure": [r"\bazure\b"],
    "bash": [r"\bbash\b", r"\bshell scripting\b"],
    "c": [r"(?<!\+)\bc\b(?!\+)"],
    "c#": [r"\bc#\b", r"\bc sharp\b"],
    "c++": [r"\bc\+\+\b"],
    "ci/cd": [r"\bci/cd\b", r"\bcontinuous integration\b", r"\bcontinuous deployment\b"],
    "css": [r"\bcss\b"],
    "data analysis": [r"\bdata analysis\b", r"\bdata analytics\b"],
    "data structures": [r"\bdata structures\b"],
    "django": [r"\bdjango\b"],
    "docker": [r"\bdocker\b"],
    "etl": [r"\betl\b"],
    "express": [r"\bexpress(?:\.js)?\b"],
    "figma": [r"\bfigma\b"],
    "fastapi": [r"\bfastapi\b"],
    "flask": [r"\bflask\b"],
    "gitlab": [r"\bgitlab\b"],
    "gcp": [r"\bgcp\b", r"\bgoogle cloud\b"],
    "git": [r"\bgit\b", r"\bgithub\b"],
    "go": [r"\bgolang\b"],
    "graphql": [r"\bgraphql\b"],
    "html": [r"\bhtml\b"],
    "java": [r"\bjava\b", r"\bcore java\b"],
    "javascript": [r"\bjavascript\b"],
    "jira": [r"\bjira\b"],
    "jest": [r"\bjest\b"],
    "linux": [r"\blinux\b", r"\bunix\b"],
    "kubernetes": [r"\bkubernetes\b", r"\bk8s\b"],
    "machine learning": [r"\bmachine learning\b", r"\bml\b"],
    "mongodb": [r"\bmongodb\b", r"\bmongo\b"],
    "mysql": [r"\bmysql\b"],
    "next.js": [r"\bnext\.?js\b"],
    "node.js": [r"\bnode\.?js\b", r"\bnodejs\b"],
    "numpy": [r"\bnumpy\b"],
    "oop": [r"\boop\b", r"\bobject oriented\b", r"\bobject-oriented\b"],
    "pandas": [r"\bpandas\b"],
    "postgres": [r"\bpostgres\b", r"\bpostgresql\b"],
    "python": [r"\bpython\b"],
    "pytorch": [r"\bpytorch\b"],
    "react": [r"\breact\b"],
    "redis": [r"\bredis\b"],
    "redux": [r"\bredux\b"],
    "rest": [r"\brest\b", r"\brest api\b"],
    "scikit-learn": [r"\bscikit-learn\b", r"\bsklearn\b"],
    "selenium": [r"\bselenium\b"],
    "spring": [r"\bspring\b", r"\bspring boot\b"],
    "sql": [r"\bsql\b"],
    "tableau": [r"\btableau\b"],
    "terraform": [r"\bterraform\b"],
    "tensorflow": [r"\btensorflow\b"],
    "testing": [r"\btesting\b", r"\bunit test(?:ing)?\b"],
    "typescript": [r"\btypescript\b"],
    "ui/ux": [r"\bui/ux\b", r"\buser experience\b", r"\buser interface\b"],
    "webpack": [r"\bwebpack\b"],
}

SKILL_ALIASES = {
    "amazon web services": "aws",
    "aws": "aws",
    "azure": "azure",
    "api": "api",
    "apis": "api",
    "bash": "bash",
    "shell scripting": "bash",
    "c": "c",
    "c#": "c#",
    "c sharp": "c#",
    "c++": "c++",
    "ci/cd": "ci/cd",
    "continuous integration": "ci/cd",
    "continuous deployment": "ci/cd",
    "css": "css",
    "data analysis": "data analysis",
    "data analytics": "data analysis",
    "data structures": "data structures",
    "django": "django",
    "docker": "docker",
    "etl": "etl",
    "express": "express",
    "express.js": "express",
    "figma": "figma",
    "fastapi": "fastapi",
    "flask": "flask",
    "gcp": "gcp",
    "google cloud": "gcp",
    "git": "git",
    "github": "git",
    "gitlab": "gitlab",
    "go": "go",
    "golang": "go",
    "graphql": "graphql",
    "html": "html",
    "java": "java",
    "javascript": "javascript",
    "jira": "jira",
    "jest": "jest",
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",
    "linux": "linux",
    "unix": "linux",
    "machine learning": "machine learning",
    "ml": "machine learning",
    "mongodb": "mongodb",
    "mongo": "mongodb",
    "mysql": "mysql",
    "next.js": "next.js",
    "nextjs": "next.js",
    "node.js": "node.js",
    "nodejs": "node.js",
    "numpy": "numpy",
    "oop": "oop",
    "object oriented": "oop",
    "object-oriented": "oop",
    "pandas": "pandas",
    "postgres": "postgres",
    "postgresql": "postgres",
    "python": "python",
    "pytorch": "pytorch",
    "react": "react",
    "redis": "redis",
    "redux": "redux",
    "rest": "rest",
    "rest api": "rest",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "selenium": "selenium",
    "spring": "spring",
    "spring boot": "spring",
    "sql": "sql",
    "tableau": "tableau",
    "terraform": "terraform",
    "tensorflow": "tensorflow",
    "testing": "testing",
    "typescript": "typescript",
    "ui/ux": "ui/ux",
    "user experience": "ui/ux",
    "user interface": "ui/ux",
    "webpack": "webpack",
}

SKILL_SECTION_STOPWORDS = {
    "skills", "technical skills", "technologies", "tools", "frameworks", "languages",
    "coursework", "education", "experience", "projects", "summary", "profile",
    "technical", "stack", "core competencies", "competencies", "proficient", "familiar",
}
SKILL_TOKEN_STOPWORDS = {
    "and", "or", "with", "using", "used", "in", "of", "to", "for", "the", "a", "an",
    "strong", "knowledge", "experience", "proficiency", "skills", "tools", "frameworks",
    "languages", "platforms", "libraries", "technologies", "working", "understanding",
}
SKILL_HEADING_CATEGORY_MAP = {
    "programming languages": "programming_languages",
    "programming language": "programming_languages",
    "languages": "programming_languages",
    "language": "programming_languages",
    "frameworks/libraries": "frameworks_libraries",
    "frameworks": "frameworks_libraries",
    "framework": "frameworks_libraries",
    "libraries": "frameworks_libraries",
    "library": "frameworks_libraries",
    "databases": "databases",
    "database": "databases",
    "cloud/devops": "cloud_devops",
    "cloud": "cloud_devops",
    "devops": "cloud_devops",
    "infrastructure": "cloud_devops",
    "infra": "cloud_devops",
    "tools/platforms": "tools_platforms",
    "tools": "tools_platforms",
    "platforms": "tools_platforms",
    "platform": "tools_platforms",
    "technologies": "tools_platforms",
}
SKILL_CATEGORY_ORDER = [
    "programming_languages",
    "frameworks_libraries",
    "databases",
    "cloud_devops",
    "tools_platforms",
    "other",
]
SKILL_CATEGORY_LABELS = {
    "programming_languages": "Programming languages",
    "frameworks_libraries": "Frameworks and libraries",
    "databases": "Databases",
    "cloud_devops": "Cloud and DevOps",
    "tools_platforms": "Tools and platforms",
    "other": "Other skills",
}
SKILL_CATEGORY_MAP = {
    "api": "other",
    "aws": "cloud_devops",
    "azure": "cloud_devops",
    "bash": "programming_languages",
    "c": "programming_languages",
    "c#": "programming_languages",
    "c++": "programming_languages",
    "ci/cd": "cloud_devops",
    "css": "programming_languages",
    "data analysis": "other",
    "data structures": "other",
    "django": "frameworks_libraries",
    "docker": "cloud_devops",
    "etl": "other",
    "express": "frameworks_libraries",
    "fastapi": "frameworks_libraries",
    "figma": "tools_platforms",
    "flask": "frameworks_libraries",
    "gcp": "cloud_devops",
    "git": "tools_platforms",
    "gitlab": "tools_platforms",
    "go": "programming_languages",
    "graphql": "frameworks_libraries",
    "html": "programming_languages",
    "java": "programming_languages",
    "javascript": "programming_languages",
    "jest": "frameworks_libraries",
    "jira": "tools_platforms",
    "kubernetes": "cloud_devops",
    "linux": "tools_platforms",
    "machine learning": "other",
    "mongodb": "databases",
    "mysql": "databases",
    "next.js": "frameworks_libraries",
    "node.js": "frameworks_libraries",
    "numpy": "frameworks_libraries",
    "oop": "other",
    "pandas": "frameworks_libraries",
    "postgres": "databases",
    "python": "programming_languages",
    "pytorch": "frameworks_libraries",
    "react": "frameworks_libraries",
    "redis": "databases",
    "redux": "frameworks_libraries",
    "rest": "other",
    "scikit-learn": "frameworks_libraries",
    "selenium": "frameworks_libraries",
    "spring": "frameworks_libraries",
    "sql": "programming_languages",
    "tableau": "tools_platforms",
    "terraform": "cloud_devops",
    "tensorflow": "frameworks_libraries",
    "testing": "other",
    "typescript": "programming_languages",
    "ui/ux": "other",
    "webpack": "tools_platforms",
}

DEGREE_PATTERNS = {
    "bachelor": r"\b(bachelor(?:'s)?|b\.?\s?tech|b\.?\s?e\.?|b\.?\s?s\.?|bsc|bca|bs\b|be\b)\b",
    "master": r"\b(master(?:'s)?|m\.?\s?tech|m\.?\s?e\.?|m\.?\s?s\.?|msc|mca|mba|ms\b|me\b)\b",
    "phd": r"\b(phd|ph\.?\s?d\.?|doctorate|doctoral)\b",
    "diploma": r"\b(diploma|associate(?:'s)?|associates)\b",
}

GRADUATED_PATTERNS = re.compile(r"\b(graduated|completed|earned|alumni)\b", re.IGNORECASE)
NOT_GRADUATED_PATTERNS = re.compile(
    r"\b(expected|expected graduation|pursuing|candidate|currently enrolled|in progress|anticipated)\b",
    re.IGNORECASE,
)
INSTITUTION_RE = re.compile(r"\b(university|college|institute|school)\b", re.IGNORECASE)
EDUCATION_CONTEXT_RE = re.compile(
    r"\b(education|academic|degree|gpa|cgpa|major|minor|bachelor|master|phd|doctorate|diploma|associate|graduat|expected)\b",
    re.IGNORECASE,
)
URL_RE = re.compile(r"(https?://\S+|www\.\S+)", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w+\b")
NUMBER_RE = re.compile(r"(\d+(\.\d+)?)(%|ms|s|x|k|m|usd|\$)?", re.IGNORECASE)
YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")
NAME_TOKEN_RE = re.compile(r"^[A-Za-z][A-Za-z'`.-]*$")
NAME_STOPWORDS = {
    "resume", "curriculum", "vitae", "profile", "summary", "experience", "education",
    "skills", "projects", "contact", "intern", "engineer", "developer", "scientist",
}
NEGATIVE_DOC_PATTERNS = {
    "cover_letter": re.compile(r"\b(cover letter|dear hiring manager|dear recruiter|sincerely|to whom it may concern)\b", re.IGNORECASE),
    "invoice": re.compile(r"\b(invoice|bill to|amount due|payment terms|subtotal|tax invoice)\b", re.IGNORECASE),
    "contract": re.compile(r"\b(agreement|contract|party of the first part|terms and conditions|effective date)\b", re.IGNORECASE),
    "job_description": re.compile(r"\b(responsibilities|requirements|qualifications|job description|about the role)\b", re.IGNORECASE),
}


def detect_sections(text: str) -> dict:
    t = text.lower()
    present = {}
    for key, pattern in SECTION_PATTERNS.items():
        present[key] = bool(re.search(pattern, t))
    return present


def detect_resume_document(text: str) -> dict:
    lower = text.lower()
    sections = detect_sections(text)
    emails = EMAIL_RE.findall(text)
    years = YEAR_RE.findall(text)
    bullets = split_bullets(text)

    score = 0.0
    reasons = []
    negatives = []

    if emails:
        score += 0.2
        reasons.append("contact information found")
    if sections.get("education"):
        score += 0.18
        reasons.append("education section found")
    if sections.get("experience"):
        score += 0.22
        reasons.append("experience section found")
    if sections.get("skills"):
        score += 0.18
        reasons.append("skills section found")
    if sections.get("projects"):
        score += 0.08
        reasons.append("projects section found")
    if years:
        score += 0.08
        reasons.append("date/year information found")
    if bullets:
        score += 0.06
        reasons.append("bullet points found")

    doc_type = "resume"
    negative_hits = 0
    for label, pattern in NEGATIVE_DOC_PATTERNS.items():
        if pattern.search(lower):
            negative_hits += 1
            negatives.append(label.replace("_", " "))
            doc_type = label

    score -= 0.18 * negative_hits
    score = max(0.0, min(1.0, score))
    is_resume = score >= 0.55 and not (doc_type != "resume" and score < 0.75)
    reason_parts = reasons[:4]
    if negatives:
        reason_parts.append(f"negative signals: {', '.join(negatives[:2])}")

    return {
        "is_resume": is_resume,
        "document_type": "resume" if is_resume else doc_type,
        "confidence": round(score, 3),
        "reason": "; ".join(reason_parts) if reason_parts else "Not enough resume signals found.",
    }


def extract_links(text: str) -> dict:
    urls = URL_RE.findall(text)
    emails = EMAIL_RE.findall(text)
    github = [u for u in urls if "github.com" in u.lower()]
    linkedin = [u for u in urls if "linkedin.com" in u.lower()]
    portfolio = [u for u in urls if any(x in u.lower() for x in ["vercel.app", "netlify.app", "portfolio", "about.me"])]
    return {
        "emails": list(dict.fromkeys(emails)),
        "urls": list(dict.fromkeys(urls)),
        "github": list(dict.fromkeys(github)),
        "linkedin": list(dict.fromkeys(linkedin)),
        "portfolio": list(dict.fromkeys(portfolio)),
    }


def slugify_handle(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "candidate"


def _looks_like_name_line(line: str) -> bool:
    stripped = " ".join(line.strip().split())
    if not stripped or len(stripped) > 60:
        return False
    if EMAIL_RE.search(stripped) or URL_RE.search(stripped) or any(ch.isdigit() for ch in stripped):
        return False

    tokens = [token.strip(".,") for token in stripped.replace("|", " ").split() if token.strip(".,")]
    if not 2 <= len(tokens) <= 4:
        return False

    normalized_tokens = []
    for token in tokens:
        if not NAME_TOKEN_RE.match(token):
            return False
        lowered = token.lower()
        if lowered in NAME_STOPWORDS:
            return False
        normalized_tokens.append(lowered)

    if len(set(normalized_tokens)) == 1:
        return False
    return True


def _normalize_name(line: str) -> str:
    tokens = [token.strip(".,") for token in line.replace("|", " ").split() if token.strip(".,")]
    normalized = []
    for token in tokens:
        if len(token) == 1:
            normalized.append(token.upper())
        elif token.isupper() or token.islower():
            normalized.append(token.capitalize())
        else:
            normalized.append(token[0].upper() + token[1:])
    return " ".join(normalized)


def _name_from_email(email: str | None) -> str | None:
    if not email:
        return None
    local = email.split("@", 1)[0]
    parts = [part for part in re.split(r"[._-]+", local) if part]
    if not 2 <= len(parts) <= 4:
        return None
    if any(any(ch.isdigit() for ch in part) for part in parts):
        return None
    if any(part.lower() in NAME_STOPWORDS for part in parts):
        return None
    return " ".join(part.capitalize() for part in parts)


def _name_from_slug(value: str | None) -> str | None:
    if not value:
        return None
    parts = [part for part in re.split(r"[^A-Za-z]+", value) if part]
    if not 2 <= len(parts) <= 4:
        return None
    filtered = [part for part in parts if part.lower() not in NAME_STOPWORDS]
    if not 2 <= len(filtered) <= 4:
        return None
    return " ".join(part.capitalize() for part in filtered)


def extract_identity(text: str, filename: str = "", facts: dict | None = None) -> dict:
    facts = facts or {}
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    emails = EMAIL_RE.findall(text)
    name = (facts.get("name") or "").strip() or None

    if not name:
        for line in lines[:12]:
            if _looks_like_name_line(line):
                name = _normalize_name(line)
                break

    if not name:
        for line in lines[:5]:
            cleaned = re.sub(r"[^A-Za-z\s'`.-]", " ", line)
            cleaned = " ".join(cleaned.split())
            if _looks_like_name_line(cleaned):
                name = _normalize_name(cleaned)
                break

    email = (facts.get("email") or "").strip() or (emails[0] if emails else None)
    filename_stem = re.sub(r"\.[^.]+$", "", filename).strip()
    if not name:
        name = _name_from_email(email)
    if not name:
        name = _name_from_slug(filename_stem)

    if name:
        base_handle = slugify_handle(name)
    elif email:
        base_handle = slugify_handle(email.split("@", 1)[0])
    elif filename_stem:
        base_handle = slugify_handle(filename_stem)
    else:
        base_handle = "candidate"

    if not name:
        name = _name_from_slug(base_handle)

    return {
        "name": name,
        "email": email,
        "derived_handle": base_handle,
    }


def split_bullets(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    bullets = []
    for line in lines:
        if line.startswith(("-", "•", "*")) or re.match(r"^\d+\.", line):
            bullets.append(re.sub(r"^(-|•|\*|\d+\.)\s*", "", line).strip())
    return bullets


def skill_match(resume_text: str, target_role: str) -> dict:
    profile = ROLE_PROFILES.get(target_role) or ROLE_PROFILES["Software Engineering Intern"]
    role_keywords = profile["keywords"]

    text = resume_text.lower()
    matched = [kw for kw in role_keywords if kw in text]
    missing = [kw for kw in role_keywords if kw not in matched]
    score = len(matched) / max(1, len(role_keywords))
    return {"matched": matched, "missing": missing, "score": round(score, 3)}


def extract_skills(text: str, facts: dict | None = None) -> dict:
    facts = facts or {}
    normalized = text.lower()
    categorized = {category: [] for category in SKILL_CATEGORY_ORDER}
    for skill, patterns in SKILL_PATTERNS.items():
        if any(re.search(pattern, normalized, re.IGNORECASE) for pattern in patterns):
            _add_skill_to_category(categorized, skill)
    section_skills, section_categories = _extract_skills_from_sections(text)
    fact_skills = _normalize_fact_skills([str(value) for value in facts.get("skills", [])])
    fact_skill_groups = _normalize_fact_skill_groups(facts.get("skill_groups"))
    for skill in section_skills:
        _add_skill_to_category(categorized, skill)
    for category, values in section_categories.items():
        for value in values:
            _add_skill_to_category(categorized, value, preferred_category=category)
    for skill in fact_skills:
        _add_skill_to_category(categorized, skill)
    for category, values in fact_skill_groups.items():
        for value in values:
            _add_skill_to_category(categorized, value, preferred_category=category)
    categorized = {key: sorted(dict.fromkeys(values)) for key, values in categorized.items()}
    detected = []
    for category in SKILL_CATEGORY_ORDER:
        detected.extend(categorized[category])
    detected = sorted(dict.fromkeys(detected))
    return {
        "detected": detected,
        "count": len(detected),
        "section_detected": sorted(section_skills),
        "llm_detected": sorted(fact_skills),
        "categorized": categorized,
        "category_labels": SKILL_CATEGORY_LABELS,
    }


def _normalize_skill_label(value: str) -> str | None:
    cleaned = " ".join(value.strip().lower().split())
    cleaned = cleaned.strip(" .,:;-")
    if not cleaned:
        return None
    if re.fullmatch(r"\d{4}", cleaned) or re.fullmatch(r"\d+%?", cleaned):
        return None
    if len(cleaned) > 32:
        return None
    if cleaned in SKILL_SECTION_STOPWORDS or cleaned in SKILL_TOKEN_STOPWORDS:
        return None
    alias = SKILL_ALIASES.get(cleaned)
    if alias:
        return alias
    if not re.fullmatch(r"[a-z0-9.+#/ -]+", cleaned):
        return None
    tokens = [token for token in re.split(r"\s+", cleaned) if token]
    if not 1 <= len(tokens) <= 4:
        return None
    if all(token in SKILL_TOKEN_STOPWORDS for token in tokens):
        return None
    return cleaned


def _normalize_fact_skills(values: list[str]) -> list[str]:
    normalized = []
    for value in values:
        skill = _normalize_skill_label(str(value))
        if skill:
            normalized.append(skill)
    return sorted(dict.fromkeys(normalized))


def _normalize_fact_skill_groups(raw_value) -> dict[str, list[str]]:
    if not isinstance(raw_value, dict):
        return {}
    normalized = {}
    for raw_key, raw_items in raw_value.items():
        category = _skill_category_from_heading(str(raw_key))
        if not category:
            continue
        values = raw_items if isinstance(raw_items, list) else [raw_items]
        skills = _normalize_fact_skills([str(item) for item in values])
        if skills:
            normalized[category] = skills
    return normalized


def _add_skill_to_category(categorized: dict[str, list[str]], skill: str, preferred_category: str | None = None):
    category = preferred_category or SKILL_CATEGORY_MAP.get(skill) or "other"
    categorized.setdefault(category, []).append(skill)


def _extract_skills_from_sections(text: str) -> tuple[list[str], dict[str, list[str]]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    collected = []
    categorized = {category: [] for category in SKILL_CATEGORY_ORDER}
    in_skills_block = False

    for line in lines:
        lower = line.lower()
        if re.search(SECTION_PATTERNS["skills"], lower):
            in_skills_block = True
            heading_category, found = _skills_from_line(line)
            collected.extend(found)
            for skill in found:
                _add_skill_to_category(categorized, skill, preferred_category=heading_category)
            continue

        if in_skills_block and re.match(r"^[A-Z][A-Za-z ]+$", line) and len(line.split()) <= 4:
            break

        if in_skills_block:
            heading_category, extracted = _skills_from_line(line)
            if extracted:
                collected.extend(extracted)
                for skill in extracted:
                    _add_skill_to_category(categorized, skill, preferred_category=heading_category)
            elif len(line.split()) > 18:
                break

    return sorted(dict.fromkeys(collected)), {
        key: sorted(dict.fromkeys(values))
        for key, values in categorized.items()
        if values
    }


def _skills_from_line(line: str) -> list[str]:
    cleaned = line.replace("|", ",").replace("/", ",").replace("•", ",")
    cleaned = re.sub(r"^[A-Za-z ]{1,25}:\s*", "", cleaned).strip()
    parts = [part.strip(" .:-") for part in re.split(r",|;|\u2022", cleaned) if part.strip(" .:-")]

    found = []
    for part in parts:
        lower = part.lower().strip()
        if lower in SKILL_SECTION_STOPWORDS:
            continue
        normalized = _normalize_skill_label(lower)
        if normalized:
            found.append(normalized)

    return found


def _skill_category_from_heading(heading: str) -> str | None:
    cleaned = " ".join(heading.strip().lower().split()).strip(" .:-")
    if not cleaned:
        return None
    for key, category in SKILL_HEADING_CATEGORY_MAP.items():
        if key in cleaned:
            return category
    return None


def _split_skill_candidates(value: str) -> list[str]:
    prepared = value.replace("|", ",").replace("â€¢", ",").replace("\u2022", ",")
    prepared = re.sub(r"\s{2,}", ",", prepared)
    prepared = re.sub(r"\s+-\s+", ",", prepared)
    return [
        part.strip(" .:-")
        for part in re.split(r",|;|\n", prepared)
        if part.strip(" .:-")
    ]


def _skills_from_line(line: str) -> tuple[str | None, list[str]]:
    content = line.strip()
    heading_category = None
    if ":" in content:
        heading, remainder = content.split(":", 1)
        heading_category = _skill_category_from_heading(heading)
        if heading_category:
            content = remainder.strip()

    parts = _split_skill_candidates(content)
    found = []
    for part in parts:
        lower = part.lower().strip()
        if lower in SKILL_SECTION_STOPWORDS or len(lower) > 40:
            continue
        normalized = _normalize_skill_label(lower)
        if normalized:
            found.append(normalized)

    return heading_category, found


def _normalized_degrees_from_text(education_blob: str) -> list[str]:
    found = [
        label for label, pattern in DEGREE_PATTERNS.items()
        if re.search(pattern, education_blob, re.IGNORECASE)
    ]
    found = list(dict.fromkeys(found))
    if any(degree in found for degree in ["bachelor", "master", "phd"]) and "diploma" in found:
        found = [degree for degree in found if degree != "diploma"]
    priority = {"phd": 0, "master": 1, "bachelor": 2, "diploma": 3}
    found.sort(key=lambda degree: priority.get(degree, 99))
    return found


def _pick_relevant_education_lines(lines: list[str]) -> list[str]:
    picked = []
    in_education_block = False
    for line in lines:
        lower = line.lower()
        if re.search(SECTION_PATTERNS["education"], lower):
            in_education_block = True
            picked.append(line)
            continue
        if in_education_block and re.match(r"^[A-Z][A-Za-z ]+$", line) and len(line.split()) <= 3:
            break
        if INSTITUTION_RE.search(line) or EDUCATION_CONTEXT_RE.search(line):
            picked.append(line)
            continue
        if in_education_block and YEAR_RE.search(line):
            picked.append(line)

    return list(dict.fromkeys(picked))


def _highest_degree(degrees: list[str]) -> str | None:
    for degree in ["phd", "master", "bachelor", "diploma"]:
        if degree in degrees:
            return degree
    return None


def extract_education(text: str, facts: dict | None = None) -> dict:
    facts = facts or {}
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    education_lines = _pick_relevant_education_lines(lines)
    education_blob = "\n".join(education_lines) if education_lines else ""

    degrees = _normalized_degrees_from_text(education_blob)
    fact_degrees = [str(degree).strip().lower() for degree in facts.get("degrees", []) if str(degree).strip()]
    if fact_degrees:
        normalized_fact_degrees = [degree for degree in ["phd", "master", "bachelor", "diploma"] if degree in fact_degrees]
        if normalized_fact_degrees:
            degrees = normalized_fact_degrees

    highest_degree = _highest_degree(degrees)

    years = [int(match) for match in YEAR_RE.findall(education_blob)]
    current_year = datetime.utcnow().year
    graduation_year = facts.get("graduation_year")
    if graduation_year is None:
        graduation_year = max([year for year in years if year <= current_year], default=None)

    expected_graduation = facts.get("expected_graduation")
    has_not_graduated_signal = bool(NOT_GRADUATED_PATTERNS.search(education_blob)) or bool(expected_graduation)
    graduated = facts.get("graduated")
    if graduated is None:
        graduated = bool(degrees) and not has_not_graduated_signal
        if graduated and graduation_year is None and not GRADUATED_PATTERNS.search(education_blob):
            graduated = False
        if not graduated and graduation_year is not None and not has_not_graduated_signal:
            graduated = True

    return {
        "degrees": degrees,
        "highest_degree": highest_degree,
        "graduated": bool(graduated),
        "graduation_year": graduation_year,
        "expected_graduation": bool(expected_graduation) if expected_graduation is not None else has_not_graduated_signal,
        "evidence_lines": education_lines[:5],
    }


def compute_signals(resume_text: str, target_role: str, filename: str = "", facts: dict | None = None) -> dict:
    facts = facts or {}
    bullets = split_bullets(resume_text)
    bullet_count = len(bullets)
    bullets_with_numbers = sum(1 for bullet in bullets if NUMBER_RE.search(bullet))
    action_verb_bullets = 0
    for bullet in bullets:
        first = bullet.split()[:1]
        if first and first[0].lower().strip(",.") in ACTION_VERBS:
            action_verb_bullets += 1

    avg_words = sum(len(bullet.split()) for bullet in bullets) / bullet_count if bullet_count else 0.0
    sections = detect_sections(resume_text)
    links = extract_links(resume_text)
    identity = extract_identity(resume_text, filename=filename, facts=facts)
    role = skill_match(resume_text, target_role)
    skills = extract_skills(resume_text, facts=facts)
    education = extract_education(resume_text, facts=facts)

    clarity = min(
        1.0,
        0.4 + (0.3 if avg_words <= 22 else 0.1) + (0.3 if action_verb_bullets / max(1, bullet_count) >= 0.4 else 0.1),
    )
    impact = min(1.0, bullets_with_numbers / max(1, bullet_count))
    evidence = min(
        1.0,
        (0.5 if links["github"] else 0.2) + (0.3 if links["linkedin"] else 0.1) + (0.2 if links["portfolio"] else 0.0),
    )
    ats = role["score"]
    overall = round(0.35 * ats + 0.25 * impact + 0.25 * clarity + 0.15 * evidence, 3)

    return {
        "target_role": target_role,
        "identity": identity,
        "sections": sections,
        "links": links,
        "skills": skills,
        "education": education,
        "bullets": {
            "count": bullet_count,
            "avg_words": round(avg_words, 2),
            "with_numbers": bullets_with_numbers,
            "verb_first": action_verb_bullets,
        },
        "keywords": role,
        "scores": {
            "ats": round(ats, 3),
            "impact": round(impact, 3),
            "clarity": round(clarity, 3),
            "evidence": round(evidence, 3),
            "overall": overall,
        },
    }
