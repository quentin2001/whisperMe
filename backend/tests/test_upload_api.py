"""
whisperMe Upload API 测试
覆盖：音频上传、格式校验、任务创建
"""
import io
import pytest


class TestUploadAudio:
    """POST /api/upload"""

    def test_upload_mp3(self, client):
        """上传 .mp3 文件成功"""
        fake_mp3 = io.BytesIO(b"\xff\xfb\x90\x00" + b"\x00" * 100)  # MP3 文件头
        resp = client.post(
            "/api/upload",
            files={"file": ("test_podcast.mp3", fake_mp3, "audio/mpeg")},
            data={"asr_mode": "local"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "task_id" in data
        assert data["status"] == "pending"

    def test_upload_wav(self, client):
        """上传 .wav 文件成功"""
        fake_wav = io.BytesIO(b"RIFF" + b"\x00" * 100)
        resp = client.post(
            "/api/upload",
            files={"file": ("test_audio.wav", fake_wav, "audio/wav")},
            data={"asr_mode": "local"},
        )
        assert resp.status_code == 200

    def test_upload_unsupported_format(self, client):
        """上传 .txt 返回 400"""
        fake_txt = io.BytesIO(b"this is not audio")
        resp = client.post(
            "/api/upload",
            files={"file": ("readme.txt", fake_txt, "text/plain")},
        )
        assert resp.status_code == 400
        assert "不支持" in resp.json()["detail"]

    def test_upload_creates_task_in_db(self, client, _isolate_test_env):
        """上传后数据库中有对应任务"""
        db = _isolate_test_env
        fake_mp3 = io.BytesIO(b"\xff\xfb\x90\x00" + b"\x00" * 100)
        resp = client.post(
            "/api/upload",
            files={"file": ("my_podcast.mp3", fake_mp3, "audio/mpeg")},
        )
        assert resp.status_code == 200
        task_id = resp.json()["task_id"]

        task = db.get_task(task_id)
        assert task is not None
        assert task["title"] == "my_podcast"
        assert task["podcast_name"] == "本地导入"

    def test_upload_with_asr_mode(self, client):
        """自定义 asr_mode 参数"""
        fake_mp3 = io.BytesIO(b"\xff\xfb\x90\x00" + b"\x00" * 100)
        resp = client.post(
            "/api/upload",
            files={"file": ("test.mp3", fake_mp3, "audio/mpeg")},
            data={"asr_mode": "online"},
        )
        assert resp.status_code == 200
