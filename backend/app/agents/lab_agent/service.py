
"""
Laboratory Agent Service

Supports:
- Pasted laboratory report text
- Manual structured laboratory entries
- Text-based PDF reports
- Scanned PDF reports using OCR
- JPG, JPEG and PNG laboratory reports

Extracts text and sends it to the existing deterministic lab parser.
"""

import io
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Union, Optional

import pdfplumber
import pypdfium2 as pdfium
import pytesseract
from PIL import Image

from backend.app.schemas.labs import ExtractedLabItem
from backend.app.agents.lab_agent.lab_parser import parse_lab_text

logger = logging.getLogger(__name__)


class LabAgentService:

    # Set the Tesseract executable if it exists at the default Windows path.
    TESSERACT_PATH = (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )

    @staticmethod
    def _configure_tesseract():
        """Configure the Windows Tesseract executable."""
        if os.path.exists(LabAgentService.TESSERACT_PATH):
            pytesseract.pytesseract.tesseract_cmd = (
                LabAgentService.TESSERACT_PATH
            )

    @staticmethod
    def extract_from_text(text: str) -> List[ExtractedLabItem]:
        """Extract laboratory values from already available text."""
        return parse_lab_text(text)

    @staticmethod
    def extract_from_dict_list(
        items: List[Dict[str, Any]]
    ) -> List[ExtractedLabItem]:
        """Convert manually entered laboratory values into schema objects."""
        results = []

        for d in items:
            value = d.get("value")
            numeric_value = None

            if value is not None:
                try:
                    numeric_value = float(value)
                except (TypeError, ValueError):
                    numeric_value = None

            results.append(
                ExtractedLabItem(
                    analyte_name=(
                        d.get("analyte_name")
                        or d.get("test_name", "")
                    ),
                    raw_value=str(
                        d.get("raw_value")
                        if d.get("raw_value") is not None
                        else value if value is not None else ""
                    ),
                    numeric_value=numeric_value,
                    unit=d.get("unit"),
                    reference_interval=d.get("reference_interval"),
                    confidence=1.0,
                )
            )

        return results

    @staticmethod
    def _extract_pdf_text(file_bytes: bytes) -> str:
        """
        Extract text directly from a PDF.

        If the PDF contains little or no selectable text,
        render its pages and use OCR.
        """
        extracted_pages = []

        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            if len(pdf.pages) > 20:
                raise ValueError(
                    "PDF contains more than 20 pages. "
                    "Please upload a smaller report."
                )

            for page in pdf.pages:
                text = page.extract_text() or ""
                extracted_pages.append(text)

        combined_text = "\n".join(extracted_pages).strip()

        # Text-based PDF: use direct extraction.
        if len(combined_text) >= 40:
            return combined_text

        # Scanned PDF: use OCR.
        LabAgentService._configure_tesseract()

        document = pdfium.PdfDocument(file_bytes)
        ocr_pages = []

        try:
            if len(document) > 20:
                raise ValueError(
                    "PDF contains more than 20 pages. "
                    "Please upload a smaller report."
                )

            for index in range(len(document)):
                page = document[index]

                # Render at 2x resolution for OCR.
                bitmap = page.render(scale=2)
                image = bitmap.to_pil()

                page_text = pytesseract.image_to_string(
                    image,
                    config="--psm 6"
                )

                ocr_pages.append(page_text)

        finally:
            document.close()

        return "\n".join(ocr_pages).strip()

    @staticmethod
    def _extract_image_text(file_bytes: bytes) -> str:
        """Extract text from JPG, JPEG or PNG using Tesseract OCR."""
        LabAgentService._configure_tesseract()

        image = Image.open(io.BytesIO(file_bytes))

        # Convert to RGB to support different image modes.
        image = image.convert("RGB")

        # Resize small images to improve OCR readability.
        if image.width < 1500:
            scale = 1500 / image.width
            new_size = (
                1500,
                int(image.height * scale)
            )
            image = image.resize(new_size)

        return pytesseract.image_to_string(
            image,
            config="--psm 6"
        ).strip()

    @staticmethod
    def extract_text_from_file(
    file_data: Union[str, bytes, bytearray, Any],
    filename: Optional[str] = None,
    ) -> str:
        """
        Extract text from an uploaded file.

        file_data may be:
        - A filesystem path
        - Raw file bytes
        - A Streamlit UploadedFile object

        Supported formats: PDF, JPG, JPEG and PNG.
        """

        # Handle Streamlit UploadedFile objects.
        if hasattr(file_data, "getvalue"):
            if filename is None:
                filename = getattr(file_data, "name", None)
            file_bytes = file_data.getvalue()

        # Handle filesystem paths.
        elif isinstance(file_data, str):
            path = Path(file_data)

            if not path.is_file():
                raise FileNotFoundError(
                    f"Laboratory report not found: {file_data}"
                )

            if filename is None:
                filename = path.name

            file_bytes = path.read_bytes()

        # Handle raw bytes.
        elif isinstance(file_data, (bytes, bytearray)):
            file_bytes = bytes(file_data)

        else:
            raise TypeError(
                "Unsupported file input. Provide a file path, "
                "bytes, or Streamlit UploadedFile."
            )

        if not file_bytes:
            raise ValueError("Uploaded laboratory report is empty.")

        extension = Path(filename or "").suffix.lower()

        if extension == ".pdf":
            extracted_text = LabAgentService._extract_pdf_text(
                file_bytes
            )

        elif extension in (".jpg", ".jpeg", ".png"):
            extracted_text = LabAgentService._extract_image_text(
                file_bytes
            )

        else:
            raise ValueError(
                "Unsupported file format. "
                "Please upload PDF, JPG, JPEG or PNG."
            )

        if not extracted_text.strip():
            raise ValueError(
                "No readable text could be extracted. "
                "Please upload a clearer report."
            )

        logger.info("Extracted laboratory report text from %s",filename or "uploaded report",)

        return extracted_text

    @staticmethod
    def extract_from_file(
        file_data: Union[str, bytes, bytearray, Any],
        filename: Optional[str] = None,
    ) -> List[ExtractedLabItem]:
        """Extract and parse laboratory items from an uploaded file."""
        extracted_text = LabAgentService.extract_text_from_file(
            file_data,
            filename
        )
        return parse_lab_text(extracted_text)


lab_agent_service = LabAgentService()
