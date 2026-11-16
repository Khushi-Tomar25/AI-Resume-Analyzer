"""
resume_parser.py - Multi-format Resume Parsing & Validation Engine
-------------------------------------------------------------------
Parses PDF, DOCX, and TXT resume files to extract raw text, identify key resume
sections, extract contact information, validate document health, and detect
scanned documents requiring OCR.
"""

import os
import io
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple

from config import STANDARD_SECTIONS, MAX_FILE_SIZE_MB
from utils import (
    clean_text,
    extract_email,
    extract_phone,
    extract_links,
    extract_candidate_name,
    get_text_statistics
)


class ResumeParser:
    """
    Robust resume parsing engine with file validation, corruption detection,
    scanned PDF detection, and intelligent section segmentation.
    """

    def __init__(self):
        pass

    # ==========================================
    # 1. File Health & Magic Byte Validation
    # ==========================================

    def validate_file_bytes(self, file_bytes: bytes, file_name: str) -> Tuple[bool, Optional[str]]:
        """
        Validates file integrity using byte signatures (magic bytes)
        and file size bounds.
        """
        if not file_bytes or len(file_bytes) == 0:
            return False, "The uploaded file is empty (0 bytes). Please upload a valid document."

        max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
        if len(file_bytes) > max_bytes:
            return False, f"File size ({round(len(file_bytes)/(1024*1024), 2)}MB) exceeds the {MAX_FILE_SIZE_MB}MB limit."

        name_lower = file_name.lower()

        # PDF magic byte check: must begin with %PDF-
        if name_lower.endswith(".pdf"):
            if not file_bytes.startswith(b"%PDF-"):
                return False, "Corrupted PDF file. The file header does not match the standard PDF format."

        # DOCX magic byte check: DOCX is a zip archive starting with PK\x03\x04
        elif name_lower.endswith(".docx"):
            if not file_bytes.startswith(b"PK\x03\x04"):
                return False, "Corrupted DOCX file. The file is not a valid OpenXML Word document."

        return True, None

    # ==========================================
    # 2. Multi-Format Text Extraction
    # ==========================================

    def extract_from_pdf(self, data_bytes: bytes) -> Tuple[str, int, bool]:
        """
        Extracts raw text from PDF bytes.
        Returns:
            Tuple of (extracted_text, page_count, is_scanned)
        """
        page_count = 0
        extracted_text = ""

        # Method 1: PyMuPDF (pymupdf)
        try:
            import pymupdf
            doc = pymupdf.open(stream=data_bytes, filetype="pdf")
            page_count = len(doc)
            pages = [page.get_text("text") for page in doc]
            extracted_text = "\n".join(pages).strip()
        except Exception:
            # Method 2: pdfplumber fallback
            try:
                import pdfplumber
                with pdfplumber.open(io.BytesIO(data_bytes)) as pdf:
                    page_count = len(pdf.pages)
                    pages = [p.extract_text() or "" for p in pdf.pages]
                    extracted_text = "\n".join(pages).strip()
            except Exception:
                # Method 3: pypdf fallback
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(io.BytesIO(data_bytes))
                    page_count = len(reader.pages)
                    pages = [p.extract_text() or "" for p in reader.pages]
                    extracted_text = "\n".join(pages).strip()
                except Exception as ex:
                    raise ValueError(f"Failed to parse PDF document. The file may be damaged or password-protected: {str(ex)}")

        # Scanned PDF Detection: document has pages but virtually zero text (< 40 characters)
        is_scanned = False
        if page_count > 0 and len(extracted_text.strip()) < 40:
            is_scanned = True

        return extracted_text, page_count, is_scanned

    def extract_from_docx(self, data_bytes: bytes) -> str:
        """
        Extracts text from DOCX bytes with zipfile fallback.
        """
        # Primary: python-docx
        try:
            import docx
            doc = docx.Document(io.BytesIO(data_bytes))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            
            # Extract from tables
            table_text = []
            for table in doc.tables:
                for row in table.rows:
                    cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if cells:
                        table_text.append(" | ".join(cells))

            full_text = "\n".join(paragraphs + table_text).strip()
            if full_text:
                return full_text
        except Exception:
            pass

        # Fallback: standard library zipfile + XML
        try:
            with zipfile.ZipFile(io.BytesIO(data_bytes)) as z:
                xml_content = z.read("word/document.xml")
                root = ET.fromstring(xml_content)
                ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                texts = [elem.text for elem in root.findall(".//w:t", ns) if elem.text]
                return " ".join(texts).strip()
        except Exception as e:
            raise ValueError(f"Failed to parse DOCX file. The file may be corrupted: {str(e)}")

    def extract_from_txt(self, data_bytes: bytes) -> str:
        """
        Extracts plain text with multiple encoding fallbacks.
        """
        for enc in ("utf-8", "latin-1", "cp1252", "utf-16"):
            try:
                return data_bytes.decode(enc)
            except (UnicodeDecodeError, LookupError):
                continue
        return data_bytes.decode("utf-8", errors="ignore")

    # ==========================================
    # 3. Section Segmentation
    # ==========================================

    def identify_sections(self, text: str) -> Dict[str, str]:
        """
        Segments the resume text into standard ATS sections based on headers.
        """
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        sections: Dict[str, List[str]] = {sec: [] for sec in STANDARD_SECTIONS.keys()}
        sections["other"] = []

        current_section = "summary"
        header_lookup = {}
        for sec_key, aliases in STANDARD_SECTIONS.items():
            for alias in aliases:
                header_lookup[alias.lower()] = sec_key

        for line in lines:
            line_clean = re.sub(r"[:\-_#*]", "", line).strip().lower()
            
            # Standalone line check for section title
            matched_sec = None
            if len(line_clean) <= 45:
                for header_alias, sec_name in header_lookup.items():
                    if line_clean == header_alias or line_clean.startswith(header_alias + " "):
                        matched_sec = sec_name
                        break
            
            if matched_sec:
                current_section = matched_sec
            else:
                sections[current_section].append(line)

        # Consolidate non-empty sections
        result = {}
        for sec, content_lines in sections.items():
            joined = "\n".join(content_lines).strip()
            if joined:
                result[sec] = joined

        return result

    # ==========================================
    # 4. Main Parse Pipeline
    # ==========================================

    def parse(self, file_source: Union[str, Path, io.BytesIO, bytes], file_name: str = "") -> Dict[str, Any]:
        """
        Full end-to-end resume parsing, validation, and metadata extraction.
        
        Returns:
            Dict containing:
                - candidate_name: str
                - email: Optional[str]
                - phone: Optional[str]
                - links: Dict[str, str]
                - raw_text: str
                - clean_text: str
                - sections: Dict[str, str]
                - statistics: Dict[str, Any]
                - is_scanned: bool
                - page_count: int
                - parsing_status: "success" | "warning_scanned" | "warning_short" | "error"
                - error_message: Optional[str]
                - warning_message: Optional[str]
        """
        # Convert source to bytes
        data_bytes = b""
        if isinstance(file_source, Path):
            with open(file_source, "rb") as f:
                data_bytes = f.read()
            if not file_name:
                file_name = file_source.name
        elif isinstance(file_source, str):
            is_path = False
            if "\n" not in file_source and "\r" not in file_source:
                try:
                    if os.path.isfile(file_source):
                        is_path = True
                except Exception:
                    is_path = False
            
            if is_path:
                with open(file_source, "rb") as f:
                    data_bytes = f.read()
                if not file_name:
                    file_name = os.path.basename(file_source)
            else:
                data_bytes = file_source.encode("utf-8")
                if not file_name:
                    file_name = "resume.txt"
        elif isinstance(file_source, io.BytesIO):
            data_bytes = file_source.getvalue()
        elif isinstance(file_source, bytes):
            data_bytes = file_source

        # 1. Validation check
        is_valid, validation_err = self.validate_file_bytes(data_bytes, file_name)
        if not is_valid:
            return {
                "candidate_name": "Unknown",
                "email": None,
                "phone": None,
                "links": {},
                "raw_text": "",
                "clean_text": "",
                "sections": {},
                "statistics": get_text_statistics(""),
                "file_name": file_name,
                "file_type": "unknown",
                "is_scanned": False,
                "page_count": 0,
                "parsing_status": "error",
                "error_message": validation_err,
                "warning_message": None
            }

        # 2. Text Extraction
        name_lower = file_name.lower()
        file_type = "txt"
        page_count = 1
        is_scanned = False
        raw_text = ""

        try:
            if name_lower.endswith(".pdf"):
                file_type = "pdf"
                raw_text, page_count, is_scanned = self.extract_from_pdf(data_bytes)
            elif name_lower.endswith(".docx") or name_lower.endswith(".doc"):
                file_type = "docx"
                raw_text = self.extract_from_docx(data_bytes)
            else:
                file_type = "txt"
                raw_text = self.extract_from_txt(data_bytes)
        except Exception as e:
            return {
                "candidate_name": "Unknown",
                "email": None,
                "phone": None,
                "links": {},
                "raw_text": "",
                "clean_text": "",
                "sections": {},
                "statistics": get_text_statistics(""),
                "file_name": file_name,
                "file_type": file_type,
                "is_scanned": False,
                "page_count": 0,
                "parsing_status": "error",
                "error_message": f"Unable to read file: {str(e)}",
                "warning_message": None
            }

        # 3. Clean Text & Scanned PDF Warning
        cleaned = clean_text(raw_text)
        warning_message = None

        if is_scanned:
            parsing_status = "warning_scanned"
            warning_message = (
                "⚠️ Scanned Document Detected: This document appears to be an image-only or scanned PDF without selectable text. "
                "Standard ATS systems and automated text parsers cannot read scanned files. "
                "For accurate ATS scoring and AI analysis, please upload a digital PDF exported directly from Word, Google Docs, or Canva."
            )
        elif len(cleaned) < 50:
            parsing_status = "warning_short"
            warning_message = "The uploaded file has very little readable content. Please verify that the resume text is complete."
        else:
            parsing_status = "success"

        # 4. Extract Contact Details & Sections
        email = extract_email(cleaned)
        phone = extract_phone(cleaned)
        links = extract_links(cleaned)
        candidate_name = extract_candidate_name(cleaned, email=email)
        sections = self.identify_sections(cleaned)
        stats = get_text_statistics(cleaned)

        return {
            "candidate_name": candidate_name,
            "email": email,
            "phone": phone,
            "links": links,
            "raw_text": raw_text,
            "clean_text": cleaned,
            "sections": sections,
            "statistics": stats,
            "file_name": file_name,
            "file_type": file_type,
            "is_scanned": is_scanned,
            "page_count": page_count,
            "parsing_status": parsing_status,
            "error_message": None,
            "warning_message": warning_message
        }


_parser = ResumeParser()

def parse_resume(file_source: Union[str, Path, io.BytesIO, bytes], file_name: str = "") -> Dict[str, Any]:
    """Top-level helper function to parse any resume document."""
    return _parser.parse(file_source, file_name)
