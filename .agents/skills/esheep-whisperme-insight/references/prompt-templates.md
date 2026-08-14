# Prompt Template Library - esheep-whisperme-insight

This document serves as the prompt template library for the **esheep-whisperme-insight** Skill. It provides standard prompt templates and guard prompts extracted from the whisperMe core project for generating structured podcast, audio, and video content analysis reports.

---

## 1. Deep Analysis Template (深度分析)

This is the primary prompt template for generating comprehensive podcast value analysis reports, extracted from whisperMe's `prompt_manager.py`.

```text
请根据下面提供的播客数据，生成一份深度【播客价值分析报告】。

核心防伪守则：
1. 所有结论必须100%基于转录文本，严禁臆测。
2. 未提及的内容必须如实标注"未讨论"。
3. 引用必须指向具体发言人和原话。

{{TRANSCRIPT_DATA}}

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

## 6. 知识图谱与关联索引
- **关键概念**：播客中出现的核心概念或术语（附简要解释）。
- **概念关联**：这些概念之间的关系。
- **延伸阅读**：基于讨论内容推荐的进一步学习方向。

## 7. 提及引用与资源索引
- **金句摘录**：2-5 句最有洞察力的原话。
- **书籍/文章**：提到的具体书名或文章。
- **影视作品**：提到的电影、纪录片。
- **工具/产品**：提到的软件、平台、App。
- **人物**：提到的公众人物。
- **关键数据/事实**：具体数字、统计。

## 8. 事实一致性与局限性声明
播客简介中提到但转录中未展开的内容（若有则列出，若无则说明一致）。
```

---

## 2. Speaker Guard Prompt (单发言人防幻觉约束)

When the transcript has no speaker differentiation (e.g. all speech tags are identical or unknown), prepend this guard prompt to prevent hallucinations:

```text
[🚨 极重要防错声明]
检测到本期播客的转录文本中没有区分发言人（所有发言标记均为相同角色或未知）。
请务必遵守以下刚性约束：
1. 严禁尝试在总结或分析中臆测、脑补出任何具体的发言人姓名、嘉宾画像或主持人角色。
2. 在原计划输出"发言人画像与立场分析"章节时，请将其重命名为"议题正反核心视点交锋与视角分析"。
3. 纯粹从播客讨论的议题语义逻辑出发，提炼不同观点的正反论据、共识与分歧。
```

---

## 3. Template Adaptation Notes

- **Placeholder Replacement**: The `{{TRANSCRIPT_DATA}}` placeholder must be replaced with the actual transcript text when the Agent injects it into prompt execution.
- **Content Adaptation**: For non-podcast media types (such as meetings, lectures, panel discussions, or interviews), the Agent should naturally adapt section headings and terminology while maintaining the core structure.
- **Anti-Hallucination Guardrails**: The core anti-hallucination rules (100% text-based conclusions, marking unmentioned items as "未讨论", exact citations) are critical and must strictly be preserved across all executions.
- **Long Transcript Handling**: For very long transcripts (>50,000 characters), the Agent should process and summarize the transcript in chunks first, then synthesize the overall report according to this template.
