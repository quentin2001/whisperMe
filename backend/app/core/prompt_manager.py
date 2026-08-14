import json
from pathlib import Path
from app.config import PROJECT_DIR, DATA_DIR

PROMPT_FILE = DATA_DIR / "prompt.json"

DEFAULT_PROMPT = """请根据下方提供的播客事实数据（包含单集元数据、听众评论及完整转录文本），生成一份兼具深度与可读性的【播客价值总结分析报告】。

🛡️ 核心防伪与事实基准原则（必须绝对遵循）：
1. 100% 事实锚定：所有总结、论点、人物观点与评级必须完全基于下方提供的事实源数据，严禁利用模型自身外部知识库无中生有或补充未提及的情节。
2. 拒绝幻觉与空值声明：若转录文本未讨论某话题或某人物（哪怕出现在了 Shownotes 简介中），必须如实声明未在正文中展开，严禁脑补对话。
3. 精准引用原声：提炼核心观点时，必须指明是谁表达的，并尽可能结合原话金句或具体案例论据。

{{PODCAST_DATA}}

请直接以清晰易读的 Markdown 格式输出以下结构报告（严禁输出结构外的发散废话）：

## 1. 播客全景与价值评级
- **核心主旨**：用 2-3 句话直击本质地概括本期播客讨论的核心母题与关键结论（拒绝空洞套话）。
- **目标受众**：基于讨论的认知门槛与专业维度，明确最适合收听的人群标签（如：创业者、职场新人、AI从业者等）。
- **含金量评级与判定理由**：综合「信息密度」、「观点独特性」、「实用落地度」三个维度给出客观评级（A+ / A / B / C / D）并附简要理由。
- **收听建议**：推荐指数（强烈推荐完整收听 / 看本总结即可 / 建议避坑）。

## 2. 核心议题与深度论点拆解
梳理 3-5 个播客中实际深入探讨的核心议题。对每个议题按以下格式提炼：
- **议题名称**
- **核心论点**：提炼该议题下的核心认知增量、对话共识或关键分歧。
- **论据支撑与原声金句**：引用转录中的具体案例、论证事实或发言人代表性原话（标注发言人）。

## 3. 发言人立场与观点博弈
- **角色画像与立场**：梳理各发言人（主持人/嘉宾）的核心视角、论述风格与价值倾向（仅基于单集言论表现，不带入场外预设）。
- **互动碰撞与共识边界**：分析嘉宾之间是互补共鸣还是存在观点的交锋摩擦，最终在哪些层面达成了共识或保留了分歧。

## 4. 高光金句与关键引用索引
（仅提取转录中明确出现的原声与资源，无则注明“无”）
- **💎 高光金句**：精选 3-5 句极具洞察力、发人深省或表达精妙的原话（附发言人）。
- **📚 提及资源**：列出对话中提到的具体书籍、论文、工具软件、影视作品或公众人物。
- **📊 关键数据/案例**：对话中引用的重要统计数字、实验结论或商业案例。

## 5. 听众舆情与社会共鸣
- **听众高频反馈**：基于评论列表提取听众最强烈的认同点与代表性质疑（无评论则注明“暂无评论数据”）。
- **情感极性与共鸣点**：分析讨论激发的社会情绪共鸣与潜在争议点。

## 6. 事实一致性与局限性声明
对比 Shownotes 简介与实际对话转录，说明是否存在简介中提及但正文未展开讨论的落差内容。"""

# 预设模板库
BUILTIN_TEMPLATES = {
    "standard": {
        "name": "标准分析",
        "name_en": "Standard Analysis",
        "description": "均衡全景：全景速览、多议题拆解、发言人博弈、金句索引与舆情分析",
        "description_en": "Balanced overview: full summary, viewpoint breakdown, speaker dynamics, quotes, and sentiments",
        "prompt": DEFAULT_PROMPT,
    },
    "concise": {
        "name": "精简速览",
        "name_en": "Concise Brief",
        "description": "1分钟电梯速读：3大核心洞见、高光金句、行动建议与收听决策",
        "description_en": "1-min quick brief: 3 key insights, top quotes, action guides, and decision rating",
        "prompt": """请根据下方提供的播客事实数据，生成一份极致提炼、适合 1 分钟快速阅读的【播客精简速览】。

🛡️ 核心原则：内容 100% 忠于转录文本，只保留高密度干货，去除一切套话与废话。

{{PODCAST_DATA}}

请直接以清晰干练的 Markdown 格式输出：

## ⚡ 1分钟核心速览
用 2 句话直截了当地告诉读者：这期播客在什么背景下探讨了什么核心问题，最终得出了什么关键结论。

## 🎯 3大核心洞见与认知增量
提炼本期播客最有价值、最具启发性的 3 个核心观点（每个要点包含【观点提炼】+【1句论据/原话支撑】）：
1. **[洞见一]**：...
2. **[洞见二]**：...
3. **[洞见三]**：...

## 💎 高光原声金句
精选 2-3 句转录中最具穿透力、值得收藏的发言人原话（注明发言人）。

## 🚀 行动指南与落地建议
基于播客探讨的内容，提炼 3 条听众可以立即实践、思考或进一步探索的具体行动方向。

## ⭐ 综合评级与收听决策
- **评级**：A+ / A / B / C / D
- **一句话决策**：谁必须去听完整音频？谁只看本速览就足够了？""",
    },
    "deep": {
        "name": "深度研报",
        "name_en": "Deep Analysis",
        "description": "智库研报级：底层假设、论证逻辑链、认知博弈、批判性盲区与概念图谱",
        "description_en": "Deep intelligence: underlying assumptions, argument chains, critical blindspots, and concept graph",
        "prompt": """请根据下方提供的播客事实数据（包含单集元数据、听众评论及完整转录文本），以专业智库/行业深度研报的标准，生成一份系统化、深度解构的【播客深度价值研报】。

🛡️ 核心防伪与事实基准原则（必须绝对遵循）：
1. 严格基于事实源数据，严禁无中生有。
2. 挖掘论述背后的底层逻辑链条，但绝不脑补转录文本中未出现的事实。
3. 准确归属发言人，保留原始论述语境。

{{PODCAST_DATA}}

请直接以结构严谨的 Markdown 格式输出以下报告：

## 一、 深度摘要与认知坐标
- **核心主旨与时代背景**：深入概括本期播客讨论的本质母题、现实诱因与核心结论。
- **认知价值与含金量评级**：从「底层信息密度」、「逻辑自洽性」、「认知独特性」三个维度深度评级（A+ / A / B / C / D）并阐述详实判定依据。
- **推荐人群与知识位阶**：精准描摹适合深度研读的目标人群及其前置认知要求。

## 二、 核心议题全景解构与论证链
对播客中展开的 3-5 个核心议题进行深度纵向解构，每个议题包含：
- **议题名称与核心命题**
- **底层假设与立论前提**：发言人是基于哪些显性或隐性假设展开推理的？
- **核心论证逻辑链**：梳理从前提到论据、再到结论的完整因果逻辑推导过程。
- **关键事实与案例证据**：对话中引用的具体数据、商业案例或一手经验（包含发言人原话引用）。

## 三、 多维立场剖析与思想碰撞
- **发言人视角与认知底色**：深入剖析各参与者（主持人/嘉宾）的思考框架、价值偏好与认知盲点（仅基于单集言论表现）。
- **共识边界与隐性冲突**：梳理对话过程中观点的交锋时刻，揭示各方在哪些维度达成了深度共识，在哪些深层逻辑上保留了分歧。
- **互动张力与讨论质感**：评估对话的开放度与思辨深度。

## 四、 批判性思考与潜在盲区
- **未被讨论的对立视角**：播客论述中是否存在被忽视的对立面、反直觉反例或未展开讨论的外部变量？
- **逻辑局限与适用边界**：播客中提出的方案或结论，在哪些特定条件或场景下可能会失效？
- **前沿延伸与未来争议**：该议题在未来可能引发的进一步讨论与发展趋势。

## 五、 概念图谱与延伸知识库
- **核心概念/专业术语**：提取对话中出现的关键概念，结合播客语境给出清晰释义。
- **提及资源完整索引**：系统整理对话中提及的书籍、学术论文、软件工具、影视作品及公众人物。
- **延伸探索路径**：基于本期讨论的核心脉络，推荐值得进一步阅读或调研的知识方向。

## 六、 高价值原声金句库
精选 4-6 句兼具思想深度、表达力度与启示意义的高光原话，附带说话人及其所处语境。

## 七、 事实一致性与局限性声明
对比节目 Shownotes 简介与实际转录内容，逐条说明是否存在简介中提及但实际未展开讨论的落差内容。""",
    },
}

# 兼容旧格式：合并 base_prompt + action_prompt 为单个 prompt
def _migrate_old_format(data: dict) -> dict:
    """将旧的 base_prompt + action_prompt 格式合并为单个 prompt 字段。"""
    if "prompt" in data and data["prompt"]:
        return data
    if "base_prompt" in data or "action_prompt" in data:
        base = data.get("base_prompt", "")
        action = data.get("action_prompt", "")
        # 在 base 和 action 之间插入占位符
        merged = f"{base}\n\n{{{{PODCAST_DATA}}}}\n\n{action}"
        data["prompt"] = merged
        # 保留旧字段以备回退，但标记已迁移
        data["_migrated"] = True
    return data


def load_prompt() -> dict:
    """Load the prompt JSON file. Returns dict with 'prompt' key (and templates info)."""
    default_data = {
        "prompt": DEFAULT_PROMPT,
        "default_template_id": "standard",
        "template_order": ["standard", "concise", "deep"]
    }

    if not PROMPT_FILE.exists():
        try:
            with open(PROMPT_FILE, "w", encoding="utf-8") as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)
            return default_data
        except Exception:
            return default_data

    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        data = _migrate_old_format(data)

        if "prompt" not in data or not data["prompt"]:
            data["prompt"] = DEFAULT_PROMPT

        if "default_template_id" not in data:
            data["default_template_id"] = "standard"

        if "template_order" not in data:
            data["template_order"] = ["standard", "concise", "deep"]

        # 如果做了迁移，写回文件
        if data.get("_migrated"):
            data.pop("_migrated", None)
            with open(PROMPT_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        return data
    except Exception:
        return default_data


def save_prompt(data: dict) -> None:
    """Save the prompt dictionary to the JSON file, merging with existing keys."""
    existing = load_prompt()
    if "custom_templates" not in data and "custom_templates" in existing:
        data["custom_templates"] = existing["custom_templates"]
    if "default_template_id" not in data and "default_template_id" in existing:
        data["default_template_id"] = existing["default_template_id"]
    if "template_order" not in data and "template_order" in existing:
        data["template_order"] = existing["template_order"]
        
    with open(PROMPT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_template_order(order: list) -> None:
    """保存模板的自定义顺序。"""
    data = load_prompt()
    data["template_order"] = order
    save_prompt(data)


def get_templates() -> dict:
    """返回所有模板字典（内置 + 自定义），并按照自定义顺序排序，附带默认标识。"""
    data = load_prompt()
    custom = data.get("custom_templates", {})
    default_id = data.get("default_template_id", "standard")
    order = data.get("template_order", [])
    
    all_tpls = {}
    for tid, t in BUILTIN_TEMPLATES.items():
        all_tpls[tid] = {
            "name": t["name"],
            "name_en": t["name_en"],
            "description": t["description"],
            "description_en": t["description_en"],
            "is_builtin": True,
            "is_default": tid == default_id
        }
    for tid, t in custom.items():
        all_tpls[tid] = {
            "name": t.get("name", "Custom"),
            "name_en": t.get("name_en", t.get("name", "Custom")),
            "description": t.get("description", ""),
            "description_en": t.get("description_en", t.get("description", "")),
            "is_builtin": False,
            "is_default": tid == default_id
        }
        
    ordered_templates = {}
    # 按照 order 排序构建
    for tid in order:
        if tid in all_tpls:
            ordered_templates[tid] = all_tpls[tid]
            
    # 追加剩余未在 order 里的 templates
    for tid, t in all_tpls.items():
        if tid not in ordered_templates:
            ordered_templates[tid] = t
            
    return ordered_templates


def get_template_prompt(template_id: str) -> str | None:
    """返回指定模板的完整 prompt 文本，不存在则返回 None。"""
    data = load_prompt()
    custom = data.get("custom_templates", {})
    
    # 1. 优先在用户自定义模板中查找
    if template_id in custom:
        return custom[template_id].get("prompt")
    
    # 2. 如果请求 standard 模板，优先返回用户通过 CLI/设置页保存的定制顶级 prompt（若有）
    if template_id == "standard":
        if data.get("prompt") and data.get("prompt").strip():
            return data["prompt"]
        return BUILTIN_TEMPLATES["standard"]["prompt"]
        
    # 3. 其他内置模板
    if template_id in BUILTIN_TEMPLATES:
        return BUILTIN_TEMPLATES[template_id]["prompt"]
        
    # 4. 不存在则返回 None
    return None


def save_custom_template(template_id: str, name: str, description: str, prompt: str) -> str:
    """保存或创建自定义模板。"""
    import time
    if template_id in BUILTIN_TEMPLATES:
        raise ValueError("Cannot overwrite builtin templates")
    data = load_prompt()
    if "custom_templates" not in data:
        data["custom_templates"] = {}
    
    tid = template_id if template_id else f"custom_{int(time.time() * 1000)}"
    data["custom_templates"][tid] = {
        "id": tid,
        "name": name,
        "name_en": name,
        "description": description,
        "description_en": description,
        "prompt": prompt
    }
    save_prompt(data)
    return tid


def delete_custom_template(template_id: str) -> bool:
    """删除指定的自定义模板。"""
    if template_id in BUILTIN_TEMPLATES:
        return False
    data = load_prompt()
    if "custom_templates" in data and template_id in data["custom_templates"]:
        del data["custom_templates"][template_id]
        save_prompt(data)
        return True
    return False
