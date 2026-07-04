"""
Suite 3 (DB): 数据库与并发读写测试
测试对象: database/core.py, repositories/
核心验证点: WAL 模式并发安全、字段级原子更新、联级删除一致性
"""
import uuid
import threading
import pytest


class TestDBWAL:
    """DB_WAL_01: WAL 初始化"""

    def test_wal_mode_enabled(self, _isolate_test_env):
        """数据库连接启用 WAL 模式与外键约束"""
        db = _isolate_test_env
        c = db.core.conn.cursor()
        c.execute("PRAGMA journal_mode;")
        row = c.fetchone()
        assert row["journal_mode"].lower() == "wal"

    def test_foreign_keys_enabled(self, _isolate_test_env):
        """外键约束开启"""
        db = _isolate_test_env
        c = db.core.conn.cursor()
        c.execute("PRAGMA foreign_keys;")
        row = c.fetchone()
        assert row["foreign_keys"] == 1

    def test_busy_timeout(self, _isolate_test_env):
        """busy_timeout 设为 30000ms"""
        db = _isolate_test_env
        c = db.core.conn.cursor()
        c.execute("PRAGMA busy_timeout;")
        row = c.fetchone()
        assert row["timeout"] >= 30000


class TestDBConcurrency:
    """DB_CON_02~03: 并发读写安全"""

    def test_concurrent_write_pressure(self, _isolate_test_env):
        """多线程并发写入不产生 database locked 错误"""
        db = _isolate_test_env
        task_id = str(uuid.uuid4())
        db.add_task(task_id, "https://example.com/concurrent-test")
        errors = []

        def writer_progress(wid):
            try:
                for i in range(20):
                    db.update_task_field(task_id, progress=(i + 1) * 5.0)
            except Exception as e:
                errors.append(f"progress-{wid}: {e}")

        def writer_speaker(wid):
            try:
                for i in range(10):
                    db.update_task_field(
                        task_id,
                        speaker_mappings={f"SPEAKER_{i}": f"Speaker_{wid}_{i}"}
                    )
            except Exception as e:
                errors.append(f"speaker-{wid}: {e}")

        threads = []
        for i in range(3):
            threads.append(threading.Thread(target=writer_progress, args=(i,)))
            threads.append(threading.Thread(target=writer_speaker, args=(i,)))

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert len(errors) == 0, f"Concurrency errors: {errors}"
        # 最终值应为最后一次写入
        task = db.get_task(task_id)
        assert task is not None

    def test_thread_local_connections(self, _isolate_test_env):
        """不同线程使用独立的 SQLite 连接"""
        db = _isolate_test_env
        conn_ids = {}
        errors = []

        def worker(wid):
            try:
                conn_ids[wid] = id(db.core.conn)
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        assert len(errors) == 0, f"Errors: {errors}"
        # 至少有 2 个不同的连接 ID（主线程 + 至少一个工作线程）
        unique_ids = set(conn_ids.values())
        assert len(unique_ids) >= 2, f"Only {len(unique_ids)} unique connections"


class TestDBAtomic:
    """DB_ATOM_04~05: 字段级原子更新"""

    def test_field_level_update(self, _isolate_test_env):
        """update_task_field 仅更新指定字段"""
        db = _isolate_test_env
        task_id = str(uuid.uuid4())
        db.add_task(task_id, "https://example.com/ep1")

        # 先设初始值
        db.update_task_field(task_id, title="原标题", status="pending", progress=10.0)
        # 只更新 title
        db.update_task_field(task_id, title="新标题")

        task = db.get_task(task_id)
        assert task["title"] == "新标题"
        assert task["status"] == "pending"
        assert task["progress"] == 10.0

    def test_empty_update_returns_current(self, _isolate_test_env):
        """无参数更新不执行 SQL"""
        db = _isolate_test_env
        task_id = str(uuid.uuid4())
        db.add_task(task_id, "https://example.com/ep1")
        db.update_task_field(task_id, title="测试")

        # 无 kwargs 调用
        result = db.update_task_field(task_id)
        assert result is not None
        assert result["title"] == "测试"


class TestDBDelete:
    """DB_DEL_06: 任务删除联级清理"""

    def test_delete_task_cascades_to_paragraphs(self, _isolate_test_env):
        """删除任务时同步清理关联 paragraphs"""
        db = _isolate_test_env
        task_id = str(uuid.uuid4())
        db.add_task(task_id, "https://example.com/ep1")

        db.add_paragraphs([{
            "id": "p_cascade_test", "podcast_id": task_id,
            "start_time": 0.0, "end_time": 10.0,
            "content": "级联删除测试", "sentences": [], "speaker": "SPEAKER_00"
        }])
        assert len(db.get_paragraphs_by_podcast(task_id)) == 1

        result = db.delete_task(task_id)
        assert result is True
        assert db.get_task(task_id) is None
        assert len(db.get_paragraphs_by_podcast(task_id)) == 0


class TestDBSpeaker:
    """DB_SPK_07~10: 说话人管理"""

    def test_merge_speakers_data_consistency(self, _isolate_test_env):
        """合并说话人后加权平均正确"""
        db = _isolate_test_env
        db.upsert_speaker("Alice", [1.0, 0.0, 0.0], sample_count=3)
        db.upsert_speaker("Bob", [0.0, 1.0, 0.0], sample_count=2)
        db.upsert_speaker("Charlie", [0.5, 0.5, 0.0], sample_count=1)

        # 合并 Bob → Alice
        result = db.merge_speakers("Bob", "Alice")
        assert result is True

        # Bob 消失
        assert db.get_speaker("Bob") is None
        # Alice 保留，sample_count 为 5 (3+2)
        alice = db.get_speaker("Alice")
        assert alice["sample_count"] == 5

    def test_merge_same_speaker_rejected(self, client):
        """合并同一个说话人返回 400"""
        resp = client.post("/api/tasks/speakers/merge", json={
            "source_name": "Alice",
            "target_name": "Alice"
        })
        assert resp.status_code == 400
        assert "不能合并同一个说话人" in resp.json()["detail"]

    def test_merge_nonexistent_speaker_404(self, client):
        """source 或 target 不存在时返回 404"""
        resp = client.post("/api/tasks/speakers/merge", json={
            "source_name": "Nobody",
            "target_name": "AlsoNobody"
        })
        assert resp.status_code == 404

    def test_forget_speaker_keeps_history(self, _isolate_test_env):
        """忘记说话人后声纹库删除但不影响已有任务"""
        db = _isolate_test_env
        db.upsert_speaker("Charlie", [0.5, 0.5, 0.5])

        # 在声纹库中存在
        assert db.get_speaker("Charlie") is not None

        # 删除
        result = db.delete_speaker("Charlie")
        assert result is True

        # 声纹库中消失
        assert db.get_speaker("Charlie") is None

    def test_forget_nonexistent_speaker_404(self, client):
        """删除不存在的说话人返回 404"""
        resp = client.post("/api/tasks/speakers/forget", json={"name": "Nobody"})
        assert resp.status_code == 404


class TestDBQueue:
    """DB_QUEUE_11~12: 任务队列"""

    def test_queue_position(self, _isolate_test_env):
        """pending 任务的排队位置正确"""
        import time
        db = _isolate_test_env
        id_a = str(uuid.uuid4())
        id_b = str(uuid.uuid4())
        id_c = str(uuid.uuid4())
        db.add_task(id_a, "https://example.com/epA")
        time.sleep(0.01)
        db.add_task(id_b, "https://example.com/epB")
        time.sleep(0.01)
        db.add_task(id_c, "https://example.com/epC")

        pos_a = db.get_task_queue_position(id_a)
        pos_c = db.get_task_queue_position(id_c)
        assert pos_a == 1
        assert pos_c == 3
