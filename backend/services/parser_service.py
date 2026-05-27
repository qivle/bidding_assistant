import pdfplumber
import docx
import io

def parse_pdf(file_bytes: bytes, max_pages: int = 150) -> str:
    """提取 PDF 文本内容，注入页码标记"""
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for i, page in enumerate(pdf.pages):
                if i >= max_pages:
                    break
                page_text = page.extract_text()
                if page_text:
                    text += f"\n\n---[第{i+1}页]---\n\n"
                    text += page_text + "\n"
    except Exception as e:
        print(f"PDF parsing error: {e}")
    return text

def parse_docx(file_bytes: bytes) -> str:
    """提取 Word 文档内容，适当注入段落标识"""
    text = ""
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        for i, para in enumerate(doc.paragraphs):
            # 为了给大模型提供一些位置上下文，我们在明显的标题或者每隔50段注入一次标记
            if para.style.name.startswith('Heading') or i % 50 == 0:
                text += f"\n---[文档位置: 段落 {i+1}]---\n"
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

