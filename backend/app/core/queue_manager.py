import threading
import time
from app.database import db

# 导入日志接管
from app.core import logger
print = logger.info

class TaskQueueManager:
    def __init__(self):
        self.worker_thread = None
        self.running = False
        self.handler = None
        self.current_task_id = None
        self.lock = threading.Lock()
        self.wakeup_event = threading.Event()

    def start(self, handler_fn):
        """
        启动后台工作线程
        """
        self.handler = handler_fn
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        print("⚙️ [LOG] 后台 SQLite 驱动任务队列工作线程已启动。")

    def stop(self):
        """
        关闭后台工作线程
        """
        self.running = False
        self.wakeup_event.set()  # 唤醒等待中的线程以退出
        if self.worker_thread:
            self.worker_thread.join()
        print("⚙️ [LOG] 后台 SQLite 驱动任务队列工作线程已停止。")

    def add_task(self, task_id: str, url: str):
        """
        将任务加入处理队列（仅用于唤醒线程进行调度，具体任务入库由 API 路由层完成）
        """
        print(f"📥 [LOG] 任务 {task_id} 已记录并加入 SQLite 排队状态。")
        self.wakeup_event.set()

    def get_current_task_id(self):
        """
        获取当前正在运行的任务 ID
        """
        with self.lock:
            return self.current_task_id

    def get_queue_position(self, task_id: str) -> int:
        """
        获取任务在队列中的排队位置（0 表示正在运行，1 表示排在第一个，2 表示排在第二个...）
        """
        curr_id = self.get_current_task_id()
        return db.get_task_queue_position(task_id, curr_id)

    def _worker_loop(self):
        while self.running:
            try:
                # 1. 查找下一个等待执行的 pending 任务
                next_task = db.get_next_pending_task()
                
                if next_task is None:
                    # 如果没有排队任务，线程进入阻塞等待，直到有新任务唤醒（或 3 秒超时轮询兜底）
                    self.wakeup_event.wait(timeout=3.0)
                    self.wakeup_event.clear()
                    continue

                task_id = next_task.get("id")
                url = next_task.get("url")

                with self.lock:
                    self.current_task_id = task_id
                
                print(f"🎬 [LOG] SQLite 队列开始调度处理任务: {task_id}")
                
                # 检查任务是否在调度前被取消
                check_task = db.get_task(task_id)
                if check_task and check_task.get("status") == "cancelled":
                    print(f"🚫 [LOG] 任务 {task_id} 已被标记取消，跳过调度。")
                    with self.lock:
                        self.current_task_id = None
                    continue
                
                if self.handler:
                    try:
                        self.handler(task_id, url)
                    except Exception as e:
                        print(f"❌ [LOG] SQLite 队列处理任务 {task_id} 出现未捕获异常: {e}")
                
                with self.lock:
                    self.current_task_id = None
                
                print(f"🏁 [LOG] SQLite 队列完成任务调度: {task_id}")
            except Exception as e:
                print(f"⚠️ [LOG] SQLite 队列循环出现异常: {e}")
                time.sleep(1)

# 实例化全局单例
queue_manager = TaskQueueManager()
