import csv
from pathlib import Path
from typing import List, Dict, Any

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

try:
    import openpyxl
except ImportError:
    openpyxl = None

class DocumentExtractor:
    @staticmethod
    def extract(file_path: Path, file_type: str) -> List[Dict[str, Any]]:
        """
        Extracts structured page content from various file formats.
        Returns a list of dicts: [{"page": 1, "section": "...", "content": "..."}]
        """
        ext = file_type.lower().replace(".", "")
        if ext == "pdf":
            return DocumentExtractor._extract_pdf(file_path)
        elif ext in ["docx", "doc"]:
            return DocumentExtractor._extract_docx(file_path)
        elif ext in ["xlsx", "xls"]:
            return DocumentExtractor._extract_xlsx(file_path)
        elif ext == "csv":
            return DocumentExtractor._extract_csv(file_path)
        else:
            return DocumentExtractor._extract_text(file_path)

    @staticmethod
    def _extract_pdf(file_path: Path) -> List[Dict[str, Any]]:
        if PdfReader is None:
            return [{
                "page": 1,
                "section": "Error",
                "content": "pypdf package is not available in the current Python environment."
            }]
        pages = []
        try:
            reader = PdfReader(str(file_path))
            for idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                # Attempt to determine section header from top lines
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                section = lines[0] if lines else f"Page {idx + 1}"
                pages.append({
                    "page": idx + 1,
                    "section": section[:80],
                    "content": text
                })
        except Exception as e:
            pages.append({
                "page": 1,
                "section": "Error",
                "content": f"Failed to extract PDF: {str(e)}"
            })
        return pages

    @staticmethod
    def _extract_docx(file_path: Path) -> List[Dict[str, Any]]:
        if DocxDocument is None:
            return [{
                "page": 1,
                "section": "Error",
                "content": "python-docx package is not available in the current Python environment."
            }]
        try:
            doc = DocxDocument(str(file_path))
            pages = []
            current_section = "General Information"
            current_text = []
            page_num = 1
            
            for para in doc.paragraphs:
                text = para.text.strip()
                if not text:
                    continue
                style_name = getattr(para.style, "name", "") if para.style else ""
                if style_name.startswith("Heading"):
                    if current_text:
                        pages.append({
                            "page": page_num,
                            "section": current_section,
                            "content": "\n".join(current_text)
                        })
                        current_text = []
                        page_num += 1
                    current_section = text
                else:
                    current_text.append(text)
            
            if current_text:
                pages.append({
                    "page": page_num,
                    "section": current_section,
                    "content": "\n".join(current_text)
                })
            return pages if pages else [{"page": 1, "section": "General", "content": ""}]
        except Exception as e:
            return [{"page": 1, "section": "Error", "content": f"DOCX extraction failed: {str(e)}"}]

    @staticmethod
    def _extract_xlsx(file_path: Path) -> List[Dict[str, Any]]:
        if openpyxl is None:
            return [{
                "page": 1,
                "section": "Error",
                "content": "openpyxl package is not available in the current Python environment."
            }]
        try:
            wb = openpyxl.load_workbook(str(file_path), data_only=True)
            pages = []
            for sheet_idx, sheet_name in enumerate(wb.sheetnames):
                sheet = wb[sheet_name]
                rows = []
                for row in sheet.iter_rows(values_only=True):
                    row_strs = [str(cell) for cell in row if cell is not None]
                    if row_strs:
                        rows.append(" | ".join(row_strs))
                pages.append({
                    "page": sheet_idx + 1,
                    "section": f"Sheet: {sheet_name}",
                    "content": "\n".join(rows)
                })
            return pages
        except Exception as e:
            return [{"page": 1, "section": "Error", "content": f"Excel extraction failed: {str(e)}"}]

    @staticmethod
    def _extract_csv(file_path: Path) -> List[Dict[str, Any]]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                lines = [" | ".join(row) for row in reader if any(row)]
            return [{
                "page": 1,
                "section": file_path.stem,
                "content": "\n".join(lines)
            }]
        except Exception as e:
            return [{"page": 1, "section": "Error", "content": f"CSV extraction failed: {str(e)}"}]

    @staticmethod
    def _extract_text(file_path: Path) -> List[Dict[str, Any]]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
            return [{
                "page": 1,
                "section": file_path.stem,
                "content": text
            }]
        except Exception as e:
            return [{"page": 1, "section": "Error", "content": f"Text extraction failed: {str(e)}"}]
