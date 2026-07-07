from app.database.core import DatabaseCore
from app.database.migrations import init_schema, run_migrations
from app.database.repositories.task_repository import TaskRepository
from app.database.repositories.paragraph_repository import ParagraphRepository
from app.database.repositories.speaker_repository import SpeakerRepository

class DatabaseFacade:
    def __init__(self):
        self.core = DatabaseCore()
        init_schema(self.core)
        
        self.task_repo = TaskRepository(self.core)
        self.paragraph_repo = ParagraphRepository(self.core)
        self.speaker_repo = SpeakerRepository(self.core)
        
        run_migrations(self.core, self)

    # ==================== TASKS ====================
    def get_all_tasks(self):
        return self.task_repo.get_all_tasks()

    def get_task(self, task_id: str):
        return self.task_repo.get_task(task_id)

    def get_task_by_url(self, url: str):
        return self.task_repo.get_task_by_url(url)

    def get_next_pending_task(self):
        return self.task_repo.get_next_pending_task()

    def get_task_queue_position(self, task_id: str, current_task_id: str = None):
        return self.task_repo.get_task_queue_position(task_id, current_task_id)

    def add_task(self, task_id: str, url: str, asr_mode: str = "local", summary_mode: str = "local"):
        return self.task_repo.add_task(task_id, url, asr_mode, summary_mode)

    def update_task_field(self, task_id: str, **kwargs):
        return self.task_repo.update_task_field(task_id, **kwargs)

    def delete_task(self, task_id: str):
        return self.task_repo.delete_task(task_id)

    # ==================== PARAGRAPHS ====================
    def get_paragraphs_by_podcast(self, podcast_id: str):
        return self.paragraph_repo.get_paragraphs_by_podcast(podcast_id)

    def delete_paragraphs_by_podcast(self, podcast_id: str):
        return self.paragraph_repo.delete_paragraphs_by_podcast(podcast_id)

    def add_paragraphs(self, paragraphs: list[dict]):
        return self.paragraph_repo.add_paragraphs(paragraphs)



    # ==================== SPEAKERS ====================
    def get_all_speakers(self):
        return self.speaker_repo.get_all_speakers()

    def get_speaker(self, name: str):
        return self.speaker_repo.get_speaker(name)

    def get_all_speakers_with_embeddings(self):
        return self.speaker_repo.get_all_speakers_with_embeddings()

    def upsert_speaker(self, name: str, embedding: list[float], sample_count: int = 1):
        return self.speaker_repo.upsert_speaker(name, embedding, sample_count)

    def merge_speakers(self, source_name: str, target_name: str) -> bool:
        return self.speaker_repo.merge_speakers(source_name, target_name)

    def delete_speaker(self, name: str) -> bool:
        return self.speaker_repo.delete_speaker(name)

# Expose a global db instance
db = DatabaseFacade()
