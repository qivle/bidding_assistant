import openai
from openai import AsyncOpenAI
import json
import httpx
from models.schemas import AIConfig
import re
from typing import AsyncGenerator

def clean_json_text(text: str) -> str:
    """清理 LLM 返回的文本，只保留 JSON 部分"""
    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    return text.strip()

async def call_llm_with_fallback(prompt: str, config: AIConfig, use_flash: bool = False) -> str:
    base_url = config.baseUrl.strip() if config.baseUrl else ""
    if "api.deepseek.com" in base_url and not base_url.endswith("/v1") and not base_url.endswith("/v1/"):
        base_url = base_url.rstrip("/") + "/v1"
        
    client = AsyncOpenAI(
        api_key=config.apiKey,
        base_url=base_url,
        http_client=httpx.AsyncClient(verify=False, trust_env=False)
    )
    
    target_model = config.model_flash if (use_flash and config.model_flash) else config.model
    
    try:
        res = await client.chat.completions.create(
            model=target_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        return res.choices[0].message.content
    except Exception as e:
        if "response_format" in str(e) or "JSON" in str(e):
            print(f"Model does not support json_object format, falling back to standard text. Error: {e}")
            try:
                res2 = await client.chat.completions.create(
                    model=target_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0
                )
                return res2.choices[0].message.content
            except Exception as e2:
                print(f"Retry without JSON mode also failed: {e2}")
                raise e2
        else:
            raise e

async def extract_bidding_info(text: str, config: AIConfig) -> dict:
    prompt1 = f"""
    你是一个专业的招投标分析专家。请仔细阅读以下招标文件片段，进行初步拆解。
    【任务1】：提取项目信息(name, number, budget)。
    【任务2】：提取致命风险(fatalFlaws)。请找到所有带有 "★", "▲", "必须提供", "实质性响应" 等字眼的废标条款。
    **重要指令**：
    - 请将废标项进行归类整理，例如分为“商务要求”、“技术参数要求”、“特定资质要求”等大类。
    - 请根据文本中我注入的 `---[文档位置: 段落 X]---` 标记，尽可能准确地写出该条款所在的页码或段落位置。如果找不到，可写“未知”。
    - **切记**：不要将普通的常规资质文件（如营业执照复印件、法人身份证等）列入此风险雷达列表中，除非它带有非常规的实质性约束条件。
    
    【任务3】：提取投标文件分册结构(volumes)。政企标书通常分为多个分册。
    **极度严厉指令（防止遗漏与支持层级）**：
    1. 【表单无序号规则】：强制要求！如果原文中有“封面”、“目录”，你必须将它们作为 item 提取出来，绝不能遗漏！但是【绝对不能】擅自给它们加上序号（如不能写成“1. 封面”，只能写“封面”）。只有原文中明确带有序号的实体文件才能保留序号。
    2. 【分册锚点规则】：真正的分册依据通常是类似“分为三部分”、“第一分册/第二分册”、“资格审查文件”、“商务技术文件”、“报价文件”等独立封装要求。如果原文出现了“12.1 响应文件组成（三部分）”，不能把“12.1 响应文件组成”当做分册名。必须向下钻取，把“（一）资格证明文件”、“（二）商务文件”等作为真正的 volume_name。
    3. 请完全保留原文中的层级号和所有细分标号（如 '2.1 商务文件'，'(1) 投标声明书' 到 '(14)' 全部条目）。
    4. 绝对不允许省略、合并或跳过任何一个文件要求！如果原文有14条商务文件和7条技术文件，你的列表中必须如实出现这21个独立项目，必须逐一输出！
    5. 如果招标文件要求将“商务文件”和“技术文件”合并封装在一个叫做“商务技术文件”的分册中，你【必须】只生成一个 volume！绝不能拆分为两个 volume！你应该把“2.1 商务文件”和“2.2 技术文件”作为 `"type": "heading"` 放在同一个 volume 的 items 里。
    6. 绝不允许丢弃条目前面的序号！`name` 字段的值必须严格以原始序号开头，如 '(1) 投标声明书'，绝不能擅自删减序号！

    请严格以 JSON 格式输出：
    {{
        "projectInfo": {{"name": "", "number": "", "budget": ""}},
        "fatalFlaws": [
            {{
                "category": "商务与资质要求",
                "items": [
                    {{"description": "★ 投标人必须具备建筑工程一级资质", "page": "第12页"}}
                ]
            }}
        ],
        "volumes": [
            {{
                "volume_name": "商务技术文件",
                "items": [
                    {{"name": "2.1 商务文件", "is_required": false, "type": "heading"}},
                    {{"name": "(1) 投标声明书", "is_required": true, "type": "file"}},
                    {{"name": "(2) 法定代表人授权委托书", "is_required": true, "type": "file"}}
                ]
            }}
        ]
    }}
    
    招标文件内容片段：
    {text} 
    """
    
    try:
        print("Running Agent 1 (Structure & Risks)...")
        content1 = await call_llm_with_fallback(prompt1, config)
        cleaned_content1 = clean_json_text(content1)
        base_json = json.loads(cleaned_content1)
        
        # Agent 3: 核验与修复
        prompt3 = f"""
        你是招投标解析的质检与修复专家。
        这是前置大模型初步提取的JSON结构：
        {json.dumps(base_json, ensure_ascii=False)}
        
        请严格对照以下招标文件原文，对这个 JSON 执行【必须的】核验与纠偏：
        1. **合并分册检查**：如果原文要求将“商务文件”和“技术文件”放在一起（例如都叫“商务技术文件”），但上面的 JSON 错误地把它们拆成了两个 `volumes`，你必须将它们合并为同一个 volume（如 `volume_name: "商务技术文件"`），并将“商务文件”和“技术文件”作为 `type: "heading"` 放在 items 数组中！
        2. **找回丢失的序号**：强制检查每一个 item 的 `name`！如果前置模型擅自删掉了诸如 `(1)`、`(2)`、`一、` 等原始序号，你必须从原文中找回来，并给每一个 name 加上它在原文中原本就有的序号！例如 `(1) 投标声明书`。
        3. **查漏补缺**：严格对照原文，检查是否有遗漏的文件要求，确保一一对应，一个都不能少。
        4. **剔除伪造序号**：允许保留“封面”、“目录”等项目，但必须强制检查它们的 name。如果原文并没有给它们分配序号，你必须将擅自添加的序号删掉（例如把“1. 封面”纠正回“封面”）。
        5. **纠正分册名**：如果 volume_name 被错误地命名为“响应文件组成”或大类标题，请将其修正为真正的分册名（如“资格证明文件”、“商务技术文件”、“报价文件”等）。
        
        【必须遵守的标准修改示例】：
        如果原文要求将“商务文件”和“技术文件”合并，且有序号，你修改后的 `volumes` 数组应该严格长这样（包含 type="heading" 且保留原始序号）：
        [
            {{
                "volume_name": "商务技术文件",
                "items": [
                    {{"name": "2.1 商务文件", "is_required": false, "type": "heading"}},
                    {{"name": "(1) 投标声明书", "is_required": true, "type": "file"}},
                    {{"name": "(2) 法定代表人授权委托书", "is_required": true, "type": "file"}},
                    {{"name": "2.2 技术文件", "is_required": false, "type": "heading"}},
                    {{"name": "(1) 服务响应表", "is_required": true, "type": "file"}}
                ]
            }}
        ]
        
        请输出经过严格核验和修正后的完整 JSON，只输出 JSON，不要任何多余字符。
        
        招标文件原文片段：
        {text}
        """
        print("Running Agent 3 (Verification)...")
        content3 = await call_llm_with_fallback(prompt3, config)
        cleaned_content3 = clean_json_text(content3)
        base_json = json.loads(cleaned_content3)
        
        # Agent 2: 模板特征词抽取
        prompt2 = f"""
        你是一个文本匹配与定位专家。
        这是之前提取出的标书结构JSON：
        {json.dumps(base_json, ensure_ascii=False)}
        
        【任务】：招标文件原文的后半部分通常有“响应文件格式”或“附件模板”章节。请遍历 JSON 中 volumes 里的所有 items。
        如果某个 item（比如各种承诺函、声明函、偏离表、报价表、业绩表等）在原文中附带了**具体的模板、表格或填写框架**，请**提取该模板在原文中的确切起始标题或特征词**（例如："附件一：法定代表人授权委托书" 或 "（7）类似成功案例的业绩"）。
        
        **极度重要指令**：
        1. 即使原文标有“格式自拟”、“格式可自行调整”或要求提供“复印件”，**只要原文下面紧跟着画了一个表格或提供了一个填写的框架**，就提取它的特征词作为 `template_text`。
        - **注意**：提取的模板特征词必须是真正的模板或附件在文档结尾处独立成页的真实模板标题（例如：'附件一：投标声明书'，或'（7）类似成功案例的业绩证明材料'）。**绝不要**被正文要求中的指导语（如'内容见投标声明书'）所蒙骗！
        2. 如果确实没有任何专门的表格或填写框架（纯粹只要一份复印件或自由编写，没有提供格式），请果断返回 null，绝不要摘抄正文的说明语句凑数！
        
        填入该 item 的 `template_text` 字段。
        
        请返回更新后完整的 JSON（保持原有结构，仅将 template_text 字段填充为特征词）。
        请严格以 JSON 格式输出，不要包含任何多余的前言或后记。
        
        招标文件原文片段：
        {text}
        """
        print("Running Agent 2 (Template Marker Extraction)...")
        content2 = await call_llm_with_fallback(prompt2, config, use_flash=True)
        
        with open("llm_debug.txt", "w", encoding="utf-8") as f:
            f.write("=== AGENT 1 ===\n" + cleaned_content1 + "\n\n=== AGENT 3 ===\n" + cleaned_content3 + "\n\n=== AGENT 2 RAW ===\n" + content2)
            
        cleaned_content2 = clean_json_text(content2)
        final_json = json.loads(cleaned_content2)
        return final_json
        
    except Exception as e:
        print(f"LLM API Error: {e}")
        return {
            "projectInfo": {"name": "未知", "number": "未知", "budget": "未知"},
            "fatalFlaws": [],
            "volumes": []
        }

async def extract_bidding_info_stream(text: str, config: AIConfig) -> AsyncGenerator[str, None]:
    base_url = config.baseUrl.strip() if config.baseUrl else ""
    if "api.deepseek.com" in base_url and not base_url.endswith("/v1") and not base_url.endswith("/v1/"):
        base_url = base_url.rstrip("/") + "/v1"
        
    client = AsyncOpenAI(
        api_key=config.apiKey,
        base_url=base_url,
        http_client=httpx.AsyncClient(verify=False, trust_env=False)
    )
    
    yield json.dumps({"status": "agent1", "message": "Agent 1: 正在阅读全文，提取废标项与分册结构..."}) + "\n"
    
    prompt1 = f"""
    你是一个专业的招投标分析专家。请仔细阅读以下招标文件片段，进行初步拆解。
    【任务1】：提取项目信息(name, number, budget)。
    【任务2】：提取致命风险(fatalFlaws)。请找到所有带有 "★", "▲", "必须提供", "实质性响应" 等字眼的废标条款。
    **重要指令**：
    - 请将废标项进行归类整理，例如分为“商务要求”、“技术参数要求”、“特定资质要求”等大类。
    - 请根据文本中我注入的 `---[文档位置: 段落 X]---` 标记，尽可能准确地写出该条款所在的页码或段落位置。如果找不到，可写“未知”。
    - **切记**：不要将普通的常规资质文件（如营业执照复印件、法人身份证等）列入此风险雷达列表中，除非它带有非常规的实质性约束条件。
    
    【任务3】：提取投标文件分册结构(volumes)。政企标书通常分为多个分册。
    **极度严厉指令（防止遗漏与支持层级）**：
    1. 【表单无序号规则】：强制要求！如果原文中有“封面”、“目录”，你必须将它们作为 item 提取出来，绝不能遗漏！但是【绝对不能】擅自给它们加上序号（如不能写成“1. 封面”，只能写“封面”）。只有原文中明确带有序号的实体文件才能保留序号。
    2. 【分册锚点规则】：真正的分册依据通常是类似“分为三部分”、“第一分册/第二分册”、“资格审查文件”、“商务技术文件”、“报价文件”等独立封装要求。如果原文出现了“12.1 响应文件组成（三部分）”，不能把“12.1 响应文件组成”当做分册名。必须向下钻取，把“（一）资格证明文件”、“（二）商务文件”等作为真正的 volume_name。
    3. 请完全保留原文中的层级号和所有细分标号（如 '2.1 商务文件'，'(1) 投标声明书' 到 '(14)' 全部条目）。
    4. 绝对不允许省略、合并或跳过任何一个文件要求！如果原文有14条商务文件和7条技术文件，你的列表中必须如实出现这21个独立项目，必须逐一输出！
    5. 如果招标文件要求将“商务文件”和“技术文件”合并封装在一个叫做“商务技术文件”的分册中，你【必须】只生成一个 volume！绝不能拆分为两个 volume！你应该把“2.1 商务文件”和“2.2 技术文件”作为 `"type": "heading"` 放在同一个 volume 的 items 里。
    6. 绝不允许丢弃条目前面的序号！`name` 字段的值必须严格以原始序号开头，如 '(1) 投标声明书'，绝不能擅自删减序号！

    请严格以 JSON 格式输出：
    {{
        "projectInfo": {{"name": "", "number": "", "budget": ""}},
        "fatalFlaws": [
            {{
                "category": "商务与资质要求",
                "items": [
                    {{"description": "★ 投标人必须具备建筑工程一级资质", "page": "第12页"}}
                ]
            }}
        ],
        "volumes": [
            {{
                "volume_name": "商务技术文件",
                "items": [
                    {{"name": "2.1 商务文件", "is_required": false, "type": "heading"}},
                    {{"name": "(1) 投标声明书", "is_required": true, "type": "file"}},
                    {{"name": "(2) 法定代表人授权委托书", "is_required": true, "type": "file"}}
                ]
            }}
        ]
    }}
    
    招标文件内容片段：
    {text} 
    """
    
    try:
        res = await client.chat.completions.create(
            model=config.model,
            messages=[{"role": "user", "content": prompt1}],
            temperature=0.0,
            stream=True
        )
        content1 = ""
        async for chunk in res:
            if chunk.choices and chunk.choices[0].delta.content:
                text_chunk = chunk.choices[0].delta.content
                content1 += text_chunk
                yield json.dumps({"status": "chunk1", "text": text_chunk}) + "\n"
        
        cleaned_content1 = clean_json_text(content1)
        base_json = json.loads(cleaned_content1)
        
        yield json.dumps({"status": "agent3", "message": "Agent 3: 正在执行极度严格的质检核验，合并分册结构并找回丢失的序号..."}) + "\n"
        
        prompt3 = f"""
        你是招投标解析的质检与修复专家。
        这是前置大模型初步提取的JSON结构：
        {json.dumps(base_json, ensure_ascii=False)}
        
        请严格对照以下招标文件原文，对这个 JSON 执行【必须的】核验与纠偏：
        1. **合并分册检查**：如果原文要求将“商务文件”和“技术文件”放在一起（例如都叫“商务技术文件”），但上面的 JSON 错误地把它们拆成了两个 `volumes`，你必须将它们合并为同一个 volume（如 `volume_name: "商务技术文件"`），并将“商务文件”和“技术文件”作为 `type: "heading"` 放在 items 数组中！
        2. **找回丢失的序号**：强制检查每一个 item 的 `name`！如果前置模型擅自删掉了诸如 `(1)`、`(2)`、`一、` 等原始序号，你必须从原文中找回来，并给每一个 name 加上它在原文中原本就有的序号！例如 `(1) 投标声明书`。
        3. **查漏补缺**：严格对照原文，检查是否有遗漏的文件要求，确保一一对应，一个都不能少。
        4. **剔除伪造序号**：允许保留“封面”、“目录”等项目，但必须强制检查它们的 name。如果原文并没有给它们分配序号，你必须将擅自添加的序号删掉（例如把“1. 封面”纠正回“封面”）。
        5. **纠正分册名**：如果 volume_name 被错误地命名为“响应文件组成”或大类标题，请将其修正为真正的分册名（如“资格证明文件”、“商务技术文件”、“报价文件”等）。
        
        【必须遵守的标准修改示例】：
        如果原文要求将“商务文件”和“技术文件”合并，且有序号，你修改后的 `volumes` 数组应该严格长这样（包含 type="heading" 且保留原始序号）：
        [
            {{
                "volume_name": "商务技术文件",
                "items": [
                    {{"name": "2.1 商务文件", "is_required": false, "type": "heading"}},
                    {{"name": "(1) 投标声明书", "is_required": true, "type": "file"}},
                    {{"name": "(2) 法定代表人授权委托书", "is_required": true, "type": "file"}},
                    {{"name": "2.2 技术文件", "is_required": false, "type": "heading"}},
                    {{"name": "(1) 服务响应表", "is_required": true, "type": "file"}}
                ]
            }}
        ]
        
        请输出经过严格核验和修正后的完整 JSON，只输出 JSON，不要任何多余字符。
        
        招标文件原文片段：
        {text}
        """
        res3 = await client.chat.completions.create(
            model=config.model,
            messages=[{"role": "user", "content": prompt3}],
            temperature=0.0,
            stream=True
        )
        content3 = ""
        async for chunk in res3:
            if chunk.choices and chunk.choices[0].delta.content:
                text_chunk = chunk.choices[0].delta.content
                content3 += text_chunk
                yield json.dumps({"status": "chunk3", "text": text_chunk}) + "\n"
                
        cleaned_content3 = clean_json_text(content3)
        base_json = json.loads(cleaned_content3)
        
        yield json.dumps({"status": "agent2", "message": "Agent 2: 正在二次阅读原文，为各个分册文件寻找并匹配模板..."}) + "\n"
        
        prompt2 = f"""
        你是一个文本匹配与定位专家。
        这是之前提取出的标书结构JSON：
        {json.dumps(base_json, ensure_ascii=False)}
        
        【任务】：招标文件原文的后半部分通常有“响应文件格式”或“附件模板”章节。请遍历 JSON 中 volumes 里的所有 items。
        如果某个 item（比如各种承诺函、声明函、偏离表、报价表、业绩表等）在原文中附带了**具体的模板、表格或填写框架**，请**提取该模板在原文中的确切起始标题或特征词**（例如："附件一：法定代表人授权委托书" 或 "（7）类似成功案例的业绩"）。
        
        **极度重要指令**：
        1. 即使原文标有“格式自拟”、“格式可自行调整”或要求提供“复印件”，**只要原文下面紧跟着画了一个表格或提供了一个填写的框架**，就提取它的特征词作为 `template_text`。
        - **注意**：提取的模板特征词必须是真正的模板或附件在文档结尾处独立成页的真实模板标题（例如：'附件一：投标声明书'，或'（7）类似成功案例的业绩证明材料'）。**绝不要**被正文要求中的指导语（如'内容见投标声明书'）所蒙骗！
        2. 如果确实没有任何专门的表格或填写框架（纯粹只要一份复印件或自由编写，没有提供格式），请果断返回 null，绝不要摘抄正文的说明语句凑数！
        
        填入该 item 的 `template_text` 字段。
        请严格以 JSON 格式输出更新后的完整 JSON，不要包含多余的前言后记。
        
        招标文件原文片段：
        {text}
        """
        
        target_model = config.model_flash if config.model_flash else config.model
        res2 = await client.chat.completions.create(
            model=target_model,
            messages=[{"role": "user", "content": prompt2}],
            temperature=0.0,
            stream=True
        )
        content2 = ""
        async for chunk in res2:
            if chunk.choices and chunk.choices[0].delta.content:
                text_chunk = chunk.choices[0].delta.content
                content2 += text_chunk
                yield json.dumps({"status": "chunk2", "text": text_chunk}) + "\n"
                
        cleaned_content2 = clean_json_text(content2)
        final_json = json.loads(cleaned_content2)
        yield json.dumps({"status": "done", "data": final_json}) + "\n"
        
    except Exception as e:
        print(f"LLM API Stream Error: {e}")
        yield json.dumps({"status": "error", "message": str(e)}) + "\n"
