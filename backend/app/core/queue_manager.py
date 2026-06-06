import queue
import threading
import time

class TaskQueueManager:
    def __init__(self):
        self.task_queue = queue.Queue()
        self.worker_thread = None
        self.running = False
        self.handler = None
        self.current_task_id = None
        self.lock = threading.Lock()

    def start(self, handler_fn):
        """
        启动后台工作线程
        """
        self.handler = handler_fn
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        print("⚙️ [LOG] 后台串行任务队列工作线程已启动。")

    def stop(self):
        """
        关闭后台工作线程
        """
        self.running = False
        self.task_queue.put(None)
        if self.worker_thread:
            self.worker_thread.join()
        print("⚙️ [LOG] 后台串行任务队列工作线程已停止。")

    def add_task(self, task_id: str, url: str):
        """
        将任务加入处理队列
        """
        self.task_queue.put((task_id, url))
        print(f"📥 [LOG] 任务 {task_id} 已加入队列中。")

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
        with self.lock:
            if self.current_task_id == task_id:
                return 0
        
        # 复制队列里的内容来计算排队名次
        items = list(self.task_queue.queue)
        for idx, item in enumerate(items):
            if item is None:
                continue
            tid, _ = item
            if tid == task_id:
                return idx + 1 # 1-based index
        return -1

    def _worker_loop(self):
        while self.running:
            try:
                item = self.task_queue.get()
                if item is None:
                    break
                
                task_id, url = item
                with self.lock:
                    self.current_task_id = task_id
                
                print(f"🎬 [LOG] 队列开始处理任务: {task_id}")
                if self.handler:
                    try:
                        self.handler(task_id, url)
                    except Exception as e:
                        print(f"❌ [LOG] 队列处理任务 {task_id} 出现未捕获异常: {e}")
                
                with self.lock:
                    self.current_task_id = None
                self.task_queue.task_done()
                print(f"🏁 [LOG] 队列完成任务处理: {task_id}")
            except Exception as e:
                print(f"⚠️ [LOG] 队列循环出现异常: {e}")
                time.sleep(1)

# 实例化全局单例
queue_manager = TaskQueueManager()
