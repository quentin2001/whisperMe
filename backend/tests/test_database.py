"""
whisperMe 数据库层单元测试
覆盖：tasks、paragraphs、speakers 表的 CRUD、级联删除、JSON 自动解析
"""
import uuid
import json
import pytest
from datetime import datetime


class TestTaskCRUD:
    """任务表增删改查"""

    def test_add_task_and_get_task(self, _isolate_test_env):
        """创建任务后能正确读取"""
        db = _isolate_test_env
        task_id = str(uuid.uuid4())
        db.add_task(task_id, "https://example.com/ep1", asr_mode="local", summary_mode="local")

        task = db.get_task(task_id)
        assert task is not None
        assert task["id"] == task_id
        assert task["url"] == "https://example.com/ep1"
        assert task["status"] == "pending"
        assert task["asr_mode"] == "local"
        assert task["progress"] == 0.0

    def test_get_all_tasks(self, _isolate_test_env):
        """列表返回正确数量和按 created_at DESC 排序"""
        db = _isolate_test_env
        id1 = str(uuid.uuid4())
        id2 = str(uuid.uuid4())
        db.add_task(id1, "https://example.com/ep1")
        db.add_task(id2, "https://example.com/ep2")

        tasks = db.get_all_tasks()
        assert len(tasks) == 2
        # 最新创建的在前
        assert tasks[0]["id"] == id2
        assert tasks[1]["id"] == id1

    def test_update_task(self, _isolate_test_env):
        """更新字段后持久化正确"""
        db = _isolate_test_env
        task_id = str(uuid.uuid4())
        db.add_task(task_id, "https://example.com/ep1")

        db.update_task_field(task_id, title="新标题", status="completed", progress=100.0)

        task = db.get_task(task_id)
        assert task["title"] == "新标题"
        assert task["status"] == "completed"
        assert task["progress"] == 100.0

    def test_delete_task_cascades(self, _isolate_test_env):
        """删除任务同时清理关联 paragraphs"""
        db = _isolate_test_env
        task_id = str(uuid.uuid4())
        db.add_task(task_id, "https://example.com/ep1")

        # 添加关联段落
        db.add_paragraphs([{
            "id": "p1", "podcast_id": task_id,
            "start_time": 0.0, "end_time": 10.0,
            "content": "测试内容", "sentences": [], "speaker": "SPEAKER_00"
        }])
        assert len(db.get_paragraphs_by_podcast(task_id)) == 1

        # 删除任务
        result = db.delete_task(task_id)
        assert result is True
        assert db.get_task(task_id) is None
        assert len(db.get_paragraphs_by_podcast(task_id)) == 0

    def test_delete_nonexistent_task(self, _isolate_test_env):
        """删除不存在的任务返回 False"""
        db = _isolate_test_env
        result = db.delete_task("nonexistent-id")
        assert result is False

    def test_get_next_pending_task(self, _isolate_test_env):
        """按 created_at ASC 返回最早的 pending 任务"""
        db = _isolate_test_env
        id1 = str(uuid.uuid4())
        id2 = str(uuid.uuid4())
        db.add_task(id1, "https://example.com/ep1")
        db.add_task(id2, "https://example.com/ep2")
        # 将 id2 设为 completed，id1 应该是下一个 pending
        db.update_task_field(id2, status="completed")

        next_task = db.get_next_pending_task()
        assert next_task is not None
        assert next_task["id"] == id1

    def test_get_next_pending_task_empty(self, _isolate_test_env):
        """没有 pending 任务时返回 None"""
        db = _isolate_test_env
        assert db.get_next_pending_task() is None

    def test_get_task_queue_position(self, _isolate_test_env):
        """pending 任务的排队位置计算正确"""
        db = _isolate_test_env
        id1 = str(uuid.uuid4())
        id2 = str(uuid.uuid4())
        id3 = str(uuid.uuid4())
        db.add_task(id1, "https://example.com/ep1")
        db.add_task(id2, "https://example.com/ep2")
        db.add_task(id3, "https://example.com/ep3")

        # id1 最早创建，排第 1
        pos1 = db.get_task_queue_position(id1)

        # id3 最晚创建，排第 3
        pos3 = db.get_task_queue_position(id3)

    def test_get_task_queue_position_non_pending(self, _isolate_test_env):
        """非 pending 任务返回 -1"""
        db = _isolate_test_env
        task_id = str(uuid.uuid4())
        db.add_task(task_id, "https://example.com/ep1")
        db.update_task_field(task_id, status="completed")

        pos = db.get_task_queue_position(task_id)
        assert pos == -1


class TestParagraphCRUD:
    """段落表增删改查"""

    def test_add_paragraphs_and_get(self, _isolate_test_env):
        """段落 CRUD"""
        db = _isolate_test_env
        task_id = str(uuid.uuid4())
        db.add_task(task_id, "https://example.com/ep1")

        paragraphs = [
            {"id": "p1", "podcast_id": task_id, "start_time": 0.0, "end_time": 10.0,
             "content": "第一段", "sentences": [], "speaker": "SPEAKER_00"},
            {"id": "p2", "podcast_id": task_id, "start_time": 10.0, "end_time": 20.0,
             "content": "第二段", "sentences": [], "speaker": "SPEAKER_01"},
        ]
        db.add_paragraphs(paragraphs)

        result = db.get_paragraphs_by_podcast(task_id)
        assert len(result) == 2
        contents = {p["content"] for p in result}
        assert contents == {"第一段", "第二段"}

    def test_delete_paragraphs_by_podcast(self, _isolate_test_env):
        """按 podcast_id 删除所有段落"""
        db = _isolate_test_env
        task_id = str(uuid.uuid4())
        db.add_task(task_id, "https://example.com/ep1")
        db.add_paragraphs([
            {"id": "p1", "podcast_id": task_id, "start_time": 0.0, "end_time": 10.0,
             "content": "测试", "sentences": [], "speaker": ""}
        ])

        db.delete_paragraphs_by_podcast(task_id)
        assert len(db.get_paragraphs_by_podcast(task_id)) == 0


class TestSpeakerCRUD:
    """声纹库增删改查"""

    def test_speaker_upsert_and_merge(self, _isolate_test_env):
        """声纹 upsert、加权合并、删除"""
        db = _isolate_test_env

        # 插入两个声纹
        db.upsert_speaker("Alice", [1.0, 0.0, 0.0], sample_count=3)
        db.upsert_speaker("Bob", [0.0, 1.0, 0.0], sample_count=2)

        speakers = db.get_all_speakers()
        assert len(speakers) == 2

        # 获取单个声纹（含 embedding）
        alice = db.get_speaker("Alice")
        assert alice is not None
        assert alice["name"] == "Alice"
        assert alice["sample_count"] == 3

        # 合并 Bob → Alice
        result = db.merge_speakers("Bob", "Alice")
        assert result is True

        # Bob 应该被删除
        assert db.get_speaker("Bob") is None

        # Alice 的 embedding 应该是加权平均
        alice = db.get_speaker("Alice")
        assert alice["sample_count"] == 5  # 3 + 2

        # 删除声纹
        result = db.delete_speaker("Alice")
        assert result is True
        assert db.get_speaker("Alice") is None

    def test_speaker_get_with_embeddings(self, _isolate_test_env):
        """获取全局声纹库（含 embedding 向量）"""
        db = _isolate_test_env
        db.upsert_speaker("Speaker_A", [0.1, 0.2, 0.3])
        db.upsert_speaker("Speaker_B", [0.4, 0.5, 0.6])

        result = db.get_all_speakers_with_embeddings()
        assert "Speaker_A" in result
        assert "Speaker_B" in result
        assert "embedding" in result["Speaker_A"]
        assert result["Speaker_A"]["embedding"] == [0.1, 0.2, 0.3]

    def test_merge_nonexistent_speakers(self, _isolate_test_env):
        """合并不存的声纹返回 False"""
        db = _isolate_test_env
        result = db.merge_speakers("Nobody", "AlsoNobody")
        assert result is False

    def test_delete_nonexistent_speaker(self, _isolate_test_env):
        """删除不存在的声纹返回 False"""
        db = _isolate_test_env
        result = db.delete_speaker("Nobody")
        assert result is False


class TestJsonAutoParse:
    """dict_factory JSON 自动解析"""

    def test_json_auto_parse(self, _isolate_test_env):
        """dict_factory 自动解析 JSON 字段"""
        db = _isolate_test_env
        task_id = str(uuid.uuid4())
        db.add_task(task_id, "https://example.com/ep1")
        db.update_task_field(
            task_id,
            metadata={"key": "value", "nested": {"a": 1}},
            speaker_mappings={"SPEAKER_00": "主持人"},
        )

        task = db.get_task(task_id)
        # metadata 应该被自动解析为 dict
        assert isinstance(task["metadata"], dict)
        assert task["metadata"]["key"] == "value"
        assert task["metadata"]["nested"]["a"] == 1
        # speaker_mappings 应该被自动解析为 dict
        assert isinstance(task["speaker_mappings"], dict)
        assert task["speaker_mappings"]["SPEAKER_00"] == "主持人"
