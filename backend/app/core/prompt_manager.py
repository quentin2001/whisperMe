import json
from pathlib import Path
from app.config import PROJECT_DIR

PROMPT_FILE = PROJECT_DIR / "prompt.json"

DEFAULT_BASE_PROMPT = """请根据下面提供的【播客单集 Shownotes】、【听众热门评论】和【播客对话转录文本】，生成一份详尽、结构清晰的【播客价值总结分析报告】。

核心防伪守则（必须严格遵守，否则视为失败）：
1. 严禁臆测发散：所有分析结论、嘉宾立场、议题提炼及评级，必须100%基于下方提供的事实源数据。严禁使用你自身固有知识库中的外部信息去扩展或脑补播客中未提及的事情或技术细节。
2. 拒绝幻觉，空值如实报告：如果播客转录本中完全没有提及某人、某事或某个观点，哪怕该词出现在了 Shownotes 简介里，也绝对不得在总结中编造其对话内容，必须如实标注转录文本中未讨论或未提及。
3. 精准引用：提炼核心观点和发言人立场时，必须直接引用（或高度提炼）转录文本中的原话、金句或提及的具体事例，并指明是谁说的。
4. 客观呈现听众反馈：舆情分析部分必须完全基于热门听众评论列表中的实际留言，不得凭空编造听众情感走向。"""

DEFAULT_ACTION_PROMPT = """请以 Markdown 格式输出以下结构的内容（严禁输出结构外的发散废话，直接输出报告正文）：

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

def load_prompt() -> dict:
    """Load the prompt JSON file and return as a dictionary. Creates it if missing."""
    default_data = {
        "base_prompt": DEFAULT_BASE_PROMPT,
        "action_prompt": DEFAULT_ACTION_PROMPT
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
        modified = False
        if "base_prompt" not in data or not data["base_prompt"]:
            data["base_prompt"] = DEFAULT_BASE_PROMPT
            modified = True
        if "action_prompt" not in data or not data["action_prompt"]:
            data["action_prompt"] = DEFAULT_ACTION_PROMPT
            modified = True
        if modified:
            with open(PROMPT_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        return data
    except Exception:
        return default_data

def save_prompt(data: dict) -> None:
    """Save the prompt dictionary to the JSON file."""
    with open(PROMPT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

