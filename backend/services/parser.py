import fitz  # PyMuPDF
from docx import Document

import re


def extract_text_pdf(file_bytes: bytes) -> str:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages_out = []

    for page in doc:
        d = page.get_text("dict")

        lines_out = []

        for block in d.get("blocks", []):
            # only text blocks
            if block.get("type") != 0:
                continue

            for line in block.get("lines", []):
                # each line has spans; join spans in their natural order
                spans = line.get("spans", [])
                if not spans:
                    continue

                line_text = "".join(s.get("text", "") for s in spans).strip()
                if line_text:
                    lines_out.append(line_text)

        page_text = "\n".join(lines_out)

        # light cleanup
        page_text = re.sub(r"[ \t]+", " ", page_text)
        page_text = re.sub(r"\n{3,}", "\n\n", page_text)

        pages_out.append(page_text)

    return "\n\n".join(pages_out).strip()


def extract_text_docx(file_bytes: bytes) -> str:
    import io
    f = io.BytesIO(file_bytes)
    doc = Document(f)
    paras = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    return "\n".join(paras).strip()
