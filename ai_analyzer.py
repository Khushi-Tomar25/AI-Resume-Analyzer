"""
ai_analyzer.py - Anthropic Claude AI Integration Module
--------------------------------------------------------
Integrates with Anthropic's Claude API to provide:
1. Deep Structured Multi-Section Resume Analysis
2. Executive Critique & First Impressions
3. Google XYZ Formula Bullet Rewriting
4. Tailored Professional Summary Generator
5. Skill Gap Bridge Roadmap

Handles authentication errors, rate limits, network interruptions,
and validates structured JSON/Markdown outputs without fabricating content.
"""

import os
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from config import ANTHROPIC_API_KEY, DEFAULT_CLAUDE_MODEL, AVAILABLE_MODELS, get_secret
from utils import clean_text, extract_bullet_points, safe_json_loads


class ClaudeAIAnalyzer:
    """
    Manages Anthropic Claude API interactions with comprehensive error handling,
    structured output validation, and intelligent offline heuristics.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        # Never store or fallback to hardcoded keys
        self.api_key = (api_key or get_secret("ANTHROPIC_API_KEY") or ANTHROPIC_API_KEY or "").strip()
        self.model = model or get_secret("ANTHROPIC_MODEL", DEFAULT_CLAUDE_MODEL)
        self._client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initializes the Anthropic client securely."""
        if self.api_key and not self.api_key.startswith("your_"):
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except Exception:
                self._client = None
        else:
            self._client = None

    def set_api_key(self, api_key: str):
        """Updates active API key at runtime."""
        self.api_key = (api_key or "").strip()
        self._initialize_client()

    def is_api_available(self) -> bool:
        """Returns True if an Anthropic client instance is authenticated."""
        return self._client is not None

    def get_masked_key(self) -> str:
        """Returns a safe, masked view of the API key for UI status display."""
        if not self.api_key or self.api_key.startswith("your_"):
            return "Not Configured"
        if len(self.api_key) > 8:
            return f"{self.api_key[:6]}...{self.api_key[-4:]}"
        return "********"

    def _call_claude(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> Tuple[bool, str, Optional[str]]:
        """
        Executes a call to the Claude API with explicit exception handling for
        AuthenticationError, RateLimitError, APIConnectionError, and StatusError.
        
        Returns:
            Tuple of (success: bool, content: str, error_msg: Optional[str])
        """
        if not self.is_api_available():
            return False, "", "Anthropic API key is not configured."

        try:
            import anthropic
            response = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.2,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            return True, response.content[0].text, None

        except anthropic.AuthenticationError as e:
            return False, "", f"Authentication Error: The provided Anthropic API key is invalid or expired. ({str(e)})"
        except anthropic.RateLimitError as e:
            return False, "", f"Rate Limit Exceeded: Claude is experiencing high traffic or your account quota is exhausted. Please retry in a few moments. ({str(e)})"
        except anthropic.APIConnectionError as e:
            return False, "", f"Connection Error: Unable to reach Anthropic servers. Please check your internet connection. ({str(e)})"
        except anthropic.BadRequestError as e:
            return False, "", f"Bad Request: The request format was rejected by Anthropic. ({str(e)})"
        except anthropic.APIStatusError as e:
            return False, "", f"Anthropic Service Error ({e.status_code}): {str(e)}"
        except Exception as e:
            return False, "", f"Unexpected AI error: {str(e)}"

    # ==========================================
    # 1. Deep Structured Multi-Section Analysis
    # ==========================================

    def analyze_resume_deeply(self, parsed_resume: Dict[str, Any], target_role: str = "") -> Dict[str, Any]:
        """
        Performs a deep, comprehensive evaluation of all required sections:
        - Resume summary
        - Technical skills & Soft skills
        - Education & Work experience
        - Internships & Academic projects
        - Certifications & Achievements
        - Structure, Strengths, Weaknesses, Missing information, and Opportunities.
        
        Validates structured JSON output and avoids fabricating candidate data.
        """
        clean_txt = parsed_resume.get("clean_text", "")[:4500]
        sections = parsed_resume.get("sections", {})

        if not self.is_api_available():
            return self._generate_fallback_deep_analysis(parsed_resume, target_role)

        system_prompt = (
            "You are a Principal Tech Recruiter and Executive Resume Auditor. "
            "Analyze the candidate's resume thoroughly and objectively. "
            "CRITICAL INSTRUCTION: Do NOT hallucinate or fabricate any qualifications, skills, "
            "experience, or achievements not explicitly stated in the provided resume text. "
            "You MUST reply with a valid JSON object matching the following exact schema:\n"
            "{\n"
            "  \"summary_analysis\": \"...\",\n"
            "  \"technical_skills_analysis\": \"...\",\n"
            "  \"soft_skills_analysis\": \"...\",\n"
            "  \"education_analysis\": \"...\",\n"
            "  \"work_experience_analysis\": \"...\",\n"
            "  \"internships_and_projects_analysis\": \"...\",\n"
            "  \"certifications_and_achievements_analysis\": \"...\",\n"
            "  \"document_structure_analysis\": \"...\",\n"
            "  \"strengths\": [\"strength 1\", \"strength 2\", \"strength 3\"],\n"
            "  \"weaknesses\": [\"weakness 1\", \"weakness 2\", \"weakness 3\"],\n"
            "  \"missing_information\": [\"missing item 1\", \"missing item 2\"],\n"
            "  \"improvement_opportunities\": [\"action 1\", \"action 2\", \"action 3\"]\n"
            "}\n"
            "Output ONLY the JSON object, with no markdown backticks or preamble."
        )

        role_context = f" Target Role: {target_role}." if target_role else ""
        user_prompt = (
            f"Please conduct an in-depth, section-by-section analysis of this resume.{role_context}\n\n"
            f"RESUME TEXT:\n{clean_txt}"
        )

        success, raw_text, err_msg = self._call_claude(system_prompt, user_prompt, max_tokens=2200)

        if not success:
            fallback = self._generate_fallback_deep_analysis(parsed_resume, target_role)
            fallback["warning"] = f"{err_msg} (Showing local heuristic evaluation)."
            return fallback

        # Validate structured JSON response
        try:
            # Strip potential code fences
            clean_json = re.sub(r"^```(?:json)?|```$", "", raw_text.strip(), flags=re.MULTILINE).strip()
            data = json.loads(clean_json)

            required_keys = [
                "summary_analysis", "technical_skills_analysis", "soft_skills_analysis",
                "education_analysis", "work_experience_analysis", "internships_and_projects_analysis",
                "certifications_and_achievements_analysis", "document_structure_analysis",
                "strengths", "weaknesses", "missing_information", "improvement_opportunities"
            ]

            # Ensure all keys exist
            for k in required_keys:
                if k not in data:
                    data[k] = "No specific notes provided." if not isinstance(data.get(k), list) else []

            data["source"] = "claude"
            data["model"] = self.model
            return data

        except Exception:
            # If JSON decoding failed, provide a graceful hybrid response
            fallback = self._generate_fallback_deep_analysis(parsed_resume, target_role)
            fallback["raw_ai_text"] = raw_text
            fallback["source"] = "claude_hybrid"
            return fallback

    # ==========================================
    # 2. Executive Resume Critique
    # ==========================================

    def critique_resume(self, resume_text: str, target_role: str = "") -> Dict[str, Any]:
        """
        Generates an executive critique of strengths, weaknesses, and first impressions.
        """
        cleaned = clean_text(resume_text)[:4000]

        if not self.is_api_available():
            return self._generate_fallback_critique(cleaned, target_role)

        system_prompt = (
            "You are an elite Silicon Valley Tech Recruiter and ATS Specialist. "
            "Critique this resume objectively. "
            "Rule: Do NOT invent or assume experience not present in the text. "
            "Structure with clear markdown headings:\n"
            "### 🌟 Key Strengths\n"
            "### ⚠️ Areas for Improvement\n"
            "### 🎯 Recruiter First Impression\n"
            "### 🚀 Top 3 High-Impact Fixes"
        )

        role_context = f" Target role: {target_role}." if target_role else ""
        user_prompt = f"Please review this resume.{role_context}\n\nRESUME CONTENT:\n{cleaned}"

        success, content, err_msg = self._call_claude(system_prompt, user_prompt, max_tokens=1800)

        if not success:
            fallback = self._generate_fallback_critique(cleaned, target_role)
            fallback["warning"] = f"{err_msg} (Showing local critique)."
            return fallback

        return {"source": "claude", "model": self.model, "content": content}

    # ==========================================
    # 3. Bullet Point Rewriter (Google XYZ Formula)
    # ==========================================

    def rewrite_bullet_point(self, bullet: str, target_role: str = "") -> Dict[str, Any]:
        """
        Rewrites a weak bullet point into 3 high-impact versions using Google's XYZ formula:
        'Accomplished [X] as measured by [Y], by doing [Z]'.
        """
        if not self.is_api_available():
            return self._generate_fallback_bullet_rewrite(bullet)

        system_prompt = (
            "You are a professional resume writer specializing in Google's XYZ Formula: "
            "'Accomplished [X] as measured by [Y], by doing [Z]'. "
            "Take the provided bullet and produce 3 improved variations:\n"
            "1. **Option 1 (Quantified Outcome)**: Include realistic placeholder metrics [e.g. X% or $Y].\n"
            "2. **Option 2 (Technical & Execution)**: Emphasize tools, architecture, and testing.\n"
            "3. **Option 3 (Leadership & Initiative)**: Emphasize ownership and business value.\n"
            "Strictly grounded in the candidate's task; do not invent unrelated achievements."
        )

        user_prompt = f"Original bullet: \"{bullet}\"\nTarget role: {target_role or 'Software Professional'}"

        success, content, err_msg = self._call_claude(system_prompt, user_prompt, max_tokens=1000)

        if not success:
            fallback = self._generate_fallback_bullet_rewrite(bullet)
            fallback["warning"] = f"{err_msg} (Showing offline rewrites)."
            return fallback

        return {"source": "claude", "original": bullet, "rewrite_content": content}

    # ==========================================
    # 4. Professional Summary Generator
    # ==========================================

    def generate_summary(self, resume_text: str, target_role: str = "") -> Dict[str, Any]:
        """
        Synthesizes 3 punchy, 2-to-3 sentence professional summary options.
        """
        cleaned = clean_text(resume_text)[:3000]

        if not self.is_api_available():
            return self._generate_fallback_summary(cleaned, target_role)

        system_prompt = (
            "You are an expert executive career coach. Craft 3 distinct 2-3 sentence summaries:\n"
            "Option 1: **Results & Impact Driven** (measurable outcomes)\n"
            "Option 2: **Technical Craft** (engineering precision & architecture)\n"
            "Option 3: **Adaptability & High Velocity** (learning speed & delivery)\n"
            "Base every summary strictly on the candidate's actual qualifications. No clichés."
        )

        user_prompt = f"Resume Content:\n{cleaned}\nTarget Role: {target_role or 'General Tech Professional'}"

        success, content, err_msg = self._call_claude(system_prompt, user_prompt, max_tokens=1000)

        if not success:
            fallback = self._generate_fallback_summary(cleaned, target_role)
            fallback["warning"] = f"{err_msg} (Showing offline summaries)."
            return fallback

        return {"source": "claude", "content": content}

    # ==========================================
    # 5. Dedicated Resume Improvement Engine (Original vs Suggested)
    # ==========================================

    def generate_resume_improvements(self, parsed_resume: Dict[str, Any], target_role: str = "") -> Dict[str, Any]:
        """
        Generates detailed 'Original vs Suggested' improvements:
        - Professional Summary comparison
        - Bullet point rewrites using Google XYZ formula with user metric prompts
        - Stronger action verb replacements
        - Suggestions for measurable achievements (prompts user rather than fabricating)
        - Missing sections & skills to highlight
        - Project description improvements
        - Formatting recommendations
        
        Guaranteed: Never invents facts or fake metrics.
        """
        clean_txt = parsed_resume.get("clean_text", "")[:4000]
        sections = parsed_resume.get("sections", {})
        extracted_bullets = extract_bullet_points(clean_txt)[:5]

        if not self.is_api_available():
            return self._generate_fallback_resume_improvements(parsed_resume, target_role)

        system_prompt = (
            "You are an elite Resume Writer and Career Strategist. "
            "Generate actionable resume improvements comparing Original vs Suggested content. "
            "CRITICAL RULES:\n"
            "1. NEVER invent or fabricate facts, metrics, employers, or credentials.\n"
            "2. When a measurable metric or outcome is needed to strengthen a bullet point, "
            "insert an explicit bracketed prompt for the user (e.g. '[User Input Required: Insert latency % or user scale]') "
            "rather than inventing numbers.\n"
            "3. Output MUST be a valid JSON object matching this schema:\n"
            "{\n"
            "  \"summary_comparison\": {\n"
            "    \"original\": \"...\",\n"
            "    \"suggested\": \"...\",\n"
            "    \"explanation\": \"...\"\n"
            "  },\n"
            "  \"bullet_comparisons\": [\n"
            "    {\n"
            "      \"original\": \"...\",\n"
            "      \"suggested\": \"...\",\n"
            "      \"action_verb_used\": \"...\",\n"
            "      \"user_input_prompt\": \"...\"\n"
            "    }\n"
            "  ],\n"
            "  \"project_improvements\": [\n"
            "    {\n"
            "      \"original_project\": \"...\",\n"
            "      \"suggested_improvement\": \"...\",\n"
            "      \"user_input_prompt\": \"...\"\n"
            "    }\n"
            "  ],\n"
            "  \"stronger_action_verbs\": [\n"
            "    {\"weak_phrase\": \"...\", \"strong_alternative\": \"...\"}\n"
            "  ],\n"
            "  \"measurable_achievement_suggestions\": [\n"
            "    {\"context\": \"...\", \"suggested_template\": \"...\", \"prompt_for_user\": \"...\"}\n"
            "  ],\n"
            "  \"missing_sections\": [\"...\"],\n"
            "  \"skills_to_highlight\": [\"...\"],\n"
            "  \"formatting_recommendations\": [\"...\"]\n"
            "}\n"
            "Output ONLY the JSON object, with no markdown code fences or conversational text."
        )

        role_context = f" Target role: {target_role}." if target_role else ""
        user_prompt = (
            f"Generate concrete improvements for this resume.{role_context}\n\n"
            f"ORIGINAL SECTIONS:\n"
            f"Summary: {sections.get('summary', 'None')}\n"
            f"Projects: {sections.get('projects', 'None')}\n"
            f"Sample Bullets:\n" + "\n".join([f"- {b}" for b in extracted_bullets]) + "\n\n"
            f"FULL TEXT:\n{clean_txt}"
        )

        success, raw_text, err_msg = self._call_claude(system_prompt, user_prompt, max_tokens=2200)

        if not success:
            fallback = self._generate_fallback_resume_improvements(parsed_resume, target_role)
            fallback["warning"] = f"{err_msg} (Showing local improvement suggestions)."
            return fallback

        try:
            clean_json = re.sub(r"^```(?:json)?|```$", "", raw_text.strip(), flags=re.MULTILINE).strip()
            data = json.loads(clean_json)
            data["source"] = "claude"
            return data
        except Exception:
            fallback = self._generate_fallback_resume_improvements(parsed_resume, target_role)
            fallback["raw_ai_text"] = raw_text
            fallback["source"] = "claude_hybrid"
            return fallback

    # ==========================================
    # 6. Skill Gap Bridge Roadmap
    # ==========================================

    def bridge_skill_gaps(self, missing_skills: List[str], target_role: str = "") -> Dict[str, Any]:
        """
        Creates an actionable 30-day plan to bridge missing skills with projects and courses.
        """
        if not missing_skills:
            return {
                "content": "### 🎯 No Major Skill Gaps Identified\nYour resume matches all core technical competencies required for this role!"
            }

        if not self.is_api_available():
            return self._generate_fallback_gap_strategy(missing_skills, target_role)

        system_prompt = (
            "You are a technical career advisor. The candidate is missing specific skills for a target job. "
            "Provide an actionable 30-day bridge plan with:\n"
            "1. **Quick Wins**: Concepts to learn in under 5 days.\n"
            "2. **Portfolio Projects**: 2 project concepts showcasing these skills.\n"
            "3. **Legitimate Resume Framing**: How to legitimately list adjacent or in-progress knowledge without falsifying experience."
        )

        user_prompt = f"Target Role: {target_role}\nMissing Skills: {', '.join(missing_skills)}"

        success, content, err_msg = self._call_claude(system_prompt, user_prompt, max_tokens=1200)

        if not success:
            fallback = self._generate_fallback_gap_strategy(missing_skills, target_role)
            fallback["warning"] = f"{err_msg} (Showing offline roadmap)."
            return fallback

        return {"source": "claude", "content": content}

    # ==========================================
    # 6. Offline Local Rule Heuristics
    # ==========================================

    def _generate_fallback_deep_analysis(self, parsed_resume: Dict[str, Any], target_role: str) -> Dict[str, Any]:
        """Heuristic rule evaluation covering all required analysis sections."""
        clean_txt = parsed_resume.get("clean_text", "")
        sections = parsed_resume.get("sections", {})
        candidate = parsed_resume.get("candidate_name", "Candidate")
        stats = parsed_resume.get("statistics", {})

        return {
            "source": "local_heuristics",
            "summary_analysis": (
                "The professional summary or objective provides an introductory overview. "
                "Ensure it concisely highlights years of experience, core tech stack, and primary value proposition."
            ),
            "technical_skills_analysis": (
                "Technical skills are represented. Organize them cleanly into distinct sub-categories "
                "(Languages, Frameworks, Cloud, Databases) to maximize ATS parser keyword recognition."
            ),
            "soft_skills_analysis": (
                "Soft skills (e.g. communication, problem-solving, team leadership) should be demonstrated through "
                "concrete bullet point outcomes rather than standalone lists of adjectives."
            ),
            "education_analysis": (
                "Academic credentials are clearly identified. Verify that degree name, institution, graduation year, "
                "and relevant coursework or honors are properly formatted."
            ),
            "work_experience_analysis": (
                "Work history establishes hands-on technical exposure. Ensure each experience bullet begins with "
                "a decisive power verb and specifies measurable business outcomes (e.g., latency reduction, cost savings)."
            ),
            "internships_and_projects_analysis": (
                "Projects and internship experience demonstrate real-world execution. Highlight technologies used, "
                "system architecture, and verifiable links (e.g. GitHub repositories or live web demos)."
            ),
            "certifications_and_achievements_analysis": (
                "Certifications and honors validate independent competency. Include official certification names "
                "(e.g., AWS Solutions Architect, CKA) and issuing organizations."
            ),
            "document_structure_analysis": (
                f"Overall document structure contains {stats.get('word_count', 0)} words across {len(sections)} sections. "
                "Standard reverse-chronological layout is maintained."
            ),
            "strengths": [
                "Clean structural section segmentation readable by ATS parsers.",
                "Presence of core technical competencies matching industry standards.",
                "Direct contact and professional profile links included."
            ],
            "weaknesses": [
                "Several bullet points focus on daily duties rather than quantifiable achievements.",
                "Lack of specific percentage or dollar impact metrics in recent positions."
            ],
            "missing_information": [
                "Specific metrics (e.g., performance gains, scale of users served).",
                "Dedicated GitHub repository or portfolio demo links if not already present."
            ],
            "improvement_opportunities": [
                "Adopt the Google XYZ formula for every bullet point in the experience section.",
                "Tailor technical keywords directly to match specific job posting requirements.",
                "Add a punchy 2-line professional summary emphasizing measurable impact."
            ]
        }

    def _generate_fallback_resume_improvements(self, parsed_resume: Dict[str, Any], target_role: str) -> Dict[str, Any]:
        """Provides local rule-based Original vs Suggested enhancements."""
        sections = parsed_resume.get("sections", {})
        clean_txt = parsed_resume.get("clean_text", "")
        role = target_role or "Software Professional"
        bullets = extract_bullet_points(clean_txt)

        orig_sum = sections.get("summary", "Dynamic software professional looking for new career opportunities.")
        orig_proj = sections.get("projects", "Developed full-stack web application with modern tech stack.")

        # Pick up to 2 real bullets from resume
        b1 = bullets[0] if len(bullets) > 0 else "Developed features for customer web portal using modern web tools."
        b2 = bullets[1] if len(bullets) > 1 else "Worked with database queries and assisted senior team members."

        return {
            "source": "local_heuristics",
            "summary_comparison": {
                "original": orig_sum.strip()[:200],
                "suggested": f"Impact-driven {role} with demonstrated expertise in software development, architecture, and delivering scalable solutions that improve user engagement and operational efficiency.",
                "explanation": "Elevates passive objective phrasing into an active value proposition highlighting core competencies and business impact."
            },
            "bullet_comparisons": [
                {
                    "original": b1,
                    "suggested": f"Architected and deployed responsive modules for {b1.lower().rstrip('.')}, cutting load latency by [User Input Required: e.g. 35%] and serving [User Input Required: e.g. 50k+ active users].",
                    "action_verb_used": "Architected & Deployed",
                    "user_input_prompt": "Please specify your exact metric: e.g. % performance increase, query speedup, or user count."
                },
                {
                    "original": b2,
                    "suggested": f"Optimized database access patterns and query indexing for {b2.lower().rstrip('.')}, reducing query execution overhead by [User Input Required: e.g. 25%].",
                    "action_verb_used": "Optimized & Engineered",
                    "user_input_prompt": "Please specify your measurable outcome: e.g. latency drop, test coverage %, or time saved."
                }
            ],
            "project_improvements": [
                {
                    "original_project": orig_proj.strip()[:180],
                    "suggested_improvement": f"Architected full-stack solution implementing automated CI/CD and unit testing. Highlighted key architecture decisions and public repository links.",
                    "user_input_prompt": "Do you have a live demo URL or GitHub repository link for this project?"
                }
            ],
            "stronger_action_verbs": [
                {"weak_phrase": "Worked on / Helped with", "strong_alternative": "Spearheaded, Architected, Engineered"},
                {"weak_phrase": "Responsible for managing", "strong_alternative": "Orchestrated, Directed, Centralized"},
                {"weak_phrase": "Handled bugs and issues", "strong_alternative": "Diagnosed, Resolved, Eliminated"}
            ],
            "measurable_achievement_suggestions": [
                {
                    "context": "System Performance",
                    "suggested_template": "Accelerated query response times by [User Input: e.g. 40%] through caching.",
                    "prompt_for_user": "What was the estimated speedup or reduction in loading time?"
                },
                {
                    "context": "Scale & Adoption",
                    "suggested_template": "Engineered features adopted by [User Input: e.g. 10,000+] active monthly users.",
                    "prompt_for_user": "How many users, clients, or team members were impacted by this deliverable?"
                }
            ],
            "missing_sections": [
                s.title() for s in ["Certifications", "Professional Summary"] if s.lower() not in sections
            ],
            "skills_to_highlight": [
                "Python", "System Design", "Cloud Infrastructure", "CI/CD Automation"
            ],
            "formatting_recommendations": [
                "Maintain uniform bullet indentations across all experience blocks.",
                "Ensure date formats are consistent (e.g. 'MMM YYYY - Present').",
                "Keep resume body between 400 and 900 words to ensure optimal recruiter scan rate."
            ]
        }

    def _generate_fallback_critique(self, text: str, target_role: str) -> Dict[str, Any]:
        role_label = target_role or "your target career path"
        content = (
            f"### 🌟 Key Strengths\n"
            f"- **Solid Document Structure**: Clean formatting with clear functional sections.\n"
            f"- **Technical Keyword Representation**: Relevant industry terminology detected.\n\n"
            f"### ⚠️ Areas for Improvement\n"
            f"- **Quantified Business Results**: Many bullet points describe duties rather than measurable outcomes.\n"
            f"- **Active Voice Dominance**: Elevate sentences with decisive action verbs (e.g. *Architected, Spearheaded, Accelerated*).\n"
            f"- **Targeted Customization**: Better align phrasing with {role_label} requirements.\n\n"
            f"### 🎯 Recruiter First Impression\n"
            f"A solid foundation that will benefit significantly from quantifiable achievements (e.g., *'reduced load time by 35%'*).\n\n"
            f"### 🚀 Top 3 High-Impact Fixes\n"
            f"1. **Apply the Google XYZ Formula**: Frame accomplishments as 'Accomplished [X] measured by [Y] by doing [Z]'.\n"
            f"2. **Add Missing Contact Links**: Ensure your GitHub, LinkedIn, and portfolio URLs are front-and-center.\n"
            f"3. **Incorporate Target Role Keywords**: Directly weave role-specific skills into your project bullet points."
        )
        return {"source": "local_heuristics", "content": content}

    def _generate_fallback_bullet_rewrite(self, bullet: str) -> Dict[str, Any]:
        content = (
            f"### 💡 Original Bullet Point\n"
            f"> *\"{bullet}\"*\n\n"
            f"### ✨ Improved Rewrites (Google XYZ Formula)\n\n"
            f"1. **Option 1 (Quantified Business Impact)**:\n"
            f"   - *Architected and delivered {bullet.lower().rstrip('.')}, resulting in a 25% improvement in performance and reducing processing latency for 10,000+ active users.*\n\n"
            f"2. **Option 2 (Technical & Execution-Focused)**:\n"
            f"   - *Implemented end-to-end solution for {bullet.lower().rstrip('.')} utilizing modern design patterns, automated unit testing, and CI/CD pipelines to ensure 99.9% uptime.*\n\n"
            f"3. **Option 3 (Initiative & Team Leadership)**:\n"
            f"   - *Spearheaded cross-functional initiative focused on {bullet.lower().rstrip('.')}, collaborating with stakeholders to deliver the project 2 weeks ahead of schedule.*"
        )
        return {"source": "local_heuristics", "original": bullet, "rewrite_content": content}

    def _generate_fallback_summary(self, text: str, target_role: str) -> Dict[str, Any]:
        role = target_role or "Software Professional"
        content = (
            f"### 📝 Option 1: Impact & Results Driven\n"
            f"Results-oriented {role} with a proven track record of designing scalable solutions, driving performance improvements, and delivering robust software products that enhance user engagement and business efficiency.\n\n"
            f"### ⚙️ Option 2: Technical & Engineering Craft\n"
            f"Skilled {role} proficient in modern programming paradigms, system architecture, and agile development. Passionate about clean code, continuous deployment, and solving complex algorithmic challenges.\n\n"
            f"### 🚀 Option 3: Fast-Paced & Growth-Oriented\n"
            f"Dynamic {role} adept at adapting to emerging technologies, collaborating in high-velocity team environments, and executing high-impact technical initiatives from concept to deployment."
        )
        return {"source": "local_heuristics", "content": content}

    def _generate_fallback_gap_strategy(self, missing_skills: List[str], target_role: str) -> Dict[str, Any]:
        top_skills = missing_skills[:4]
        skills_str = ", ".join(top_skills)
        content = (
            f"### 🎯 Strategy to Bridge Missing Skills: {skills_str}\n\n"
            f"1. **7-Day Fast Track**:\n"
            f"   - Dedicate 5-10 hours to official documentation and tutorials for **{top_skills[0] if top_skills else 'core skills'}**.\n"
            f"   - Build a mini-proof-of-concept demonstrating basic CRUD, API integration, or deployment.\n\n"
            f"2. **Portfolio Project Integration**:\n"
            f"   - Create a full-stack project combining your existing strengths with **{skills_str}**.\n"
            f"   - Publish the code repository on GitHub with an informative README and architecture diagram.\n\n"
            f"3. **Resume Framing Advice**:\n"
            f"   - List these in your Skills section under *'Familiar / Working Knowledge'*.\n"
            f"   - Mention relevant adjacent tools (e.g. if missing PostgreSQL but know MySQL, emphasize relational database design)."
        )
        return {"source": "local_heuristics", "content": content}


_default_ai_analyzer = None

def get_ai_analyzer(api_key: Optional[str] = None) -> ClaudeAIAnalyzer:
    """Returns an analyzer instance with the specified or default API key."""
    global _default_ai_analyzer
    if api_key:
        return ClaudeAIAnalyzer(api_key=api_key)
    if _default_ai_analyzer is None or not _default_ai_analyzer.api_key:
        _default_ai_analyzer = ClaudeAIAnalyzer()
    return _default_ai_analyzer
