import json
import uuid
import random
import threading
from datetime import datetime, timedelta
from app.core.llm_utils import call_llm
from app.config import config

class BoardService:
    @staticmethod
    def generate_card_content(quote: str):
        prompt = f"""你是一个知识内化与卡片记忆提取专家。
请根据下面的播客转录原话，提取出一个闪光标题（Spark Title）和为何重要（Why It Matters）的解释。

原话内容：
「{quote}」

要求：
1. 闪光标题：精炼、醒目、深刻，能一针见血指出这段话的核心观点，不超过 15 字。
2. 为何重要：用一两句话解释该观点的含金量、底层逻辑或启发性意义，语气理性中肯，不超过 60 字。
3. 必须以 JSON 格式输出，包含 "spark_title" 和 "why_it_matters" 两个字段。
4. 不要包含 ```json 或 ``` 格式块，只输出纯 JSON 字符串，不要有任何其他内容。"""

        try:
            response_str = call_llm(prompt, label="Card提炼")
            cleaned_str = response_str.strip()
            if cleaned_str.startswith("```json"):
                cleaned_str = cleaned_str[7:]
            if cleaned_str.startswith("```"):
                cleaned_str = cleaned_str[3:]
            if cleaned_str.endswith("```"):
                cleaned_str = cleaned_str[:-3]
            cleaned_str = cleaned_str.strip()
            
            parsed = json.loads(cleaned_str)
            spark_title = parsed.get("spark_title", "未命名观点").strip()
            why_it_matters = parsed.get("why_it_matters", "原话具有深刻启发意义。").strip()
        except Exception as e:
            from app.core import logger
            logger.info(f"⚠️ [LOG ERROR] LLM 卡片提炼失败: {e}")
            spark_title = quote[:15] + "..." if len(quote) > 15 else quote
            why_it_matters = "由于大模型连接失败或解析异常，该卡片以默认模式生成。原话非常关键，值得反复记忆复习。"

        return spark_title, why_it_matters

    @staticmethod
    def calculate_next_review(efactor: float, interval: int, direction: str):
        today = datetime.today()
        if direction == "left":
            new_status = "active"
            if interval == 1:
                new_interval = 6
            elif interval == 6:
                new_interval = 12
            else:
                new_interval = int(round(interval * efactor))
                
            new_efactor = efactor
            next_date = (today + timedelta(days=new_interval)).strftime("%Y-%m-%d")
        else:
            new_status = "warning"
            new_interval = 1
            new_efactor = max(1.3, efactor - 0.2)
            next_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")
            
        return new_status, new_interval, new_efactor, next_date

    @staticmethod
    def send_forget_warning_webhook(card, podcast_title, podcast_name):
        webhook_url = config.get("webhook_url", "").strip()
        if not webhook_url:
            return
            
        import httpx
        source_link = f"http://localhost:9173/?task_id={card['podcast_id']}&paragraph_id={card['paragraph_id']}"
        payload = {
            "msg_type": "text",
            "text": {
                "content": f"🧠 【知识遗忘唤醒警告】\n闪光点: {card['spark_title']}\n原话: {card['quote']}\nAI 提炼: {card['why_it_matters']}\n播客来源: {podcast_name} - 《{podcast_title}》\n🧭 溯源链接: {source_link}"
            }
        }
        def send_webhook_async(url, payload):
            try:
                with httpx.Client(timeout=10.0, trust_env=False, verify=False) as client:
                    client.post(url, json=payload)
                    from app.core import logger
                    logger.info("🔔 [LOG] Webhook notification sent successfully.")
            except Exception as wh_err:
                from app.core import logger
                logger.info(f"⚠️ [LOG WARNING] Webhook notification failed: {wh_err}")
        
        threading.Thread(target=send_webhook_async, args=(webhook_url, payload), daemon=True).start()

    @staticmethod
    def synthesize_cards(card_a, card_b, my_synthesis: str):
        llm_prompt = f"""你是一个高级哲学与跨领域知识合成大师。
现在用户决定将以下两张知识观点卡片，结合他自己的个人融合灵感，融合成一张全新的【对撞合题灵感卡片】（Synthesis Card）。

卡片 A 标题：{card_a.get('spark_title')}
卡片 A 原文内容："{card_a.get('quote')}"

卡片 B 标题：{card_b.get('spark_title')}
卡片 B 原文内容："{card_b.get('quote')}"

用户融合顿悟（my_synthesis）：
"{my_synthesis.strip()}"

你的任务是：
1. 结合卡片 A、卡片 B 和用户的个人顿悟，融合成一个高度凝练、金句般深刻的全新【合题观点原文】（quote，不超过 120 字）。
2. 为这个碰撞出来的观点，起一个极具学术张力与思维美感的【对撞主题标题】（spark_title，不超过 20 字，格式必须为：“【合题】xxxx”，例如：“【合题】系统权力与精神牢笼的同质性”）。
3. 撰写一段【为什么重要 (why_it_matters)】的诠释，阐述这层跨界融会背后的认知红利与启发（why_it_matters，不超过 100 字）。
4. 必须输出 JSON 格式，且只包含三个字段: "spark_title" (字符串), "quote" (字符串), "why_it_matters" (字符串)。
5. 直接输出 JSON 字符串，不要包含 ```json 或 ```，不要有任何多余字符。"""

        try:
            response_str = call_llm(llm_prompt, label="Link合成")
            cleaned_str = response_str.strip()
            if cleaned_str.startswith("```json"):
                cleaned_str = cleaned_str[7:]
            if cleaned_str.startswith("```"):
                cleaned_str = cleaned_str[3:]
            if cleaned_str.endswith("```"):
                cleaned_str = cleaned_str[:-3]
            cleaned_str = cleaned_str.strip()
            
            parsed = json.loads(cleaned_str)
            s_title = parsed.get("spark_title", f"【合题】{card_a.get('spark_title')} & {card_b.get('spark_title')}")
            s_quote = parsed.get("quote", my_synthesis.strip())
            s_why = parsed.get("why_it_matters", f"将观点《{card_a.get('spark_title')}》与《{card_b.get('spark_title')}》跨界碰撞融合的脑洞结晶。")
        except Exception as e:
            from app.core import logger
            logger.info(f"⚠️ [LOG ERROR] Synthesize LLM call failed: {e}")
            s_title = f"【合题】{card_a.get('spark_title')} & {card_b.get('spark_title')}"
            s_quote = my_synthesis.strip()
            s_why = f"跨越不同播客领域的脑力对撞成果。融合了：{card_a.get('spark_title')} 与 {card_b.get('spark_title')}。"

        return s_title, s_quote, s_why

    @staticmethod
    def collide_cards(card_a, card_b):
        prompt = f"""你是一个创意无限的跨界知识对撞与链接专家。你擅长在看似完全无关的两个观点中，发现它们底层的通感、共鸣或矛盾火花。

下面是两个知识观点卡片：
卡片 A：
- 标题：{card_a['spark_title']}
- 原文：{card_a['quote']}

卡片 B：
- 标题：{card_b['spark_title']}
- 原文：{card_b['quote']}

你的任务是：
1. 找出这两个观点底层逻辑深处的呼应点、互补点或冲突性火花。
2. 计算它们的【张力指数】（dissonance_index，介于 75 到 99 之间的整数，数值越高代表领域跨度越大，对撞效果越惊喜）。
3. 编写一句【对撞理由】（match_reason，不超过 60 字，例如：“卡片A关于伊朗战争，卡片B关于个人灵气消失。但它们底层都在探讨权力系统对个体生命的压迫。”）。
4. 作为一个跨界对撞机，向用户提一个深刻的、极具启发性的对撞提问（question，不超过 60 字，语气类似：“主人，我发现这两个人在不同领域都在强调/探讨【...】。你觉得它们是一回事吗？”）。
5. 必须以 JSON 格式输出，包含以下字段：
   - "dissonance_index": 整数
   - "match_reason": 字符串
   - "question": 字符串
6. 直接输出 JSON 字符串，不要包含 ```json 或 ``` 格式块，不要有任何多余文字。"""

        try:
            response_str = call_llm(prompt, label="Collider对撞")
            cleaned_str = response_str.strip()
            if cleaned_str.startswith("```json"):
                cleaned_str = cleaned_str[7:]
            if cleaned_str.startswith("```"):
                cleaned_str = cleaned_str[3:]
            if cleaned_str.endswith("```"):
                cleaned_str = cleaned_str[:-3]
            cleaned_str = cleaned_str.strip()
            
            parsed = json.loads(cleaned_str)
            dissonance_index = int(parsed.get("dissonance_index", random.randint(75, 98)))
            match_reason = parsed.get("match_reason", "虽然一者讨论领域不同，但它们在思维模式上具有同构契合性。")
            question = parsed.get("question", "我发现这两个观点底层都在强调一些共同的事情。你觉得它们是一回事吗？")
        except Exception as e:
            from app.core import logger
            logger.info(f"⚠️ [LOG ERROR] Collider AI prompt failed: {e}")
            dissonance_index = random.randint(78, 96)
            match_reason = f"虽然一者关于【{card_a.get('spark_title')}】，另一者关于【{card_b.get('spark_title')}】，但底层思维方式惊人地相似。"
            question = f"主人，我发现【{card_a['spark_title']}】与【{card_b['spark_title']}】之间或许有独特的默契。你觉得它们有什么底层联系吗？"

        return dissonance_index, match_reason, question

    @staticmethod
    def refine_insight(original_text: str):
        prompt = f"""你是一个个人知识管理的洞察提炼助手。
用户从一期播客中摘录了一段话，请你将这段长篇大论压缩、提炼成句【以第一人称口吻表达的原则或格言】。
要求：
1. 极其简练，直击核心（不超过30个字）。
2. 使用第一人称（例如：“限制社媒使用时间，可以让我的多巴胺基线恢复正常”）。
3. 只输出这一句话，不要有任何其他解释。

用户摘录原文：
"{original_text}"
"""
        try:
            response_str = call_llm(prompt, label="Insight润色")
            refined_content = response_str.strip()
        except Exception as e:
            from app.core import logger
            logger.info(f"⚠️ [LOG ERROR] Insight LLM refinement failed: {e}")
            refined_content = original_text[:30] + "..." if len(original_text) > 30 else original_text

        return refined_content
