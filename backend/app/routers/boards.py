import random
import json
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.config import config
from app.database import db
from app.core.transcriber import PodcastTranscriber
from app.core.notifier import notifier

from app.core import logger
print = logger.info

router = APIRouter(prefix="/api", tags=["boards"])

transcriber = PodcastTranscriber()

# --- Pydantic Schemas ---
class CreateCardRequest(BaseModel):
    paragraph_id: str
    podcast_id: str
    board_id: str = "board_default"

class ReviewCardRequest(BaseModel):
    direction: str  # "left" or "right"

class CreateLinkRequest(BaseModel):
    source_card_id: str
    target_card_id: str
    my_synthesis: str = ""
    board_id: str = None

class UpdateCardPositionRequest(BaseModel):
    x: float
    y: float

class CreateBoardRequest(BaseModel):
    name: str

class AddCardToBoardRequest(BaseModel):
    card_id: str
    pos_x: float = 0.0
    pos_y: float = 0.0

class CreateInsightRequest(BaseModel):
    podcast_id: str
    original_text: str

class ReviewInsightRequest(BaseModel):
    action: str # "keep" or "discard"

# --- Unified LLM Calling Helper ---
def call_llm(prompt: str, summary_mode: str = None, label: str = "LLM调用") -> str:
    import httpx
    
    if not summary_mode:
        summary_mode = config.get("summary_mode", "local")
        
    if summary_mode == "online":
        api_key = config.get("online_summary_api_key", "").strip()
        base_url = config.get("online_summary_base_url", "https://api.openai.com/v1").strip()
        target_model = config.get("online_summary_model", "gpt-4o-mini").strip()
        api_url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        print(f"📡 [LOG] {label}【在线模式】 - 接口: {api_url} | 模型: {target_model}")
    else:
        ollama_url = config.get("ollama_url", "http://localhost:11434").strip()
        target_model = config.get("ollama_model", "qwen2.5:7b-instruct").strip()
        base_url = ollama_url.rstrip('/')
        api_url = f"{base_url}/v1/chat/completions" if '/v1' not in base_url else f"{base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        print(f"🤖 [LOG] {label}【本地模式】 - 接口: {api_url} | 模型: {target_model}")
        
    payload = {
        "model": target_model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "temperature": 0.1
    }
    
    with httpx.Client(timeout=120.0, trust_env=False) as client:
        response = client.post(api_url, json=payload, headers=headers)
        if response.status_code != 200:
            raise Exception(f"LLM API error (code {response.status_code}): {response.text}")
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()

# --- API Endpoints ---

@router.get("/paragraphs")
def get_paragraphs(podcast_id: str):
    paragraphs = db.get_paragraphs_by_podcast(podcast_id)
    is_old_format = paragraphs and len(paragraphs) > 0 and ("sentences" not in paragraphs[0] or not isinstance(paragraphs[0].get("sentences"), list))
    if not paragraphs or is_old_format:
        task = db.get_task(podcast_id)
        if not task or not task.get("transcript"):
            return []
        try:
            print(f"🔄 [LOG] 为老任务 {podcast_id} 动态生成（或重新生成）语义段落...")
            paragraphs = transcriber.cluster_segments_to_paragraphs(podcast_id, task.get("transcript"))
            db.delete_paragraphs_by_podcast(podcast_id)
            db.add_paragraphs(paragraphs)
        except Exception as e:
            print(f"❌ [LOG ERROR] 动态生成段落失败: {e}")
            return []
    
    podcast_cards = db.get_cards_by_podcast(podcast_id)
    sedimented_paragraph_ids = {c["paragraph_id"] for c in podcast_cards}
    for p in paragraphs:
        p["sedimented"] = p["id"] in sedimented_paragraph_ids
        
    return paragraphs

@router.post("/cards/create")
def create_card(req: CreateCardRequest):
    existing_cards = db.get_all_cards()
    for c in existing_cards:
        if c.get("paragraph_id") == req.paragraph_id:
            return c

    paragraphs = db.get_paragraphs_by_podcast(req.podcast_id)
    paragraph = None
    for p in paragraphs:
        if p["id"] == req.paragraph_id:
            paragraph = p
            break
            
    if not paragraph:
        paragraphs = get_paragraphs(req.podcast_id)
        for p in paragraphs:
            if p["id"] == req.paragraph_id:
                paragraph = p
                break
    
    if not paragraph:
        raise HTTPException(status_code=404, detail="未找到对应的语义段落")
        
    quote = paragraph["content"]
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
        print(f"⚠️ [LOG ERROR] LLM 卡片提炼失败: {e}")
        spark_title = quote[:15] + "..." if len(quote) > 15 else quote
        why_it_matters = "由于大模型连接失败或解析异常，该卡片以默认模式生成。原话非常关键，值得反复记忆复习。"

    card_id = str(uuid.uuid4())
    tomorrow = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    card = {
        "id": card_id,
        "paragraph_id": req.paragraph_id,
        "podcast_id": req.podcast_id,
        "spark_title": spark_title,
        "quote": quote,
        "why_it_matters": why_it_matters,
        "efactor": 2.5,
        "interval": 1,
        "next_review_date": tomorrow,
        "status": "active",
        "created_at": datetime.now().isoformat()
    }
    
    db.create_card(card)
    if req.board_id:
        db.add_card_to_board(req.board_id, card_id)
    return card

@router.delete("/cards/paragraph/{paragraph_id}")
def delete_card_by_paragraph(paragraph_id: str):
    cards = db.get_all_cards()
    card_to_delete = None
    for c in cards:
        if c.get("paragraph_id") == paragraph_id:
            card_to_delete = c
            break
            
    if not card_to_delete:
        raise HTTPException(status_code=404, detail="未找到该段落对应的卡片")
        
    success = db.delete_card(card_to_delete["id"])
    if not success:
        raise HTTPException(status_code=500, detail="删除卡片失败")
        
    return {"status": "ok", "deleted_card_id": card_to_delete["id"]}

@router.put("/cards/{card_id}/position")
def update_card_position(card_id: str, req: UpdateCardPositionRequest):
    card = db.get_card(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="卡片未找到")
    
    updated_card = db.update_card(card_id, pos_x=req.x, pos_y=req.y)
    return {"status": "ok", "card": updated_card}

@router.get("/boards")
def get_boards():
    return db.get_all_boards()

@router.post("/boards")
def create_board(req: CreateBoardRequest):
    b_id = f"board_{uuid.uuid4().hex[:12]}"
    return db.create_board(b_id, req.name)

@router.post("/boards/{board_id}/cards")
def add_card_to_board(board_id: str, req: AddCardToBoardRequest):
    db.add_card_to_board(board_id, req.card_id, req.pos_x, req.pos_y)
    return {"status": "ok"}

@router.put("/boards/{board_id}/cards/{card_id}/position")
def update_board_card_position(board_id: str, card_id: str, req: UpdateCardPositionRequest):
    db.update_board_card_position(board_id, card_id, req.x, req.y)
    return {"status": "ok"}

@router.get("/cards")
def get_cards(board_id: str = None):
    if board_id:
        cards = db.get_cards_by_board(board_id)
    else:
        cards = db.get_all_cards()
    for c in cards:
        task = db.get_task(c["podcast_id"])
        if task:
            c["podcast_title"] = task.get("title", "未知标题")
            c["podcast_image_url"] = task.get("image_url", "")
            c["podcast_name"] = task.get("podcast_name", "未知播客")
            
            paras = db.get_paragraphs_by_podcast(c["podcast_id"])
            for p in paras:
                if p["id"] == c["paragraph_id"]:
                    c["start_time"] = p.get("start_time", 0)
                    c["end_time"] = p.get("end_time", 0)
                    break
    return cards

@router.get("/cards/due")
def get_due_cards():
    today = datetime.today().strftime("%Y-%m-%d")
    all_cards = db.get_all_cards()
    valid_cards = [c for c in all_cards if c.get("status") in ["active", "warning"]]
    due_cards = [c for c in valid_cards if c.get("next_review_date", "") <= today]
    due_cards.sort(key=lambda x: (0 if x.get("status") == "warning" else 1, x.get("created_at", "")), reverse=True)
    
    def populate_card_details(c):
        task = db.get_task(c["podcast_id"])
        if task:
            c["podcast_title"] = task.get("title", "未知标题")
            c["podcast_image_url"] = task.get("image_url", "")
            c["podcast_name"] = task.get("podcast_name", "未知播客")
            paras = db.get_paragraphs_by_podcast(c["podcast_id"])
            for p in paras:
                if p["id"] == c["paragraph_id"]:
                    c["start_time"] = p.get("start_time", 0)
                    c["end_time"] = p.get("end_time", 0)
                    break
        return c

    due_cards = [populate_card_details(c) for c in due_cards]
    if len(due_cards) >= 3:
        return due_cards[:3]
        
    non_due_cards = [c for c in valid_cards if c.get("next_review_date", "") > today]
    random.shuffle(non_due_cards)
    needed = 3 - len(due_cards)
    backfill_cards = non_due_cards[:needed]
    backfill_cards = [populate_card_details(c) for c in backfill_cards]
    
    result = due_cards + backfill_cards
    return result

@router.post("/cards/{card_id}/review")
def review_card(card_id: str, req: ReviewCardRequest):
    card = db.get_card(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="卡片不存在")
        
    today = datetime.today()
    efactor = card.get("efactor", 2.5)
    interval = card.get("interval", 1)
    
    if req.direction == "left":
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
        
        try:
            task = db.get_task(card["podcast_id"])
            podcast_title = task.get("title", "未知标题") if task else "未知播客"
            podcast_name = task.get("podcast_name", "未知播客") if task else "未知播客"
            
            notifier.send_desktop_notification(
                title=f"🧠 记忆唤醒警报: 【{card['spark_title']}】",
                message=f"该卡片已被设为遗忘提醒。原文: {card['quote'][:60]}..."
            )
            
            webhook_url = config.get("webhook_url", "").strip()
            if webhook_url:
                import httpx
                source_link = f"http://localhost:5173/?task_id={card['podcast_id']}&paragraph_id={card['paragraph_id']}"
                payload = {
                    "msg_type": "text",
                    "text": {
                        "content": f"🧠 【知识遗忘唤醒警告】\n闪光点: {card['spark_title']}\n原话: {card['quote']}\nAI 提炼: {card['why_it_matters']}\n播客来源: {podcast_name} - 《{podcast_title}》\n🧭 溯源链接: {source_link}"
                    }
                }
                def send_webhook_async(url, payload):
                    try:
                        with httpx.Client(timeout=10.0, trust_env=False) as client:
                            client.post(url, json=payload)
                            print("🔔 [LOG] Webhook notification sent successfully.")
                    except Exception as wh_err:
                        print(f"⚠️ [LOG WARNING] Webhook notification failed: {wh_err}")
                
                threading.Thread(target=send_webhook_async, args=(webhook_url, payload), daemon=True).start()
                
        except Exception as notif_err:
            print(f"⚠️ [LOG ERROR] 发送复习失败通知失败: {notif_err}")
            
    db.update_card(
        card_id,
        status=new_status,
        efactor=new_efactor,
        interval=new_interval,
        next_review_date=next_date
    )
    
    return db.get_card(card_id)

@router.get("/links")
def get_links():
    return db.get_all_links()

@router.post("/links")
def create_link(req: CreateLinkRequest):
    card_a = db.get_card(req.source_card_id)
    card_b = db.get_card(req.target_card_id)
    if not card_a or not card_b:
        raise HTTPException(status_code=404, detail="关联的卡片不存在")
        
    llm_prompt = f"""你是一个高级哲学与跨领域知识合成大师。
    现在用户决定将以下两张知识观点卡片，结合他自己的个人融合灵感，融合成一张全新的【对撞合题灵感卡片】（Synthesis Card）。
    
    卡片 A 标题：{card_a.get('spark_title')}
    卡片 A 原文内容："{card_a.get('quote')}"
    
    卡片 B 标题：{card_b.get('spark_title')}
    卡片 B 原文内容："{card_b.get('quote')}"
    
    用户融合顿悟（my_synthesis）：
    "{req.my_synthesis.strip()}"
    
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
        s_quote = parsed.get("quote", req.my_synthesis.strip())
        s_why = parsed.get("why_it_matters", f"将观点《{card_a.get('spark_title')}》与《{card_b.get('spark_title')}》跨界碰撞融合的脑洞结晶。")
    except Exception as e:
        print(f"⚠️ [LOG ERROR] Synthesize LLM call failed: {e}")
        s_title = f"【合题】{card_a.get('spark_title')} & {card_b.get('spark_title')}"
        s_quote = req.my_synthesis.strip()
        s_why = f"跨越不同播客领域的脑力对撞成果。融合了：{card_a.get('spark_title')} 与 {card_b.get('spark_title')}。"

    pos_x_a = card_a.get("pos_x") or 0.0
    pos_y_a = card_a.get("pos_y") or 0.0
    pos_x_b = card_b.get("pos_x") or 0.0
    pos_y_b = card_b.get("pos_y") or 0.0
    mid_x = (pos_x_a + pos_x_b) / 2.0
    mid_y = (pos_y_a + pos_y_b) / 2.0 - 200

    s_card_id = f"s_card_{uuid.uuid4().hex[:12]}"
    synthesized_card = {
        "id": s_card_id,
        "paragraph_id": f"synthesis-{uuid.uuid4().hex[:12]}",
        "podcast_id": "collider",
        "podcast_name": "💥 跨界灵感对撞",
        "spark_title": s_title,
        "quote": s_quote,
        "why_it_matters": s_why,
        "created_at": datetime.now().isoformat(),
        "is_synthesis": True,
        "parent_ids": [req.source_card_id, req.target_card_id],
        "parent_titles": [card_a.get("spark_title"), card_b.get("spark_title")],
        "efactor": 2.5,
        "status": "stable",
        "pos_x": mid_x,
        "pos_y": mid_y
    }
    db.create_card(synthesized_card)
    
    if req.board_id:
        db.add_card_to_board(req.board_id, s_card_id, mid_x, mid_y)
    
    link1 = {
        "id": f"link_{uuid.uuid4().hex[:12]}",
        "source_card_id": req.source_card_id,
        "target_card_id": s_card_id,
        "my_synthesis": req.my_synthesis.strip(),
        "created_at": datetime.now().isoformat()
    }
    db.create_link(link1)
    
    link2 = {
        "id": f"link_{uuid.uuid4().hex[:12]}",
        "source_card_id": req.target_card_id,
        "target_card_id": s_card_id,
        "my_synthesis": req.my_synthesis.strip(),
        "created_at": datetime.now().isoformat()
    }
    db.create_link(link2)
    
    return link1

@router.get("/cards/collider")
def get_collider():
    cards = db.get_all_cards()
    if len(cards) < 2:
        raise HTTPException(status_code=400, detail="本地卡片盒中卡片数量少于2张，无法启动 AI 对撞机")
        
    links = db.get_all_links()
    
    def is_linked(id_a, id_b):
        for l in links:
            if (l["source_card_id"] == id_a and l["target_card_id"] == id_b) or \
               (l["source_card_id"] == id_b and l["target_card_id"] == id_a):
                return True
        return False
        
    unlinked_pairs = []
    for i in range(len(cards)):
        for j in range(i+1, len(cards)):
            if not is_linked(cards[i]["id"], cards[j]["id"]):
                unlinked_pairs.append((cards[i], cards[j]))
                
    if not unlinked_pairs:
        raise HTTPException(status_code=400, detail="所有卡片均已建立关联，AI 对撞机没有可对撞的脑洞啦！")
        
    diff_podcast_pairs = [p for p in unlinked_pairs if p[0]["podcast_id"] != p[1]["podcast_id"]]
    pair = random.choice(diff_podcast_pairs) if diff_podcast_pairs else random.choice(unlinked_pairs)
    
    card_a, card_b = pair
    
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
        print(f"⚠️ [LOG ERROR] Collider AI prompt failed: {e}")
        dissonance_index = random.randint(78, 96)
        match_reason = f"虽然一者关于【{card_a.get('spark_title')}】，另一者关于【{card_b.get('spark_title')}】，但底层思维方式惊人地相似。"
        question = f"主人，我发现【{card_a['spark_title']}】与【{card_b['spark_title']}】之间或许有独特的默契。你觉得它们有什么底层联系吗？"

    for c in [card_a, card_b]:
        task = db.get_task(c["podcast_id"])
        if task:
            c["podcast_title"] = task.get("title", "未知标题")
            c["podcast_name"] = task.get("podcast_name", "未知播客")
            
    return {
        "card_a": card_a,
        "card_b": card_b,
        "question": question,
        "dissonance_index": dissonance_index,
        "match_reason": match_reason
    }

@router.post("/insights")
def create_insight(req: CreateInsightRequest):
    prompt = f"""你是一个个人知识管理的洞察提炼助手。
用户从一期播客中摘录了一段话，请你将这段长篇大论压缩、提炼成句【以第一人称口吻表达的原则或格言】。
要求：
1. 极其简练，直击核心（不超过30个字）。
2. 使用第一人称（例如：“限制社媒使用时间，可以让我的多巴胺基线恢复正常”）。
3. 只输出这一句话，不要有任何其他解释。

用户摘录原文：
"{req.original_text}"
"""
    try:
        response_str = call_llm(prompt, label="Insight润色")
        refined_content = response_str.strip()
    except Exception as e:
        print(f"⚠️ [LOG ERROR] Insight LLM refinement failed: {e}")
        refined_content = req.original_text[:30] + "..." if len(req.original_text) > 30 else req.original_text

    tomorrow = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    insight = {
        "podcast_id": req.podcast_id,
        "original_text": req.original_text,
        "refined_content": refined_content,
        "review_count": 0,
        "next_review_date": tomorrow,
        "status": "ACTIVE"
    }
    return db.create_insight(insight)

@router.get("/insights/review")
def get_insights_for_review():
    insights = db.get_insights_for_review()
    for ins in insights:
        task = db.get_task(ins["podcast_id"])
        if task:
            ins["podcast_title"] = task.get("title", "未知标题")
            ins["podcast_name"] = task.get("podcast_name", "未知播客")
    return insights

@router.post("/insights/{insight_id}/review")
def review_insight(insight_id: str, req: ReviewInsightRequest):
    insight = db.get_all_insights()
    target = None
    for ins in insight:
        if ins["id"] == insight_id:
            target = ins
            break
            
    if not target:
        raise HTTPException(status_code=404, detail="Insight not found")
        
    today = datetime.today()
    if req.action == "keep":
        current_count = target.get("review_count", 0)
        intervals = [1, 3, 7, 14, 30]
        next_interval = intervals[min(current_count, len(intervals)-1)]
        next_date = (today + timedelta(days=next_interval)).strftime("%Y-%m-%d")
        
        db.update_insight(
            insight_id,
            review_count=current_count + 1,
            next_review_date=next_date
        )
    elif req.action == "discard":
        db.delete_insight(insight_id)
        
    return {"status": "ok"}
