"""
report_generator.py - Professional PDF Report Generation Engine
----------------------------------------------------------------
Generates downloadable, executive-grade PDF evaluation reports using ReportLab.
Includes:
- Branded header banner & project identity
- Candidate resume overview metadata
- ATS Compatibility scorecard & 6-pillar breakdown
- Job match percentage & skill alignment (when applicable)
- Skills analysis & categorized taxonomy matrix
- Missing skills highlights
- Strengths & Weaknesses
- AI Career Recommendations & Actionable Checklist
- Dynamic 'Page X of Y' page numbering on all pages via NumberedCanvas
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether
)
from reportlab.pdfgen import canvas

from config import REPORTS_DIR


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas that computes total page count dynamically
    and prints 'Page X of Y' on every page along with confidential footer.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8.5)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Bottom divider rule
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.75)
        self.line(36, 34, 612 - 36, 34)

        # Footer Left & Right labels
        self.drawString(36, 22, "ResumeAI • AI-Powered Resume Analyzer & ATS Optimizer")
        self.drawRightString(612 - 36, 22, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


class ReportGenerator:
    """
    Builds structured, executive-grade PDF audit reports for resume analyses.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or REPORTS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_pdf_report(
        self,
        parsed_resume: Dict[str, Any],
        ats_results: Dict[str, Any],
        job_match_results: Optional[Dict[str, Any]] = None,
        ai_critique: Optional[str] = None,
        target_role: Optional[str] = None
    ) -> str:
        """
        Builds a comprehensive PDF report and returns the absolute file path.
        """
        candidate_name = parsed_resume.get("candidate_name", "Candidate")
        safe_name = "".join(c for c in candidate_name if c.isalnum() or c in (" ", "_")).strip().replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Resume_Analysis_{safe_name}_{timestamp}.pdf"
        filepath = self.output_dir / filename

        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=45
        )

        styles = getSampleStyleSheet()
        
        # Professional Typography
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0F172A")
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#64748B")
        )
        h2_style = ParagraphStyle(
            "Heading2Custom",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=10,
            spaceAfter=5
        )
        body_style = ParagraphStyle(
            "BodyCustom",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor("#334155")
        )
        bold_body = ParagraphStyle(
            "BoldBody",
            parent=body_style,
            fontName="Helvetica-Bold"
        )

        elements = []

        # ==========================================
        # 1. Header Banner & Project Identity
        # ==========================================
        elements.append(Paragraph("ResumeAI &bull; AI-Powered Resume Analyzer", title_style))
        elements.append(Spacer(1, 3))
        
        target_str = f" | Target Role: <b>{target_role}</b>" if target_role else ""
        meta_line = f"Candidate: <b>{candidate_name}</b> | Filename: <b>{parsed_resume.get('file_name', 'resume.pdf')}</b> | Generated: {datetime.now().strftime('%B %d, %Y')}{target_str}"
        elements.append(Paragraph(meta_line, subtitle_style))
        elements.append(Spacer(1, 8))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563EB"), spaceAfter=12))

        # ==========================================
        # 2. Executive Scorecard & Resume Overview
        # ==========================================
        total_ats = ats_results.get("total_score", 0)
        badge = ats_results.get("badge", {})
        badge_label = badge.get("label", "Evaluated")
        badge_hex = badge.get("color", "#3B82F6")

        stats = parsed_resume.get("statistics", {})
        word_count = stats.get("word_count", 0)
        read_time = stats.get("reading_time_minutes", 0)

        match_score_str = "Awaiting JD"
        if job_match_results and "overall_match_score" in job_match_results:
            match_score_str = f"{job_match_results['overall_match_score']}%"

        scorecard_data = [
            [
                Paragraph("<b>ATS Compatibility Score</b>", subtitle_style),
                Paragraph("<b>Rating Tier</b>", subtitle_style),
                Paragraph("<b>Job Match Compatibility</b>", subtitle_style),
                Paragraph("<b>Resume Length Overview</b>", subtitle_style)
            ],
            [
                Paragraph(f"<font size='16' color='#0F172A'><b>{total_ats} / 100</b></font>", body_style),
                Paragraph(f"<font size='13' color='{badge_hex}'><b>{badge_label}</b></font>", body_style),
                Paragraph(f"<font size='15' color='#2563EB'><b>{match_score_str}</b></font>", body_style),
                Paragraph(f"<font size='13' color='#0F172A'><b>{word_count} words</b> (~{read_time} min read)</font>", body_style)
            ]
        ]
        
        score_table = Table(scorecard_data, colWidths=[135, 125, 135, 145])
        score_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ]))
        elements.append(score_table)
        elements.append(Spacer(1, 12))

        # ==========================================
        # 3. ATS Scoring Categories Breakdown
        # ==========================================
        elements.append(Paragraph("ATS Scoring Categories Breakdown", h2_style))
        breakdown = ats_results.get("breakdown", {})

        table_rows = [
            [
                Paragraph("<b>Scoring Category</b>", bold_body),
                Paragraph("<b>Score</b>", bold_body),
                Paragraph("<b>Max</b>", bold_body),
                Paragraph("<b>Pct</b>", bold_body),
                Paragraph("<b>Status & Highlights</b>", bold_body)
            ]
        ]

        for pillar_name, data in breakdown.items():
            sc = data.get("score", 0)
            mx = data.get("max_score", 0)
            pct = data.get("percentage", 0)
            cat_title = data.get("category", pillar_name)
            feedback = data.get("feedback", "")
            if not feedback and data.get("passed"):
                feedback = "; ".join(data.get("passed", [])[:2])
            elif not feedback and data.get("warnings"):
                feedback = "; ".join(data.get("warnings", [])[:2])

            color_tag = "#10B981" if pct >= 75 else ("#F59E0B" if pct >= 50 else "#EF4444")
            table_rows.append([
                Paragraph(cat_title, body_style),
                Paragraph(f"<b>{sc}</b>", body_style),
                Paragraph(str(mx), body_style),
                Paragraph(f"<font color='{color_tag}'><b>{pct}%</b></font>", body_style),
                Paragraph(feedback[:140] + ("..." if len(feedback) > 140 else ""), body_style)
            ])

        pillar_table = Table(table_rows, colWidths=[150, 45, 40, 55, 250])
        pillar_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(pillar_table)
        elements.append(Spacer(1, 12))

        # ==========================================
        # 4. Resume Strengths & Weaknesses
        # ==========================================
        strengths = ats_results.get("strengths", [])
        weaknesses = ats_results.get("weaknesses", [])
        critical_fixes = ats_results.get("critical_fixes", [])

        if strengths:
            elements.append(Paragraph("Verified Resume Strengths", h2_style))
            for s in strengths[:4]:
                elements.append(Paragraph(f"<font color='#10B981'>[✔]</font> {s}", body_style))
                elements.append(Spacer(1, 2))
            elements.append(Spacer(1, 6))

        if weaknesses or critical_fixes:
            elements.append(Paragraph("Identified Areas for Improvement & Weaknesses", h2_style))
            for fix in critical_fixes:
                elements.append(Paragraph(f"<font color='#EF4444'>[🚨 Action]</font> <b>{fix}</b>", body_style))
                elements.append(Spacer(1, 2))
            for w in weaknesses[:4]:
                elements.append(Paragraph(f"<font color='#F59E0B'>[⚡]</font> {w}", body_style))
                elements.append(Spacer(1, 2))
            elements.append(Spacer(1, 8))

        # ==========================================
        # 5. Job Match Analysis & Missing Skills
        # ==========================================
        if job_match_results and "overall_match_score" in job_match_results:
            elements.append(Paragraph("Job Description Matching & Skill Gaps", h2_style))
            matched_skills = job_match_results.get("matched_skills", [])
            missing_skills = job_match_results.get("missing_skills", [])
            partial_skills = job_match_results.get("partial_matching_skills", [])

            match_text = f"<b>Matching Skills ({len(matched_skills)}):</b> " + (", ".join(matched_skills) if matched_skills else "None")
            elements.append(Paragraph(match_text, body_style))
            elements.append(Spacer(1, 3))

            if partial_skills:
                p_text = f"<b>Adjacent / Partial Matches ({len(partial_skills)}):</b> " + ", ".join([f"{p['candidate_has']} (for {p['requested']})" for p in partial_skills])
                elements.append(Paragraph(p_text, body_style))
                elements.append(Spacer(1, 3))

            miss_text = f"<font color='#DC2626'><b>Missing Skills ({len(missing_skills)}):</b></font> " + (", ".join(missing_skills) if missing_skills else "None identified")
            elements.append(Paragraph(miss_text, body_style))
            elements.append(Spacer(1, 10))

        # ==========================================
        # 6. AI Recommendations & Next Steps
        # ==========================================
        elements.append(Paragraph("AI Recommendations & Career Strategy", h2_style))
        if ai_critique:
            for line in ai_critique.split("\n"):
                l = line.strip()
                if not l:
                    continue
                if l.startswith("#"):
                    clean_h = l.replace("#", "").strip()
                    elements.append(Paragraph(f"<b>{clean_h}</b>", bold_body))
                    elements.append(Spacer(1, 2))
                elif l.startswith("-") or l.startswith("*"):
                    clean_b = l.lstrip("-* ").strip()
                    elements.append(Paragraph(f"&bull; {clean_b}", body_style))
                    elements.append(Spacer(1, 2))
                else:
                    elements.append(Paragraph(l, body_style))
                    elements.append(Spacer(1, 2))
        else:
            default_tips = [
                "Structure accomplishments using the Google XYZ formula: 'Accomplished [X] as measured by [Y], by doing [Z]'.",
                "Ensure technical keywords from your target job posting appear naturally in project descriptions.",
                "Back up claims with quantitative numbers: team size, percentage speedups, or dollar budgets."
            ]
            for tip in default_tips:
                elements.append(Paragraph(f"&bull; {tip}", body_style))
                elements.append(Spacer(1, 2))

        # Build document with dynamic NumberedCanvas page numbering
        doc.build(elements, canvasmaker=NumberedCanvas)
        return str(filepath)


_default_report_generator = ReportGenerator()

def generate_pdf_report(
    parsed_resume: Dict[str, Any],
    ats_results: Dict[str, Any],
    job_match_results: Optional[Dict[str, Any]] = None,
    ai_critique: Optional[str] = None,
    target_role: Optional[str] = None
) -> str:
    """Convenience helper to generate professional PDF report."""
    return _default_report_generator.generate_pdf_report(
        parsed_resume=parsed_resume,
        ats_results=ats_results,
        job_match_results=job_match_results,
        ai_critique=ai_critique,
        target_role=target_role
    )
