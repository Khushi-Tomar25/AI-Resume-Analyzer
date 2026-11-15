"""
ats_scorer.py - Transparent ATS Compatibility Scoring Engine
-------------------------------------------------------------
Calculates an estimated ATS Compatibility Score (0 - 100) using a transparent,
explainable multi-pillar heuristic methodology:
1. Contact Information & Online Presence (10 pts)
2. Section Completeness & Education/Work Details (20 pts)
3. Action Verbs & Leadership Phrasing (15 pts)
4. Quantifiable Achievements & Measurable Impact (20 pts)
5. Skills Keyword Density & Domain Coverage (20 pts)
6. Document Structure & Readability (15 pts)

IMPORTANT DISCLAIMER:
This score is an independent estimate based on industry resume best practices and
heuristic algorithms. It is not an official score from any commercial ATS vendor
(such as Workday, Taleo, Greenhouse, or iCIMS).
"""

from typing import Dict, List, Any
from config import (
    ATS_WEIGHTS,
    OPTIMAL_WORD_COUNT_MIN,
    OPTIMAL_WORD_COUNT_MAX
)
from utils import (
    count_action_verbs,
    extract_quantified_achievements,
    get_score_badge
)
from skill_extractor import extract_skills_from_text


# Category weights (Sum = 100)
SCORING_WEIGHTS = {
    "contact_info": 10,
    "section_completeness": 20,
    "action_verbs": 15,
    "quantified_impact": 20,
    "skills_density": 20,
    "document_readability": 15
}

METHODOLOGY_DISCLAIMER = (
    "Estimated ATS Compatibility Score based on ResumeAI's transparent multi-pillar heuristic methodology. "
    "This is an objective benchmark and is not affiliated with or endorsed by any proprietary commercial ATS vendor "
    "(such as Workday, Taleo, Greenhouse, or Lever)."
)


class ATSScorer:
    """
    Transparent, explainable ATS compatibility evaluator.
    Independent of external AI APIs for 100% offline reliability.
    """

    def __init__(self, weights: Dict[str, int] = None):
        self.weights = weights or SCORING_WEIGHTS

    def score_contact_info(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluates contact details presence (Max 10 pts)."""
        max_score = self.weights["contact_info"]
        score = 0.0
        passed = []
        warnings = []

        # Email (+4 pts)
        if parsed_data.get("email"):
            score += 4.0
            passed.append(f"Valid Email detected: {parsed_data['email']}")
        else:
            warnings.append("Missing email address. Recruiters cannot contact you automatically.")

        # Phone (+3 pts)
        if parsed_data.get("phone"):
            score += 3.0
            passed.append(f"Phone number detected: {parsed_data['phone']}")
        else:
            warnings.append("Missing phone number.")

        # LinkedIn (+2 pts)
        links = parsed_data.get("links", {})
        if links.get("linkedin"):
            score += 2.0
            passed.append("Professional LinkedIn profile URL detected.")
        else:
            warnings.append("No LinkedIn profile detected. Modern ATS parsers look for public profiles.")

        # Technical Portfolio / GitHub (+1 pt)
        if links.get("github") or links.get("portfolio"):
            score += 1.0
            passed.append("GitHub or personal portfolio link detected.")
        else:
            warnings.append("No GitHub or technical portfolio link detected.")

        score = min(max_score, round(score, 1))
        return {
            "category": "Contact Information",
            "score": score,
            "max_score": max_score,
            "weight_pct": max_score,
            "percentage": round((score / max_score) * 100, 1),
            "explanation": "Validates that automated parsing engines can extract contact channels (Email, Phone, LinkedIn, Portfolio).",
            "passed": passed,
            "warnings": warnings
        }

    def score_sections(self, sections: Dict[str, str]) -> Dict[str, Any]:
        """Evaluates section completeness, education, and experience presence (Max 20 pts)."""
        max_score = self.weights["section_completeness"]
        core_sections = {
            "experience": (8.0, "Work Experience / History"),
            "education": (5.0, "Education Details"),
            "skills": (4.0, "Technical Skills"),
            "projects": (2.0, "Projects"),
            "summary": (1.0, "Professional Summary / Objective")
        }

        score = 0.0
        passed = []
        warnings = []

        for sec_key, (weight, label) in core_sections.items():
            if sec_key in sections and len(sections[sec_key].strip()) > 25:
                score += weight
                passed.append(f"Identified standard section: {label}")
            else:
                warnings.append(f"Missing or brief section: {label}")

        score = min(max_score, round(score, 1))
        return {
            "category": "Section Completeness & History",
            "score": score,
            "max_score": max_score,
            "weight_pct": max_score,
            "percentage": round((score / max_score) * 100, 1),
            "explanation": "Checks for essential resume sections (Experience, Education, Skills, Projects, Summary).",
            "passed": passed,
            "warnings": warnings
        }

    def score_action_verbs(self, text: str) -> Dict[str, Any]:
        """Evaluates active power verbs (Max 15 pts)."""
        max_score = self.weights["action_verbs"]
        verb_count, found_verbs = count_action_verbs(text)

        if verb_count >= 12:
            score = max_score
            feedback = f"Outstanding action verb usage ({verb_count} distinct power verbs found)."
        elif verb_count >= 8:
            score = max_score * 0.8
            feedback = f"Good action verb usage ({verb_count} verbs). Aim for 12+ for maximum recruiter appeal."
        elif verb_count >= 4:
            score = max_score * 0.5
            feedback = f"Moderate action verb usage ({verb_count} verbs). Replace passive descriptions with decisive verbs."
        else:
            score = max_score * 0.2
            feedback = f"Very few action verbs ({verb_count} found). Active voice is heavily favored by ATS parsers."

        score = min(max_score, round(score, 1))
        return {
            "category": "Action Verbs & Leadership",
            "score": score,
            "max_score": max_score,
            "weight_pct": max_score,
            "percentage": round((score / max_score) * 100, 1),
            "explanation": "Evaluates usage of impactful power verbs (e.g. Architected, Spearheaded, Automated) instead of passive duties.",
            "distinct_verbs_count": verb_count,
            "sample_verbs": found_verbs[:8],
            "feedback": feedback
        }

    def score_quantified_impact(self, text: str) -> Dict[str, Any]:
        """Evaluates quantifiable metrics, %, $, and user scale (Max 20 pts)."""
        max_score = self.weights["quantified_impact"]
        achievements = extract_quantified_achievements(text)
        count = len(achievements)

        if count >= 6:
            score = max_score
            feedback = f"Exceptional quantifiable results! {count} measurable accomplishments detected."
        elif count >= 3:
            score = max_score * 0.75
            feedback = f"Good quantifiable metrics ({count} found). Adding dollar savings or latency percentages will boost impact."
        elif count >= 1:
            score = max_score * 0.40
            feedback = f"Few metrics found ({count} detected). Back up claims with numbers (e.g. 'Improved efficiency by 30%')."
        else:
            score = 0.0
            feedback = "No measurable metrics detected. Experience bullet points currently lack quantifiable results."

        score = min(max_score, round(score, 1))
        return {
            "category": "Quantified Achievements",
            "score": score,
            "max_score": max_score,
            "weight_pct": max_score,
            "percentage": round((score / max_score) * 100, 1),
            "explanation": "Detects quantifiable numbers, percentages (%), dollar figures ($), and scale indicators in accomplishments.",
            "quantified_count": count,
            "sample_achievements": achievements[:5],
            "feedback": feedback
        }

    def score_skills_density(self, text: str) -> Dict[str, Any]:
        """Evaluates skill keywords volume and breadth (Max 20 pts)."""
        max_score = self.weights["skills_density"]
        skills_info = extract_skills_from_text(text)
        total_skills = skills_info["total_skills_count"]
        cat_count = len(skills_info["category_distribution"])

        if total_skills >= 15 and cat_count >= 3:
            score = max_score
            feedback = f"Strong technical keyword representation ({total_skills} skills across {cat_count} domains)."
        elif total_skills >= 10:
            score = max_score * 0.80
            feedback = f"Solid skill representation ({total_skills} skills). Add complementary frameworks or database tools."
        elif total_skills >= 5:
            score = max_score * 0.50
            feedback = f"Moderate skill coverage ({total_skills} skills). Expand technical competencies for higher keyword ranking."
        else:
            score = max_score * 0.25
            feedback = f"Low skill density ({total_skills} skills detected). Ensure tools and languages are clearly listed."

        score = min(max_score, round(score, 1))
        return {
            "category": "Skills Keyword Density",
            "score": score,
            "max_score": max_score,
            "weight_pct": max_score,
            "percentage": round((score / max_score) * 100, 1),
            "explanation": "Audits relevant technical keywords, tools, and domain skills across multiple taxonomy categories.",
            "total_skills": total_skills,
            "category_count": cat_count,
            "feedback": feedback
        }

    def score_readability(self, text: str, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluates resume word count and document structure (Max 15 pts)."""
        max_score = self.weights["document_readability"]
        word_count = stats.get("word_count", 0)
        score = max_score
        warnings = []
        passed = []

        if OPTIMAL_WORD_COUNT_MIN <= word_count <= OPTIMAL_WORD_COUNT_MAX:
            passed.append(f"Optimal resume length: {word_count} words (Target: {OPTIMAL_WORD_COUNT_MIN}-{OPTIMAL_WORD_COUNT_MAX}).")
        elif word_count < OPTIMAL_WORD_COUNT_MIN:
            score -= 5.0
            warnings.append(f"Resume is relatively brief ({word_count} words). Expand on project accomplishments and responsibilities.")
        else:
            score -= 4.0
            warnings.append(f"Resume is slightly lengthy ({word_count} words). Ensure experience stays concise and relevant.")

        if stats.get("line_count", 0) >= 15:
            passed.append("Healthy line count and vertical density.")
        else:
            warnings.append("Low line density detected.")

        score = max(0.0, min(max_score, round(score, 1)))
        return {
            "category": "Formatting & Readability",
            "score": score,
            "max_score": max_score,
            "weight_pct": max_score,
            "percentage": round((score / max_score) * 100, 1),
            "explanation": "Evaluates word count, structural formatting balance, and human reading flow.",
            "word_count": word_count,
            "passed": passed,
            "warnings": warnings
        }

    def calculate_ats_score(self, parsed_resume: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs the complete ATS compatibility scoring pipeline across all 6 pillars.
        Returns a transparent, fully explainable report.
        """
        clean_txt = parsed_resume.get("clean_text", "")
        sections = parsed_resume.get("sections", {})
        stats = parsed_resume.get("statistics", {})

        # Compute each pillar independently
        contact_res = self.score_contact_info(parsed_resume)
        sec_res = self.score_sections(sections)
        verb_res = self.score_action_verbs(clean_txt)
        quant_res = self.score_quantified_impact(clean_txt)
        skills_res = self.score_skills_density(clean_txt)
        read_res = self.score_readability(clean_txt, stats)

        # Aggregate total score (0 - 100)
        total_score = round(
            contact_res["score"] +
            sec_res["score"] +
            verb_res["score"] +
            quant_res["score"] +
            skills_res["score"] +
            read_res["score"],
            1
        )
        total_score = max(0.0, min(100.0, total_score))
        badge = get_score_badge(total_score)

        # Strengths & Weaknesses
        strengths = []
        weaknesses = []
        critical_fixes = []

        strengths.extend(sec_res["passed"])
        strengths.extend(contact_res["passed"])
        if verb_res["score"] >= 10:
            strengths.append(verb_res["feedback"])
        if quant_res["score"] >= 12:
            strengths.append(quant_res["feedback"])
        strengths.extend(read_res["passed"])

        weaknesses.extend(sec_res["warnings"])
        weaknesses.extend(contact_res["warnings"])
        if quant_res["score"] < 10:
            weaknesses.append(quant_res["feedback"])
        if verb_res["score"] < 10:
            weaknesses.append(verb_res["feedback"])
        weaknesses.extend(read_res["warnings"])

        # High priority critical action fixes
        if quant_res["score"] < 8:
            critical_fixes.append("Add numbers, metrics, or % results to your experience bullet points.")
        if contact_res["score"] < 7:
            critical_fixes.append("Ensure your email and phone number are clearly listed near the top.")
        if sec_res["score"] < 14:
            critical_fixes.append("Include standard section headings (Work Experience, Education, Skills).")
        if skills_res["score"] < 10:
            critical_fixes.append("Add a dedicated 'Technical Skills' section with industry-standard keywords.")

        # Actionable recommendations
        recommendations = [
            "Structure accomplishments using the Google XYZ formula: 'Accomplished [X] as measured by [Y], by doing [Z]'.",
            "Avoid multi-column tables, text boxes, and images that can confuse standard ATS parsers.",
            "Tailor keywords to match each job description to maximize automated screening match rates."
        ]

        return {
            "total_score": total_score,
            "badge": badge,
            "methodology_disclaimer": METHODOLOGY_DISCLAIMER,
            "breakdown": {
                "Contact Information": contact_res,
                "Section Completeness": sec_res,
                "Action Verbs": verb_res,
                "Quantified Impact": quant_res,
                "Skills Keyword Density": skills_res,
                "Readability & Length": read_res
            },
            "strengths": strengths,
            "weaknesses": weaknesses,
            "critical_fixes": critical_fixes,
            "recommendations": recommendations,
            # Backwards compatibility keys
            "passed_checks": strengths,
            "warning_checks": weaknesses,
            "improvement_tips": recommendations
        }


_default_scorer = ATSScorer()

def calculate_ats_score(parsed_resume: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience helper to compute transparent ATS score."""
    return _default_scorer.calculate_ats_score(parsed_resume)
