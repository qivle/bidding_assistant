import docx
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import io
import fitz  # PyMuPDF
import copy

from docx.oxml.ns import qn

def find_element_and_copy(source_doc, marker_text, dest_doc, all_markers=None):
    """
    在 source_doc 中查找包含 marker_text 的段落，
    通常在标书中，模板会放在文档的最后面，而在前面的目录或要求说明中会提及。
    为了避免拷贝前面的说明文字，我们将寻找 marker_text 的【最后一次】有效出现位置，并从那里开始拷贝。
    """
    if not marker_text or marker_text.strip() in ['null', 'None']:
        return False
        
    clean_marker = marker_text.strip().replace(" ", "")
    if not clean_marker:
        return False
        
    other_markers = []
    if all_markers:
        other_markers = [m.strip().replace(" ", "") for m in all_markers if m and m.strip().replace(" ", "") != clean_marker]

    candidate_indices = []
    # 首先遍历所有元素，找到所有可能的起始位置
    for idx, elem in enumerate(source_doc.element.body):
        if elem.tag.endswith('p'):
            p = docx.text.paragraph.Paragraph(elem, source_doc)
            clean_p = p.text.strip().replace(" ", "")
            if clean_marker in clean_p:
                # 启发式判断：标题段落通常不会很长（排除掉大段的说明文字）
                if len(clean_p) < len(clean_marker) + 15:
                    candidate_indices.append(idx)
                    
    if not candidate_indices:
        return False
        
    # 取最后一个匹配位置，因为真正的模板附件通常在标书末尾
    start_idx = candidate_indices[-1]
    
    elements_copied = 0
    max_elements = 100 # 稍微放宽拷贝的元素数量
    
    body_elements = list(source_doc.element.body)
    
    import re
    
    for i in range(start_idx, len(body_elements)):
        elem = body_elements[i]
        
        # 停止拷贝的条件：遇到了下一个明显的标题，并且已经拷贝了一些内容
        if elements_copied > 0 and elem.tag.endswith('p'):
            p = docx.text.paragraph.Paragraph(elem, source_doc)
            text = p.text.strip()
            clean_text = text.replace(" ", "")
            is_heading = p.style.name.startswith('Heading')
            
            # 判断是否是下一个模板的标题
            is_new_template = False
            if 2 < len(text) < 40:
                # 1. 启发式正则
                if text.startswith(('附件', '附表', '格式', '第')):
                    is_new_template = True
                elif re.match(r'^[（\(]?[一二三四五六七八九十\d]+[）\)、]', text):
                    if any(keyword in text for keyword in ['函', '表', '格式', '声明', '部分']):
                        is_new_template = True
                # 2. 绝对匹配其他已知模板的特征词
                if clean_text and any((om in clean_text or clean_text in om) for om in other_markers):
                    is_new_template = True
                        
            if is_heading or is_new_template:
                break
                
        # 深拷贝 XML 节点
        new_elem = copy.deepcopy(elem)
        
        # 关键修复：不能直接 append，必须插入到 sectPr（如果有）之前，否则 Word 会把它们全部丢到文档最后或破坏结构
        sectPr = dest_doc.element.body.find(qn('w:sectPr'))
        if sectPr is not None:
            sectPr.addprevious(new_elem)
        else:
            dest_doc.element.body.append(new_elem)
            
        elements_copied += 1
        
        if elements_copied >= max_elements:
            break
            
    return elements_copied > 0

def create_styled_document(analysis_data: dict, volume_index: int, attachment_bytes: bytes = None, source_bytes: bytes = None, source_filename: str = None) -> io.BytesIO:
    """基于大模型提取的数据，生成原生带有样式排版的 Word 分册"""
    doc = docx.Document()
    
    # 设置全局中文字体
    doc.styles['Normal'].font.name = '宋体'
    doc.styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    doc.styles['Normal'].font.size = Pt(12)
    
    # 加载源文档（如果存在且是 Word）
    source_doc = None
    if source_bytes and source_filename and source_filename.lower().endswith('.docx'):
        try:
            source_doc = docx.Document(io.BytesIO(source_bytes))
        except Exception as e:
            print(f"Error loading source docx: {e}")
    
    volumes = analysis_data.get('volumes', [])
    if volume_index < 0 or volume_index >= len(volumes):
        raise ValueError("Invalid volume index")
        
    vol = volumes[volume_index]
    
    # 封面
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title.add_run(f"\n\n\n\n\n【{vol.get('volume_name', '投标文件')}】\n\n")
    title_run.font.size = Pt(36)
    title_run.font.bold = True
    
    proj_name = analysis_data.get('projectInfo', {}).get('name', '未命名项目')
    proj_num = analysis_data.get('projectInfo', {}).get('number', '未知编号')
    
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = sub.add_run(f"项目名称：{proj_name}\n项目编号：{proj_num}\n\n\n\n")
    sub_run.font.size = Pt(18)
    
    doc.add_page_break()
    
    # 提取所有的 marker 用于辅助防越界
    items = vol.get('items', [])
    all_markers = []
    for item in items:
        tt = item.get('template_text')
        if tt and tt.strip() not in ['null', 'None']:
            all_markers.append(tt)
            
    for item in items:
        item_name = item.get('name', '未知材料')
        doc.add_heading(item_name, level=2)
        
        template_text = item.get('template_text')
        has_template = False
        
        if source_doc and template_text:
            # 尝试在源文档中查找并克隆
            has_template = find_element_and_copy(source_doc, template_text, doc, all_markers)
            
        if not has_template:
            # 留白或简单提示
            if template_text and template_text.strip() not in ['null', 'None']:
                p_info = doc.add_paragraph(f"[原文档模板特征词：{template_text}，未自动匹配到格式，请自行插入]")
                p_info.runs[0].font.color.rgb = docx.shared.RGBColor(128, 128, 128)
            else:
                p_info = doc.add_paragraph("\n[请在此处插入对应的正文或扫描件]\n")
                p_info.runs[0].font.color.rgb = docx.shared.RGBColor(128, 128, 128)
                
        doc.add_page_break()

    # 附加证明材料 (PDF 转图片)
    if attachment_bytes:
        doc.add_heading('附件：资质证明与附件扫描件', level=1)
        try:
            with fitz.open(stream=attachment_bytes, filetype="pdf") as pdf_doc:
                for page_num in range(len(pdf_doc)):
                    page = pdf_doc.load_page(page_num)
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_bytes = pix.tobytes("png")
                    
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
