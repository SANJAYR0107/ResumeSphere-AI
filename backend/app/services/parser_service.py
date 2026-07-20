"""
parser_service.py - Resume PDF Parsing Service

This module is the core text extraction engine for Phase 2.
It is responsible for:
  - Validating that an uploaded file is a PDF
  - Persisting the uploaded file to the uploads folder
  - Extracting all readable text from every page using PyMuPDF (fitz)
  - Cleaning the raw text by removing excessive whitespace
  - Returning structured data (text, page count, character count)

Architecture note:
  This module contains only pure functions (no class state) to remain
  composable, testable, and easy to mock in unit tests.

Dependencies:
  - fitz (PyMuPDF)  : PDF rendering and text extraction
  - pathlib.Path    : File-system path manipulation
  - shutil          : Streaming file copy to disk
  - fastapi         : UploadFile type and HTTPException
"""

import logging
import re
import shutil
from pathlib import Path

import fitz  # PyMuPDF
from fastapi import HTTPException, UploadFile

from backend.app.config import ALLOWED_CONTENT_TYPE, UPLOAD_FOLDER

# Module-level logger – inherits the root logger configured in main.py
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_pdf(file: UploadFile) -> None:
    """Raise HTTP 400 if the uploaded file is not a PDF.

    Validation is performed on both the MIME content-type header sent by the
    client and the file extension.  Checking both reduces the risk of a user
    renaming a non-PDF to trick the server.

    Parameters
    ----------
    file : UploadFile
        The file object received from the FastAPI multipart parser.

    Raises
    ------
    HTTPException (400)
        When the content-type is not ``application/pdf`` OR the filename
        does not end with ``.pdf``.
    """
    # Derive the extension (lower-cased) from the original filename
    extension: str = Path(file.filename or "").suffix.lower()

    if file.content_type != ALLOWED_CONTENT_TYPE or extension != ".pdf":
        logger.warning(
            "Invalid file upload attempt: filename='%s', content_type='%s'",
            file.filename,
            file.content_type,
        )
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid file type '{file.content_type}'. "
                "Only PDF files (application/pdf) are accepted."
            ),
        )

    logger.info("File validation passed: '%s'", file.filename)


def save_uploaded_file(file: UploadFile) -> Path:
    """Persist an in-memory UploadFile to the configured uploads folder.

    The file is streamed in chunks via ``shutil.copyfileobj`` so large
    resumes do not exhaust server RAM.

    Parameters
    ----------
    file : UploadFile
        The validated PDF upload received from the route handler.

    Returns
    -------
    Path
        Absolute path of the saved file on disk.

    Raises
    ------
    HTTPException (500)
        When the file cannot be written due to an OS-level error.
    """
    # Strip any directory components from the filename to prevent path traversal
    # e.g. "../../etc/passwd" → "passwd" (harmless)
    safe_name: str = Path(file.filename or "resume.pdf").name
    destination: Path = UPLOAD_FOLDER / safe_name

    try:
        # Open the destination in binary-write mode and stream the upload
        with destination.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except OSError as exc:
        logger.error("Failed to save uploaded file '%s': %s", file.filename, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Could not save the uploaded file: {exc}",
        ) from exc

    logger.info("Resume saved to disk: '%s'", destination)
    return destination


def extract_text_from_pdf(file_path: Path) -> dict:
    """Extract all readable text from every page of a PDF resume.

    Uses PyMuPDF (fitz) to open the document and iterate over its pages.
    Each page's text is concatenated in reading order.

    Parameters
    ----------
    file_path : Path
        Absolute path to the PDF file that was previously saved to disk.

    Returns
    -------
    dict
        A dictionary with the following keys:

        * ``raw_text``  (str)  – Concatenated text from all pages before cleaning.
        * ``pages``     (int)  – Total number of pages in the document.

    Raises
    ------
    HTTPException (404)
        When the file at ``file_path`` cannot be opened or is not a valid PDF.
    HTTPException (500)
        When an unexpected error occurs during page iteration.
    """
    try:
        # Open the PDF document; fitz raises RuntimeError for invalid/corrupt files
        document: fitz.Document = fitz.open(str(file_path))
    except RuntimeError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Could not open the PDF file '{file_path.name}': {exc}",
        ) from exc

    raw_text: str = ""
    page_count: int = len(document)

    try:
        for page_index in range(page_count):
            page: fitz.Page = document.load_page(page_index)
            # get_text("text") extracts plain Unicode text in reading order
            page_text: str = page.get_text("text")  # type: ignore
            raw_text += page_text
    except Exception as exc:  # noqa: BLE001 – catch-all for unexpected fitz errors
        # page_index may be unbound if page_count == 0 and the loop never ran
        page_num = locals().get("page_index", "?")
        logger.error("Unexpected error reading page %s of '%s': %s", page_num, file_path.name, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error while reading pages: {exc}",
        ) from exc
    finally:
        document.close()  # Always release the file handle

    logger.info("Extracted %d page(s) from '%s'", page_count, file_path.name)
    return {"raw_text": raw_text, "pages": page_count}


def clean_text(raw_text: str) -> str:
    """Normalise raw extracted PDF text for downstream processing.

    Operations applied (in order):
      1. Replace any sequence of whitespace that contains a newline with a
         single newline – preserves paragraph boundaries.
      2. Collapse runs of two or more consecutive blank lines into one.
      3. Strip leading and trailing whitespace from the entire string.

    Parameters
    ----------
    raw_text : str
        The unprocessed text returned by :func:`extract_text_from_pdf`.

    Returns
    -------
    str
        Cleaned text ready for display or further NLP processing.
    """
    # Step 1: Replace horizontal whitespace (spaces/tabs) runs with one space
    text: str = re.sub(r"[^\S\n]+", " ", raw_text)

    # Step 2: Collapse three or more consecutive newlines into two (one blank line)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Step 3: Strip leading/trailing whitespace
    return text.strip()
