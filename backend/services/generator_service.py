import docx
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import io
import fitz  # PyMuPDF

def create_styled_document(analysis_data: dict, attachment_bytes: bytes = None) -> io.BytesIO:
    """基于大模型提取的数据，生成原生带有样式排版的 Word 框架"""
    doc = docx.Document()
    
    # 设置全局中文字体 (比如仿宋或黑体)
    doc.styles['Normal'].font.name = '宋体'
    doc.styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    doc.styles['Normal'].font.size = Pt(12)
    
    # 1. 封面页
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title.add_run(f"\n\n\n\n\n【投标文件】\n\n")
    title_run.font.size = Pt(36)
    title_run.font.bold = True
    
    proj_name = analysis_data.get('projectInfo', {}).get('name', '未命名项目')
    proj_num = analysis_data.get('projectInfo', {}).get('number', '未知编号')
    
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = sub.add_run(f"项目名称：{proj_name}\n项目编号：{proj_num}\n\n\n\n")
    sub_run.font.size = Pt(18)
    
    # 插入分页符
    doc.add_page_break()
    
    # 2. 动态循环生成分册结构 (Volumes)
    volumes = analysis_data.get('volumes', [])
    for vol_idx, vol in enumerate(volumes):
        doc.add_heading(vol.get('volume_name', f'分册 {vol_idx+1}'), level=1)
        items = vol.get('items', [])
        
        for item in items:
            item_name = item.get('name', '未知材料')
            doc.add_heading(item_name, level=2)
            
            # 模板注入：如果 Agent 2 抽取出原文的格式模板文字，则原样克隆注入
            template_text = item.get('template_text')
            if template_text and template_text.strip() not in ['null', 'None']:
                p_info = doc.add_paragraph("【系统智能体提示：以下为从招标文件提取的对应模板格式，请核对并填空】")
                p_info.runs[0].font.color.rgb = docx.shared.RGBColor(0, 128, 0)
                
                # 注入实际模板文字
                p_tmpl = doc.add_paragraph(template_text)
                p_tmpl.style = 'Normal'
            else:
                p_info = doc.add_paragraph("【系统提示：未在招标文件中检索到该材料的特定模板，请在此处插入对应的扫描件或自主撰写正文】")
                p_info.runs[0].font.color.rgb = docx.shared.RGBColor(255, 0, 0)
                
        doc.add_page_break()

    # 3. 废标风险自查清单 (附录)
    doc.add_heading('附录：实质性响应自查表（内部复核用，打印前请删除）', level=1)
    table = doc.add_table(rows=1, cols=2)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = '实质性要求 (★/▲)'
    hdr_cells[1].text = '是否已响应'
    
    for flaw in analysis_data.get('fatalFlaws', []):
        row_cells = table.add_row().cells
        row_cells[0].text = flaw
        row_cells[1].text = '□ 是'

    # 5. 附加证明材料 (PDF 转图片)
    if attachment_bytes:
        doc.add_page_break()
        doc.add_heading('第五部分：资质证明与附件扫描件', level=1)
        try:
            with fitz.open(stream=attachment_bytes, filetype="pdf") as pdf_doc:
                for page_num in range(len(pdf_doc)):
                    page = pdf_doc.load_page(page_num)
                    # 提高渲染分辨率
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_bytes = pix.tobytes("png")
                    
                    # 将图片插入 Word
                    img_stream = io.BytesIO(img_bytes)
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.add_run().add_picture(img_stream, width=Inches(6.0))
        except Exception as e:
            p = doc.add_paragraph(f"【附件转换失败: {str(e)}】")
            p.runs[0].font.color.rgb = docx.shared.RGBColor(255, 0, 0)

    # 保存到内存字节流
    byte_io = io.BytesIO()
    doc.save(byte_io)
    byte_io.seek(0)
    
    return byte_io
