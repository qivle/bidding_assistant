import re
import httpx
from openai import AsyncOpenAI
import json
from models.schemas import AIConfig, AnalysisResult

def clean_json_text(text: str) -> str:
    # 移除 markdown 代码块包裹 (如 ```json ... ``` 或 ``` ... ```)
    text = text.strip()
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text

async def extract_bidding_info(text: str, config: AIConfig) -> dict:
    # 自动修正 DeepSeek 的 baseUrl，防止用户漏填 /v1
    base_url = config.baseUrl.strip() if config.baseUrl else ""
    if "api.deepseek.com" in base_url and not base_url.endswith("/v1") and not base_url.endswith("/v1/"):
        base_url = base_url.rstrip("/") + "/v1"
        
    # 使用自定义 httpx 客户端，禁用 SSL 证书验证并忽略系统/注册表代理环境（防止 Windows 代理残留导致 Connection error）
    client = AsyncOpenAI(
        api_key=config.apiKey,
        base_url=base_url,
        http_client=httpx.AsyncClient(verify=False, trust_env=False)
    )
    
    async def call_llm_with_fallback(prompt: str) -> str:
        # 尝试带 response_format 的调用（JSON Mode）
        try:
            res = await client.chat.completions.create(
                model=config.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            return res.choices[0].message.content
        except Exception as e:
            # 如果是 BadRequestError 或者参数错误，尝试不带 response_format 的常规调用
            print(f"JSON mode failed or API error, retrying without JSON mode: {e}")
            try:
                res = await client.chat.completions.create(
                    model=config.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                )
                return res.choices[0].message.content
            except Exception as e2:
                # 依然失败则抛出，让外层捕获
                print(f"Retry without JSON mode also failed: {e2}")
                raise e2
    
    # Agent 1: 结构与风险识别
    prompt1 = f"""
    你是一个专业的招投标分析专家。请仔细阅读以下招标文件片段，进行初步拆解。
    【任务1】：提取项目信息(name, number, budget)。
    【任务2】：提取致命风险(fatalFlaws)。请找到所有带有 "★", "▲", "必须提供", "实质性响应" 等字眼的废标条款。
    **重要指令**：
    - 请将废标项进行归类整理，例如分为“商务要求”、“技术参数要求”、“特定资质要求”等大类。
    - 请根据文本中我注入的 `---[第X页]---` 或 `---[文档位置: 段落 X]---` 标记，尽可能准确地写出该条款所在的页码或段落位置。如果找不到，可写“未知”。
    - **切记**：不要将普通的常规资质文件（如营业执照复印件、法人身份证等）列入此风险雷达列表中，除非它带有非常规的实质性约束条件。那些会在投标文件分册中直接提供的常规材料无需在风险雷达中重复罗列。
    
    【任务3】：提取投标文件分册结构(volumes)。政企标书通常分为多个分册（如：资格文件、商务与技术文件、报价文件）。请严格按照招标文件要求的结构，列举每个分册的名称(volume_name)，以及该分册下需要包含的文件材料清单(items, 包含name and is_required)。

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
                "volume_name": "第一分册：资格证明文件",
                "items": [
                    {{"name": "法定代表人授权书", "is_required": true}},
                    {{"name": "营业执照正本复印件", "is_required": true}}
                ]
            }}
        ]
    }}
    
    招标文件内容片段：
    {text} 
    """
    
    try:
        print("Running Agent 1 (Structure & Risks)...")
        content1 = await call_llm_with_fallback(prompt1)
        cleaned_content1 = clean_json_text(content1)
        base_json = json.loads(cleaned_content1)
        
        # Agent 2: 模板特征词抽取
        prompt2 = f"""
        你是一个文本匹配与定位专家。
        这是之前提取出的标书结构JSON：
        {json.dumps(base_json, ensure_ascii=False)}
        
        【任务】：招标文件原文的后半部分通常有“响应文件格式”或“附件模板”章节。请遍历 JSON 中 volumes 里的所有 items。
        如果某个 item（比如各种承诺函、声明函、偏离表、报价表）在原文中有具体的模板格式，请**不要**提取整个模板的内容，而是**提取该模板在原文中的确切起始标题或特征词**（例如："附件一：法定代表人授权委托书（格式）" 或 "五、无重大违法记录声明"）。
        我们将使用这个特征词去原始文档中精准切割底层排版。
        填入该 item 的 `template_text` 字段。如果没有模板，或者只是要求提供复印件（如营业执照），则保留为 null。
        
        请返回更新后完整的 JSON（保持原有结构，仅将 template_text 字段填充为特征词）。
        
        请严格以 JSON 格式输出，不要包含任何多余的前言或后记。
        
        招标文件原文片段：
        {text}
        """
        print("Running Agent 2 (Template Marker Extraction)...")
        content2 = await call_llm_with_fallback(prompt2)
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

