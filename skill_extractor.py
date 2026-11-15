"""
skill_extractor.py - Configurable Skill Extraction & Categorization Engine
--------------------------------------------------------------------------
Identifies and categorizes technical skills, programming languages, frameworks,
tools, soft skills, and domain-specific concepts from resumes and job descriptions.
Features:
- Word-boundary safe pattern matching to prevent false positives
- Alias normalization (e.g., 'k8s' -> 'Kubernetes', 'js' -> 'JavaScript')
- Configurable skill dictionary with runtime extension support
"""

import re
from typing import Dict, List, Set, Tuple, Any, Optional
from config import SKILL_TAXONOMY, SKILL_ALIASES
from utils import clean_text


# Standardized Category Taxonomy
DEFAULT_TAXONOMY: Dict[str, List[str]] = {
    "Programming Languages": [
        "python", "java", "c++", "c#", "c", "javascript", "typescript", "go",
        "golang", "rust", "ruby", "php", "swift", "kotlin", "scala", "r",
        "matlab", "dart", "html", "html5", "css", "css3", "sass", "bash",
        "shell", "powershell", "perl", "sql"
    ],
    "Frameworks": [
        "react", "angular", "vue", "vue.js", "next.js", "nuxt.js", "node.js",
        "express", "express.js", "django", "flask", "fastapi", "spring",
        "spring boot", "ruby on rails", "asp.net", "laravel", "tailwind css",
        "bootstrap", "material-ui", "redux", "graphql", "rest api"
    ],
    "Tools": [
        "git", "github", "gitlab", "docker", "kubernetes", "k8s", "terraform",
        "ansible", "jenkins", "jira", "postman", "linux", "nginx", "apache",
        "prometheus", "grafana", "helm", "vscode", "visual studio", "circleci"
    ],
    "Technical & Domain Skills": [
        "cloud computing", "machine learning", "deep learning", "nlp",
        "natural language processing", "computer vision", "data analysis",
        "artificial intelligence", "data structures", "algorithms",
        "system design", "microservices", "agile", "scrum", "ci/cd",
        "object oriented programming", "oop", "test driven development", "tdd",
        "aws", "azure", "google cloud", "gcp", "postgresql", "mysql", "sqlite",
        "mongodb", "redis", "cassandra", "dynamodb", "elasticsearch",
        "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras",
        "llm", "large language models", "transformers", "rag", "embeddings",
        "prompt engineering", "tableau", "power bi"
    ],
    "Soft Skills": [
        "communication", "teamwork", "leadership", "problem solving",
        "critical thinking", "adaptability", "time management", "collaboration",
        "conflict resolution", "creativity", "work ethic", "attention to detail",
        "emotional intelligence", "decision making", "presentation skills",
        "negotiation", "mentorship", "project management"
    ]
}


class SkillExtractor:
    """
    Boundary-safe, configurable skill extraction engine.
    """

    def __init__(self, taxonomy: Optional[Dict[str, List[str]]] = None, aliases: Optional[Dict[str, str]] = None):
        self.taxonomy = taxonomy or DEFAULT_TAXONOMY
        self.aliases = aliases or SKILL_ALIASES
        self._compiled_patterns = self._compile_skill_patterns()

    def _compile_skill_patterns(self) -> Dict[str, Dict[str, re.Pattern]]:
        """
        Pre-compiles regex patterns for all skills to ensure fast, boundary-safe matching.
        Protects against false positives for short tokens like 'c', 'r', 'go', 'git'.
        """
        compiled = {}
        for category, skills in self.taxonomy.items():
            compiled[category] = {}
            for skill in skills:
                escaped = re.escape(skill)
                # Strict boundary for short / sensitive skill names
                if skill in ["c++", "c#", "c", "r", "go", "php", "git", "sql"]:
                    pattern = rf"(?<!\w){escaped}(?!\w)"
                else:
                    pattern = rf"\b{escaped}\b"
                compiled[category][skill] = re.compile(pattern, re.IGNORECASE)
        return compiled

    def add_custom_skills(self, category: str, skills: List[str]):
        """
        Allows dynamic runtime addition of custom skills to any category.
        """
        if category not in self.taxonomy:
            self.taxonomy[category] = []
        for s in skills:
            s_clean = s.strip().lower()
            if s_clean and s_clean not in self.taxonomy[category]:
                self.taxonomy[category].append(s_clean)
        self._compiled_patterns = self._compile_skill_patterns()

    def extract_skills(self, text: str) -> Dict[str, Any]:
        """
        Extracts all recognized skills from input text, normalizes aliases,
        and groups them by category without false positives.
        
        Returns:
            Dict containing:
                - 'all_skills': sorted list of unique normalized skills found
                - 'skills_by_category': dict mapping category -> list of skills found
                - 'total_skills_count': integer count of unique skills
                - 'category_distribution': count of skills per category
        """
        cleaned = clean_text(text)
        found_by_category: Dict[str, List[str]] = {cat: [] for cat in self.taxonomy.keys()}
        all_found_skills: Set[str] = set()

        # Match compiled patterns per category
        for category, skills_dict in self._compiled_patterns.items():
            for skill_name, pattern in skills_dict.items():
                if pattern.search(cleaned):
                    normalized = self.aliases.get(skill_name.lower(), skill_name)
                    if normalized not in found_by_category[category]:
                        found_by_category[category].append(normalized)
                    all_found_skills.add(normalized)

        # Check for alias matches (e.g. 'k8s' -> 'kubernetes')
        text_lower = cleaned.lower()
        for alias, canonical in self.aliases.items():
            alias_pattern = rf"(?<!\w){re.escape(alias)}(?!\w)"
            if re.search(alias_pattern, text_lower):
                all_found_skills.add(canonical)
                # Find canonical's category
                for cat, skills in self.taxonomy.items():
                    if canonical in [s.lower() for s in skills]:
                        if canonical not in found_by_category[cat]:
                            found_by_category[cat].append(canonical)

        # Sort all lists
        for cat in found_by_category:
            found_by_category[cat] = sorted(list(set(found_by_category[cat])))

        distribution = {
            cat: len(skills) for cat, skills in found_by_category.items() if len(skills) > 0
        }

        return {
            "all_skills": sorted(list(all_found_skills)),
            "skills_by_category": found_by_category,
            "total_skills_count": len(all_found_skills),
            "category_distribution": distribution
        }

    def compare_skills(self, resume_skills: List[str], target_skills: List[str]) -> Dict[str, Any]:
        """
        Compares resume skills against target job description skills.
        """
        res_set = set(s.lower() for s in resume_skills)
        target_set = set(s.lower() for s in target_skills)

        matched = sorted(list(res_set.intersection(target_set)))
        missing = sorted(list(target_set - res_set))
        additional = sorted(list(res_set - target_set))

        match_ratio = round((len(matched) / len(target_set) * 100), 1) if target_set else 100.0

        return {
            "matched_skills": matched,
            "missing_skills": missing,
            "additional_skills": additional,
            "match_ratio": match_ratio,
            "matched_count": len(matched),
            "missing_count": len(missing),
            "target_total_count": len(target_set)
        }


_default_extractor = SkillExtractor()

def extract_skills_from_text(text: str) -> Dict[str, Any]:
    """Convenience helper to extract categorized skills from text."""
    return _default_extractor.extract_skills(text)

def compare_resume_to_jd_skills(resume_skills: List[str], jd_skills: List[str]) -> Dict[str, Any]:
    """Convenience helper to compare resume skills against job description skills."""
    return _default_extractor.compare_skills(resume_skills, jd_skills)

def add_custom_skills_to_dictionary(category: str, skills: List[str]):
    """Extends the skill extractor taxonomy with custom skills."""
    _default_extractor.add_custom_skills(category, skills)
