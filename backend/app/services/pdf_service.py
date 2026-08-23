import io
from fastapi import HTTPException, UploadFile, status
from pypdf import PdfReader

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def extract_text_from_pdf(file_contents: bytes, filename: str = "uploaded.pdf") -> str:
    """
    Validates PDF file size and format, extracting raw text from all pages using pypdf.
    Raises HTTPException(400) on invalid PDF format or empty text extraction.
    """
    if len(file_contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File '{filename}' exceeds maximum allowed size of 10MB.",
        )

    if not file_contents.startswith(b"%PDF"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File '{filename}' is not a valid PDF document.",
        )

    try:
        pdf_stream = io.BytesIO(file_contents)
        reader = PdfReader(pdf_stream)
        extracted_pages = []

        for idx, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                extracted_pages.append(text.strip())

        full_text = "\n\n".join(extracted_pages).strip()

        if not full_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"PDF document '{filename}' contains no extractable text.",
            )

        return full_text
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse PDF document '{filename}': {str(e)}",
        )
