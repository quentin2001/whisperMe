import random
import json
import uuid
import threading
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
from app.core.llm_utils import call_llm

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
    from app.services.board_service import BoardService
    spark_title, why_it_matters = BoardService.generate_card_content(quote)

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
    
    from app.services.board_service import BoardService
    new_status, new_interval, new_efactor, next_date = BoardService.calculate_next_review(efactor, interval, req.direction)
    
    if req.direction != "left":
        try:
            task = db.get_task(card["podcast_id"])
            podcast_title = task.get("title", "未知标题") if task else "未知播客"
            podcast_name = task.get("podcast_name", "未知播客") if task else "未知播客"
            
            notifier.send_desktop_notification(
                title=f"🧠 记忆唤醒警报: 【{card['spark_title']}】",
                message=f"该卡片已被设为遗忘提醒。原文: {card['quote'][:60]}..."
            )
            
            BoardService.send_forget_warning_webhook(card, podcast_title, podcast_name)
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
        
    from app.services.board_service import BoardService
    s_title, s_quote, s_why = BoardService.synthesize_cards(card_a, card_b, req.my_synthesis)

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
    
    from app.services.board_service import BoardService
    dissonance_index, match_reason, question = BoardService.collide_cards(card_a, card_b)

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
    from app.services.board_service import BoardService
    refined_content = BoardService.refine_insight(req.original_text)

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
