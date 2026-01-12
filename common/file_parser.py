"""
File parsing utilities for document upload
Supports: PDF, DOCX, TXT, Markdown
"""

import io
import os
import logging
from typing import Tuple

logging.basicConfig(level=logging.INFO)


def parse_file(content: bytes, filename: str) -> Tuple[bool, str, str]:
    """
    Parse uploaded file and extract text content
    
    Args:
        content: Raw file bytes
        filename: Original filename with extension
        
    Returns:
        Tuple of (success, text_content, error_message)
    """
    ext = os.path.splitext(filename)[1].lower()
    
    try:
        if ext == ".pdf":
            return _parse_pdf(content, filename)
        elif ext == ".docx":
            return _parse_docx(content, filename)
        else:
            return _parse_text(content, filename)
    except Exception as e:
        logging.exception(f"[FileParser] Failed to parse {filename}: {e}")
        return False, "", f"Parse error: {str(e)}"


def _parse_pdf(content: bytes, filename: str) -> Tuple[bool, str, str]:
    """Parse PDF file"""
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(content))
        pages = []
        for p in reader.pages:
            pages.append(p.extract_text() or "")
        text = "\n\n".join(pages)
        
        if not text.strip():
            logging.warning(f"[FileParser] PDF contained no extractable text: {filename}")
            return False, "", "No text extracted from PDF. If it's scanned, try a text-based file."
        
        return True, text, ""
    except Exception as e:
        return False, "", f"PDF parse error: {str(e)}"


def _parse_docx(content: bytes, filename: str) -> Tuple[bool, str, str]:
    """Parse DOCX file"""
    try:
        from docx import Document
        doc = Document(io.BytesIO(content))
        text = "\n".join(para.text for para in doc.paragraphs)
        
        if not text.strip():
            logging.warning(f"[FileParser] DOCX contained no extractable text: {filename}")
            return False, "", "No text extracted from DOCX. Please upload a text-rich document."
        
        return True, text, ""
    except Exception as e:
        return False, "", f"DOCX parse error: {str(e)}"


def _parse_text(content: bytes, filename: str) -> Tuple[bool, str, str]:
    """Parse text/markdown file"""
    try:
        # Try UTF-8 first, then fallback to latin-1
        try:
            text = content.decode("utf-8", errors="ignore")
        except Exception:
            text = content.decode("latin-1", errors="ignore")
        
        if not text.strip():
            logging.warning(f"[FileParser] Text file contained no extractable text: {filename}")
            return False, "", "No text extracted from file. Please upload a non-empty text file."
        
        return True, text, ""
    except Exception as e:
        return False, "", f"Text parse error: {str(e)}"


def save_upload(content: bytes, filename: str, upload_dir: str = "/app/data/uploads") -> bool:
    """
    Save uploaded file to disk
    
    Args:
        content: File bytes
        filename: Original filename
        upload_dir: Directory to save uploads
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        os.makedirs(upload_dir, exist_ok=True)
        save_path = os.path.join(upload_dir, filename)
        with open(save_path, 'wb') as f:
            f.write(content)
        logging.info(f"[FileParser] Saved upload to {save_path}")
        return True
    except Exception as e:
        logging.warning(f"[FileParser] Failed to save upload: {e}")
        return False
