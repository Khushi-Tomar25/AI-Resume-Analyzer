"""
job_matcher.py - Transparent Job Description Matching Engine
-------------------------------------------------------------
Compares resume content against target Job Descriptions using a multi-factor
transparent algorithm:
1. Exact Skill Matching (40% weight)
2. Partial & Adjacent Technology Alignment (15% weight)
3. TF-IDF Vector Semantic Similarity (30% weight)
4. Keyword Relevance & Frequency Coverage (15% weight)

Identifies:
- Required Skills
- Exact Matching Skills
- Partial / Adjacent Skills
- Missing Skills
- Experience Requirements Alignment
- Keyword Relevance
- Job Compatibility Percentage (0-100%)

NOTE: Transparent methodology is fully explained and does not disguise keyword
overlap as black-box AI predictions.
"""

import re
from typing import Dict, List, Any, Tuple, Set
from collections import Counter

from skill_extractor import extract_skills_from_text, compare_resume_to_jd_skills
from utils import clean_text, extract_words, get_score_badge


# Related / Adjacent Technology Taxonomy Map for Partial Matches
RELATED_TECH_MAP: Dict[str, Set[str]] = {
    # Relational & SQL Databases
    "postgresql": {"mysql", "sqlite", "oracle", "mariadb", "microsoft sql server", "sql"},
    "mysql": {"postgresql", "sqlite", "oracle", "mariadb", "sql"},
    "sqlite": {"postgresql", "mysql", "sql"},
    "mongodb": {"dynamodb", "cassandra", "redis", "firebase"},
    # Frontend Frameworks
    "react": {"vue", "angular", "next.js", "svelte"},
    "vue": {"react", "angular", "nuxt.js"},
    "angular": {"react", "vue", "typescript"},
    "next.js": {"react", "node.js"},
    # Python Frameworks
    "fastapi": {"flask", "django", "tornado"},
    "flask": {"fastapi", "django"},
    "django": {"fastapi", "flask"},
    # Cloud Providers
    "aws": {"azure", "gcp", "google cloud"},
    "azure": {"aws", "gcp", "google cloud"},
    "gcp": {"aws", "azure", "google cloud"},
    # Container & Orchestration
    "kubernetes": {"docker", "helm", "openshift"},
    "docker": {"kubernetes", "podman", "containerization"},
    # Machine Learning Frameworks
    "pytorch": {"tensorflow", "keras", "scikit-learn"},
    "tensorflow": {"pytorch", "keras", "scikit-learn"},
    "scikit-learn": {"pandas", "numpy", "pytorch", "tensorflow"},
    # CI/CD Tools
    "github actions": {"gitlab ci", "jenkins", "circleci", "ci/cd"},
    "jenkins": {"github actions", "gitlab ci", "circleci", "ci/cd"},
    # Testing
    "pytest": {"unittest", "jest", "unit testing"},
    "jest": {"mocha", "cypress", "pytest"}
}


class JobMatcher:
    """
    Transparent, explainable job description matching and gap analysis engine.
    """

    def __init__(self):
        pass

    def compute_tfidf_similarity(self, resume_text: str, jd_text: str) -> float:
        """
        Calculates cosine similarity between resume and job description using TF-IDF.
        Falls back to pure-Python cosine similarity if needed.
        """
        clean_res = clean_text(resume_text)
        clean_jd = clean_text(jd_text)

        if not clean_res or not clean_jd:
            return 0.0

        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            vectorizer = TfidfVectorizer(
                stop_words="english",
                ngram_range=(1, 2),
                max_features=5000
            )
            tfidf_matrix = vectorizer.fit_transform([clean_res, clean_jd])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return round(float(similarity) * 100, 1)

        except Exception:
            res_words = Counter(extract_words(clean_res))
            jd_words = Counter(extract_words(clean_jd))
            all_words = set(res_words.keys()).union(set(jd_words.keys()))

            dot_product = sum(res_words[w] * jd_words[w] for w in all_words)
            mag_res = (sum(res_words[w] ** 2 for w in all_words)) ** 0.5
            mag_jd = (sum(jd_words[w] ** 2 for w in all_words)) ** 0.5

            if not mag_res or not mag_jd:
                return 0.0

            cosine_sim = dot_product / (mag_res * mag_jd)
            return round(float(cosine_sim) * 100, 1)

    def extract_experience_requirement(self, jd_text: str, resume_text: str) -> Dict[str, Any]:
        """
        Identifies years of experience mentioned in the job description and checks
        for corresponding signals in the resume.
        """
        exp_pattern = r"(\d+\+?(?:\s*-\s*\d+)?)\s*(?:years?|yrs?)(?:\s+of)?(?:\s+experience)?"
        jd_matches = re.findall(exp_pattern, jd_text, re.IGNORECASE)
        res_matches = re.findall(exp_pattern, resume_text, re.IGNORECASE)

        target_req = jd_matches[0].strip() if jd_matches else "Not specifically stated"
        resume_signal = res_matches[0].strip() if res_matches else "Experience demonstrated in roles"

        return {
            "required_experience": target_req,
            "resume_experience_signal": resume_signal,
            "aligned": bool(jd_matches and res_matches)
        }

    def find_partial_matches(self, resume_skills: List[str], missing_skills: List[str]) -> List[Dict[str, str]]:
        """
        Identifies partial/adjacent matches where the candidate has a closely related
        technology (e.g. has MySQL when JD asks for PostgreSQL).
        """
        res_skills_set = set(s.lower() for s in resume_skills)
        partial_matches = []

        for missing in missing_skills:
            m_lower = missing.lower()
            related_techs = RELATED_TECH_MAP.get(m_lower, set())
            overlap = related_techs.intersection(res_skills_set)
            if overlap:
                partial_matches.append({
                    "requested": missing,
                    "candidate_has": sorted(list(overlap))[0],
                    "relationship": f"Candidate possesses adjacent skill '{sorted(list(overlap))[0]}'"
                })

        return partial_matches

    def extract_top_jd_keywords(self, jd_text: str, top_n: int = 15) -> List[Tuple[str, int]]:
        """Extracts top non-trivial recurring keywords from the JD."""
        stopwords = {
            "and", "the", "with", "for", "that", "this", "from", "you", "your",
            "will", "have", "are", "our", "work", "team", "role", "looking",
            "experience", "years", "candidate", "about", "what", "must", "ability",
            "skills", "knowledge", "understanding", "strong", "preferred", "required",
            "including", "responsibilities", "qualifications"
        }
        words = [w for w in extract_words(jd_text) if len(w) > 2 and w not in stopwords]
        counter = Counter(words)
        return counter.most_common(top_n)

    def match(self, resume_text: str, jd_text: str) -> Dict[str, Any]:
        """
        Performs full multi-factor comparative analysis between resume and job description.
        Returns explainable metrics, matched, partial, and missing skills.
        """
        clean_res = clean_text(resume_text)
        clean_jd = clean_text(jd_text)

        if not clean_jd.strip():
            return {
                "error": "Job description is empty. Please paste a job description to calculate compatibility."
            }

        # 1. Direct Skill Extraction
        res_skills_info = extract_skills_from_text(clean_res)
        jd_skills_info = extract_skills_from_text(clean_jd)

        res_skills = res_skills_info["all_skills"]
        jd_skills = jd_skills_info["all_skills"]

        skills_comp = compare_resume_to_jd_skills(res_skills, jd_skills)
        matched_skills = skills_comp["matched_skills"]
        raw_missing_skills = skills_comp["missing_skills"]
        additional_skills = skills_comp["additional_skills"]

        # 2. Partial / Adjacent Skills Discovery
        partial_matches = self.find_partial_matches(res_skills, raw_missing_skills)
        partial_requested_keys = set(p["requested"].lower() for p in partial_matches)
        
        # Truly missing skills (neither exact nor partial)
        truly_missing = [s for s in raw_missing_skills if s.lower() not in partial_requested_keys]

        # 3. TF-IDF Semantic Similarity
        tfidf_score = self.compute_tfidf_similarity(clean_res, clean_jd)

        # 4. Keyword Relevance
        top_keywords = self.extract_top_jd_keywords(clean_jd, top_n=15)
        res_words_set = set(extract_words(clean_res))
        keyword_presence = {kw: (kw in res_words_set) for kw, _ in top_keywords}
        covered_kw_count = sum(1 for present in keyword_presence.values() if present)
        kw_coverage_pct = round((covered_kw_count / len(keyword_presence) * 100), 1) if keyword_presence else 100.0

        # 5. Experience Requirement Alignment
        exp_info = self.extract_experience_requirement(clean_jd, clean_res)

        # 6. Composite Job Compatibility Percentage
        # Formula:
        # - Exact Skills Match Rate: 40%
        # - Partial Skills Credit (half credit for adjacent tech): 15%
        # - TF-IDF Semantic Similarity: 30%
        # - Top Keyword Coverage: 15%
        total_jd_skills = max(1, len(jd_skills))
        exact_ratio = (len(matched_skills) / total_jd_skills) * 100
        partial_ratio = (len(partial_matches) / total_jd_skills) * 50  # 50% credit for partial

        composite_score = (
            (exact_ratio * 0.40) +
            (partial_ratio * 0.15) +
            (tfidf_score * 0.30) +
            (kw_coverage_pct * 0.15)
        )
        composite_score = round(max(0.0, min(100.0, composite_score)), 1)
        badge = get_score_badge(composite_score)

        # Methodology Explanation string
        methodology_explanation = (
            "Compatibility score calculated using a 4-factor hybrid formula: "
            "40% Exact Skill Overlap + 15% Partial/Adjacent Technology Credit + "
            "30% TF-IDF Semantic Vector Similarity + 15% Top Job Keyword Density."
        )

        # Actionable Tailoring Recommendations
        recommendations = []
        if truly_missing:
            top_missing = truly_missing[:5]
            recommendations.append(f"Add critical missing skills prominently: {', '.join(top_missing)}.")
        if partial_matches:
            first_p = partial_matches[0]
            recommendations.append(
                f"You have '{first_p['candidate_has']}' which is adjacent to requested '{first_p['requested']}'. "
                f"Explicitly mention your familiarity with {first_p['requested']} in your skills section."
            )
        if kw_coverage_pct < 65:
            missing_kws = [kw for kw, p in keyword_presence.items() if not p][:4]
            if missing_kws:
                recommendations.append(f"Weave high-frequency terms from the job post into your bullets: {', '.join(missing_kws)}.")
        if not recommendations:
            recommendations.append("Strong job alignment! Highlight your quantifiable outcomes that mirror the primary responsibilities.")

        return {
            "overall_match_score": composite_score,
            "badge": badge,
            "methodology_explanation": methodology_explanation,
            "required_skills": jd_skills,
            "matched_skills": matched_skills,
            "partial_matching_skills": partial_matches,
            "missing_skills": truly_missing,
            "additional_skills": additional_skills,
            "tfidf_similarity": tfidf_score,
            "skill_match_ratio": round(exact_ratio, 1),
            "keyword_coverage_pct": kw_coverage_pct,
            "experience_alignment": exp_info,
            "top_jd_keywords": top_keywords,
            "keyword_presence": keyword_presence,
            "recommendations": recommendations
        }


_default_matcher = JobMatcher()

def match_resume_to_job(resume_text: str, jd_text: str) -> Dict[str, Any]:
    """Convenience helper to match resume against job description."""
    return _default_matcher.match(resume_text, jd_text)
