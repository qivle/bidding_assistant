import pdfplumber
import docx
import io

def parse_pdf(file_bytes: bytes, max_pages: int = 30) -> str:
    """提取 PDF 文本内容，为了演示和速度，默认限制前 30 页"""
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for i, page in enumerate(pdf.pages):
                if i >= max_pages:
                    break
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"PDF parsing error: {e}")
    return text

def parse_docx(file_bytes: bytes) -> str:
    """提取 Word 文档内容"""
    text = ""
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"DOCX parsing error: {e}")
    return text

def parse_document(filename: str, file_bytes: bytes) -> str:
    if filename.lower().endswith(".pdf"):
        return parse_pdf(file_bytes)
    elif filename.lower().endswith(".docx"):
        return parse_docx(file_bytes)
    else:
        return "不支持的文件格式，仅支持 PDF 或 DOCX。"
