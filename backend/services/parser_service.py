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
    """提取 Word 文档内容，按顺序提取段落和表格"""
    text = ""
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        for i, child in enumerate(doc.element.body):
            if i % 50 == 0:
                text += f"\n---[文档位置: 块 {i+1}]---\n"
                
            if child.tag.endswith('p'):
                p = docx.text.paragraph.Paragraph(child, doc)
                if p.style.name.startswith('Heading'):
                    text += f"\n---[文档位置: 标题]---\n"
                text += p.text + "\n"
            elif child.tag.endswith('tbl'):
                text += "\n[此处存在一个文档表格，请注意这可能是一个模板框架]\n"
                # 简单提取一点表格文本以便模型判断
                tbl = docx.table.Table(child, doc)
                for row in tbl.rows:
                    row_text = []
                    for cell in row.cells:
                        row_text.append(cell.text.replace('\n', ' ').strip())
                    text += " | ".join(row_text) + "\n"
                text += "\n"
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

