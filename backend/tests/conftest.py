"""
whisperMe 后端测试 - 全局 Fixtures
"""
import os
import sys
import shutil
import tempfile
import uuid
import pytest
from datetime import datetime
from unittest.mock import MagicMock

# 确保 backend 目录在 Python 路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(autouse=True)
def _isolate_test_env(monkeypatch):
    """
    每个测试用例使用独立的临时 SQLite 数据库，避免测试间互相污染。
    同时 mock 掉队列管理器，阻止后台线程启动。
    """
    tmp_dir = tempfile.mkdtemp(prefix="whisperme_test_")
    test_db_path = os.path.join(tmp_dir, "test_whisperMe.db")

    import app.database.core as db_core
    monkeypatch.setattr(db_core, "DB_FILE_PATH", test_db_path)
    import app.database as db_module
    test_db = db_module.DatabaseFacade()
    monkeypatch.setattr(db_module, "db", test_db)

    # 替换所有直接 import db 的模块
    for mod_name in ["app.main", "app.routers.tasks", "app.routers.boards", "app.services.board_service", "app.services.task_service"]:
        mod = sys.modules.get(mod_name)
        if mod and hasattr(mod, "db"):
            monkeypatch.setattr(mod, "db", test_db)

    # Mock 队列管理器
    import app.core.queue_manager as qm_module
    mock_qm = MagicMock()
    mock_qm.add_task = MagicMock()
    mock_qm.start = MagicMock()
    mock_qm.get_queue_position = MagicMock(return_value=-1)
    mock_qm.get_current_task_id = MagicMock(return_value=None)
    mock_qm.task_queue = MagicMock()
    mock_qm.task_queue.qsize = MagicMock(return_value=0)
    monkeypatch.setattr(qm_module, "queue_manager", mock_qm)

    for mod_name in ["app.main", "app.routers.tasks"]:
        mod = sys.modules.get(mod_name)
        if mod and hasattr(mod, "queue_manager"):
            monkeypatch.setattr(mod, "queue_manager", mock_qm)

    # 阻止 startup 后台线程
    import app.main as main_mod
    monkeypatch.setattr(main_mod, "start_system_background_tasks", lambda: None)

    yield test_db

    # 清理临时目录
    try:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    except Exception:
        pass


@pytest.fixture
def client():
    """FastAPI TestClient 实例"""
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


@pytest.fixture
def sample_task(_isolate_test_env):
    """创建一个 completed 状态的示例任务（含 transcript + paragraphs）"""
    test_db = _isolate_test_env
    task_id = str(uuid.uuid4())

    test_db.add_task(task_id, "https://example.com/podcast/ep1", asr_mode="local", summary_mode="local")
    test_db.update_task_field(
        task_id,
        title="测试播客 - 第一期",
        podcast_name="测试播客",
        status="completed",
        progress=100.0,
        image_url="https://example.com/image.jpg",
        metadata={
            "title": "测试播客 - 第一期",
            "podcast_name": "测试播客",
            "shownotes": "这是一期测试播客。",
            "like_count": 100,
            "comment_count": 20,
            "comments": [],
            "image_url": "https://example.com/image.jpg",
            "source": "xiaoyuzhou",
            "duration": "45:30"
        },
        transcript=[
            {"start": 0.0, "end": 5.0, "text": "大家好，欢迎收听测试播客。", "speaker": "SPEAKER_00"},
            {"start": 5.0, "end": 12.0, "text": "今天我们讨论软件测试的重要性。", "speaker": "SPEAKER_00"},
            {"start": 12.0, "end": 20.0, "text": "测试是保证软件质量的关键环节。", "speaker": "SPEAKER_01"},
        ],
        summary="本期播客讨论了软件测试的重要性。",
        speaker_mappings={"SPEAKER_00": "主持人", "SPEAKER_01": "嘉宾"},
        speaker_embeddings={"SPEAKER_00": [0.1] * 10, "SPEAKER_01": [0.2] * 10},
        speaker_confidence={},
        audio_url="/audio/test_ep1.mp3",
    )

    paragraphs = [
        {
            "id": f"p_{task_id}_0",
            "podcast_id": task_id,
            "start_time": 0.0,
            "end_time": 12.0,
            "content": "大家好，欢迎收听测试播客。今天我们讨论软件测试的重要性。",
            "sentences": [
                {"start": 0.0, "end": 5.0, "text": "大家好，欢迎收听测试播客。", "speaker": "SPEAKER_00"},
                {"start": 5.0, "end": 12.0, "text": "今天我们讨论软件测试的重要性。", "speaker": "SPEAKER_00"},
            ],
            "speaker": "SPEAKER_00"
        },
        {
            "id": f"p_{task_id}_1",
            "podcast_id": task_id,
            "start_time": 12.0,
            "end_time": 20.0,
            "content": "测试是保证软件质量的关键环节。",
            "sentences": [
                {"start": 12.0, "end": 20.0, "text": "测试是保证软件质量的关键环节。", "speaker": "SPEAKER_01"},
            ],
            "speaker": "SPEAKER_01"
        }
    ]
    test_db.add_paragraphs(paragraphs)

    return {
        "id": task_id,
        "url": "https://example.com/podcast/ep1",
        "status": "completed",
        "title": "测试播客 - 第一期",
        "paragraphs": paragraphs,
    }


@pytest.fixture
def sample_pending_task(_isolate_test_env):
    """创建一个 pending 状态的示例任务"""
    test_db = _isolate_test_env
    task_id = str(uuid.uuid4())
    test_db.add_task(task_id, "https://example.com/podcast/ep2", asr_mode="local", summary_mode="local")
    return {"id": task_id, "url": "https://example.com/podcast/ep2", "status": "pending"}


@pytest.fixture
def mock_downloader(monkeypatch):
    """Mock PodcastDownloader 的下载和元数据解析方法"""
    from app.routers.tasks import downloader

    def fake_download(url, progress_callback=None):
        if progress_callback:
            progress_callback(100.0)
        return ("/tmp/fake_audio.mp3", {"title": "Fake Podcast", "duration": "30:00"})

    def fake_parse_metadata(url):
        return {
            "title": "Fake Podcast Title",
            "podcast_name": "Fake Podcast Show",
            "image_url": "https://example.com/fake.jpg",
            "shownotes": "Fake shownotes",
            "like_count": 42,
            "comment_count": 5,
            "comments": [],
            "source": "xiaoyuzhou",
            "duration": "30:00"
        }

    monkeypatch.setattr(downloader, "download_url_audio", fake_download)
    monkeypatch.setattr(downloader, "parse_metadata", fake_parse_metadata)
    return downloader
