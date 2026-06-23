import threading
import time
from app.database import db
from app.config import config

# 导入日志接管
from app.core import logger
print = logger.info


def detect_max_concurrent() -> int:
    """
    确定最大并行任务数：
    1. 用户手动配置 max_concurrent_tasks > 0 → 直接使用
    2. 自动检测 GPU 显存：
       - 无 GPU 或检测失败: 1（串行）
       - < 6GB VRAM: 1
       - 6-10GB VRAM: 2
       - >= 10GB VRAM: 3
    """
    user_cfg = config.get("max_concurrent_tasks", 0)
    if user_cfg and user_cfg > 0:
        print(f"⚙️ [LOG] 使用用户配置的并行数: {user_cfg}")
        return user_cfg

    try:
        import torch
        if torch.cuda.is_available():
            free_mem, total_mem = torch.cuda.mem_get_info(0)
            total_gb = total_mem / (1024 ** 3)
            if total_gb >= 10:
                return 3
            elif total_gb >= 6:
                return 2
            else:
                return 1
    except Exception:
        pass
    return 1


class TaskQueueManager:
    def __init__(self):
        self.worker_threads = []
        self.running = False
        self.handler = None
        self.current_task_ids = set()
        self.lock = threading.Lock()
        self.wakeup_event = threading.Event()
        self._max_concurrent = 1  # 启动时再检测

    def start(self, handler_fn):
        """
        启动后台工作线程池
        """
        self.handler = handler_fn
        self.running = True
        self._max_concurrent = detect_max_concurrent()
        print(f"⚙️ [LOG] 并行转录模式启动 - 最大并发数: {self._max_concurrent}")

        for i in range(self._max_concurrent):
            t = threading.Thread(target=self._worker_loop, args=(i,), daemon=True)
            t.start()
            self.worker_threads.append(t)

    def stop(self):
        """
        关闭后台工作线程
        """
        self.running = False
        self.wakeup_event.set()  # 唤醒等待中的线程以退出
        for t in self.worker_threads:
            t.join(timeout=5.0)
        self.worker_threads = []
        print("⚙️ [LOG] 后台 SQLite 驱动任务队列工作线程已停止。")

    def add_task(self, task_id: str, url: str):
        """
        将任务加入处理队列（仅用于唤醒线程进行调度，具体任务入库由 API 路由层完成）
        """
        print(f"📥 [LOG] 任务 {task_id} 已记录并加入 SQLite 排队状态。")
        self.wakeup_event.set()

    def get_current_task_id(self):
        """
        获取第一个正在运行的任务 ID（兼容旧调用）
        """
        with self.lock:
            if self.current_task_ids:
                return next(iter(self.current_task_ids))
            return None

    def get_current_task_ids(self):
        """
        获取所有正在运行的任务 ID 集合
        """
        with self.lock:
            return set(self.current_task_ids)

    def get_queue_position(self, task_id: str) -> int:
        """
        获取任务在队列中的排队位置（0 表示正在运行，1 表示排在第一个，2 表示排在第二个...）
        """
        with self.lock:
            if task_id in self.current_task_ids:
                return 0
        return db.get_task_queue_position(task_id, None)

    def _worker_loop(self, worker_id: int):
        """每个 worker 线程独立运行，从队列中取任务执行"""
        while self.running:
            try:
                # 检查是否已达并发上限
                with self.lock:
                    active_count = len(self.current_task_ids)

                if active_count >= self._max_concurrent:
                    # 已满载，等待唤醒
                    self.wakeup_event.wait(timeout=3.0)
                    self.wakeup_event.clear()
                    continue

                # 查找下一个等待执行的 pending 任务（排除已在执行的）
                next_task = db.get_next_pending_task()

                if next_task is None:
                    self.wakeup_event.wait(timeout=3.0)
                    self.wakeup_event.clear()
                    continue

                task_id = next_task.get("id")

                # 尝试抢占任务（CAS 操作，防止多个 worker 重复取同一任务）
                with self.lock:
                    if task_id in self.current_task_ids:
                        continue
                    self.current_task_ids.add(task_id)

                url = next_task.get("url")
                print(f"🎬 [LOG] Worker-{worker_id} 开始处理任务: {task_id}")

                # 检查任务是否在调度前被取消
                check_task = db.get_task(task_id)
                if check_task and check_task.get("status") == "cancelled":
                    print(f"🚫 [LOG] 任务 {task_id} 已被标记取消，跳过调度。")
                    with self.lock:
                        self.current_task_ids.discard(task_id)
                    continue

                if self.handler:
                    try:
                        self.handler(task_id, url)
                    except Exception as e:
                        print(f"❌ [LOG] Worker-{worker_id} 处理任务 {task_id} 出现未捕获异常: {e}")

                with self.lock:
                    self.current_task_ids.discard(task_id)

                # 唤醒其他 worker 检查新任务
                self.wakeup_event.set()
                print(f"🏁 [LOG] Worker-{worker_id} 完成任务调度: {task_id}")
            except Exception as e:
                print(f"⚠️ [LOG] Worker-{worker_id} 队列循环出现异常: {e}")
                time.sleep(1)

# 实例化全局单例
queue_manager = TaskQueueManager()
