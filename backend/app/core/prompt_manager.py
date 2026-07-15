import json
from pathlib import Path
from app.config import PROJECT_DIR, DATA_DIR

PROMPT_FILE = DATA_DIR / "prompt.json"

DEFAULT_PROMPT = """请根据下面提供的播客数据，生成一份详尽、结构清晰的【播客价值总结分析报告】。

核心防伪守则（必须严格遵守，否则视为失败）：
1. 严禁臆测发散：所有分析结论、嘉宾立场、议题提炼及评级，必须100%基于下方提供的事实源数据。严禁使用你自身固有知识库中的外部信息去扩展或脑补播客中未提及的事情或技术细节。
2. 拒绝幻觉，空值如实报告：如果播客转录本中完全没有提及某人、某事或某个观点，哪怕该词出现在了 Shownotes 简介里，也绝对不得在总结中编造其对话内容，必须如实标注转录文本中未讨论或未提及。
3. 精准引用：提炼核心观点和发言人立场时，必须直接引用（或高度提炼）转录文本中的原话、金句或提及的具体事例，并指明是谁说的。
4. 客观呈现听众反馈：舆情分析部分必须完全基于热门听众评论列表中的实际留言，不得凭空编造听众情感走向。

{{PODCAST_DATA}}

请以 Markdown 格式输出以下结构的内容（严禁输出结构外的发散废话，直接输出报告正文）：

## 1. 播客概要与含金量评级
- **核心主旨**：用2-3句话精准总结这期播客实际讨论的核心主题（拒绝大话空话，紧扣转录事实）。
- **目标受众**：根据播客讨论内容的专业深度，说明适合哪些细分人群收听。
- **含金量评级与判定理由**：请给出评级（A+ / A / B / C / D 之一），并从内容信息密度、观点的独特性和知识实用度三个维度，基于转录中的干货多寡简述判定理由。
- **推荐等级**：是否值得花时间复听（值得去听 / 仅看总结即可 / 建议避坑）。

## 2. 核心观点与议题提炼
请梳理出播客实际讨论的3-5个核心议题。对每个议题：
- **议题名称**
- **核心论点**：结合不同人的发言总结其达成的共识或分歧。
- **关键论据/金句**：必须包含转录中发言人提到过的原话、金句或他们讲到的具体案例。

## 3. 发言人画像与立场分析
- **角色定位**：说明都有谁参与了说话，谁是主持人（Host），谁是嘉宾（Guest）。
- **立场与风格**：简述各位发言人的核心立场、讨论风格以及观点倾向，切忌根据发言人的名气脑补其背景，只分析其在此单集中的言论表现。
- **互动氛围**：他们之间的互动如何（比如是和谐互补，还是存在观点的交锋摩擦）。

## 4. 听众口碑与评论区舆情分析
- **听众主要反馈**：评论区大家最赞同的观点是什么？有没有提出不同的质疑？（必须从提供的评论列表中提取，无评论则写暂无评论数据）。
- **评论情感极性**：正向期待为主 / 中立探讨 / 存在争议偏见。
- **社会共鸣点**：这期播客勾起了听众什么共鸣或情绪。

## 5. 事实一致性与局限性声明
请在此处特别说明：本报告有哪些内容是简介（Shownotes）中提到但转录对话中实际并未展开讨论的？（若有，请逐一列出；若无，写 Shownotes 提及内容与实际转录文本一致）。

## 6. 提及引用与资源索引
请从转录文本中提取以下类别的提及项（仅提取转录中明确提到的，未提及则写"无"）：
- **金句摘录**：转录中发言人说过的有洞察力、发人深省或表达精辟的原话（2-5句），注明发言人。
- **书籍/文章**：提到的具体书名、论文或文章。
- **影视作品**：提到的电影、纪录片、剧集。
- **工具/产品**：提到的软件、平台、App 或技术工具。
- **人物**：提到的公众人物或历史人物（非播客参与者本身）。
- **关键数据/事实**：提到的具体数字、统计或可验证的事实。"""

# 预设模板库
BUILTIN_TEMPLATES = {
    "standard": {
        "name": "标准分析",
        "name_en": "Standard Analysis",
        "description": "6 节完整结构：概要、观点、发言人、舆情、一致性、引用",
        "description_en": "6-section full structure: summary, viewpoints, speakers, sentiment, consistency, quotes",
        "prompt": DEFAULT_PROMPT,
    },
    "concise": {
        "name": "精简速览",
        "name_en": "Concise Brief",
        "description": "只提取核心主旨、金句和行动建议，适合快速浏览",
        "description_en": "Extract core points, quotes, and action items only. Quick read.",
        "prompt": """请根据下面提供的播客数据，生成一份精简的【播客速览报告】。

核心规则：所有内容必须100%基于提供的转录文本，严禁编造。

{{PODCAST_DATA}}

请以 Markdown 格式输出：

## 核心主旨
用 2-3 句话总结这期播客在讨论什么。

## 关键金句
提取转录中 3-5 句最有价值的原话，注明发言人。

## 行动建议
根据播客内容，列出 3-5 条听众可以立即采取的行动或进一步探索的方向。

## 一句话评价
用一句话告诉朋友这期值不值得听。""",
    },
    "deep": {
        "name": "深度分析",
        "name_en": "Deep Analysis",
        "description": "在标准基础上增加论证逻辑链、反方观点、知识图谱",
        "description_en": "Extended with argument chains, counterpoints, and knowledge graph",
        "prompt": """请根据下面提供的播客数据，生成一份深度【播客价值分析报告】。

核心防伪守则：
1. 所有结论必须100%基于转录文本，严禁臆测。
2. 未提及的内容必须如实标注"未讨论"。
3. 引用必须指向具体发言人和原话。

{{PODCAST_DATA}}

请以 Markdown 格式输出：

## 1. 播客概要与含金量评级
- **核心主旨**：精准总结核心主题。
- **目标受众**：适合哪些细分人群。
- **含金量评级**：A+ / A / B / C / D，从信息密度、观点独特性、知识实用度三个维度说明理由。
- **推荐等级**：值得去听 / 仅看总结即可 / 建议避坑。

## 2. 核心观点与议题提炼
梳理 3-5 个核心议题，每个包含：议题名称、核心论点、关键论据/金句。

## 3. 论证逻辑链分析
对每个核心议题，梳理发言人的完整论证逻辑：
- **前提假设**：他们基于什么假设在讨论？
- **推理过程**：从前提到结论的逻辑链条是什么？
- **隐含前提**：有哪些未明说但暗含的前提条件？
- **逻辑漏洞**：论证中是否存在跳跃、以偏概全或循环论证？

## 4. 反方观点与争议空间
- **未被讨论的反面**：播客中只呈现了一面的观点，另一面是什么？
- **潜在争议点**：哪些结论可能引发不同意见？
- **缺失视角**：如果请一个持相反立场的人来评论，他会怎么说？

## 5. 发言人画像与立场分析
- **角色定位**：主持人 vs 嘉宾。
- **立场与风格**：核心立场、讨论风格、观点倾向。
- **互动氛围**：和谐互补还是观点交锋。

## 6. 听众口碑与舆情分析
- **主要反馈**：评论区最赞同的观点和质疑。
- **情感极性**：正向 / 中立 / 争议。
- **社会共鸣点**：勾起了什么共鸣或情绪。

## 7. 知识图谱与关联索引
- **关键概念**：播客中出现的核心概念或术语（附简要解释）。
- **概念关联**：这些概念之间的关系。
- **延伸阅读**：基于讨论内容推荐的进一步学习方向。

## 8. 提及引用与资源索引
- **金句摘录**：2-5 句最有洞察力的原话。
- **书籍/文章**：提到的具体书名或文章。
- **影视作品**：提到的电影、纪录片。
- **工具/产品**：提到的软件、平台、App。
- **人物**：提到的公众人物。
- **关键数据/事实**：具体数字、统计。

## 9. 事实一致性与局限性声明
Shownotes 中提到但转录中未展开的内容（若有则列出，若无则说明一致）。""",
    },
    "custom": {
        "name": "自定义/空白",
        "name_en": "Custom / Blank",
        "description": "完全空白的模板，由您自由书写提示词",
        "description_en": "A completely blank template for you to write your own custom prompt",
        "prompt": """{{PODCAST_DATA}}
 
请根据以上播客转录内容，生成总结：""",
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
    default_data = {"prompt": DEFAULT_PROMPT}

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

        # 如果做了迁移，写回文件
        if data.get("_migrated"):
            data.pop("_migrated", None)
            with open(PROMPT_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        return data
    except Exception:
        return default_data


def save_prompt(data: dict) -> None:
    """Save the prompt dictionary to the JSON file."""
    with open(PROMPT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_templates() -> dict:
    """返回所有模板字典（内置 + 自定义）。"""
    data = load_prompt()
    custom = data.get("custom_templates", {})
    
    templates = {}
    for tid, t in BUILTIN_TEMPLATES.items():
        templates[tid] = {
            "name": t["name"],
            "name_en": t["name_en"],
            "description": t["description"],
            "description_en": t["description_en"],
            "is_builtin": True
        }
    for tid, t in custom.items():
        templates[tid] = {
            "name": t.get("name", "Custom"),
            "name_en": t.get("name_en", t.get("name", "Custom")),
            "description": t.get("description", ""),
            "description_en": t.get("description_en", t.get("description", "")),
            "is_builtin": False
        }
    return templates


def get_template_prompt(template_id: str) -> str | None:
    """返回指定模板的完整 prompt 文本，不存在则返回 None。"""
    if template_id in BUILTIN_TEMPLATES:
        return BUILTIN_TEMPLATES[template_id]["prompt"]
    data = load_prompt()
    custom = data.get("custom_templates", {})
    if template_id in custom:
        return custom[template_id]["prompt"]
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
