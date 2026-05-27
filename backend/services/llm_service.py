from openai import AsyncOpenAI
import json
from models.schemas import AIConfig, AnalysisResult

async def extract_bidding_info(text: str, config: AIConfig) -> dict:
    client = AsyncOpenAI(
        api_key=config.apiKey,
        base_url=config.baseUrl
    )
    
    # Agent 1: 结构与风险识别
    prompt1 = f"""
    你是一个专业的招投标分析专家。请仔细阅读以下招标文件片段，进行初步拆解。
    【任务1】：提取项目信息(name, number, budget)。
    【任务2】：提取致命风险(fatalFlaws)，即所有带有 "★", "▲", "必须提供", "实质性响应" 等字眼的废标条款。
    【任务3】：提取投标文件分册结构(volumes)。政企标书通常分为多个分册（如：资格文件、商务与技术文件、报价文件）。请严格按照招标文件要求的结构，列举每个分册的名称(volume_name)，以及该分册下需要包含的文件材料清单(items, 包含name和is_required)。

    请严格以 JSON 格式输出：
    {{
        "projectInfo": {{"name": "", "number": "", "budget": ""}},
        "fatalFlaws": [""],
        "volumes": [
            {{
                "volume_name": "第一分册：资格证明文件",
                "items": [
                    {{"name": "法定代表人授权书", "is_required": true}},
                    {{"name": "无串通竞标行为的承诺函", "is_required": true}}
                ]
            }}
        ]
    }}
    
    招标文件内容片段：
    {text[:20000]} 
    """
    
    try:
        print("Running Agent 1 (Structure & Risks)...")
        res1 = await client.chat.completions.create(
            model=config.model,
            messages=[{"role": "user", "content": prompt1}],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        base_json = json.loads(res1.choices[0].message.content)
        
        # Agent 2: 模板格式抽取
        prompt2 = f"""
        你是一个文本匹配与抽取专家。
        这是之前提取出的标书结构JSON：
        {json.dumps(base_json, ensure_ascii=False)}
        
        【任务】：招标文件原文的后半部分通常有“响应文件格式”或“模板”章节。请遍历 JSON 中 volumes 里的所有 items。如果某个 item（比如各种承诺函、声明函、偏离表）在原文中有具体的模板内容或格式要求，请将原文的模板文字原样提取出来，填入该 item 的 `template_text` 字段。如果没有模板，或者只是要求提供复印件（如营业执照），则保留为 null。
        
        请返回更新后完整的 JSON（保持原有结构，仅扩充 template_text）。
        
        招标文件原文片段：
        {text[:20000]}
        """
        print("Running Agent 2 (Template Extraction)...")
        res2 = await client.chat.completions.create(
            model=config.model,
            messages=[{"role": "user", "content": prompt2}],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        final_json = json.loads(res2.choices[0].message.content)
        return final_json
        
    except Exception as e:
        print(f"LLM API Error: {e}")
        return {
            "projectInfo": {"name": "未知", "number": "未知", "budget": "未知"},
            "fatalFlaws": [f"API调用失败: {str(e)}"],
            "volumes": []
        }
