"""
whisperMe Tasks API 测试
覆盖：任务 CRUD、批量创建、取消、说话人管理、转录导出
"""
import uuid
import pytest


class TestListTasks:
    """GET /api/tasks"""

    def test_list_tasks_empty(self, client):
        """空库返回空列表"""
        resp = client.get("/api/tasks")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_tasks_with_data(self, client, sample_task):
        """有任务时返回正确数据"""
        resp = client.get("/api/tasks")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        ids = [t["id"] for t in data]
        assert sample_task["id"] in ids


class TestCreateTask:
    """POST /api/tasks"""

    def test_create_task(self, client):
        """创建任务返回 task_id + status=pending"""
        resp = client.post("/api/tasks", json={"url": "https://example.com/podcast/ep1"})
        assert resp.status_code == 200
        data = resp.json()
        assert "task_id" in data
        assert data["status"] == "pending"

    def test_create_task_missing_url(self, client):
        """缺少 url 字段返回 422"""
        resp = client.post("/api/tasks", json={})
        assert resp.status_code == 422

    def test_create_task_with_asr_mode(self, client):
        """指定 asr_mode 参数"""
        resp = client.post("/api/tasks", json={
            "url": "https://example.com/podcast/ep1",
            "asr_mode": "online"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "pending"


class TestBatchCreateTasks:
    """POST /api/tasks/batch"""

    def test_batch_create_tasks(self, client):
        """批量创建成功"""
        resp = client.post("/api/tasks/batch", json={
            "urls": [
                "https://example.com/podcast/ep1",
                "https://example.com/podcast/ep2",
                "https://example.com/podcast/ep3",
            ]
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["created"] == 3
        assert len(data["tasks"]) == 3
        for t in data["tasks"]:
            assert t["status"] == "pending"

    def test_batch_create_over_20(self, client):
        """超过 20 个链接返回 400"""
        urls = [f"https://example.com/podcast/ep{i}" for i in range(21)]
        resp = client.post("/api/tasks/batch", json={"urls": urls})
        assert resp.status_code == 400

    def test_batch_create_empty_list(self, client):
        """空列表返回 400"""
        resp = client.post("/api/tasks/batch", json={"urls": []})
        assert resp.status_code == 400


class TestGetTaskDetail:
    """GET /api/tasks/{task_id}"""

    def test_get_task_detail(self, client, sample_task):
        """返回完整任务详情"""
        resp = client.get(f"/api/tasks/{sample_task['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == sample_task["id"]
        assert data["title"] == "测试播客 - 第一期"
        assert data["status"] == "completed"
        # completed 任务应包含 paragraphs
        assert "paragraphs" in data
        assert len(data["paragraphs"]) == 2

    def test_get_task_not_found(self, client):
        """不存在的任务返回 404"""
        resp = client.get(f"/api/tasks/{uuid.uuid4()}")
        assert resp.status_code == 404

    def test_get_pending_task_no_paragraphs(self, client, sample_pending_task):
        """pending 任务的 paragraphs 为空"""
        resp = client.get(f"/api/tasks/{sample_pending_task['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["paragraphs"] == []


class TestDeleteTask:
    """DELETE /api/tasks/{task_id}"""

    def test_delete_task(self, client, sample_task):
        """删除已完成的任务"""
        resp = client.delete(f"/api/tasks/{sample_task['id']}")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # 确认已删除
        resp2 = client.get(f"/api/tasks/{sample_task['id']}")
        assert resp2.status_code == 404

    def test_delete_pending_task(self, client, sample_pending_task):
        """删除 pending 任务（会先取消再删除）"""
        resp = client.delete(f"/api/tasks/{sample_pending_task['id']}")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_delete_nonexistent_task(self, client):
        """删除不存在的任务返回 404"""
        resp = client.delete(f"/api/tasks/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestCancelTask:
    """POST /api/tasks/{task_id}/cancel"""

    def test_cancel_pending_task(self, client, sample_pending_task):
        """取消 pending 任务"""
        resp = client.post(f"/api/tasks/{sample_pending_task['id']}/cancel")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    def test_cancel_completed_task(self, client, sample_task):
        """取消已完成任务返回 success=false"""
        resp = client.post(f"/api/tasks/{sample_task['id']}/cancel")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False

    def test_cancel_nonexistent_task(self, client):
        """取消不存在的任务返回 404"""
        resp = client.post(f"/api/tasks/{uuid.uuid4()}/cancel")
        assert resp.status_code == 404


class TestSpeakerManagement:
    """说话人管理 API"""

    def test_rename_speaker(self, client, sample_task):
        """重命名说话人"""
        resp = client.post(f"/api/tasks/{sample_task['id']}/speaker/rename", json={
            "speaker_id": "SPEAKER_00",
            "new_name": "主持人小明"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["speaker_mappings"]["SPEAKER_00"] == "主持人小明"

    def test_list_speakers(self, client, _isolate_test_env):
        """获取全局声纹库列表"""
        db = _isolate_test_env
        db.upsert_speaker("Alice", [0.1] * 10)

        resp = client.get("/api/tasks/speakers/list")
        assert resp.status_code == 200
        data = resp.json()
        assert "speakers" in data
        names = [s["name"] for s in data["speakers"]]
        assert "Alice" in names

    def test_merge_speakers(self, client, _isolate_test_env):
        """合并两个说话人声纹"""
        db = _isolate_test_env
        db.upsert_speaker("Alice", [1.0, 0.0, 0.0], sample_count=3)
        db.upsert_speaker("Bob", [0.0, 1.0, 0.0], sample_count=2)

        resp = client.post("/api/tasks/speakers/merge", json={
            "source_name": "Bob",
            "target_name": "Alice"
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # Bob 应该已被删除
        resp2 = client.get("/api/tasks/speakers/list")
        names = [s["name"] for s in resp2.json()["speakers"]]
        assert "Bob" not in names
        assert "Alice" in names

    def test_merge_same_speaker(self, client):
        """合并同一个说话人返回 400"""
        resp = client.post("/api/tasks/speakers/merge", json={
            "source_name": "Alice",
            "target_name": "Alice"
        })
        assert resp.status_code == 400

    def test_forget_speaker(self, client, _isolate_test_env):
        """从声纹库中删除说话人"""
        db = _isolate_test_env
        db.upsert_speaker("Alice", [0.1] * 10)

        resp = client.post("/api/tasks/speakers/forget", json={"name": "Alice"})
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_forget_nonexistent_speaker(self, client):
        """删除不存在的说话人返回 404"""
        resp = client.post("/api/tasks/speakers/forget", json={"name": "Nobody"})
        assert resp.status_code == 404


class TestTranscriptExport:
    """GET /api/tasks/{task_id}/transcript"""

    def test_export_transcript_text(self, client, sample_task):
        """导出 text 格式"""
        resp = client.get(f"/api/tasks/{sample_task['id']}/transcript?format=text")
        assert resp.status_code == 200
        text = resp.text
        assert "主持人" in text or "SPEAKER_00" in text
        assert "测试播客" in text

    def test_export_transcript_srt(self, client, sample_task):
        """导出 SRT 格式"""
        resp = client.get(f"/api/tasks/{sample_task['id']}/transcript?format=srt")
        assert resp.status_code == 200
        text = resp.text
        assert "-->" in text
        assert "00:00" in text

    def test_export_transcript_vtt(self, client, sample_task):
        """导出 VTT 格式"""
        resp = client.get(f"/api/tasks/{sample_task['id']}/transcript?format=vtt")
        assert resp.status_code == 200
        text = resp.text
        assert "WEBVTT" in text

    def test_export_transcript_json(self, client, sample_task):
        """导出 JSON 格式"""
        resp = client.get(f"/api/tasks/{sample_task['id']}/transcript?format=json")
        assert resp.status_code == 200
        data = resp.json()
        assert "paragraphs" in data
        assert "speaker_mappings" in data
        assert data["task_id"] == sample_task["id"]

    def test_export_transcript_docx(self, client, sample_task):
        """导出 DOCX 格式逐字稿"""
        import io
        import docx
        resp = client.get(f"/api/tasks/{sample_task['id']}/transcript?format=docx")
        assert resp.status_code == 200
        assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in resp.headers["content-type"]
        doc = docx.Document(io.BytesIO(resp.content))
        assert len(doc.paragraphs) > 0

    def test_export_transcript_markdown(self, client, sample_task):
        """导出 Markdown 格式逐字稿"""
        resp = client.get(f"/api/tasks/{sample_task['id']}/transcript?format=markdown")
        assert resp.status_code == 200
        assert "text/markdown" in resp.headers["content-type"]
        assert "## 完整逐字稿" in resp.text
        assert sample_task["title"] in resp.text

    def test_export_transcript_md_alias(self, client, sample_task):
        """支持 format=md 简写导出"""
        resp = client.get(f"/api/tasks/{sample_task['id']}/transcript?format=md")
        assert resp.status_code == 200
        assert "## 完整逐字稿" in resp.text

    def test_export_transcript_not_completed(self, client, sample_pending_task):
        """未完成任务无法导出"""
        resp = client.get(f"/api/tasks/{sample_pending_task['id']}/transcript")
        assert resp.status_code == 400


class TestSummaryExport:
    """GET /api/tasks/{task_id}/summary/export"""

    def test_export_summary_docx_success(self, client, sample_task, _isolate_test_env):
        """导出 AI 总结 DOCX 格式"""
        import io
        import docx
        db = _isolate_test_env
        db.update_task_field(
            sample_task["id"],
            summary="# 深度洞察\n\n这是总结内容。\n\n| 序号 | 要点 |\n|---|---|\n| 1 | 核心观点 |"
        )

        resp = client.get(f"/api/tasks/{sample_task['id']}/summary/export?format=docx")
        assert resp.status_code == 200
        assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in resp.headers["content-type"]
        doc = docx.Document(io.BytesIO(resp.content))
        assert len(doc.paragraphs) > 0
        assert len(doc.tables) == 1

    def test_export_summary_markdown_success(self, client, sample_task, _isolate_test_env):
        """导出 AI 总结 Markdown 格式"""
        db = _isolate_test_env
        db.update_task_field(sample_task["id"], summary="# 深度洞察\n\n总结文本")

        resp = client.get(f"/api/tasks/{sample_task['id']}/summary/export?format=markdown")
        assert resp.status_code == 200
        assert "# 深度洞察" in resp.text

    def test_export_summary_no_summary(self, client, sample_task, _isolate_test_env):
        """无总结时导出返回 400"""
        db = _isolate_test_env
        db.update_task_field(sample_task["id"], summary="")
        resp = client.get(f"/api/tasks/{sample_task['id']}/summary/export?format=docx")
        assert resp.status_code == 400

    def test_export_summary_not_found(self, client):
        """任务不存在返回 404"""
        resp = client.get("/api/tasks/nonexistent-id/summary/export?format=docx")
        assert resp.status_code == 404


class TestMetadataRefresh:
    """POST /api/tasks/{task_id}/metadata/refresh"""

    def test_refresh_metadata_success(self, client, sample_task, monkeypatch):
        """成功刷新在线播客元数据和评论"""
        from app.routers import tasks as tasks_router

        mock_comments = [
            {"author": "听友A", "content": "这期播客太精彩了！", "likes": 12},
            {"author": "听友B", "content": "收获满满", "likes": 8}
        ]
        def mock_parse_metadata(url):
            return {
                "title": "已更新的标题",
                "podcast_name": "测试播客",
                "shownotes": "最新更新的大纲",
                "like_count": 99,
                "comment_count": 2,
                "comments": mock_comments,
                "image_url": "https://example.com/cover2.jpg",
                "pub_date": "2026-08-27",
                "source": "xiaoyuzhou"
            }

        monkeypatch.setattr(tasks_router.downloader, "parse_metadata", mock_parse_metadata)

        resp = client.post(f"/api/tasks/{sample_task['id']}/metadata/refresh")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["task"]["title"] == "已更新的标题"
        assert len(data["task"]["metadata"]["comments"]) == 2
        assert data["task"]["metadata"]["comments"][0]["author"] == "听友A"

    def test_refresh_metadata_nonexistent_task(self, client):
        """任务不存在返回 404"""
        resp = client.post("/api/tasks/nonexistent-id/metadata/refresh")
        assert resp.status_code == 404

    def test_refresh_metadata_local_upload_task(self, client, _isolate_test_env):
        """本地音频文件无网络 URL 返回 400"""
        db = _isolate_test_env
        db.add_task("local-upload-1", "/path/to/local/file.mp3", asr_mode="upload")
        db.update_task_field(
            "local-upload-1",
            metadata={"source": "local", "comments": []}
        )

        resp = client.post("/api/tasks/local-upload-1/metadata/refresh")
        assert resp.status_code == 400
        assert "本地上传任务没有源链接" in resp.json()["detail"]

