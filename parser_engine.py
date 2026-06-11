import pdfplumber
import docx2txt
import io

class ResumeParser:
    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        """Extracts text from multi-column PDFs using layout preservation."""
        text_content = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                # layout-aware extraction reads blocks accurately instead of raw left-to-right
                page_text = page.extract_text(layout=True)
                if page_text:
                    text_content.append(page_text)
        return "\n".join(text_content)

    @staticmethod
    def extract_text_from_docx(file_bytes: bytes) -> str:
        """Extracts text from DocX templates."""
        file_stream = io.BytesIO(file_bytes)
        return docx2txt.process(file_stream)

    @classmethod
    def parse(cls, filename: str, file_bytes: bytes) -> str:
        """Determines file type and routes to correct parser engine."""
        ext = filename.split(".")[-1].lower()
        if ext == "pdf":
            return cls.extract_text_from_pdf(file_bytes)
        elif ext in ["docx", "doc"]:
            return cls.extract_text_from_docx(file_bytes)
        else:
            raise ValueError(f"Unsupported file format: .{ext}")